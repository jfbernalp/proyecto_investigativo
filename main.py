import argparse
import sys
import os
import subprocess
from pathlib import Path

from config.settings import (
    RAW_JOBS_FILE,
    PROCESSED_JOBS_FILE,
    ANALYTICS_DASHBOARD_FILE,
    MATRIZ_OFERTAS_CSV,
    HABILIDADES_LARGO_CSV,
    DEFAULT_MAX_PAGES
)
from src.scrapers.computrabajo_scraper import CompuTrabajoScraper
from src.scrapers.elempleo_scraper import ElEmpleoScraper
from src.scrapers.magneto_scraper import MagnetoScraper
from src.scrapers.glassdoor_scraper import GlassdoorScraper
from src.scrapers.getonboard_scraper import GetOnBoardScraper
from src.scrapers.torre_scraper import TorreScraper
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.scrapers.talent_scraper import TalentScraper
from src.processing.requirements_parser import procesar_pipeline_nlp
from src.analytics.correlation_engine import ejecutar_analisis_correlacion_y_modelado
from src.database.db_manager import DatabaseManager
import pandas as pd

def run_scrapers(role="cientifico-de-datos", max_pages=DEFAULT_MAX_PAGES):
    """
    Ejecuta todos los scrapers disponibles (CompuTrabajo + ElEmpleo + Get on Board + Torre.ai + LinkedIn + Talent.com),
    consolida los registros y los guarda en Excel y en la Base de Datos.
    """
    db = DatabaseManager()
    
    scrapers = [
        CompuTrabajoScraper(),
        ElEmpleoScraper(),
        GetOnBoardScraper(),
        TorreScraper(),
        LinkedInScraper(),
        TalentScraper()
    ]
    
    todas_las_ofertas = []
    
    print("\n" + "=" * 70)
    print(f">>> EJECUTANDO SCRAPERS MULTI-PORTAL (ROL: {role} | {max_pages} PÁGS/PORTAL) <<<")
    print("=" * 70)

    for scraper in scrapers:
        try:
            ofertas = scraper.scrape(role=role, max_pages=max_pages)
            todas_las_ofertas.extend(ofertas)
        except Exception as e:
            print(f"[ERROR] Falló el scraper de {scraper.portal_name}: {e}")

    if not todas_las_ofertas:
        print("[ADVERTENCIA] No se recolectaron ofertas de ningún portal.")
        return

    from src.processing.cleaner import sanitizar_dataframe_para_excel
    df_raw = sanitizar_dataframe_para_excel(pd.DataFrame(todas_las_ofertas))
    
    # 1. Guardar en Excel en data/raw/
    RAW_JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_excel(RAW_JOBS_FILE, index=False)
    print(f"\n[OK] Datos crudos consolidados en: {RAW_JOBS_FILE}")

    # 2. Persistir en Base de Datos (Tabla 'ofertas_raw')
    db.guardar_dataframe(df_raw, table_name="ofertas_raw")
    print(f"[OK] Total ofertas recolectadas entre todos los portales: {len(df_raw)}")
    print(f"[OK] Distribución por portal:\n{df_raw['Portal'].value_counts().to_string()}")

def run_processing():
    db = DatabaseManager()
    
    # Intentar leer primero de la base de datos o del archivo crudo
    if RAW_JOBS_FILE.exists():
        df_raw = pd.read_excel(RAW_JOBS_FILE)
    else:
        df_raw = db.leer_tabla("ofertas_raw")

    if df_raw.empty:
        print(f"[ERROR] No hay datos crudos para procesar. Ejecuta primero '--scrape'.")
        return

    df_procesado = procesar_pipeline_nlp(df_raw, PROCESSED_JOBS_FILE)
    
    # Persistir en Base de Datos (Tabla 'ofertas_procesadas')
    db.guardar_dataframe(df_procesado, table_name="ofertas_procesadas")

def run_analytics():
    db = DatabaseManager()
    
    if not PROCESSED_JOBS_FILE.exists():
        print(f"[ERROR] No existe el archivo procesado: {PROCESSED_JOBS_FILE}. Ejecuta primero '--process'.")
        return

    df_modelado, df_valor, matriz_corr = ejecutar_analisis_correlacion_y_modelado(
        input_file=PROCESSED_JOBS_FILE,
        output_excel=ANALYTICS_DASHBOARD_FILE,
        output_matriz_csv=MATRIZ_OFERTAS_CSV,
        output_largo_csv=HABILIDADES_LARGO_CSV
    )

    # Leer formato largo para persistencia relacional
    df_largo = pd.read_csv(HABILIDADES_LARGO_CSV)

    # Persistir en Modelo Dimensional con Snapshot Histórico
    db.registrar_snapshot_historico(df_modelado, df_largo)

    # Persistir tablas analíticas adicionales en Base de Datos
    db.guardar_dataframe(df_valor, table_name="valor_economico_habilidades")
    
    # Matriz de correlación a formato tabular para BD
    matriz_db = matriz_corr.reset_index().rename(columns={"index": "Variable"})
    db.guardar_dataframe(matriz_db, table_name="matriz_correlaciones")
    
    print("\n[OK] Tablas analíticas e históricas actualizadas en la Base de Datos:")
    for t in db.listar_tablas():
        print(f"  - {t}")

def run_dashboard():
    dashboard_path = Path(__file__).resolve().parent / "src" / "dashboard" / "app.py"
    print(f"\n[INFO] Lanzando Dashboard interactivo conectado a la Base de Datos...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])

def main():
    parser = argparse.ArgumentParser(description="Pipeline Multi-Portal de Inteligencia Laboral & Base de Datos")
    parser.add_argument("--scrape", action="store_true", help="Ejecuta la extracción de ofertas en CompuTrabajo y ElEmpleo")
    parser.add_argument("--process", action="store_true", help="Ejecuta la limpieza y minería NLP de requisitos")
    parser.add_argument("--analyze", action="store_true", help="Ejecuta el análisis estadístico, correlaciones y BD")
    parser.add_argument("--dashboard", action="store_true", help="Lanza la aplicación web con el dashboard interactivo")
    parser.add_argument("--all", action="store_true", help="Ejecuta el pipeline multiportal completo de punta a punta")
    parser.add_argument("--role", type=str, default="cientifico-de-datos", help="Rol a scrapear (default: cientifico-de-datos)")
    parser.add_argument("--pages", type=int, default=DEFAULT_MAX_PAGES, help="Límite de páginas a consultar por portal")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.all:
        print("\n>>> INICIANDO PIPELINE MULTI-PORTAL COMPLETO DE INVESTIGACIÓN <<<")
        run_scrapers(role=args.role, max_pages=args.pages)
        run_processing()
        run_analytics()
        run_dashboard()
    else:
        if args.scrape:
            run_scrapers(role=args.role, max_pages=args.pages)
        if args.process:
            run_processing()
        if args.analyze:
            run_analytics()
        if args.dashboard:
            run_dashboard()

if __name__ == "__main__":
    main()
