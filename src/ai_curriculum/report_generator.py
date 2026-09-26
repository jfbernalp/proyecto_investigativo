"""
Generador de Informes Ejecutivos y Persistencia en PostgreSQL para las Recomendaciones de IA.
Convierte el JSON estructurado de Gemini en un informe estratégico Markdown/HTML y en sentencias SQL.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

INPUT_JSON_PATH = BASE_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"
REPORT_MD_PATH = BASE_DIR / "docs" / "informe_recomendaciones_unicafam_ia.md"
SQL_OUTPUT_PATH = BASE_DIR / "data" / "curriculo_unicafam" / "cargar_propuestas_hetzner.sql"

class CurriculumReportGenerator:
    """Generador de informes y DDL/DML para propuestas curriculares generadas por IA."""

    def __init__(self, json_path: Path = INPUT_JSON_PATH):
        self.json_path = json_path
        if not self.json_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de recomendaciones: {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def generar_informe_markdown(self) -> Path:
        """Genera un informe ejecutivo de alto nivel en Markdown."""
        diag = self.data["diagnostico"]
        propuestas = self.data["propuestas"]

        md_lines = [
            "# 🎓 Informe Estratégico de Inteligencia Curricular y Oportunidades Académicas",
            "**Institución:** Fundación Universitaria Cafam (UniCafam)  ",
            "**Programa Evaluado:** Tecnología en Análisis y Gestión de Datos (83 Créditos - 5 Semestres)  ",
            "**Fuente de Datos:** Observatorio del Mercado Laboral (317 ofertas analizadas en Colombia y Remoto)  ",
            "**Marco Regulatorio:** Decreto 1330 de 2019 (Ministerio de Educación Nacional de Colombia)  ",
            "",
            "---",
            "",
            "## 1. 📊 Diagnóstico Ejecutivo del Programa Actual",
            f"### **Índice de Alineación y Competitividad con el Mercado:** `{diag['puntuacion_competitividad_mercado']} / 100`",
            "",
            diag["resumen_ejecutivo"],
            "",
            "### 🟢 Fortalezas Clave del Currículo",
        ]
        for f in diag["fortalezas_principales"]:
            md_lines.append(f"- ✅ {f}")

        md_lines.extend([
            "",
            "### 🔴 Brechas Críticas Tecnológicas (GAPs con 0 materias formales)",
        ])
        for b in diag["brechas_criticas_mercado"]:
            md_lines.append(f"- ⚠️ {b}")

        md_lines.extend([
            "",
            "### ⚠️ Riesgos Competitivos y Salariales para los Graduados",
        ])
        for r in diag["riesgos_competitivos_egresado"]:
            md_lines.append(f"- 🚨 {r}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 2. 🚀 Portafolio de Nuevas Propuestas Formativas Diseñadas por IA",
            "A continuación se detallan las 4 ofertas formativas recomendadas para cerrar las brechas salariales y posicionar a UniCafam como referente:",
            ""
        ])

        for p in propuestas:
            md_lines.extend([
                f"### 📌 [{p['tipo_propuesta'].upper()}] {p['nombre_programa']}",
                f"- **Título Otorgado:** {p['titulo_otorgado']}",
                f"- **Nivel Académico:** {p['nivel_academico']} | **Modalidad:** {p['modalidad_sugerida']}",
                f"- **Duración:** {p['duracion_estimada']} | **Créditos Totales:** {p['creditos_totales']} ({p['horas_totales']} Horas)",
                f"- **Impacto Salarial Proyectado:** {p['impacto_salarial_proyectado']}",
                f"- **Roles Objetivo:** {', '.join(p['roles_ocupacionales_objetivo'])}",
                f"- **Perfil de Ingreso:** {p['perfil_ingreso']}",
                f"- **Perfil de Egreso:** {p['perfil_egreso']}",
                "",
                "#### 📚 Plan de Estudios y Malla Curricular:",
                "| Módulo / Asignatura | Créditos | Horas TFD | Horas TTI | Stack Tecnológico | Justificación de Mercado |",
                "|---|:---:|:---:|:---:|---|---|"
            ])

            for m in p["plan_estudios"]:
                stack_str = ", ".join(m["stack_tecnologico"])
                md_lines.append(
                    f"| **{m['nombre_modulo']}** | {m['creditos']} | {m['horas_tfd']} | {m['horas_tti']} | `{stack_str}` | {m['justificacion_demanda_laboral']} |"
                )

            md_lines.extend([
                "",
                "**Resultados de Aprendizaje Esperados (RAE):**"
            ])
            for m in p["plan_estudios"]:
                md_lines.append(f"- **{m['nombre_modulo']}:**")
                for rae in m["resultados_aprendizaje_esperados_rae"]:
                    md_lines.append(f"  * 🎯 *{rae}*")
            md_lines.append("\n---\n")

        REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"[REPORT] Informe Markdown generado en: {REPORT_MD_PATH}")
        return REPORT_MD_PATH

    def generar_script_sql(self) -> Path:
        """Genera sentencias SQL completas compatibles con PostgreSQL (Hetzner) y Apache Superset."""
        from src.ai_curriculum.mig_excel_exporter import normalizar_propuesta_a_mig
        diag = self.data["diagnostico"]
        propuestas = self.data["propuestas"]

        sql = [
            "-- ==================================================================",
            "-- PERSISTENCIA DE PROPUESTAS CURRICULARES MIG EN POSTGRESQL (HETZNER)",
            "-- Compatible con Apache Superset (jfbernalp.dev)",
            "-- ==================================================================",
            "",
            "DROP VIEW IF EXISTS view_superset_kpis_curriculares_mig CASCADE;",
            "DROP VIEW IF EXISTS view_superset_malla_curricular_mig CASCADE;",
            "DROP VIEW IF EXISTS view_superset_oferta_academica_mig CASCADE;",
            "DROP TABLE IF EXISTS dim_docentes_propuestas_mig CASCADE;",
            "DROP TABLE IF EXISTS fact_modulos_propuestas_mig CASCADE;",
            "DROP TABLE IF EXISTS dim_propuestas_curriculares_mig CASCADE;",
            "DROP TABLE IF EXISTS fact_diagnostico_ia CASCADE;",
            "",
            """CREATE TABLE fact_diagnostico_ia (
    id SERIAL PRIMARY KEY,
    programa_evaluado VARCHAR(200),
    puntuacion_competitividad NUMERIC(5,2),
    resumen_ejecutivo TEXT,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
            "",
            """CREATE TABLE dim_propuestas_curriculares_mig (
    id_propuesta VARCHAR(64) PRIMARY KEY,
    tipo_propuesta VARCHAR(100),
    nombre_programa VARCHAR(250),
    titulo_otorgado VARCHAR(250),
    nivel_academico VARCHAR(100),
    duracion_estimada VARCHAR(100),
    creditos_totales INTEGER,
    horas_totales INTEGER,
    modalidad VARCHAR(100),
    horario TEXT,
    fecha_inicio_estimada VARCHAR(100),
    fecha_terminacion_estimada VARCHAR(100),
    proximas_ediciones VARCHAR(150),
    inversion_publico_externo TEXT,
    inversion_comunidad_unicafam TEXT,
    inversion_egresados TEXT,
    inversion_grupos TEXT,
    justificacion_detallada TEXT,
    objetivos_programa TEXT,
    dirigido_a TEXT,
    metodologia_detallada TEXT,
    valores_agregados TEXT,
    perfil_ingreso TEXT,
    perfil_egreso TEXT,
    roles_objetivo TEXT,
    impacto_salarial_proyectado TEXT,
    url_descarga_excel TEXT
);""",
            "",
            """CREATE TABLE fact_modulos_propuestas_mig (
    id_modulo SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares_mig(id_propuesta) ON DELETE CASCADE,
    numero_modulo INTEGER,
    nombre_modulo VARCHAR(250),
    semestre_sugerido VARCHAR(50),
    creditos INTEGER,
    horas_tfd INTEGER,
    horas_tti INTEGER,
    horas_totales_modulo INTEGER,
    contenido_detallado TEXT,
    cronograma_fechas TEXT,
    stack_tecnologico TEXT,
    raes TEXT,
    justificacion_mercado TEXT
);""",
            "",
            """CREATE TABLE dim_docentes_propuestas_mig (
    id_docente SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares_mig(id_propuesta) ON DELETE CASCADE,
    nombre_o_rol VARCHAR(250),
    modulo_asignado VARCHAR(250),
    perfil_experto TEXT
);""",
            ""
        ]

        # Insert diagnostico
        resumen_safe = diag["resumen_ejecutivo"].replace("'", "''")
        sql.append(f"INSERT INTO fact_diagnostico_ia (programa_evaluado, puntuacion_competitividad, resumen_ejecutivo) VALUES ('Tecnología en Análisis y Gestión de Datos', {diag['puntuacion_competitividad_mercado']}, '{resumen_safe}');\n")

        # Insert propuestas
        for raw_p in propuestas:
            p = normalizar_propuesta_a_mig(raw_p)
            id_p = p.id_propuesta
            tipo = p.tipo_propuesta.replace("'", "''")
            nombre = p.nombre_programa.replace("'", "''")
            titulo = p.titulo_otorgado.replace("'", "''")
            nivel = p.nivel_academico.replace("'", "''")
            dur = p.duracion_estimada.replace("'", "''")
            mod = p.modalidad_sugerida.replace("'", "''")
            hor = (p.horario or '').replace("'", "''")
            f_ini = (p.fecha_inicio_estimada or '').replace("'", "''")
            f_fin = (p.fecha_terminacion_estimada or '').replace("'", "''")
            prox = (p.proximas_ediciones or '').replace("'", "''")
            inv_ext = (p.inversion.publico_externo if p.inversion else '').replace("'", "''")
            inv_com = (p.inversion.comunidad_unicafam if p.inversion else '').replace("'", "''")
            inv_egr = (p.inversion.egresados if p.inversion else '').replace("'", "''")
            inv_grp = (p.inversion.grupos_empresas if p.inversion else '').replace("'", "''")
            just = (p.justificacion_detallada or '').replace("'", "''")
            objs = "\n".join(p.objetivos_programa or []).replace("'", "''")
            dir_a = (p.dirigido_a or '').replace("'", "''")
            metod = (p.metodologia_detallada or '').replace("'", "''")
            vals = "\n".join(p.valores_agregados or []).replace("'", "''")
            p_in = p.perfil_ingreso.replace("'", "''")
            p_out = p.perfil_egreso.replace("'", "''")
            roles = ", ".join(p.roles_ocupacionales_objetivo).replace("'", "''")
            sal = p.impacto_salarial_proyectado.replace("'", "''")
            url_desc = f"https://jfbernalp.dev/downloads/mig/{id_p}_MIG.xlsx"

            sql.append(
                f"INSERT INTO dim_propuestas_curriculares_mig VALUES ('{id_p}', '{tipo}', '{nombre}', '{titulo}', '{nivel}', '{dur}', {p.creditos_totales}, {p.horas_totales}, '{mod}', '{hor}', '{f_ini}', '{f_fin}', '{prox}', '{inv_ext}', '{inv_com}', '{inv_egr}', '{inv_grp}', '{just}', '{objs}', '{dir_a}', '{metod}', '{vals}', '{p_in}', '{p_out}', '{roles}', '{sal}', '{url_desc}');"
            )

            for m in p.plan_estudios:
                m_nom = m.nombre_modulo.replace("'", "''")
                m_num = m.numero_modulo or 1
                sem = str(m.semestre_sugerido or 'N/A').replace("'", "''")
                h_tot = m.horas_totales_modulo or (m.creditos * 48)
                cont_det = (m.contenido_detallado or '').replace("'", "''")
                cron = (m.cronograma_fechas or '').replace("'", "''")
                stack = ", ".join(m.stack_tecnologico).replace("'", "''")
                raes = " | ".join(m.resultados_aprendizaje_esperados_rae).replace("'", "''")
                just_m = m.justificacion_demanda_laboral.replace("'", "''")

                sql.append(
                    f"INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('{id_p}', {m_num}, '{m_nom}', '{sem}', {m.creditos}, {m.horas_tfd}, {m.horas_tti}, {h_tot}, '{cont_det}', '{cron}', '{stack}', '{raes}', '{just_m}');"
                )

            for doc in (p.docentes_perfiles or []):
                d_nom = doc.nombre_o_rol.replace("'", "''")
                d_mod = doc.modulo_asignado.replace("'", "''")
                d_exp = doc.perfil_experto.replace("'", "''")
                sql.append(
                    f"INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('{id_p}', '{d_nom}', '{d_mod}', '{d_exp}');"
                )

        # Vistas Superset
        sql.extend([
            "",
            "-- Vistas para Apache Superset",
            """CREATE OR REPLACE VIEW view_superset_oferta_academica_mig AS
SELECT 
    p.id_propuesta,
    p.tipo_propuesta,
    p.nombre_programa,
    p.titulo_otorgado,
    p.nivel_academico,
    p.modalidad,
    p.duracion_estimada,
    p.creditos_totales,
    p.horas_totales,
    p.horario,
    p.fecha_inicio_estimada,
    p.proximas_ediciones,
    p.inversion_publico_externo,
    p.inversion_comunidad_unicafam,
    p.inversion_egresados,
    p.inversion_grupos,
    p.impacto_salarial_proyectado,
    p.roles_objetivo,
    p.justificacion_detallada,
    p.objetivos_programa,
    p.metodologia_detallada,
    p.valores_agregados,
    COUNT(m.id_modulo) AS total_modulos,
    p.url_descarga_excel,
    ('<a href="' || COALESCE(p.url_descarga_excel, '#') || '" target="_blank" style="background-color: #1F4E79; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block;">📥 Descargar MIG (.xlsx)</a>') AS boton_descarga_html
FROM dim_propuestas_curriculares_mig p
LEFT JOIN fact_modulos_propuestas_mig m ON p.id_propuesta = m.id_propuesta
GROUP BY 
    p.id_propuesta, p.tipo_propuesta, p.nombre_programa, p.titulo_otorgado, p.nivel_academico,
    p.modalidad, p.duracion_estimada, p.creditos_totales, p.horas_totales, p.horario,
    p.fecha_inicio_estimada, p.proximas_ediciones, p.inversion_publico_externo,
    p.inversion_comunidad_unicafam, p.inversion_egresados, p.inversion_grupos,
    p.impacto_salarial_proyectado, p.roles_objetivo, p.justificacion_detallada,
    p.objetivos_programa, p.metodologia_detallada, p.valores_agregados, p.url_descarga_excel;""",
            "",
            """CREATE OR REPLACE VIEW view_superset_malla_curricular_mig AS
SELECT 
    m.id_modulo,
    p.id_propuesta,
    p.nombre_programa,
    p.tipo_propuesta,
    p.nivel_academico,
    m.numero_modulo,
    m.nombre_modulo,
    m.creditos,
    m.horas_tfd,
    m.horas_tti,
    m.horas_totales_modulo,
    m.cronograma_fechas,
    m.stack_tecnologico,
    m.raes,
    m.justificacion_mercado,
    d.nombre_o_rol AS docente_asignado,
    d.perfil_experto AS perfil_docente_experto
FROM fact_modulos_propuestas_mig m
JOIN dim_propuestas_curriculares_mig p ON m.id_propuesta = p.id_propuesta
LEFT JOIN dim_docentes_propuestas_mig d ON m.id_propuesta = d.id_propuesta AND m.nombre_modulo = d.modulo_asignado;""",
            "",
            """CREATE OR REPLACE VIEW view_superset_kpis_curriculares_mig AS
SELECT 
    d.id,
    d.programa_evaluado,
    d.puntuacion_competitividad AS indice_competitividad_mercado,
    (SELECT COUNT(*) FROM dim_propuestas_curriculares_mig) AS total_propuestas_generadas,
    (SELECT SUM(creditos_totales) FROM dim_propuestas_curriculares_mig) AS total_creditos_ofertados,
    (SELECT SUM(horas_totales) FROM dim_propuestas_curriculares_mig) AS total_horas_formacion,
    (SELECT COUNT(*) FROM fact_modulos_propuestas_mig) AS total_modulos_disenados,
    d.resumen_ejecutivo,
    d.fecha_generacion
FROM fact_diagnostico_ia d
ORDER BY d.fecha_generacion DESC
LIMIT 1;"""
        ])

        SQL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SQL_OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(sql))

        print(f"[SQL] Script SQL generado en: {SQL_OUTPUT_PATH}")
        return SQL_OUTPUT_PATH

    def sincronizar_propuestas_a_base_de_datos(self) -> None:
        """Sincroniza directamente las propuestas estructuradas en la Base de Datos relacional activa."""
        from src.database.db_manager import DatabaseManager
        from src.ai_curriculum.mig_excel_exporter import normalizar_propuesta_a_mig
        from sqlalchemy import text
        import pandas as pd

        db = DatabaseManager()
        diag = self.data["diagnostico"]
        propuestas = self.data["propuestas"]

        with db.engine.begin() as conn:
            # Limpiar tablas anteriores de propuestas para inserción limpia
            conn.execute(text("DELETE FROM dim_docentes_propuestas_mig;"))
            conn.execute(text("DELETE FROM fact_modulos_propuestas_mig;"))
            conn.execute(text("DELETE FROM dim_propuestas_curriculares_mig;"))

        # 1. Diagnostico
        df_diag = pd.DataFrame([{
            "programa_evaluado": "Tecnología en Análisis y Gestión de Datos",
            "puntuacion_competitividad": diag["puntuacion_competitividad_mercado"],
            "resumen_ejecutivo": diag["resumen_ejecutivo"]
        }])
        db.guardar_dataframe(df_diag, table_name="fact_diagnostico_ia", if_exists="append")

        # 2. Propuestas, Módulos y Docentes
        prop_rows = []
        mod_rows = []
        doc_rows = []

        for raw_p in propuestas:
            p = normalizar_propuesta_a_mig(raw_p)
            prop_rows.append({
                "id_propuesta": p.id_propuesta,
                "tipo_propuesta": p.tipo_propuesta,
                "nombre_programa": p.nombre_programa,
                "titulo_otorgado": p.titulo_otorgado,
                "nivel_academico": p.nivel_academico,
                "duracion_estimada": p.duracion_estimada,
                "creditos_totales": p.creditos_totales,
                "horas_totales": p.horas_totales,
                "modalidad": p.modalidad_sugerida,
                "horario": p.horario,
                "fecha_inicio_estimada": p.fecha_inicio_estimada,
                "fecha_terminacion_estimada": p.fecha_terminacion_estimada,
                "proximas_ediciones": p.proximas_ediciones,
                "inversion_publico_externo": p.inversion.publico_externo if p.inversion else "",
                "inversion_comunidad_unicafam": p.inversion.comunidad_unicafam if p.inversion else "",
                "inversion_egresados": p.inversion.egresados if p.inversion else "",
                "inversion_grupos": p.inversion.grupos_empresas if p.inversion else "",
                "justificacion_detallada": p.justificacion_detallada,
                "objetivos_programa": "\n".join(p.objetivos_programa or []),
                "dirigido_a": p.dirigido_a,
                "metodologia_detallada": p.metodologia_detallada,
                "valores_agregados": "\n".join(p.valores_agregados or []),
                "perfil_ingreso": p.perfil_ingreso,
                "perfil_egreso": p.perfil_egreso,
                "roles_objetivo": ", ".join(p.roles_ocupacionales_objetivo),
                "impacto_salarial_proyectado": p.impacto_salarial_proyectado,
                "url_descarga_excel": f"https://jfbernalp.dev/downloads/mig/{p.id_propuesta}_MIG.xlsx"
            })

            for m in p.plan_estudios:
                mod_rows.append({
                    "id_propuesta": p.id_propuesta,
                    "numero_modulo": m.numero_modulo or 1,
                    "nombre_modulo": m.nombre_modulo,
                    "semestre_sugerido": str(m.semestre_sugerido or 'N/A'),
                    "creditos": m.creditos,
                    "horas_tfd": m.horas_tfd,
                    "horas_tti": m.horas_tti,
                    "horas_totales_modulo": m.horas_totales_modulo or (m.creditos * 48),
                    "contenido_detallado": m.contenido_detallado,
                    "cronograma_fechas": m.cronograma_fechas,
                    "stack_tecnologico": ", ".join(m.stack_tecnologico),
                    "raes": " | ".join(m.resultados_aprendizaje_esperados_rae),
                    "justificacion_mercado": m.justificacion_demanda_laboral
                })

            for doc in (p.docentes_perfiles or []):
                doc_rows.append({
                    "id_propuesta": p.id_propuesta,
                    "nombre_o_rol": doc.nombre_o_rol,
                    "modulo_asignado": doc.modulo_asignado,
                    "perfil_experto": doc.perfil_experto
                })

        db.guardar_dataframe(pd.DataFrame(prop_rows), table_name="dim_propuestas_curriculares_mig", if_exists="append")
        db.guardar_dataframe(pd.DataFrame(mod_rows), table_name="fact_modulos_propuestas_mig", if_exists="append")
        if doc_rows:
            db.guardar_dataframe(pd.DataFrame(doc_rows), table_name="dim_docentes_propuestas_mig", if_exists="append")

        print(f"[DATABASE SYNC] Propuestas curriculares sincronizadas en la Base de Datos para Apache Superset.")

    def generar_excel_mig(self) -> Dict[str, Any]:
        """Exporta las propuestas a formato Excel MATRIZ INTEGRADA DE GESTIÓN (MIG)."""
        from src.ai_curriculum.mig_excel_exporter import MIGExcelExporter
        exporter = MIGExcelExporter()
        resultado = exporter.exportar_portafolio_completo(json_path=self.json_path)
        return resultado

if __name__ == "__main__":
    generator = CurriculumReportGenerator()
    generator.generar_informe_markdown()
    generator.generar_script_sql()
    generator.generar_excel_mig()
    generator.sincronizar_propuestas_a_base_de_datos()

