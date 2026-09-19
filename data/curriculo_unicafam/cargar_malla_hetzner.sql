-- ==================================================================
-- PERSISTENCIA PRIVADA DE MALLA CURRICULAR UNICAFAM EN HETZNER
-- ==================================================================

-- 1. Tabla Dimensión Malla Curricular
DROP VIEW IF EXISTS vista_cobertura_curricular CASCADE;
DROP TABLE IF EXISTS fact_habilidades_academicas CASCADE;
DROP TABLE IF EXISTS fact_saberes_academicos CASCADE;
DROP TABLE IF EXISTS dim_malla_curricular CASCADE;

CREATE TABLE dim_malla_curricular (
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
);

-- 2. Tabla de Habilidades y Competencias Tecnológicas Enseñadas
CREATE TABLE fact_habilidades_academicas (
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
);

-- 3. Tabla de Saberes Específicos Detallados
CREATE TABLE fact_saberes_academicos (
    id_saber SERIAL PRIMARY KEY,
    programa_academico VARCHAR(200) NOT NULL,
    codigo_materia VARCHAR(64) REFERENCES dim_malla_curricular(codigo_materia),
    orden_tema INTEGER,
    saber_especifico TEXT
);

-- INSERCIONES: dim_malla_curricular
INSERT INTO dim_malla_curricular VALUES ('14029050101', 'Tecnología en Análisis y Gestión de Datos', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 48, 96, 144, 'Presencial', 'Específica', 'Gestionar datos para proveer la información requerida por los diferentes grupos de interés de la organización.', 'Los Fundamentos de Big Data son esenciales para que un Tecnólogo en Gestión y Análisis de Datos pueda abordar los desafíos asociados con la gestión, procesamiento y análisis de grandes cantidades de datos, lo que se traduce en habilidades valiosas en un entorno empresarial cada vez más orientado a datos.', '1_Fundamentos_de_Big_Data_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029030101', 'Tecnología en Análisis y Gestión de Datos', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 32, 64, 96, 'Presencial', 'Específica', 'Proponer nuevos usos de los datos que provean información útil que agregue valor.', 'Este curso introductorio a la ciencia de datos le permitirá al estudiante identificar los conceptos esenciales del quehacer de un científico de datos, así como articular estos conceptos con otras unidades de aprendizaje, que serán fundamentales en su formación.', '1_Introduccion a la ciencia de datos_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029020101', 'Tecnología en Análisis y Gestión de Datos', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 48, 96, 144, 'PAT', 'Básica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'La estadística es importante en la tecnología en análisis y gestión de datos porque proporciona las bases necesarias para comprender, limpiar, visualizar y evaluar datos de manera efectiva. Facilita la toma de decisiones informadas, la optimización de procesos y la innovación a través de la interpretación adecuada de datos y la extracción de insights significativos para las organizaciones.', '1_Introduccion_A_la_Estadistica_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029060101', 'Tecnología en Análisis y Gestión de Datos', 'PARTICIPACIÓN SOCIAL', 1, 'Primer Semestre', 2, 32, 64, 96, 'PRESENCIAL', 'Transversal', 'COMPETENCIA', 'El enfoque de la unidad se centra en la responsabilidad social universitaria (RSU) caracterizado en palabras de (De la Calle, García, & Gimenez, 2007) por actividades en las cuales los estudiantes adquieren la capacidad de compromiso, de escucha, diálogo, son capaces de tomar distancia de los problemas, aprenden a mirar a través de los ojos del otro, a ponerse en su lugar, con un pensamiento crítico, desarrollando el sentido auténtico del servicio y de la solidaridad. Dicho enfoque está en consonancia y fundamentado en lo planteado en el artículo 9 del decreto 1038 de 2015 por el cual se reglamenta la cátedra de paz.

En esta línea y con el propósito de enmarcar el enfoque conceptual de la cátedra y las acciones que se desarrollan en los diversos proyectos de responsabilidad social universitaria, se relacionarán y se definirán con el propósito de sustentar el trabajo: 

a) Cultura de la paz: la cual se entiende como el sentido y vivencia de los valores ciudadanos, los derechos humanos, el Derecho Internacional Humanitario, la participación democrática, la prevención de la violencia y la resolución pacífica de los conflictos
 b) Educación para la paz: se entiende como la apropiación de conocimientos y competencias ciudadanas para la convivencia pacífica, la participación democrática, la construcción de equidad, el respeto por la pluralidad, los derechos humanos y el Derecho Internacional Humanitario
 c) Desarrollo sostenible: se entiende como aquel que conduce al crecimiento económico, la elevación de la calidad de la vida y al bienestar social, sin agotar la base de recursos naturales renovables en que se sustenta, 

