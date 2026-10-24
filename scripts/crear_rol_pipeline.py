"""
Crea (o rota la clave de) el rol de mínimo privilegio que usa el pipeline mensual.

pipeline_observatorio puede:
  - leer e insertar en el histórico (dim_ofertas, fact_*_historico, ofertas_raw_historico)
  - actualizar SOLO los campos de seguimiento de dim_ofertas (última detección, modalidad, seniority)
  - recalcular agg_metricas_mensuales (DELETE/INSERT por período)
  - reemplazar las 6 tablas de la "foto actual" (ofertas_raw, ofertas_procesadas, ...), de las que es dueño
y NO puede borrar, vaciar, modificar ni eliminar (DROP) las tablas históricas, ni tocar las curriculares.

Además revoca TRUNCATE/TRIGGER que anon/authenticated tenían sobre las tablas de public
(el proyecto no usa la API REST de Supabase).

Uso (con la conexión de propietario en DATABASE_URL):
    python scripts/crear_rol_pipeline.py
Escribe DATABASE_URL_PIPELINE en .env (nunca se imprime la clave).
"""

import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, TABLAS_PROTEGIDAS

ROL = "pipeline_observatorio"
TABLAS_FOTO_ACTUAL = (
    "ofertas_raw", "ofertas_procesadas", "valor_economico_habilidades",
    "matriz_correlaciones", "ofertas_modeladas_bi", "habilidades_desagregadas_bi",
)
SECUENCIAS = ("fact_extracciones_historico_id_extraccion_seq", "fact_habilidades_historico_id_registro_seq")


def url_para_rol(url_propietario: str, clave: str) -> str:
    """Misma conexión (pooler de Supabase), con usuario <rol>.<proyecto> y la clave nueva."""
    partes = urlsplit(url_propietario)
    usuario = partes.username or ""
    proyecto = usuario.split(".", 1)[1] if "." in usuario else None
    usuario_rol = f"{ROL}.{proyecto}" if proyecto else ROL
    host = partes.hostname + (f":{partes.port}" if partes.port else "")
    return urlunsplit((partes.scheme, f"{usuario_rol}:{quote(clave, safe='')}@{host}", partes.path, partes.query, ""))


def guardar_en_env(clave_env: str, valor: str):
    env = ROOT_DIR / ".env"
    lineas = [l for l in env.read_text(encoding="utf-8").splitlines() if not l.startswith(f"{clave_env}=")] if env.exists() else []
    lineas.append(f"{clave_env}={valor}")
    env.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main():
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
    engine = create_engine(url)
    clave = secrets.token_urlsafe(36)

    with engine.begin() as conn:
        existe = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": ROL}).fetchone()
        verbo = "ALTER" if existe else "CREATE"
        conn.execute(text(f"{verbo} ROLE {ROL} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD '{clave}'"))
        # Necesario para transferirle la propiedad de las tablas de foto actual
        conn.execute(text(f"GRANT {ROL} TO current_user"))

        conn.execute(text(f"GRANT USAGE, CREATE ON SCHEMA public TO {ROL}"))
        for tabla in TABLAS_PROTEGIDAS:
            conn.execute(text(f"REVOKE ALL ON {tabla} FROM {ROL}"))
            conn.execute(text(f"GRANT SELECT, INSERT ON {tabla} TO {ROL}"))
        conn.execute(text(f"GRANT UPDATE (ultima_fecha_deteccion, modalidad, seniority) ON dim_ofertas TO {ROL}"))
        conn.execute(text(f"GRANT USAGE ON SEQUENCE {', '.join(SECUENCIAS)} TO {ROL}"))
        conn.execute(text(f"GRANT SELECT, INSERT, DELETE ON agg_metricas_mensuales TO {ROL}"))
        for tabla in TABLAS_FOTO_ACTUAL:
            if conn.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{tabla}"}).scalar():
                conn.execute(text(f"ALTER TABLE {tabla} OWNER TO {ROL}"))

        roles_api = [r[0] for r in conn.execute(text(
            "SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')"
        ))]
        if roles_api:  # solo existen en Supabase
            conn.execute(text(f"REVOKE TRUNCATE, TRIGGER ON ALL TABLES IN SCHEMA public FROM {', '.join(roles_api)}"))

    guardar_en_env("DATABASE_URL_PIPELINE", url_para_rol(url, clave))
    print(f"[OK] Rol {ROL} {'actualizado' if existe else 'creado'}; DATABASE_URL_PIPELINE guardada en .env")


if __name__ == "__main__":
    main()
