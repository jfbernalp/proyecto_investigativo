"""
Analizador Cuantitativo de Brechas (GAP Analysis) entre el Mercado Laboral y el Currículo de UniCafam.
Cruza la demanda real de habilidades con la oferta académica formal para alimentar el motor de IA.

El lado del mercado sale del contexto versionado (contexto_mercado.py, base del observatorio): sin
salarios rellenados ni brechas "de alto salario" (REGLA DE ORO: no inventar cifras).
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.processing.taxonomies import CLASIFICACION_CATEGORIAS

CURRICULUM_DB_PATH = BASE_DIR / "data" / "curriculo_unicafam" / "curriculo_unicafam.db"

def obtener_categoria_skill(habilidad: str) -> str:
    """Devuelve la categoría funcional de una habilidad según la taxonomía estándar."""
    for cat, skills in CLASIFICACION_CATEGORIAS.items():
        if habilidad in skills:
            return cat
    return "Otras Tecnologías"

class CurriculumGapAnalyzer:
    """
    Motor analítico determinístico para cruzar la oferta académica de UniCafam
    con las demandas y salarios del mercado laboral.
    """

    def __init__(self, curriculum_db: Optional[Path] = None):
        self.curriculum_db = curriculum_db or CURRICULUM_DB_PATH

    def _get_curriculum_connection(self) -> sqlite3.Connection:
        # Solo lectura: si la base no existe, sqlite crearía un archivo vacío y el error saldría más tarde
        # como "no such table" (pasó en el servidor: *.db no se versiona)
        if not Path(self.curriculum_db).is_file() or Path(self.curriculum_db).stat().st_size == 0:
            raise RuntimeError(
                f"No existe la base curricular {self.curriculum_db}. Constrúyala desde los Excel versionados con: "
                "python src/curriculum/curriculum_db_sync.py")
        return sqlite3.connect(f"file:{self.curriculum_db}?mode=ro", uri=True)

    def obtener_metricas_curriculo(self) -> Dict[str, Any]:
        """Extrae la estructura curricular y las habilidades enseñadas en UniCafam."""
        with self._get_curriculum_connection() as con:
            query_malla = """
            SELECT 
                semestre_ordinal,
                semestre_nombre,
                codigo_materia,
                nombre_materia,
                creditos,
                horas_tfd,
                horas_tti,
                horas_totales,
                area_formacion,
                modalidad,
                competencia_general
            FROM dim_malla_curricular
            ORDER BY semestre_ordinal, codigo_materia
            """
            df_malla = pd.read_sql_query(query_malla, con)

            query_habs = """
            SELECT 
                habilidad_tecnologica,
                COUNT(DISTINCT codigo_materia) AS total_materias,
                GROUP_CONCAT(DISTINCT nombre_materia) AS materias_donde_se_ve,
                MIN(semestre_ordinal) AS primer_semestre_donde_aparece,
                MAX(semestre_ordinal) AS ultimo_semestre_donde_aparece
            FROM fact_habilidades_academicas
            GROUP BY habilidad_tecnologica
            ORDER BY total_materias DESC
            """
            df_habs = pd.read_sql_query(query_habs, con)

            total_creditos = int(df_malla["creditos"].sum())
            total_horas = int(df_malla["horas_totales"].sum())
            total_materias = len(df_malla)

        return {
            "institucion": "Fundación Universitaria Cafam (UniCafam)",
            "facultad": "Escuela de Ingeniería y Ciencias Empresariales",
            "ecosistema_academico_datos": {
                "programa_evaluado": "Tecnología en Análisis y Gestión de Datos (Pregrado Técnico-Tecnológico, 5 semestres, 83 créditos, 32 materias)",
                "programa_articulado_continuidad": "Profesional en Ciencia de Datos (Pregrado Profesional Universitario, articulado por ciclos propedéuticos / homologación de créditos para graduarse como Científico de Datos)",
                "programa_afin": "Ingeniería de Sistemas (Pregrado Profesional Universitario)"
            },
            "total_creditos": total_creditos,
            "total_horas": total_horas,
            "total_materias": total_materias,
            "malla_completa": df_malla.to_dict(orient="records"),
            "habilidades_academicas": df_habs.to_dict(orient="records")
        }

    def calcular_matriz_brechas(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cruza determinísticamente oferta académica vs demanda laboral (contexto_mercado.construir_contexto).
        """
        curriculo = self.obtener_metricas_curriculo()

        df_m = pd.DataFrame(contexto["demanda_habilidades"])
        df_m["categoria"] = df_m["habilidad"].apply(obtener_categoria_skill)
        df_c = pd.DataFrame(curriculo["habilidades_academicas"])

        def normalizar_hab(h: str) -> str:
            if not isinstance(h, str):
                return ""
            h_upper = h.upper().strip()
            if "POWER BI" in h_upper: return "POWER BI"
            if "TABLEAU" in h_upper: return "TABLEAU"
            if "EXCEL" in h_upper: return "EXCEL"
            if "PYTHON" in h_upper: return "PYTHON"
            if "SQL" in h_upper: return "SQL"
            if "GIT" in h_upper: return "GIT"
            if "ETL" in h_upper or "PIPELINE" in h_upper: return "ETL"
            if "NOSQL" in h_upper or "MONGODB" in h_upper: return "NOSQL"
            if "NLP" in h_upper or "LLM" in h_upper: return "NLP"
            if "MACHINE LEARNING" in h_upper: return "MACHINE LEARNING"
            if "DEEP LEARNING" in h_upper: return "DEEP LEARNING"
            if "ESTADISTICA" in h_upper or "ESTADÍSTICA" in h_upper: return "ESTADISTICA"
            if "SPARK" in h_upper: return "SPARK"
            if "HADOOP" in h_upper or "HIVE" in h_upper: return "HADOOP"
            if "BIG DATA" in h_upper: return "BIG DATA"
            if "DOCKER" in h_upper or "KUBERNETES" in h_upper: return "DOCKER"
            if "MLOPS" in h_upper: return "MLOPS"
            if "DATABRICKS" in h_upper: return "DATABRICKS"
            if "AIRFLOW" in h_upper: return "AIRFLOW"
            if "AWS" in h_upper: return "AWS"
            if "AZURE" in h_upper: return "AZURE"
            if "GCP" in h_upper or "GOOGLE CLOUD" in h_upper or "BIGQUERY" in h_upper: return "GCP"
            if "SCIKIT" in h_upper: return "SCIKIT-LEARN"
            if "TENSORFLOW" in h_upper or "KERAS" in h_upper: return "TENSORFLOW"
            if "PYTORCH" in h_upper: return "PYTORCH"
            if h_upper == "R" or "LENGUAJE R" in h_upper or "RSTUDIO" in h_upper: return "R"
            return h_upper

        df_m["hab_norm"] = df_m["habilidad"].apply(normalizar_hab)
        df_c["hab_norm"] = df_c["habilidad_tecnologica"].apply(normalizar_hab)

        # Agrupar currículo por habilidad normalizada para evitar duplicaciones en el merge
        df_c_grouped = df_c.groupby("hab_norm", as_index=False).agg({
            "total_materias": "sum",
            "materias_donde_se_ve": lambda s: ", ".join(sorted(set([m.strip() for m in ", ".join(s).split(",") if m.strip()]))),
            "primer_semestre_donde_aparece": "min",
            "ultimo_semestre_donde_aparece": "max"
        })

        merged = pd.merge(df_m, df_c_grouped, on="hab_norm", how="left")

        # 1. Fortalezas (habilidades presentes en la oferta académica)
        fortalezas = merged[merged["total_materias"].notna()].copy()
        fortalezas = fortalezas.sort_values(by="pct_ofertas", ascending=False)

        # 2. Brechas Críticas (habilidades del mercado ausentes en la oferta actual)
        brechas = merged[merged["total_materias"].isna()].copy()
        brechas = brechas.sort_values(by="pct_ofertas", ascending=False)

        # Cobertura ponderada por demanda: de cada 100 menciones de habilidades en las ofertas del último
        # corte, cuántas corresponden a habilidades que el programa ya enseña (cálculo, no opinión del modelo)
        cobertura = round(float(100.0 * fortalezas["n_ofertas"].sum() / df_m["n_ofertas"].sum()), 1) if len(df_m) else None
        columnas_mercado = ["habilidad", "n_ofertas", "pct_ofertas"]
        return {
            "resumen_ejecutivo": {
                "total_vacantes_ultimo_mes": contexto["n_ofertas_mes"],
                "ultimo_corte": contexto["ultimo_corte"],
                "total_creditos_programa": curriculo["total_creditos"],
                "total_materias_programa": curriculo["total_materias"],
                "total_habilidades_cubiertas": len(fortalezas),
                "total_brechas_detectadas": len(brechas),
                "cobertura_ponderada_por_demanda_pct": cobertura,
            },
            "fortalezas": fortalezas[columnas_mercado + ["total_materias", "materias_donde_se_ve"]].to_dict(orient="records"),
            "brechas_criticas_mercado": brechas[columnas_mercado + ["categoria"]].to_dict(orient="records"),
            "malla_referencia": curriculo["malla_completa"],
            "ecosistema_academico": curriculo.get("ecosistema_academico_datos", {})
        }

