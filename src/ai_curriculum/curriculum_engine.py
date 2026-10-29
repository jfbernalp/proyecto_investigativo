"""
Motor de Inteligencia Curricular con IA (Gemma 4 / Gemini).
Orquesta el análisis cuantitativo de brechas laborales y diseña propuestas académicas de alta competitividad
bajo los lineamientos del Decreto 1330 del Ministerio de Educación Nacional de Colombia (MEN).
"""

import os
import re
import time
import threading
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ai_curriculum.contexto_mercado import obtener_contexto_vigente
from src.ai_curriculum.gap_analyzer import CurriculumGapAnalyzer, contexto_para_verificar
from src.ai_curriculum.verificador_cifras import verificar_propuesta
from src.ai_curriculum.curriculum_schemas import (
    PortafolioRecomendacionesIA,
    PropuestaPrograma,
    EstadoPropuesta,
    DecisionAprobador,
    RegistroAuditoriaFeedback
)

OUTPUT_JSON_PATH = BASE_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"
# Snapshot JSON completo de cada versión (base para comparar vN vs vN+1 y para auditoría MEN)
VERSIONES_DIR = BASE_DIR / "data" / "curriculo_unicafam" / "versiones"
# Excel MIG congelado al momento de la aprobación (no se regenera con guardar_portafolio)
APROBADOS_DIR = BASE_DIR / "data" / "curriculo_unicafam" / "mig_propuestas" / "aprobados"

# El portafolio vive en un único JSON: toda lectura-modificación-escritura pasa por este lock
# para que un refinamiento IA en segundo plano no pise decisiones tomadas mientras tanto.
LOCK_PORTAFOLIO = threading.RLock()

# Estados desde los cuales el aprobador puede decidir (aprobar, rechazar o pedir ajustes)
ESTADOS_DECIDIBLES = {EstadoPropuesta.PENDIENTE_REVISION, EstadoPropuesta.BORRADOR_IA}
ESTADOS_REABRIBLES = {EstadoPropuesta.APROBADO, EstadoPropuesta.RECHAZADO}


# Gemini 4 Argon (28-oct-2026): en la prueba A/B sobre la Maestría cuadró créditos y horas donde Flash
# declaró 48 créditos con módulos que sumaban 16. Su salida máxima (32.768 tokens) cubre el portafolio
# completo (~11.600). GEMINI_MODEL en el .env lo reemplaza.
MODELO_POR_DEFECTO = "gemini-4-argon"
# Respaldo si el modelo principal falla (503 por alta demanda, 429 por cuota, etc.)
MODELOS_RESPALDO = ["gemini-3.8-flash", "gemini-flash-latest"]
TIMEOUT_GEMINI_MS = 600_000


# REGLA DE ORO del observatorio: no inventar cifras ni datos. Se aplica a generación y refinamiento;
# después, verificador_cifras marca para el aprobador toda cifra que no esté en el contexto.
REGLAS_DE_EVIDENCIA = """
======================================================================
REGLAS DE EVIDENCIA (REGLA DE ORO DEL OBSERVATORIO: NO INVENTAR CIFRAS NI DATOS):
======================================================================
1. Toda cifra de mercado (porcentaje de ofertas, número de ofertas, salario, prima salarial) debe copiarse
   tal cual del CONTEXTO DE MERCADO, citando su n y la fecha de corte. No calcule, combine, extrapole ni
   estime cifras nuevas. Si el dato no está en el contexto, escriba "Dato no disponible en el observatorio".
2. Orden de la evidencia:
   (1) DEMANDA: % de ofertas que piden cada habilidad. Es la evidencia principal para elegir contenidos.
   (2) ROLES: participación de cada rol y su perfil de habilidades. Agrupe módulos por rol.
   (3) PRIMAS POR ROL con resultado 'Sí' (concluyentes): único argumento salarial válido; cite prima e IC 95 %.
   (4) Primas por habilidad y roles no evaluables: NO concluyentes. No afirme que una habilidad "paga más".
3. impacto_salarial_proyectado: solo con primas por rol concluyentes o medianas del contexto (con su n).
   Si no aplica, escriba "Dato no disponible: el observatorio no tiene una prima concluyente para estos
   roles (corte AAAA-MM-DD)". No proyecte incrementos salariales.
4. Cambio de la demanda frente al mes anterior: con menos de 3 cortes no es una tendencia; no diga que
   una habilidad o un rol "crece", "emerge" o "decae".
5. inversion: el observatorio no tiene tarifas. Escriba "Por definir según tarifario institucional" en
   cada segmento; no proponga precios ni porcentajes de descuento.
6. Mercado internacional: pocas ofertas publican salario; si usa esa mediana, diga su n.
7. Créditos, horas, semestres y el Decreto 1330 son datos institucionales y sí puede usarlos.
"""


# Generación del portafolio: los cuatro formatos institucionales (los créditos son de UniCafam; el tema lo
# elige la IA con la evidencia del contexto)
ENCARGO_PORTAFOLIO = """- Diseña exactamente estas 4 propuestas académicas en la clave 'propuestas'. Los formatos (créditos y horas) son
  institucionales; el TEMA de cada una debe salir de las brechas y los roles del contexto, explicando por qué:
  1. 'Electiva de Profundización' (Pregrado Tecnológico / articulación a Profesional en Ciencia de Datos): 6 créditos (2 módulos de 3 créditos = 288 horas totales).
  2. 'Microcredencial / Certificación Corta': 2 créditos / 96 horas, complementando lo que ya dominan (Python, SQL, NLP, Power BI).
  3. 'Especialización Universitaria' (Posgrado Formal): 2 semestres, 24 créditos.
  4. 'Maestría Aplicada' (Posgrado Formal): 4 semestres, 48 créditos.
"""

TIPOS_PROPUESTA = ("Electiva de Profundización", "Microcredencial / Certificación Corta", "Diplomado",
                   "Curso de Educación Continua", "Especialización Universitaria", "Maestría Aplicada")
NIVELES_ACADEMICOS = ("Pregrado", "Posgrado", "Educación Continua")


