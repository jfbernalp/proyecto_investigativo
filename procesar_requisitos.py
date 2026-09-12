import re
import pandas as pd

def parse_requisitos_columna(requisitos_str):
    """
    Desglosa la cadena original de 'Requisitos' de CompuTrabajo en componentes atómicos:
    - Nivel educativo
    - Años de experiencia (numérico)
    - Conocimientos explícitos listados por la plataforma
    - Idiomas
    """
    if not isinstance(requisitos_str, str) or not requisitos_str.strip():
        return {
            "Nivel_Educacion": "No especificado",
            "Anios_Experiencia": None,
            "Conocimientos_Explicitos": [],
            "Idiomas": "No especificado"
        }

    partes = [p.strip() for p in requisitos_str.split("|")]
    
    nivel_educacion = "No especificado"
    anios_experiencia = None
    conocimientos = []
    idiomas = "No especificado"

    for parte in partes:
        # 1. Nivel de educación
        if parte.lower().startswith("educación mínima:") or parte.lower().startswith("educacion minima:"):
            nivel_educacion = re.sub(r"(?i)educaci[oó]n m[ií]nima:\s*", "", parte).strip()
        
        # 2. Años de experiencia
        elif "experiencia" in parte.lower():
            match = re.search(r"(\d+)\s*(?:año|ano|años|anos)?\s*de experiencia", parte, re.IGNORECASE)
            if match:
                anios_experiencia = int(match.group(1))
            elif "sin experiencia" in parte.lower() or "no requiere experiencia" in parte.lower():
                anios_experiencia = 0
            else:
                # Si solo dice "años de experiencia" sin número específico
                anios_experiencia = 1

        # 3. Conocimientos explícitos de CompuTrabajo
        elif parte.lower().startswith("conocimientos:"):
            raw_skills = re.sub(r"(?i)conocimientos:\s*", "", parte)
            conocimientos = [s.strip().title() for s in raw_skills.split(",") if s.strip()]

        # 4. Idiomas
        elif parte.lower().startswith("idiomas:"):
            idiomas = re.sub(r"(?i)idiomas:\s*", "", parte).strip()

    return {
        "Nivel_Educacion": nivel_educacion,
        "Anios_Experiencia": anios_experiencia,
        "Conocimientos_Explicitos": conocimientos,
        "Idiomas": idiomas
    }


# ==============================================================================
# TAXONOMÍA Y DICCIONARIO DE HABILIDADES TÉCNICAS (DATA SCIENCE & ANALYTICS)
# ==============================================================================
TAXONOMIA_HABILIDADES = {
    # Lenguajes de Programación y Consulta
    "Python": r"\bpython\b",
    "R": r"\b[rR]\b(?:\s*studio|\s*language|\s*lenguaje)?",
    "SQL": r"\bsql\b|\bpostgresql\b|\bmysql\b|\boracle\b|\bsql\s*server\b|\bpl/sql\b",
    "Scala": r"\bscala\b",
    "Java / C++": r"\bjava\b|\bc\+\+\b|\bc#\b",
    
    # Visualización y BI
    "Power BI": r"\bpower\s*bi\b|\bpowerbi\b|\bdax\b",
    "Tableau": r"\btableau\b",
    "Excel Avanzado": r"\bexcel\b|\bhojas\s*de\s*c[aá]lculo\b|\bvba\b",
    "Qlik": r"\bqlik\b|\bqlikview\b|\bqliksense\b",
    "Looker": r"\blooker\b|\blooker\s*studio\b",

    # Big Data y Computación Distribuida
    "Spark / PySpark": r"\bspark\b|\bpyspark\b",
    "Databricks": r"\bdatabricks\b",
    "Hadoop / Hive": r"\bhadoop\b|\bhive\b",
    "Kafka": r"\bkafka\b",

    # Cloud Computing
    "AWS": r"\baws\b|\bamazon\s*web\s*services\b|\bredshift\b|\bs3\b|\bec2\b",
    "Azure": r"\bazure\b|\bsynapse\b|\bazure\s*ml\b",
    "Google Cloud (GCP)": r"\bgcp\b|\bgoogle\s*cloud\b|\bbigquery\b",

    # Machine Learning, IA y Estadística
    "Machine Learning General": r"\bmachine\s*learning\b|\baprendizaje\s*autom[aá]tico\b|\bml\b",
    "Deep Learning": r"\bdeep\s*learning\b|\baprendizaje\s*profundo\b|\bredes\s*neuronales\b",
    "NLP / LLMs": r"\bnlp\b|\bprocesamiento\s*de\s*lenguaje\s*natural\b|\bllm\b|\btransformers\b|\bbert\b|\bgpt\b",
    "Computer Vision": r"\bcomputer\s*vision\b|\bvisi[oó]n\s*por\s*computador[a]?\b|\bopencv\b",
    "Scikit-Learn": r"\bscikit-learn\b|\bsklearn\b",
    "TensorFlow / Keras": r"\btensorflow\b|\bkeras\b",
    "PyTorch": r"\bpytorch\b",
    "Estadística / Modelamiento": r"\bestad[ií]stic[ao]\b|\bmodelamiento\b|\bmodelado\s*predictivo\b|\bseries\s*de\s*tiempo\b",

    # Ingeniería de Datos & MLOps
    "ETL / Pipelines de Datos": r"\betl\b|\bpipelines?\b|\bflujos\s*de\s*datos\b|\bairbyte\b|\bdbt\b",
    "Airflow": r"\bairflow\b",
    "Docker / Kubernetes": r"\bdocker\b|\bkubernetes\b|\bcontenedores\b",
    "Git / Control de Versiones": r"\bgit\b|\bgithub\b|\bgitlab\b",
    "Bases de Datos NoSQL": r"\bnosql\b|\bmongodb\b|\bcassandra\b|\bredis\b|\belasticsearch\b",
    "MLOps": r"\bmlops\b|\bmlflow\b"
}

