"""Roles emergentes/en descenso: solo con portales comparables y con prueba estadística."""
import pandas as pd

from src.analytics import tendencia_roles as tr


def _ofertas(filas):
    return pd.DataFrame([{"mes_periodo": m, "portal": p, "rol": r, "id_vacante_hash": f"{m}{p}{r}{i}"}
                         for m, p, r, n in filas for i in range(n)])


def test_cambio_grande_es_emergente_y_el_otro_desciende():
    df = _ofertas([(202609, "A", "DE", 20), (202609, "A", "DS", 180),
                   (202610, "A", "DE", 90), (202610, "A", "DS", 110)])
    r = tr.comparar_meses(df, 202610)
    estados = {f["rol"]: f["estado"] for f in r["filas"]}
    assert estados == {"DE": tr.EMERGENTE, "DS": tr.DESCENSO}
    assert not r["es_tendencia"] and "no es una tendencia" in r["lectura"]


def test_portal_nuevo_o_con_busqueda_cambiada_no_cuenta(monkeypatch):
    monkeypatch.setattr(tr, "CAMBIOS_DISENO_BUSQUEDA", {"B": [202610]})
    df = _ofertas([(202609, "A", "DE", 50), (202609, "A", "DS", 50), (202609, "B", "DS", 100),
                   (202610, "A", "DE", 50), (202610, "A", "DS", 50), (202610, "B", "DE", 100),
                   (202610, "C", "DE", 300)])
    r = tr.comparar_meses(df, 202610)
    assert r["portales_comparados"] == ["A"] and r["portales_excluidos_por_cambio_de_busqueda"] == ["B"]
    assert {f["estado"] for f in r["filas"]} == {tr.SIN_CAMBIO}


def test_rol_nuevo_y_pocas_ofertas():
    df = _ofertas([(202609, "A", "DS", 100), (202609, "A", "BI", 2),
                   (202610, "A", "DS", 100), (202610, "A", "BI", 3), (202610, "A", "MLOps", 4)])
    estados = {f["rol"]: f["estado"] for f in tr.comparar_meses(df, 202610)["filas"]}
    assert estados["MLOps"] == tr.NUEVO and estados["BI"] == tr.NO_EVALUABLE


def test_sin_mes_anterior():
    r = tr.comparar_meses(_ofertas([(202610, "A", "DS", 10)]), 202610)
    assert r["filas"] == [] and "anterior" in r["conclusion"]
