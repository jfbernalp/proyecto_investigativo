"""
Genera (o rota) las credenciales del portal sin mostrarlas en pantalla.

- APPROVER_SECRET_KEY aleatoria (firma de sesiones).
- Una contraseña aleatoria por rol (visualizador, aprobador, administrador).
- En el .env se guardan SOLO los hashes PBKDF2 (PORTAL_HASH_<ROL>) y la clave de sesión.
- Las contraseñas legibles se escriben en un archivo aparte con permisos 600, para entregarlas
  a cada responsable y luego borrarlo.

Rotar la clave de sesión cierra todas las sesiones abiertas.
Solo usa la biblioteca estándar (se puede correr en el servidor sin dependencias).

Uso:  python3 scripts/generar_credenciales_portal.py <ruta_.env> <ruta_archivo_credenciales>
"""

import base64
import hashlib
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

ROLES = ("visualizador", "aprobador", "administrador")
ITERACIONES = 600_000


def hash_pbkdf2(password: str) -> str:
    sal = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${base64.b64encode(sal).decode()}${base64.b64encode(derivado).decode()}"


def actualizar_env(ruta: Path, valores: dict):
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    lineas = [l for l in lineas if l.split("=", 1)[0].strip() not in valores
              and l.split("=", 1)[0].strip() != "APROBADOR_PASSWORD"]
    lineas += [f"{k}={v}" for k, v in valores.items()]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    os.chmod(ruta, 0o600)


def main(ruta_env: Path, ruta_credenciales: Path):
    passwords = {rol: secrets.token_urlsafe(18) for rol in ROLES}
    valores = {"APPROVER_SECRET_KEY": secrets.token_urlsafe(48)}
    valores.update({f"PORTAL_HASH_{rol.upper()}": hash_pbkdf2(pw) for rol, pw in passwords.items()})
    actualizar_env(ruta_env, valores)

    ruta_credenciales.write_text(
        f"Credenciales del portal programático (generadas {datetime.now():%Y-%m-%d %H:%M}).\n"
        "Entregar a cada responsable por un canal privado y BORRAR este archivo.\n\n"
        + "".join(f"{rol:<14} usuario: {rol:<14} contraseña: {pw}\n" for rol, pw in passwords.items()),
        encoding="utf-8",
    )
    os.chmod(ruta_credenciales, 0o600)
    print(f"[OK] {ruta_env}: APPROVER_SECRET_KEY y {len(ROLES)} hashes actualizados (APROBADOR_PASSWORD eliminado).")
    print(f"[OK] Contraseñas legibles en {ruta_credenciales} (permisos 600).")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