Lo que se busca con este proceso con los estudiantes es lograr que se genere una experiencia de gana-gana que permita a los estudiantes el fortalecimiento de sus competencias comunicativas y profesionales, acudiendo a un proceso de transferencia de saberes disciplinares y de experiencia de vida.', '1_Participacion_Social_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029010101', 'Tecnología en Análisis y Gestión de Datos', 'FUNDAMENTOS DE MATEMATICAS', 1, 'Primer Semestre', 3, 32, 64, 96, 'Presencial', 'Básica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'Las matemáticas son la base teórica de muchas disciplinas, incluyendo el análisis de datos. Comprender los fundamentos matemáticos le proporcionará al Tecnólogo en Análisis y gestión de Datos una base sólida para entender y aplicar conceptos más avanzados en estadísticas, algoritmos y modelos de datos.', '1_TAGD_Fundamentos de Matemáticas_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029070101', 'Tecnología en Análisis y Gestión de Datos', 'HABILIDADES PARA APRENDER', 1, 'Primer Semestre', 2, 32, 64, 96, 'Presencial', 'Transversal', 'Proponer una solución a una problemática, interés o necesidad de un grupo humano u organización con enfoque social y/o socio-empresarial que articule tanto el saber disciplinar como la experiencia de vida y el compromiso personal con la investigación formativa, la cultura de paz y convivencia y el principio institucional de la responsabilidad social universitaria.', 'El lenguaje como instrumento para comunicar ideas y argumentos sobre diferentes campos del conocimiento humano, es la base a partir de la cual los tecnólogos en análisis y gestión de datos fortalecen sus conocimientos gramaticales, sus habilidades de análisis e interpretación crítica de textos y la capacidad para elaborar documentos claros que expongan, sustenten y comuniquen de manera eficiente la información necesaria para la toma exitosa de decisiones. Con este propósito, el objetivo de esta Unidad de Aprendizaje es brindar herramientas necesarias y suficientes para que los futuros profesionales logren hacer uso del lenguaje de manera oral y escrita, aplicando las normas y diferenciando la intención comunicativa de los documentos sugeridos.', '1_TAGD_Habilidades_para_Apreder_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029040101', 'Tecnología en Análisis y Gestión de Datos', 'TEORÍA GENERAL DE SISTEMAS', 1, 'Primer Semestre', 3, 32, 64, 96, 'Presencial', 'Específica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'La Teoría General de Sistemas proporciona al tecnólogo en análisis y gestión de datos la capacidad de comprender y analizar la realidad a partir de principios y paradigmas fundamentados en la multidisciplinariedad. Esta perspectiva no solo amplía el panorama más allá de la ciencia clásica, sino que también consolida el pensamiento sistémico como una convergencia teórica, conceptual y procedimental que abarca diversos campos del conocimiento bajo la noción unificadora de sistemas.', '1_TAGD_Teoria_General_de_Sistemas.xlsx');
INSERT INTO dim_malla_curricular VALUES ('142001130301', 'Tecnología en Análisis y Gestión de Datos', 'ALGORÍTMOS', 1, 'Primer Semestre', 3, 48, 96, 144, 'PAT', 'Específica', 'Gestionar datos para proveer la información requerida por los diferentes grupos de interés de la organización.', 'Es indispensable para cualquier profesional actual, poseer las capacidades y habilidades mínimas necesarias para la resolución de problemas, por medio del uso de herramientas metodológicas estructuradas y conceptos básicos de programación.', '2_Algorítmos_V2 .xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029100201', 'Tecnología en Análisis y Gestión de Datos', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 32, 64, 96, 'Presencial', 'Espécifica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'Los entornos empresariales actuales requieren constantemente inspeccionar, limpiar, depurar y trasformas los datos con el objetivo de encontrar información útil que les permita realizar análisis y poder concluir sobre aspectos determinados de los objetivos del negocio y tomar decisiones.', '2_Introducción _a_la_analitica de datos_V2 (2).xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029090201', 'Tecnología en Análisis y Gestión de Datos', 'ALGEBRA LINEAL', 2, 'Segundo Semestre', 3, 32, 64, 96, 'Presencial', 'Básica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'El algebra lineal le permite al estudiante ordenar información por medio de matrices y vectores, así como generalizar , plantear modelar, argumentar y resolver situaciones problémicas propios de la ingeniería. 
Las competencias adquiridas durante y como consecuencia del desarrollo de esta unidad de aprendizaje, sirven como base para potenciar la apropiación de conocimientos, y la adquisición de competencias específicas propias de las unidades académicas del área de formación.', '2_TAGD_Algebra_Lineal_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14025080202', 'Tecnología en Análisis y Gestión de Datos', 'CALCULO DIFERENCIAL', 2, 'Segundo Semestre', 3, 32, 64, 96, 'Presencial', 'Básica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'El cálculo diferencial proporciona a los tecnólogos en Análisis y Gestión de Datos, los fundamentos teóricos y prácticos que le permiten el modelamiento de diversas situaciones reales a partir del análisis de funciones.
Las competencias adquiridas durante y como consecuencia del desarrollo de esta unidad de aprendizaje, sirven como base para potenciar la apropiación de conocimientos, y la adquisición de competencias específicas propias de las unidades académicas del área de formación.', '2_TAGD_Calculo_Diferencial_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14025140202', 'Tecnología en Análisis y Gestión de Datos', 'EMPRENDIMIENTO', 2, 'Segundo Semestre', 2, 32, 64, 96, 'Presencial', 'Transversal', 'Plantea planes de negocio a partir de la identificación de problemas, necesidades o deseos no satisfechos de un segmento de la población, proponiendo soluciones creativas, innovadoras y competitivas evaluadas por medio de análisis de mercado, técnico y financiero para determinar su factibilidad', 'Según Wallace, 1926; Poincaré, 1952; Vinache, 1952, el proceso creativo se ha establecido comprendiendo cuatro fases: preparación, incubación, iluminación y verificación. Por otro lado los laboratorios creativos, son espacios de sensibilización, investigación, experimentación, creación y lanzamiento de nuevas ideas que se generan a partir de las capacidades creativas de las personas que los constituyen. Quiere decir, que al abrir espacios de co-creación, se está fomentando la creatividad, la innovación y la solución a distintos temas, fruto de los procesos de interacción entre estudiantes, docentes y empresas o sociedad en general y sus realidades. Las soluciones propuestas, que surgen fruto del proceso creativo, pueden ser: una idea de negocio, modelos de negocio, o iniciativas sociales o ambientales dirigidas a distintos tipos de población (población vulnerable, empresas, entre otras).', '2_TAGD_Emprendimiento_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029130201', 'Tecnología en Análisis y Gestión de Datos', 'Electiva I - Fundamentos de Python I', 2, 'Segundo Semestre', 2, 32, 64, 96, 'Presencial', 'Específica', 'Implementar soluciones a problemas logísticos, de operación y gestión organizacionales por medio de herramientas tecnológicas y el análisis de datos, aportando a la sostenibilidad y desarrollo organizacional.', 'En el contexto actual de transformación digital y la creciente importancia de la analítica de datos en los entornos industriales, la implementación de la unidad de aprendizaje "LINEA ELECTIVA DE ENFASIS II - FUNDAMENTOS DE PYTHON I"  representa una oportunidad estratégica para fortalecer el perfil del Ingeniero Industrial de la Fundación Universitaria Cafam, La programación en Python se ha convertido en una herramienta fundamental para el análisis, modelamiento y optimización de procesos industriales. respondiendo a las necesidades actuales del sector industrial y preparando a los estudiantes para liderar procesos de transformación digital y mejoramiento continuo en diversos contextos organizacionales.

El contenido estructurado del programa, que abarca desde los fundamentos básicos hasta la aplicación práctica en un proyecto integrador y la preparación para una certificación internacional, garantiza que los estudiantes adquieran competencias relevantes y aplicables en su futuro desempeño profesional.

Esta formación complementaria en programación no solo enriquece el perfil técnico del ingeniero, sino que amplía su capacidad de contribuir al desarrollo económico de la ciudad y del país mediante la implementación de soluciones innovadoras basadas en datos y tecnología. Al ofrecer un lenguaje de programación ampliamente adoptado por la industria, accesible para principiantes y con alta demanda en el mercado laboral, esta electiva representa una inversión estratégica en la formación integral del ingeniero industrial del siglo XXI.', '2_TAGD__Electiva I( Fundamentos de Python I)_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029170301', 'Tecnología en Análisis y Gestión de Datos', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 48, 96, 144, 'PAT', 'Específica', 'Gestionar datos para proveer la información requerida por los diferentes grupos de interés de la organización.', 'En esta Unidad de Aprendizaje se establecen las bases de la aplicación del paradigma orientado a objetos y se le brindan al estudiante las herramientas para la aplicación de los principios y características de este paradigma para fortalecer en el estudiante las habilidades en el desarrollo de programas computacionales. Estas habilidades se reconocen como claves dentro del dominio del perfil de “Programación”.', '3_Algoritmos II.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029180301', 'Tecnología en Análisis y Gestión de Datos', 'DISEÑO DE BASE DE DATOS', 3, 'Tercer Semestre', 2, 32, 64, 96, 'Presencial', 'Específica', 'Garantizar la calidad en la cadena de los datos durante su ciclo de vida para contar con información veraz, válida e integra.', 'En la actualidad los datos y su ordenamiento en bases de datos son aspectos fundamentales en el proceso de generación de información. El diseño de bases de datos es esencial para precisar las dimensiones, propiedades y límites que permite determinar el procesamiento idóneo de la información.', '3_Diseño de base de datos_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029150301', 'Tecnología en Análisis y Gestión de Datos', 'ANÁLITICA DESCRIPTIVA I', 3, 'Tercer Semestre', 3, 32, 64, 96, 'Presencial', 'Básica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'En ciencia de datos, muchas variables pueden modelarse usando distribuciones de probabilidades para representar la incertidumbre y la variabilidad en datos observados. Las distribuciones proporcionan un marco matemático para entender cómo se distribuyen los datos y cómo pueden comportarse en diferentes contextos.', '3_TAGD_Analitica_Descriptiva_I_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029140301', 'Tecnología en Análisis y Gestión de Datos', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 32, 64, 96, 'Presencial', 'Básica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'El cálculo integral  le permite al tecnologo resolver  situaciones problémicas relacionadas con las ciencias exactas, naturales y administrativas, a través de las integrales definidas e indefinidas.
Las competencias adquiridas durante y como consecuencia del desarrollo de esta unidad de aprendizaje, sirven como base para potenciar la apropiación de conocimientos, y la adquisición de competencias específicas propias de las unidades académicas del área de formación.', '3_TAGD_Calculo Integral.2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029160301', 'Tecnología en Análisis y Gestión de Datos', 'INVESTIGACIÓN DE OPERACIONES', 3, 'Tercer Semestre', 3, 32, 64, 96, 'Presencial', 'Específica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'La unidad de aprendizaje,  busca generar las competencias necesarias para que los estudiantes construyan modelos matemáticos de Programación Lineal, estadística y algoritmos con el fin de que proponga acciones, para mejorar y optimizar los modelos de inventarios, producción y  transporte en las organizaciones.', '3_TAGD_Investigacion_de_Operaciones_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029190301', 'Tecnología en Análisis y Gestión de Datos', 'SEMINARIO DE INVESTIGACIÓN I', 3, 'Tercer Semestre', 2, 32, 64, 96, 'Presencial', 'Transversal', 'Elaborar una propuesta de investigación  que aborde un problema pertinente, viable y ético, aplicado a la sociedad, las empresas o los servicios, que esté relacionado con el programa de estudio o con una de las línea de investigación de la institución.', 'La investigación en el programa pretende articular las competencias investigativas en la construcción y aplicación del conocimiento con el fin de generar soluciones a problemas relacionados con el  hombre, la sociedad y las empresas. Se busca con ello integrar la importancia de los contenidos del programa con el desarrollo de los procesos de investigación formativa. En ese sentido, el programa garantizará la investigación formativa y el alcance de las competencias investigativas de los estudiantes, tal como establece la política de investigación, abordando la oportunidades que ofrece la unidad de aprendizaje de métodología de la investigación.', '3_TAGD_Seminario de Investigación_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('142001130504', 'Tecnología en Análisis y Gestión de Datos', 'GESTION DE PROYECTOS', 4, 'Cuarto Semestre', 2, 32, 64, 96, 'PAT', 'Específica', 'Garantizar la calidad de la cadena del dato para asegurar su confiabilidad e integridad.', 'La gestión de proyectos es una herramienta que permite planear, organizar y coordinar, personas, recursos e insumos utilizados para el cumplimiento de objetivos y establecer los mejores estándares de calidad de los proyectos. Esta acción involucra una mayor capacidad de análisis y toma de decisiones de las actividades descritas en el proyecto entorno de: el tiempo, presupuesto y alcance.', '4_Gestion_de_Proyectos V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029220401', 'Tecnología en Análisis y Gestión de Datos', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 48, 96, 144, 'Presencial', 'Específica', 'Proponer nuevos usos de los datos que provean información útil que agregue valor.', 'La minería de datos es un método de análisis de datos para descubrir patrones en grandes conjuntos de datos utilizando los métodos de estadísticas, inteligencia artificial, aprendizaje automático y bases de datos. Además busca los patrones ocultos en los datos que pueden utilizarse para predecir el comportamiento futuro. Las empresas, los científicos y los gobiernos han utilizado este enfoque por años para transformar los datos en conocimientos proactivos.', '4_Mineria de Datos_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029230401', 'Tecnología en Análisis y Gestión de Datos', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 48, 96, 144, 'Presencial', 'Específica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'Cuando queremos estudiar un proceso, lo más seguro es que no conozcamos el modelo teórico de la misma base de datos.  los modelos analíticos son la base de todo sistema de inteligencia artificial y por lo tanto cuánto más preciso sea el modelo analítico, las predicciones y optimizaciones serán más óptimas y las decisiones basadas en estas serán mejores generando un mayor valor para la organización.', '4_Modelos_Análíticos_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029200401', 'Tecnología en Análisis y Gestión de Datos', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 48, 96, 144, 'Presencial', 'Específica', 'Garantizar la calidad de la cadena del dato para asegurar su confiabilidad e integridad.', 'La UA Seguridad de la Información no solo es relevante sino esencial en un programa de Ingeniería de Telecomunicaciones por que le proporcionará a los estudiantes las herramientas y conocimientos necesarios para enfrentar y mitigar los riesgos de seguridad en un mundo cada vez más digital y conectado y que adicionalmente, debe ser preventivo y resiliente frente a las diversas amenazas que se pueden generar en los sistemas de telecomunicaciones producto de las vulnerabilidades que se pueden presentar en los activo de red vitales para el tratamiento de la información.', '4_Seguridad de la Informacion_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029210401', 'Tecnología en Análisis y Gestión de Datos', 'ANALÍTICA DESCRÍPTIVA II', 4, 'Cuarto Semestre', 3, 32, 64, 96, 'Presencial', 'Específica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'Hay una diversidad de problemas que son modelados y resueltos a través de modelos probabilísticos ya establecidos, por lo que resulta importante que el científico de datos domine el cálculo de analíticas descriptivas, en particular técnicas de inferencia. Esta unidad de aprendizaje contribuye a desarrollar un pensamiento lógico y algorítmico al modelar fenómenos aleatorios resolviendo problemas en los que interviene la incertidumbre y al mismo tiempo hacer inferencias sobre estos, para la toma de decisiones.', '4_TAGD_Analítica_Descriptiva_II.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029240401', 'Tecnología en Análisis y Gestión de Datos', 'BASES DE DATOS NoSQL', 4, 'Cuarto Semestre', 2, 32, 64, 96, 'Presencial', 'Específica', 'Garantizar la calidad de la cadena del dato para asegurar su confiabilidad e integridad.', 'Explorar bases de datos NoSQL proporciona una estrategia más flexible y escalable para gestionar datos en situaciones donde las bases de datos relacionales pueden no ser la solución más adecuada. La elección entre bases de datos SQL y NoSQL dependerá de los requisitos específicos del proyecto y de las características inherentes de los datos que se deben gestionar.', '4_TAGD_Base_de_Datos_NoSQL_V2_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029010101', 'Tecnología en Análisis y Gestión de Datos', 'Electiva II (Fundamentos Estratégicos de Gobierno de Datos)', 4, 'Cuarto Semestre', 2, 32, 64, 96, 'Presencial', 'Fundamentación', 'Gestionar datos para proveer la información requerida por los diferentes grupos de interés de la organización.', 'Gobierno de Datos es el ejercicio de la autoridad y el control (planificación, el seguimiento y la aplicación) a través de la gestión de los activos de datos. La función de Gobierno de Datos guía de cómo se llevan acabo todas las demás funciones de gestión de datos.', '4_TAGD_Electiva_II_Introduccion_al_gobierno de datos_2025_2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029270501', 'Tecnología en Análisis y Gestión de Datos', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 48, 96, 144, 'PAT', 'Específica', 'Procesar datos que permitan identificar patrones y generar hipótesis sobre la relación entre estos.', 'La analítica predictiva le permite a los tecnologos en datos pronosticar comportamientos futuros a partir del análisis de datos históricos y en tiempo real. Esta disciplina facilita la identificación de patrones, la predicción de demandas, la prevencion de fallos y la optimizar procesos en diversos contextos organizacionales. Su aplicación permite validar modelos predictivos, incrementando su precisión y adaptabilidad frente a entornos cambiantes.  Esto garantiza la contruccion de modelos robustos, confiables, escalables y actualizables, lo que convierte a la analítica predictiva en un pilar esencial para la toma de decisiones estratégicas en el ámbito de la ciencia de datos.', '5_Análitica Predictiva_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029280501', 'Tecnología en Análisis y Gestión de Datos', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 32, 64, 96, 'PAT', 'Específico', 'Gestionar datos para proveer la información requerida por los diferentes grupos de interés de la organización.', 'Las herramientas para el análisis de datos son fundamentales en la formación del profesional en ciencia de datos, ya que les brindan los conocimientos y competencias necesarias para transformar grandes volúmenes de datos en información significativa y útil para la toma de decisiones. Mediante el dominio de herramientas especializadas, el estudiante podrá abordar de manera sistemática el ciclo completo del análisis de datos: desde la recolección, limpieza y transformación, hasta la exploración, modelado básico y visualización.  Estas herramientas no solo optimizan los procesos técnicos, sino que también fortalecen la capacidad de generar insights accionables y estratégicos que aporten valor a las organizaciones.', '5_Herramientas para el Analisis_de _datos_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029300501', 'Tecnología en Análisis y Gestión de Datos', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 32, 64, 96, 'PRESENCIAL', 'Específica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'El procesamiento de texto y las técnicas de información son fundamentales para que el estudiante desarrolle metodologías que le permitan transformar información textual en datos estructurados, analizables y relevantes para la toma de decisiones. Mediante el uso de técnicas de procesamiento de lenguaje natural (PLN), representaciones vectoriales, análisis de patrones y métodos básicos de búsqueda, el estudiante podrá extraer conocimiento útil a partir de fuentes textuales como encuestas, redes sociales, comentarios de clientes, artículos y documentos. Esta asignatura le brinda la capacidad de integrar soluciones analíticas en contextos reales, mediante el uso de herramientas computacionales y la automatización de flujos de procesamiento textual', '5_Procesamiento de Texto y Tecnicas de Informacion.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029320501', 'Tecnología en Análisis y Gestión de Datos', 'PROYECTO INTEGRADOR I', 5, 'Quinto Semestre', 3, 48, 96, 144, 'PAT', 'Transversal', 'Proponer nuevos usos de los datos que provean información útil que agregue valor', 'La articulación de las diferentes competencias adquiridas en el desarrollo del programa, para la recopilación, sistematización y análisis de la información en pro de la solución de un problema, necesidad industrial o la respuesta a una pregunta, es una competencia fundamental en el desempeño del Ingeniero.', '5_Proyecto Integrador_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029310501', 'Tecnología en Análisis y Gestión de Datos', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 64, 128, 192, 'Presencial', 'Transversal', 'Proponer una solución a una problemática, interés o necesidad de un grupo humano u organización con enfoque social y/o socio-empresarial que articule tanto el saber disciplinar como la experiencia de vida y el compromiso personal con la investigación formativa, la cultura de paz y convivencia y el principio institucional de la responsabilidad social universitaria.', 'Las prácticas profesionales son una unidad de aprendizaje, que desarrolla desde la práctica, el desempeño laboral del futuro profesional. Durante la misma, el estudiante debe diseñar y desarrollar diversas actividades aprendidas en las diferentes unidades de aprendizaje y que estarán bajo la supervisión y guía de la empresa que tenga este convenio con la universidad. En esta unidad se hacen evidentes las capacidades desarrolladas durante el proceso formativo.', '5_Práctica Profesional_V2.xlsx');
INSERT INTO dim_malla_curricular VALUES ('14029290501', 'Tecnología en Análisis y Gestión de Datos', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 32, 64, 96, 'Presencial', 'Específica', 'Apoyar la toma de decisiones mediante el uso y análisis de la información.', 'En todos los niveles de una organización (estratégico, táctico u operativo), los líderes se enfrentan diariamente a problemas que impactan la eficiencia y efectividad de la empresa. Abordar estas situaciones de manera proactiva requiere identificar las causas que generan los desafíos organizacionales. La toma de decisiones en este contexto es una función crítica, ejercida por personas con conocimientos especializados y la capacidad de evaluar alternativas con un alto grado de asertividad. Existen diversos modelos de toma de decisiones, cada uno con enfoques y criterios distintos, cuya aplicabilidad depende de las características específicas del problema a resolver. Comprender estos modelos y su adecuada implementación permite a las organizaciones mejorar sus procesos, optimizar recursos y responder a los cambios del entorno', '5_Toma de decisiones Organizacio_V2.xlsx');

