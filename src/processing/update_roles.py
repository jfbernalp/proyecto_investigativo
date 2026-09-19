"""
Normalizador y Clasificador de Roles Ocupacionales Reales.
Analiza el título de la vacante (nombre_oferta) y clasifica la vacante en su rol técnico real:
- Científico de Datos (Data Scientist)
- Machine Learning / AI Engineer
- Ingeniero de Datos (Data Engineer)
- Analista de Datos (Data Analyst)
- Analista de BI & Visualización
- Desarrollador de Software / Datos
"""

import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LABOR_DB_PATH = BASE_DIR / "data" / "labor_market.db"

def clasificar_rol_real(titulo: str) -> str:
    """Clasifica el rol técnico basado en palabras clave del título del cargo."""
    if not isinstance(titulo, str):
        return "Científico de Datos (Data Scientist)"
    t = titulo.lower().strip()
    
    # 1. Machine Learning & MLOps / AI Engineer
    if any(k in t for k in ["machine learning", "ml engineer", "ai engineer", "inteligencia artificial", "deep learning", "nlp", "ia"]):
        return "Machine Learning / AI Engineer"
    
    # 2. Data Engineer / Arquitecto / ETL / Big Data
    if any(k in t for k in ["ingeniero de datos", "data engineer", "arquitecto de datos", "data architect", "etl", "big data", "data governance"]):
        return "Ingeniero de Datos (Data Engineer)"
        
    # 3. BI / Business Intelligence / Visualización
    if any(k in t for k in ["bi", "business intelligence", "power bi", "tableau", "inteligencia de negocios", "storytelling"]):
        return "Analista de BI & Visualización"
        
    # 4. Data Analyst / Analista de Datos
    if any(k in t for k in ["analista de datos", "data analyst", "analista de informaci", "analitica", "analítica", "analyst"]):
        return "Analista de Datos (Data Analyst)"
        
    # 5. Data Scientist / Científico de Datos
    if any(k in t for k in ["científico", "cientifico", "data scientist", "science", "investigador", "scientist"]):
        return "Científico de Datos (Data Scientist)"
        
    # 6. Desarrollador / Developer
    if any(k in t for k in ["desarrollador", "developer", "software", "full stack", "backend"]):
        return "Desarrollador de Software / Datos"
        
    return "Científico de Datos (Data Scientist)"

def actualizar_roles_en_bd():
    """Actualiza la columna rol_buscado en SQLite con la clasificación real."""
    con = sqlite3.connect(LABOR_DB_PATH)
    cur = con.cursor()
    
    # 1. Obtener todas las ofertas
    df = pd.read_sql_query("SELECT id_vacante_hash, nombre_oferta FROM dim_ofertas", con)
    df["rol_real"] = df["nombre_oferta"].apply(clasificar_rol_real)
    
    # 2. Actualizar dim_ofertas
    for _, row in df.iterrows():
        cur.execute(
            "UPDATE dim_ofertas SET rol_buscado = ? WHERE id_vacante_hash = ?",
            (row["rol_real"], row["id_vacante_hash"])
        )
        
    # 3. Actualizar ofertas_modeladas_bi si existe
    for _, row in df.iterrows():
        cur.execute(
            "UPDATE ofertas_modeladas_bi SET Rol_Buscado = ? WHERE id_vacante_hash = ?",
            (row["rol_real"], row["id_vacante_hash"])
        )
        
    con.commit()
    print("[SUCCESS] Actualización de roles completada en SQLite:")
    res = cur.execute("SELECT rol_buscado, COUNT(*) FROM dim_ofertas GROUP BY rol_buscado ORDER BY COUNT(*) DESC").fetchall()
    for rol, count in res:
        print(f"  - {rol}: {count} vacantes ({count*100/len(df):.1f}%)")
    con.close()

if __name__ == "__main__":
    actualizar_roles_en_bd()
