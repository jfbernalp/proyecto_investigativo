import re
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
from src.processing.taxonomies import TAXONOMIA_HABILIDADES

def parse_requisitos_columna(requisitos_str: str) -> Dict[str, Any]:
    """
    Desglosa la cadena de Requisitos en componentes atómicos.
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
        # Nivel educativo
        if parte.lower().startswith("educación mínima:") or parte.lower().startswith("educacion minima:"):
            nivel_educacion = re.sub(r"(?i)educaci[oó]n m[ií]nima:\s*", "", parte).strip()
        
        # Años de experiencia
        elif "experiencia" in parte.lower():
            match = re.search(r"(\d+)\s*(?:año|ano|años|anos)?\s*de experiencia", parte, re.IGNORECASE)
            if match:
                anios_experiencia = int(match.group(1))
            elif "sin experiencia" in parte.lower() or "no requiere experiencia" in parte.lower():
                anios_experiencia = 0
            else:
                anios_experiencia = 1

        # Conocimientos explícitos
        elif parte.lower().startswith("conocimientos:"):
            raw_skills = re.sub(r"(?i)conocimientos:\s*", "", parte)
            conocimientos = [s.strip().title() for s in raw_skills.split(",") if s.strip()]

        # Idiomas
        elif parte.lower().startswith("idiomas:"):
            idiomas = re.sub(r"(?i)idiomas:\s*", "", parte).strip()

    return {
        "Nivel_Educacion": nivel_educacion,
        "Anios_Experiencia": anios_experiencia,
        "Conocimientos_Explicitos": conocimientos,
        "Idiomas": idiomas
    }

def extraer_habilidades_texto(texto: str) -> List[str]:
    """
    Busca ocurrencias de la taxonomía de habilidades dentro de un texto usando expresiones regulares.
    """
    if not isinstance(texto, str):
        return []
    encontradas = []
    for habilidad, patron in TAXONOMIA_HABILIDADES.items():
        if re.search(patron, texto, flags=re.IGNORECASE):
            encontradas.append(habilidad)
    return encontradas

from src.processing.cleaner import es_oferta_relevante, clasificar_rol_tecnico

def procesar_pipeline_nlp(df_input: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de NLP, normalización y estructuración,
    filtrando previamente las ofertas irrelevantes y clasificando el rol técnico real.
    """
    print("=" * 70)
    print("EJECUTANDO PIPELINE DE MINERÍA DE TEXTO Y DESAGREGACIÓN DE REQUISITOS")
    print("=" * 70)

    # 0. Filtro estricto de relevancia temática (Data Science / Analytics)
    print(f"0. Validando relevancia temática sobre {len(df_input)} ofertas...")
    es_valida = df_input.apply(
        lambda row: es_oferta_relevante(str(row.get("Nombre Oferta", "")), str(row.get("Descripcion", ""))),
        axis=1
    )
    df_filtrado = df_input[es_valida].copy()
    descartadas = len(df_input) - len(df_filtrado)
    print(f"   [FILTRO DE CALIDAD] {len(df_filtrado)} ofertas relevantes conservadas. {descartadas} ofertas no relacionadas descartadas.")

    if df_filtrado.empty:
        print("[ADVERTENCIA] No quedaron ofertas relevantes tras el filtro.")
        return pd.DataFrame()

    # Clasificar el rol real a partir del título
    df_filtrado["Rol_Buscado"] = df_filtrado["Nombre Oferta"].apply(clasificar_rol_tecnico)

    # 1. Parsing de requisitos
    print("1. Extrayendo educación, experiencia y conocimientos...")
    parsed_reqs = df_filtrado["Requisitos"].apply(parse_requisitos_columna)
    df_parsed = pd.DataFrame(parsed_reqs.tolist(), index=df_filtrado.index)
    df_estructurado = pd.concat([df_filtrado, df_parsed], axis=1)

    # 2. Minería NLP sobre texto completo
    print("2. Extrayendo habilidades técnicas con expresiones regulares...")
    texto_completo = (
        df_estructurado["Nombre Oferta"].fillna("") + " " +
        df_estructurado["Requisitos"].fillna("") + " " + 
        df_estructurado["Descripcion"].fillna("")
    )
    df_estructurado["Habilidades_Tecnicas"] = texto_completo.apply(extraer_habilidades_texto)
    df_estructurado["Total_Habilidades_Detectadas"] = df_estructurado["Habilidades_Tecnicas"].apply(len)

    # 3. Formato Largo Desagregado
    print("3. Generando formato largo (Tidy Data)...")
    df_desagregado = df_estructurado.explode("Habilidades_Tecnicas").dropna(subset=["Habilidades_Tecnicas"])
    df_desagregado = df_desagregado.rename(columns={"Habilidades_Tecnicas": "Habilidad"})

    # 4. Resumen de Frecuencias
    total_ofertas = len(df_estructurado)
    resumen_habilidades = df_desagregado["Habilidad"].value_counts().reset_index()
    resumen_habilidades.columns = ["Habilidad", "Total_Ofertas_Demandadas"]
    resumen_habilidades["Porcentaje_Demanda_%"] = ((resumen_habilidades["Total_Ofertas_Demandadas"] / total_ofertas) * 100).round(2)

    # 5. Guardado en Excel multihoja seguro
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_export = df_estructurado.copy()
    df_export["Conocimientos_Explicitos"] = df_export["Conocimientos_Explicitos"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df_export["Habilidades_Tecnicas"] = df_export["Habilidades_Tecnicas"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    from src.processing.cleaner import sanitizar_dataframe_para_excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        sanitizar_dataframe_para_excel(resumen_habilidades).to_excel(writer, sheet_name="Ranking_Habilidades", index=False)
        sanitizar_dataframe_para_excel(df_desagregado).to_excel(writer, sheet_name="Habilidades_Desagregadas", index=False)
        sanitizar_dataframe_para_excel(df_export).to_excel(writer, sheet_name="Ofertas_Estructuradas", index=False)

    print(f"[NLP ENGINE] Archivo procesado guardado en: {output_path}")
    return df_estructurado
