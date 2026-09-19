"""
Módulo de Procesamiento e Ingesta de Malla Curricular de UniCafam.
Extrae metadatos, carrera/programa, créditos, competencias, saberes y herramientas tecnológicas
a partir de los microcurrículos en formato Excel oficial.
"""

import os
import glob
import re
import openpyxl
import pandas as pd
from typing import Dict, List, Tuple, Any

# Diccionario de Tecnologías y Habilidades para Mapeo Curricular
DICCIONARIO_HABILIDADES_TECH = {
    "Python": [r"\bpython\b", r"\bpandas\b", r"\bnumpy\b", r"\bmatplotlib\b", r"\bseaborn\b"],
    "SQL / Bases de Datos Relacionales": [r"\bsql\b", r"\brelacional", r"\bpostgres", r"\bmysql\b", r"\boracle\b", r"\bmodelo relacional\b", r"\bdiseño de base de datos\b"],
    "Bases de Datos NoSQL": [r"\bnosql\b", r"\bmongodb\b", r"\bcassandra\b", r"\bredis\b", r"\bgrafos\b", r"\bneo4j\b", r"\bdocumentos\b"],
    "Big Data & Arquitecturas Distribuidas": [r"\bbig data\b", r"\bhadoop\b", r"\bspark\b", r"\bpyspark\b", r"\bmapreduce\b", r"\bhive\b", r"\bdata lake\b"],
    "Minería de Datos & KDD": [r"\bminer[ií]a de datos\b", r"\bkdd\b", r"\bpatrones\b", r"\bclustering\b", r"\breglas de asociaci[oó]n\b", r"\bclasificaci[oó]n\b"],
    "Analítica Predictiva & Machine Learning": [r"\banal[ií]tica predictiva\b", r"\bmachine learning\b", r"\baprendizaje autom[aá]tico\b", r"\bregresi[oó]n\b", r"\b[aá]rboles de decisi[oó]n\b", r"\brandom forest\b", r"\bscikit-learn\b"],
    "Procesamiento de Lenguaje Natural (NLP)": [r"\bnlp\b", r"\bprocesamiento de texto\b", r"\btécnicas de informaci[oó]n\b", r"\btext mining\b", r"\btf-idf\b", r"\bcorpus\b", r"\btweet\b", r"\bsentimiento\b"],
    "Analítica Descriptiva & Visualización": [r"\banal[ií]tica descriptiva\b", r"\bvisualizaci[oó]n\b", r"\bpower bi\b", r"\btableau\b", r"\bdashboards\b", r"\btableros\b", r"\bgr[aá]ficos estad[ií]sticos\b"],
    "Excel Avanzado / Hojas de Cálculo": [r"\bexcel\b", r"\bhojas? de c[aá]lculo\b", r"\btablas din[aá]micas\b"],
    "R / Estadística Computacional": [r"\b\br\b", r"\brstudio\b", r"\bpaquetes de r\b"],
    "Estadística & Probabilidad": [r"\bestad[ií]stica\b", r"\bprobabilidad\b", r"\binferencia\b", r"\bdistribuciones\b", r"\bmuestreo\b", r"\bhip[oó]tesis\b"],
    "Investigación de Operaciones & Optimización": [r"\binvestigaci[oó]n de operaciones\b", r"\boptimizaci[oó]n\b", r"\bprogramaci[oó]n lineal\b", r"\bsimplex\b", r"\bteor[ií]a de colas\b"],
    "Gobierno de Datos & Calidad": [r"\bgobierno de datos\b", r"\bdata governance\b", r"\bcalidad de datos\b", r"\bdama\b", r"\bdmbok\b", r"\bmetadatos\b", r"\blineaje\b"],
    "Seguridad de la Información & Ciberseguridad": [r"\bseguridad de la informaci[oó]n\b", r"\bciberseguridad\b", r"\bcifrado\b", r"\bprivacidad\b", r"\biso 27001\b", r"\bvulnerabilidades\b"],
    "Algoritmos & Lógica de Programación": [r"\balgor[ií]tmos\b", r"\bpseudoc[oó]digo\b", r"\bestructuras? de datos\b", r"\bl[oó]gica de programaci[oó]n\b", r"\bcomplejidad\b"],
    "Matemáticas Aplicadas & Álgebra Lineal": [r"\b[aá]lgebra lineal\b", r"\bmatrices\b", r"\bvectores\b", r"\bc[aá]lculo diferencial\b", r"\bc[aá]lculo integral\b", r"\bderivadas\b", r"\bintegrales\b"],
    "Gestión de Proyectos & Metodologías Ágiles": [r"\bgesti[oó]n de proyectos\b", r"\bscrum\b", r"\b[aá]gil\b", r"\bpmi\b", r"\bcronograma\b"],
    "Toma de Decisiones & Estrategia": [r"\btoma de decisiones\b", r"\bestilos de decisi[oó]n\b", r"\bkpis\b", r"\bm[eé]tricas de negocio\b"]
}

