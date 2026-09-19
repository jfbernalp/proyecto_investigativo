"""
Sincronizador de Malla Curricular y Generador de Tablas para PostgreSQL en Hetzner.
Genera el esquema relacional, carga los datos y crea la vista analítica de Brechas Curriculares con soporte multi-programa.
"""

import os
import sqlite3
import pandas as pd
from curriculum_parser import CurriculumParser

SQL_OUTPUT_FILE = "data/curriculo_unicafam/cargar_malla_hetzner.sql"
SQLITE_LOCAL_DB = "data/curriculo_unicafam/curriculo_unicafam.db"

def generar_script_sql(df_malla: pd.DataFrame, df_habilidades: pd.DataFrame, df_saberes: pd.DataFrame):
    """Genera un archivo SQL DDL + DML completo para PostgreSQL en Hetzner."""
    
    sql_lines = [
        "-- ==================================================================",
        "-- PERSISTENCIA PRIVADA DE MALLA CURRICULAR UNICAFAM EN HETZNER",
        "-- ==================================================================",
        "",
        "-- 1. Tabla Dimensión Malla Curricular",
        "DROP VIEW IF EXISTS vista_cobertura_curricular CASCADE;",
        "DROP TABLE IF EXISTS fact_habilidades_academicas CASCADE;",
        "DROP TABLE IF EXISTS fact_saberes_academicos CASCADE;",
        "DROP TABLE IF EXISTS dim_malla_curricular CASCADE;",
        "",
        """CREATE TABLE dim_malla_curricular (
    codigo_materia VARCHAR(64) PRIMARY KEY,
    programa_academico VARCHAR(200) NOT NULL,
    nombre_materia TEXT NOT NULL,
    semestre_ordinal INTEGER NOT NULL,
    semestre_nombre VARCHAR(100) NOT NULL,
    creditos INTEGER NOT NULL,
    horas_tfd INTEGER NOT NULL,
    horas_tti INTEGER NOT NULL,
    horas_totales INTEGER NOT NULL,
    modalidad VARCHAR(50),
    area_formacion VARCHAR(100),
    competencia_general TEXT,
    justificacion TEXT,
    archivo_origen VARCHAR(255)
);""",
        "",
        "-- 2. Tabla de Habilidades y Competencias Tecnológicas Enseñadas",
        """CREATE TABLE fact_habilidades_academicas (
    id_registro SERIAL PRIMARY KEY,
    programa_academico VARCHAR(200) NOT NULL,
    codigo_materia VARCHAR(64) REFERENCES dim_malla_curricular(codigo_materia),
    nombre_materia TEXT,
    semestre_ordinal INTEGER,
    semestre_nombre VARCHAR(100),
    creditos INTEGER,
    habilidad_tecnologica VARCHAR(150),
    termino_detectado VARCHAR(150),
    area_formacion VARCHAR(100)
);""",
        "",
        "-- 3. Tabla de Saberes Específicos Detallados",
        """CREATE TABLE fact_saberes_academicos (
    id_saber SERIAL PRIMARY KEY,
    programa_academico VARCHAR(200) NOT NULL,
    codigo_materia VARCHAR(64) REFERENCES dim_malla_curricular(codigo_materia),
    orden_tema INTEGER,
    saber_especifico TEXT
);""",
        ""
    ]
    
    # Inserciones en dim_malla_curricular
    sql_lines.append("-- INSERCIONES: dim_malla_curricular")
    for _, r in df_malla.iterrows():
        comp = str(r['competencia_general']).replace("'", "''")
        just = str(r['justificacion']).replace("'", "''")
        nom = str(r['nombre_materia']).replace("'", "''")
        prog = str(r['programa_academico']).replace("'", "''")
        sql_lines.append(
            f"INSERT INTO dim_malla_curricular VALUES ('{r['codigo_materia']}', '{prog}', '{nom}', {r['semestre_ordinal']}, '{r['semestre_nombre']}', {r['creditos']}, {r['horas_tfd']}, {r['horas_tti']}, {r['horas_totales']}, '{r['modalidad']}', '{r['area_formacion']}', '{comp}', '{just}', '{r['archivo_origen']}');"
        )
    sql_lines.append("")
    
    # Inserciones en fact_habilidades_academicas
    sql_lines.append("-- INSERCIONES: fact_habilidades_academicas")
    for _, r in df_habilidades.iterrows():
        nom = str(r['nombre_materia']).replace("'", "''")
        hab = str(r['habilidad_tecnologica']).replace("'", "''")
        term = str(r['termino_detectado']).replace("'", "''")
        prog = str(r['programa_academico']).replace("'", "''")
        sql_lines.append(
            f"INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('{prog}', '{r['codigo_materia']}', '{nom}', {r['semestre_ordinal']}, '{r['semestre_nombre']}', {r['creditos']}, '{hab}', '{term}', '{r['area_formacion']}');"
        )
    sql_lines.append("")
    
    # Inserciones en fact_saberes_academicos
    sql_lines.append("-- INSERCIONES: fact_saberes_academicos")
    for _, r in df_saberes.iterrows():
        saber = str(r['saber_especifico']).replace("'", "''")
        prog = str(r['programa_academico']).replace("'", "''")
        sql_lines.append(
            f"INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('{prog}', '{r['codigo_materia']}', {r['orden_tema']}, '{saber}');"
        )
    sql_lines.append("")

    # Vista de Cobertura Curricular
    sql_lines.extend([
        "-- ==================================================================",
        "-- 4. VISTA DE ANÁLISIS DE COBERTURA CURRICULAR POR PROGRAMA",
        "-- ==================================================================",
        """CREATE OR REPLACE VIEW vista_cobertura_curricular AS
SELECT 
    m.programa_academico,
    m.habilidad_tecnologica,
    COUNT(DISTINCT m.codigo_materia) as materias_que_la_ensenian,
    MIN(m.semestre_ordinal) as primer_semestre_introduccion,
    STRING_AGG(DISTINCT m.nombre_materia, ', ') as asignaturas_donde_se_imparte,
    SUM(m.creditos) as creditos_acumulados_asociados
FROM fact_habilidades_academicas m
GROUP BY m.programa_academico, m.habilidad_tecnologica;
"""
    ])
    
    with open(SQL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))
        
    print(f"[OK] Archivo SQL generado exitosamente en: {SQL_OUTPUT_FILE}")

def guardar_base_local(df_malla: pd.DataFrame, df_habilidades: pd.DataFrame, df_saberes: pd.DataFrame):
    """Guarda copia local en SQLite para inspección rápida."""
    conn = sqlite3.connect(SQLITE_LOCAL_DB)
    df_malla.to_sql("dim_malla_curricular", conn, if_exists="replace", index=False)
    df_habilidades.to_sql("fact_habilidades_academicas", conn, if_exists="replace", index=False)
    df_saberes.to_sql("fact_saberes_academicos", conn, if_exists="replace", index=False)
    conn.close()
    print(f"[OK] Base de datos SQLite local generada en: {SQLITE_LOCAL_DB}")

if __name__ == "__main__":
    parser = CurriculumParser()
    df_m, df_h, df_s = parser.procesar_todo()
    generar_script_sql(df_m, df_h, df_s)
    guardar_base_local(df_m, df_h, df_s)