-- INSERCIONES: fact_habilidades_academicas
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Bases de Datos NoSQL', 'mongodb', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Procesamiento de Lenguaje Natural (NLP)', 'text mining', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Analítica Descriptiva & Visualización', 'visualización', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 'FUNDAMENTOS DE BIG DATA', 1, 'Primer Semestre', 3, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 'Analítica Predictiva & Machine Learning', 'machine learning', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 'Gobierno de Datos & Calidad', 'gobierno de datos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 'INTRODUCCIÓN A LA CIENCIA DE DATOS', 1, 'Primer Semestre', 2, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Minería de Datos & KDD', 'patrones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'R / Estadística Computacional', 'r', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Estadística & Probabilidad', 'estadistica', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Investigación de Operaciones & Optimización', 'optimización', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 'INTRODUCCION A LA ESTADISTICA', 1, 'Primer Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 'PARTICIPACIÓN SOCIAL', 1, 'Primer Semestre', 2, 'Analítica Descriptiva & Visualización', 'power bi', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 'PARTICIPACIÓN SOCIAL', 1, 'Primer Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 'PARTICIPACIÓN SOCIAL', 1, 'Primer Semestre', 2, 'R / Estadística Computacional', 'r', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'FUNDAMENTOS DE MATEMATICAS', 1, 'Primer Semestre', 3, 'Minería de Datos & KDD', 'patrones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'FUNDAMENTOS DE MATEMATICAS', 1, 'Primer Semestre', 3, 'R / Estadística Computacional', 'r', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'FUNDAMENTOS DE MATEMATICAS', 1, 'Primer Semestre', 3, 'Estadística & Probabilidad', 'hipótesis', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'FUNDAMENTOS DE MATEMATICAS', 1, 'Primer Semestre', 3, 'Algoritmos & Lógica de Programación', 'algoritmos', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029070101', 'HABILIDADES PARA APRENDER', 1, 'Primer Semestre', 2, 'Bases de Datos NoSQL', 'documentos', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029040101', 'TEORÍA GENERAL DE SISTEMAS', 1, 'Primer Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130301', 'ALGORÍTMOS', 1, 'Primer Semestre', 3, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130301', 'ALGORÍTMOS', 1, 'Primer Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130301', 'ALGORÍTMOS', 1, 'Primer Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130301', 'ALGORÍTMOS', 1, 'Primer Semestre', 3, 'Algoritmos & Lógica de Programación', 'algorítmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Python', 'python', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Minería de Datos & KDD', 'minería de datos', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Analítica Descriptiva & Visualización', 'power bi', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'R / Estadística Computacional', 'r', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 'INTRODUCCIÓN A LA ANALÍTICA DE LOS DATOS', 2, 'Segundo Semestre', 2, 'Estadística & Probabilidad', 'estadística', 'Espécifica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029090201', 'ALGEBRA LINEAL', 2, 'Segundo Semestre', 3, 'Matemáticas Aplicadas & Álgebra Lineal', 'algebra lineal', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029090201', 'ALGEBRA LINEAL', 2, 'Segundo Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14025080202', 'CALCULO DIFERENCIAL', 2, 'Segundo Semestre', 3, 'Investigación de Operaciones & Optimización', 'optimización', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14025080202', 'CALCULO DIFERENCIAL', 2, 'Segundo Semestre', 3, 'Matemáticas Aplicadas & Álgebra Lineal', 'calculo diferencial', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14025080202', 'CALCULO DIFERENCIAL', 2, 'Segundo Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029130201', 'Electiva I - Fundamentos de Python I', 2, 'Segundo Semestre', 2, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029130201', 'Electiva I - Fundamentos de Python I', 2, 'Segundo Semestre', 2, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029130201', 'Electiva I - Fundamentos de Python I', 2, 'Segundo Semestre', 2, 'Investigación de Operaciones & Optimización', 'optimización', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029130201', 'Electiva I - Fundamentos de Python I', 2, 'Segundo Semestre', 2, 'Algoritmos & Lógica de Programación', 'algoritmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'Algoritmos & Lógica de Programación', 'algorítmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 'ALGORÍTMOS II', 3, 'Tercer Semestre', 3, 'Matemáticas Aplicadas & Álgebra Lineal', 'matrices', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029180301', 'DISEÑO DE BASE DE DATOS', 3, 'Tercer Semestre', 2, 'SQL / Bases de Datos Relacionales', 'sql', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029180301', 'DISEÑO DE BASE DE DATOS', 3, 'Tercer Semestre', 2, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029180301', 'DISEÑO DE BASE DE DATOS', 3, 'Tercer Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029180301', 'DISEÑO DE BASE DE DATOS', 3, 'Tercer Semestre', 2, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029150301', 'ANÁLITICA DESCRIPTIVA I', 3, 'Tercer Semestre', 3, 'Minería de Datos & KDD', 'patrones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029150301', 'ANÁLITICA DESCRIPTIVA I', 3, 'Tercer Semestre', 3, 'Estadística & Probabilidad', 'estadística', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 'R / Estadística Computacional', 'r', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 'Matemáticas Aplicadas & Álgebra Lineal', 'calculo integral', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 'CALCULO INTEGRAL', 3, 'Tercer Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Básica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029160301', 'INVESTIGACIÓN DE OPERACIONES', 3, 'Tercer Semestre', 3, 'Estadística & Probabilidad', 'estadística', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029160301', 'INVESTIGACIÓN DE OPERACIONES', 3, 'Tercer Semestre', 3, 'Investigación de Operaciones & Optimización', 'investigación de operaciones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029160301', 'INVESTIGACIÓN DE OPERACIONES', 3, 'Tercer Semestre', 3, 'Algoritmos & Lógica de Programación', 'algoritmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029160301', 'INVESTIGACIÓN DE OPERACIONES', 3, 'Tercer Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029190301', 'SEMINARIO DE INVESTIGACIÓN I', 3, 'Tercer Semestre', 2, 'R / Estadística Computacional', 'r', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029190301', 'SEMINARIO DE INVESTIGACIÓN I', 3, 'Tercer Semestre', 2, 'Estadística & Probabilidad', 'hipótesis', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130504', 'GESTION DE PROYECTOS', 4, 'Cuarto Semestre', 2, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130504', 'GESTION DE PROYECTOS', 4, 'Cuarto Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130504', 'GESTION DE PROYECTOS', 4, 'Cuarto Semestre', 2, 'Gestión de Proyectos & Metodologías Ágiles', 'gestion de proyectos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130504', 'GESTION DE PROYECTOS', 4, 'Cuarto Semestre', 2, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Minería de Datos & KDD', 'minería de datos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Analítica Predictiva & Machine Learning', 'aprendizaje automático', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Procesamiento de Lenguaje Natural (NLP)', 'text mining', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Algoritmos & Lógica de Programación', 'algoritmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 'MINERÍA DE DATOS', 4, 'Cuarto Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Minería de Datos & KDD', 'patrones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Analítica Predictiva & Machine Learning', 'regresión', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Procesamiento de Lenguaje Natural (NLP)', 'text mining', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 'MODELOS ANALÍTICOS', 4, 'Cuarto Semestre', 3, 'Estadística & Probabilidad', 'hipótesis', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 'Seguridad de la Información & Ciberseguridad', 'seguridad de la información', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 'SEGURIDAD DE LA INFORMACIÓN', 4, 'Cuarto Semestre', 3, 'Matemáticas Aplicadas & Álgebra Lineal', 'vectores', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029210401', 'ANALÍTICA DESCRÍPTIVA II', 4, 'Cuarto Semestre', 3, 'Minería de Datos & KDD', 'patrones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029210401', 'ANALÍTICA DESCRÍPTIVA II', 4, 'Cuarto Semestre', 3, 'Analítica Predictiva & Machine Learning', 'regresión', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029210401', 'ANALÍTICA DESCRÍPTIVA II', 4, 'Cuarto Semestre', 3, 'Estadística & Probabilidad', 'estadística', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029210401', 'ANALÍTICA DESCRÍPTIVA II', 4, 'Cuarto Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029240401', 'BASES DE DATOS NoSQL', 4, 'Cuarto Semestre', 2, 'SQL / Bases de Datos Relacionales', 'sql', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029240401', 'BASES DE DATOS NoSQL', 4, 'Cuarto Semestre', 2, 'Bases de Datos NoSQL', 'nosql', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029240401', 'BASES DE DATOS NoSQL', 4, 'Cuarto Semestre', 2, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'Electiva II (Fundamentos Estratégicos de Gobierno de Datos)', 4, 'Cuarto Semestre', 2, 'Bases de Datos NoSQL', 'documentos', 'Fundamentación');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'Electiva II (Fundamentos Estratégicos de Gobierno de Datos)', 4, 'Cuarto Semestre', 2, 'Big Data & Arquitecturas Distribuidas', 'big data', 'Fundamentación');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 'Electiva II (Fundamentos Estratégicos de Gobierno de Datos)', 4, 'Cuarto Semestre', 2, 'Gobierno de Datos & Calidad', 'gobierno de datos', 'Fundamentación');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Minería de Datos & KDD', 'kdd', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Analítica Predictiva & Machine Learning', 'analítica predictiva', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Estadística & Probabilidad', 'hipótesis', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Algoritmos & Lógica de Programación', 'algoritmos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 'ANALÍTICA PREDICTIVA', 5, 'Quinto Semestre', 3, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 'Python', 'python', 'Específico');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 'Analítica Descriptiva & Visualización', 'visualización', 'Específico');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específico');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 'R / Estadística Computacional', 'r', 'Específico');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 'HERRAMIENTAS PARA EL ANÁLISIS DE DATOS', 5, 'Quinto Semestre', 2, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específico');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Bases de Datos NoSQL', 'documentos', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Minería de Datos & KDD', 'patrones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Procesamiento de Lenguaje Natural (NLP)', 'procesamiento de texto', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Analítica Descriptiva & Visualización', 'visualización', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 'PROCESAMIENTO DE TEXTO Y TÉCNICAS DE INFORMACIÓN', 5, 'Quinto Semestre', 2, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029320501', 'PROYECTO INTEGRADOR I', 5, 'Quinto Semestre', 3, 'Analítica Descriptiva & Visualización', 'power bi', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029320501', 'PROYECTO INTEGRADOR I', 5, 'Quinto Semestre', 3, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029320501', 'PROYECTO INTEGRADOR I', 5, 'Quinto Semestre', 3, 'Estadística & Probabilidad', 'hipótesis', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029320501', 'PROYECTO INTEGRADOR I', 5, 'Quinto Semestre', 3, 'Gestión de Proyectos & Metodologías Ágiles', 'cronograma', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 'Python', 'python', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 'Minería de Datos & KDD', 'patrones', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 'Analítica Descriptiva & Visualización', 'power bi', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 'PRÁCTICA PROFESIONAL', 5, 'Quinto Semestre', 4, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Transversal');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Python', 'python', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Analítica Descriptiva & Visualización', 'power bi', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Excel Avanzado / Hojas de Cálculo', 'excel', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'R / Estadística Computacional', 'r', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Investigación de Operaciones & Optimización', 'investigación de operaciones', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Algoritmos & Lógica de Programación', 'complejidad', 'Específica');
INSERT INTO fact_habilidades_academicas (programa_academico, codigo_materia, nombre_materia, semestre_ordinal, semestre_nombre, creditos, habilidad_tecnologica, termino_detectado, area_formacion) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 'TOMA DE DECISIONES ORGANIZACIONALES', 5, 'Quinto Semestre', 2, 'Toma de Decisiones & Estrategia', 'toma de decisiones', 'Específica');

