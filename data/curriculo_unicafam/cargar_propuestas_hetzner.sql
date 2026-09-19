-- ==================================================================
-- PERSISTENCIA DE PROPUESTAS CURRICULARES IA EN POSTGRESQL (HETZNER)
-- ==================================================================

DROP TABLE IF EXISTS fact_modulos_propuestas CASCADE;
DROP TABLE IF EXISTS dim_propuestas_curriculares CASCADE;
DROP TABLE IF EXISTS fact_diagnostico_ia CASCADE;

CREATE TABLE fact_diagnostico_ia (
    id SERIAL PRIMARY KEY,
    programa_evaluado VARCHAR(200),
    puntuacion_competitividad NUMERIC(5,2),
    resumen_ejecutivo TEXT,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_propuestas_curriculares (
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
);

CREATE TABLE fact_modulos_propuestas (
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
);

INSERT INTO fact_diagnostico_ia (programa_evaluado, puntuacion_competitividad, resumen_ejecutivo) VALUES ('Tecnología en Análisis y Gestión de Datos', 72.5, 'El programa de Tecnología en Análisis y Gestión de Datos presenta una base sólida en fundamentos de programación (Python) y gestión de datos (SQL), lo que le otorga una cobertura de mercado del 69.7%. Sin embargo, existe una desconexión crítica entre el perfil actual y las vacantes de ''Alto Salario''. El currículo actual está orientado a un perfil de analista tradicional, mientras que el mercado demanda perfiles de ''Científico de Datos'' con competencias avanzadas en infraestructura Cloud (GCP/AWS), automatización (MLOps) y procesamiento de lenguaje natural (NLP/LLMs). La falta de herramientas de visualización líderes (Power BI) y arquitecturas de nube pone en riesgo la competitividad salarial de los egresados, limitándolos al mercado local de ingresos medios y bloqueando su acceso al mercado remoto internacional de altos ingresos.');

INSERT INTO dim_propuestas_curriculares VALUES ('PROP_01', 'Electiva de Profundización', 'Implementación de Arquitecturas Cloud y MLOps', 'Certificado de Profundización en Cloud Data & MLOps', 'Pregrado', '1 semestre', 6, 288, 'Híbrida / PAT', '+45% de incremento salarial al acceder a roles de infraestructura cloud.', 'Estudiantes de últimos semestres de Tecnología en Análisis de Datos con bases en Python y SQL.', 'Capaz de desplegar modelos de machine learning en entornos de nube y gestionar pipelines de datos automatizados.');
INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 'Arquitecturas de Datos en la Nube (AWS & GCP)', 5, 3, 48, 96, 'AWS S3, AWS Glue, Google Cloud Storage, BigQuery', 'Configurar entornos de almacenamiento y procesamiento de datos en la nube utilizando servicios gestionados de AWS y GCP.', 'Las brechas de alto salario identificadas muestran que GCP y AWS son los motores de salarios superiores a $11M COP.');
INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 'Automatización y Ciclo de Vida de Modelos (MLOps)', 5, 3, 48, 96, 'Docker, Git, MLflow, CI/CD Pipelines', 'Diseñar flujos de trabajo automatizados para el entrenamiento, despliegue y monitoreo de modelos de aprendizaje automático.', 'El mercado demanda la transición de modelos experimentales a modelos productivos mediante control de versiones y contenedores.');
INSERT INTO dim_propuestas_curriculares VALUES ('PROP_02', 'Microcredencial / Certificación Corta', 'Business Intelligence Avanzado & Data Storytelling', 'Certificación en Analítica de Negocios con Power BI', 'Educación Continua', '8 semanas', 2, 96, 'Virtual Sincrónica', 'Aumento inmediato de empleabilidad en roles de analítica de negocios local.', 'Profesionales o técnicos con conocimiento básico de Excel y manejo de datos.', 'Especialista en la creación de tableros de control interactivos y modelamiento de datos para la toma de decisiones.');
INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_02', 'Modelamiento DAX y Visualización de Impacto', N/A, 2, 16, 32, 'Power BI, DAX, Power Query', 'Construir modelos de datos relacionales y medidas complejas utilizando el lenguaje DAX para resolver problemas de negocio.', 'Power BI aparece consistentemente como una de las habilidades con mayor brecha (GAP 0 materias) en el análisis de mercado.');
INSERT INTO dim_propuestas_curriculares VALUES ('PROP_03', 'Especialización Universitaria', 'Especialización en Ingeniería de Datos y Arquitecturas Cloud', 'Especialista en Ingeniería de Datos', 'Posgrado', '2 semestres', 24, 1152, 'Híbrida', 'Salarios proyectados de $10M - $18M COP en mercado local.', 'Tecnólogos o profesionales en áreas de sistemas, estadística o ingeniería con manejo de Python/SQL.', 'Arquitecto de soluciones de datos capaz de diseñar infraestructuras escalables para grandes volúmenes de información.');
INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_03', 'Ingeniería de Pipelines de Datos a Escala', 1, 8, 32, 64, 'Apache Spark, PySpark, Airflow', 'Implementar procesos de extracción, transformación y carga (ETL) utilizando frameworks de procesamiento distribuido.', 'El procesamiento distribuido (Spark) es una necesidad crítica para roles de Data Engineering de alto nivel.');
INSERT INTO dim_propuestas_curriculares VALUES ('PROP_04', 'Maestría Aplicada', 'Maestría en Inteligencia Artificial y Analítica Estratégica', 'Magíster en IA Aplicada', 'Posgrado', '4 semestres', 48, 2304, 'Virtual / Híbrida', 'Acceso al mercado remoto internacional con promedios > $30M COP.', 'Profesionales con sólida base matemática, estadística y de programación.', 'Líder de proyectos de IA capaz de integrar modelos de lenguaje generativo y aprendizaje profundo en estrategias de negocio.');
INSERT INTO fact_modulos_propuestas (id_propuesta, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_04', 'Deep Learning y Procesamiento de Lenguaje Natural (NLP/LLMs)', 2, 12, 48, 96, 'PyTorch, Hugging Face, LangChain, TensorFlow', 'Desarrollar aplicaciones basadas en modelos de lenguaje de gran escala y arquitecturas de redes neuronales profundas.', 'NLP/LLMs es una de las brechas tecnológicas con mayor crecimiento y demanda salarial en el mercado global.');