import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT

class MagnetoScraper(BaseScraper):
    """
    Scraper modular para el portal Magneto Empleos (magneto365.com).
    Aprovecha Schema.org (JSON-LD) y metadatos estructurados para máxima precisión.
    """

    BASE_URL = "https://www.magneto365.com"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        super().__init__(portal_name="Magneto", headers=headers or DEFAULT_HEADERS, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Consulta las ofertas en Magneto y extrae sus datos estructurados mapeados al esquema canónico.
        """
        # Limpieza de rol para búsqueda
        query_terms = [t for t in role.replace("-", " ").lower().split() if len(t) > 2]
        search_query = "+".join(query_terms)
        
        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            # URL de búsqueda en Magneto
            url = f"{self.BASE_URL}/co/empleos?q={search_query}&page={page}"
            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # Encontrar enlaces a vacantes (tienen el patrón /co/empleos/...-id)
                job_links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/empleos/" in href and re.search(r"-\d+$", href):
                        full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                        if full_url not in job_links:
                            job_links.append(full_url)

                if not job_links:
                    print(f"[{self.portal_name}] No se encontraron más enlaces en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se encontraron {len(job_links)} ofertas en la página {page}. Procesando detalle...")

                for idx, link in enumerate(job_links, start=1):
                    # Extraer ID y título tentativo de la URL
                    id_match = re.search(r"/empleos/(.+)-(\d+)$", link)
                    slug_title = id_match.group(1).replace("-", " ") if id_match else ""
                    codigo = id_match.group(2) if id_match else f"MAG_{idx}_{page}"

                    # FILTRO TEMPRANO: Descartar cargos por el slug de la URL antes de consultar el detalle
                    from src.processing.cleaner import es_oferta_relevante
                    if slug_title and not es_oferta_relevante(slug_title):
                        continue

                    # Pausa de cortesía
                    time.sleep(random.uniform(0.3, 0.8))

                    # Valores por defecto
                    nombre_oferta = "No especificado"
                    empresa = "Confidencial / No especificada"
                    ubicacion = "No especificada"
                    salario = "A convenir / No especificado"
                    modalidad = "No especificada"
                    fecha_publicacion = "No especificada"
                    descripcion = ""
                    requisitos_texto = ""

                    try:
                        job_resp = self.session.get(link, headers=self.headers, timeout=self.timeout)
                        if job_resp.status_code == 200:
                            job_soup = BeautifulSoup(job_resp.text, "html.parser")

                            # 1. Extracción vía Schema.org (JSON-LD) si está presente
                            ld_data = None
                            for s in job_soup.find_all("script", type="application/ld+json"):
                                try:
                                    parsed_json = json.loads(s.string)
                                    if isinstance(parsed_json, dict) and parsed_json.get("@type") == "JobPosting":
                                        ld_data = parsed_json
                                        break
                                except:
                                    continue

                            if ld_data:
                                nombre_oferta = ld_data.get("title") or nombre_oferta
                                empresa = ld_data.get("hiringOrganization", {}).get("name") or empresa
                                
                                # Ubicación
                                loc_raw = ld_data.get("jobLocation", {})
                                if isinstance(loc_raw, list) and len(loc_raw) > 0:
                                    loc_raw = loc_raw[0]
                                loc_info = loc_raw.get("address", {}) if isinstance(loc_raw, dict) else {}
                                if isinstance(loc_info, dict):
                                    city = loc_info.get("addressLocality")
                                    if isinstance(city, list):
                                        ubicacion = ", ".join(city)
                                    elif city:
                                        ubicacion = str(city)

                                # Salario
                                base_sal = ld_data.get("baseSalary", {})
                                if isinstance(base_sal, dict):
                                    val_sal = base_sal.get("value", {})
                                    if isinstance(val_sal, dict):
                                        min_v = val_sal.get("minValue")
                                        max_v = val_sal.get("maxValue")
                                        if min_v and max_v:
                                            salario = f"$ {min_v:,.0f} a $ {max_v:,.0f}".replace(",", ".")
                                        elif min_v:
                                            salario = f"$ {min_v:,.0f}".replace(",", ".")

                                # Fecha
                                fecha_publicacion = ld_data.get("datePosted") or fecha_publicacion

                                # Descripción
                                descripcion = ld_data.get("description") or ""

                            # 2. Fallback de extracción HTML si faltan datos
                            if nombre_oferta == "No especificado":
                                h1_el = job_soup.find("h1")
                                if h1_el:
                                    nombre_oferta = h1_el.get_text(strip=True)

                            # Detección de modalidad en el texto
                            text_lower = (nombre_oferta + " " + descripcion).lower()
                            if "híbrido" in text_lower or "hibrido" in text_lower:
                                modalidad = "Híbrido"
                            elif "remoto" in text_lower or "teletrabajo" in text_lower:
                                modalidad = "Remoto"
                            elif "presencial" in text_lower:
                                modalidad = "Presencial"

                            # Requisitos y palabras clave
                            tags = [t.get_text(strip=True) for t in job_soup.select(".tag, [class*='badge'], [class*='keyword']")]
                            if tags:
                                requisitos_texto = " | ".join(tags)

                    except Exception as e:
                        print(f"   [AVISO Magneto] Error al procesar detalle de {link}: {e}")

                    # Validar que la oferta sea relevante para Ciencia / Analítica de Datos
                    from src.processing.cleaner import es_oferta_relevante
                    if not es_oferta_relevante(nombre_oferta, descripcion):
                        continue

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
            time.sleep(random.uniform(1.0, 2.0))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas obtenidas: {len(self.data)}")
        return self.data
