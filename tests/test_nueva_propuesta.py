"""Nueva propuesta desde el portal: solo administrador, datos validados, una generación a la vez."""
import pytest
from fastapi.testclient import TestClient

import src.web.app as web
from tests.conftest import PASSWORDS_PRUEBA

SOLICITUD = {"tipo_propuesta": "Diplomado", "nivel_academico": "Educación Continua", "creditos": 4,
             "enfoque": "Gobierno de datos", "notas": ""}


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    web._intentos_fallidos.clear()
    web._generaciones.clear()
    monkeypatch.setattr(web, "sincronizar_db_background", lambda: None)


def _cliente(rol):
    c = TestClient(web.app)
    assert c.post("/api/auth/login", json={"username": rol, "password": PASSWORDS_PRUEBA[rol]}).status_code == 200
    return c


@pytest.mark.parametrize("rol", ["visualizador", "aprobador"])
def test_solo_el_administrador_genera(rol):
    c = _cliente(rol)
    assert c.post("/api/propuestas/nueva", json=SOLICITUD).status_code == 403
    assert c.get("/portal-programatico/nueva", follow_redirects=False).status_code == 302
    assert "Nueva propuesta" not in c.get("/portal-programatico").text


@pytest.mark.parametrize("cambio", [{"creditos": 0}, {"creditos": 99}, {"tipo_propuesta": "Doctorado"},
                                    {"nivel_academico": "Bachillerato"}, {"enfoque": "x" * 301}])
def test_valida_la_solicitud(cambio):
    assert _cliente("administrador").post("/api/propuestas/nueva", json={**SOLICITUD, **cambio}).status_code == 400


def test_genera_en_segundo_plano_y_una_a_la_vez(monkeypatch):
    llamadas = []

    class MotorFalso:
        def generar_propuesta_individual(self, solicitud, usuario, rol):
            llamadas.append((solicitud, usuario, rol))
            return type("P", (), {"id_propuesta": "PROP_09"})()

    monkeypatch.setattr(web, "_crear_engine", lambda: MotorFalso())
    c = _cliente("administrador")
    assert "Nueva propuesta" in c.get("/portal-programatico").text
    assert c.get("/portal-programatico/nueva").status_code == 200

    # Con una generación en curso no se acepta otra
    web._generaciones["x"] = {"id_trabajo": "x", "estado": "en_curso", "solicitante": "u", "tipo_propuesta": "t"}
    assert c.post("/api/propuestas/nueva", json=SOLICITUD).status_code == 409
    web._generaciones.clear()

    r = c.post("/api/propuestas/nueva", json=SOLICITUD)       # TestClient ejecuta la tarea al responder
    assert r.status_code == 202
    estado = c.get(f"/api/generaciones/{r.json()['id_trabajo']}").json()
    assert estado["estado"] == "lista" and estado["id_propuesta"] == "PROP_09"
    assert llamadas[0][0]["creditos"] == 4 and llamadas[0][2] == "Usuario Administrador"


def test_error_de_la_ia_no_expone_detalles(monkeypatch):
    class MotorQueFalla:
        def generar_propuesta_individual(self, *a):
            raise RuntimeError("clave secreta 123 en la traza")

    monkeypatch.setattr(web, "_crear_engine", lambda: MotorQueFalla())
    c = _cliente("administrador")
    r = c.post("/api/propuestas/nueva", json=SOLICITUD)
    estado = c.get(f"/api/generaciones/{r.json()['id_trabajo']}").json()
    assert estado["estado"] == "error" and "secreta" not in estado["error"]


def test_encargo_fija_formato_y_no_cambia_el_prompt_del_portafolio():
    from src.ai_curriculum import curriculum_engine as ce
    texto = ce.encargo_propuesta_individual(SOLICITUD, "Admin", "Usuario Administrador")
    assert "4 créditos = 192 horas" in texto and "Gobierno de datos" in texto and "exactamente 1 propuesta" in texto
    assert "exactamente estas 4 propuestas" in ce.ENCARGO_PORTAFOLIO
