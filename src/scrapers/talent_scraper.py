import requests
from bs4 import BeautifulSoup
import time
import random
import re
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
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                
                # Identificar tarjetas únicas de empleo
                job_cards = []
                for c in soup.find_all("div", class_=lambda cl: cl and "JobCard_" in cl):
                    title_el = c.find(["h2", "h3"])
                    if title_el and title_el not in [j.find(["h2", "h3"]) for j in job_cards]:
                        job_cards.append(c)

                if not job_cards:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se detectaron {len(job_cards)} vacantes en página {page}. Evaluando relevancia...")

                for idx, c in enumerate(job_cards, start=1):
                    h_el = c.find(["h2", "h3"])
                    nombre_oferta = h_el.get_text(strip=True) if h_el else ""

                    # FILTRO TEMPRANO: Descartar si no es del dominio de datos
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    # Enlace e ID
                    link_el = c.find("a", href=re.compile(r"/view\?id=")) or c.find("a", href=True)
                    href = link_el.get("href", "") if link_el else ""
                    link = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                    
                    id_match = re.search(r"id=([a-zA-Z0-9_-]+)", href)
                    codigo = id_match.group(1) if id_match else f"TAL_{page}_{idx}"

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

                    # Descripción / Snippet
                    p_snippet = c.find("p")
                    descripcion = p_snippet.get_text(strip=True) if p_snippet else ""
                    requisitos_texto = ""

                    # Evitar duplicados
                    if any(d["Codigo"] == str(codigo) for d in self.data):
                        continue

                    self.data.append({
                        "Portal": self.portal_name,
                        "Rol_Buscado": role,
                        "Codigo": str(codigo),
                        "Nombre Oferta": nombre_oferta,
                        "Empresa": empresa,
                        "Ubicacion": ubicacion,
                        "Salario": salario_texto,
                        "Modalidad": modalidad,
                        "Fecha Publicacion": "Reciente",
                        "Descripcion": descripcion,
                        "Requisitos": requisitos_texto,
                        "URL": link
                    })

            except requests.exceptions.RequestException as e:
                print(f"[{self.portal_name}] [EXCEPCIÓN CRÍTICA] Error de red en página {page}: {e}")
                break

            page += 1
            time.sleep(random.uniform(1.0, 2.0))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data