-- INSERCIONES: fact_saberes_academicos
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029050101', 1, '1. Introducción al Big Data
1.1. Historia de manejo de datos
1.2. Algunos ejemplos de Big data

2. Tipos de datos y su caracteristicas
2.1. Datos estructurados
2.2. Datos No estructurados
2.3. Bases de datos y almacenamiento
2.4. Las 5 V
2.5. proceso ETL (Extracción - Transformación - Carga)
2.6. Ciclo de vida de los datos

3. Modelos orientados al Big Data
3.1. Data Mining
3.2. Text Mining
3.3. Web Mining
3.4. Otros modelos

4. Herramientas en Big data
4.1. Introducción a Hadoop
4.2. Arquitectura y componentes básicos aplicados a Big data
4.3. Introducción a python,
4.4. Arquitectura y componentes básicos aplicados a Big data,
4.5. Introducción a MongoDB,
4.6.Arquitectura y componentes básicos aplicados a Big data,
4.7. Introducción a R,
4.8. Arquitectura y componentes básicos aplicados a Big data.
4.9. Herramientas de visualización');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029030101', 1, '1. Generalidades
1.1. Desarrollo histórico y características
1.2. Definicion de información y dato
1.3. Principales tecnologías usadas en la adquisición de datos

2. Fases del Ciclo de vida de los datos
2.1. Definición de dato como entidad de analisis
2.2. Planificación
2.3. Construcción de un modelo
2.4. Explicar un modelo
2.5. Evaluación de un modelo
2.6. Impementación de un modelo
2.7. Monitoreo de modelos

