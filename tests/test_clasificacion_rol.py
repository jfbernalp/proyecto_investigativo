"""Clasificación de rol desde el título: palabras completas, frase de rol antes que tema y «Sin clasificar» sin defecto."""
import numpy as np
import pandas as pd
import pytest

from src.analytics import tendencia_roles as tr
from src.analytics.primas_salariales import estimar_roles
from src.processing.cleaner import (ROL_ANALISTA, ROL_BI, ROL_CIENTIFICO, ROL_DESARROLLADOR, ROL_INGENIERO, ROL_ML,
                                    ROL_SIN_CLASIFICAR, clasificar_rol_tecnico)


@pytest.mark.parametrize("titulo, rol", [
    ("Científico de Datos Senior", ROL_CIENTIFICO),
    ("Lead Data Scientist", ROL_CIENTIFICO),
    ("Ingeniero(a) de Datos - Bogotá", ROL_INGENIERO),
    ("Ingeniera/o de datos", ROL_INGENIERO),
    ("Ingeniero cloud de datos", ROL_INGENIERO),
    ("Big Data Platform Engineer", ROL_INGENIERO),
    ("Administrador de bases de datos SQL Server", ROL_INGENIERO),
    ("Machine Learning Engineer", ROL_ML),
    ("Ingeniero de inteligencia artificial", ROL_ML),
    ("Analista de BI", ROL_BI),
    ("Data Visualization Engineer", ROL_BI),
    ("Analista de datos junior", ROL_ANALISTA),
    ("Desarrollador backend", ROL_DESARROLLADOR),
])
def test_frases_de_rol(titulo, rol):
    assert clasificar_rol_tecnico(titulo) == rol


def test_palabras_completas_no_fragmentos():
    # Antes «ia» coincidía dentro de «gerencia» y «bi» dentro de «bilingüe»: todo terminaba en ML o BI
    assert clasificar_rol_tecnico("Asistente bilingüe de gerencia") == ROL_SIN_CLASIFICAR
    assert clasificar_rol_tecnico("Analista de datos bilingüe") == ROL_ANALISTA
    assert clasificar_rol_tecnico("Especialista en analítica de datos para la gerencia") == ROL_ANALISTA


def test_gana_el_cargo_que_va_primero():
    assert clasificar_rol_tecnico("Data Engineer - Data Science team") == ROL_INGENIERO
    assert clasificar_rol_tecnico("Analista de datos (Power BI, SQL)") == ROL_ANALISTA
    # una frase de rol gana a una palabra del tema aunque esta vaya antes
    assert clasificar_rol_tecnico("ETL y analista de datos") == ROL_ANALISTA


def test_sin_rol_reconocible_no_se_asigna_cientifico():
    for titulo in ("Head of Data", "Data Center Coordinator", "Data Entry Clerk", "Profesional de protección de datos",
                   "", None):
        assert clasificar_rol_tecnico(titulo) == ROL_SIN_CLASIFICAR


def test_tendencia_no_evalua_sin_clasificar():
    df = pd.DataFrame([{"mes_periodo": m, "portal": "A", "rol": r, "id_vacante_hash": f"{m}{r}{i}"}
                       for m, r, n in [(202609, "DS", 100), (202609, ROL_SIN_CLASIFICAR, 10),
                                       (202610, "DS", 100), (202610, ROL_SIN_CLASIFICAR, 90)] for i in range(n)])
    r = tr.comparar_meses(df, 202610)
    assert [f["rol"] for f in r["filas"]] == ["DS"] and r["n_ofertas"] == 190


def test_primas_por_rol_excluyen_sin_clasificar():
    rng = np.random.default_rng(0)
    roles = ["A"] * 60 + ["B"] * 50 + [ROL_SIN_CLASIFICAR] * 70        # el más frecuente no puede ser la referencia
    df = pd.DataFrame({"rol": roles, "nivel": rng.choice(["Junior", "Senior"], len(roles)), "portal": "P", "mes": "202610",
                       "log_salario": 15 + rng.normal(0, 0.2, len(roles))})
    r = estimar_roles(df, min_ofertas=10)
    assert r["referencia"] == "A" and r["n_sin_clasificar"] == 70 and r["n_ofertas"] == 110
    assert [f["rol"] for f in r["filas"]] == ["B"]


def test_controles_raros_no_rompen_hc3():
    from src.analytics.primas_salariales import estimar
    rng = np.random.default_rng(1)
    n = 120
    df = pd.DataFrame({"habilidades": [["SQL"] if i % 2 else [] for i in range(n)],
                       "rol": ["A"] * 70 + ["B"] * 48 + ["C", "D"],          # dos roles de una sola oferta
                       "nivel": rng.choice(["Junior", "Senior"], n), "portal": "P", "mes": "202610"})
    df["log_salario"] = 15 + 0.2 * df.habilidades.apply(len) + rng.normal(0, 0.1, n)
    fila = estimar(df)["filas"][0]
    assert np.isfinite(fila["ic95_superior_pct"]) and fila["concluyente"]
