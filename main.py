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
from src.database.db_manager import DatabaseManager
import pandas as pd

def run_scrapers(role="cientifico-de-datos", max_pages=DEFAULT_MAX_PAGES):
    """
    Ejecuta todos los scrapers disponibles (CompuTrabajo + ElEmpleo + Get on Board + LinkedIn + Talent.com + Magneto + Remotive),
    consolida los registros y los guarda en Excel y en la Base de Datos.
    """
    from src.scrapers.computrabajo_scraper import CompuTrabajoScraper
    from src.scrapers.elempleo_scraper import ElEmpleoScraper
    from src.scrapers.magneto_scraper import MagnetoScraper
    from src.scrapers.getonboard_scraper import GetOnBoardScraper
    from src.scrapers.linkedin_scraper import LinkedInScraper
    from src.scrapers.talent_scraper import TalentScraper
    from src.scrapers.remotive_scraper import RemotiveScraper
    db = DatabaseManager()
    
    # Torre.ai desactivado (24-oct-2026): su API pública de búsqueda responde 400 y el sitio usa
    # ahora una API interna de su app. Glassdoor tampoco se usa: Cloudflare + robots.txt lo impiden.
    # Remotive: API pública con atribución obligatoria (ver RemotiveScraper.ATRIBUCION).
    scrapers = [
        CompuTrabajoScraper(),
        ElEmpleoScraper(),
        GetOnBoardScraper(),
        LinkedInScraper(),
        TalentScraper(),
        MagnetoScraper(),
        RemotiveScraper()
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
        return None

    from src.processing.cleaner import sanitizar_dataframe_para_excel
    df_raw = sanitizar_dataframe_para_excel(pd.DataFrame(todas_las_ofertas))
    
    # 1. Guardar en Excel en data/raw/
    RAW_JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_excel(RAW_JOBS_FILE, index=False)
    print(f"\n[OK] Datos crudos consolidados en: {RAW_JOBS_FILE}")

    reportar_salud_scrapers(df_raw, db, [s.portal_name for s in scrapers])

    # 2. Persistir el crudo: histórico append-only por mes + tabla 'ofertas_raw' (solo la corrida actual)
    db.registrar_raw_historico(df_raw)
    db.guardar_dataframe(df_raw, table_name="ofertas_raw")
    print(f"[OK] Total ofertas recolectadas entre todos los portales: {len(df_raw)}")
    print(f"[OK] Distribución por portal:\n{df_raw['Portal'].value_counts().to_string()}")
    return df_raw

def reportar_salud_scrapers(df_raw, db, portales):
    """
    Tabla de salud por portal: ofertas recolectadas, cobertura de descripción (texto que alimenta
    la minería NLP) y comparación con el mes anterior. En GitHub Actions emite advertencias y
    agrega la tabla al resumen de la corrida, para que un scraper roto no pase inadvertido.
    """
    from datetime import datetime
    mes_actual = int(datetime.now().strftime("%Y%m"))
    previo = {}
    try:
        anterior = db.ejecutar_consulta(
            f"SELECT portal, COUNT(*) AS n FROM ofertas_raw_historico WHERE mes_periodo = "
            f"(SELECT MAX(mes_periodo) FROM ofertas_raw_historico WHERE mes_periodo < {mes_actual}) GROUP BY portal"
        )
        previo = dict(zip(anterior["portal"], anterior["n"])) if not anterior.empty else {}
    except Exception:
        pass

    filas, alertas = [], []
    for portal in portales:
        sub = df_raw[df_raw["Portal"] == portal] if not df_raw.empty else df_raw
        n = len(sub)
        con_texto = (sub["Descripcion"].fillna("").astype(str).str.len() >= 200).mean() if n else 0.0
        ant = int(previo.get(portal, 0))
        filas.append((portal, n, con_texto, ant))
        if n == 0:
            alertas.append(f"{portal}: 0 ofertas (scraper caído o bloqueado)")
        elif ant and n < 0.5 * ant:
            alertas.append(f"{portal}: {n} ofertas vs {ant} el mes anterior (caída >50%)")
        if n and con_texto < 0.5:
            alertas.append(f"{portal}: solo {con_texto:.0%} de ofertas con descripción (la minería de habilidades queda sin texto)")

    tabla = ["| Portal | Ofertas | Con descripción | Mes anterior |", "|---|---:|---:|---:|"]
    tabla += [f"| {p} | {n} | {t:.0%} | {a} |" for p, n, t, a in filas]
    print("\n[SALUD SCRAPERS]\n" + "\n".join(tabla))
    for alerta in alertas:
        print(f"[SALUD SCRAPERS] ⚠ {alerta}")
        if os.getenv("GITHUB_ACTIONS") == "true":
            print(f"::warning title=Salud de scrapers::{alerta}")
    resumen_gh = os.getenv("GITHUB_STEP_SUMMARY")
    if resumen_gh:
        with open(resumen_gh, "a", encoding="utf-8") as f:
            f.write("## Salud de scrapers\n\n" + "\n".join(tabla) + "\n\n")
            f.write("".join(f"- ⚠️ {a}\n" for a in alertas) or "Sin alertas.\n")

def run_processing():
    db = DatabaseManager()
    from src.processing.requirements_parser import procesar_pipeline_nlp
    
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
    from src.analytics.correlation_engine import ejecutar_analisis_correlacion_y_modelado
    
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

def run_curriculum_ai():
    print("\n" + "=" * 70)
    print(">>> EJECUTANDO MOTOR DE INTELIGENCIA CURRICULAR IA (UNICAFAM) <<<")
    print("=" * 70)
    from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
    engine = CurriculumIntelligenceEngine()
    engine.ejecutar_analisis_y_generacion()

def run_export_mig():
    print("\n" + "=" * 70)
    print(">>> EXPORTANDO OFERTA ACADÉMICA A EXCEL MATRIZ MIG (UNICAFAM) <<<")
    print("=" * 70)
    from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter
    exporter = MIGExcelExporter()
    res = exporter.exportar_portafolio_completo()
    print(f"\n[OK] Se generaron {res['total_propuestas']} propuestas en formato MIG:")
    print(f"  - Libro Maestro Consolidado: {res['master']}")
    for f in res["individuales"]:
        print(f"  - {f.name}")

def run_web(host="0.0.0.0", port=8000):
    print(f"\n[INFO] Iniciando Portal Web Institucional UniCafam en http://{host}:{port} ...")
    import uvicorn
    uvicorn.run("src.web.app:app", host=host, port=port, reload=True)

def abortar_si_no_hay_datos(df_raw):
    """
    Si el scraping no trajo nada, NO se continúa: el procesamiento leería el Excel crudo de una
    corrida anterior y lo registraría como snapshot del mes actual.
    """
    if df_raw is None or df_raw.empty:
        print("[ABORTADO] El scraping no recolectó ofertas; no se procesa ni se registra snapshot.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Pipeline Multi-Portal de Inteligencia Laboral & Base de Datos (UniCafam)")
    parser.add_argument("--scrape", action="store_true", help="Ejecuta la extracción de ofertas en CompuTrabajo y ElEmpleo")
    parser.add_argument("--process", action="store_true", help="Ejecuta la limpieza y minería NLP de requisitos")
    parser.add_argument("--analyze", action="store_true", help="Ejecuta el análisis estadístico, correlaciones y BD")
    parser.add_argument("--curriculum-ia", action="store_true", help="Ejecuta el motor de IA para diseñar nuevas propuestas curriculares")
    parser.add_argument("--export-mig", action="store_true", help="Exporta las propuestas académicas a formato Excel MATRIZ MIG")
    parser.add_argument("--dashboard", action="store_true", help="Lanza la aplicación Streamlit con el dashboard interactivo")
    parser.add_argument("--web", action="store_true", help="Lanza la Landing Page institucional UniCafam (FastAPI)")
    parser.add_argument("--port", type=int, default=8000, help="Puerto para el servidor web (default: 8000)")
    parser.add_argument("--all", action="store_true", help="Ejecuta el pipeline multiportal completo de punta a punta")
    parser.add_argument("--role", type=str, default="cientifico-de-datos", help="Rol a scrapear (default: cientifico-de-datos)")
    parser.add_argument("--pages", type=int, default=DEFAULT_MAX_PAGES, help="Límite de páginas a consultar por portal")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.all:
        # Pipeline de datos (el que corre GitHub Actions). No lanza el dashboard: Streamlit no
        # termina y dejaba la corrida colgada hasta el timeout. Usar --dashboard por separado.
        print("\n>>> INICIANDO PIPELINE MULTI-PORTAL COMPLETO DE INVESTIGACIÓN <<<")
        abortar_si_no_hay_datos(run_scrapers(role=args.role, max_pages=args.pages))
        run_processing()
        run_analytics()
    else:
        if args.scrape:
            df_raw = run_scrapers(role=args.role, max_pages=args.pages)
            if args.process or args.analyze:
                abortar_si_no_hay_datos(df_raw)
        if args.process:
            run_processing()
        if args.analyze:
            run_analytics()
        if args.curriculum_ia:
            run_curriculum_ai()
        if args.export_mig:
            run_export_mig()
        if args.dashboard:
            run_dashboard()
        if args.web:
            run_web(port=args.port)

if __name__ == "__main__":
    main()

