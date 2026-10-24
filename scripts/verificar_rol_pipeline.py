"""
Verifica los permisos de pipeline_observatorio conectándose CON ese rol (DATABASE_URL_PIPELINE).
Todo lo que escribe se hace dentro de transacciones que se revierten: no modifica datos.

Uso:  python scripts/verificar_rol_pipeline.py
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DatabaseManager  # noqa: E402  (carga .env)

resultados = []


def intentar(engine, sql: str, params=None) -> Exception | None:
    """Ejecuta en una transacción que siempre se revierte. Devuelve la excepción o None."""
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            for sentencia in sql.split(";;"):
                conn.execute(text(sentencia), params or {})
            return None
        except Exception as e:
            return e
        finally:
            tx.rollback()


def debe(nombre: str, permitido: bool, error: Exception | None):
    ok = (error is None) if permitido else (error is not None)
    resultados.append(ok)
    detalle = "" if ok or error is None else f"  ({str(getattr(error, 'orig', error)).splitlines()[0][:90]})"
    print(f"{'PASS' if ok else 'FAIL'} {'puede' if permitido else 'NO puede'}: {nombre}{detalle}")


def main():
    url = os.getenv("DATABASE_URL_PIPELINE")
    if not url:
        sys.exit("Falta DATABASE_URL_PIPELINE en .env (ejecutar scripts/crear_rol_pipeline.py)")
    eng = create_engine(url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1))

    with eng.connect() as c:
        print("Conectado como:", c.execute(text("SELECT current_user")).scalar())
    debe("inicializar DatabaseManager (sin DDL)", True, None if DatabaseManager(url) else RuntimeError())

    h = "SELECT id_vacante_hash FROM dim_ofertas LIMIT 1"
    # --- Lo que el pipeline necesita ---
    debe("leer el histórico", True, intentar(eng, "SELECT count(*) FROM fact_habilidades_historico"))
    debe("insertar en fact_extracciones_historico", True, intentar(eng,
        "INSERT INTO fact_extracciones_historico (id_vacante_hash, mes_periodo) VALUES ('prueba_rol', 209901)"))
    debe("insertar en fact_habilidades_historico", True, intentar(eng,
        "INSERT INTO fact_habilidades_historico (id_vacante_hash, habilidad, mes_periodo) VALUES ('prueba_rol', 'x', 209901)"))
    debe("insertar en ofertas_raw_historico", True, intentar(eng,
        "INSERT INTO ofertas_raw_historico (id_vacante_hash, mes_periodo) VALUES ('prueba_rol', 209901)"))
    debe("upsert de seguimiento en dim_ofertas", True, intentar(eng,
        f"INSERT INTO dim_ofertas (id_vacante_hash, ultima_fecha_deteccion) SELECT id_vacante_hash, CURRENT_DATE FROM ({h}) x "
        "ON CONFLICT (id_vacante_hash) DO UPDATE SET ultima_fecha_deteccion = EXCLUDED.ultima_fecha_deteccion, modalidad = 'Remoto'"))
    debe("recalcular un mes de agg_metricas_mensuales", True, intentar(eng,
        "DELETE FROM agg_metricas_mensuales WHERE mes_periodo = 209901"))
    debe("reemplazar tabla de foto actual (ofertas_raw)", True, intentar(eng,
        "DROP TABLE ofertas_raw;;CREATE TABLE ofertas_raw (x int)"))

    # --- Lo que NUNCA debe poder hacer ---
    for t in ("dim_ofertas", "fact_extracciones_historico", "fact_habilidades_historico", "ofertas_raw_historico"):
        debe(f"DELETE en {t}", False, intentar(eng, f"DELETE FROM {t}"))
        debe(f"TRUNCATE en {t}", False, intentar(eng, f"TRUNCATE {t} CASCADE"))
        debe(f"DROP de {t}", False, intentar(eng, f"DROP TABLE {t} CASCADE"))
    debe("UPDATE en fact_habilidades_historico", False, intentar(eng, "UPDATE fact_habilidades_historico SET habilidad = 'x'"))
    debe("cambiar primera_fecha_deteccion", False, intentar(eng, "UPDATE dim_ofertas SET primera_fecha_deteccion = '2000-01-01'"))
    debe("borrar usando la excepción de mantenimiento", False, intentar(eng,
        "SET LOCAL observatorio.permitir_mantenimiento = 'on';;DELETE FROM fact_extracciones_historico"))
    debe("deshabilitar triggers", False, intentar(eng, "ALTER TABLE fact_extracciones_historico DISABLE TRIGGER ALL"))
    debe("tocar propuestas curriculares", False, intentar(eng, "DELETE FROM dim_propuestas_curriculares_mig"))
    debe("tocar historial de auditoría HITL", False, intentar(eng, "DELETE FROM historial_revisiones_curriculo"))
    debe("crear roles", False, intentar(eng, "CREATE ROLE intruso"))

    print(f"\n{sum(resultados)}/{len(resultados)} verificaciones OK")
    sys.exit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