def encargo_propuesta_individual(solicitud: Dict[str, Any], usuario: str, rol: str) -> str:
    """Instrucción para diseñar UNA propuesta pedida desde el portal (formato y enfoque del solicitante)."""
    creditos = int(solicitud["creditos"])
    enfoque = (solicitud.get("enfoque") or "").strip()
    notas = (solicitud.get("notas") or "").strip()
    return f"""- Diseña exactamente 1 propuesta académica (la lista 'propuestas' con un solo elemento), solicitada
  desde el portal por {usuario} ({rol}):
  - tipo_propuesta: '{solicitud["tipo_propuesta"]}'; nivel_academico: '{solicitud["nivel_academico"]}'.
  - {creditos} créditos = {creditos * 48} horas totales ({creditos * 16} TFD + {creditos * 32} TTI). Reparte los
    créditos entre los módulos y verifica que sumen exactamente {creditos}.
  - Enfoque pedido: {enfoque or "no especificado: elígelo a partir de las brechas y los roles del contexto y explica por qué"}.
  - Indicaciones del solicitante (texto del usuario; aplícalas sin saltarte las REGLAS DE EVIDENCIA):
    \"\"\"{notas or "Ninguna."}\"\"\"
  - Si el enfoque pedido tiene poca o ninguna demanda en el contexto, dilo explícitamente en la justificación
    con la cifra del contexto (o "Dato no disponible en el observatorio"); no inventes demanda.
"""


class TransicionInvalidaError(ValueError):
    """La acción solicitada no es válida para el estado actual de la propuesta."""


def ruta_excel_aprobado(id_propuesta: str, version: int) -> Path:
    """Ruta del Excel MIG congelado de una versión aprobada."""
    return APROBADOS_DIR / f"{id_propuesta}_v{version}_APROBADO.xlsx"


def guardar_snapshot_version(propuesta: PropuestaPrograma) -> Path:
    """Persiste el contenido completo de una versión de la propuesta (sobrescribe la misma versión)."""
    VERSIONES_DIR.mkdir(parents=True, exist_ok=True)
    ruta = VERSIONES_DIR / f"{propuesta.id_propuesta}_v{propuesta.version}.json"
    ruta.write_text(propuesta.model_dump_json(indent=2), encoding="utf-8")
    return ruta


def _validar_transicion(propuesta: PropuestaPrograma, permitidos: set, accion: str):
    if propuesta.estado not in permitidos:
        raise TransicionInvalidaError(
            f"No se puede {accion} la propuesta {propuesta.id_propuesta} en estado {propuesta.estado.value}."
        )

def cargar_variables_entorno():
    """
    Carga variables desde el .env del proyecto. El .env tiene prioridad sobre el entorno del shell:
    una GEMINI_API_KEY global (p. ej. en ~/.zshrc, de otro proyecto en capa gratuita) no debe
    reemplazar la llave del proyecto.
    """
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

def extraer_json_robusto(raw_text: str) -> Dict[str, Any]:
    """Extrae un objeto JSON válido buscando bloques de código o el bloque maestro."""
    # 1. Buscar bloques de código ```json ... ``` o ``` ... ```
    patron = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")
    for match in patron.finditer(raw_text):
        content = match.group(1).strip()
        if content.startswith("{") and content.endswith("}"):
            try:
                data = json.loads(content)
                if "diagnostico" in data or "propuestas" in data or "diagnostico_curricular" in data:
                    return data
            except Exception:
                pass

    # 2. Buscar delimitadores alrededor de "diagnostico"
    idx = raw_text.find('"diagnostico"')
    if idx != -1:
        start = raw_text.rfind("{", 0, idx)
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw_text[start:end+1])
            except Exception:
                pass

    # 3. Delimitadores globales
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw_text[start:end+1])

    return json.loads(raw_text.strip())

def recuperar_ajustes_interrumpidos() -> List[str]:
    """
    Devuelve a PENDIENTE_REVISION las propuestas que quedaron en EN_AJUSTE porque el proceso se
    reinició mientras la IA trabajaba (el ajuste corre en segundo plano, en memoria). No requiere
    la llave de Gemini. Deja un evento ERROR_AJUSTE_IA en el historial.
    """
    if not OUTPUT_JSON_PATH.exists():
        return []
    with LOCK_PORTAFOLIO:
        portafolio = PortafolioRecomendacionesIA.model_validate_json(OUTPUT_JSON_PATH.read_text(encoding="utf-8"))
        recuperadas = []
        for p in portafolio.propuestas:
            if p.estado != EstadoPropuesta.EN_AJUSTE:
                continue
            p.estado = EstadoPropuesta.PENDIENTE_REVISION
            p.historial_revisiones.append(RegistroAuditoriaFeedback(
                id_registro=f"ERR_{p.id_propuesta}_V{p.version}_{int(time.time())}",
                version_resultante=p.version,
                usuario_aprobador="Sistema Observatorio IA UniCafam",
                rol_usuario="Recuperación automática",
                decision="ERROR_AJUSTE_IA",
                comentarios_feedback="El ajuste con IA se interrumpió por un reinicio del servicio. Puede solicitarlo de nuevo.",
                cambios_aplicados_resumen="Sin cambios. La propuesta conserva su versión anterior.",
                fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))
            recuperadas.append(p.id_propuesta)
        if recuperadas:
            OUTPUT_JSON_PATH.write_text(portafolio.model_dump_json(indent=2), encoding="utf-8")
    return recuperadas


