import requests
from bs4 import BeautifulSoup
import time
import random
import json
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT

class ElEmpleoScraper(BaseScraper):
    """
    Scraper modular para el portal elempleo.com Colombia.
    """

    BASE_URL = "https://www.elempleo.com"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        super().__init__(portal_name="ElEmpleo", headers=headers or DEFAULT_HEADERS, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Recorre las páginas de búsqueda de ElEmpleo y extrae las ofertas cumpliendo el esquema canónico.
        """
        # Formato de URL en ElEmpleo: /co/ofertas-empleo/trabajo-cientifico-de-datos?page=1
        query_slug = role.replace("-", " ").strip().replace(" ", "-").lower()
        search_base = f"{self.BASE_URL}/co/ofertas-empleo/trabajo-{query_slug}"

        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            url = f"{search_base}?page={page}"
            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select(".result-item")

                if not cards:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se encontraron {len(cards)} ofertas en la página {page}.")

                for idx, card in enumerate(cards, start=1):
                    # 1. Intentar extraer data embebida de Google Analytics si está disponible
                    area_bind = card.select_one(".js-area-bind")
                    ga_data = {}
                    if area_bind and area_bind.get("data-ga4-offerdata"):
                        try:
                            ga_data = json.loads(area_bind.get("data-ga4-offerdata"))
                        except:
                            ga_data = {}

                    # 2. Título y Enlace
                    title_elem = card.select_one("a.js-offer-title, a.titulo, h2 a")
                    if not title_elem:
                        continue

                    nombre_oferta = ga_data.get("title") or title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    link = self.BASE_URL + href if href.startswith("/") else href

                    # FILTRO TEMPRANO: Descartar cargos no relacionados antes de peticiones de detalle
                    from src.processing.cleaner import es_oferta_relevante
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    # ID de oferta
                    codigo = str(ga_data.get("id") or (href.split("-")[-1] if "-" in href else f"EE_{idx}_{page}"))

                    # Empresa
                    empresa = ga_data.get("company") or "Confidencial / No especificada"
                    if empresa == "Confidencial / No especificada":
                        emp_el = card.select_one(".info-company-name, .company-name-text")
                        if emp_el:
                            empresa = emp_el.get_text(strip=True)

                    # Ubicación
                    ubicacion = ga_data.get("location") or "No especificada"
                    if ubicacion == "No especificada":
                        loc_el = card.select_one(".info-city, .info-location, [class*='city']")
                        if loc_el:
                            ubicacion = loc_el.get_text(strip=True)

                    # Salario
                    salario = ga_data.get("salary") or "A convenir / No especificado"
                    if "confidencial" in salario.lower() or salario == "A convenir / No especificado":
                        sal_el = card.select_one(".info-salary, .text-salary")
                        if sal_el:
                            salario = sal_el.get_text(strip=True)

                    # Modalidad
                    mod_el = card.select_one(".js-work-modality, .info-modality, [class*='modality']")
                    modalidad = mod_el.get_text(strip=True).replace("-", "").strip() if mod_el else "No especificada"

                    # Fecha de publicación
                    date_el = card.select_one(".info-publish-date, .date-publish, span[class*='publish']")
                    fecha_publicacion = date_el.get_text(strip=True) if date_el else "No especificada"

                    # Pausa de cortesía
                    time.sleep(random.uniform(0.3, 0.8))

                    # 3. Consulta de Detalle para Descripción y Requisitos
                    descripcion = ""
                    requisitos_texto = ""

                    try:
                        job_resp = self.session.get(link, headers=self.headers, timeout=self.timeout)
                        if job_resp.status_code == 200:
                            job_soup = BeautifulSoup(job_resp.text, "html.parser")
                            
                            # Descripción
                            desc_container = job_soup.select_one(".description-block, .job-details, .offer-summary, .main-content, main")
                            if desc_container:
                                p_texts = [p.get_text(strip=True) for p in desc_container.find_all(["p", "div", "li"]) if len(p.get_text(strip=True)) > 40]
                                if p_texts:
                                    descripcion = "\n".join(p_texts[:8])

                            # Requisitos
                            req_tags = job_soup.select(".requirements-content, .offer-data-additional, .job-requirements, ul.list-requirements")
                            req_list = []
                            for r_tag in req_tags:
                                req_list.append(r_tag.get_text(separator=" | ", strip=True))
                            if req_list:
                                requisitos_texto = " | ".join(req_list)
                            elif ga_data.get("equivalentPositions"):
                                requisitos_texto = f"Posiciones afines: {ga_data.get('equivalentPositions')}"

                    except Exception as e:
                        print(f"   [AVISO ElEmpleo] Error al conectar con detalle de oferta {codigo}: {e}")

                    # Agregar registro cumpliendo el contrato canónico
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
            time.sleep(random.uniform(1.0, 2.5))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas obtenidas: {len(self.data)}")
        return self.data
