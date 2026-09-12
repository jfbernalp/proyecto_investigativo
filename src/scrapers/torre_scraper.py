import requests
import time
import random
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante

class TorreScraper(BaseScraper):
    """
    Scraper / Consumidor API para el portal internacional Torre.ai (torre.ai / torre.co).
    Extrae ofertas técnicas, salarios en USD y habilidades requeridas.
    """

    BASE_URL = "https://torre.ai"
    SEARCH_API = "https://search.torre.co/opportunities/_search/"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        super().__init__(portal_name="Torre.ai", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Consulta ofertas en Torre.ai usando la API de búsqueda semántica.
        """
        role_skills = {
            "cientifico-de-datos": ["Data Science", "Machine Learning"],
            "analista-de-datos": ["Data Analytics", "Business Intelligence"],
            "ingeniero-de-datos": ["Data Engineering", "Big Data"]
        }
        skills_to_query = role_skills.get(role, ["Data Science"])

        self.data = []
        page = 0  # Torre usa paginación 0-indexed

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page < max_pages:
            url = f"{self.SEARCH_API}?page={page}&size=20&aggregate=false"
            print(f"\n---> [Página {page+1}/{max_pages}] Consultando Torre API...")

            # Construir filtro de búsqueda
            payload = {
                "and": [
                    {"status": {"code": "open"}}
                ]
            }
            if skills_to_query:
                payload["and"].append({
                    "or": [{"skill/role": {"text": s, "experience": "potential-to-develop"}} for s in skills_to_query]
                })

            try:
                response = self.session.post(url, headers=self.headers, json=payload, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page+1}.")
                    break

                json_data = response.json()
                results = json_data.get("results", [])

                if not results:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page+1}.")
                    break

                print(f"[{self.portal_name}] Se obtuvieron {len(results)} ofertas en página {page+1}. Evaluando relevancia...")

                for res in results:
                    nombre_oferta = res.get("objective", "")

                    # FILTRO TEMPRANO: Descartar cargos no relacionados
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    codigo = str(res.get("id", f"TOR_{len(self.data)+1}"))

                    # Empresas
                    orgs = res.get("organizations", [])
                    empresa = orgs[0].get("name", "Confidencial / No especificada") if orgs else "Confidencial"

                    # Ubicación
                    locations = res.get("locations", [])
                    ubicacion = ", ".join(locations[:2]) if locations else "Global / Remoto"

                    # Modalidad
                    modalidad = "Remoto" if res.get("remote", True) else "Presencial"

                    # Salario / Compensación
                    comp_info = res.get("compensation", {}).get("data", {})
                    salario = "A convenir / No especificado"
                    if isinstance(comp_info, dict):
                        currency = comp_info.get("currency", "USD")
                        min_a = comp_info.get("minAmount")
                        max_a = comp_info.get("maxAmount")
                        period = comp_info.get("periodicity", "monthly")

                        if min_a and max_a and min_a > 0:
                            salario = f"{currency} {min_a:,.0f} a {max_a:,.0f} ({period})".replace(",", ".")
                        elif min_a and min_a > 0:
                            salario = f"{currency} {min_a:,.0f} ({period})".replace(",", ".")

                    # Requisitos / Habilidades
                    skills_raw = res.get("skills", [])
                    skills_names = [s.get("name", "") for s in skills_raw if isinstance(s, dict)]
                    requisitos_texto = " | ".join([s for s in skills_names if s])

                    # Descripción o Tagline
                    tagline = res.get("tagline", "")
                    descripcion = tagline

                    # URL
                    slug = res.get("slug") or codigo
                    link = f"{self.BASE_URL}/jobs/{slug}"

                    self.data.append({
                        "Portal": self.portal_name,
                        "Rol_Buscado": role,
                        "Codigo": codigo,
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
                print(f"[{self.portal_name}] [EXCEPCIÓN] Error al consultar API en página {page+1}: {e}")
                break

            page += 1
            time.sleep(random.uniform(0.5, 1.2))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data
