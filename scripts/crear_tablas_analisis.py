"""
Crea las tablas de resultados del análisis de primas salariales (si no existen) y da permiso al rol del
pipeline para escribirlas (el análisis se repite en cada corte mensual desde GitHub Actions).

Tablas (una fila por habilidad/rol y por corte; se conserva la historia de cortes):
  analisis_primas_habilidad, analisis_primas_rol, analisis_tendencia_roles (rol y mes)

Uso (rol propietario, .env local):  python scripts/crear_tablas_analisis.py
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

COLUMNAS_COMUNES = """
    ultimo_corte DATE NOT NULL,
    fecha_analisis DATE NOT NULL,
    mercado TEXT NOT NULL,
    n_muestra INTEGER NOT NULL,
    n_ofertas INTEGER NOT NULL,
    prima_pct NUMERIC,
    ic95_inferior_pct NUMERIC,
    ic95_superior_pct NUMERIC,
    p NUMERIC,
    q_bh NUMERIC,
    concluyente BOOLEAN,
    evaluable BOOLEAN NOT NULL,
    r2_modelo NUMERIC
"""
DDL = [
    f"CREATE TABLE IF NOT EXISTS analisis_primas_habilidad (habilidad TEXT NOT NULL, {COLUMNAS_COMUNES}, "
    "PRIMARY KEY (ultimo_corte, mercado, habilidad))",
    f"CREATE TABLE IF NOT EXISTS analisis_primas_rol (rol TEXT NOT NULL, rol_referencia TEXT NOT NULL, {COLUMNAS_COMUNES}, "
    "PRIMARY KEY (ultimo_corte, mercado, rol))",
    """CREATE TABLE IF NOT EXISTS analisis_tendencia_roles (
        mes_periodo INTEGER NOT NULL, mes_anterior INTEGER NOT NULL, rol TEXT NOT NULL,
        fecha_analisis DATE NOT NULL, portales_comparados TEXT NOT NULL, portales_excluidos TEXT NOT NULL,
        n_ofertas INTEGER NOT NULL, n_total INTEGER NOT NULL, pct NUMERIC NOT NULL,
        n_ofertas_anterior INTEGER NOT NULL, n_total_anterior INTEGER NOT NULL, pct_anterior NUMERIC NOT NULL,
        cambio_pp NUMERIC NOT NULL, p NUMERIC, q_bh NUMERIC, estado TEXT NOT NULL,
        cortes_disponibles INTEGER NOT NULL, es_tendencia BOOLEAN NOT NULL,
        PRIMARY KEY (mes_periodo, rol))""",
]
TABLAS = ("analisis_primas_habilidad", "analisis_primas_rol", "analisis_tendencia_roles")


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    with engine.begin() as conn:
        for sentencia in DDL:
            conn.execute(text(sentencia))
        if conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'pipeline_observatorio'")).fetchone():
            for tabla in TABLAS:
                conn.execute(text(f"GRANT SELECT, INSERT, DELETE ON {tabla} TO pipeline_observatorio"))
            print("[OK] permisos de escritura para pipeline_observatorio")
    print(f"[OK] tablas {', '.join(TABLAS)}")


if __name__ == "__main__":
    main()
