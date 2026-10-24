import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante
from src.scrapers.base_scraper import BaseScraper


class RemotiveScraper(BaseScraper):
    """
    Consumidor de la API pública de Remotive (https://remotive.com/api-documentation):
    empleos remotos internacionales con salario, en reemplazo parcial de Torre.ai.

    Términos de uso de la API: citar a Remotive como fuente y enlazar la URL de cada oferta
    (se conserva en el campo URL y se cita en el portal), no consultar más de ~4 veces al día
    (el pipeline hace 1 consulta al mes) y no republicar las ofertas en otros portales de empleo
    (el observatorio publica solo análisis agregado). La API pública devuelve un número reducido
    de ofertas (≈10); el catálogo completo es de pago.
    """

    API_URL = "https://remotive.com/api/remote-jobs"
    ATRIBUCION = "Fuente: Remotive (remotive.com)"

    # Ubicaciones de candidato accesibles desde Colombia
    UBICACIONES_ACCESIBLES = ("worldwide", "anywhere", "latam", "latin america", "americas",
                              "south america", "colombia")

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({"Accept": "application/json"})
        custom_headers.pop("Referer", None)
        super().__init__(portal_name="Remotive", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 1) -> List[Dict[str, Any]]:
        self.data = []
        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (1 CONSULTA, categoría data)")
        print("=" * 70)

        response = self._get_con_reintentos(self.session, f"{self.API_URL}?category=data")
        if response is None or response.status_code != 200:
            estado = response.status_code if response is not None else "sin respuesta"
            print(f"[{self.portal_name}] [ERROR HTTP {estado}]")
            return self.data

        empleos = response.json().get("jobs", [])
        print(f"[{self.portal_name}] La API pública devolvió {len(empleos)} ofertas. Evaluando relevancia y ubicación...")
        for job in empleos:
            titulo = job.get("title", "").strip()
            descripcion = BeautifulSoup(job.get("description", ""), "html.parser").get_text(" ", strip=True)
            ubicacion = job.get("candidate_required_location") or "Worldwide"
            if not es_oferta_relevante(titulo, descripcion):
                continue
            if not any(u in ubicacion.lower() for u in self.UBICACIONES_ACCESIBLES):
                continue
            self.data.append({
                "Portal": self.portal_name,
                "Rol_Buscado": role,
                "Codigo": str(job.get("id")),
                "Nombre Oferta": titulo,
                "Empresa": job.get("company_name") or "Confidencial / No especificada",
                "Ubicacion": f"Remoto ({ubicacion})",
                "Salario": self._salario_texto(job.get("salary", "")),
                "Modalidad": "Remoto",
                "Fecha Publicacion": (job.get("publication_date") or "")[:10] or "Reciente",
                "Descripcion": descripcion,
                "Requisitos": " | ".join(job.get("tags") or []),
                "URL": job.get("url", ""),
                "Fuente": self.ATRIBUCION,
            })

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data

    @staticmethod
    def _salario_texto(texto: str) -> str:
        """
        Convierte el salario libre de Remotive ('$170k - $200k', '70K-80K', '$50-$75 /hour')
        al formato de limpiar_salario_numerico(): 'USD 170.000 a 200.000 (yearly)'.
        """
        sin_dato = "A convenir / No especificado"
        if not texto:
            return sin_dato
        t = texto.lower()
        if any(x in t for x in ("task", "project", "per word", "commission")):
            return sin_dato
        moneda = "EUR" if ("€" in t or "eur" in t) else "GBP" if ("£" in t or "gbp" in t) else "USD"
        if any(x in t for x in ("hour", "/hr", "hourly")):
            periodo = "hourly"
        elif any(x in t for x in ("month", "/mo")):
            periodo = "monthly"
        else:
            periodo = "yearly"

        valores = []
        for numero, k in re.findall(r"(\d{1,3}(?:,\d{3})+|\d+(?:[.,]\d+)?)\s*(k)?", t):
            numero = numero.replace(",", "") if re.fullmatch(r"\d{1,3}(?:,\d{3})+", numero) else numero.replace(",", ".")
            valores.append(float(numero) * (1000 if k else 1))
        valores = [v for v in valores if v > 0]
        if not valores or (periodo == "yearly" and max(valores) < 1000):
            return sin_dato
        fmt = lambda v: f"{v:,.0f}".replace(",", ".")
        rango = f"{fmt(min(valores))} a {fmt(max(valores))}" if len(valores) > 1 else fmt(valores[0])
        return f"{moneda} {rango} ({periodo})"