3. El científico de datos y sus competencias
3.1. ¿Que debe saber un científico de datos?
3.2. Las destrezas que se deben adquirir
3.3. Software más usados en el análisis de datos, breve descripción

4. Aproximación a las metodologías de análisis de datos
4.1. Introducción al Machine Learning
4.2. Introducción al Big Data
4.3. Introducción a la Inteligencia Artificial

5. La ética en el manejo de datos
5.1. Principales teorias éticas sobre el uso y manejo de datos
5.2. Toma de decisiones éticas

6. Elementos básicos de gobierno de datos.
6.1. Los datos como activo de valor
6.2. sinergias en el manejo de datos
6.3. Factores necesarios en el gobierno de datos');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029020101', 1, '1.	Descripción de datos 
1.1.	Introducción a la estadística
1.2.	Escalas de medición: nominal, ordinal, de intervalo, de razón y su representación grafica 
1.3.	Distribución de frecuencias y graficas 
1.4.	Medidas de tendencia central (datos sin agrupar - datos agrupados): meda, mediana - moda media ponderada media geométrica
1.5.	Medidas de posición (datos sin agrupar - datos agrupados):   - deciles, cuartiles, percentiles   y su representación grafica (diagrama de cajas y bigotes)
1.6.	Medidas de dispersión (datos sin agrupar - datos agrupados):  - Rango, desviación media, varianza y desviación estándar - coeficiente de variación 
1.7.	Medidas de forma: - sesgo, asimétrica y curtosis
1.8.	Medidas de asociación:  Diagrama de dispersión, coeficiente de correlación lineal de Pearson.
2.	Probabilidad 
2.1.	Introducción a la probabilidad 
2.2.	Teoría de conjuntos
2.3.	Técnicas de conteo
2.4.	Principios y axiomas
2.5.	Probabilidad condicional
2.6.	Independencia de eventos 
2.7.	Teorema de Bayes');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 1, 'SABERES ESPECÍFICOS 
(saber)');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 2, 'Responsabilidad social universitaria
Responsabilidad social individual
Desarrollo sostenible
Proyección social
Cultura de paz y convivencia');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029060101', 3, 'Responsabilidad social universitaria
Responsabilidad social individual
Desarrollo sostenible
Proyección social
Cultura de paz y convivencia');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 1, '1. Expresiones algebraicas.
1.1 Operaciones básicas de expresiones algebraicas. 
1.2 Factorización de expresiones algebraicas .
1.2.1 Métodos generales de factorización. 
1.2.2 División sintética. 
1.3 Simplificación de expresiones algebraicas. 
1.4 Fracciones parciales. 