SEMESTRE_MAP = {
    "1": 1, "I": 1, "PRIMERO": 1, "PRIMER": 1, "1_PRIMER SEMESTRE": 1,
    "2": 2, "II": 2, "SEGUNDO": 2, "2_SEGUNDO SEMESTRE": 2,
    "3": 3, "III": 3, "TERCERO": 3, "TERCER": 3, "3_TERCER SEMESTRE": 3,
    "4": 4, "IV": 4, "CUARTO": 4, "4_CUARTO SEMESTRE": 4,
    "5": 5, "V": 5, "QUINTO": 5, "5_QUINTO SEMESTRE": 5,
    "6": 6, "VI": 6, "SEXTO": 6, "6_SEXTO SEMESTRE": 6
}

def normalizar_programa(prog_raw: str, path_file: str) -> str:
    """Estandariza el nombre de la carrera / programa académico."""
    p = str(prog_raw).strip()
    if not p or p == "None":
        # Intentar inferir de la carpeta contenedora
        for part in path_file.split(os.sep):
            if "TECNOLOGI" in part.upper() or "INGENIERI" in part.upper() or "ESPECIALIZA" in part.upper():
                p = part
                break
    
    # Normalización canónica
    p_up = p.upper()
    if "ANÁLISIS" in p_up or "ANALISIS" in p_up or "GESTIÓN DE DATOS" in p_up or "GESTION DE DATOS" in p_up or "TAGD" in p_up:
        return "Tecnología en Análisis y Gestión de Datos"
    elif "INGENIERÍA DE SISTEMAS" in p_up or "SISTEMAS" in p_up:
        return "Ingeniería de Sistemas"
    elif "ESPECIALIZACIÓN" in p_up:
        return "Especialización en Analítica Aplicada"
    elif "MAESTRÍA" in p_up:
        return "Maestría en Ciencia de Datos"
    return p if p else "Tecnología en Análisis y Gestión de Datos"

def normalizar_semestre(sem_raw: str, path_folder: str = "") -> Tuple[int, str]:
    """Determina el semestre numérico (1-5) y el nombre normalizado."""
    s_clean = str(sem_raw).strip().upper()
    if s_clean in SEMESTRE_MAP:
        ordinal = SEMESTRE_MAP[s_clean]
    else:
        match = re.search(r'(\d)_([A-Za-z]+ Semestre)', path_folder, re.IGNORECASE)
        if match:
            ordinal = int(match.group(1))
        else:
            ordinal = 1
            
    nombres = {
        1: "Primer Semestre",
        2: "Segundo Semestre",
        3: "Tercer Semestre",
        4: "Cuarto Semestre",
        5: "Quinto Semestre",
        6: "Sexto Semestre"
    }
    return ordinal, nombres.get(ordinal, f"Semestre {ordinal}")

