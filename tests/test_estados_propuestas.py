"""Máquina de estados de las propuestas, sobre una copia temporal del portafolio (no toca data/)."""
import json
import shutil

import pytest

from src.ai_curriculum import curriculum_engine as ce
from src.ai_curriculum.curriculum_schemas import DecisionAprobador, EstadoPropuesta
from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter

PORTAFOLIO_REAL = ce.OUTPUT_JSON_PATH


@pytest.fixture
def engine(tmp_path, monkeypatch):
    destino = tmp_path / "portafolio.json"
    shutil.copy(PORTAFOLIO_REAL, destino)
    datos = json.loads(destino.read_text(encoding="utf-8"))
    for i, p in enumerate(datos["propuestas"]):
        p["estado"] = "APROBADO" if i == 0 else "PENDIENTE_REVISION"
    destino.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(ce, "OUTPUT_JSON_PATH", destino)
    monkeypatch.setattr(ce, "VERSIONES_DIR", tmp_path / "versiones")
    monkeypatch.setattr(ce, "APROBADOS_DIR", tmp_path / "aprobados")
    # No regenerar los Excel del repositorio durante las pruebas
    monkeypatch.setattr(MIGExcelExporter, "exportar_portafolio_completo", lambda self, *a, **k: {})
    return ce.CurriculumIntelligenceEngine()


def _ids(engine):
    props = engine.cargar_portafolio().propuestas
    return props[0].id_propuesta, props[1].id_propuesta


def test_aprobar_pendiente_congela_excel(engine):
    _, pendiente = _ids(engine)
    p = engine.registrar_decision_formal(pendiente, DecisionAprobador.APROBAR, "Prueba", "Aprobador")
    assert p.estado == EstadoPropuesta.APROBADO
    assert ce.ruta_excel_aprobado(pendiente, p.version).exists()


def test_no_se_aprueba_dos_veces(engine):
    aprobada, _ = _ids(engine)
    with pytest.raises(ce.TransicionInvalidaError):
        engine.registrar_decision_formal(aprobada, DecisionAprobador.APROBAR, "Prueba", "Aprobador")


def test_no_se_ajusta_una_aprobada(engine):
    aprobada, _ = _ids(engine)
    with pytest.raises(ce.TransicionInvalidaError):
        engine.marcar_en_ajuste(aprobada)


def test_rechazo_guarda_motivo_y_se_puede_reabrir(engine):
    _, pendiente = _ids(engine)
    p = engine.registrar_decision_formal(pendiente, DecisionAprobador.RECHAZAR, "Prueba", "Aprobador",
                                         motivo_rechazo="Se traslapa con otro programa")
    assert p.estado == EstadoPropuesta.RECHAZADO and "traslapa" in p.motivo_rechazo
    p = engine.reabrir_propuesta(pendiente, "Prueba", "Aprobador")
    assert p.estado == EstadoPropuesta.PENDIENTE_REVISION
    assert p.historial_revisiones[-1].decision == "REAPERTURA_REVISION"


def test_ajuste_interrumpido_se_recupera_al_arrancar(engine):
    _, pendiente = _ids(engine)
    engine.marcar_en_ajuste(pendiente)
    assert ce.recuperar_ajustes_interrumpidos() == [pendiente]
    p = next(x for x in engine.cargar_portafolio().propuestas if x.id_propuesta == pendiente)
    assert p.estado == EstadoPropuesta.PENDIENTE_REVISION
    assert p.historial_revisiones[-1].decision == "ERROR_AJUSTE_IA"
    assert ce.recuperar_ajustes_interrumpidos() == []
