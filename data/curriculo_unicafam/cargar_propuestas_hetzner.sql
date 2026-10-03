-- ==================================================================
-- PERSISTENCIA DE PROPUESTAS CURRICULARES MIG EN POSTGRESQL (HETZNER)
-- Compatible con Apache Superset (jfbernalp.dev)
-- ==================================================================

DROP VIEW IF EXISTS view_superset_kpis_curriculares_mig CASCADE;
DROP VIEW IF EXISTS view_superset_malla_curricular_mig CASCADE;
DROP VIEW IF EXISTS view_superset_oferta_academica_mig CASCADE;
DROP TABLE IF EXISTS historial_revisiones_curriculo CASCADE;
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
    url_descarga_excel TEXT,
    estado VARCHAR(50) DEFAULT 'PENDIENTE_REVISION',
    version INTEGER DEFAULT 1,
    aprobado_por VARCHAR(150),
    fecha_decision VARCHAR(50),
    motivo_rechazo TEXT
);

CREATE TABLE historial_revisiones_curriculo (
    id SERIAL PRIMARY KEY,
    id_propuesta VARCHAR(64) REFERENCES dim_propuestas_curriculares_mig(id_propuesta) ON DELETE CASCADE,
    version_resultante INTEGER,
    usuario_aprobador VARCHAR(150),
    rol_usuario VARCHAR(100),
    decision VARCHAR(50),
    comentarios_feedback TEXT,
    cambios_aplicados_resumen TEXT,
    fecha_registro VARCHAR(50)
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

INSERT INTO fact_diagnostico_ia (programa_evaluado, puntuacion_competitividad, resumen_ejecutivo) VALUES ('Tecnología en Análisis y Gestión de Datos', 52.0, 'El ecosistema de formación en datos de UniCafam (Tecnología en Análisis y Gestión de Datos, articulado por ciclo propedéutico al Profesional en Ciencia de Datos) posee bases curriculares extraordinariamente competitivas. El programa actual cubre con rigor competencias clave en Python, SQL, NLP, Machine Learning y visualización con Power BI/Tableau, alcanzando una cobertura de mercado del 52.0%. No obstante, el Observatorio Laboral revela una brecha salarial abismal entre el mercado local colombiano ($4.516.768 COP promedio) y el mercado remoto internacional ($32.943.043 COP promedio). Las vacantes de alto valor (salarios superiores a $11.000.000 COP local y hasta $68.000.000 COP remoto) exigen competencias de ingeniería y operaciones que actualmente no forman parte del núcleo básico del tecnólogo. Para capitalizar el 48% restante del mercado, la institución debe proyectar una ruta de profundización y posgrado enfocada en: 1) Infraestructura Cloud Enterprise (AWS, GCP, Azure), 2) Prácticas de MLOps y contenedorización (Docker, Kubernetes, MLflow), 3) Big Data Distribuido a gran escala (Databricks, Spark) y 4) IA Generativa aplicada a nivel empresarial. Esta estrategia curricular no reemplaza nuestras fortalezas actuales; las potencia, garantizando el cumplimiento de la reglamentación del Ministerio de Educación Nacional (Decreto 1330) y asegurando que nuestros egresados de tecnología escalen orgánicamente hacia roles profesionales y de posgrado de máxima remuneración global.');

INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_01', 'Electiva de Profundización', 'Implementación de Arquitecturas Cloud y MLOps', 'Certificado de Profundización en Cloud Data Engineering & MLOps', 'Pregrado', '1 semestre', 6, 288, 'Híbrida / PAT (Presencialidad Asistida por Tecnología)', 'Sábados de 7:00 a.m. a 1:00 p.m. / Sesiones sincrónicas virtuales y laboratorios presenciales bimensuales', 'Febrero de 2025', 'Junio de 2025', 'Cohortes en el primer y segundo semestre de cada año académico', '$2.950.000 COP', '$2.212.500 COP (25% dcto afiliados/estudiantes)', '$2.360.000 COP (20% dcto)', '$2.065.000 COP (por convenio empresarial >3 personas)', 'La tecnología en Análisis y Gestión de Datos de UniCafam forma tecnólogos con excelente dominio de análisis predictivo, Python y SQL. Sin embargo, para acceder a vacantes de alta remuneración, estos profesionales deben operar en la nube y automatizar el ciclo de vida de los modelos. Según el observatorio, AWS y GCP registran un porcentaje de penetración conjunto de más del 32% en la demanda y salarios de hasta $15M COP. Introducir una electiva de 6 créditos en el último año de la tecnología y articulación profesional asegura que el estudiante no solo construya modelos (lo que ya hace muy bien), sino que aprenda a empaquetarlos, desplegarlos y monitorearlos. Esto duplica de inmediato el espectro de empleabilidad hacia roles de Junior Cloud Engineer y MLOps Practitioner, apalancando la prima salarial internacional.', 'Objetivo General: Desarrollar competencias teórico-prácticas en la estructuración de flujos de datos automatizados y despliegue continuo de modelos de Machine Learning en entornos de computación en la nube empresariales.
Objetivo Específico 1: Implementar arquitecturas de almacenamiento y procesamiento serverless en AWS y GCP para canalizar volúmenes de datos a escala.
Objetivo Específico 2: Contenedorizar aplicaciones de IA utilizando Docker y desplegar microservicios eficientes accesibles a través de APIs web.
Objetivo Específico 3: Diseñar ciclos de vida automatizados de modelos (MLOps) integrando herramientas de tracking como MLflow y pipelines básicos de CI/CD.', 'Estudiantes de 5to semestre de la Tecnología en Análisis y Gestión de Datos, estudiantes de Ingeniería de Sistemas de UniCafam y egresados tecnólogos de datos que dominen Python intermedio y bases de datos relacionales.', 'Modelo pedagógico activo basado en retos (PBL - Project Based Learning). Los estudiantes desarrollarán un proyecto integrador a lo largo del semestre consistente en tomar un modelo predictivo previamente entrenado en su carrera, empaquetarlo en un contenedor Docker, desplegarlo como microservicio en AWS, y configurar su respectivo pipeline de control, monitoreo y CI/CD utilizando GitHub Actions y MLflow. Las clases constan de un 30% de conceptualización y un 70% de talleres aplicados en laboratorios cloud (AWS Academy y Google Cloud for Education).', 'Acceso gratuito a entornos sandbox de AWS y Google Cloud a través de convenios educativos de UniCafam.
Voucher de descuento de hasta el 50% para la certificación oficial AWS Certified Cloud Practitioner o GCP Associate Cloud Engineer.
Desarrollo de un portafolio de producción alojado en GitHub listo para ser presentado en procesos de selección internacional.', 'Estudiante o profesional del área de tecnología/sistemas con conocimientos demostrables en programación estructurada en Python (estructuras de datos, funciones, Pandas) y fundamentos conceptuales de bases de datos relacionales y Machine Learning básico.', 'Al finalizar la electiva, el egresado será capaz de aprovisionar infraestructura de computación y almacenamiento en la nube, diseñar canalizaciones de datos (pipelines) automatizadas, empaquetar algoritmos en contenedores portables y desplegar servicios web que expongan modelos analíticos listos para el consumo empresarial.', 'Asociado de Ingeniería de Datos (Junior Data Engineer), Especialista de Soporte Cloud (Cloud Support Associate), Practicante de Operaciones de Machine Learning (MLOps Practitioner)', '+55% sobre el promedio salarial de un analista de datos tradicional en el mercado local (Proyección de ingresos iniciales: $5.500.000 COP a $7.000.000 COP)', 'https://jfbernalp.dev/downloads/mig/PROP_01_MIG.xlsx', 'PENDIENTE_REVISION', 1, '', '', '');
INSERT INTO historial_revisiones_curriculo (id_propuesta, version_resultante, usuario_aprobador, rol_usuario, decision, comentarios_feedback, cambios_aplicados_resumen, fecha_registro) VALUES ('PROP_01', 1, 'Sistema Observatorio IA UniCafam', 'Motor Generativo (Gemini 3.5 Flash)', 'CREACION_INICIAL', 'Generación curricular inicial groundeada en datos del mercado laboral y Decreto 1330 MEN.', 'Diseño base de microcurrículos, RAEs y perfil docente.', '2026-10-03 12:00:00');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 1, 'Cloud Data Engineering (AWS & GCP Foundations)', '5', 3, 48, 96, 144, '1. Fundamentos de nube e Infraestructura Global.
2. Almacenamiento de datos escalable en AWS (S3) y GCP (Cloud Storage).
3. Bases de datos modernas y Data Warehousing (Amazon Redshift, Google BigQuery).
4. Orquestación serverless y ETL en la nube (AWS Glue, Cloud Dataflow).
5. Seguridad, gobernanza de datos y manejo de accesos (IAM).', 'Semanas 1 a 8', 'AWS S3, Google Cloud Storage, BigQuery, AWS Glue, IAM', 'Diseñar arquitecturas de almacenamiento híbrido utilizando servicios de nubes públicas líderes que soporten las necesidades analíticas de una organización. | Estructurar procesos ETL serverless para la ingesta, transformación y carga de bases de datos analíticas a gran escala.', 'Más del 32% de las ofertas analizadas en el Observatorio laboral de UniCafam exigen el manejo de AWS o GCP, estando asociadas a salarios medianos superiores a los $11.000.000 COP.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_01', 2, 'MLOps & Despliegue de Modelos de IA', '5', 3, 48, 96, 144, '1. Introducción al ciclo de vida de MLOps y comparación con DevOps.
2. Creación de APIs web para consumo de modelos (FastAPI, Flask).
3. Contenedorización de aplicaciones y entornos aislados de desarrollo con Docker.
4. Tracking de experimentos, almacenamiento de artefactos y registro de modelos con MLflow.
5. Monitoreo básico del comportamiento del modelo en producción (Data Drift e inferencia).', 'Semanas 9 a 16', 'Docker, FastAPI, MLflow, GitHub Actions', 'Empaquetar aplicaciones analíticas y modelos de Machine Learning dentro de contenedores estandarizados que aseguren su portabilidad entre diferentes plataformas. | Implementar flujos continuos de control de versiones y despliegue automatizado para el monitoreo sistemático de la degradación de modelos en producción.', 'MLOps se posiciona como una de las habilidades de mayor valor en el observatorio, con un salario mediano registrado en vacantes de $65.833.333 COP debido a su alta escasez de talento calificado.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_01', 'Especialista en Infraestructura de Datos Cloud', 'Cloud Data Engineering (AWS & GCP Foundations)', 'Ingeniero de Sistemas o de Datos con especialización o maestría en áreas afines, certificado oficialmente como AWS Certified Solutions Architect o GCP Professional Cloud Architect, con experiencia laboral mínima de 4 años en el sector corporativo diseñando pipelines en la nube.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_01', 'Ingeniero de Plataformas AI / MLOps Lead', 'MLOps & Despliegue de Modelos de IA', 'Científico de Datos Senior o MLOps Engineer con experiencia laboral de más de 5 años en despliegue de modelos a gran escala, dominio experto en metodologías ágiles de ingeniería de software, empaquetamiento con Docker y orquestadores.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_02', 'Microcredencial / Certificación Corta', 'IA Generativa y Arquitecturas RAG para Negocios', 'Certificación Universitaria de Especialista en IA Generativa & Arquitecturas RAG para Negocios', 'Educación Continua / Formación Avanzada', '8 semanas', 2, 96, '100% Virtual con mentorías semanales sincrónicas', 'Martes y Jueves de 6:00 p.m. a 9:00 p.m. (Virtual Sincrónico)', 'Abril de 2025', 'Junio de 2025', 'Tres ediciones anuales planificadas (Febrero, Junio, Septiembre)', '$1.500.000 COP', '$1.125.000 COP (25% dcto)', '$1.200.000 COP (20% dcto)', '$1.050.000 COP (por convenio empresarial >3 personas)', 'La revolución de la Inteligencia Artificial Generativa y los Modelos de Lenguaje de Gran Escala (LLMs) ha transformado la demanda empresarial. Los egresados de UniCafam cuentan con sólidas competencias en Procesamiento de Lenguaje Natural (NLP) tradicional gracias a la materia ''Procesamiento de Texto y Técnicas de Información''. Esta microcredencial tiende un puente directo hacia las tecnologías más modernas de IA de Frontera: Retrieval-Augmented Generation (RAG) y bases de datos vectoriales. Conectando lo que ya saben de procesamiento de texto con LLMs comerciales y de código abierto (Llama, OpenAI, Claude), el egresado se transforma en un desarrollador de soluciones cognitivas inteligentes que automatizan la búsqueda de información corporativa, impulsando su empleabilidad en un mercado que valora estas competencias en niveles sumamente altos.', 'Objetivo General: Capacitar en el diseño, desarrollo e integración de sistemas de IA Generativa empresariales utilizando arquitecturas RAG para optimizar la toma de decisiones y la automatización de procesos de consulta.
Objetivo Específico 1: Utilizar frameworks avanzados de desarrollo (LangChain e Indexadores) para orquestar flujos cognitivos complejos basados en LLMs.
Objetivo Específico 2: Implementar bases de datos vectoriales para el almacenamiento de embeddings semánticos optimizados.
Objetivo Específico 3: Diseñar aplicaciones web que utilicen técnicas de Prompt Engineering avanzado y agentes inteligentes autónomos.', 'Científicos de datos, tecnólogos en análisis de datos, ingenieros de desarrollo de software, analistas de BI senior y entusiastas de la tecnología con nociones lógicas de programación en Python.', 'Enfoque de taller práctico hands-on. Cada sesión sincrónica introduce un reto técnico real de la industria (p. ej., construir un chatbot que responda preguntas basadas exclusivamente en los manuales de procedimientos de una empresa). Los laboratorios se desarrollan sobre cuadernos de Jupyter de Google Colab utilizando APIs comerciales y modelos open-source de Hugging Face. Se utiliza un canal continuo de comunicación en Discord para mentorías personalizadas de código.', 'Inclusión en el portafolio institucional de microcredenciales digitales insignias de UniCafam con estándar internacional OpenBadges para compartir en LinkedIn.
Acceso directo a la comunidad de expertos en Inteligencia Artificial de la escuela de Ingeniería UniCafam.
Plantillas de código listas para producción en entornos empresariales.', 'Profesional o estudiante con bases sólidas de programación en Python (manipulación de APIs, manejo básico de librerías de datos) y comprensión conceptual de bases de datos SQL / NoSQL.', 'El egresado será capaz de construir pipelines de procesamiento de texto no estructurado, indexar información corporativa en bases de datos vectoriales en la nube, orquestar flujos de interacción con LLMs mediante LangChain y desplegar agentes inteligentes que interactúen con bases de datos internas de manera segura.', 'Desarrollador de Aplicaciones de Inteligencia Artificial (AI Application Developer), Ingeniero de Prompt & NLP (Prompt Engineer), Consultor Tecnológico en Soluciones Cognitivas', '+40% sobre la base de ingresos ordinaria debido a la alta escasez de desarrolladores especializados en integraciones con LLMs (Rango proyectado local: $6.000.000 COP - $8.500.000 COP)', 'https://jfbernalp.dev/downloads/mig/PROP_02_MIG.xlsx', 'PENDIENTE_REVISION', 1, '', '', '');
INSERT INTO historial_revisiones_curriculo (id_propuesta, version_resultante, usuario_aprobador, rol_usuario, decision, comentarios_feedback, cambios_aplicados_resumen, fecha_registro) VALUES ('PROP_02', 1, 'Sistema Observatorio IA UniCafam', 'Motor Generativo (Gemini 3.5 Flash)', 'CREACION_INICIAL', 'Generación curricular inicial groundeada en datos del mercado laboral y Decreto 1330 MEN.', 'Diseño base de microcurrículos, RAEs y perfil docente.', '2026-10-03 12:00:00');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_02', 1, 'Arquitecturas RAG & Bases de Datos Vectoriales', '1', 2, 32, 64, 96, '1. Introducción a la IA Generativa, Modelos Fundacionales y Transformers.
2. Fundamentos de Embeddings: Conversión de texto a vectores densos.
3. Bases de Datos Vectoriales: Almacenamiento, indexación y búsqueda en Pinecone, ChromaDB y Qdrant.
4. El flujo RAG (Retrieval-Augmented Generation): Conexión de documentos privados con LLMs.
5. Frameworks de Orquestación: Construcción paso a paso con LangChain y LlamaIndex.
6. Prompt Engineering Avanzado, técnicas Few-Shot y control de alucinaciones.
7. Agentes autónomos de IA que interactúan con APIs externas y SQL corporativo.
8. Despliegue de un prototipo interactivo utilizando Streamlit.', 'Semanas 1 a 8', 'LangChain, Pinecone, ChromaDB, OpenAI API, Hugging Face, Streamlit', 'Implementar arquitecturas del tipo Retrieval-Augmented Generation conectando repositorios documentales extensos con Modelos de Lenguaje de Gran Escala para responder consultas contextualizadas de alta precisión. | Configurar sistemas de persistencia e indexación vectorial óptimos de alto rendimiento que agilicen las búsquedas de proximidad semántica en la organización.', 'El segmento de NLP/LLMs registra una presencia crítica del 16% en la demanda analítica, con salarios promedio de $8.375.000 COP a nivel local, escalando rápidamente cuando se combina con tecnologías de vanguardia como agentes autónomos.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_02', 'Investigador / Ingeniero Senior en NLP & IA Generativa', 'Arquitecturas RAG & Bases de Datos Vectoriales', 'Profesional en Ingeniería de Sistemas, Inteligencia Artificial o Ciencia de Datos, con Maestría o Doctorado en Inteligencia Artificial o Computación Cognitiva, con publicaciones científicas o experiencia de mínimo 3 años desarrollando productos basados en tecnologías Transformers y modelos GPT.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_03', 'Especialización Universitaria', 'Especialización en Ingeniería de Datos y Arquitecturas Cloud', 'Especialista en Ingeniería de Datos y Arquitecturas Cloud', 'Posgrado', '2 semestres', 24, 1152, 'Híbrida (Virtual interactiva con laboratorios prácticos sincrónicos de alta intensidad)', 'Viernes de 5:00 p.m. a 10:00 p.m. y Sábados de 8:00 a.m. a 2:00 p.m.', 'Julio de 2025', 'Junio de 2026', 'Admisiones anuales para inicio en cada periodo académico del segundo semestre', '$9.800.000 COP por semestre', '$7.840.000 COP por semestre (20% dcto para egresados)', '$7.840.000 COP por semestre (20% dcto)', '$8.330.000 COP por semestre (15% dcto por convenios colectivos)', 'La ingeniería de datos es el pilar invisible pero más demandado del ecosistema de analítica moderno. Las ofertas para Ingenieros de Datos representan el 11.2% del total analizado, pero se caracterizan por una de las compensaciones promedio más elevadas del mercado nacional (salario promedio de $15M a $18M COP para especialistas en Azure, Databricks y Google Cloud). Un tecnólogo de UniCafam o un egresado de Ingeniería de Sistemas puede dar un salto profesional sin precedentes mediante este posgrado de un año. Mientras otros programas del mercado se centran excesivamente en la estadística teórica, UniCafam se posicionará como líder indiscutible en la formación de arquitectos de infraestructura, orquestación, Big Data distribuido y optimización de flujos de valor del dato empresarial, atendiendo una necesidad desatendida en el ecosistema nacional.', 'Objetivo General: Formar especialistas capaces de estructurar, optimizar y liderar la arquitectura de almacenamiento, procesamiento y distribución de flujos de datos empresariales multi-nube bajo estándares de seguridad y alta disponibilidad.
Objetivo Específico 1: Configurar sistemas distribuidos e infraestructuras híbridas que procesen petabytes de datos estructurados y no estructurados de manera eficiente.
Objetivo Específico 2: Diseñar flujos de integración y orquestación de datos automatizados robustos con tolerancia a fallas utilizando herramientas líderes como Apache Airflow.
Objetivo Específico 3: Implementar arquitecturas modernas de almacenamiento analítico como Lakehouses, Databricks y Delta Lakes.', 'Egresados del pregrado profesional en Ciencia de Datos, ingenieros de sistemas, ingenieros de software, tecnólogos en análisis de datos de UniCafam con experiencia profesional comprobada en programación avanzada y bases de datos relacionales, y profesionales de carreras cuantitativas de TI.', 'La metodología pedagógica integra estudios de casos reales con prácticas de co-diseño de arquitectura empresarial en la nube. Los laboratorios se desarrollan utilizando arquitecturas multi-cloud. Cada módulo de posgrado requiere la resolución de un problema de rendimiento de big data empresarial, en el cual se evalúa no solo el funcionamiento lógico sino el costo computacional de la nube, preparando al estudiante para gestionar recursos de tecnología reales de forma eficiente.', 'Alineación directa con la ruta de certificación oficial de Microsoft Certified: Azure Data Engineer Associate y Databricks Certified Associate Developer.
Acceso preferente al Laboratorio de Ciberseguridad y Big Data de la Escuela de Ingeniería de UniCafam.
Cátedra abierta de casos de éxito dictada por Directores de Datos (CDOs) de corporaciones líderes en la región.', 'Profesional graduado en ingeniería de sistemas, analítica, ciencia de datos u otras ramas de la ingeniería de software, con sólido dominio práctico de lenguajes de programación como Python y bases de datos transaccionales de alto rendimiento.', 'El Especialista de UniCafam podrá modelar y desplegar almacenes de datos a escala de petabytes en la nube, crear y gestionar canalizaciones de datos distribuidas con Spark y Apache Airflow, coordinar esquemas de gobernanza, seguridad y monitoreo de la calidad de datos y liderar de forma técnica la transformación de infraestructuras analíticas corporativas.', 'Ingeniero de Datos Senior (Senior Data Engineer), Arquitecto de Datos Cloud (Cloud Data Architect), Administrador de Infraestructuras Analíticas (Analytic Infrastructure Administrator)', 'Acceso directo a vacantes con salarios locales de nivel medio-alto y alto (Rango proyectado local: $12.000.000 COP a $18.000.000 COP, mercado internacional remoto: >$25.000.000 COP)', 'https://jfbernalp.dev/downloads/mig/PROP_03_MIG.xlsx', 'PENDIENTE_REVISION', 1, '', '', '');
INSERT INTO historial_revisiones_curriculo (id_propuesta, version_resultante, usuario_aprobador, rol_usuario, decision, comentarios_feedback, cambios_aplicados_resumen, fecha_registro) VALUES ('PROP_03', 1, 'Sistema Observatorio IA UniCafam', 'Motor Generativo (Gemini 3.5 Flash)', 'CREACION_INICIAL', 'Generación curricular inicial groundeada en datos del mercado laboral y Decreto 1330 MEN.', 'Diseño base de microcurrículos, RAEs y perfil docente.', '2026-10-03 12:00:00');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_03', 1, 'Procesamiento Distribuido a Gran Escala con Databricks & Spark', '1', 4, 64, 128, 192, '1. Fundamentos de computación distribuida y arquitecturas de memoria RAM masiva.
2. Arquitectura interna de Apache Spark y APIs principales (DataFrames y SQL).
3. Gestión de clusters de datos, procesamiento Batch y Streaming de datos a gran escala.
4. Introducción a la plataforma unificada Databricks.
5. El paradigma Modern Lakehouse y persistencia tolerante con Delta Lake.
6. Optimización de rendimiento de procesamiento distribuido y particionamiento de datos.', 'Semanas 1 a 12 (Primer Semestre)', 'Apache Spark, PySpark, Databricks, Delta Lake, Parquet', 'Estructurar flujos de datos analíticos masivos procesando información persistida de forma paralela en clústeres optimizados de cómputo en la nube. | Diseñar estructuras de almacenamiento híbrido Lakehouse que permitan lecturas de datos confiables en tiempo real bajo esquemas de consistencia ACID.', 'Databricks destaca en el observatorio con un salario mediano local de $15.000.000 COP y alta demanda por empresas financieras de primer nivel debido a la necesidad de mover datos a alta velocidad con costes controlados.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_03', 2, 'Orquestación de Pipelines & Cloud Integration', '1', 4, 64, 128, 192, '1. Flujos lógicos e interdependencia de procesos de datos.
2. Concepto de DAG (Directed Acyclic Graphs) y automatización.
3. Implementación de orquestadores industriales: Apache Airflow profundo.
4. Integración y despliegue continuo de DAGs en AWS y Azure.
5. Monitoreo automatizado, alarmas integradas y control de fallas en producción.
6. Gobierno, linaje y procedencia de datos en pipelines corporativos.', 'Semanas 13 a 24 (Primer Semestre)', 'Apache Airflow, AWS, Azure, GitHub Enterprise, Datadog', 'Diseñar flujos de procesamiento automatizados y orquestados secuencialmente que posean control de contingencias y alertas preventivas integradas ante caídas de servicio. | Garantizar la auditabilidad técnica del ciclo de vida del dato corporativo mediante metadatos y esquemas de linaje integrados en la nube.', 'La habilidad de orquestar flujos de datos (ETL / Pipelines) tiene un salario mediano registrado en el observatorio de $20.000.000 COP, siendo fundamental para coordinar equipos de datos grandes.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_03', 3, 'Infraestructura como Código, Docker & Kubernetes para Datos', '2', 4, 64, 128, 192, '1. Virtualización a nivel de sistema operativo y concepto de contenedores.
2. Creación y composición avanzada de redes locales y servicios multi-contenedor con Docker Compose.
3. Fundamentos de orquestación a escala con Kubernetes.
4. Despliegue de bases de datos y orquestadores en entornos clúster autocontrolados.
5. Infraestructura como Código (IaC) utilizando Terraform para aprovisionamiento automatizado.
6. Seguridad aplicada a redes de Big Data de alta disponibilidad.', 'Semanas 1 a 12 (Segundo Semestre)', 'Docker, Kubernetes, Terraform, Helm, YAML', 'Desplegar entornos de contenedores e infraestructura tecnológica repetible mediante código que permitan clonar clústeres de datos robustos en segundos. | Orquestar aplicaciones y servicios analíticos de alta disponibilidad garantizando la auto-recuperación y el auto-escalado horizontal continuo frente a sobrecargas.', 'Docker & Kubernetes lideran el ranking salarial absoluto del observatorio con un salario mediano de $66.666.666 COP, convirtiéndose en el diferenciador de élite definitivo en la industria de TI.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_03', 'Especialista de Infraestructuras Big Data y Spark', 'Procesamiento Distribuido a Gran Escala con Databricks & Spark', 'Ingeniero de Datos con posgrado en Big Data, maestría finalizada, con certificación oficial activa Databricks Certified Solutions Architect y experiencia de +6 años diseñando sistemas para multinacionales.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_03', 'Arquitecto Senior de Integraciones Cloud', 'Orquestación de Pipelines & Cloud Integration', 'Magíster en Ingeniería de Sistemas con sólida experiencia en orquestación de datos corporativos, con proyectos a escala en producción utilizando Apache Airflow y Kubernetes en los principales proveedores de nube.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_03', 'Especialista en DevOps e Infraestructura como Código (IaC)', 'Infraestructura como Código, Docker & Kubernetes para Datos', 'Ingeniero de Software especialista, certificado en Terraform y Kubernetes (CKA), con un mínimo de 5 años liderando departamentos de infraestructura ágil y automatizada en corporaciones de telecomunicaciones o banca.');
INSERT INTO dim_propuestas_curriculares_mig VALUES ('PROP_04', 'Maestría Aplicada', 'Maestría en Inteligencia Artificial y Ciencia de Datos Estratégica', 'Magíster en Inteligencia Artificial y Ciencia de Datos Estratégica', 'Posgrado / Maestría', '4 semestres', 48, 2304, 'Híbrida de alta flexibilidad', 'Jornada Nocturna y Concentrada en Fines de Semana (Híbrida)', 'Agosto de 2025', 'Junio de 2027', 'Apertura anual para cada segundo semestre académico', '$12.500.000 COP por semestre', '$10.000.000 COP por semestre (20% dcto egresados/docentes)', '$10.000.000 COP por semestre (20% dcto)', '$10.625.000 COP por semestre (15% dcto corporativo)', 'La cúspide del mercado laboral analítico global está dominada por vacantes de Científicos de Datos y Machine Learning Engineers (conjuntamente representan el 78.1% de la demanda en el observatorio). Mientras las ofertas de entrada locales pagan sumas intermedias, las posiciones de dirección técnica y diseño de arquitecturas complejas de Inteligencia Artificial superan con creces los salarios promedio remotos de $32M COP, con techos salariales de hasta $68M COP. Esta maestría aplicada de UniCafam cubre el espacio estratégico de liderazgo técnico e investigación corporativa. Ofrece una continuación natural a los egresados del Profesional en Ciencia de Datos, permitiéndoles profundizar en Deep Learning avanzado (PyTorch/TensorFlow), toma de decisiones estratégicas bajo enfoques causales y gobernanza ética de IA. UniCafam se consolidará como el hub de formación avanzada del más alto nivel, articulando la academia con el mercado remoto internacional de máxima remuneración.', 'Objetivo General: Formar líderes y tomadores de decisiones estratégicas que posean el más alto dominio tecnológico para diseñar, auditar e implementar soluciones complejas basadas en Inteligencia Artificial que generen valor económico exponencial y resuelvan problemas estructurales de las industrias.
Objetivo Específico 1: Diseñar arquitecturas de aprendizaje profundo complejas optimizadas para procesamiento de imagen, voz, secuencias temporales y agentes autónomos utilizando librerías avanzadas.
Objetivo Específico 2: Implementar enfoques de inferencia causal y modelado analítico avanzado para estructurar políticas de negocio basadas en atribución científica rigurosa.
Objetivo Específico 3: Establecer marcos éticos de gobernanza de la IA asegurando la privacidad, transparencia y explicabilidad algorítmica corporativa.', 'Profesionales y directores con perfiles en Ciencia de Datos, Ingeniería de Sistemas, Estadística, Matemáticas o profesionales con experiencia en analítica cuantitativa que deseen liderar la transformación mediante inteligencia artificial y acceder a roles directivos globales.', 'Seminarios avanzados de investigación aplicada combinados con laboratorios computacionales de alto rendimiento (GPU clusters). Los estudiantes formularán un Proyecto de Grado de Aplicación Industrial que debe resolver de manera efectiva un problema analítico de alta complejidad técnica y viabilidad de mercado dentro de una empresa real. La maestría promueve activamente el desarrollo de publicaciones científicas y patentes de algoritmos.', 'Uso de clústeres de supercómputo equipados con GPUs NVIDIA corporativas de alto rendimiento para el entrenamiento de modelos de Deep Learning complejos.
Networking corporativo de alto nivel: interacción continua con presidentes de empresas, gerentes de analítica e investigadores de todo el continente.
Homologación automática de créditos para egresados de la Especialización de UniCafam, reduciendo drásticamente la inversión y el tiempo de estudio de la maestría.', 'Magíster o Profesional en carreras afines a Ingeniería, Ciencias de la Computación, Matemáticas o Estadística, con una comprensión profunda del análisis matemático avanzado, álgebra lineal, modelos predictivos clásicos y dominio técnico de Python.', 'El egresado poseerá las capacidades para dirigir centros de excelencia de IA, proponer nuevos algoritmos de Deep Learning que optimicen dinámicamente operaciones complejas, realizar análisis de causalidad científica para la formulación de estrategias y formular arquitecturas éticas de cumplimiento normativo global.', 'Director / VP de Inteligencia Artificial y Ciencia de Datos (VP / Director of AI & Data), Ingeniero de Investigación en Aprendizaje Profundo (Deep Learning Research Engineer), Arquitecto de Machine Learning de Alta Especialidad (Principal Machine Learning Scientist)', 'Acceso asegurado a posiciones directivas corporativas y roles de consultor experto global (Salarios locales de liderazgo: $18.000.000 COP a $28.000.000 COP, mercado internacional remoto: >$40.000.000 COP)', 'https://jfbernalp.dev/downloads/mig/PROP_04_MIG.xlsx', 'PENDIENTE_REVISION', 1, '', '', '');
INSERT INTO historial_revisiones_curriculo (id_propuesta, version_resultante, usuario_aprobador, rol_usuario, decision, comentarios_feedback, cambios_aplicados_resumen, fecha_registro) VALUES ('PROP_04', 1, 'Sistema Observatorio IA UniCafam', 'Motor Generativo (Gemini 3.5 Flash)', 'CREACION_INICIAL', 'Generación curricular inicial groundeada en datos del mercado laboral y Decreto 1330 MEN.', 'Diseño base de microcurrículos, RAEs y perfil docente.', '2026-10-03 12:00:00');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_04', 1, 'Modelado Avanzado de Aprendizaje Profundo & Redes Neuronales', '1', 4, 64, 128, 192, '1. Introducción al entrenamiento por retropropagación y gradientes en redes profundas.
2. Arquitecturas de visión artificial complejas (CNNs y Redes Generativas Adversarias - GANs).
3. Redes recurrentes y procesamiento secuencial (LSTMs y GRUs).
4. Mecanismos de atención y Transformers profundos.
5. Modelos fundacionales e inferencia multimodal (Visión-Lenguaje).
6. Entrenamiento eficiente de redes a escala y ajuste fino (Fine-Tuning) utilizando PyTorch.', 'Semanas 1 a 12 (Primer Semestre)', 'PyTorch, TensorFlow, Keras, Hugging Face, Weights & Biases', 'Construir y optimizar redes neuronales profundas que incorporen mecanismos de auto-atención para procesar de forma automática datos de múltiples fuentes como visión de máquina y secuencias complejas. | Implementar procesos de fine-tuning avanzado en modelos fundacionales optimizando el consumo de cómputo GPU corporativo.', 'El modelado predictivo avanzado y las tecnologías de aprendizaje profundo como PyTorch y TensorFlow figuran en las brechas con mejores salarios en el observatorio, con promedios que rozan los $34.333.333 COP a nivel de especialista.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_04', 2, 'Inferencia Causal & Modelamiento Decisional para Negocios', '2', 4, 64, 128, 192, '1. Limitaciones de la correlación de datos convencional frente a la causalidad de eventos.
2. Teoría de Grafos Causal y el Cálculo Do (Pearl''s Causal Framework).
3. Métodos experimentales modernos y pruebas A/B de escala industrial.
4. Métodos cuasi-experimentales en ciencias de datos (Diff-in-Diff, RDD, Propensity Score Matching).
5. Modelado causal para atribución comercial y optimización de políticas de precios dinámicos.
6. Herramientas de estimación de efectos causales con Python.', 'Semanas 1 a 12 (Segundo Semestre)', 'DoWhy, CausalML, EconML, Statsmodels', 'Sustentar científicamente políticas de negocio de alto impacto distinguiendo los efectos reales directos de simples asociaciones accidentales de datos históricos. | Modelar y diseñar experimentos A/B que calculen efectos promedio de tratamiento de forma óptima bajo presencia de variables de confusión.', 'La inferencia estadística aplicada constituye el núcleo del científico de datos (rol más demandado con 45.6% de menciones), representando el salto intelectual de un analista descriptivo tradicional hacia un formulador de estrategias complejas de negocio.');
INSERT INTO fact_modulos_propuestas_mig (id_propuesta, numero_modulo, nombre_modulo, semestre_sugerido, creditos, horas_tfd, horas_tti, horas_totales_modulo, contenido_detallado, cronograma_fechas, stack_tecnologico, raes, justificacion_mercado) VALUES ('PROP_04', 3, 'Gobernanza de Datos, Ética en IA & Algoritmos Explicables (XAI)', '3', 4, 64, 128, 192, '1. Sesgo algorítmico, equidad informática (Algorithmic Fairness) y discriminación por IA.
2. Métodos de interpretación y explicación de modelos complejos de caja negra (SHAP, LIME).
3. Cumplimiento normativo e internacional de privacidad de datos (GDPR, Ley de Inteligencia Artificial de la UE y normativas locales del MEN).
4. Gobierno de datos y aseguramiento de la robustez frente a ataques adversarios de modelos.
5. Marcos de auditoría ética y responsabilidad corporativa algorítmica.', 'Semanas 1 a 12 (Tercer Semestre)', 'SHAP, LIME, Fairlearn, Alibi, InterpretML', 'Interpretar cuantitativamente el proceso de decisión lógica interna de cualquier clasificador o estimador predictivo de caja negra garantizando la confianza total del usuario final. | Garantizar el pleno cumplimiento de normativas de transparencia y equidad estructural en algoritmos analíticos aplicados en sectores sensibles de la sociedad.', 'Las organizaciones internacionales más prestigiosas exigen marcos de gobernanza y transparencia técnica como requisito ineludible de contratación, permitiendo el despliegue comercial seguro y protegiendo el prestigio corporativo.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_04', 'Científico de Datos Senior con Doctorado en Ciencias de la Computación / Deep Learning', 'Modelado Avanzado de Aprendizaje Profundo & Redes Neuronales', 'Ph.D. en Computación o IA con amplias publicaciones científicas indexadas Q1 o Q2 en aprendizaje automático, con amplia experiencia de modelado complejo con frameworks de cómputo en la nube a gran escala.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_04', 'Especialista en Inferencia Causal y Econometría Analítica', 'Inferencia Causal & Modelamiento Decisional para Negocios', 'Doctor en Economía Cuantitativa o Estadística Aplicada, con vasta trayectoria laboral en diseño de experimentos de alta precisión de comportamiento de consumo e inferencia para industrias digitales de primer nivel.');
INSERT INTO dim_docentes_propuestas_mig (id_propuesta, nombre_o_rol, modulo_asignado, perfil_experto) VALUES ('PROP_04', 'Experto en Regulación de Datos y XAI (Explainable AI)', 'Gobernanza de Datos, Ética en IA & Algoritmos Explicables (XAI)', 'Ph.D. o Magíster en Ética Aplicada, Derecho de TI o Ciencia de Datos, que haya liderado procesos de auditoría del comportamiento ético de algoritmos de decisión de otorgamiento de crédito o contratación en entidades de la Unión Europea o América Latina.');

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