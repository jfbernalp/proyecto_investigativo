"""
Respaldo completo de la base de datos del observatorio (todas las tablas → CSV comprimido).

Se ejecuta automáticamente antes de cada corrida de GitHub Actions (queda como artefacto)
y puede correrse a mano:  python scripts/backup_bd.py [directorio_destino]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL


def respaldar(destino_base: Path) -> Path:
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    url = url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
    # Conexión directa: un respaldo no debe crear tablas ni triggers
    engine = create_engine(url, pool_pre_ping=True)

    destino = destino_base / f"bd_{datetime.now():%Y%m%d_%H%M%S}"
    destino.mkdir(parents=True, exist_ok=True)
    resumen = {}
    for tabla in sorted(inspect(engine).get_table_names()):
        df = pd.read_sql_table(tabla, engine)
        df.to_csv(destino / f"{tabla}.csv.gz", index=False, compression="gzip")
        resumen[tabla] = len(df)
    (destino / "resumen.json").write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    print(f"[BACKUP] {len(resumen)} tablas respaldadas en {destino}")
    for tabla, n in resumen.items():
        print(f"  - {tabla}: {n}")
    return destino


if __name__ == "__main__":
    respaldar(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DIR / "backups")