def extraer_habilidades_texto(texto):
    """
    Busca ocurrencias de las habilidades del diccionario dentro del texto (Requisitos + Descripción).
    """
    if not isinstance(texto, str):
        return []
    
    encontradas = []
    for habilidad, patron in TAXONOMIA_HABILIDADES.items():
        if re.search(patron, texto, flags=re.IGNORECASE):
            encontradas.append(habilidad)
    return encontradas


def procesar_dataset_ofertas(ruta_excel_entrada="ofertas_computrabajo.xlsx", ruta_excel_salida="ofertas_analizadas.xlsx"):
    print(f"1. Cargando archivo: {ruta_excel_entrada}...")
    df = pd.read_excel(ruta_excel_entrada)

    # --------------------------------------------------------------------------
    # PASO 1: Desglosar la columna 'Requisitos' en campos individuales
    # --------------------------------------------------------------------------
    print("2. Desglosando columna 'Requisitos' en Educación, Experiencia y Habilidades...")
    parsed_reqs = df["Requisitos"].apply(parse_requisitos_columna)
    
    df_parsed = pd.DataFrame(parsed_reqs.tolist())
    df_estructurado = pd.concat([df, df_parsed], axis=1)

    # --------------------------------------------------------------------------
    # PASO 2: Minería de texto para detectar habilidades técnicas en el texto completo
    # --------------------------------------------------------------------------
    print("3. Extrayendo habilidades técnicas clave con NLP/Regex...")
    texto_completo = (
        df_estructurado["Nombre Oferta"].fillna("") + " " +
        df_estructurado["Requisitos"].fillna("") + " " + 
        df_estructurado["Descripcion"].fillna("")
    )
    
    df_estructurado["Habilidades_Tecnicas"] = texto_completo.apply(extraer_habilidades_texto)
    df_estructurado["Total_Habilidades_Detectadas"] = df_estructurado["Habilidades_Tecnicas"].apply(len)

    # --------------------------------------------------------------------------
    # PASO 3: Formato Desagregado (Tidy / Long Format) para conteos y análisis
    # --------------------------------------------------------------------------
    print("4. Generando dataset desagregado (1 fila por habilidad requerida)...")
    df_desagregado = df_estructurado.explode("Habilidades_Tecnicas")
    df_desagregado = df_desagregado.dropna(subset=["Habilidades_Tecnicas"])
    df_desagregado = df_desagregado.rename(columns={"Habilidades_Tecnicas": "Habilidad"})

    # Columnas seleccionadas para el formato largo
    columnas_desagregadas = [
        "Codigo", "Nombre Oferta", "Empresa", "Ubicacion", "Salario", 
        "Modalidad", "Nivel_Educacion", "Anios_Experiencia", "Habilidad", "URL"
    ]
    df_desagregado_final = df_desagregado[columnas_desagregadas]

    # --------------------------------------------------------------------------
    # PASO 4: Resumen Estadístico (Ranking de Habilidades)
    # --------------------------------------------------------------------------
    print("5. Calculando estadísticas de frecuencia...")
    total_ofertas = len(df)
    resumen_habilidades = (
        df_desagregado["Habilidad"]
        .value_counts()
        .reset_index()
    )
    resumen_habilidades.columns = ["Habilidad", "Total_Ofertas_Demandadas"]
    resumen_habilidades["Porcentaje_Demanda_%"] = (
        (resumen_habilidades["Total_Ofertas_Demandadas"] / total_ofertas) * 100
    ).round(2)

    # --------------------------------------------------------------------------
    # PASO 5: Exportar a un único Excel con múltiples hojas analíticas
    # --------------------------------------------------------------------------
    print(f"6. Guardando resultados en: {ruta_excel_salida}...")
    
    # Preparar el dataframe principal para Excel (convertir listas a string para que se visualicen bien)
    df_estructurado_export = df_estructurado.copy()
    df_estructurado_export["Conocimientos_Explicitos"] = df_estructurado_export["Conocimientos_Explicitos"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df_estructurado_export["Habilidades_Tecnicas"] = df_estructurado_export["Habilidades_Tecnicas"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    with pd.ExcelWriter(ruta_excel_salida, engine="openpyxl") as writer:
        # Hoja 1: Resumen y ranking de habilidades más demandadas
        resumen_habilidades.to_excel(writer, sheet_name="Ranking_Habilidades", index=False)
        
        # Hoja 2: Dataset desagregado (Long Format - Ideal para Tablas Dinámicas y Gráficos)
        df_desagregado_final.to_excel(writer, sheet_name="Habilidades_Desagregadas", index=False)
        
        # Hoja 3: Ofertas estructuradas con columnas limpias (Wide Format)
        df_estructurado_export.to_excel(writer, sheet_name="Ofertas_Estructuradas", index=False)

    print("\n" + "=" * 70)
    print("PROCESAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    print(f"Total de ofertas analizadas: {total_ofertas}")
    print(f"Total de menciones de habilidades: {len(df_desagregado_final)}")
    print(f"Habilidades únicas identificadas: {len(resumen_habilidades)}")
    print("\nTop 10 Habilidades más solicitadas:")
    print(resumen_habilidades.head(10).to_string(index=False))

if __name__ == "__main__":
    procesar_dataset_ofertas()
