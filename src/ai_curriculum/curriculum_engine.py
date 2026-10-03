"""
Motor de Inteligencia Curricular con IA (Gemma 4 / Gemini).
Orquesta el análisis cuantitativo de brechas laborales y diseña propuestas académicas de alta competitividad
bajo los lineamientos del Decreto 1330 del Ministerio de Educación Nacional de Colombia (MEN).
"""

import os
import re
import time
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import google.generativeai as genai
from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ai_curriculum.gap_analyzer import CurriculumGapAnalyzer
from src.ai_curriculum.curriculum_schemas import (
    PortafolioRecomendacionesIA,
    PropuestaPrograma,
    EstadoPropuesta,
    DecisionAprobador,
    RegistroAuditoriaFeedback
)

OUTPUT_JSON_PATH = BASE_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"

def cargar_variables_entorno():
    """Carga variables desde .env si existen."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

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

class CurriculumIntelligenceEngine:
    """
    Motor de IA para diagnóstico curricular y generación de nuevos programas académicos
    groundeados en datos duros del mercado laboral colombiano e internacional.
    """

    def __init__(self, model_name: str = "models/gemini-3.5-flash"):
        cargar_variables_entorno()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno o archivo .env")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.gap_analyzer = CurriculumGapAnalyzer()

    def _construir_prompt_contextual(self, datos_analiticos: Dict[str, Any]) -> str:
        """Construye el prompt contextual con datos cuantitativos reales, ecosistema dual UniCafam y marco MEN."""
        
        resumen = datos_analiticos["resumen_ejecutivo"]
        fortalezas = datos_analiticos["fortalezas"][:10]
        brechas_criticas = datos_analiticos["brechas_criticas_mercado"][:10]
        brechas_salario = datos_analiticos["brechas_alto_valor_economico"][:6]
        roles = datos_analiticos["roles_mas_demandados"][:5]
        salarios = datos_analiticos["salarios_por_mercado"]
        ecosistema = datos_analiticos.get("ecosistema_academico", {})

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
DATOS CUANTITATIVOS DUROS DEL OBSERVATORIO LABORAL:
======================================================================
1. Resumen Global:
   - Ofertas analizadas: {resumen['total_vacantes']} vacantes.
   - Créditos del programa tecnológico actual: {resumen['total_creditos_programa']} créditos (32 asignaturas).
   - Cobertura actual de mercado: {resumen['cobertura_porcentual_mercado']}%

2. Roles Más Demandados:
   {json.dumps(roles, ensure_ascii=False, indent=2)}

3. Panorama Salarial:
   {json.dumps(salarios, ensure_ascii=False, indent=2)}

4. Top Fortalezas Actuales UniCafam (Habilidades cubiertas en la oferta académica):
   {json.dumps(fortalezas, ensure_ascii=False, indent=2)}

5. Principales Brechas Críticas Reales del Mercado (Habilidades donde el mercado abre oportunidades de alto valor):
   {json.dumps(brechas_criticas, ensure_ascii=False, indent=2)}

6. Brechas de Alto Salario (> $8M COP local / > $20M COP remoto):
   {json.dumps(brechas_salario, ensure_ascii=False, indent=2)}

======================================================================
EL VERDADERO RETO Y FOCO ESTRATÉGICO:
======================================================================
El estudiante tecnólogo de UniCafam egresa con un perfil altamente competitivo como Analista de Datos / BI Developer junior (salarios locales de $4M a $6M COP).
Sin embargo, las vacantes de ALTO VALOR SALARIAL ($11M a $66M COP, especialmente en multinacionales y mercado remoto internacional) exigen competencias que marcan el salto hacia la Ciencia e Ingeniería de Datos avanzada:
1. Infraestructura Cloud Enterprise: AWS, Google Cloud Platform (BigQuery), Azure.
2. MLOps y Despliegue en Producción: Docker, Kubernetes, CI/CD para modelos, MLflow.
3. Big Data Distribuido: Databricks, Apache Spark a gran escala, orquestación con Apache Airflow.
4. IA Generativa Empresarial: Modelos Fundacionales, RAG (Retrieval-Augmented Generation), bases de datos vectoriales.

======================================================================
MARCO REGULATORIO Y PEDAGÓGICO UNICAFAM (MEN DECRETO 1330 Y FORMATO MIG):
======================================================================
- 1 Crédito Académico = 48 horas totales (16 horas TFD - Acompañamiento Docente, 32 horas TTI - Trabajo Independiente).
- RAEs redactados con verbos de desempeño observable (Taxonomía de Bloom).
- Todas las propuestas deben cumplir la estructura de la MATRIZ INTEGRADA DE GESTIÓN (MIG) de UniCafam.
- Diseña exactamente estas 4 propuestas académicas en la clave 'propuestas':
  1. 'Electiva de Profundización' (Pregrado Tecnológico / Articulación a Profesional en Ciencia de Datos): 6 créditos (2 módulos de 3 créditos = 288 horas totales). Enfoque: Cloud Data Engineering y MLOps Práctico (AWS/GCP, Docker, despliegue de modelos).
  2. 'Microcredencial / Certificación Corta': 1 programa ágil de 2 créditos / 96 horas (ej: Especialización en IA Generativa & Arquitecturas RAG para Negocios o Modern Data Stack con Databricks & Spark, complementando lo que ya dominan en Python, NLP y Power BI).
  3. 'Especialización Universitaria' (Posgrado Formal): 1 programa de 2 semestres, 24 créditos (ej: Especialización en Ingeniería de Datos y Arquitecturas Cloud).
  4. 'Maestría Aplicada' (Posgrado Formal): 1 maestría de 4 semestres, 48 créditos (ej: Maestría en Inteligencia Artificial y Ciencia de Datos Estratégica, articulando la ruta de egresados de Ciencia de Datos al mercado global de alta remuneración).

======================================================================
ESQUEMA JSON OBLIGATORIO DE RESPUESTA (COMPATIBLE MATRIZ MIG):
======================================================================
Devuelve ÚNICAMENTE un bloque ```json con la siguiente estructura:
```json
{{
  "diagnostico": {{
    "resumen_ejecutivo": "Diagnóstico profundo...",
    "puntuacion_competitividad_mercado": 74.0,
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
        "publico_externo": "$2.800.000 COP",
        "comunidad_unicafam": "$2.100.000 COP (25% dcto afiliados/estudiantes)",
        "egresados": "$2.240.000 COP (20% dcto)",
        "grupos_empresas": "$1.960.000 COP (por convenio empresarial >3 personas)"
      }},
      "proximas_ediciones": "Cohortes semestrales continuas",
      "justificacion_detallada": "Sustentación pedagógica y económica detallada con datos del observatorio laboral...",
      "objetivos_programa": [
        "Objetivo General: Desarrollar competencias...",
        "Objetivo Específico 1: Implementar...",
        "Objetivo Específico 2: Optimizar..."
      ],
      "dirigido_a": "Estudiantes y tecnólogos con conocimientos previos en Python y SQL...",
      "metodologia_detallada": "Enfoque 100% práctico basado en proyectos reales (PBL) con laboratorios guiados en la nube...",
      "valores_agregados": [
        "Alineación con vacantes de alta remuneración del observatorio laboral.",
        "Certificación institucional UniCafam y proyectos para portafolio GitHub.",
        "Docentes líderes técnicos en la industria."
      ],
      "perfil_ingreso": "Perfil del aspirante...",
      "perfil_egreso": "Competencias adquiridas...",
      "roles_ocupacionales_objetivo": ["Junior Cloud Data Engineer", "MLOps Practitioner"],
      "impacto_salarial_proyectado": "+45% de prima salarial sobre la media local",
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
          "justificacion_demanda_laboral": "El 22.5% de las vacantes exige conocimientos en nubes públicas."
        }}
      ],
      "docentes_perfiles": [
        {{
          "nombre_o_rol": "Especialista / Magíster en Cloud Architecture & Big Data",
          "modulo_asignado": "Arquitecturas de Datos en la Nube (AWS & GCP)",
          "perfil_experto": "Profesional con +5 años liderando infraestructuras de datos en la nube y certificaciones AWS/GCP Professional."
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
        print("[1/5] Extrayendo y calculando matriz de brechas curriculares vs mercado laboral...")
        datos_analiticos = self.gap_analyzer.calcular_matriz_brechas()

        print(f"[2/5] Construyendo prompt pedagógico y regulatorio MIG UniCafam ({self.model_name})...")
        prompt = self._construir_prompt_contextual(datos_analiticos)

        print(f"[3/5] Invocando la API de Google ({self.model_name})...")
        modelos_candidatos = [self.model_name, "models/gemini-3.5-flash", "models/gemini-flash-latest", "models/gemini-3.8-flash"]
        modelos_probados = []
        for m in modelos_candidatos:
            if m not in modelos_probados:
                modelos_probados.append(m)

        raw_text = None
        ultimo_error = None
        for mod_name in modelos_probados:
            try:
                print(f"      Conectando con modelo: {mod_name}...")
                model = genai.GenerativeModel(mod_name)
                response = model.generate_content(prompt, request_options={"timeout": 600})
                raw_text = response.text.strip()
                if raw_text:
                    print(f"      ✓ Respuesta recibida exitosamente de {mod_name}")
                    break
            except Exception as e:
                print(f"      ⚠ Falló con {mod_name}: {e}")
                ultimo_error = e
                if "429" in str(e) or "quota" in str(e).lower():
                    print("      Esperando 32s por ventana de cuota por minuto antes del siguiente intento...")
                    time.sleep(32)

        if not raw_text:
            raise RuntimeError(f"No fue posible generar respuesta con ningún modelo: {ultimo_error}")

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

        portafolio = PortafolioRecomendacionesIA.model_validate(data_dict)

        # Guardar en archivo JSON persistente
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
        Toma una propuesta curricular existente y la somete a reingeniería con Gemini 3.5 Flash
        atendiendo al pie de la letra las observaciones pedagógicas y técnicas del aprobador.
        """
        print(f"\n[HITL IA] Iniciando refinamiento asistido para la propuesta {id_propuesta}...")
        portafolio = self.cargar_portafolio()
        
        # Localizar la propuesta objetivo
        idx_target = None
        prop_target: Optional[PropuestaPrograma] = None
        for i, p in enumerate(portafolio.propuestas):
            if p.id_propuesta == id_propuesta:
                idx_target = i
                prop_target = p
                break
                
        if prop_target is None or idx_target is None:
            raise ValueError(f"No se encontró ninguna propuesta con ID: {id_propuesta}")

        version_anterior = prop_target.version
        nueva_version = version_anterior + 1

        prompt_refinamiento = f"""
Eres el Vicerrector Académico y Máximo Experto en Diseño Curricular de la Fundación Universitaria Cafam (UniCafam), Escuela de Ingeniería y Ciencias Empresariales.

El directivo académico y usuario aprobador ha revisado la siguiente propuesta curricular y ha solicitado ajustes específicos mediante retroalimentación técnica y pedagógica.

======================================================================
PROPUESTA CURRICULAR ACTUAL (VERSIÓN {version_anterior}):
======================================================================
{prop_target.model_dump_json(indent=2)}

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
6. En el objeto JSON devuelto, incluye obligatoriamente una clave especial llamada "resumen_cambios_realizados" (texto conciso explicando los cambios puntuales aplicados frente a la versión anterior).

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
        modelos_candidatos = [self.model_name, "models/gemini-3.5-flash", "models/gemini-flash-latest"]
        modelos_probados = []
        for m in modelos_candidatos:
            if m not in modelos_probados:
                modelos_probados.append(m)

        raw_text = None
        ultimo_error = None
        for mod_name in modelos_probados:
            try:
                model = genai.GenerativeModel(mod_name)
                response = model.generate_content(prompt_refinamiento, request_options={"timeout": 600})
                raw_text = response.text.strip()
                if raw_text:
                    print(f"      ✓ Ajuste completado por {mod_name}")
                    break
            except Exception as e:
                print(f"      ⚠ Error con {mod_name}: {e}")
                ultimo_error = e
                if "429" in str(e) or "quota" in str(e).lower():
                    time.sleep(32)

        if not raw_text:
            raise RuntimeError(f"No fue posible refinar la propuesta con ningún modelo: {ultimo_error}")

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

        # Mantener historial anterior y anexar nuevo hito de auditoría
        historial_previo = list(prop_target.historial_revisiones)
        nuevo_registro = RegistroAuditoriaFeedback(
            id_registro=f"REV_{id_propuesta}_V{nueva_version}_{int(time.time())}",
            version_resultante=nueva_version,
            usuario_aprobador=usuario_aprobador,
            rol_usuario=rol_usuario,
            decision="SOLICITUD_AJUSTE",
            comentarios_feedback=feedback_humano,
            cambios_aplicados_resumen=resumen_cambios,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        historial_previo.append(nuevo_registro)
        propuesta_refinada.historial_revisiones = historial_previo

        # Actualizar portafolio y persistir
        portafolio.propuestas[idx_target] = propuesta_refinada
        self.guardar_portafolio(portafolio)
        print(f"[OK] Propuesta {id_propuesta} actualizada a v{nueva_version} en estado PENDIENTE_REVISION.")
        return propuesta_refinada, resumen_cambios

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
        portafolio = self.cargar_portafolio()
        target: Optional[PropuestaPrograma] = None
        for p in portafolio.propuestas:
            if p.id_propuesta == id_propuesta:
                target = p
                break

        if not target:
            raise ValueError(f"No se encontró la propuesta {id_propuesta}")

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
        print(f"[DECISIÓN REGISTRADA] {id_propuesta} marcada como {target.estado.value} por {usuario_aprobador}.")
        return target

if __name__ == "__main__":
    engine = CurriculumIntelligenceEngine(model_name="models/gemini-3.8-flash")
    resultado = engine.ejecutar_analisis_y_generacion()
    print("\n" + "="*70)
    print("DIAGNÓSTICO EJECUTIVO GENERADO POR LA IA:")
    print("="*70)
    print(f"Puntaje de Competitividad: {resultado.diagnostico.puntuacion_competitividad_mercado}/100")
    print(f"Resumen: {resultado.diagnostico.resumen_ejecutivo}\n")
    print("PROGRAMAS PROPUESTOS (FORMATO MIG UNICAFAM):")
    for p in resultado.propuestas:
        print(f"\n▶ [{p.tipo_propuesta}] {p.nombre_programa}")
        print(f"  - Título: {p.titulo_otorgado}")
        print(f"  - Créditos: {p.creditos_totales} | Duración: {p.duracion_estimada} | Modalidad: {p.modalidad_sugerida}")
        print(f"  - Impacto Salarial: {p.impacto_salarial_proyectado}")
        print(f"  - Módulos ({len(p.plan_estudios)}): {', '.join([m.nombre_modulo for m in p.plan_estudios])}")

