"""
Esquemas Pydantic para el Motor de Inteligencia Curricular con IA.
Garantizan que la salida de Google Gemini cumpla con los estándares del MEN (Decreto 1330)
y genere datos estructurados listos para persistencia y visualización.
"""

from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

class ModuloAsignatura(BaseModel):
    """Estructura de una asignatura o módulo formativo según estándares MEN."""
    nombre_modulo: str = Field(..., description="Nombre formal de la asignatura o módulo")
    semestre_sugerido: Optional[Union[int, str]] = Field(None, description="Semestre sugerido o N/A")
    creditos: int = Field(..., description="Número de créditos académicos (1 crédito = 48 horas)")
    horas_tfd: int = Field(..., description="Horas de Trabajo con Acompañamiento Docente (1/3)")
    horas_tti: int = Field(..., description="Horas de Trabajo Autónomo e Independiente (2/3)")
    stack_tecnologico: List[str] = Field(..., description="Herramientas y lenguajes enseñados (ej: AWS, Docker, Airflow)")
    resultados_aprendizaje_esperados_rae: List[str] = Field(
        ..., 
        description="Resultados de Aprendizaje Esperados (RAE) redactados con verbo de acción Taxonomía Bloom"
    )
    justificacion_demanda_laboral: str = Field(
        ..., 
        description="Justificación técnica sustentada en los datos del mercado laboral y vacantes analizadas"
    )

class DiagnosticoPrograma(BaseModel):
    """Diagnóstico FODA y brechas del programa actual de UniCafam vs Mercado."""
    resumen_ejecutivo: str = Field(..., description="Diagnóstico general de la pertinencia y empleabilidad del programa")
    puntuacion_competitividad_mercado: float = Field(..., description="Calificación de 0 a 100 de alineación con el mercado")
    fortalezas_principales: List[str] = Field(..., description="Áreas donde el currículo de UniCafam es sólido y competitivo")
    brechas_criticas_mercado: List[str] = Field(..., description="Brechas tecnológicas de alta demanda ausentes en la malla")
    riesgos_competitivos_egresado: List[str] = Field(..., description="Riesgos salariales y laborales para el egresado actual")

class PropuestaPrograma(BaseModel):
    """Propuesta de oferta académica para fortalecer el portafolio de UniCafam."""
    id_propuesta: str = Field(..., description="Identificador único (ej: PROP_ESP_DATA_ENG)")
    tipo_propuesta: str = Field(
        ..., description="Tipo de nivel formativo propuesto (Microcredencial, Electiva, Especialización, Maestría)"
    )
    nombre_programa: str = Field(..., description="Nombre comercial y académico sugerido")
    titulo_otorgado: str = Field(..., description="Denominación del título o certificación obtenida")
    nivel_academico: str = Field(..., description="Nivel formativo: Pregrado / Posgrado / Educación Continua")
    duracion_estimada: str = Field(..., description="Duración en semestres, meses u horas")
    creditos_totales: int = Field(..., description="Total de créditos académicos del programa")
    horas_totales: int = Field(..., description="Total de horas de formación (créditos * 48)")
    modalidad_sugerida: str = Field(
        ..., description="Modalidad de impartición (Presencial, Virtual, Híbrida / PAT)"
    )
    perfil_ingreso: str = Field(..., description="Perfil y prerrequisitos del aspirante")
    perfil_egreso: str = Field(..., description="Competencias y capacidades del graduado")
    roles_ocupacionales_objetivo: List[str] = Field(
        ..., description="Cargos del mercado a los que podrá aspirar (ej: Data Engineer, MLOps Specialist)"
    )
    impacto_salarial_proyectado: str = Field(
        ..., description="Estimación del incremento o rango salarial esperado para el egresado según datos del observatorio"
    )
    plan_estudios: List[ModuloAsignatura] = Field(
        ..., description="Lista de asignaturas o módulos estructurados que componen el programa"
    )

class PortafolioRecomendacionesIA(BaseModel):
    """Contenedor maestro de la evaluación y portafolio generado por la IA."""
    diagnostico: DiagnosticoPrograma
    propuestas: List[PropuestaPrograma]
