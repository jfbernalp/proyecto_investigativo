import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT

class CompuTrabajoScraper(BaseScraper):
    """
    Scraper robusto y especializado para co.computrabajo.com
    """

    BASE_URL = "https://co.computrabajo.com"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        super().__init__(portal_name="CompuTrabajo", headers=headers or DEFAULT_HEADERS, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Recorre las páginas de búsqueda de CompuTrabajo y extrae las ofertas y su detalle.
        """
        search_query = role.replace(" ", "-").lower()
        search_url = f"{self.BASE_URL}/trabajo-de-{search_query}?p="
        
        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            url = f"{search_url}{page}"
            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    if response.status_code == 403:
                        print("   Motivo: 403 Forbidden (Bloqueo de acceso o User-Agent inválido).")
                    elif response.status_code == 404:
                        print("   Motivo: 404 Not Found (Fin de listado o ruta no encontrada).")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                offers = soup.select("article[data-id]")

                if not offers:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}. Fin de la búsqueda.")
                    break

                print(f"[{self.portal_name}] Se encontraron {len(offers)} ofertas en la página {page}.")

                for idx, offer in enumerate(offers, start=1):
                    codigo = offer.get("data-id", "N/A")

                    link_elem = offer.select_one("h2 a.js-o-link, h1 a.js-o-link, a.js-o-link") or offer.find("a")
                    if not link_elem:
                        continue

                    nombre_oferta = link_elem.get_text(strip=True)
                    href = link_elem.get("href", "")
                    link = self.BASE_URL + href if href.startswith("/") else href

                    # FILTRO TEMPRANO: Si el cargo no es de datos, descartar antes de hacer la petición de detalle
                    from src.processing.cleaner import es_oferta_relevante
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    empresa_elem = offer.select_one("p a[offer-grid-article-company-url], p.fc_base a")
                    empresa = empresa_elem.get_text(strip=True) if empresa_elem else "Confidencial / No especificada"

                    ubicacion_elem = offer.select_one("p.fs16 span.mr10")
                    ubicacion = ubicacion_elem.get_text(strip=True) if ubicacion_elem else "No especificada"

                    badges = [s.get_text(strip=True) for s in offer.select("div.fs13 span.dIB")]
                    salario = "A convenir / No especificado"
                    modalidad = "No especificada"

                    for badge in badges:
                        if "$" in badge or "Mensual" in badge:
                            salario = badge
                        elif any(m in badge.lower() for m in ["remoto", "presencial", "híbrido", "hibrido"]):
                            modalidad = badge

                    fecha_elem = offer.select_one("p.fc_aux")
                    fecha_publicacion = fecha_elem.get_text(strip=True) if fecha_elem else "No especificada"

                    # Pausa de cortesía
                    time.sleep(random.uniform(0.5, 1.2))

                    # Consulta a detalle
                    descripcion = ""
                    requisitos_texto = ""

                    try:
                        job_resp = self.session.get(link, headers=self.headers, timeout=self.timeout)
                        if job_resp.status_code == 200:
                            job_soup = BeautifulSoup(job_resp.text, "html.parser")
                            
                            desc_elem = job_soup.find("p", class_="mbB")
                            if desc_elem:
                                descripcion = desc_elem.get_text(separator="\n", strip=True)

                            req_elem = job_soup.find("ul", class_="disc mbB")
                            if req_elem:
                                req_list = [li.get_text(strip=True) for li in req_elem.find_all("li")]
                                requisitos_texto = " | ".join(req_list)
                    except Exception as e:
                        print(f"   [AVISO] Error al conectar con detalle de oferta {codigo}: {e}")

                    self.data.append({
                        "Portal": self.portal_name,
                        "Rol_Buscado": role,
                        "Codigo": codigo,
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
                print(f"[{self.portal_name}] [EXCEPCIÓN CRÍTICA] Error de red en página {page}: {e}")
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas obtenidas: {len(self.data)}")
        return self.data
