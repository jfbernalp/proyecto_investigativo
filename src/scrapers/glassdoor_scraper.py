import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante

class GlassdoorScraper(BaseScraper):
    """
    Scraper modular para el portal Glassdoor Colombia (glassdoor.com).
    Extrae ofertas y salarios estimados mediante parsing HTML y Schema.org.
    """

    BASE_URL = "https://www.glassdoor.com"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        # Encabezados optimizados para Glassdoor
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        })
        super().__init__(portal_name="Glassdoor", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Consulta las ofertas en Glassdoor para el rol especificado.
        """
        # Formatear búsqueda para Glassdoor
        query_formatted = role.replace(" ", "-").lower()
        search_url = f"{self.BASE_URL}/Job/colombia-{query_formatted}-jobs-SRCH_IL.0,8_IN52.htm"

        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            # Paginación en Glassdoor (ejemplo: _IP2.htm para página 2)
            if page == 1:
                url = search_url
            else:
                url = search_url.replace(".htm", f"_IP{page}.htm")

            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    if response.status_code == 403:
                        print("   Motivo: 403 Forbidden (Protección Cloudflare de Glassdoor).")
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # 1. Buscar tarjetas de empleo mediante selectores comunes de Glassdoor
                job_cards = soup.select(
                    "li[data-id], div.JobCard_jobCardWrapper__*, li[class*='JobsList_jobListItem'], "
                    "article.jobCard, div[data-test='jobListing'], a[data-test='job-link']"
                )

                # Fallback: buscar enlaces que contengan /job-listing/ o /partner/jobListing.htm
                if not job_cards:
                    job_cards = soup.find_all("a", href=re.compile(r"/partner/jobListing\.htm|/job-listing/|/Empleo/.*-job-SRCH"))

                if not job_cards:
                    # Verificar si los datos están embebidos en JSON-LD (Schema.org) o __NEXT_DATA__
                    json_ld_tags = soup.find_all("script", type="application/ld+json")
                    found_in_json = False

                    for s in json_ld_tags:
                        try:
                            ld = json.loads(s.string)
                            if isinstance(ld, dict) and ld.get("@type") == "ItemList":
                                items = ld.get("itemListElement", [])
                                for idx, it in enumerate(items):
                                    job = it.get("item", {})
                                    if isinstance(job, dict) and job.get("@type") == "JobPosting":
                                        found_in_json = True
                                        self._procesar_job_posting_ld(job, idx, page, role)
                        except:
                            continue

                    if found_in_json:
                        print(f"[{self.portal_name}] Se extrajeron {len(self.data)} ofertas desde JSON-LD en página {page}.")
                        page += 1
                        continue

                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se detectaron {len(job_cards)} elementos de empleo en la página {page}.")

                for idx, card in enumerate(job_cards, start=1):
                    # Extracción de título y enlace
                    link_elem = card if card.name == "a" else card.find("a", href=True)
                    if not link_elem:
                        continue

                    nombre_oferta = link_elem.get_text(strip=True)
                    href = link_elem.get("href", "")
                    link = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    codigo = card.get("data-id") or re.search(r"jobListingId=(\d+)", href) or f"GD_{idx}_{page}"
                    if hasattr(codigo, "group"):
                        codigo = codigo.group(1)

                    # Empresa
                    empresa_el = card.select_one("[class*='EmployerName'], [class*='employerName'], span.EmployerProfile_employerName__*")
                    empresa = empresa_el.get_text(strip=True) if empresa_el else "Confidencial / No especificada"
                    # Limpiar posible rating numérico en el nombre de empresa (ej. 'Mercado Libre 4.2' -> 'Mercado Libre')
                    empresa = re.sub(r"\s+\d+\.\d+$", "", empresa)

                    # Ubicación
                    loc_el = card.select_one("[class*='Location'], [class*='location'], [data-test='emp-location']")
                    ubicacion = loc_el.get_text(strip=True) if loc_el else "Colombia"

                    # Salario
                    sal_el = card.select_one("[class*='Salary'], [class*='salary'], [data-test='detailSalary']")
                    salario = sal_el.get_text(strip=True) if sal_el else "A convenir / No especificado"

                    # Modalidad
                    modalidad = "No especificada"
                    if "remoto" in nombre_oferta.lower() or "remote" in nombre_oferta.lower():
                        modalidad = "Remoto"
                    elif "híbrido" in nombre_oferta.lower() or "hibrido" in nombre_oferta.lower():
                        modalidad = "Híbrido"

                    descripcion = ""
                    requisitos_texto = ""

                    # Validación de relevancia antes de agregar
                    if not es_oferta_relevante(nombre_oferta, descripcion):
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
                        "Fecha Publicacion": "Reciente",
                        "Descripcion": descripcion,
                        "Requisitos": requisitos_texto,
                        "URL": link
                    })

            except requests.exceptions.RequestException as e:
                print(f"[{self.portal_name}] [EXCEPCIÓN CRÍTICA] Error de red en página {page}: {e}")
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data

    def _procesar_job_posting_ld(self, job: Dict[str, Any], idx: int, page: int, role: str) -> None:
        """
        Procesa un objeto Schema.org JobPosting de Glassdoor.
        """
        nombre_oferta = job.get("title", "")
        empresa = job.get("hiringOrganization", {}).get("name", "Confidencial / No especificada")
        
        loc_raw = job.get("jobLocation", {}).get("address", {})
        ubicacion = loc_raw.get("addressLocality") or loc_raw.get("addressRegion") or "Colombia"
        if isinstance(ubicacion, list):
            ubicacion = ", ".join(ubicacion)

        # Salario
        base_sal = job.get("baseSalary", {})
        salario = "A convenir / No especificado"
        if isinstance(base_sal, dict):
            val_sal = base_sal.get("value", {})
            if isinstance(val_sal, dict):
                min_v = val_sal.get("minValue")
                max_v = val_sal.get("maxValue")
                if min_v and max_v:
                    salario = f"$ {min_v:,.0f} a $ {max_v:,.0f}".replace(",", ".")
                elif min_v:
                    salario = f"$ {min_v:,.0f}".replace(",", ".")

        descripcion = job.get("description", "")
        link = job.get("url") or f"{self.BASE_URL}/job-listing/{idx}"

        if not es_oferta_relevante(nombre_oferta, descripcion):
            return

        self.data.append({
            "Portal": self.portal_name,
            "Rol_Buscado": role,
            "Codigo": f"GD_{idx}_{page}",
            "Nombre Oferta": nombre_oferta,
            "Empresa": empresa,
            "Ubicacion": ubicacion,
            "Salario": salario,
            "Modalidad": "No especificada",
            "Fecha Publicacion": job.get("datePosted", "Reciente"),
            "Descripcion": descripcion,
            "Requisitos": "",
            "URL": link
        })