class CurriculumParser:
    """Extractor especializado para microcurrículos de UniCafam."""
    
    def __init__(self, root_dir: str = "data/curriculo_unicafam"):
        self.root_dir = root_dir

    def parsear_archivo(self, filepath: str) -> Dict[str, Any]:
        """Extrae la información estructurada de un único archivo Excel."""
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet = wb.active
        
        info = {
            "archivo": os.path.basename(filepath),
            "ruta_completa": filepath,
            "programa_academico_raw": None,
            "codigo_materia": None,
            "nombre_materia": None,
            "semestre_raw": None,
            "creditos": 2,
            "horas_tfd": 32,
            "horas_tti": 64,
            "modalidad": "Presencial",
            "area_formacion": "Específica",
            "justificacion": "",
            "competencia_general": "",
            "saberes_especificos": [],
            "habilidades_destrezas": [],
            "actitudes": [],
            "resultados_aprendizaje": [],
            "recursos_software": [],
            "bibliografia": ""
        }
        
        filas = list(sheet.iter_rows(values_only=True))
        
        for r_idx, row in enumerate(filas):
            row_clean = [str(c).strip() for c in row if c is not None and str(c).strip()]
            for c_idx, cell in enumerate(row_clean):
                cell_up = cell.upper()
                
                # Programa / Carrera
                if "PROGRAMA:" in cell_up and c_idx + 1 < len(row_clean):
                    info["programa_academico_raw"] = row_clean[c_idx + 1]
                
                # Nombre de la materia
                if "NOMBRE UNIDAD DE APRENDIZAJE" in cell_up and c_idx + 1 < len(row_clean):
                    info["nombre_materia"] = row_clean[c_idx + 1]
                
                # Créditos
                if "CRÉDITOS:" in cell_up or "CREDITOS:" in cell_up:
                    if c_idx + 1 < len(row_clean):
                        try:
                            info["creditos"] = int(re.sub(r"[^\d]", "", row_clean[c_idx + 1]))
                        except:
                            pass
                
                # Horas TFD y TTI
                if "TFD:" in cell_up and c_idx + 1 < len(row_clean):
                    try:
                        info["horas_tfd"] = int(re.sub(r"[^\d]", "", row_clean[c_idx + 1]))
                    except:
                        pass
                if "TTI:" in cell_up and c_idx + 1 < len(row_clean):
                    try:
                        info["horas_tti"] = int(re.sub(r"[^\d]", "", row_clean[c_idx + 1]))
                    except:
                        pass
                        
                # Modalidad
                if "MODALIDAD:" in cell_up and c_idx + 1 < len(row_clean):
                    info["modalidad"] = row_clean[c_idx + 1]
                
                # Semestre
                if "SEMESTRE:" in cell_up and c_idx + 1 < len(row_clean):
                    info["semestre_raw"] = row_clean[c_idx + 1]
                
                # Código
                if "CÓDIGO:" in cell_up and c_idx + 1 < len(row_clean):
                    info["codigo_materia"] = row_clean[c_idx + 1]
                
                # Área de formación
                if "ÁREA DE FORMACIÓN:" in cell_up and c_idx + 1 < len(row_clean):
                    info["area_formacion"] = row_clean[c_idx + 1]
                
                # Justificación
                if "JUSTIFICACIÓN:" in cell_up and c_idx + 1 < len(row_clean):
                    info["justificacion"] = row_clean[c_idx + 1]
                
                # Recursos de Apoyo / Software
                if "RECURSOS DE APOYO" in cell_up and c_idx + 1 < len(row_clean):
                    info["recursos_software"].append(row_clean[c_idx + 1])
                
                # Bibliografía
                if "BIBLIOGRAFÍA" in cell_up and c_idx + 1 < len(row_clean):
                    info["bibliografia"] = row_clean[c_idx + 1]

        # Normalizar Programa / Carrera
        info["programa_academico"] = normalizar_programa(info["programa_academico_raw"], filepath)

        # Normalizar código y nombre si no se encontraron en encabezados estándar
        if not info["nombre_materia"]:
            base_name = os.path.basename(filepath).replace(".xlsx", "")
            base_name = re.sub(r"^\d+_", "", base_name).replace("_V2", "").replace("_", " ").strip()
            info["nombre_materia"] = base_name.upper()
            
        if not info["codigo_materia"]:
            info["codigo_materia"] = f"UCAF_{abs(hash(info['nombre_materia'])) % 1000000:06d}"

        # Extraer bloques de tablas de Saberes y Competencias
        for r_idx, row in enumerate(filas):
            row_str = " ".join([str(c) for c in row if c is not None]).upper()
            if "COMPETENCIA" in row_str and "SABERES" in row_str:
                for sub_r in range(r_idx + 1, min(r_idx + 10, len(filas))):
                    sub_cells = [str(c).strip() for c in filas[sub_r] if c is not None and str(c).strip()]
                    if not sub_cells or "RESULTADO DE" in " ".join(sub_cells).upper():
                        break
                    if len(sub_cells) >= 1 and not info["competencia_general"]:
                        info["competencia_general"] = sub_cells[0]
                    if len(sub_cells) >= 2:
                        info["saberes_especificos"].append(sub_cells[1])
                    if len(sub_cells) >= 3:
                        info["habilidades_destrezas"].append(sub_cells[2])
                    if len(sub_cells) >= 4:
                        info["actitudes"].append(sub_cells[3])

        # Normalizar Semestre
        sem_ord, sem_nom = normalizar_semestre(info["semestre_raw"], filepath)
        info["semestre_ordinal"] = sem_ord
        info["semestre_nombre"] = sem_nom
        
        return info

    def extraer_habilidades_tecnologicas(self, info_materia: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mapea los textos de la materia contra el diccionario de habilidades."""
        textos_totales = " ".join([
            info_materia.get("nombre_materia", ""),
            info_materia.get("justificacion", ""),
            info_materia.get("competencia_general", ""),
            " ".join(info_materia.get("saberes_especificos", [])),
            " ".join(info_materia.get("habilidades_destrezas", [])),
            " ".join(info_materia.get("recursos_software", [])),
            info_materia.get("bibliografia", "")
        ]).lower()
        
        habilidades_encontradas = []
        
        for hab_canon, regex_list in DICCIONARIO_HABILIDADES_TECH.items():
            for rgx in regex_list:
                match = re.search(rgx, textos_totales, re.IGNORECASE)
                if match:
                    habilidades_encontradas.append({
                        "programa_academico": info_materia["programa_academico"],
                        "codigo_materia": info_materia["codigo_materia"],
                        "nombre_materia": info_materia["nombre_materia"],
                        "semestre_ordinal": info_materia["semestre_ordinal"],
                        "semestre_nombre": info_materia["semestre_nombre"],
                        "creditos": info_materia["creditos"],
                        "habilidad_tecnologica": hab_canon,
                        "termino_detectado": match.group(0),
                        "area_formacion": info_materia["area_formacion"]
                    })
                    break
                    
        return habilidades_encontradas

    def procesar_todo(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Procesa todos los Excels del directorio y genera los DataFrames normalizados."""
        archivos = sorted(glob.glob(os.path.join(self.root_dir, "**/*.xlsx"), recursive=True))
        print(f"[CURRICULUM PARSER] Procesando {len(archivos)} microcurrículos en {self.root_dir}...")
        
        lista_materias = []
        lista_habilidades = []
        lista_saberes_detalle = []
        
        for f in archivos:
            info = self.parsear_archivo(f)
            
            # 1. Dimensión Malla Curricular
            lista_materias.append({
                "programa_academico": str(info["programa_academico"]).strip(),
                "codigo_materia": str(info["codigo_materia"]).strip(),
                "nombre_materia": str(info["nombre_materia"]).strip(),
                "semestre_ordinal": int(info["semestre_ordinal"]),
                "semestre_nombre": str(info["semestre_nombre"]).strip(),
                "creditos": int(info["creditos"]),
                "horas_tfd": int(info["horas_tfd"]),
                "horas_tti": int(info["horas_tti"]),
                "horas_totales": int(info["horas_tfd"]) + int(info["horas_tti"]),
                "modalidad": str(info["modalidad"]).strip(),
                "area_formacion": str(info["area_formacion"]).strip(),
                "competencia_general": str(info["competencia_general"]).strip(),
                "justificacion": str(info["justificacion"]).strip(),
                "archivo_origen": str(info["archivo"]).strip()
            })
            
            # 2. Habilidades Tecnológicas Mapeadas
            habs = self.extraer_habilidades_tecnologicas(info)
            lista_habilidades.extend(habs)
            
            # 3. Detalle de Saberes
            for idx, saber in enumerate(info["saberes_especificos"]):
                lista_saberes_detalle.append({
                    "programa_academico": str(info["programa_academico"]).strip(),
                    "codigo_materia": str(info["codigo_materia"]).strip(),
                    "orden_tema": idx + 1,
                    "saber_especifico": str(saber).strip()
                })
                
        df_malla = pd.DataFrame(lista_materias)
        df_habilidades = pd.DataFrame(lista_habilidades)
        df_saberes = pd.DataFrame(lista_saberes_detalle)
        
        print(f"[OK] {len(df_malla)} materias procesadas.")
        print(f"[OK] {len(df_habilidades)} competencias tecnológicas mapeadas.")
        print(f"[OK] {len(df_saberes)} saberes específicos desagregados.")
        
        return df_malla, df_habilidades, df_saberes

if __name__ == "__main__":
    parser = CurriculumParser()
    df_m, df_h, df_s = parser.procesar_todo()
    print("\n--- RESUMEN POR PROGRAMA Y SEMESTRE ---")
    print(df_m.groupby(["programa_academico", "semestre_ordinal", "semestre_nombre"])[["nombre_materia", "creditos"]].agg({"nombre_materia": "count", "creditos": "sum"}).reset_index())
