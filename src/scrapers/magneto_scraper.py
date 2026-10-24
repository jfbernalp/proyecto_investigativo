import json
import random
import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante
from src.scrapers.base_scraper import BaseScraper


class MagnetoScraper(BaseScraper):
    """
    Scraper para Magneto (magneto365.com), portal de empleo colombiano.

    La búsqueda con ?q= se resuelve en el navegador (el HTML devuelve siempre las mismas
    vacantes generales). La ruta /co/trabajos/buscar/<término>[/<página>] sí se renderiza en el
    servidor y trae un ItemList JSON-LD con las URL de las vacantes. Cada vacante publica un
    JobPosting JSON-LD con descripción completa, salario y vigencia. robots.txt permite el rastreo.
    """

    BASE_URL = "https://www.magneto365.com"
    BUSQUEDA_URL = BASE_URL + "/co/trabajos/buscar/{termino}"

    TERMINOS_POR_ROL = {
        "cientifico-de-datos": [
            "cientifico-de-datos", "data-scientist", "analista-de-datos",
            "data-analyst", "ingeniero-de-datos", "data-engineer",
        ],
        "analista-de-datos": ["analista-de-datos", "data-analyst", "business-intelligence"],
        "ingeniero-de-datos": ["ingeniero-de-datos", "data-engineer"],
    }

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Referer": self.BASE_URL + "/co",
        })
        super().__init__(portal_name="Magneto", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        terminos = self.TERMINOS_POR_ROL.get(role, [role])
        self.data = []

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} ({len(terminos)} BÚSQUEDAS x {max_pages} PÁGINAS)")
        print("=" * 70)

        urls: List[str] = []
        for termino in terminos:
            vistas_termino = set()
            for page in range(1, max_pages + 1):
                url = self.BUSQUEDA_URL.format(termino=termino) + (f"/{page}" if page > 1 else "")
                print(f"\n---> [{termino} | Página {page}/{max_pages}] Consultando: {url}")
                nuevas = [u for u in self._urls_de_busqueda(url) if u not in vistas_termino]
                if not nuevas:
                    print(f"[{self.portal_name}] Sin más resultados para '{termino}'.")
                    break
                vistas_termino.update(nuevas)
                urls.extend(u for u in nuevas if u not in urls)
                time.sleep(random.uniform(1.0, 2.0))

        print(f"\n[{self.portal_name}] {len(urls)} vacantes únicas en los resultados. Consultando detalle de las relevantes...")
        for link in urls:
            codigo_match = re.search(r"-(\d+)/?$", link)
            if not codigo_match:
                continue
            # Filtro temprano por el slug (evita pedir el detalle de cargos ajenos al dominio de datos)
            titulo_slug = link.rsplit("/", 1)[-1].replace("-", " ")
            if not es_oferta_relevante(titulo_slug):
                continue
            oferta = self._obtener_oferta(link, codigo_match.group(1), role)
            if oferta and es_oferta_relevante(oferta["Nombre Oferta"], oferta["Descripcion"]):
                self.data.append(oferta)

        con_detalle = sum(1 for d in self.data if d["Descripcion"])
        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)} "
              f"({con_detalle} con descripción completa)")
        return self.data

    def _urls_de_busqueda(self, url: str) -> List[str]:
        response = self._get_con_reintentos(self.session, url)
        if response is None or response.status_code != 200:
            estado = response.status_code if response is not None else "sin respuesta"
            print(f"[{self.portal_name}] [ERROR HTTP {estado}] en {url}")
            return []
        for item in self._json_ld(response.text):
            if item.get("@type") == "ItemList":
                return [e["url"] for e in item.get("itemListElement", []) if e.get("url")]
        return []

    def _obtener_oferta(self, link: str, codigo: str, role: str) -> Optional[Dict[str, Any]]:
        time.sleep(random.uniform(0.8, 1.6))
        response = self._get_con_reintentos(self.session, link)
        if response is None or response.status_code != 200:
            return None
        job = next((i for i in self._json_ld(response.text) if i.get("@type") == "JobPosting"), None)
        if not job:
            return None

        descripcion = BeautifulSoup(job.get("description", ""), "html.parser").get_text(" ", strip=True)
        empresa = (job.get("hiringOrganization") or {}).get("name") or "Confidencial / No especificada"
        lugar = job.get("jobLocation")
        lugar = lugar[0] if isinstance(lugar, list) and lugar else lugar
        direccion = (lugar or {}).get("address") or {} if isinstance(lugar, dict) else {}
        partes = [direccion.get("addressLocality"), direccion.get("addressRegion")] if isinstance(direccion, dict) else []
        # Los campos vienen como texto, como lista o como objeto {"name": ...}
        partes = [p[0] if isinstance(p, list) and p else p for p in partes]
        partes = [p.get("name") if isinstance(p, dict) else p for p in partes]
        ubicacion = ", ".join(str(p) for p in partes if p) or "Colombia"

        modalidad = "Remoto" if job.get("jobLocationType") == "TELECOMMUTE" else "Presencial"
        texto = f"{job.get('title', '')} {descripcion}".lower()
        if modalidad == "Presencial" and ("híbrido" in texto or "hibrido" in texto or "hybrid" in texto):
            modalidad = "Híbrido"

        return {
            "Portal": self.portal_name,
            "Rol_Buscado": role,
            "Codigo": codigo,
            "Nombre Oferta": job.get("title", "").strip(),
            "Empresa": empresa,
            "Ubicacion": ubicacion,
            "Salario": self._salario_texto(job.get("baseSalary")),
            "Modalidad": modalidad,
            "Fecha Publicacion": job.get("datePosted", "Reciente"),
            "Descripcion": descripcion,
            "Requisitos": "",
            "URL": link,
        }

    @staticmethod
    def _salario_texto(base_salary: Any) -> str:
        """Formato que entiende limpiar_salario_numerico(): '$ 3.000.000 a $ 4.500.000 (Mensual)'."""
        if not isinstance(base_salary, dict):
            return "A convenir / No especificado"
        valor = base_salary.get("value") or {}
        minimo = valor.get("minValue") or valor.get("value")
        maximo = valor.get("maxValue")
        if base_salary.get("currency", "COP") != "COP" or not minimo or float(minimo) <= 0:
            return "A convenir / No especificado"
        fmt = lambda x: f"$ {float(x):,.0f}".replace(",", ".")
        rango = f"{fmt(minimo)} a {fmt(maximo)}" if maximo and float(maximo) > float(minimo) else fmt(minimo)
        return f"{rango} (Mensual)"

    @staticmethod
    def _json_ld(html: str) -> List[Dict[str, Any]]:
        items = []
        for script in BeautifulSoup(html, "html.parser").select('script[type="application/ld+json"]'):
            try:
                datos = json.loads(script.string or "")
            except ValueError:
                continue
            items.extend(d for d in (datos if isinstance(datos, list) else [datos]) if isinstance(d, dict))
        return items
