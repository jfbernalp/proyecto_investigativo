"""
Deduplicación única del histórico (24-oct-2026).

Las re-ejecuciones del pipeline en el mismo mes insertaron la misma vacante varias veces.
Este script, en UNA transacción con la excepción de mantenimiento activada:
  1. fact_extracciones_historico: deja 1 fila por (vacante, mes) — la más reciente (mayor id).
  2. fact_habilidades_historico: deja 1 fila por (vacante, habilidad, mes) — la más reciente.
     Se conserva la unión de habilidades detectadas en cualquier corrida.
  3. Verifica que las filas resultantes = claves únicas previas y que ninguna vacante/mes
     desaparezca. Si algo no cuadra, revierte todo.
  4. Crea índices únicos para que la BD rechace duplicados en adelante.
Luego recalcula agg_metricas_mensuales.

Uso:  python scripts/deduplicar_historico.py            (simulación: hace todo y revierte)
      python scripts/deduplicar_historico.py --ejecutar (aplica)
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, DatabaseManager, SETTING_MANTENIMIENTO

TABLAS = {
    "fact_extracciones_historico": ("id_extraccion", ["id_vacante_hash", "mes_periodo"]),
    "fact_habilidades_historico": ("id_registro", ["id_vacante_hash", "habilidad", "mes_periodo"]),
}


def foto(conn, tabla, claves):
    cols = ", ".join(claves)
    return {
        "filas": conn.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar(),
        "claves": conn.execute(text(f"SELECT COUNT(*) FROM (SELECT DISTINCT {cols} FROM {tabla}) x")).scalar(),
        "vacantes_mes": conn.execute(text(
            f"SELECT COUNT(*) FROM (SELECT DISTINCT id_vacante_hash, mes_periodo FROM {tabla}) x")).scalar(),
    }


def main(ejecutar: bool):
    engine = create_engine(DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1))
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(text(f"SET LOCAL {SETTING_MANTENIMIENTO} = 'on'"))
            for tabla, (id_col, claves) in TABLAS.items():
                antes = foto(conn, tabla, claves)
                particion = ", ".join(claves)
                borradas = conn.execute(text(f"""
                    DELETE FROM {tabla} WHERE {id_col} IN (
                        SELECT {id_col} FROM (
                            SELECT {id_col}, ROW_NUMBER() OVER (PARTITION BY {particion} ORDER BY {id_col} DESC) AS rn
                            FROM {tabla}
                        ) x WHERE rn > 1
                    )
                """)).rowcount
                despues = foto(conn, tabla, claves)
                print(f"{tabla}: {antes['filas']} → {despues['filas']} filas (−{borradas}); "
                      f"claves únicas {antes['claves']} → {despues['claves']}; vacante/mes {antes['vacantes_mes']} → {despues['vacantes_mes']}")
                if not (despues["filas"] == antes["claves"] == despues["claves"]
                        and despues["vacantes_mes"] == antes["vacantes_mes"]):
                    raise RuntimeError(f"Verificación fallida en {tabla}: se revierte todo.")
                conn.execute(text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{tabla}_clave ON {tabla} ({particion})"))
                print(f"  índice único ux_{tabla}_clave creado")
            if ejecutar:
                tx.commit()
                print("[APLICADO] Deduplicación confirmada.")
            else:
                tx.rollback()
                print("[SIMULACIÓN] Todo verificado y revertido. Use --ejecutar para aplicar.")
        except Exception:
            tx.rollback()
            raise

    if ejecutar:
        meses = DatabaseManager().recalcular_todas_las_metricas()
        print(f"[MÉTRICAS] Recalculadas para {meses}")


if __name__ == "__main__":
    main("--ejecutar" in sys.argv)
