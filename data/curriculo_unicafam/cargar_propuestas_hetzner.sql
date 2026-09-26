-- ==================================================================
-- PERSISTENCIA DE PROPUESTAS CURRICULARES MIG EN POSTGRESQL (HETZNER)
-- Compatible con Apache Superset (jfbernalp.dev)
-- ==================================================================

DROP VIEW IF EXISTS view_superset_kpis_curriculares_mig CASCADE;
DROP VIEW IF EXISTS view_superset_malla_curricular_mig CASCADE;
DROP VIEW IF EXISTS view_superset_oferta_academica_mig CASCADE;
DROP TABLE IF EXISTS dim_docentes_propuestas_mig CASCADE;
DROP TABLE IF EXISTS fact_modulos_propuestas_mig CASCADE;
DROP TABLE IF EXISTS dim_propuestas_curriculares_mig CASCADE;
DROP TABLE IF EXISTS fact_diagnostico_ia CASCADE;

CREATE TABLE fact_diagnostico_ia (
    id SERIAL PRIMARY KEY,
    programa_evaluado VARCHAR(200),
    puntuacion_competitividad NUMERIC(5,2),
    resumen_ejecutivo TEXT,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_propuestas_curriculares_mig (
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

CREATE TABLE fact_modulos_propuestas_mig (
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

CREATE TABLE dim_docentes_propuestas_mig (
    id_docente SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares_mig(id_propuesta) ON DELETE CASCADE,
    nombre_o_rol VARCHAR(250),
    modulo_asignado VARCHAR(250),
    perfil_experto TEXT
);

INSERT INTO fact_diagnostico_ia (programa_evaluado, puntuacion_competitividad, resumen_ejecutivo) VALUES ('Tecnología en Análisis y Gestión de Datos', 72.5, 'El programa de Tecnología en Análisis y Gestión de Datos presenta una base sólida en fundamentos de programación (Python) y gestión de datos (SQL), lo que le otorga una cobertura de mercado del 69.7%. Sin embargo, existe una desconexión crítica entre el perfil actual y las vacantes de ''Alto Salario''. El currículo actual está orientado a un perfil de analista tradicional, mientras que el mercado demanda perfiles de ''Científico de Datos'' con competencias avanzadas en infraestructura Cloud (GCP/AWS), automatización (MLOps) y procesamiento de lenguaje natural (NLP/LLMs). La falta de herramientas de visualización líderes (Power BI) y arquitecturas de nube pone en riesgo la competitividad salarial de los egresados, limitándolos al mercado local de ingresos medios y bloqueando su acceso al mercado remoto internacional de altos ingresos.');

INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_01', 'Electiva de Profundización', 'Implementación de Arquitecturas Cloud y MLOps', 'Certificado de Profundización en Cloud Data & MLOps', 'Pregrado', '1 semestre', 6, 288, 'Híbrida / PAT', 'Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas', 'Próximo inicio de cohorte académica', 'Al completar el número total de horas del programa', 'Cohortes semestrales continuas', 'Por definir según tarifario institucional', 'Descuento especial comunidad UniCafam / Afiliados Cafam', 'Tarifa preferencial egresados UniCafam', 'Tarifa corporativa por volumen (>3 inscritos)', 'El presente programa responde a las demandas urgentes del mercado laboral identificadas por el Observatorio de Inteligencia Laboral de UniCafam. El análisis de vacantes revela una brecha del sector productivo en competencias de Implementación de Arquitecturas Cloud y MLOps. El impacto salarial proyectado (+45% de incremento salarial al acceder a roles de infraestructura cloud.) sustenta la pertinencia de formar talento especializado con alta tasa de empleabilidad y proyección nacional e internacional.', 'Desarrollar competencias especializadas en Implementación de Arquitecturas Cloud y MLOps para responder a los desafíos tecnológicos del mercado.
Implementar soluciones técnicas reales mediante proyectos aplicados utilizando herramientas líderes de la industria.
Integrar metodologías ágiles y estándares internacionales en el ciclo de vida de los datos e inteligencia artificial.', 'Estudiantes de últimos semestres de Tecnología en Análisis de Datos con bases en Python y SQL.', 'Metodología 100% teórico-práctica con enfoque en Aprendizaje Basado en Retos y Proyectos Reales (PBL). Las sesiones combinan fundamentación conceptual, laboratorios guiados en la nube y trabajo autónomo con acompañamiento de expertos de la industria. Cada módulo concluye con un entregable técnico aplicable.', 'Alineación directa con los requisitos reales de vacantes analizadas en el Observatorio Laboral.
Enfoque en tecnologías de alta prima salarial (+45% de incremento salarial al acceder a roles de infraestructura cloud.).
Certificación institucional respaldada por la Fundación Universitaria Cafam.
Docentes activos y líderes técnicos en empresas multinacionales de tecnología.', 'Estudiantes de últimos semestres de Tecnología en Análisis de Datos con bases en Python y SQL.', 'Capaz de desplegar modelos de machine learning en entornos de nube y gestionar pipelines de datos automatizados.', 'Junior Cloud Data Engineer, MLOps Assistant, Data Pipeline Technician', '+45% de incremento salarial al acceder a roles de infraestructura cloud.', 'https://jfbernalp.dev/downloads/mig/PROP_01_MIG.xlsx');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 1, 'Arquitecturas de Datos en la Nube (AWS & GCP)', '5', 3, 48, 96, 144, 'Unidades Temáticas:
1. Fundamentación y Arquitectura.
2. Implementación Práctica y Laboratorios (AWS S3, AWS Glue, Google Cloud Storage, BigQuery).
3. Proyecto de Aplicación y Evaluación.

Resultados de Aprendizaje:
Configurar entornos de almacenamiento y procesamiento de datos en la nube utilizando servicios gestionados de AWS y GCP.', 'Módulo 1 - Semanas 1 a 4', 'AWS S3, AWS Glue, Google Cloud Storage, BigQuery', 'Configurar entornos de almacenamiento y procesamiento de datos en la nube utilizando servicios gestionados de AWS y GCP.', 'Las brechas de alto salario identificadas muestran que GCP y AWS son los motores de salarios superiores a $11M COP.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 2, 'Automatización y Ciclo de Vida de Modelos (MLOps)', '5', 3, 48, 96, 144, 'Unidades Temáticas:
1. Fundamentación y Arquitectura.
2. Implementación Práctica y Laboratorios (Docker, Git, MLflow, CI/CD Pipelines).
3. Proyecto de Aplicación y Evaluación.

Resultados de Aprendizaje:
Diseñar flujos de trabajo automatizados para el entrenamiento, despliegue y monitoreo de modelos de aprendizaje automático.', 'Módulo 2 - Semanas 5 a 8', 'Docker, Git, MLflow, CI/CD Pipelines', 'Diseñar flujos de trabajo automatizados para el entrenamiento, despliegue y monitoreo de modelos de aprendizaje automático.', 'El mercado demanda la transición de modelos experimentales a modelos productivos mediante control de versiones y contenedores.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_01', 'Especialista / Magíster en AWS S3', 'Arquitecturas de Datos en la Nube (AWS & GCP)', 'Profesional con más de 5 años de experiencia liderando proyectos de Arquitecturas de Datos en la Nube (AWS & GCP) en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_01', 'Especialista / Magíster en Docker', 'Automatización y Ciclo de Vida de Modelos (MLOps)', 'Profesional con más de 5 años de experiencia liderando proyectos de Automatización y Ciclo de Vida de Modelos (MLOps) en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_02', 'Microcredencial / Certificación Corta', 'Business Intelligence Avanzado & Data Storytelling', 'Certificación en Analítica de Negocios con Power BI', 'Educación Continua', '8 semanas', 2, 96, 'Virtual Sincrónica', 'Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas', 'Próximo inicio de cohorte académica', 'Al completar el número total de horas del programa', 'Cohortes semestrales continuas', 'Por definir según tarifario institucional', 'Descuento especial comunidad UniCafam / Afiliados Cafam', 'Tarifa preferencial egresados UniCafam', 'Tarifa corporativa por volumen (>3 inscritos)', 'El presente programa responde a las demandas urgentes del mercado laboral identificadas por el Observatorio de Inteligencia Laboral de UniCafam. El análisis de vacantes revela una brecha del sector productivo en competencias de Business Intelligence Avanzado & Data Storytelling. El impacto salarial proyectado (Aumento inmediato de empleabilidad en roles de analítica de negocios local.) sustenta la pertinencia de formar talento especializado con alta tasa de empleabilidad y proyección nacional e internacional.', 'Desarrollar competencias especializadas en Business Intelligence Avanzado & Data Storytelling para responder a los desafíos tecnológicos del mercado.
Implementar soluciones técnicas reales mediante proyectos aplicados utilizando herramientas líderes de la industria.
Integrar metodologías ágiles y estándares internacionales en el ciclo de vida de los datos e inteligencia artificial.', 'Profesionales o técnicos con conocimiento básico de Excel y manejo de datos.', 'Metodología 100% teórico-práctica con enfoque en Aprendizaje Basado en Retos y Proyectos Reales (PBL). Las sesiones combinan fundamentación conceptual, laboratorios guiados en la nube y trabajo autónomo con acompañamiento de expertos de la industria. Cada módulo concluye con un entregable técnico aplicable.', 'Alineación directa con los requisitos reales de vacantes analizadas en el Observatorio Laboral.
Enfoque en tecnologías de alta prima salarial (Aumento inmediato de empleabilidad en roles de analítica de negocios local.).
Certificación institucional respaldada por la Fundación Universitaria Cafam.
Docentes activos y líderes técnicos en empresas multinacionales de tecnología.', 'Profesionales o técnicos con conocimiento básico de Excel y manejo de datos.', 'Especialista en la creación de tableros de control interactivos y modelamiento de datos para la toma de decisiones.', 'BI Analyst, Data Visualization Specialist', 'Aumento inmediato de empleabilidad en roles de analítica de negocios local.', 'https://jfbernalp.dev/downloads/mig/PROP_02_MIG.xlsx');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_02', 1, 'Modelamiento DAX y Visualización de Impacto', 'N/A', 2, 16, 32, 48, 'Unidades Temáticas:
1. Fundamentación y Arquitectura.
2. Implementación Práctica y Laboratorios (Power BI, DAX, Power Query).
3. Proyecto de Aplicación y Evaluación.

Resultados de Aprendizaje:
Construir modelos de datos relacionales y medidas complejas utilizando el lenguaje DAX para resolver problemas de negocio.', 'Módulo 1 - Semanas 1 a 4', 'Power BI, DAX, Power Query', 'Construir modelos de datos relacionales y medidas complejas utilizando el lenguaje DAX para resolver problemas de negocio.', 'Power BI aparece consistentemente como una de las habilidades con mayor brecha (GAP 0 materias) en el análisis de mercado.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_02', 'Especialista / Magíster en Power BI', 'Modelamiento DAX y Visualización de Impacto', 'Profesional con más de 5 años de experiencia liderando proyectos de Modelamiento DAX y Visualización de Impacto en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_03', 'Especialización Universitaria', 'Especialización en Ingeniería de Datos y Arquitecturas Cloud', 'Especialista en Ingeniería de Datos', 'Posgrado', '2 semestres', 24, 1152, 'Híbrida', 'Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas', 'Próximo inicio de cohorte académica', 'Al completar el número total de horas del programa', 'Cohortes semestrales continuas', 'Por definir según tarifario institucional', 'Descuento especial comunidad UniCafam / Afiliados Cafam', 'Tarifa preferencial egresados UniCafam', 'Tarifa corporativa por volumen (>3 inscritos)', 'El presente programa responde a las demandas urgentes del mercado laboral identificadas por el Observatorio de Inteligencia Laboral de UniCafam. El análisis de vacantes revela una brecha del sector productivo en competencias de Especialización en Ingeniería de Datos y Arquitecturas Cloud. El impacto salarial proyectado (Salarios proyectados de $10M - $18M COP en mercado local.) sustenta la pertinencia de formar talento especializado con alta tasa de empleabilidad y proyección nacional e internacional.', 'Desarrollar competencias especializadas en Especialización en Ingeniería de Datos y Arquitecturas Cloud para responder a los desafíos tecnológicos del mercado.
Implementar soluciones técnicas reales mediante proyectos aplicados utilizando herramientas líderes de la industria.
Integrar metodologías ágiles y estándares internacionales en el ciclo de vida de los datos e inteligencia artificial.', 'Tecnólogos o profesionales en áreas de sistemas, estadística o ingeniería con manejo de Python/SQL.', 'Metodología 100% teórico-práctica con enfoque en Aprendizaje Basado en Retos y Proyectos Reales (PBL). Las sesiones combinan fundamentación conceptual, laboratorios guiados en la nube y trabajo autónomo con acompañamiento de expertos de la industria. Cada módulo concluye con un entregable técnico aplicable.', 'Alineación directa con los requisitos reales de vacantes analizadas en el Observatorio Laboral.
Enfoque en tecnologías de alta prima salarial (Salarios proyectados de $10M - $18M COP en mercado local.).
Certificación institucional respaldada por la Fundación Universitaria Cafam.
Docentes activos y líderes técnicos en empresas multinacionales de tecnología.', 'Tecnólogos o profesionales en áreas de sistemas, estadística o ingeniería con manejo de Python/SQL.', 'Arquitecto de soluciones de datos capaz de diseñar infraestructuras escalables para grandes volúmenes de información.', 'Data Engineer, Cloud Data Architect, ETL Developer', 'Salarios proyectados de $10M - $18M COP en mercado local.', 'https://jfbernalp.dev/downloads/mig/PROP_03_MIG.xlsx');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_03', 1, 'Ingeniería de Pipelines de Datos a Escala', '1', 8, 32, 64, 96, 'Unidades Temáticas:
1. Fundamentación y Arquitectura.
2. Implementación Práctica y Laboratorios (Apache Spark, PySpark, Airflow).
3. Proyecto de Aplicación y Evaluación.

Resultados de Aprendizaje:
Implementar procesos de extracción, transformación y carga (ETL) utilizando frameworks de procesamiento distribuido.', 'Módulo 1 - Semanas 1 a 4', 'Apache Spark, PySpark, Airflow', 'Implementar procesos de extracción, transformación y carga (ETL) utilizando frameworks de procesamiento distribuido.', 'El procesamiento distribuido (Spark) es una necesidad crítica para roles de Data Engineering de alto nivel.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_03', 'Especialista / Magíster en Apache Spark', 'Ingeniería de Pipelines de Datos a Escala', 'Profesional con más de 5 años de experiencia liderando proyectos de Ingeniería de Pipelines de Datos a Escala en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_04', 'Maestría Aplicada', 'Maestría en Inteligencia Artificial y Analítica Estratégica', 'Magíster en IA Aplicada', 'Posgrado', '4 semestres', 48, 2304, 'Virtual / Híbrida', 'Sábados de 8:00 a.m. a 1:00 p.m. / Sesiones sincrónicas', 'Próximo inicio de cohorte académica', 'Al completar el número total de horas del programa', 'Cohortes semestrales continuas', 'Por definir según tarifario institucional', 'Descuento especial comunidad UniCafam / Afiliados Cafam', 'Tarifa preferencial egresados UniCafam', 'Tarifa corporativa por volumen (>3 inscritos)', 'El presente programa responde a las demandas urgentes del mercado laboral identificadas por el Observatorio de Inteligencia Laboral de UniCafam. El análisis de vacantes revela una brecha del sector productivo en competencias de Maestría en Inteligencia Artificial y Analítica Estratégica. El impacto salarial proyectado (Acceso al mercado remoto internacional con promedios > $30M COP.) sustenta la pertinencia de formar talento especializado con alta tasa de empleabilidad y proyección nacional e internacional.', 'Desarrollar competencias especializadas en Maestría en Inteligencia Artificial y Analítica Estratégica para responder a los desafíos tecnológicos del mercado.
Implementar soluciones técnicas reales mediante proyectos aplicados utilizando herramientas líderes de la industria.
Integrar metodologías ágiles y estándares internacionales en el ciclo de vida de los datos e inteligencia artificial.', 'Profesionales con sólida base matemática, estadística y de programación.', 'Metodología 100% teórico-práctica con enfoque en Aprendizaje Basado en Retos y Proyectos Reales (PBL). Las sesiones combinan fundamentación conceptual, laboratorios guiados en la nube y trabajo autónomo con acompañamiento de expertos de la industria. Cada módulo concluye con un entregable técnico aplicable.', 'Alineación directa con los requisitos reales de vacantes analizadas en el Observatorio Laboral.
Enfoque en tecnologías de alta prima salarial (Acceso al mercado remoto internacional con promedios > $30M COP.).
Certificación institucional respaldada por la Fundación Universitaria Cafam.
Docentes activos y líderes técnicos en empresas multinacionales de tecnología.', 'Profesionales con sólida base matemática, estadística y de programación.', 'Líder de proyectos de IA capaz de integrar modelos de lenguaje generativo y aprendizaje profundo en estrategias de negocio.', 'Senior Data Scientist, AI Solution Architect, Machine Learning Engineer', 'Acceso al mercado remoto internacional con promedios > $30M COP.', 'https://jfbernalp.dev/downloads/mig/PROP_04_MIG.xlsx');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_04', 1, 'Deep Learning y Procesamiento de Lenguaje Natural (NLP/LLMs)', '2', 12, 48, 96, 144, 'Unidades Temáticas:
1. Fundamentación y Arquitectura.
2. Implementación Práctica y Laboratorios (PyTorch, Hugging Face, LangChain, TensorFlow).
3. Proyecto de Aplicación y Evaluación.

Resultados de Aprendizaje:
Desarrollar aplicaciones basadas en modelos de lenguaje de gran escala y arquitecturas de redes neuronales profundas.', 'Módulo 1 - Semanas 1 a 4', 'PyTorch, Hugging Face, LangChain, TensorFlow', 'Desarrollar aplicaciones basadas en modelos de lenguaje de gran escala y arquitecturas de redes neuronales profundas.', 'NLP/LLMs es una de las brechas tecnológicas con mayor crecimiento y demanda salarial en el mercado global.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_04', 'Especialista / Magíster en PyTorch', 'Deep Learning y Procesamiento de Lenguaje Natural (NLP/LLMs)', 'Profesional con más de 5 años de experiencia liderando proyectos de Deep Learning y Procesamiento de Lenguaje Natural (NLP/LLMs) en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado.');

-- Vistas para Apache Superset
CREATE OR REPLACE VIEW view_superset_oferta_academica_mig AS
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

CREATE OR REPLACE VIEW view_superset_malla_curricular_mig AS
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

CREATE OR REPLACE VIEW view_superset_kpis_curriculares_mig AS
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