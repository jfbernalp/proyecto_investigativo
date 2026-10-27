import pytest

from src.analytics.correlation_engine import tiene_habilidad
from src.processing.requirements_parser import extraer_habilidades_texto


@pytest.mark.parametrize("texto", [
    "Dominio de Python, R y SQL",
    "Programación en Python y/o R.",
    "Experiencia con RStudio",
    "Python | R | SQL",
])
def test_r_lenguaje_se_detecta(texto):
    assert "R" in extraer_habilidades_texto(texto)


@pytest.mark.parametrize("texto", [
    "Área de R&D de la compañía",
    "Equipo de I+D (R&D) en Bogotá",
    "Analista de datos para el área comercial",
])
def test_r_falsos_positivos(texto):
    assert "R" not in extraer_habilidades_texto(texto)


def test_nosql_no_cuenta_como_sql_en_el_texto():
    habilidades = extraer_habilidades_texto("Bases de datos NoSQL como MongoDB")
    assert "SQL" not in habilidades


def test_nosql_no_cuenta_como_sql_en_la_codificacion():
    # Regresión del hallazgo de auditoría: "SQL" in "Bases de Datos NoSQL" era True por subcadena
    assert not tiene_habilidad("Python, Bases de Datos NoSQL", "SQL")
    assert tiene_habilidad("Python, SQL, Bases de Datos NoSQL", "SQL")
    assert tiene_habilidad("Bases de Datos NoSQL", "Bases de Datos NoSQL")
    assert not tiene_habilidad(None, "SQL")