def contexto_para_verificar(contexto: Dict[str, Any], analizador: Optional["CurriculumGapAnalyzer"] = None) -> Dict[str, Any]:
    """
    El contexto de mercado más el resumen del cruce currículo-mercado: el modelo recibe ambos (p. ej. la
    cobertura ponderada por demanda), así que ambos son fuentes válidas de cifras. Se recalcula desde el
    contexto archivado, de modo que una re-verificación da el mismo resultado.
    """
    resumen = (analizador or CurriculumGapAnalyzer()).calcular_matriz_brechas(contexto)["resumen_ejecutivo"]
    return {**contexto, "cruce_curricular": resumen}


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from src.ai_curriculum.contexto_mercado import construir_contexto
    from src.database.db_manager import DATABASE_URL, normalizar_url_bd
    resultado = CurriculumGapAnalyzer().calcular_matriz_brechas(
        construir_contexto(create_engine(normalizar_url_bd(DATABASE_URL))))
    print("=== RESUMEN EJECUTIVO ===")
    print(resultado["resumen_ejecutivo"])
    for f in resultado["fortalezas"][:6]:
        print(f"  ✓ {f['habilidad']}: {f['pct_ofertas']}% de ofertas | {f['total_materias']} materias")
    for b in resultado["brechas_criticas_mercado"][:8]:
        print(f"  ✗ {b['habilidad']} [{b['categoria']}]: {b['pct_ofertas']}% de ofertas (n={b['n_ofertas']})")
