-- ====================================================================================
-- VISTAS SQL Y MODELO DIMENSIONAL PARA APACHE SUPERSET - OFERTA CURRICULAR MIG UNICAFAM
-- Compatible con PostgreSQL (Hetzner / Supabase) y SQLite
-- ====================================================================================

-- 1. Tabla de Diagnóstico Ejecutivo FODA e Índice de Competitividad
CREATE TABLE IF NOT EXISTS fact_diagnostico_ia (
    id SERIAL PRIMARY KEY,
    programa_evaluado VARCHAR(200),
    puntuacion_competitividad NUMERIC(5,2),
    resumen_ejecutivo TEXT,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimensión de Propuestas Curriculares (Formato Matriz Integrada de Gestión MIG)
CREATE TABLE IF NOT EXISTS dim_propuestas_curriculares_mig (
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
);

-- 3. Tabla de Hechos: Módulos y Malla Formativa MIG
CREATE TABLE IF NOT EXISTS fact_modulos_propuestas_mig (
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
);

-- 4. Dimensión: Cuerpo Docente y Perfiles de Expertos MIG
CREATE TABLE IF NOT EXISTS dim_docentes_propuestas_mig (
    id_docente SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares_mig(id_propuesta) ON DELETE CASCADE,
    nombre_o_rol VARCHAR(250),
    modulo_asignado VARCHAR(250),
    perfil_experto TEXT
);

-- ====================================================================================
-- VISTAS OPTIMIZADAS PARA DATASETS Y DASHBOARDS EN APACHE SUPERSET
-- ====================================================================================

-- Vista 1: Oferta Académica Consolidada para Tablas y Tarjetas en Superset
CREATE VIEW IF NOT EXISTS view_superset_oferta_academica_mig AS
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
    p.objetivos_programa, p.metodologia_detallada, p.valores_agregados, p.url_descarga_excel;

-- Vista 2: Desglose Modular y Malla Curricular para Gráficos y Tablas Detalladas
CREATE VIEW IF NOT EXISTS view_superset_malla_curricular_mig AS
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
LEFT JOIN dim_docentes_propuestas_mig d ON m.id_propuesta = d.id_propuesta AND m.nombre_modulo = d.modulo_asignado;

-- Vista 3: Scorecards y Métricas Ejecutivas del Observatorio Laboral UniCafam
CREATE VIEW IF NOT EXISTS view_superset_kpis_curriculares_mig AS
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
LIMIT 1;