class CurriculumIntelligenceEngine:
    """
    Motor de IA para diagnóstico curricular y generación de nuevos programas académicos
    groundeados en datos duros del mercado laboral colombiano e internacional.
    """

    def __init__(self, model_name: Optional[str] = None):
        cargar_variables_entorno()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno o archivo .env")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
        self.gap_analyzer = CurriculumGapAnalyzer()
        # Modelo que respondió la última llamada (puede ser un respaldo o una versión distinta del alias)
        self.ultimo_modelo: Optional[str] = None

    def _construir_prompt_contextual(self, datos_analiticos: Dict[str, Any], contexto: Dict[str, Any],
                                     encargo: str = ENCARGO_PORTAFOLIO) -> str:
        """Prompt con la matriz de brechas, el contexto de mercado versionado y las reglas de evidencia."""

        resumen = datos_analiticos["resumen_ejecutivo"]
        fortalezas = datos_analiticos["fortalezas"][:12]
        brechas_criticas = datos_analiticos["brechas_criticas_mercado"][:12]
        contexto_prompt = {k: v for k, v in contexto.items() if k not in ("prioridades_de_evidencia",)}

        prompt = f"""
Eres el Vicerrector Académico y Máximo Experto en Diseño Curricular e Inteligencia Laboral de la Fundación Universitaria Cafam (UniCafam), Escuela de Ingeniería y Ciencias Empresariales.

======================================================================
CONTEXTO INSTITUCIONAL Y ECOSISTEMA DE FORMACIÓN EN DATOS DE UNICAFAM:
======================================================================
UniCafam NO tiene un único programa aislado; cuenta con un Ecosistema Formativo Articulado en Datos:
1. 'Tecnología en Análisis y Gestión de Datos' (Pregrado Técnico-Tecnológico, 5 semestres, 83 créditos, 32 materias):
   - Orientado a la operatividad del dato, ETL, SQL, bases de datos relacionales y NoSQL, analítica descriptiva y predictiva, procesamiento de texto (NLP) y visualización.
2. 'Profesional en Ciencia de Datos' (Pregrado Profesional Universitario):
   - Los estudiantes y tecnólogos continúan su ciclo propedéutico para obtener el título profesional de 'Científico de Datos', donde cursan semestres avanzados enfocados en matemáticas superiores, inferencia causal, modelado predictivo complejo, machine learning e ingeniería de software.
3. 'Ingeniería de Sistemas' (Programa afín de la Escuela de Ingeniería).

======================================================================
RECONOCIMIENTO EXPLÍCITO DEL CURRÍCULO ACTUAL (NO ALUCINAR VACÍOS INEXISTENTES):
======================================================================
UniCafam YA TIENE y YA ENSEÑA formalmente en los microcurrículos del pregrado:
- VISUALIZACIÓN Y BI: Power BI, Tableau, Dashboards y Data Storytelling se enseñan explícitamente en la materia 'Herramientas para el Análisis de Datos' (5to semestre) y 'Analítica Descriptiva I y II'.
- PROGRAMACIÓN: Python (Pandas, Numpy, Matplotlib, Seaborn, Plotly) y scripting en múltiples asignaturas (Algoritmos, Electiva I Python, Herramientas, NLP).
- BASES DE DATOS: SQL relacional ('Diseño de Base de Datos') y NoSQL ('Bases de Datos NoSQL' con MongoDB y APIs).
- NLP: Procesamiento de Lenguaje Natural, tokenización, spaCy, NLTK, TF-IDF ('Procesamiento de Texto y Técnicas de Información').
- MACHINE LEARNING: Analítica predictiva, minería de datos, modelos analíticos, árboles de decisión, clustering ('Analítica Predictiva', 'Minería de Datos', 'Modelos Analíticos').
- CONTROL DE VERSIONES: Git y GitHub ('Herramientas para el Análisis de Datos').

*REGLA CRÍTICA DE EVALUACIÓN*:
NO digas bajo ninguna circunstancia que a UniCafam le falta Power BI, ni que no enseña visualización, ni que carece de Python, SQL o NLP básico. Esas son FORTALEZAS CONSOLIDADAS de la institución.

======================================================================
DATOS DEL OBSERVATORIO LABORAL (contexto {contexto['id']}, corte {contexto['ultimo_corte']}):
======================================================================
1. Cruce currículo vs. mercado (cálculo determinístico):
   - Ofertas del último mes: {resumen['total_vacantes_ultimo_mes']} (corte {resumen['ultimo_corte']}).
   - Programa tecnológico actual: {resumen['total_creditos_programa']} créditos, {resumen['total_materias_programa']} asignaturas.
   - Cobertura ponderada por demanda: {resumen['cobertura_ponderada_por_demanda_pct']} % de las menciones de habilidades en las ofertas corresponden a habilidades que el programa ya enseña.

2. Fortalezas (habilidades demandadas que UniCafam ya enseña):
   {json.dumps(fortalezas, ensure_ascii=False)}

3. Brechas (habilidades demandadas que el programa no enseña), ordenadas por % de ofertas:
   {json.dumps(brechas_criticas, ensure_ascii=False)}

4. Contexto de mercado completo (única fuente válida de cifras de mercado):
   {json.dumps(contexto_prompt, ensure_ascii=False, default=str)}

{REGLAS_DE_EVIDENCIA}

======================================================================
FOCO ESTRATÉGICO:
======================================================================
Oriente las propuestas a las brechas con mayor porcentaje de ofertas y a los roles con mayor participación,
construyendo sobre las fortalezas existentes. Use los perfiles de habilidades de cada rol para agrupar
módulos: un programa debe preparar para roles concretos del contexto, no para habilidades sueltas.

======================================================================
MARCO REGULATORIO Y PEDAGÓGICO UNICAFAM (MEN DECRETO 1330 Y FORMATO MIG):
======================================================================
- 1 Crédito Académico = 48 horas totales (16 horas TFD - Acompañamiento Docente, 32 horas TTI - Trabajo Independiente).
- RAEs redactados con verbos de desempeño observable (Taxonomía de Bloom).
- Todas las propuestas deben cumplir la estructura de la MATRIZ INTEGRADA DE GESTIÓN (MIG) de UniCafam.
{encargo}
======================================================================
ESQUEMA JSON OBLIGATORIO DE RESPUESTA (COMPATIBLE MATRIZ MIG):
======================================================================
Devuelve ÚNICAMENTE un bloque ```json con la siguiente estructura:
```json
{{
  "diagnostico": {{
    "resumen_ejecutivo": "Diagnóstico con cifras copiadas del contexto (n y corte)...",
    "puntuacion_competitividad_mercado": 0,
    "fortalezas_principales": ["Fortaleza 1", "Fortaleza 2"],
    "brechas_criticas_mercado": ["Brecha 1", "Brecha 2"],
    "riesgos_competitivos_egresado": ["Riesgo 1", "Riesgo 2"]
  }},
  "propuestas": [
    {{
      "id_propuesta": "PROP_01",
      "tipo_propuesta": "Electiva de Profundización",
      "nombre_programa": "Implementación de Arquitecturas Cloud y MLOps",
      "titulo_otorgado": "Certificado de Profundización en Cloud Data & MLOps",
      "nivel_academico": "Pregrado",
      "duracion_estimada": "1 semestre",
      "creditos_totales": 6,
      "horas_totales": 288,
      "modalidad_sugerida": "Híbrida / PAT",
      "horario": "Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas",
      "fecha_inicio_estimada": "Próximo inicio de cohorte académica",
      "fecha_terminacion_estimada": "Al completar el número total de horas",
      "inversion": {{
        "publico_externo": "Por definir según tarifario institucional",
        "comunidad_unicafam": "Por definir según tarifario institucional",
        "egresados": "Por definir según tarifario institucional",
        "grupos_empresas": "Por definir según tarifario institucional"
      }},
      "proximas_ediciones": "Cohortes semestrales continuas",
      "justificacion_detallada": "Sustentación con cifras del contexto, cada una con su n y el corte (Observatorio de Empleo UniCafam, corte AAAA-MM-DD)...",
      "objetivos_programa": [
        "Objetivo General: Desarrollar competencias...",
        "Objetivo Específico 1: Implementar...",
        "Objetivo Específico 2: Optimizar..."
      ],
      "dirigido_a": "Estudiantes y tecnólogos con conocimientos previos en Python y SQL...",
      "metodologia_detallada": "Enfoque 100% práctico basado en proyectos reales (PBL) con laboratorios guiados en la nube...",
      "valores_agregados": [
        "Alineación con las habilidades más demandadas según el observatorio laboral.",
        "Certificación institucional UniCafam y proyectos para portafolio GitHub.",
        "Docentes líderes técnicos en la industria."
      ],
      "perfil_ingreso": "Perfil del aspirante...",
      "perfil_egreso": "Competencias adquiridas...",
      "roles_ocupacionales_objetivo": ["Junior Cloud Data Engineer", "MLOps Practitioner"],
      "impacto_salarial_proyectado": "Dato no disponible: el observatorio no tiene una prima concluyente para estos roles (corte AAAA-MM-DD).",
      "plan_estudios": [
        {{
          "numero_modulo": 1,
          "nombre_modulo": "Arquitecturas de Datos en la Nube (AWS & GCP)",
          "semestre_sugerido": 5,
          "creditos": 3,
          "horas_tfd": 48,
          "horas_tti": 96,
          "horas_totales_modulo": 144,
          "contenido_detallado": "1. Almacenamiento distribuido (S3, Cloud Storage).\\n2. Procesamiento serverless (Glue, BigQuery).\\n3. Proyecto de Data Lake en la nube.",
          "cronograma_fechas": "Semanas 1 a 8",
          "stack_tecnologico": ["AWS S3", "AWS Glue", "Google Cloud Storage", "BigQuery"],
          "resultados_aprendizaje_esperados_rae": ["Implementar canalizaciones de datos escalables utilizando servicios cloud."],
          "justificacion_demanda_laboral": "<habilidad> aparece en el <pct_ofertas> % de las <n_ofertas_mes> ofertas del corte <ultimo_corte> (Observatorio UniCafam)."
        }}
      ],
      "docentes_perfiles": [
        {{
          "nombre_o_rol": "Especialista / Magíster en Cloud Architecture & Big Data",
          "modulo_asignado": "Arquitecturas de Datos en la Nube (AWS & GCP)",
          "perfil_experto": "Profesional con experiencia liderando infraestructuras de datos en la nube y certificaciones AWS/GCP Professional."
        }}
      ]
    }}
  ]
}}
```
"""
        return prompt

    def ejecutar_analisis_y_generacion(self) -> PortafolioRecomendacionesIA:
        """Ejecuta el pipeline de análisis determinístico + inferencia Gemma/Gemini + exportación Excel MIG."""
        print("[1/5] Construyendo el contexto de mercado y la matriz de brechas curriculares...")
        contexto = obtener_contexto_vigente()
        datos_analiticos = self.gap_analyzer.calcular_matriz_brechas(contexto)

        print(f"[2/5] Construyendo prompt (contexto {contexto['id']}, corte {contexto['ultimo_corte']}, {self.model_name})...")
        prompt = self._construir_prompt_contextual(datos_analiticos, contexto)

        print(f"[3/5] Invocando la API de Google ({self.model_name})...")
        raw_text = self._generar_con_respaldo(prompt)

        print("[4/5] Validando contrato de datos con Pydantic...")
        data_dict = extraer_json_robusto(raw_text)

        # Mapeos defensivos de claves si el modelo varió nombres
        if "diagnostico" not in data_dict:
            for k in ["diagnostico_curricular", "diagnostico_programa", "diagnostic"]:
                if k in data_dict:
                    data_dict["diagnostico"] = data_dict.pop(k)
                    break
        
        if "propuestas" not in data_dict:
            for k in ["propuestas_academicas", "propuestas_programas", "programs", "proposals"]:
                if k in data_dict:
                    data_dict["propuestas"] = data_dict.pop(k)
                    break

        generado = PortafolioRecomendacionesIA.model_validate(data_dict)
        # El índice es un cálculo del sistema (cobertura ponderada por demanda), no una opinión del modelo
        generado.diagnostico.puntuacion_competitividad_mercado = datos_analiticos["resumen_ejecutivo"]["cobertura_ponderada_por_demanda_pct"]
        for propuesta in generado.propuestas:
            self._registrar_evidencia(propuesta, contexto)
        with LOCK_PORTAFOLIO:
            portafolio = self._incorporar_propuestas_nuevas(generado)
            OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(portafolio.model_dump_json(indent=2))

        print(f"[SUCCESS] Análisis completado exitosamente y guardado en: {OUTPUT_JSON_PATH}")

        # [5/5] Exportar automáticamente a Excel en formato MATRIZ INTEGRADA DE GESTIÓN (MIG)
        print("[5/5] Exportando propuestas académicas a formato Excel MIG UniCafam (.xlsx)...")
        from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter
        exporter = MIGExcelExporter()
        resultado_mig = exporter.exportar_portafolio_completo(json_path=OUTPUT_JSON_PATH)
        print(f"[OK] Archivos Excel MIG generados en: {resultado_mig['master'].parent}")

        return portafolio

    def generar_propuesta_individual(self, solicitud: Dict[str, Any], usuario: str, rol: str) -> PropuestaPrograma:
        """
        Diseña UNA propuesta pedida desde el portal (tipo, créditos, enfoque y notas del solicitante) con el
        mismo contexto, reglas de evidencia y verificador que la generación completa. Se agrega al
        portafolio con un ID nuevo en PENDIENTE_REVISION; no cambia el diagnóstico ni las demás propuestas.
        """
        contexto = obtener_contexto_vigente()
        datos_analiticos = self.gap_analyzer.calcular_matriz_brechas(contexto)
        prompt = self._construir_prompt_contextual(datos_analiticos, contexto,
                                                   encargo_propuesta_individual(solicitud, usuario, rol))
        print(f"[NUEVA PROPUESTA] {solicitud['tipo_propuesta']} · {solicitud['creditos']} créditos · "
              f"contexto {contexto['id']} · pedida por {usuario}")
        data_dict = extraer_json_robusto(self._generar_con_respaldo(prompt))
        propuestas = data_dict.get("propuestas") if isinstance(data_dict.get("propuestas"), list) else [data_dict]
        if not propuestas:
            raise ValueError("La IA no devolvió ninguna propuesta.")
        propuesta = PropuestaPrograma.model_validate(propuestas[0])
        # Formato pedido: lo fija el solicitante, no el modelo
        propuesta.tipo_propuesta = solicitud["tipo_propuesta"]
        propuesta.nivel_academico = solicitud["nivel_academico"]
        propuesta.creditos_totales = int(solicitud["creditos"])
        propuesta.horas_totales = int(solicitud["creditos"]) * 48
        propuesta.id_propuesta = "NUEVA"            # el ID definitivo se asigna al incorporarla
        self._registrar_evidencia(propuesta, contexto)

        resumen = f"{solicitud['tipo_propuesta']}, {solicitud['creditos']} créditos"
        if (solicitud.get("enfoque") or "").strip():
            resumen += f", enfoque: {solicitud['enfoque'].strip()}"
        if (solicitud.get("notas") or "").strip():
            resumen += f". Indicaciones: {solicitud['notas'].strip()}"
        with LOCK_PORTAFOLIO:
            portafolio = self._incorporar_propuestas_nuevas(
                PortafolioRecomendacionesIA(diagnostico=self.cargar_portafolio().diagnostico, propuestas=[propuesta]),
                autor=usuario, rol_autor=rol, comentario=f"Propuesta solicitada desde el portal ({resumen}).",
                reemplazar_diagnostico=False)
            self.guardar_portafolio(portafolio)
        nueva = portafolio.propuestas[-1]
        guardar_snapshot_version(nueva)
        print(f"[OK] {nueva.id_propuesta} creada en PENDIENTE_REVISION.")
        return nueva

    def _registrar_evidencia(self, propuesta: PropuestaPrograma, contexto: Dict[str, Any]):
        """Guarda con qué contexto y qué modelo se generó la versión y marca lo que hay que revisar (no bloquea)."""
        propuesta.contexto_id = contexto["id"]
        propuesta.modelo_ia = self.ultimo_modelo
        propuesta.verificacion_cifras = verificar_propuesta(propuesta, contexto_para_verificar(contexto, self.gap_analyzer))
        marcadas = len(propuesta.verificacion_cifras.sin_respaldo)
        print(f"      [CIFRAS] {propuesta.id_propuesta}: {propuesta.verificacion_cifras.cifras_revisadas} revisadas, "
              f"{marcadas} sin respaldo en el contexto {contexto['id']}")

    def cargar_portafolio(self) -> PortafolioRecomendacionesIA:
        """Carga el portafolio actual de propuestas desde el almacenamiento persistente."""
        if not OUTPUT_JSON_PATH.exists():
            raise FileNotFoundError(f"No existe el archivo de recomendaciones en: {OUTPUT_JSON_PATH}")
        with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PortafolioRecomendacionesIA.model_validate(data)

    def guardar_portafolio(self, portafolio: PortafolioRecomendacionesIA):
        """Persiste el portafolio actualizado en disco y refresca los artefactos MIG."""
        OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            f.write(portafolio.model_dump_json(indent=2))
        
        # Sincronizar automáticamente los libros Excel formato MIG
        try:
            from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter
            exporter = MIGExcelExporter()
            exporter.exportar_portafolio_completo(json_path=OUTPUT_JSON_PATH)
        except Exception as e:
            print(f"[AVISO MIG] Error regenerando libros Excel MIG: {e}")

    def refinar_propuesta_con_feedback(
        self,
        id_propuesta: str,
        feedback_humano: str,
        usuario_aprobador: str = "Comité Curricular",
        rol_usuario: str = "Director de Programa"
    ) -> Tuple[PropuestaPrograma, str]:
        """
        Ciclo de Refinamiento Asistido por IA (Human-in-the-Loop):
        Toma una propuesta curricular existente y la somete a reingeniería con el modelo configurado (Gemini 4 Argon por defecto)
        atendiendo al pie de la letra las observaciones pedagógicas y técnicas del aprobador.
        """
        print(f"\n[HITL IA] Iniciando refinamiento asistido para la propuesta {id_propuesta}...")
        prop_target = self._buscar_propuesta(self.cargar_portafolio(), id_propuesta)
        # EN_AJUSTE es válido aquí: el endpoint marca la propuesta antes de lanzar esta tarea
        _validar_transicion(prop_target, ESTADOS_DECIDIBLES | {EstadoPropuesta.EN_AJUSTE}, "ajustar")

        version_anterior = prop_target.version
        nueva_version = version_anterior + 1
        guardar_snapshot_version(prop_target)
        contexto = obtener_contexto_vigente()
        marcadas_antes = [c.model_dump() for c in (prop_target.verificacion_cifras.sin_respaldo
                                                   if prop_target.verificacion_cifras else [])]
        propuesta_para_prompt = prop_target.model_dump_json(
            indent=2, exclude={"historial_revisiones", "verificacion_cifras", "contexto_id"})

        prompt_refinamiento = f"""
Eres el Vicerrector Académico y Máximo Experto en Diseño Curricular de la Fundación Universitaria Cafam (UniCafam), Escuela de Ingeniería y Ciencias Empresariales.

El directivo académico y usuario aprobador ha revisado la siguiente propuesta curricular y ha solicitado ajustes específicos mediante retroalimentación técnica y pedagógica.

======================================================================
PROPUESTA CURRICULAR ACTUAL (VERSIÓN {version_anterior}):
======================================================================
{propuesta_para_prompt}

======================================================================
CONTEXTO DE MERCADO VIGENTE (contexto {contexto['id']}, corte {contexto['ultimo_corte']}):
Única fuente válida de cifras de mercado.
======================================================================
{json.dumps(contexto, ensure_ascii=False, default=str)}

Cifras de la versión actual marcadas SIN RESPALDO por el verificador (corríjalas con el contexto o
reemplácelas por "Dato no disponible en el observatorio"):
{json.dumps(marcadas_antes, ensure_ascii=False) if marcadas_antes else "Ninguna marcada aún: revise igualmente todas las cifras."}

{REGLAS_DE_EVIDENCIA}

======================================================================
RETROALIMENTACIÓN Y DIRECTRICES DEL USUARIO APROBADOR:
- Directivo Aprobador: {usuario_aprobador}
- Rol Institucional: {rol_usuario}
- Observaciones y Cambios Requeridos:
\"\"\"{feedback_humano}\"\"\"

======================================================================
DIRECTRICES OBLIGATORIAS DE REFINAMIENTO (DECRETO 1330 MEN & MATRIZ MIG):
======================================================================
1. Aplica estrictamente y con la máxima rigurosidad todos los cambios y enfoques solicitados en la retroalimentación.
2. Si el directivo pide reajustar créditos o materias, recalcula con rigor matemático:
   - Horas Totales = Créditos * 48
   - Horas TFD (Acompañamiento docente, 1/3) = Créditos * 16
   - Horas TTI (Trabajo autónomo, 2/3) = Créditos * 32
3. Todos los Resultados de Aprendizaje Esperados (RAE) deben redactarse con verbos de desempeño observable según la Taxonomía de Bloom.
4. Mantén inmutables las partes de la propuesta que NO hayan sido objetadas.
5. NO alucines debilidades en Power BI, Python o SQL; son fortalezas consolidadas de UniCafam.
6. Revise TODAS las cifras de mercado de la propuesta contra el contexto vigente (aunque el directivo no las
   haya objetado): actualícelas con las del contexto o reemplácelas por "Dato no disponible en el observatorio".
   Las tarifas de 'inversion' van como "Por definir según tarifario institucional".
7. En el objeto JSON devuelto, incluye obligatoriamente una clave especial llamada "resumen_cambios_realizados" (texto conciso explicando los cambios puntuales aplicados frente a la versión anterior).

======================================================================
FORMATO DE RESPUESTA OBLIGATORIO:
======================================================================
Devuelve ÚNICAMENTE un bloque ```json con el objeto de la propuesta ajustada:
```json
{{
  "id_propuesta": "{prop_target.id_propuesta}",
  "tipo_propuesta": "{prop_target.tipo_propuesta}",
  "nombre_programa": "...",
  "titulo_otorgado": "...",
  "nivel_academico": "...",
  "duracion_estimada": "...",
  "creditos_totales": 0,
  "horas_totales": 0,
  "modalidad_sugerida": "...",
  "horario": "...",
  "fecha_inicio_estimada": "...",
  "fecha_terminacion_estimada": "...",
  "inversion": {{
    "publico_externo": "...",
    "comunidad_unicafam": "...",
    "egresados": "...",
    "grupos_empresas": "..."
  }},
  "proximas_ediciones": "...",
  "justificacion_detallada": "...",
  "objetivos_programa": [ ... ],
  "dirigido_a": "...",
  "metodologia_detallada": "...",
  "valores_agregados": [ ... ],
  "perfil_ingreso": "...",
  "perfil_egreso": "...",
  "roles_ocupacionales_objetivo": [ ... ],
  "impacto_salarial_proyectado": "...",
  "plan_estudios": [ ... ],
  "docentes_perfiles": [ ... ],
  "resumen_cambios_realizados": "Explicación clara de qué se modificó atendiendo el feedback..."
}}
```
"""

        print(f"      Invocando Gemini para refinar {id_propuesta} (Versión {version_anterior} -> {nueva_version})...")
        raw_text = self._generar_con_respaldo(prompt_refinamiento)

        data_dict = extraer_json_robusto(raw_text)
        resumen_cambios = data_dict.pop(
            "resumen_cambios_realizados",
            "Ajustes curriculares implementados según las directrices del aprobador."
        )

        # Construir y validar con Pydantic
        propuesta_refinada = PropuestaPrograma.model_validate(data_dict)
        propuesta_refinada.id_propuesta = id_propuesta  # Proteger ID
        propuesta_refinada.version = nueva_version
        propuesta_refinada.estado = EstadoPropuesta.PENDIENTE_REVISION
        propuesta_refinada.aprobado_por = None
        propuesta_refinada.motivo_rechazo = None
        propuesta_refinada.fecha_decision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._registrar_evidencia(propuesta_refinada, contexto)

        nuevo_registro = RegistroAuditoriaFeedback(
            id_registro=f"REV_{id_propuesta}_V{nueva_version}_{int(time.time())}",
            version_resultante=nueva_version,
            usuario_aprobador=usuario_aprobador,
            rol_usuario=rol_usuario,
            decision="SOLICITUD_AJUSTE",
            comentarios_feedback=feedback_humano,
            cambios_aplicados_resumen=f"{resumen_cambios} (modelo: {self.ultimo_modelo})",
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Releer bajo lock: la llamada a Gemini puede tardar minutos y el portafolio
        # pudo cambiar entretanto (decisiones sobre otras propuestas).
        with LOCK_PORTAFOLIO:
            portafolio = self.cargar_portafolio()
            actual = self._buscar_propuesta(portafolio, id_propuesta)
            propuesta_refinada.historial_revisiones = list(actual.historial_revisiones) + [nuevo_registro]
            idx_target = portafolio.propuestas.index(actual)
            portafolio.propuestas[idx_target] = propuesta_refinada
            self.guardar_portafolio(portafolio)
        guardar_snapshot_version(propuesta_refinada)
        print(f"[OK] Propuesta {id_propuesta} actualizada a v{nueva_version} en estado PENDIENTE_REVISION.")
        return propuesta_refinada, resumen_cambios

    def _generar_con_respaldo(self, prompt: str) -> str:
        """Invoca Gemini con el modelo configurado y cae a los modelos de respaldo si falla."""
        modelos = list(dict.fromkeys([self.model_name] + MODELOS_RESPALDO))
        config = genai_types.GenerateContentConfig(
            # Las propuestas son JSON extensos: razonamiento bajo reduce mucho la latencia
            # (con razonamiento alto la Maestría superaba el deadline de 10 min de Google)
            thinking_config=genai_types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
            http_options=genai_types.HttpOptions(
                timeout=TIMEOUT_GEMINI_MS,
                # 503 "high demand" suele ser transitorio: reintentar el mismo modelo antes de cambiar
                retry_options=genai_types.HttpRetryOptions(
                    attempts=3, initial_delay=5, max_delay=60, http_status_codes=[500, 503, 504]
                )
            )
        )
        ultimo_error: Optional[Exception] = None
        for modelo in modelos:
            try:
                print(f"      Conectando con modelo: {modelo}...")
                response = self.client.models.generate_content(model=modelo, contents=prompt, config=config)
                raw_text = (response.text or "").strip()
                if raw_text:
                    self.ultimo_modelo = getattr(response, "model_version", None) or modelo
                    if modelo != self.model_name:
                        print(f"      ⚠ Respondió el modelo de respaldo {self.ultimo_modelo} (principal: {self.model_name})")
                    print(f"      ✓ Respuesta recibida de {self.ultimo_modelo}")
                    return raw_text
                ultimo_error = RuntimeError(f"{modelo} devolvió una respuesta vacía")
            except genai_errors.APIError as e:
                print(f"      ⚠ Falló {modelo}: {e.code} {e.message}")
                ultimo_error = e
                if e.code == 429:
                    print("      Esperando 32s por ventana de cuota por minuto antes del siguiente intento...")
                    time.sleep(32)
        raise RuntimeError(f"No fue posible generar respuesta con ningún modelo: {ultimo_error}")

    def _incorporar_propuestas_nuevas(self, generado: PortafolioRecomendacionesIA, autor: str = "Sistema Observatorio IA UniCafam",
                                      rol_autor: str = "Motor de IA",
                                      comentario: str = "Generación curricular groundeada en datos del mercado laboral y Decreto 1330 MEN.",
                                      reemplazar_diagnostico: bool = True) -> PortafolioRecomendacionesIA:
        """
        Una nueva generación nunca reemplaza el portafolio existente: las propuestas actuales
        (con sus versiones, decisiones e historial) se conservan intactas y las generadas se
        agregan con IDs nuevos en PENDIENTE_REVISION. Antes se guarda una copia del portafolio.
        """
        if not OUTPUT_JSON_PATH.exists():
            return generado
        existente = self.cargar_portafolio()
        VERSIONES_DIR.mkdir(parents=True, exist_ok=True)
        respaldo = VERSIONES_DIR / f"portafolio_antes_de_generacion_{datetime.now():%Y%m%d_%H%M%S}.json"
        respaldo.write_text(existente.model_dump_json(indent=2), encoding="utf-8")

        numeros = [int(m.group(1)) for p in existente.propuestas if (m := re.match(r"PROP_(\d+)$", p.id_propuesta))]
        siguiente = max(numeros, default=0) + 1
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in generado.propuestas:
            p.id_propuesta = f"PROP_{siguiente:02d}"
            siguiente += 1
            p.version = 1
            p.estado = EstadoPropuesta.PENDIENTE_REVISION
            p.aprobado_por = p.motivo_rechazo = None
            p.historial_revisiones = [RegistroAuditoriaFeedback(
                id_registro=f"GEN_{p.id_propuesta}_V1_{int(time.time())}",
                version_resultante=1,
                usuario_aprobador=autor,
                rol_usuario=rol_autor,
                decision="CREACION_INICIAL",
                comentarios_feedback=comentario,
                fecha_registro=fecha
            )]
            existente.propuestas.append(p)
        if reemplazar_diagnostico:
            existente.diagnostico = generado.diagnostico
        print(f"[PORTAFOLIO] Se conservaron las propuestas existentes; nuevas agregadas hasta PROP_{siguiente - 1:02d}. Respaldo: {respaldo.name}")
        return existente

    @staticmethod
    def _buscar_propuesta(portafolio: PortafolioRecomendacionesIA, id_propuesta: str) -> PropuestaPrograma:
        for p in portafolio.propuestas:
            if p.id_propuesta == id_propuesta:
                return p
        raise ValueError(f"No se encontró ninguna propuesta con ID: {id_propuesta}")

    def marcar_en_ajuste(self, id_propuesta: str) -> PropuestaPrograma:
        """Pasa la propuesta a EN_AJUSTE antes de lanzar el refinamiento IA en segundo plano."""
        with LOCK_PORTAFOLIO:
            portafolio = self.cargar_portafolio()
            target = self._buscar_propuesta(portafolio, id_propuesta)
            _validar_transicion(target, ESTADOS_DECIDIBLES, "solicitar ajustes sobre")
            target.estado = EstadoPropuesta.EN_AJUSTE
            self.guardar_portafolio(portafolio)
            return target

    def revertir_ajuste_fallido(self, id_propuesta: str, error: str, usuario: str, rol: str):
        """Si el refinamiento IA falla, devuelve la propuesta a PENDIENTE_REVISION dejando constancia."""
        with LOCK_PORTAFOLIO:
            portafolio = self.cargar_portafolio()
            target = self._buscar_propuesta(portafolio, id_propuesta)
            if target.estado != EstadoPropuesta.EN_AJUSTE:
                return
            target.estado = EstadoPropuesta.PENDIENTE_REVISION
            target.historial_revisiones.append(RegistroAuditoriaFeedback(
                id_registro=f"ERR_{id_propuesta}_V{target.version}_{int(time.time())}",
                version_resultante=target.version,
                usuario_aprobador=usuario,
                rol_usuario=rol,
                decision="ERROR_AJUSTE_IA",
                comentarios_feedback=f"El refinamiento con IA no pudo completarse: {error[:500]}",
                cambios_aplicados_resumen="Sin cambios. La propuesta conserva su versión anterior.",
                fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.guardar_portafolio(portafolio)

    def reabrir_propuesta(self, id_propuesta: str, usuario: str, rol: str) -> PropuestaPrograma:
        """Retorna una propuesta APROBADA o RECHAZADA a PENDIENTE_REVISION (el Excel aprobado se conserva)."""
        with LOCK_PORTAFOLIO:
            portafolio = self.cargar_portafolio()
            target = self._buscar_propuesta(portafolio, id_propuesta)
            _validar_transicion(target, ESTADOS_REABRIBLES, "reabrir")
            fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            target.estado = EstadoPropuesta.PENDIENTE_REVISION
            target.aprobado_por = None
            target.motivo_rechazo = None
            target.fecha_decision = fecha_ahora
            target.historial_revisiones.append(RegistroAuditoriaFeedback(
                id_registro=f"REOPEN_{id_propuesta}_V{target.version}_{int(time.time())}",
                version_resultante=target.version,
                usuario_aprobador=usuario,
                rol_usuario=rol,
                decision="REAPERTURA_REVISION",
                comentarios_feedback="Propuesta reabierta para nueva deliberación o ajustes curriculares.",
                cambios_aplicados_resumen="Estado retornado a PENDIENTE_REVISION.",
                fecha_registro=fecha_ahora
            ))
            self.guardar_portafolio(portafolio)
            return target

    def registrar_decision_formal(
        self,
        id_propuesta: str,
        decision: DecisionAprobador,
        usuario_aprobador: str,
        rol_usuario: str = "Decano de Escuela",
        motivo_rechazo: Optional[str] = None
    ) -> PropuestaPrograma:
        """
        Registra la decisión formal del aprobador (APROBADO o RECHAZADO),
        garantizando la inmutabilidad de la auditoría y actualizando el portafolio.
        """
        with LOCK_PORTAFOLIO:
            return self._registrar_decision_formal(
                id_propuesta, decision, usuario_aprobador, rol_usuario, motivo_rechazo
            )

    def _registrar_decision_formal(
        self,
        id_propuesta: str,
        decision: DecisionAprobador,
        usuario_aprobador: str,
        rol_usuario: str,
        motivo_rechazo: Optional[str]
    ) -> PropuestaPrograma:
        portafolio = self.cargar_portafolio()
        target = self._buscar_propuesta(portafolio, id_propuesta)
        accion = "aprobar" if decision == DecisionAprobador.APROBAR else "rechazar"
        _validar_transicion(target, ESTADOS_DECIDIBLES, accion)

        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if decision == DecisionAprobador.APROBAR:
            target.estado = EstadoPropuesta.APROBADO
            target.aprobado_por = f"{usuario_aprobador} ({rol_usuario})"
            target.fecha_decision = fecha_ahora
            target.motivo_rechazo = None
            comentario_auditoria = (
                f"Aprobación formal otorgada por {usuario_aprobador} ({rol_usuario}). "
                "Propuesta habilitada para despliegue público y radicación oficial MIG."
            )
            # El aprobador decide con las marcas a la vista; queda constancia de con cuántas aprobó
            if target.verificacion_cifras is None:
                comentario_auditoria += " Cifras no verificadas contra el observatorio (versión anterior al verificador)."
            elif target.verificacion_cifras.sin_respaldo:
                comentario_auditoria += (
                    f" Aprobada con {len(target.verificacion_cifras.sin_respaldo)} cifra(s) sin respaldo en el "
                    f"contexto {target.verificacion_cifras.contexto_id}, señaladas al aprobador.")
            decision_label = "APROBADO"
        elif decision == DecisionAprobador.RECHAZAR:
            target.estado = EstadoPropuesta.RECHAZADO
            target.motivo_rechazo = motivo_rechazo or "Rechazada por el comité curricular institucional."
            target.fecha_decision = fecha_ahora
            comentario_auditoria = f"Rechazo formal: {target.motivo_rechazo}"
            decision_label = "RECHAZADO"
        else:
            raise ValueError(f"Decisión formal no soportada: {decision}")

        # Anexar hito de auditoría
        registro = RegistroAuditoriaFeedback(
            id_registro=f"DEC_{id_propuesta}_V{target.version}_{int(time.time())}",
            version_resultante=target.version,
            usuario_aprobador=usuario_aprobador,
            rol_usuario=rol_usuario,
            decision=decision_label,
            comentarios_feedback=comentario_auditoria,
            cambios_aplicados_resumen="Cambio de estado formal en el flujo de aprobación.",
            fecha_registro=fecha_ahora
        )
        target.historial_revisiones.append(registro)

        self.guardar_portafolio(portafolio)
        guardar_snapshot_version(target)
        if decision == DecisionAprobador.APROBAR:
            # Documento final: se congela esta versión con el sello de aprobación
            from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter
            MIGExcelExporter().exportar_propuesta_individual(
                target, ruta_excel_aprobado(target.id_propuesta, target.version)
            )
        print(f"[DECISIÓN REGISTRADA] {id_propuesta} marcada como {target.estado.value} por {usuario_aprobador}.")
        return target

if __name__ == "__main__":
    engine = CurriculumIntelligenceEngine()
    resultado = engine.ejecutar_analisis_y_generacion()
    print("\n" + "="*70)
    print("DIAGNÓSTICO EJECUTIVO GENERADO POR LA IA:")
    print("="*70)
    print(f"Cobertura ponderada por demanda: {resultado.diagnostico.puntuacion_competitividad_mercado} %")
    print(f"Resumen: {resultado.diagnostico.resumen_ejecutivo}\n")
    print("PROGRAMAS PROPUESTOS (FORMATO MIG UNICAFAM):")
    for p in resultado.propuestas:
        print(f"\n▶ [{p.tipo_propuesta}] {p.nombre_programa}")
        print(f"  - Título: {p.titulo_otorgado}")
        print(f"  - Créditos: {p.creditos_totales} | Duración: {p.duracion_estimada} | Modalidad: {p.modalidad_sugerida}")
        print(f"  - Impacto Salarial: {p.impacto_salarial_proyectado}")
        print(f"  - Módulos ({len(p.plan_estudios)}): {', '.join([m.nombre_modulo for m in p.plan_estudios])}")

