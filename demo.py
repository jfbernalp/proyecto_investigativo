import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd

# ==============================================================================
# CONFIGURACIÓN INICIAL Y PARÁMETROS
# ==============================================================================

# URL base y plantilla de búsqueda para "científico de datos" en Colombia
BASE_URL = "https://co.computrabajo.com"
SEARCH_URL = "https://co.computrabajo.com/trabajo-de-cientifico-de-datos?p="

# Límite máximo de páginas a scrapear (puedes aumentar o dejar en None para extraer todo)
MAX_PAGES = 5

# Inicializamos una sesión HTTP para reutilizar conexiones y mantener cookies
session = requests.Session()

# Encabezados HTTP (Headers) para simular la navegación de un usuario real desde un navegador moderno.
# Esto evita que el servidor responda con un error HTTP 403 (Forbidden).
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://co.computrabajo.com/"
}

# Estructura de almacenamiento temporal para las ofertas extraídas
data = []
page = 1

print("=" * 70)
print("INICIANDO PROCESO DE EXTRACCIÓN DE OFERTAS - COMPUTRABAJO")
print("=" * 70)

# ==============================================================================
# BUCLE PRINCIPAL DE PAGINACIÓN
# ==============================================================================

while True:
    # Verificación de límite de páginas (si está configurado)
    if MAX_PAGES and page > MAX_PAGES:
        print(f"\n[INFO] Se alcanzó el límite de páginas configurado ({MAX_PAGES}).")
        break

    url = f"{SEARCH_URL}{page}"
    print(f"\n---> [PÁGINA {page}] Consultando: {url}")

    try:
        # Petición GET a la página del listado
        response = session.get(url, headers=headers, timeout=15)

        # ----------------------------------------------------------------------
        # VALIDACIÓN DE CÓDIGOS DE ESTADO HTTP
        # ----------------------------------------------------------------------
        if response.status_code != 200:
            print(f"[ERROR HTTP {response.status_code}] No se pudo cargar la página {page}.")
            if response.status_code == 403:
                print("   Motivo: 403 Forbidden (Acceso denegado / Bloqueo por User-Agent o IP).")
            elif response.status_code == 404:
                print("   Motivo: 404 Not Found (Página no encontrada o fin de listado).")
            elif 500 <= response.status_code <= 599:
                print(f"   Motivo: Error del servidor web ({response.status_code}).")
            break  # Detenemos la paginación si la página falla

        # Parseo del contenido HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Seleccionamos todas las tarjetas de ofertas en el listado
        offers = soup.select("article[data-id]")

        # Si no encontramos ofertas, asumimos que llegamos al final del catálogo
        if len(offers) == 0:
            print(f"[INFO] No se encontraron más ofertas en la página {page}. Fin de la búsqueda.")
            break

        print(f"[OK] Se encontraron {len(offers)} ofertas en la página {page}. Procesando...")

        # ======================================================================
        # EXTRACCIÓN DE CADA OFERTA DE EMPLEO
        # ======================================================================
        for idx, offer in enumerate(offers, start=1):
            codigo = offer.get("data-id", "N/A")

            # 1. Título y enlace de la oferta
            link_elem = offer.select_one("h2 a.js-o-link, h1 a.js-o-link, a.js-o-link") or offer.find("a")
            if not link_elem:
                print(f"   [AVISO] No se pudo encontrar enlace para el elemento {idx} (ID: {codigo}). Saltando...")
                continue

            nombre_oferta = link_elem.get_text(strip=True)
            href = link_elem.get("href", "")
            link = BASE_URL + href if href.startswith("/") else href

            # 2. Nombre de la empresa
            empresa_elem = offer.select_one("p a[offer-grid-article-company-url], p.fc_base a")
            empresa = empresa_elem.get_text(strip=True) if empresa_elem else "Confidencial / No especificada"

            # 3. Ubicación (Ciudad / Departamento)
            ubicacion_elem = offer.select_one("p.fs16 span.mr10")
            ubicacion = ubicacion_elem.get_text(strip=True) if ubicacion_elem else "No especificada"

            # 4. Etiquetas adicionales (Salario, Modalidad, etc.)
            badges = [s.get_text(strip=True) for s in offer.select("div.fs13 span.dIB")]

            salario = "A convenir / No especificado"
            modalidad = "No especificada"

            for badge in badges:
                if "$" in badge or "Mensual" in badge:
                    salario = badge
                elif any(m in badge.lower() for m in ["remoto", "presencial", "híbrido", "hibrido"]):
                    modalidad = badge

            # 5. Fecha de publicación relativa
            fecha_elem = offer.select_one("p.fc_aux")
            fecha_publicacion = fecha_elem.get_text(strip=True) if fecha_elem else "No especificada"

            print(f"   ({idx}/{len(offers)}) Procesando: {nombre_oferta[:40]}... | Empresa: {empresa[:20]}")

            # Pausa aleatoria entre peticiones para no saturar el servidor
            time.sleep(random.uniform(0.8, 1.8))

            # ------------------------------------------------------------------
            # CONSULTA A LA PÁGINA DE DETALLE (DESCRIPCIÓN Y REQUISITOS)
            # ------------------------------------------------------------------
            descripcion = ""
            requisitos_texto = ""

            try:
                job_response = session.get(link, headers=headers, timeout=15)

                if job_response.status_code != 200:
                    print(f"      [ERROR HTTP {job_response.status_code}] en detalle de oferta: {link}")
                else:
                    job_soup = BeautifulSoup(job_response.text, "html.parser")

                    # Extracción de la descripción completa
                    desc_elem = job_soup.find("p", class_="mbB")
                    if desc_elem:
                        descripcion = desc_elem.get_text(separator="\n", strip=True)

                    # Extracción de la lista de requerimientos
                    req_list = []
                    req_elem = job_soup.find("ul", class_="disc mbB")
                    if req_elem:
                        for li in req_elem.find_all("li"):
                            req_list.append(li.get_text(strip=True))

                    requisitos_texto = " | ".join(req_list)

            except requests.exceptions.RequestException as e:
                print(f"      [EXCEPCIÓN DE RED] Error al conectar con detalle de oferta {codigo}: {e}")

            # Agregamos el registro estructurado para el análisis de datos
            data.append({
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
        print(f"[EXCEPCIÓN CRÍTICA] Error de conexión en la página {page}: {e}")
        break

    # Avanzar a la siguiente página
    page += 1

    # Pausa de cortesía entre páginas
    time.sleep(random.uniform(2, 4))

# ==============================================================================
# CONVERSIÓN A DATAFRAME Y EXPORTACIÓN A EXCEL
# ==============================================================================
print("\n" + "=" * 70)
print("FINALIZACIÓN DEL SCRAPING - GUARDANDO DATOS")
print("=" * 70)

if data:
    df = pd.DataFrame(data)
    nombre_archivo = "ofertas_computrabajo.xlsx"
    df.to_excel(nombre_archivo, index=False)
    print(f"[EXITO] Se extrajeron {len(df)} ofertas con éxito.")
    print(f"[ARCHIVO] Guardado en: {nombre_archivo}")
    print(f"[COLUMNAS] {list(df.columns)}")
else:
    print("[ADVERTENCIA] No se recolectaron datos. Revisa los mensajes de error mostrados en consola.")
