import math

import pytest

from src.processing.cleaner import detectar_moneda_y_mercado, limpiar_salario_numerico, neutralizar_formula

LOCAL = "Mercado Local (Colombia - COP)"
INTERNACIONAL = "Mercado Internacional (Remoto - USD)"


@pytest.mark.parametrize("texto, esperado", [
    ("$ 7.000.000,00 (Mensual)", 7_000_000),          # CompuTrabajo
    ("$2,5 a $3 millones", 2_750_000),                # ElEmpleo
    ("$ 3.000.000 a $ 4.500.000 (Mensual)", 3_750_000),  # Magneto
])
def test_salarios_cop(texto, esperado):
    assert limpiar_salario_numerico(texto) == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["A convenir / No especificado", "Confidencial", None, ""])
def test_sin_salario_no_inventa_valor(texto):
    valor = limpiar_salario_numerico(texto)
    assert valor is None or (isinstance(valor, float) and math.isnan(valor))


def test_salario_usd_anual_se_convierte_a_mensual_cop():
    # 80.000 USD/año → 6.666,67 USD/mes; el valor exacto depende de la tasa configurada
    assert limpiar_salario_numerico("USD 70.000 a 90.000 (yearly)") > limpiar_salario_numerico("USD 70.000 (yearly)")


@pytest.mark.parametrize("portal, salario, moneda, mercado", [
    # Regresión: "No especificado" contiene "cad" y se clasificaba como dólar canadiense
    ("LinkedIn", "A convenir / No especificado", "COP", LOCAL),
    ("Talent.com", "A convenir / No especificado", "COP", LOCAL),
    ("Magneto", "$ 4.000.000 (Mensual)", "COP", LOCAL),
    ("GetOnBoard", "A convenir / No especificado", "USD", INTERNACIONAL),
    ("Remotive", "USD 70.000 a 80.000 (yearly)", "USD", INTERNACIONAL),
    ("LinkedIn", "CAD 90,000", "CAD", INTERNACIONAL),
    ("Remotive", "EUR 60.000 (yearly)", "EUR", INTERNACIONAL),
    ("LinkedIn", None, "COP", LOCAL),
])
def test_clasificacion_de_mercado(portal, salario, moneda, mercado):
    assert detectar_moneda_y_mercado(portal, salario) == (moneda, mercado)


@pytest.mark.parametrize("entrada, salida", [
    ("=HYPERLINK(\"http://x\")", "'=HYPERLINK(\"http://x\")"),
    ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
    ("@SUM(A1)", "'@SUM(A1)"),
    ("-cmd|calc", "'-cmd|calc"),
    ("-5", "-5"),                       # número negativo: no es fórmula
    ("- Experiencia en SQL", "- Experiencia en SQL"),  # viñeta
    ("Analista de datos", "Analista de datos"),
    (42, 42),
])
def test_neutralizar_formulas(entrada, salida):
    assert neutralizar_formula(entrada) == salida
