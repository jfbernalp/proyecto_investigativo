import pytest

from src.processing.seniority import (
    determinar_seniority, extraer_anios_experiencia, nivel_por_anios, nivel_por_titulo,
)


@pytest.mark.parametrize("texto, anios", [
    ("Universidad | 3 años de experiencia | Idiomas: Inglés", 3),
    ("Cuenta con 3 a 5 años de experiencia en entidades financieras", 3),
    ("Mínimo 2 años de experiencia profesional, con al menos 1 año en BI", 2),   # el primero es el general
    ("Excel avanzadoExperiencia: 2 años en análisis de datos", 2),
    ("personal con experiencia mínima de 3 años para el cargo", 3),
    ("Experiencia laboral de 1 a 3 años en análisis de datos", 1),
    ("cuentas con 6 meses de experiencia (prácticas)", 0.5),
    ("Menos de 1 año de experiencia", 0),
    ("Sin experiencia, formación en estadística", 0),
    ("5+ years of experience with Spark", 5),
    ("at least 4 years building data pipelines", 4),
])
def test_anios_explicitos(texto, anios):
    assert extraer_anios_experiencia(texto) == pytest.approx(anios)


@pytest.mark.parametrize("texto", [
    "Somos una empresa con más de 30 años de experiencia en el sector",
    "Buscamos un profesional con experiencia en planeación de medios",   # dice experiencia, no cuánta
    "Experiencia en NetworkX, Neo4j y Gephi",
    "",
    None,
])
def test_no_inventa_anios(texto):
    # Regresión: antes, mencionar "experiencia" sin número asignaba 1 año
    assert extraer_anios_experiencia(texto) is None


@pytest.mark.parametrize("anios, nivel", [
    (0, "Junior"), (0.5, "Junior"), (1, "Junior"), (1.5, "Junior"), (2, "Semi-Senior"), (3, "Semi-Senior"),
    (3.5, "Semi-Senior"), (4, "Senior"), (5.5, "Senior"), (6, "Líder"), (None, None),
])
def test_rangos_contiguos(anios, nivel):
    # Regresión: 1,5 y 3,5 años caían en "Lead / Principal (> 5 años)"
    assert nivel_por_anios(anios) == nivel


@pytest.mark.parametrize("titulo, nivel", [
    ("Científico de Datos Junior", "Junior"),
    ("INGENIERO DE DATOS SENIOR", "Senior"),
    ("Practicante Analisis de Datos", "Practicante"),
    ("Aprendiz análisis de datos 1626532605-2", "Practicante"),
    ("212328-LIDER CIENCIA DE DATOS MERCADEO", "Líder"),
    ("Data Engineer Semi Senior", "Semi-Senior"),
    ("Analista de datos", None),
])
def test_nivel_por_titulo(titulo, nivel):
    assert nivel_por_titulo(titulo) == nivel


def test_prioridad_y_fuente():
    oferta = {"Nombre Oferta": "Científico de Datos Senior", "Descripcion": "Mínimo 2 años de experiencia"}
    assert determinar_seniority(oferta) == (2, "Semi-Senior", "años explícitos")
    ambigua = {"Nombre Oferta": "Analista", "Criterios_detalle": {"Nivel de antigüedad": "Intermedio"}}
    assert determinar_seniority(ambigua) == (None, "No especificado", "no especificado")
    assert determinar_seniority({"Nombre Oferta": "Analista Junior"}) == (None, "Junior", "título")
    assert determinar_seniority({"Nombre Oferta": "Analista",
                                 "Criterios_detalle": {"Nivel de antigüedad": "Sin experiencia"}}) == (None, "Junior", "portal")
    assert determinar_seniority({"Nombre Oferta": "Analista de datos"}) == (None, "No especificado", "no especificado")


def test_parse_requisitos_no_inventa_experiencia():
    from src.processing.requirements_parser import parse_requisitos_columna
    assert parse_requisitos_columna("Universidad | Experiencia en Python | Idiomas: Inglés")["Anios_Experiencia"] is None
    assert parse_requisitos_columna("Universidad | 3 años de experiencia")["Anios_Experiencia"] == 3


@pytest.mark.parametrize("anios, etiqueta", [
    (1.5, "Junior / Trainee (0-1 años)"), (3.5, "Semi-Senior (2-3 años)"), (5.5, "Senior (4-5 años)"),
    (6, "Lead / Principal (> 5 años)"), (None, "No especificado"),
])
def test_categorizar_seniority_contiguo(anios, etiqueta):
    from src.processing.cleaner import categorizar_seniority
    assert categorizar_seniority(anios) == etiqueta
