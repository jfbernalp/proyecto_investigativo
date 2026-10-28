"""
Crea o actualiza las vistas obs_* (superset/vistas_observatorio.sql) en la base activa.
Son de solo lectura: no modifican datos. Requiere el rol propietario (DATABASE_URL del .env local).

Uso:  python superset/aplicar_vistas.py
"""
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

SQL = (Path(__file__).parent / "vistas_observatorio.sql").read_text(encoding="utf-8")


def main():
    sentencias = [s.strip() for s in re.split(r";\s*\n", SQL) if "CREATE OR REPLACE VIEW" in s]
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    vistas = re.findall(r"VIEW (\w+)", SQL)
    with engine.begin() as conn:
        # Recrear en una sola transacción: CREATE OR REPLACE no permite insertar columnas en medio,
        # y así el tablero nunca queda sin vistas (si algo falla, no cambia nada).
        for vista in reversed(vistas):
            conn.execute(text(f"DROP VIEW IF EXISTS {vista}"))
        for sentencia in sentencias:
            conn.execute(text(sentencia))
            print("[OK]", re.search(r"VIEW (\w+)", sentencia).group(1))
        for vista in vistas:
            print(f"     {vista}: {conn.execute(text(f'SELECT COUNT(*) FROM {vista}')).scalar()} filas")


if __name__ == "__main__":
    main()
