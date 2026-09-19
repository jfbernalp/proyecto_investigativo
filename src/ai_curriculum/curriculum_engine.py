"""
Motor de Inteligencia Curricular con IA (Gemma 4 / Gemini).
Orquesta el análisis cuantitativo de brechas laborales y diseña propuestas académicas de alta competitividad
bajo los lineamientos del Decreto 1330 del Ministerio de Educación Nacional de Colombia (MEN).
"""

import os
import re
import time
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import google.generativeai as genai
from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ai_curriculum.gap_analyzer import CurriculumGapAnalyzer
from src.ai_curriculum.curriculum_schemas import PortafolioRecomendacionesIA

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

    def __init__(self, model_name: str = "gemma-4-26b-a4b-it"):
        cargar_variables_entorno()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno o archivo .env")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.gap_analyzer = CurriculumGapAnalyzer()

    def _construir_prompt_contextual(self, datos_analiticos: Dict[str, Any]) -> str:
        """Construye el prompt detallado con datos cuantitativos reales y marco normativo MEN."""
        
        resumen = datos_analiticos["resumen_ejecutivo"]
        fortalezas = datos_analiticos["fortalezas"][:8]
        brechas_criticas = datos_analiticos["brechas_criticas_mercado"][:10]
        brechas_salario = datos_analiticos["brechas_alto_valor_economico"][:6]
        roles = datos_analiticos["roles_mas_demandados"][:5]
        salarios = datos_analiticos["salarios_por_mercado"]

        prompt = f"""
Eres el Vicerrector Académico y Experto en Diseño Curricular de la Fundación Universitaria Cafam (UniCafam).
Tu labor es auditar el programa 'Tecnología en Análisis y Gestión de Datos' (83 créditos, 5 semestres) 
frente a los datos reales del mercado laboral (317 vacantes analizadas en Colombia y Remoto Internacional).

======================================================================
DATOS CUANTITATIVOS DUROS DEL OBSERVATORIO LABORAL:
======================================================================
1. Resumen Global:
   - Ofertas analizadas: {resumen['total_vacantes']} vacantes.
   - Créditos del programa actual: {resumen['total_creditos_programa']} créditos (32 asignaturas).
   - Cobertura actual de mercado: {resumen['cobertura_porcentual_mercado']}%

2. Roles Más Demandados:
   {json.dumps(roles, ensure_ascii=False, indent=2)}

3. Panorama Salarial:
   {json.dumps(salarios, ensure_ascii=False, indent=2)}

4. Top Fortalezas UniCafam:
   {json.dumps(fortalezas, ensure_ascii=False, indent=2)}

5. Principales Brechas Críticas (GAPs con 0 materias en UniCafam):
   {json.dumps(brechas_criticas, ensure_ascii=False, indent=2)}

6. Brechas de Alto Salario (> $8M COP local / > $20M COP remoto):
   {json.dumps(brechas_salario, ensure_ascii=False, indent=2)}

======================================================================
MARCO REGULATORIO Y PEDAGÓGICO DE COLOMBIA (MEN DECRETO 1330):
======================================================================
- 1 Crédito Académico = 48 horas totales (16 horas TFD - Acompañamiento Docente, 32 horas TTI - Trabajo Independiente).
- RAEs redactados con verbos de desempeño observable (Taxonomía de Bloom).
- Diseña exactamente estas 4 propuestas académicas en la clave 'propuestas':
  1. 'Electiva de Profundización' (Pregrado Tecnológico): 2 materias de 3 créditos (ej: Cloud Data Architecture y MLOps & Modern Data Stack).
  2. 'Microcredencial / Certificación Corta': 1 programa ágil de 2 créditos / 96 horas (ej: Business Intelligence Avanzado & DAX con Power BI).
  3. 'Especialización Universitaria' (Posgrado Formal): 1 programa de 2 semestres, 24 créditos (ej: Especialización en Ingeniería de Datos y Cloud).
  4. 'Maestría Aplicada' (Posgrado): 1 maestría de 4 semestres, 48 créditos (ej: Maestría en Inteligencia Artificial y Analítica Estratégica).

======================================================================
ESQUEMA JSON OBLIGATORIO DE RESPUESTA:
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
      "nombre_programa": "Nombre del Programa",
      "titulo_otorgado": "Título o Certificado",
      "nivel_academico": "Pregrado",
      "duracion_estimada": "1 semestre",
      "creditos_totales": 6,
      "horas_totales": 288,
      "modalidad_sugerida": "Híbrida / PAT",
      "perfil_ingreso": "Perfil del aspirante...",
      "perfil_egreso": "Competencias adquiridas...",
      "roles_ocupacionales_objetivo": ["Data Engineer Junior", "Cloud Data Practitioner"],
      "impacto_salarial_proyectado": "+30% de prima salarial sobre la media local",
      "plan_estudios": [
        {{
          "nombre_modulo": "Arquitecturas de Datos en la Nube (AWS & Azure)",
          "semestre_sugerido": 4,
          "creditos": 3,
          "horas_tfd": 48,
          "horas_tti": 96,
          "stack_tecnologico": ["AWS S3", "AWS Glue", "Azure Data Factory"],
          "resultados_aprendizaje_esperados_rae": ["Implementar canalizaciones de datos escalables utilizando servicios cloud de almacenamiento y procesamiento."],
          "justificacion_demanda_laboral": "El 22.5% de las vacantes exige conocimientos en nubes públicas."
        }}
      ]
    }}
  ]
}}
```
"""
        return prompt

    def ejecutar_analisis_y_generacion(self) -> PortafolioRecomendacionesIA:
        """Ejecuta el pipeline de análisis determinístico + inferencia Gemma/Gemini."""
        print("[1/4] Extrayendo y calculando matriz de brechas curriculares vs mercado laboral...")
        datos_analiticos = self.gap_analyzer.calcular_matriz_brechas()

        print(f"[2/4] Construyendo prompt pedagógico y regulatorio ({self.model_name})...")
        prompt = self._construir_prompt_contextual(datos_analiticos)

        print(f"[3/4] Invocando la API de Google ({self.model_name})...")
        model = genai.GenerativeModel(self.model_name)

        response = model.generate_content(prompt, request_options={"timeout": 600})
        raw_text = response.text.strip()

        print("[4/4] Validando contrato de datos con Pydantic...")
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
        return portafolio

if __name__ == "__main__":
    engine = CurriculumIntelligenceEngine(model_name="gemma-4-26b-a4b-it")
    resultado = engine.ejecutar_analisis_y_generacion()
    print("\n" + "="*70)
    print("DIAGNÓSTICO EJECUTIVO GENERADO POR LA IA:")
    print("="*70)
    print(f"Puntaje de Competitividad: {resultado.diagnostico.puntuacion_competitividad_mercado}/100")
    print(f"Resumen: {resultado.diagnostico.resumen_ejecutivo}\n")
    print("PROGRAMAS PROPUESTOS:")
    for p in resultado.propuestas:
        print(f"\n▶ [{p.tipo_propuesta}] {p.nombre_programa}")
        print(f"  - Título: {p.titulo_otorgado}")
        print(f"  - Créditos: {p.creditos_totales} | Duración: {p.duracion_estimada} | Modalidad: {p.modalidad_sugerida}")
        print(f"  - Impacto Salarial: {p.impacto_salarial_proyectado}")
        print(f"  - Módulos ({len(p.plan_estudios)}): {', '.join([m.nombre_modulo for m in p.plan_estudios])}")
