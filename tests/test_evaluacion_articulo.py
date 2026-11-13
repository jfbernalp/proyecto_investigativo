"""Piezas de las evaluaciones del Artículo 1: extractores de robustez, métricas ponderadas de E4 y prompt sin contexto."""
import pandas as pd

import scripts.evaluacion_ia as ia
import scripts.robustez_primas as rp


def test_nivel_educativo_y_sector():
    assert rp.nivel_educativo("Profesional en sistemas, deseable maestría") == "Posgrado (maestría o doctorado)"
    assert rp.nivel_educativo("Tecnólogo en análisis de datos") == "Técnico o tecnólogo"
    assert rp.nivel_educativo("Experiencia con SQL") == "No se indica"
    # «Educación:» es el encabezado de requisitos, no el sector
    assert rp.sector("Educación: profesional. Empresa del sector bancario y de seguros") == "Financiero y seguros"
    assert rp.sector("Analista de datos") == "No identificado"


def test_rango_salario():
    assert rp.rango_salario("$3,5 a $4 millones") == (3_500_000, 4_000_000)
    assert rp.rango_salario("Más de $21 millones") is None
    assert rp.rango_salario("$ 7.000.000,00 (Mensual)") is None


def test_metricas_e4_ponderadas():
    # Estratos: 1 marcada (población 1), 2 revisadas (población 20), 2 no revisadas (población 100)
    df = pd.DataFrame({
        "estrato": ["marcada", "revisada", "revisada", "no revisada", "no revisada"],
        "es_cifra_de_mercado": ["Sí", "Sí", "Sí", "Sí", "No"],
        "respaldo": ["Sin respaldo", "Respaldada", "Mal atribuida", "Sin respaldo", None]})
    m = ia.metricas_e4(df, {"marcada": 1, "revisada": 10, "no revisada": 50})
    # mercado = 1 + 10 + 10 + 50 = 71; problema = 1 + 10 + 50 = 61; marcadas con problema = 1
    assert m["cifras_de_mercado_estimadas"] == 71 and m["pct_problema"] == round(61 / 71, 3)
    assert m["precision_marcas"] == 1.0 and m["recall_marcas"] == round(1 / 61, 3)
    assert m["cobertura_revision"] == round(21 / 71, 3)


def test_bloque_de_datos_se_quita_completo():
    prompt = ("intro\n" + "=" * 5 + "\nDATOS DEL OBSERVATORIO LABORAL (x)\n" + "=" * 5 + "\n45,2 % SQL\nREGLAS\n"
              + "=" * 5 + "\nFOCO ESTRATÉGICO:\nfin")
    sin, n = ia.BLOQUE_DATOS.subn("", prompt)
    assert n == 1 and "45,2" not in sin and "REGLAS" not in sin and "FOCO ESTRATÉGICO" in sin
