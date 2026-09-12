import requests
import time
import random
from typing import List, Dict, Any, Optional
from src.scrapers.base_scraper import BaseScraper
from config.settings import DEFAULT_HEADERS, DEFAULT_REQUEST_TIMEOUT
from src.processing.cleaner import es_oferta_relevante

class GetOnBoardScraper(BaseScraper):
    """
    Scraper / Consumidor API para el portal tecnológico Get on Board (getonbrd.com).
    Extrae ofertas técnicas de Data Science, Machine Learning y Analytics directamente en JSON.
    """

    BASE_URL = "https://www.getonbrd.com"
    API_URL = "https://www.getonbrd.com/api/v0/search/jobs"

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        custom_headers = (headers or DEFAULT_HEADERS).copy()
        custom_headers["Accept"] = "application/json"
        super().__init__(portal_name="GetOnBoard", headers=custom_headers, timeout=timeout)
        self.session = requests.Session()

    def scrape(self, role: str = "cientifico-de-datos", max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Consulta las vacantes en Get on Board para el rol especificado usando su API pública.
        """
        query_map = {
            "cientifico-de-datos": "data scientist",
            "analista-de-datos": "data analyst",
            "ingeniero-de-datos": "data engineer"
        }
        search_query = query_map.get(role, role.replace("-", " "))

        self.data = []
        page = 1

        print("=" * 70)
        print(f"[{self.portal_name.upper()}] INICIANDO EXTRACCIÓN - ROL: {role} (LÍMITE: {max_pages} PÁGINAS)")
        print("=" * 70)

        while page <= max_pages:
            url = f"{self.API_URL}?query={search_query}&page={page}&per_page=20"
            print(f"\n---> [Página {page}/{max_pages}] Consultando: {url}")

            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[{self.portal_name}] [ERROR HTTP {response.status_code}] en página {page}.")
                    break

                json_data = response.json()
                items = json_data.get("data", [])

                if not items:
                    print(f"[{self.portal_name}] No se encontraron más ofertas en la página {page}.")
                    break

                print(f"[{self.portal_name}] Se obtuvieron {len(items)} ofertas de la API en página {page}. Evaluando relevancia...")

                for it in items:
                    attrs = it.get("attributes", {})
                    nombre_oferta = attrs.get("title", "")
                    
                    # FILTRO TEMPRANO: Descartar si el cargo no es del dominio de datos
                    if not es_oferta_relevante(nombre_oferta):
                        continue

                    codigo = str(it.get("id", f"GOB_{len(self.data)+1}"))
                    empresa = attrs.get("company", {}).get("data", {}).get("attributes", {}).get("name", "Confidencial / No especificada")
                    
                    # Ubicación y País
                    pais = attrs.get("country", "Latinoamérica")
                    ciudad = attrs.get("city", "")
                    ubicacion = f"{ciudad}, {pais}" if ciudad else pais

                    # Salario
                    min_s = attrs.get("min_salary")
                    max_s = attrs.get("max_salary")
                    if min_s and max_s:
                        # Salarios en Get on Board suelen venir en USD
                        salario = f"USD {min_s:,.0f} a {max_s:,.0f}".replace(",", ".")
                    elif min_s:
                        salario = f"USD {min_s:,.0f}".replace(",", ".")
                    else:
                        salario = "A convenir / No especificado"

                    # Modalidad
                    es_remoto = attrs.get("remote", False)
                    mod_str = attrs.get("remote_modality", "")
                    if es_remoto or "remote" in str(mod_str).lower():
                        modalidad = "Remoto"
                    elif "hybrid" in str(mod_str).lower() or "hibrido" in str(mod_str).lower():
                        modalidad = "Híbrido"
                    else:
                        modalidad = "Presencial"

                    # Descripción y Requisitos
                    descripcion = attrs.get("description", "")
                    skills_list = attrs.get("skills", {}).get("data", [])
                    skills_tags = [s.get("attributes", {}).get("name", "") for s in skills_list if isinstance(s, dict)]
                    requisitos_texto = " | ".join([s for s in skills_tags if s])

                    # URL pública
                    link = it.get("links", {}).get("public_url") or f"{self.BASE_URL}/jobs/{codigo}"

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
                print(f"[{self.portal_name}] [EXCEPCIÓN] Error al consultar API en página {page}: {e}")
                break

            page += 1
            time.sleep(random.uniform(0.5, 1.2))

        print(f"\n[{self.portal_name}] Extracción finalizada. Total ofertas relevantes obtenidas: {len(self.data)}")
        return self.data
