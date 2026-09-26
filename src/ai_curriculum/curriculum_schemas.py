"""
Esquemas Pydantic para el Motor de Inteligencia Curricular con IA.
Garantizan que la salida de Google Gemini cumpla con los estándares del MEN (Decreto 1330)
y genere datos estructurados listos para persistencia y visualización.
"""

from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

class ModuloAsignatura(BaseModel):
    """Estructura de una asignatura o módulo formativo según estándares MEN y MIG."""
    numero_modulo: Optional[int] = Field(None, description="Número ordinal del módulo (1, 2, ...)")
    nombre_modulo: str = Field(..., description="Nombre formal de la asignatura o módulo")
    semestre_sugerido: Optional[Union[int, str]] = Field(None, description="Semestre sugerido o N/A")
    creditos: int = Field(2, description="Número de créditos académicos (1 crédito = 48 horas)")
    horas_tfd: int = Field(32, description="Horas de Trabajo con Acompañamiento Docente (1/3)")
    horas_tti: int = Field(64, description="Horas de Trabajo Autónomo e Independiente (2/3)")
    horas_totales_modulo: Optional[int] = Field(None, description="Total de horas del módulo (TFD + TTI)")
    contenido_detallado: Optional[str] = Field(
        None, 
        description="Contenido temático detallado del módulo (unidades temáticas, temas, subtemas y tecnologías aplicadas)"
    )
    cronograma_fechas: Optional[str] = Field(
        None,
        description="Fechas estimadas o semanas de impartición (ej: Semanas 1 a 4 / Sábados)"
    )
    stack_tecnologico: List[str] = Field(default_factory=list, description="Herramientas y lenguajes enseñados (ej: AWS, Docker, Airflow)")
    resultados_aprendizaje_esperados_rae: List[str] = Field(
        default_factory=list, 
        description="Resultados de Aprendizaje Esperados (RAE) redactados con verbo de acción Taxonomía Bloom"
    )
    justificacion_demanda_laboral: str = Field(
        "", 
        description="Justificación técnica sustentada en los datos del mercado laboral y vacantes analizadas"
    )

class PerfilDocente(BaseModel):
    """Perfil del cuerpo docente para la Matriz Integrada de Gestión (MIG)."""
    nombre_o_rol: str = Field(..., description="Nombre del docente o rol profesional (ej: Ing. Experto en Cloud Architecture)")
    modulo_asignado: str = Field(..., description="Nombre del módulo asignado")
    perfil_experto: str = Field(..., description="Experiencia profesional, títulos requeridos, certificaciones y trayectoria en industria")

class InversionPrograma(BaseModel):
    """Estructura de costos e inversión para diferentes segmentos según formato MIG."""
    publico_externo: str = Field("Por definir según tarifario institucional", description="Tarifa para público externo")
    comunidad_unicafam: str = Field("Descuento especial comunidad UniCafam / Afiliados Cafam", description="Tarifa para afiliados y estudiantes")
    egresados: str = Field("Tarifa preferencial egresados UniCafam", description="Tarifa para egresados")
    grupos_empresas: str = Field("Tarifa corporativa por volumen (>3 inscritos)", description="Tarifa para convenios empresariales")

class DiagnosticoPrograma(BaseModel):
    """Diagnóstico FODA y brechas del programa actual de UniCafam vs Mercado."""
    resumen_ejecutivo: str = Field(..., description="Diagnóstico general de la pertinencia y empleabilidad del programa")
    puntuacion_competitividad_mercado: float = Field(..., description="Calificación de 0 a 100 de alineación con el mercado")
    fortalezas_principales: List[str] = Field(..., description="Áreas donde el currículo de UniCafam es sólido y competitivo")
    brechas_criticas_mercado: List[str] = Field(..., description="Brechas tecnológicas de alta demanda ausentes en la malla")
    riesgos_competitivos_egresado: List[str] = Field(..., description="Riesgos salariales y laborales para el egresado actual")

class PropuestaPrograma(BaseModel):
    """Propuesta de oferta académica con estructura completa para la Matriz Integrada de Gestión (MIG)."""
    id_propuesta: str = Field(..., description="Identificador único (ej: PROP_ESP_DATA_ENG)")
    tipo_propuesta: str = Field(
        ..., description="Tipo de nivel formativo propuesto (Microcredencial, Electiva, Especialización, Maestría, Curso, Diplomado)"
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
    horario: Optional[str] = Field("Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas", description="Horario de clases")
    fecha_inicio_estimada: Optional[str] = Field("Próximo inicio de cohorte académica", description="Fecha tentativa de inicio")
    fecha_terminacion_estimada: Optional[str] = Field("Al completar el número total de horas del programa", description="Fecha tentativa de terminación")
    inversion: Optional[InversionPrograma] = Field(default_factory=InversionPrograma, description="Estructura de inversión por segmento")
    proximas_ediciones: Optional[str] = Field("Cohortes semestrales continuas", description="Próximas ediciones o cohortes")
    justificacion_detallada: Optional[str] = Field(None, description="Justificación completa basada en la demanda del mercado y brechas del observatorio")
    objetivos_programa: Optional[List[str]] = Field(default_factory=list, description="Objetivo general y objetivos específicos del programa")
    dirigido_a: Optional[str] = Field(None, description="Público objetivo, prerrequisitos y perfil del aspirante")
    metodologia_detallada: Optional[str] = Field(None, description="Metodología pedagógica, proyectos reales, aprendizaje experiencial y acompañamiento")
    valores_agregados: Optional[List[str]] = Field(default_factory=list, description="Diferenciadores de valor del programa")
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
    docentes_perfiles: Optional[List[PerfilDocente]] = Field(
        default_factory=list,
        description="Lista de docentes y perfiles expertos asignados a los módulos"
    )

class PortafolioRecomendacionesIA(BaseModel):
    """Contenedor maestro de la evaluación y portafolio generado por la IA."""
    diagnostico: DiagnosticoPrograma
    propuestas: List[PropuestaPrograma]

