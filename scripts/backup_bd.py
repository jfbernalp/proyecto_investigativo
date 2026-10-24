"""
Respaldo de la base de datos del observatorio (cada tabla legible → CSV comprimido).
Con el rol propietario respalda todo; con pipeline_observatorio, las tablas que ese rol puede modificar.

Se ejecuta automáticamente antes de cada corrida de GitHub Actions (queda como artefacto)
y puede correrse a mano:  python scripts/backup_bd.py [directorio_destino]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, normalizar_url_bd


def respaldar(destino_base: Path) -> Path:
    url = normalizar_url_bd(DATABASE_URL)
    # Conexión directa: un respaldo no debe crear tablas ni triggers
    engine = create_engine(url, pool_pre_ping=True)

    destino = destino_base / f"bd_{datetime.now():%Y%m%d_%H%M%S}"
    destino.mkdir(parents=True, exist_ok=True)
    resumen, omitidas = {}, []
    with engine.connect() as conn:
        legibles = {t for t in inspect(engine).get_table_names()
                    if conn.execute(text("SELECT has_table_privilege(:t, 'SELECT')"), {"t": f"public.{t}"}).scalar()}
    for tabla in sorted(inspect(engine).get_table_names()):
        if tabla not in legibles:
            # El rol del pipeline no ve las tablas curriculares; tampoco puede modificarlas
            omitidas.append(tabla)
            continue
        df = pd.read_sql_table(tabla, engine)
        df.to_csv(destino / f"{tabla}.csv.gz", index=False, compression="gzip")
        resumen[tabla] = len(df)
    (destino / "resumen.json").write_text(
        json.dumps({"tablas": resumen, "omitidas_sin_permiso": omitidas}, indent=2), encoding="utf-8")
    print(f"[BACKUP] {len(resumen)} tablas respaldadas en {destino}")
    if omitidas:
        print(f"[BACKUP] Omitidas (el rol no tiene SELECT): {', '.join(omitidas)}")
    for tabla, n in resumen.items():
        print(f"  - {tabla}: {n}")
    return destino


if __name__ == "__main__":
    respaldar(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DIR / "backups")