2. Ecuaciones.
2.1 Solución de ecuaciones de 1° y 2°.
2.3 Graficas de ecuaciones de 2°. - Secciones cónicas.
2.3.1. Ecuación de un circulo.
2.3.2. Ecuación de la parábola.
2.3.3. Ecuación de una elipse.
2.3.4. Ecuación de una hipérbola.
2.2 Solución de ecuaciones de grado superior. 
2,4. Solución de un sistema de ecuaciones.
2.4.1  Algebraicamente.
2.4.2. Gráficamente. 
2.4.3. Métodos numéricos.

3.Inecuaciones.
3.1. Solución de inecuaciones de 1°.
3.2. Solución de inecuaciones de 2°.

4. Ecuaciones exponenciales y logarítmicas.
4.1. Solución de ecuaciones exponenciales y logarítmicas.

5. Razones trigonométricas.
5.1. Razones trigonométricas. 
5.2. Solución de ecuaciones trigonométricas.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029070101', 1, 'Estructura gramatical de la oración y del párrafo, Las tipologías textuales, estructura y tipos de resúmenes: el RAE, el informe de lectura y la reseña crítica. La acentuación, correcciones del lenguaje, el sustantivo, las comunicaciones escritas, los signos de puntuación normas APA, técnicas de expresión oral');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029070101', 2, 'Demuestra en la redacción del informe de lectura, la comprensión del texto base y cumple con todos los párámetros de redacción, estructura del informe de lectura, oración y párrafo con excelente ortografía, léxico y cumplimiento de las normas APA.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029070101', 3, 'Demuestra en la redacción de la reseña crítica, la comprensión del texto base y cumple con todos los párámetros de redacción, estructura de RAE, oración y párrafo con excelente ortografía, léxico y cumplimiento de las normas APA.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029040101', 1, '1. Introducción a la teoria general de sistemas
1.1. Bertalanffy y su idea de sistema
1.2. Principios fundamentales de la ciencia
1.3. Enfoques: mecanicista vs sistémico

2. Fundamentos de la Teoria general de sistemas
2.1. Orígenes de la teoría
2.2. Definiciones de la teoría general de sistemas y enfoque sistémico
2.3. Elementos de un sistema
2.4. caracterización de sistemas (conceptualizació a partir de la conducta del sistema)
2.5. Tipos de sistemas según sus características

3. Aplicaciones de la teoría general de sistemas
3.1. La cibernética
3.2. la teoría de juegos
3.3. la teoría de la información

4. La teoría general de sistemas aplicada a las organizaciones
4.1. Principio de organicidad
4.2. La entropia como elemento desorganizador
4.3. La negentropia como elemento organizador');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130301', 1, '1.	Datos y tipos
1.1.	Variables
1.2.	Naturaleza de las variables
1.3.	Conversiones de variables
1.4.	Operadores
2.	Estructuras, Listas, Tuplas y Diccionarios, Conjuntos
2.1.	Tipo de estructuras.
2.2.	Llamado.
2.3.	Operaciones y funciones dentro de ellas
3.	Pseudocodigo, Diagrama de Flujo, Código
3.1.	Instrucciones
3.2.	Escritura de Instrucciones
3.3.	Regla en las instrucciones
4.	Estructuras de Control de Flujo
4.1.	Reglas y parámetros
4.2.	Algoritmos de cada estructura de control de flujo
5.	Funciones
5.1.	Distinción
5.2.	Parámetros
5.3.	Clasificaciones
5.4.	Librerías
5.5.	Objetivo de las librerías
5.6.	Crear librerías
5.7.	Numpy
5.8.	Math, Matplotlib, Pandas');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 1, '1. Concepto de Dato
1.1 Variables lineales
1.2 Variables aleatorias
1.4 Variables cuantitativas
1.5 Variables Cualitativas

2. Concepto de Información

3. Concepto de sistema de procesamiento de datos

4. Datos Estructurados

5 Datos no Estructurados

6 Definición de problema

7  Deducción de hipótesis contrastables.

8 Procedimientos de recolección de datos
8.1 Sistematización del dato 
8.2 Procedimientos de recolección de datos
8.3 Organización de los datos

9 Análisis de datos.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 2, 'El soporte argumentativo y teórico soportan con suficiecia el problema planteado y sus hipótesis.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 3, 'Los conceptos son plenamente aplicados, de acuerdo con lo reflejado en la rúbrica aplicada.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 4, 'Los conceptos y procedimientos son apropiados en alto grado por el estudiante, de acuerdo con el nivel alto presentado en las evidencias');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029100201', 5, 'Presenta un alto nivel de argumentación técnica y análisis, de acuerdo con las evidencias recopiladas y evaluadas.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029090201', 1, '1.	Matrices y sistemas lineales 
1.1.	Matrices 
1.1.1.	Definición
1.1.2.	Clases de matrices
1.1.3.	Operaciones con matrices
1.1.4.	Propiedades e las operaciones con matrices
1.1.5.	Matrices con números complejos
1.2.	Sistemas lineales 
1.2.1.	Definición y soluciones 
1.2.2.	Forma matricial de un sistema lineal
1.2.3.	Operaciones de renglón (fila) para matrices 
1.2.4.	Método de Gauss - Jordan para solución de un sistema lineal
1.2.5.	Aplicaciones (Circuitos, redes, economía)
2.	Matrices invertibles y determinantes 
2.1.	Matrices invertibles 
2.1.1.	Definición propiedades 
2.1.2.	Matriz inversa utilizando eliminación gaussiana 
2.2.	Determinantes
2.2.1.	Definición – determinante de una matriz 2x2 
2.2.2.	Matriz de cofactores.
2.2.3.	Determinante de una matriz 3x3
2.2.4.	Matriz inversa a partir del determinante y matriz adjunta
2.2.5.	Regla de Cramer 
3.	Vectores 
3.1.	Vectores en R3
3.1.1.	Propiedades físicas de un vector en el espacio.
3.1.2.	Producto escalar (punto), producto vectorial (cruz) de dos vectores
3.1.3.	Interpretación geométrica del triple producto escalar.
4.	Espacio vectorial
4.1.	Espacio vectorial – definición, propiedades 
4.2.	Subespacio vectorial - definición propiedades
4.3.	Combinación lineal – independencia lineal
4.4.	Base – dimensión rango nulidad.
5.	Transformaciones lineales
5.1.	Definición – propiedades 
6.	Valores y vectores propios
6.1.	Definición - propiedades');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14025080202', 1, '1.	Funciones 
1.1.	 Funciones básicas 
1.2.	 Funciones trascendentes 
1.3.	 Grafica de las funciones y sus transformaciones 
1.3.1 Traslación 
1.3.2 Reflexión
1.3.3 Dilatación y contracción 
1.4 Transformaciones de funciones 
1.4.1 Operación entre funciones 
1.4.2 Composición de funciones 

2. Límites y propiedades 
2.1 Cálculos de limites 
2.2 Límites infinitos  
2.3 Límites al infinito 
2.4 Continuidad 

3. Derivadas 
3.1 Derivadas y reglas de derivación.
3.2 Regla de la cadena y diferenciación implícita.
3.3 Aplicaciones de la derivada
3.3.1 Problemas de razón de cambio
3.3.2 Problemas de optimización 
3.3.3 Gráfica de funciones a partir de máximos, mínimos absolutos y locales');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14025140202', 1, 'Conceptualizar y diferenciar los distintos tipos de emprendimiento existentes

Identificar la diferencia entre problemas necesidades y deseos, como insumo principal para generar ideas de negocio

Apropiar metodologías para la adecuada validación de segmento de clientes e ideas de negocio

Definir y comprender la innovación como parte fundamental del proceso emprendedor');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029130201', 1, '1. Introducción a Python I y la programación informática.
2. Tipos de datos, Variables, Operaciones Básicas de Entrada y salida, Operadores Básicos.
3.Valores Booleanos, Ejecución condicional, Bucles, Listas y su procesamiento, Operaciones Lógicas y de Bit a Bit.
4. Funciones, Tuplas, Diccionarios, Excepciones y Procesamiento de Datos.
5. Proyecto Final - Prueba Final Fundamentos Python I - Examen de certificación PCEP - Certified Entry - Level Python programmer.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029170301', 1, '1. Arreglos.
 - Vectores y matrices.
 - Operaciones
