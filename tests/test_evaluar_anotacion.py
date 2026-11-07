"""Métricas de la evaluación contra el etiquetado manual: valores calculados a mano y flujo con planillas."""
import numpy as np
import pandas as pd
from openpyxl import load_workbook

import scripts.evaluar_anotacion as ev
import scripts.muestra_anotacion as mu


def test_kappa_cohen_calculado_a_mano():
    # acuerdo observado 0,75; esperado (2·1 + 2·3)/16 = 0,5 → kappa = (0,75 − 0,5)/(1 − 0,5) = 0,5
    assert abs(ev.kappa_cohen([1, 1, 0, 0], [1, 0, 0, 0]) - 0.5) < 1e-9
    assert ev.kappa_cohen([1, 0, 1], [1, 0, 1]) == 1.0
    assert ev.kappa_cohen([0, 0, 0], [0, 0, 0]) is None        # sin variación: no definido


def test_precision_recall_f1():
    p, r, f = ev.prf(8, 2, 4)
    assert (round(p, 3), round(r, 3), round(f, 3)) == (0.8, 0.667, 0.727)
    assert ev.prf(0, 0, 0) == (None, None, None)
    assert ev.prf(0, 3, 2)[2] == 0.0


def _planilla(tmp_path, nombre, filas):
    """Crea una planilla con el generador real y la llena como lo haría una persona anotadora."""
    base = pd.DataFrame([{"id_muestra": f"M{i:03d}", "portal": "X", "mes_periodo": 202611, "titulo": "t", "texto": "x"}
                         for i in range(1, len(filas) + 1)])
    ruta = tmp_path / nombre
    mu.planilla(base, ruta, "A")
    wb = load_workbook(ruta); ws = wb["anotacion"]
    cab = [c.value for c in ws[1]]
    for i, valores in enumerate(filas, start=2):
        for col, v in valores.items():
            ws.cell(row=i, column=cab.index(col) + 1, value=v)
    wb.save(ruta)
    return ruta


def test_lectura_y_validacion_de_planilla(tmp_path):
    ruta = _planilla(tmp_path, "a.xlsx", [
        {"rol": "Analista de Datos", "nivel": "Senior", "anios_minimos": "2,5", "SQL": "1", mu.EXCEL_CUALQUIER_NIVEL: 1,
         mu.EXCEL_AVANZADO_EXPLICITO: "1"},
        {"rol": "Científico", "nivel": "Junior", "Python": "x"},          # rol fuera de lista y valor no válido
    ])
    df, problemas = ev.leer_planilla(ruta)
    assert df.loc["M001", "anios"] == 2.5 and df.loc["M001", "SQL"] == 1
    assert df.loc["M001", "Excel Avanzado"] == 1 and df.loc["M001", "Excel avanzado explícito"] == 1
    assert df.loc["M002", "Python"] == 0 and np.isnan(df.loc["M002", "anios"])
    assert any("M002: rol" in p for p in problemas) and any("M002: valor no válido" in p for p in problemas)


def test_evaluacion_y_acuerdo(tmp_path):
    filas = [{"rol": "Analista de Datos", "nivel": "Senior", "anios_minimos": 4, "SQL": 1, "Python": 1},
             {"rol": "Ingeniero de Datos", "nivel": "No se indica", "Azure": 1},
             {"rol": "No es del tema", "nivel": "No se indica"}]
    A, _ = ev.leer_planilla(_planilla(tmp_path, "a.xlsx", filas))
    B, _ = ev.leer_planilla(_planilla(tmp_path, "b.xlsx", filas[:2]))
    ac = ev.acuerdo(A, B)
    assert ac["n_ofertas"] == 2 and ac["rol"]["acuerdo"] == 1.0 and ac["habilidades"]["SQL"]["acuerdo"] == 1.0

    # Sistema: acierta SQL, inventa AWS en la primera oferta, se le escapa Python y Azure
    sis = pd.DataFrame({"relevante": [True, True, False], "rol": ["Analista de Datos", "Científico de Datos", "No es del tema"],
                        "anios": [4.0, np.nan, np.nan], "nivel": ["Senior", "No se indica", "No se indica"]},
                       index=A.index)
    for h in ev.HABILIDADES:
        sis[f"pub::{h}"] = 0; sis[f"rec::{h}"] = 0
    sis.loc["M001", ["pub::SQL", "pub::AWS"]] = 1
    r = ev.evaluar(A, sis, reps=50, rng=np.random.default_rng(0))
    h = r["habilidades_publicado"]
    assert h["por_habilidad"]["SQL"] == {"positivos_referencia": 1, "tp": 1, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert h["por_habilidad"]["AWS"]["fp"] == 1 and h["por_habilidad"]["Azure"]["fn"] == 1
    # micro: tp 1, fp 1, fn 2 → P 0,5 · R 0,333
    assert h["micro"]["precision"] == 0.5 and h["micro"]["recall"] == 0.333
    assert r["rol"]["exactitud"] == round(2 / 3, 3)
    assert r["filtro_relevancia"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert r["anios"]["exactos_cuando_ambos"] == 1.0
