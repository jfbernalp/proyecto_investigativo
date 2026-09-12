import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante

class LinkedInScraper(BaseScraper):
    """
    Scraper modular para LinkedIn Jobs Colombia utilizando el endpoint público
    de búsqueda para invitados (Guest Search API). No requiere credenciales ni login.
    """

    BASE_URL = "https://co.linkedin.com"
    API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        })
        super().__init__(portal_name="LinkedIn", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Consulta ofertas en LinkedIn Jobs para el rol especificado.
        """
        keywords = role.replace("-", " ")
        self.data = []
        page = 0

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page < max_pages:
            start_idx = page * 25
            url = f"{self.API_URL}?keywords={keywords}&location=Colombia&start={start_idx}"
            print(f"\n---> [Página {page+1}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page+1}.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select("div.base-card, li")

                if not cards:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page+1}.")
                    break

                print(f"[{self.portal_name}] Se detectaron {len(cards)} tarjetas de empleo. Evaluando relevancia...")

                for c in cards:
                    title_el = c.select_one(".base-search-card__title, h3.base-search-card__title")
                    link_el = c.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
                    
                    if not title_el or not link_el:
                        continue

                    nombre_oferta = title_el.get_text(strip=True)
                    link = link_el.get("href", "").split("?")[0]  # Limpiar parámetros de tracking

                    # FILTRO TEMPRANO: Descartar si el cargo no pertenece al dominio de datos
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    # Extraer ID de la URL
                    id_match = re.search(r"-(\d+)$", link)
                    codigo = id_match.group(1) if id_match else f"LI_{len(self.data)+1}"

                    # Empresa
                    comp_el = c.select_one(".base-search-card__subtitle, h4.base-search-card__subtitle a, h4.base-search-card__subtitle")
                    empresa = comp_el.get_text(strip=True) if comp_el else "Confidencial / No especificada"

                    # Ubicación
                    loc_el = c.select_one(".job-search-card__location")
                    ubicacion = loc_el.get_text(strip=True) if loc_el else "Colombia"

                    # Fecha
                    date_el = c.select_one("time")
                    fecha_publicacion = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else "Reciente"

                    # Modalidad
                    modalidad = "Presencial"
                    nombre_lower = (nombre_oferta + " " + ubicacion).lower()
                    if "remoto" in nombre_lower or "remote" in nombre_lower:
                        modalidad = "Remoto"
                    elif "híbrido" in nombre_lower or "hibrido" in nombre_lower or "hybrid" in nombre_lower:
                        modalidad = "Híbrido"

                    salario = "A convenir / No especificado"
                    descripcion = f"Oferta publicada en LinkedIn para {nombre_oferta} en {empresa} ({ubicacion})."
                    requisitos_texto = ""

                    # Evitar duplicados en la misma corrida
                    if any(d["Codigo"] == str(codigo) for d in self.data):
                        continue

                    self.data.append({
                        "Portal": self.portal_name,
                        "Rol_Buscado": role,
                        "Codigo": str(codigo),
                        "Nombre Oferta": nombre_oferta,
                        "Empresa": empresa,
                        "Ubicacion": ubicacion,
                        "Salario": salario,
                        "Modalidad": modalidad,
                        "Fecha Publicacion": fecha_publicacion,
                        "Descripcion": descripcion,
                        "Requisitos": requisitos_texto,
                        "URL": link
                    })

            except requests.exceptions.RequestException as e:
                print(f"[{self.portal_name}] [EXCEPCIÓN CRÍTICA] Error de red en página {page+1}: {e}")
                break

            page += 1
            time.sleep(random.uniform(1.0, 2.0))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data