2. Clases y Métodos.
 - Clases.
 - Métodos
 - Atributos.
3. Relaciones
 - Entidades
 - Relaciones entre clase
3. Programación Orientada a Objetos.
 - Instancias, Objetos, Ejemplarizar.
 - Modularización
 - Encapsulamiento
 - Herencia
 - Polimorfismo
4. Excepciones y Capturas
 - Concepto
 - Try - Except
5. Módulos, Paquetes y archivos.
 - Rutas y usos.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029180301', 1, 'Introducción a las Bases de Datos Tipos de Modelos de Datos
Modelo relacional y álgebra relacional
Introducción al diseño de bases de datos Modelamiento de bases de datos Normalización de Bases de Datos Motores de Bases de Datos
Lenguaje SQL
Organización y gestión de bases de datos');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029150301', 1, '1. Esperanza Matemática

2. Normalidad

3. Distribución de probabilidad de variable aleatoria continua
3.1.	Aproximación de la binomial a la normal
3.2.	Distribución exponencial
3.3.	Distribución gamma
3.4.	Distribución chi cuadrado
3.5.	Distribución erlang y wiebul
3.6.	Datos bivariados continuos
3.7.	Distribuciones marginales covarianza – correlación

4.	Distribución de probabilidad de variable aleatoria discreta 
4.1.	Distribución uniforme discreta
4.2.	Prueba de Bernoulli
4.3.	Función de Distribución de Bernoulli
4.4.	Distribución Binomial
4.5.	Distribución Multinomial
4.6.	Distribución de Poisson
4.7.	Distribución geométrica
4.8.	Distribución hipergeométrica');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029140301', 1, '1. Anti derivada o primitiva de una función
1.1. El problema del área – e integración numérica

2. Integral indefinida
2.1. Reglas básicas de integración
2.2. Integración con condiciones iníciales

3. Técnicas de integración.
3.1. Integración por sustitución.

4. integrales definidas – Teorema fundamental del cálculo
4.1. Área bajo la curva
4.2. Área entre curvas
4.3  Centro de masa
4.4 Trabajo
4.5 Presión hidrostática

5. Otros métodos de integración
5.1. Integración por partes
5.2. Integrales trigonométricas
5.3. Integrales por sustitución trigonométrica
5.4. Integrales utilizando fracciones parciales
 
6. Volumen de un sólido de revolución.
6.1. Método de discos
6.2. Método de capas

7. Integrales impropias');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029160301', 1, '1. INTRODUCCIÓN A LA INVESTIGACIÓN DE OPERACIONES 
1.1.  Breve historia de la investigación de operaciones. 
1.2.  Introducción a la Investigación de Operaciones 
1.3.  Definición de investigación de operaciones. 
1.4.  Aplicaciones de la Investigación de Operaciones 
1.5.  Metodología de la investigación de operaciones. 

2. METODO SIMPLEX 
2.1.	 SoluciónGraficaproblemalineal 
2.2.	 Teoría del método Simplex 
2.3.	 Conceptos básicos del método 
                2.3.1. Variablesdeholgura, artificial y de excedente 
                2.3.2. Variables básicas y soluciones 
2.4.	 El método de la M grande
2.5.	 Método de dos fases
2.6.	 Casos especiales de método simplex 
 2.6.1. Problemasnoacotados 
 2.6.2. Problemasinconsistentes 
 2.6.3. Problemasdegenerados 

3.  ANALISIS DE SENSIBILIDAD Y DUALIDAD 
3.1.  Introducción gráfica al análisis de sensibilidad 
3.2.  Análisis de sensibilidad 
3.3.  Análisis de sensibilidad cuando se cambia mas de un parámetro 
3.4.  Método dual 
3.5.  Holgura complementaria 
3.6.  Método Simplex dual 


4.  MODELO DE TRANSPORTE 
4.1.  Definición problema de transporte 
4.2.  Método de aproximación Vogel 
4.3.  Método simplex para el transporte 
4.4.  Procedimiento de optimización 

5.   MODELOSDEREDES 
5.1.  Definiciones básicas 
5.2.  Problemas camino más corto 
5.3.  Problemasflujomáximo 
5.4.  CPM YPERT 
5.5.  Problemas de flujo en redes de costo mínimo 
5.6.  Problemas de árbol de extensión mínima 
5.7.  Método Simplex para redes');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029190301', 1, '(1) El proceso de la investigación, sus métodos y enfoques
(2) El método científico y la ciencia.
(3) Historia de la ciencia y epistemología
(4) Formulación del Problema de investigación, hipótesis, objetivos de investigación, marco teórico.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '142001130504', 1, 'Analizar los conceptos de gestión de proyectos
Conceptualizar el desarrollo de los proyectos
Determinar los factores relevantes de la gestión de proyectos');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029220401', 1, '1  Importancia del dato en la toma de decisiones.
1.1  La importancia del dato en las decisiones de Negocio
1.2  Definición de minería de datos
1.3  El proceso de la Minería de Datos
1.4  Tipologías de Técnicas de Minería de Datos
1.5  Propiedades de la Minería de Datos
2  Análisis exploratorio de datos y preprocesamiento 2.1Exploración de los Datos
2.1 Preprocesamiento de Datos
2.2 Preprocesamiento de Datos II Predictivos
2.3 Medición de la Calidad del Modelo Predictivo
3 – Fundamentos y administración de la información.?
3.1  Conceptualización analítica de los datos
3.2  Manejo de Excel avanzado filtros avanzados
3.3  Manejo de Excel avanzado Tablas Dinámicas
3.4  Manejo de Excel avanzado relación de tablas dinámicas
3.5  Manejo de Excel avanzado - Gráficos dinámicos y combinados
4   Clasificación y predicción
4.1  Problemas de clasificación.
4.2  Árboles de decisión
4.3  Clasificadores estadísticos: regresión y análisis discriminante
4.4  Redes Bayesianas
4.5. Redes Neuronales.
4.6   de los modelos extraídos.
5  Reglas de Asociación
5.1 Definición de reglas de asociación
5.2 Definición del problema.
5.3 Algoritmo A priori.
6   Agrupación (Clustering)
6.1. Definición.
6.2  Distancia entre datos.
6.3 Principales métodos de agrupación.
7   Detección de datos anómalos
7.1  Métodos estadísticos
7.2 Métodos de proximidad.
7.3 Métodos de agrupación.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029230401', 1, '1.	Definición de modelos analíticos
2.	Tipos de modelos analíticos

3.	Modelos analíticos supervisados: 

•	Árboles de Decisiones
•	Random forest
•	Regresión lineal.
•	Regresión logística.
•	Clasificación de Naïve Bayes.
•	Support Vector Machines (SVM).
•	Métodos “Ensemble” (Conjuntos de clasificadores).
•	Reglas de Asociación

4.	Modelos analíticos no supervisado

•	Reducción de dimensión.
o	Análisis de componentes principales.
o	Descomposición en valores singulares.
o	Análisis de componentes independientes.
•	Clustering con K-Means
•	Modelos de Gradient Boosting
•	Redes Neuronales
•	Modelos de Deep Learning');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029200401', 1, '1. Introducción a la Seguridad de la Información.
1.1. Definición y propósito de la seguridad de la información.
1.2. Definición y propósito de la seguridad informática.
1.3. Términos y definiciones de acuerdo al estándar ISO/IEC 27001:2022.
1.4. Ataques, amenazas y vulnerabilidades.
1.5. Vectores de ataque, generalidades, tipos y metodologías aplicables a vectores de ataque.
1.6. Delitos Informáticos y aspectos Jurídicos Relacionados.

2. Fundamentos del Estándar NTC ISO/IEC 27001:2022.
2.1. Generalidades del estándar.
2.2. Contexto de la organización.
2.3. Liderazgo.
2.4. Planificación.
2.5. Apoyo.
2.6. Operación.
2.7. Evaluación de desempeño.
2.8. Mejora continua.

3. Estándar ISO/IEC 27002:2022.
3.1. Estructura ISO/IEC 27002:2013 vs ISO/IEC 27002:2022.
3.2. Análisis Anexo A - ISO/IEC 27002:2013. 
3.3. Análisis Anexo A - ISO/IEC 27002:2022.

