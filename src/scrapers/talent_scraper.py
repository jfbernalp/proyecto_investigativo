import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante

class TalentScraper(BaseScraper):
    """
    Scraper modular para el portal Talent.com Colombia (co.talent.com).
    Extrae ofertas técnicas locales y remotas en Colombia.
    """

    BASE_URL = "https://co.talent.com"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        })
        super().__init__(portal_name="Talent.com", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Consulta ofertas en Talent.com Colombia para el rol especificado.
        """
        query_map = {
            "cientifico-de-datos": "data+scientist",
            "analista-de-datos": "data+analyst",
            "ingeniero-de-datos": "data+engineer"
        }
        keyword = query_map.get(role, role.replace("-", "+"))

        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            url = f"{self.BASE_URL}/jobs?k={keyword}&l=Colombia&p={page}"
            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self._get_con_reintentos(self.session, url)

                if response is None or response.status_code != 200:
                    estado = response.status_code if response is not None else "sin respuesta"
                    print(f"[{self.portal_name}] [ERROR HTTP {estado}] en página {page}.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # Cada vacante vive en un contenedor con su ID estable (data-new-id), que también
                # forma la URL /view?id=. Antes se usaba la posición (TAL_página_índice), lo que
                # mezclaba ofertas distintas entre meses en el histórico.
                job_cards = soup.select("[data-new-id]")

                if not job_cards:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se detectaron {len(job_cards)} vacantes en página {page}. Evaluando relevancia...")

                for c in job_cards:
                    h_el = c.find(["h2", "h3"])
                    nombre_oferta = h_el.get_text(strip=True) if h_el else ""

                    # FILTRO TEMPRANO: Descartar si no es del dominio de datos
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    codigo = c["data-new-id"].strip()
                    if not codigo or any(d["Codigo"] == codigo for d in self.data):
                        continue
                    link = f"{self.BASE_URL}/view?id={codigo}"

                    # Empresa
                    comp_el = c.find(class_=lambda cl: cl and ("company" in str(cl).lower() or "employer" in str(cl).lower()))
                    empresa = comp_el.get_text(strip=True) if comp_el else "Confidencial / No especificada"

                    # Ubicación
                    loc_el = c.find(class_=lambda cl: cl and ("location" in str(cl).lower() or "city" in str(cl).lower()))
                    ubicacion = loc_el.get_text(strip=True) if loc_el else "Colombia"

                    # Salario
                    sal_el = c.find(class_=lambda cl: cl and ("salary" in str(cl).lower() or "price" in str(cl).lower() or "badge" in str(cl).lower()))
                    salario_texto = sal_el.get_text(strip=True) if sal_el and "$" in sal_el.get_text() else "A convenir / No especificado"

                    # Modalidad
                    modalidad = "Presencial"
                    nombre_lower = (nombre_oferta + " " + ubicacion).lower()
                    if "remoto" in nombre_lower or "remote" in nombre_lower:
                        modalidad = "Remoto"
                    elif "híbrido" in nombre_lower or "hibrido" in nombre_lower or "hybrid" in nombre_lower:
                        modalidad = "Híbrido"

                    descripcion = self._obtener_descripcion(link)

                    self.data.append({
                        "Portal": self.portal_name,
                        "Rol_Buscado": role,
                        "Codigo": codigo,
                        "Nombre Oferta": nombre_oferta,
                        "Empresa": empresa,
                        "Ubicacion": ubicacion,
                        "Salario": salario_texto,
                        "Modalidad": modalidad,
                        "Fecha Publicacion": "Reciente",
                        "Descripcion": descripcion,
                        "Requisitos": "",
                        "URL": link
                    })

            except requests.exceptions.RequestException as e:
                print(f"[{self.portal_name}] [EXCEPCIÓN CRÍTICA] Error de red en página {page}: {e}")
                break

            page += 1
            time.sleep(random.uniform(1.0, 2.0))

        con_detalle = sum(1 for d in self.data if d["Descripcion"])
        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)} "
              f"({con_detalle} con descripción completa)")
        return self.data

    def _obtener_descripcion(self, link: str) -> str:
        """Texto completo de la vacante: JSON-LD JobPosting si existe, si no el bloque de descripción."""
        time.sleep(random.uniform(0.8, 1.6))
        response = self._get_con_reintentos(self.session, link)
        if response is None or response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                datos = json.loads(script.string or "")
            except ValueError:
                continue
            for item in (datos if isinstance(datos, list) else [datos]):
                if isinstance(item, dict) and item.get("@type") == "JobPosting" and item.get("description"):
                    return BeautifulSoup(item["description"], "html.parser").get_text(" ", strip=True)
        bloque = soup.select_one('[class*="description" i]')
        return bloque.get_text(" ", strip=True) if bloque else ""
