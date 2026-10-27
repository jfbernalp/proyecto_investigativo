"""
Configuración común de las pruebas.

Las pruebas NUNCA tocan Supabase ni el servidor: DATABASE_URL apunta a un SQLite temporal y las
credenciales del portal son de prueba (generadas aquí, no las reales).
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="observatorio_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'pruebas.db'}"
os.environ.pop("REQUIRE_REMOTE_DB", None)
os.environ["GEMINI_API_KEY"] = "clave-de-prueba-no-real"
os.environ["APPROVER_SECRET_KEY"] = "s" * 48
os.environ["PORTAL_COOKIE_SECURE"] = "0"

from scripts.generar_credenciales_portal import hash_pbkdf2  # noqa: E402

PASSWORDS_PRUEBA = {
    "visualizador": "prueba-visualizador-1",
    "aprobador": "prueba-aprobador-1",
    "administrador": "prueba-administrador-1",
}
for _rol, _pw in PASSWORDS_PRUEBA.items():
    os.environ[f"PORTAL_HASH_{_rol.upper()}"] = hash_pbkdf2(_pw)