4. Valoración del riesgo.
4.1. Estándar NTC ISO/IEC 31000:2018
4.2. Metodología Magerit (análisis de los riesgos).
4.3. Identificación de riesgos.
4.4. Análisis y evaluación de riesgos.
4.5. Practica: Seguridad en redes – Ataques en capa 2.

5. Modelo de Administración de Riesgos (MAR).
5.1. Concepto de Modelo de MAR.
5.2. Objetivos de un MAR.
5.3. Estructura de un MAR.
5.4. Práctica: Seguridad en redes – Mitigar riesgos en capa 2. 
5.5. Caso de Estudio: Elaborar un Modelo de Administración de Riegos.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029210401', 1, '1. Distribuciones de Probabilidad 
1.1.        Distribución normal - distribución Z
1.2.	Distribución t student
1.3.	Distribución F

2. Estadística inferencial - estimación de parámetros                              
2.1. Inferencia estadística para una muestra 
2.1.1. Distribución muestral de la proporción 
2.1.2. Distribución muestral de la varianza
2.2. Inferencia estadística para la media 
2.3. Inferencia estadística para la proporción 
2.4. Prueba de bondad de ajuste
2.5. Inferencia estadística para dos muestras 
2.5.1 Distribución muestral para la diferencia de medias
2.5.2 Distribución muestral para la diferencia de proporciones 
2.5.3. Distribución muestral para la razón entre varianzas 
2.6. Inferencia estadística para la diferencia de medias 
2.7. Inferencia estadística para la diferencia de proporciones 
2.8. Inferencia Regresión lineal simple - mínimos cuadrados');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029240401', 1, '1. Generalidades
1.1 Diferenciales de las bases de datos relacionales y no relacionales
1.2. Conocer la terminología de una base de datos SQL y No SQL (MongoDB).

2. Instalación y primeros pasos
2.1 Como instalar Mongo o como instalar alguna herramienta que nos va ayudar a trabajar con Momgo DB y gestionar la Base de Datos

3. Colecciones y Documentos
3.1 Aprender a trabajar con los documentos embebidos  de acuerdo a minería básica
3.2 Trabajar con colecciones de objetos dentro de los documentos.

4. Documentos Embebidos 1 
4.1 Como trabajar con documentos embebidos.

5.  Operadores y Consultas
5.1  Más tipos de consultas
5.2 Se harán  operaciones con las consultas
5.3 Saber como consultar y obtener información desde una base de datos No SQL MongDB

6. Documentos Embebidos 2
6.1 Trabajar de manera más profunda con los documentos embebidos o los documentos dentro de otros objetos 
6.2 Saber como trabajar más con colecciones y documentos dentro de un documento o documentos embebidos 
6.3 Como hacer operaciones de Cloud con los documentos

7. Servicio API`s RESTful con Nodejs y MongoDB
7.1 Crear un servicio API RESTful CON Nodejs y MongoDB
7.2 Ver como crear una API que es un tipo de aplicación que suele quedar mucho actualmente para el Bakken
7.3 Como crear un amigo no JDs y como conectar estas 2 tecnologías
7.4 Como utilizar Mongolos que es una librería que nos va ayudar a trabajar con estas 2 tecnologías en conjunto');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029010101', 1, '1. Fundamentos Gobierno de Datos
2. Arquitectura de Datos
3. Modelación y Diseño de Datos
4. Almacenamiento y operación de Datos
5. Seguridad de Datos
6. Habeas data y manejo de datos.
7. Integración e Interoperabilidad de Datos
8. Gestión de Documentos y contenido
9.  Datos Maestros y de Referencia
10. Gestión de Metadatos
11. Calidad de Datos');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029270501', 1, '1. Principios del análisis exploratorio de datos estructurados y su función en el ciclo de análisis de datos.
2, Modelos y técnicas de apoyo a la toma de decisiones basados en datos.
3. Fundamentos y aplicaciones de la analítica predictiva en diversos sectores.
4. Técnicas de análisis predictivo para datos financieros y de negocio.
5. Evaluación y gestión de riesgos mediante modelos analíticos.
6.Técnicas de aprendizaje automático supervisado y métodos de clasificación, con énfasis en k-nearest neighbors (k-NN).
7. Etapas del proceso KDD (Knowledge Discovery in Databases) y su integración con la analítica predictiva.
8. Técnicas de validación y ajuste de modelos predictivos.
9. Etica en modelos predictivos.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029280501', 1, '1. Principios del data storytelling: estructura narrativa, contexto, audiencia y mensaje en la comunicación basada en datos.
2. Diseño y elaboración de visualizaciones efectivas con bibliotecas de Python como Matplotlib, Seaborn y Plotly.
3. Creación de informes interactivos y dashboards con herramientas como Power BI, Tableau y Google Data Studio.
4. Documentación y presentación de análisis en entornos interactivos como Jupyter Notebook y Google Colab
5. Automatización de procesos de análisis para la generación de reportes reproducibles con Python scripting.
6. Control de versiones y trabajo colaborativo de proyectos analíticos con Git y GitHub.
7. Gestión de entornos virtuales y buenas prácticas en organización de proyectos analíticos (conda, virtualenv).
8. Ética en la comunicación de datos: integridad, transparencia, representación visual honesta y accesibilidad del mensaje.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029300501', 1, '1. Fundamentos del procesamiento de lenguaje natural (PLN): tokenización, lematización, eliminación de stopwords y técnicas básicas de preprocesamiento textual.
2. Representación de texto para análisis: bolsa de palabras, TF-IDF y modelos vectoriales simples.
3. Análisis exploratorio de datos textuales: visualización de frecuencias, nubes de palabras y detección de patrones.
4. Extracción de información a partir de texto: entidades nombradas, frases clave y relaciones semánticas.
5. Técnicas básicas de búsqueda y recuperación de información en textos no estructurados
6. Introducción al modelado temático y clasificación de documentos.
7. Herramientas computacionales para procesamiento de texto en Python (como NLTK y spaCy).
8. Automatización de flujos de procesamiento textual mediante notebooks interactivos y pipelines simples. 
9. Aplicaciones del análisis de texto en entornos reales: análisis de sentimiento, segmentación de clientes, minería de opiniones.');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029320501', 1, 'Planteamiento del problema y sus elementos
          Objetivos general y específicos
          Preguntas de investigación
          Justificación y motivación
          Viabilidad
Planteamiento de la hipótesis (si aplica)
Estudio y Análisis del estado del arte 
Construcción de Marco teórico
Alcance de la investigación e Impacto esperado
Planteamiento del diseño metodológico 
Plan de trabajo con su cronograma de actividades (Diagrama de Gantt)');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029310501', 1, 'Identifica la estructura organizacional de la empresa, definiendo los roles de dicha estructura y aplicando los saberes de la ciencia de datos para generar valor a la organización.
Desarrolla actividades que conllevan a la solución de los problemas identificados y los aborda desde la ciencia de datos
Diseña, propone y desarrollar procesos de análisis y gestión de datos  en las áreas a su cargo Trabaja en equipo
Aplica técnicas y métodos de la ciencia de datos para identificar patrones y generar conocimiento útil que agrege valor');
INSERT INTO fact_saberes_academicos (programa_academico, codigo_materia, orden_tema, saber_especifico) VALUES ('Tecnología en Análisis y Gestión de Datos', '14029290501', 1, '1. Estilos de toma de decisiones organizacionales
2. Modelos de toma de decisiones: modelo contingencial y modelo estrella
3. Decisiones individuales y en equipo
4. Herramientas para la toma de decisiones
5. Definición y análisis del problema
6. Diagramas de correlación y flujogramas de procesos
7. Herramientas de comunicación para la toma de decisiones');

-- ==================================================================
-- 4. VISTA DE ANÁLISIS DE COBERTURA CURRICULAR POR PROGRAMA
-- ==================================================================
CREATE OR REPLACE VIEW vista_cobertura_curricular AS
SELECT 
    m.programa_academico,
    m.habilidad_tecnologica,
    COUNT(DISTINCT m.codigo_materia) as materias_que_la_ensenian,
    MIN(m.semestre_ordinal) as primer_semestre_introduccion,
    STRING_AGG(DISTINCT m.nombre_materia, ', ') as asignaturas_donde_se_imparte,
    SUM(m.creditos) as creditos_acumulados_asociados
FROM fact_habilidades_academicas m
GROUP BY m.programa_academico, m.habilidad_tecnologica;
