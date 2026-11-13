# Guía de anotación: conjunto de referencia de ofertas de empleo

**Propósito:** construir, a mano y con criterio humano, la «respuesta correcta» para 200 ofertas reales
del observatorio, y medir con ella qué tan bien el sistema detecta habilidades, rol, experiencia y nivel
(precisión, recall y F1). Es la evaluación de la extracción del Artículo 1.

Versión 1 · 7-nov-2026 · Proyecto de Juan Felipe Bernal · Data Scientist

---

## 1. Reglas generales

1. **Trabaje solo.** No consulte a la otra persona anotadora ni los resultados del sistema. Las planillas
   no muestran lo que detectó el sistema, a propósito: queremos su juicio, no una corrección del sistema.
2. **Juzgue por el significado, no por palabras sueltas.** El sistema busca palabras; usted decide si la
   oferta realmente pide esa habilidad. Por eso hay casos difíciles en la sección 4.
3. **Solo cuenta lo que se pide para el cargo.** Requisitos, funciones, «deseable» o «valoramos» cuentan.
   No cuenta lo que describe a la empresa («somos líderes en inteligencia artificial») si no es parte del
   trabajo.
4. **Si duda, decida igual y anótelo** en la columna `comentario`. Las dudas sirven para mejorar la guía.
5. **No modifique las columnas grises** (id, portal, mes, título, texto). En el texto, `[CORREO]` y
   `[TELÉFONO]` reemplazan datos de contacto.
6. **Tiempo estimado:** unos 3 minutos por oferta. Anotador A: 200 ofertas (~10 horas); anotador B: 60
   (~3 horas). Conviene hacerlo en sesiones de 30–45 minutos.

## 2. Campos de la planilla

| Columna | Qué escribir |
|---|---|
| `rol` | Uno de la lista (sección 3), según el trabajo descrito **en conjunto** (título más funciones), no solo el título. |
| `anios_minimos` | Años mínimos de experiencia **si la oferta los dice**: «de 2 a 4 años» → 2; «5+ años» → 5; «sin experiencia» → 0; «6 meses» → 0,5. Si no lo dice, **deje vacío** (no adivine). |
| `nivel` | Junior, Semi-Senior, Senior, Líder o «No se indica». Use lo que diga la oferta (título o texto). Si solo hay años: 0–1 Junior, 2–3 Semi-Senior, 4–5 Senior, más de 5 Líder. Si no hay ninguna señal: «No se indica». |
| Columnas de habilidades | Escriba **1** si la oferta pide esa habilidad; deje vacío si no. |
| `Excel AVANZADO (lo dice explícitamente)` | 1 solo si la oferta dice «Excel avanzado», tablas dinámicas, macros o VBA. |
| `otras_habilidades` | Habilidades **técnicas** importantes que no tienen columna (por ejemplo SAS, SPSS, Snowflake, Jira), separadas por «;». |
| `comentario` | Dudas, casos raros, ofertas en otro idioma, texto incompleto. |

## 3. Roles

| Rol | Cuándo |
|---|---|
| Científico de Datos | Modelos estadísticos o de aprendizaje automático para predecir o explicar; experimentación. |
| Analista de Datos | Consultas, limpieza, reportes y análisis descriptivo para responder preguntas del negocio. |
| Ingeniero de Datos | Canalizaciones (pipelines), almacenamiento, bodegas y lagos de datos, plataformas; también arquitecto de datos y administrador de bases de datos. |
| Machine Learning / AI Engineer | Llevar modelos a producción, MLOps, sistemas de IA o LLM como producto. |
| Analista de BI y Visualización | Tableros, indicadores, Power BI o Tableau como función principal. |
| Desarrollador de Software / Datos | Desarrollo de software donde los datos son secundarios. |
| Otro rol | Del tema de datos, pero ninguno de los anteriores (por ejemplo, gobierno de datos o gerente de analítica sin función técnica). |
| No es del tema | Nada que ver con datos (ventas, salud asistencial, etc.). |

Si un cargo mezcla dos roles, elija el que ocupa **la mayor parte de las funciones** y anote el otro en el
comentario.

## 4. Habilidades: qué cuenta y casos difíciles

