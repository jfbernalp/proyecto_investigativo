"""
Generador de Informes Ejecutivos y Persistencia en PostgreSQL para las Recomendaciones de IA.
Convierte el JSON estructurado de Gemini en un informe estratégico Markdown/HTML y en sentencias SQL.
"""

import json
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
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
        """Genera sentencias SQL para persistir las propuestas en PostgreSQL (Hetzner)."""
        diag = self.data["diagnostico"]
        propuestas = self.data["propuestas"]

        sql = [
            "-- ==================================================================",
            "-- PERSISTENCIA DE PROPUESTAS CURRICULARES IA EN POSTGRESQL (HETZNER)",
            "-- ==================================================================",
            "",
            "DROP TABLE IF EXISTS fact_modulos_propuestas CASCADE;",
            "DROP TABLE IF EXISTS dim_propuestas_curriculares CASCADE;",
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
            """CREATE TABLE dim_propuestas_curriculares (
    id_propuesta VARCHAR(64) PRIMARY KEY,
    tipo_propuesta VARCHAR(100),
    nombre_programa VARCHAR(250),
    titulo_otorgado VARCHAR(250),
    nivel_academico VARCHAR(100),
    duracion_estimada VARCHAR(100),
    creditos_totales INTEGER,
    horas_totales INTEGER,
    modalidad VARCHAR(100),
    impacto_salarial TEXT,
    perfil_ingreso TEXT,
    perfil_egreso TEXT
);""",
            "",
            """CREATE TABLE fact_modulos_propuestas (
    id_modulo SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares(id_propuesta),
    nombre_modulo VARCHAR(250),
    semestre_sugerido INTEGER,
    creditos INTEGER,
    horas_tfd INTEGER,
    horas_tti INTEGER,
    stack_tecnologico TEXT,
    raes TEXT,
    justificacion_mercado TEXT
);""",
            ""
        ]

        # Insert diagnostico
        resumen_safe = diag["resumen_ejecutivo"].replace("'", "''")
        sql.append(f"INSERT INTO fact_diagnostico_ia (programa_evaluado, puntuacion_competitividad, resumen_ejecutivo) VALUES ('Tecnología en Análisis y Gestión de Datos', {diag['puntuacion_competitividad_mercado']}, '{resumen_safe}');\n")

        # Insert propuestas
        for p in propuestas:
            id_p = p["id_propuesta"]
            tipo = p["tipo_propuesta"].replace("'", "''")
            nombre = p["nombre_programa"].replace("'", "''")
            titulo = p["titulo_otorgado"].replace("'", "''")
            nivel = p["nivel_academico"].replace("'", "''")
            dur = p["duracion_estimada"].replace("'", "''")
            mod = p["modalidad_sugerida"].replace("'", "''")
            sal = p["impacto_salarial_proyectado"].replace("'", "''")
            p_in = p["perfil_ingreso"].replace("'", "''")
            p_out = p["perfil_egreso"].replace("'", "''")

            sql.append(
                f"INSERT INTO dim_propuestas_curriculares VALUES ('{id_p}', '{tipo}', '{nombre}', '{titulo}', '{nivel}', '{dur}', {p['creditos_totales']}, {p['horas_totales']}, '{mod}', '{sal}', '{p_in}', '{p_out}');"
            )

            for m in p["plan_estudios"]:
                m_nom = m["nombre_modulo"].replace("'", "''")
                sem = m.get("semestre_sugerido") or 1
                stack = ", ".join(m["stack_tecnologico"]).replace("'", "''")
                raes = " | ".join(m["resultados_aprendizaje_esperados_rae"]).replace("'", "''")
                just = m["justificacion_demanda_laboral"].replace("'", "''")

                sql.append(
                    f"INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('{id_p}', '{m_nom}', {sem}, {m['creditos']}, {m['horas_tfd']}, {m['horas_tti']}, '{stack}', '{raes}', '{just}');"
                )

        SQL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SQL_OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(sql))

        print(f"[SQL] Script SQL generado en: {SQL_OUTPUT_PATH}")
        return SQL_OUTPUT_PATH

if __name__ == "__main__":
    generator = CurriculumReportGenerator()
    generator.generar_informe_markdown()
    generator.generar_script_sql()
