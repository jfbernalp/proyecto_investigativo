"""
Migración única (24-oct-2026): instala las protecciones del histórico en la BD activa y
recupera lo que se había perdido. Todas las operaciones son aditivas: no borra ni modifica
filas de las tablas históricas.

  1. Crea ofertas_raw_historico y los triggers append-only (vía DatabaseManager).
  2. Recupera el crudo de 202609 y 202610 desde el historial de git (commits 3d6397a y 9eb25af).
  3. Reconstruye agg_metricas_mensuales para todos los meses (202609 se había perdido).
  4. Verifica que un DELETE sobre el histórico quede bloqueado.

Uso:  REQUIRE_REMOTE_DB=1 python scripts/aplicar_protecciones_bd.py
Hacer antes un respaldo:  python scripts/backup_bd.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DatabaseManager

CORRIDAS_EN_GIT = [
    ("3d6397a", "2026-09-12"),
    ("9eb25af", "2026-10-17"),
]


def leer_raw_de_git(commit: str) -> pd.DataFrame:
    contenido = subprocess.run(
        ["git", "show", f"{commit}:data/raw/ofertas_consolidadas.xlsx"],
        cwd=ROOT_DIR, capture_output=True, check=True
    ).stdout
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
        tmp.write(contenido)
        tmp.flush()
        return pd.read_excel(tmp.name)


def main():
    db = DatabaseManager()

    for commit, fecha in CORRIDAS_EN_GIT:
        nuevas = db.registrar_raw_historico(leer_raw_de_git(commit), fecha_extraccion=fecha)
        print(f"[RECUPERACIÓN] Crudo {fecha} (commit {commit}): +{nuevas}")

    print(f"[MÉTRICAS] Reconstruidas para: {db.recalcular_todas_las_metricas()}")

    with db.engine.connect() as conn:
        triggers = conn.execute(text(
            "SELECT event_object_table, COUNT(*) FROM information_schema.triggers "
            "WHERE trigger_name LIKE 'proteger_%' GROUP BY 1 ORDER BY 1"
        )).fetchall()
        print(f"[TRIGGERS] {triggers}")
        for tabla in ("dim_ofertas", "fact_extracciones_historico", "fact_habilidades_historico", "ofertas_raw_historico"):
            print(f"  {tabla}: {conn.execute(text(f'SELECT COUNT(*) FROM {tabla}')).scalar()}")

    try:
        with db.engine.begin() as conn:
            conn.execute(text("DELETE FROM fact_extracciones_historico WHERE mes_periodo = 202609"))
        raise SystemExit("[ERROR] El DELETE no fue bloqueado: revisar triggers.")
    except SystemExit:
        raise
    except Exception as e:
        print(f"[VERIFICADO] DELETE bloqueado por la BD: {str(getattr(e, 'orig', e)).splitlines()[0]}")


if __name__ == "__main__":
    main()
