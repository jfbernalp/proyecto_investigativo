"""
Analizador Cuantitativo de Brechas (GAP Analysis) entre el Mercado Laboral y el Currículo de UniCafam.
Cruza la demanda real de habilidades con la oferta académica formal para alimentar el motor de IA.
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.processing.taxonomies import CLASIFICACION_CATEGORIAS

LABOR_DB_PATH = BASE_DIR / "data" / "labor_market.db"
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

    def __init__(self, labor_db: Optional[Path] = None, curriculum_db: Optional[Path] = None):
        self.labor_db = labor_db or LABOR_DB_PATH
        self.curriculum_db = curriculum_db or CURRICULUM_DB_PATH

    def _get_labor_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.labor_db)

    def _get_curriculum_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.curriculum_db)

    def obtener_metricas_mercado(self) -> Dict[str, Any]:
        """Extrae el panorama general de la demanda de habilidades y salarios de forma atómica."""
        with self._get_labor_connection() as con:
            total_vacantes = con.execute("SELECT COUNT(DISTINCT id_vacante_hash) FROM dim_ofertas").fetchone()[0] or 1

            # 1. Tabla de valor económico
            query_econ = """
            SELECT 
                Habilidad AS habilidad,
                Ofertas_Con_Salario AS ofertas_con_salario,
                Salario_Promedio_COP AS salario_promedio_cop,
                Salario_Mediano_COP AS salario_mediano_cop,
                Prima_Salarial_COP AS prima_salarial_cop,
                "Prima_Salarial_%" AS prima_salarial_pct
            FROM valor_economico_habilidades
            """
            df_econ = pd.read_sql_query(query_econ, con)

            # 2. Conteo atómico de menciones por habilidad sobre las vacantes únicas
            df_facts = pd.read_sql_query("SELECT id_vacante_hash, habilidad FROM fact_habilidades_historico", con)
            
            stats_list = []
            for _, row_econ in df_econ.iterrows():
                s = row_econ["habilidad"]
                matching_vacs = set()
                for _, row_f in df_facts.iterrows():
                    parts = [p.strip() for p in str(row_f["habilidad"]).split(",")]
                    if s in parts:
                        matching_vacs.add(row_f["id_vacante_hash"])
                freq = len(matching_vacs)
                pct = round(freq * 100.0 / total_vacantes, 1)
                stats_list.append({
                    "habilidad": s,
                    "frecuencia_menciones": freq,
                    "porcentaje_penetracion": pct
                })
            
            df_counts = pd.DataFrame(stats_list)
            df_skills = pd.merge(df_counts, df_econ, on="habilidad", how="left")
            df_skills["categoria"] = df_skills["habilidad"].apply(obtener_categoria_skill)
            df_skills["salario_mediano_cop"] = df_skills["salario_mediano_cop"].fillna(4250000.0)
            df_skills = df_skills.sort_values(by="frecuencia_menciones", ascending=False)

            # 3. Roles demandados
            query_roles = f"""
            SELECT rol_buscado, COUNT(*) AS total, ROUND(COUNT(*) * 100.0 / {total_vacantes}, 1) AS pct
            FROM dim_ofertas
            GROUP BY rol_buscado
            ORDER BY total DESC
            """
            df_roles = pd.read_sql_query(query_roles, con)

            # 4. Salarios por tipo de mercado
            query_salarios = """
            SELECT 
                d.tipo_mercado,
                COUNT(*) AS total_con_salario,
                ROUND(AVG(f.salario_cop_mensual), 0) AS salario_promedio_cop,
                ROUND(MIN(f.salario_cop_mensual), 0) AS salario_min_cop,
                ROUND(MAX(f.salario_cop_mensual), 0) AS salario_max_cop
            FROM fact_extracciones_historico f
            JOIN dim_ofertas d ON f.id_vacante_hash = d.id_vacante_hash
            WHERE f.salario_cop_mensual > 0
            GROUP BY d.tipo_mercado
            """
            df_salarios = pd.read_sql_query(query_salarios, con)

        return {
            "total_vacantes_analizadas": total_vacantes,
            "habilidades_mercado": df_skills.to_dict(orient="records"),
            "roles_distribucion": df_roles.to_dict(orient="records"),
            "salarios_mercado": df_salarios.to_dict(orient="records")
        }

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

    def calcular_matriz_brechas(self) -> Dict[str, Any]:
        """
        Cruza determinísticamente oferta académica vs demanda laboral.
        """
        mercado = self.obtener_metricas_mercado()
        curriculo = self.obtener_metricas_curriculo()

        df_m = pd.DataFrame(mercado["habilidades_mercado"])
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
        fortalezas = fortalezas.sort_values(by="frecuencia_menciones", ascending=False)

        # 2. Brechas Críticas (habilidades del mercado ausentes en la oferta actual)
        brechas = merged[merged["total_materias"].isna()].copy()
        brechas = brechas.sort_values(by="frecuencia_menciones", ascending=False)

        # 3. Brechas de Alto Valor Salarial (> 8M COP)
        alto_salario = brechas[brechas["salario_mediano_cop"] >= 8000000].sort_values(by="salario_mediano_cop", ascending=False)

        return {
            "resumen_ejecutivo": {
                "total_vacantes": mercado["total_vacantes_analizadas"],
                "total_creditos_programa": curriculo["total_creditos"],
                "total_materias_programa": curriculo["total_materias"],
                "total_habilidades_cubiertas": len(fortalezas),
                "total_brechas_detectadas": len(brechas),
                "cobertura_porcentual_mercado": round(len(fortalezas) * 100.0 / len(df_m), 1) if len(df_m) > 0 else 0
            },
            "fortalezas": fortalezas[["habilidad", "frecuencia_menciones", "porcentaje_penetracion", "total_materias", "materias_donde_se_ve", "salario_mediano_cop"]].fillna("N/A").to_dict(orient="records"),
            "brechas_criticas_mercado": brechas[["habilidad", "categoria", "frecuencia_menciones", "porcentaje_penetracion", "salario_mediano_cop"]].fillna("N/A").to_dict(orient="records"),
            "brechas_alto_valor_economico": alto_salario[["habilidad", "categoria", "salario_mediano_cop", "porcentaje_penetracion"]].fillna("N/A").to_dict(orient="records"),
            "roles_mas_demandados": mercado["roles_distribucion"],
            "salarios_por_mercado": mercado["salarios_mercado"],
            "malla_referencia": curriculo["malla_completa"],
            "ecosistema_academico": curriculo.get("ecosistema_academico_datos", {})
        }

if __name__ == "__main__":
    analyzer = CurriculumGapAnalyzer()
    resultado = analyzer.calcular_matriz_brechas()
    print("=== RESUMEN EJECUTIVO ===")
    print(resultado["resumen_ejecutivo"])
    print(f"\nTotal Fortalezas Identificadas: {len(resultado['fortalezas'])}")
    for f in resultado["fortalezas"][:6]:
        print(f"  ✓ {f['habilidad']}: {f['porcentaje_penetracion']}% mercado | {f['total_materias']} materias ({f['materias_donde_se_ve']})")
    print(f"\nTotal Brechas Críticas (GAPs): {len(resultado['brechas_criticas_mercado'])}")
    for b in resultado["brechas_criticas_mercado"][:8]:
        print(f"  ✗ {b['habilidad']} [{b['categoria']}]: {b['porcentaje_penetracion']}% mercado | Salario Mediano: ${float(b['salario_mediano_cop']):,.0f} COP")