| Habilidad | Marque 1 si… | Casos difíciles |
|---|---|---|
| Python | Se pide programar en Python. | — |
| R | Se pide el lenguaje R o RStudio. | «R&D», «R+D» o una letra R suelta en otro sentido **no** cuentan. |
| SQL | Se pide SQL o una base de datos relacional (PostgreSQL, MySQL, SQL Server, Oracle **base de datos**). | **Oracle como ERP o sistema contable no cuenta.** «NoSQL» no cuenta aquí (va en NoSQL). |
| Scala | Lenguaje Scala. | — |
| Java / C++ | Java, C++ o C#. | «JavaScript» **no** cuenta. |
| Power BI | Power BI o DAX. | — |
| Tableau | Tableau. | — |
| Excel u hojas de cálculo (cualquier nivel) | Se pide Excel o hojas de cálculo, a cualquier nivel. | Si además dice «avanzado», marque también la columna de Excel avanzado. |
| Looker | Looker o Looker Studio (antes Data Studio). | — |
| Qlik | QlikView o Qlik Sense. | — |
| Spark / PySpark | Apache Spark o PySpark. | — |
| Databricks | Databricks. | — |
| Hadoop / Hive | Hadoop o Hive. | — |
| Kafka | Apache Kafka. | — |
| AWS | Amazon Web Services o sus servicios (S3, EC2, Redshift, Glue, SageMaker…). | — |
| Azure | Microsoft Azure o sus servicios (Synapse, Data Factory, Azure ML…). | «Microsoft» u «Office 365» solos **no** cuentan. |
| Google Cloud (GCP) | Google Cloud o sus servicios (BigQuery, Vertex AI…). | «Google Analytics» o «Google Sheets» **no** cuentan. |
| Machine Learning General | Aprendizaje automático o modelos predictivos en general. | Una sigla «ML» que no se refiera a machine learning no cuenta. |
| Deep Learning | Aprendizaje profundo o redes neuronales. | — |
| NLP / LLMs | Procesamiento de lenguaje natural, LLM, GPT, BERT, *transformers*. | «Transformers» en otro sentido (eléctrico) no cuenta. |
| Computer Vision | Visión por computador u OpenCV. | — |
| Scikit-Learn | scikit-learn. | — |
| TensorFlow / Keras | TensorFlow o Keras. | — |
| PyTorch | PyTorch. | — |
| Estadística / Modelamiento | Estadística, modelamiento estadístico, series de tiempo, inferencia. | «Estadísticas» como sinónimo de reportes o cifras de negocio **no** cuenta si no se pide la disciplina. |
| ETL / Pipelines de Datos | Procesos ETL/ELT o canalizaciones de datos (incluye dbt o Airbyte). | **«Pipeline» de ventas o de CI/CD de software no cuenta.** |
| Airflow | Apache Airflow. | — |
| Docker / Kubernetes | Docker, Kubernetes o contenedores. | — |
| Git / Control de Versiones | Git, GitHub, GitLab o control de versiones. | — |
| Bases de Datos NoSQL | MongoDB, Cassandra, Redis, Elasticsearch o «NoSQL». | — |
| MLOps | MLOps o MLflow. | — |

## 5. Acuerdo y versión final

1. Las 60 ofertas que etiquetan las dos personas sirven para medir el **acuerdo entre anotadores**:
   - kappa de Cohen y porcentaje de acuerdo, por habilidad y para rol y nivel;
   - coincidencia exacta y a ±1 año para los años.
2. Los desacuerdos de esas 60 se resuelven **conversando, con esta guía en la mano**. Si la guía no
   cubría el caso, se actualiza y se anota el cambio.
3. **Referencia final:** las 60 resueltas más las 140 que etiquetó solo la persona A.
4. Contra esa referencia se mide el sistema: precisión, recall y F1 por habilidad y en conjunto (micro y
   macro), exactitud y F1 de rol, y exactitud de años y de nivel. Todo con intervalos de confianza por
   *bootstrap*.
5. La misma referencia se usa para la **línea base con LLM**: el modelo extrae lo mismo de las 200
   ofertas y se compara en igualdad de condiciones.

## 6. Archivos

- `data/anotacion/anotador_A.xlsx` (200 ofertas) y `data/anotacion/anotador_B.xlsx` (60).
- `data/anotacion/clave_muestra.csv` vincula cada `id_muestra` con la oferta. **No se entrega** a las
  personas anotadoras.
- La carpeta `data/anotacion/` está fuera de git: contiene el texto de las ofertas y el repositorio es
  público.
- La muestra se reproduce con `python scripts/muestra_anotacion.py` (semilla 2026): 200 ofertas
  estratificadas por portal y mes entre las 905 únicas al 7-nov-2026.
