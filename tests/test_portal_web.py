"""Autenticación, límite de intentos y regla de oro (no mostrar cifras inventadas)."""
import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

import src.web.app as web
from tests.conftest import PASSWORDS_PRUEBA


@pytest.fixture(autouse=True)
def sin_intentos_previos():
    web._intentos_fallidos.clear()


@pytest.fixture
def cliente():
    return TestClient(web.app)


def _login(c, usuario, password):
    return c.post("/api/auth/login", json={"username": usuario, "password": password})


def _cookie(clave, datos):
    b = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode()
    return f"{b}.{hmac.new(clave.encode(), b.encode(), hashlib.sha256).hexdigest()}"


def test_contrasena_publica_antigua_rechazada(cliente):
    assert _login(cliente, "administrador", "Unicafam2026*").status_code == 401


def test_cada_rol_tiene_su_contrasena(cliente):
    assert _login(cliente, "administrador", PASSWORDS_PRUEBA["aprobador"]).status_code == 401
    r = _login(cliente, "decano@unicafam.edu.co", PASSWORDS_PRUEBA["aprobador"])
    assert r.status_code == 200 and r.json()["role_code"] == "aprobador"


def test_limite_de_intentos(cliente):
    for _ in range(web.MAX_INTENTOS_LOGIN):
        assert _login(cliente, "aprobador", "incorrecta").status_code == 401
    bloqueado = _login(cliente, "aprobador", PASSWORDS_PRUEBA["aprobador"])
    assert bloqueado.status_code == 429 and int(bloqueado.headers["Retry-After"]) > 0


def test_cookie_firmada_con_clave_antigua_rechazada(cliente):
    datos = {"usuario": "x", "rol": "x", "email": "x", "role_code": "administrador", "exp": int(time.time()) + 600}
    cliente.cookies.set(web.COOKIE_NAME, _cookie("unicafam-observatorio-hitl-secret-2026", datos))
    assert cliente.post("/api/propuestas/PROP_01/aprobar").status_code == 401


def test_token_vencido_o_sin_expiracion_rechazado(cliente):
    base = {"usuario": "x", "rol": "x", "email": "x", "role_code": "administrador"}
    for datos in ({**base, "exp": int(time.time()) - 1}, base):
        cliente.cookies.set(web.COOKIE_NAME, _cookie(web.SECRET_KEY, datos))
        assert cliente.get("/api/auth/me").json()["autenticado"] is False


def test_login_no_muestra_credenciales(cliente):
    html = cliente.get("/login").text
    assert "Unicafam2026" not in html and "seleccionarPerfil" not in html


def test_error_interno_no_expone_detalles():
    err = web._error_http(RuntimeError("password=secreto en /ruta/interna"))
    assert err.status_code == 500 and "secreto" not in err.detail


def test_kpis_sin_base_de_datos_no_inventan_cifras(monkeypatch):
    class BDCaida:
        def __init__(self, *a, **k):
            raise ConnectionError("sin conexión")
    monkeypatch.setattr(web, "DatabaseManager", BDCaida)
    kpis = web.obtener_kpis_mercado()
    assert kpis["disponible"] is False and kpis["motivo"]
    cifras = ("total_vacantes", "mediana_local_cop", "mediana_internacional_cop",
              "tasa_transparencia_pct", "fuentes_ultimo_mes", "competitividad_programa")
    assert all(kpis[c] is None for c in cifras)


def test_landing_muestra_dato_no_disponible(monkeypatch):
    monkeypatch.setattr(web, "obtener_kpis_mercado",
                        lambda: {"total_vacantes": None, "motivo": "La base de datos del observatorio no respondió."})
    html = TestClient(web.app).get("/").text
    assert "Dato no disponible" in html and "Tiempo Real" not in html and "317" not in html
