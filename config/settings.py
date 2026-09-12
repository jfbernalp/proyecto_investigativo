import os
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de datos
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_ANALYTICS_DIR = DATA_DIR / "analytics"
DOCS_DIR = BASE_DIR / "docs"

# Rutas de archivos estándar
RAW_JOBS_FILE = DATA_RAW_DIR / "ofertas_consolidadas.xlsx"
PROCESSED_JOBS_FILE = DATA_PROCESSED_DIR / "ofertas_analizadas.xlsx"
ANALYTICS_DASHBOARD_FILE = DATA_ANALYTICS_DIR / "dataset_dashboard_salarios.xlsx"
MATRIZ_OFERTAS_CSV = DATA_ANALYTICS_DIR / "matriz_ofertas_dashboard.csv"
HABILIDADES_LARGO_CSV = DATA_ANALYTICS_DIR / "habilidades_largo_dashboard.csv"

# Base de datos relacional
DATABASE_FILE = DATA_DIR / "labor_market.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

# Encabezados HTTP estándar para emular navegadores reales
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://co.computrabajo.com/"
}

# Parámetros por defecto de scraping
DEFAULT_SEARCH_ROLES = [
    "cientifico-de-datos",
    "analista-de-datos"
]
DEFAULT_MAX_PAGES = 3
DEFAULT_REQUEST_TIMEOUT = 15
