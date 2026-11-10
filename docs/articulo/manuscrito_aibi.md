---
title: "Observatorio Auditable del Mercado Laboral en Datos con Inteligencia Artificial Generativa Anclada en Evidencia: Diseño y Evaluación"
subtitle: "An Auditable Observatory of the Data Job Market with Evidence-Grounded Generative Artificial Intelligence: Design and Evaluation"
lang: es-ES
csl: estilos/ieee.csl
bibliography:
  - referencias.bib
  - referencias_metodo.bib
link-citations: true
---

<!--
Manuscrito para AiBi, Revista de Investigación, Administración e Ingeniería (UDES), artículo de investigación científica
y tecnológica. Normas (Políticas editoriales, 10-nov-2026): resumen 150–300 palabras estructurado (Antecedentes,
Objetivo, Métodos, Resultados, Conclusión), sin abreviaturas; 3–8 palabras clave en orden alfabético (Tesauro UNESCO);
secciones en números romanos; IEEE; ≥ 20 referencias; ≤ 25 páginas; Times New Roman 9 pt (estilos/referencia_aibi.docx);
figuras como .jpg aparte (≤ 580 px de ancho). APC USD 200 solo si se acepta.
Fuente de cada cifra: articulo1_borrador.md (script y corte). [PENDIENTE: …] = resultado o dato que falta.
-->

::: {custom-style="Author"}
Juan Felipe Bernal Peña^1^
:::

::: {custom-style="Author"}
*^1^ Estudiante del programa de Ciencia de Datos, Facultad de Ingeniería, Semillero de Investigación Codex, Fundación
Universitaria Cafam (UniCafam),
Bogotá, Colombia. Correo: juan.bernal@unicafam.edu.co. ORCID: https://orcid.org/0009-0005-2327-8974.*
:::

**Resumen**--- **Antecedentes:** las instituciones de educación superior necesitan ajustar sus programas en datos a un
mercado laboral que cambia con rapidez, y los modelos de lenguaje que se proponen para apoyar el diseño curricular
producen cifras sin respaldo. **Objetivo:** diseñar y evaluar un observatorio auditable del mercado laboral en roles de
datos que integra inteligencia artificial generativa anclada en evidencia, desarrollado para la actualización curricular
de la Fundación Universitaria Cafam. **Métodos:** siguiendo la investigación en ciencia del diseño, se construyó un
sistema que recolecta cada mes avisos de empleo de siete fuentes, extrae habilidades, rol y experiencia con reglas
explícitas, estima la demanda y las primas salariales con intervalos de confianza, corrección por comparaciones
múltiples y pruebas de equivalencia, y entrega a un modelo de lenguaje un contexto de mercado versionado como única
fuente de cifras; un verificador determinista revisa cada cifra generada y una persona aprueba cada propuesta. La
evaluación, en tres rondas, usó 907 avisos únicos de septiembre a noviembre de 2026 y 36 generaciones controladas.
**Resultados:** con el contexto de mercado, el verificador marcó entre 0 % y 0,7 % de las cifras revisadas; sin
anclaje, entre 93,8 % y 100 %. Frente a 200 avisos anotados a mano, las reglas alcanzaron un F1 de 0,85 en
habilidades y una exactitud de 0,79 en el rol; un modelo de lenguaje con la misma guía obtuvo 0,88 y 0,81. Con 176 ofertas con salario, las primas de los roles de ingeniería y ciencia de datos frente
al analista fueron concluyentes, mientras que ninguna prima por habilidad lo fue. **Conclusión:** anclar el modelo en un
contexto versionado y verificar sus cifras con reglas reduce notablemente las cifras sin respaldo, y declarar la
ausencia de evidencia es una función central del observatorio.

**Palabras clave:** ciencia de datos, diseño curricular, educación superior, inteligencia artificial, mercado de trabajo,
oferta de empleo, verificación de datos.

**Abstract**--- **Background:** higher education institutions need to align their data programs with a fast-changing
labor market, and the language models proposed to support curriculum design produce unsupported figures.
**Objective:** to design and evaluate an auditable observatory of the labor market for data roles that integrates
evidence-grounded generative artificial intelligence, developed for curriculum updating at Fundación Universitaria
Cafam, Colombia. **Methods:** following design science research, we built a system that collects job postings monthly
from seven sources, extracts skills, role and experience with explicit rules, estimates demand and wage premiums with
confidence intervals, multiple-comparison correction and equivalence tests, and provides a language model with a
versioned market context as its only source of figures; a deterministic verifier checks every generated figure and a
person approves each proposal. The three-round evaluation used 907 unique postings from September to November 2026 and
36 controlled generations. **Results:** with the market context, the verifier flagged between 0% and 0.7% of the
checked figures; without grounding, between 93.8% and 100%. Against 200 hand-annotated postings, the rules reached an
F1 of 0.85 for skills and an accuracy of 0.79 for role; a language model given the same guide obtained 0.88 and 0.81.
With 176 postings reporting salary, the premiums of data engineering and data
science roles over the analyst role were conclusive, while no skill premium was. **Conclusion:** grounding the model in
a versioned context and verifying its figures with rules markedly reduces unsupported figures, and reporting the absence
of evidence is a core function of the observatory.

**Keywords:** artificial intelligence, curriculum design, data science, data verification, higher education, job
postings, labour market.

# I. INTRODUCCIÓN {-}

Las instituciones de educación superior necesitan ajustar sus programas de análisis, ciencia e ingeniería de datos a un
mercado laboral que cambia con rapidez. La evidencia sobre ese mercado suele provenir de encuestas que tardan en
publicarse o de informes privados cuya metodología no es transparente. Los avisos de empleo publicados en internet se
han convertido en una fuente frecuente y granular para medir los requisitos de los empleadores
[@hershbein2018recessions; @deming2018skill], aunque no constituyen una muestra representativa del mercado
[@kurekova2015using; @lovaglio2026analyzing].

Al mismo tiempo, los modelos de lenguaje de gran tamaño (LLM, por sus siglas en inglés) se proponen como apoyo para
diseñar programas académicos [@kasneci2023chatgpt; @genc2026comparative; @brown2025toward]. Su
problema es que producen afirmaciones fluidas sin respaldo: en economía, más del 30 % de las citas generadas por
GPT-3.5 no existían [@buchanan2024chatgpt]; en un sistema de generación aumentada por recuperación sobre informes
financieros, las preguntas cuantitativas obtuvieron peores puntajes que las cualitativas [@iaroshev2024evaluating]; y,
al verificar afirmaciones científicas contra tablas, casi todos los modelos evaluados quedaron apenas por encima del azar
[@lu2023scitab]. Una propuesta curricular que afirma que una habilidad aparece en el 68 % de las ofertas solo es útil si
esa cifra se puede verificar.

Los componentes de este problema se han estudiado por separado: la recolección de avisos, la extracción de habilidades
[@khaouja2021survey; @senger2024deep] y el uso de LLM en el diseño curricular. Sin embargo, una revisión reciente del
alineamiento entre currículo e industria con inteligencia artificial señala la falta de conjuntos de datos estándar y
una validación limitada [@handayani2026driven]. Faltan sistemas integrados, de la recolección a la propuesta
curricular, con una evaluación cuantitativa de cada componente.

El objetivo de este trabajo es diseñar y evaluar un observatorio auditable del mercado laboral en roles de datos que
integra inteligencia artificial generativa anclada en evidencia. El sistema se desarrolló para apoyar la actualización
curricular de la oferta en datos de la Fundación Universitaria Cafam (UniCafam), en Bogotá, que articula la Tecnología en
Análisis y Gestión de Datos con el programa profesional en Ciencia de Datos. El observatorio (a) recolecta cada mes
avisos de siete fuentes de Colombia y de trabajo remoto; (b) estima la demanda de habilidades y las primas salariales
con intervalos de confianza y control de comparaciones múltiples; (c) entrega a un LLM un contexto de mercado
versionado como única fuente de cifras; (d) verifica de forma determinista cada cifra que genera el modelo; y (e) exige
la aprobación de una persona. El estudio responde cuatro preguntas de investigación (PI):

- **PI1, extracción:** ¿con qué exactitud el sistema de reglas extrae habilidades, rol, experiencia y nivel frente a una
  referencia humana, y frente a un LLM con las mismas instrucciones?
- **PI2, anclaje:** ¿el contexto de mercado reduce las cifras sin respaldo en las propuestas generadas, y cambia este
  efecto con el modelo?
- **PI3, verificación:** ¿con qué precisión y exhaustividad detecta el verificador las cifras sin respaldo o mal
  atribuidas?
- **PI4, utilidad:** ¿qué informa el observatorio sobre el mercado de roles de datos, con qué incertidumbre y con qué
  límites?

El sistema está desplegado y en operación desde septiembre de 2026. Este artículo reporta su diseño y la evaluación de
los tres primeros cortes mensuales; el código es abierto, de modo que cada cifra se puede reproducir.

# II. MARCO TEÓRICO {-}

## A. Los avisos de empleo en línea como fuente de datos {-}

Los avisos publicados en internet se han consolidado como fuente para medir los requisitos de habilidades de los
empleadores [@hershbein2018recessions; @deming2018skill], y hay evidencia de que las habilidades que piden corresponden a
las que se usan en el puesto [@daly2025skill]. No son, sin embargo, una muestra representativa:
Kureková et al. [@kurekova2015using] sistematizan sus problemas metodológicos; Lovaglio y Mezzanzanica [@lovaglio2026analyzing] encuentran una fuerte
sobrerrepresentación de los avisos frente a los datos de referencia de la encuesta de fuerza laboral; y varios trabajos
los combinan con estadística oficial mediante calibración o modelos de selección [@beresewicz2021enhancing;
@lovaglio2026forecasting]. Un mismo aviso suele aparecer en varios portales, y detectarlo
es un problema en sí mismo [@zhao2021framework].

En América Latina, los avisos se han usado para medir la demanda laboral [@camposvazquez2021labor;
@cocon2023scraping], extraer habilidades [@anelli2023which] y caracterizar mercados de
inteligencia artificial alineados con la clasificación europea ESCO [@guevararamirez2026characterization]. El trabajo
más cercano al presente, Suárez-Rodríguez et al. [@suarezrodriguez2026semantic], analiza 14 227 avisos de siete países latinoamericanos entre 2022
y 2025 y encuentra que, tras la aparición de ChatGPT, cambió sobre todo la terminología de las habilidades de
inteligencia artificial más que el volumen de vacantes, lo que advierte sobre las taxonomías fijas. En Colombia,
Álvarez y Hofstetter [@alvarez2014vacancies] construyen un índice de vacantes con avisos de prensa desde 1976, y Farné [@farne2011observatories]
discuten qué es y cómo funciona un observatorio del mercado de trabajo.

## B. Extracción de habilidades y su evaluación {-}

Las revisiones de la tarea distinguen entre diccionarios o reglas, modelos supervisados de etiquetado de secuencias y,
más recientemente, LLM [@khaouja2021survey; @senger2024deep]. La evaluación estándar compara contra avisos anotados a
mano con una guía y con acuerdo entre anotadores [@zhang2022skillspan]. Los estudios que comparan LLM con otros métodos
reportan resultados mixtos: el aprendizaje en contexto frente al etiquetado supervisado [@nguyen2024rethinking], el
acuerdo y el no determinismo de herramientas basadas en LLM frente a expertos [@kavargyris2026have] y la comparación
entre codificadores y LLM [@matkin2026comparative]. En analítica curricular, un LLM sin contexto rindió peor que los
métodos tradicionales en la mayoría de los casos, mientras que la generación aumentada por recuperación fue la mejor
estrategia [@xu2025from]; además, los datos sintéticos o las etiquetas incompletas inflan las métricas
[@veys2026surface; @nkrumah2025skill].

Sin etiquetado manual, Ao et al. [@ao2023skill] proponen medir qué proporción de la variación salarial explican las habilidades
extraídas: los diccionarios explican cerca del 20 %, y los modelos de tópicos más, a costa de la interpretabilidad. Otra
línea detecta habilidades nuevas y las enlaza con ESCO con revisión humana [@desanto2026skillens; @desanto2026using]. En
el dominio de los roles de datos se han comparado perfiles de inteligencia de negocios, analistas y científicos de datos
[@debortoli2014comparing; @verma2019investigation; @smaldone2022employability;
@zhang2023investigation], y Nakash y Peretz [@nakash2025decoding] clasifican carreras de inteligencia artificial a partir de los avisos.

## C. Habilidades y salarios {-}

El valor de una habilidad depende de con cuáles se combina [@stephany2024what], lo que justifica analizar el rol, como
conjunto de habilidades, además de la habilidad aislada. En avisos de científicos y analistas de datos,
Zhong et al. [@zhong2023feature] tratan el salario como un intervalo y encuentran que términos como Excel, Office o recolección de
datos se asocian negativamente con el salario. Otros trabajos estiman primas por habilidades digitales
[@garcialazaro2025digital] o de inteligencia artificial [@alekseeva2021demand], y muestran que obtener primas
concluyentes desde avisos depende del tamaño de la muestra y de cómo se mida el salario [@camposgonzalez2025impact;
@bone2025skills].

## D. Alucinación, anclaje y verificación {-}

Los LLM producen afirmaciones sin respaldo [@ji2023survey; @rawte2023troubling] e inventan citas con frecuencia
[@mcgowan2023chatgpt; @buchanan2024chatgpt], y su confiabilidad disminuye a medida que la pregunta es más específica
[@buchanan2024chatgpt]. La generación anclada en documentos recuperados [@lewis2020retrieval] reduce el problema, pero no
lo elimina [@iaroshev2024evaluating]. Para verificar, FActScore descompone el texto en afirmaciones atómicas y comprueba
cada una contra la fuente [@min2023factscore]; otros enfoques usan la incertidumbre del propio modelo
[@farquhar2024detecting] o verifican la semántica de la respuesta después de generarla [@martin2024semantic]. Como verificar contra tablas es difícil para los propios LLM [@lu2023scitab], este trabajo
verifica las cifras con reglas deterministas fuera del modelo.

## E. Ciencia del diseño, currículo con inteligencia artificial y posicionamiento {-}

La investigación en ciencia del diseño (DSR, *design science research*) ofrece el marco para construir y evaluar
artefactos [@hevner2004design; @peffers2007design]. Hay precedentes con LLM en informes financieros
[@iaroshev2024evaluating; @li2025extracting], en la adquisición de conocimiento de procesos con evaluación en tres rondas
[@schinckus2026large] y en la validación de datos con expertos [@dormehl2026domain]. En el diseño curricular con
inteligencia artificial se han estudiado el humano en el ciclo [@lusi2026augmented; @brown2025toward],
la comparación de versiones de ChatGPT con rúbrica de expertos [@genc2026comparative] y la analítica que cruza oferta y
demanda de habilidades [@varpina2026enabled]. El caso más cercano es Jēkabsone et al. [@jekabsone2026bridging], que cruza avisos, ESCO, el
currículo y entrevistas para proponer microcredenciales; Kapa y Schaefer [@kapa2026reproducible] describen un flujo reproducible de
avisos con validación externa. El scraping con fines de investigación tiene además riesgos legales y éticos que deben
gestionarse [@krotov2020tutorial; @luscombe2022algorithmic; @brown2025scraping].

Frente a estos trabajos, el presente estudio aporta: (a) una verificación determinista de cada cifra que produce el LLM
contra un contexto versionado; (b) una evaluación cuantitativa del efecto del anclaje, con y sin datos y con y sin reglas
de evidencia; (c) un criterio de «concluyente» y una prueba de equivalencia fijados antes de interpretar los
resultados, de modo que el sistema declara cuándo no hay evidencia; y (d) datos mensuales de un mercado
latinoamericano.

# III. METODOLOGÍA {-}

## A. Diseño de la investigación {-}

El estudio sigue la metodología DSR [@hevner2004design; @peffers2007design] en seis actividades: identificación del
problema, definición de objetivos, diseño y desarrollo, demostración, evaluación y comunicación. Los objetivos del
artefacto se expresaron como siete requisitos de diseño: R1, trazabilidad (toda cifra publicada se reconstruye desde los
datos crudos guardados); R2, inmutabilidad del histórico; R3, incertidumbre explícita (intervalos de confianza,
corrección por comparaciones múltiples, un criterio de «concluyente» fijado de antemano y una prueba de equivalencia);
R4, anclaje (el LLM solo recibe cifras del contexto versionado); R5, verificación independiente del modelo; R6, decisión
humana; y R7, reproducibilidad (código público, semillas y cortes fechados). La evaluación se organizó en tres rondas,
siguiendo a Schinckus et al. [@schinckus2026large] (Tabla I).

::: {custom-style="Table Caption"}
TABLA I\
RONDAS DE EVALUACIÓN DEL ARTEFACTO
:::

| Ronda | Qué se evalúa | Evaluaciones |
|---|---|---|
| Automática | Componentes por separado | E3, poder explicativo de la taxonomía; E5, efecto del anclaje |
| Humana | Contra una referencia construida a mano | E1 y E2, extracción y rol; E6, línea base con LLM; E4, verificador |
| Caso real | Funcionamiento sostenido | E7, cortes mensuales de septiembre a noviembre de 2026 |

Fuente: elaboración propia.

## B. El artefacto {-}

La Fig. 1 resume la arquitectura. La **recolección** se dispara cada mes de forma automática desde siete fuentes:
CompuTrabajo, ElEmpleo, GetOnBoard, LinkedIn, Talent.com, Magneto y Remotive (esta última mediante su interfaz pública,
con atribución). Antes de cada escritura se genera un respaldo cifrado, y los cambios en el diseño de búsqueda quedan
registrados para excluirlos de las comparaciones entre meses.

La **limpieza y extracción** usa reglas explícitas: un filtro de relevancia temática por título; la normalización del
salario a pesos colombianos (COP) mensuales, tomando el punto medio cuando el aviso publica un rango; una taxonomía de
31 habilidades con expresiones regulares; la experiencia y el nivel solo cuando el aviso los declara, con la fuente de
cada dato; y el rol por reglas sobre el título normalizado, con la categoría «sin clasificar» cuando ninguna regla
aplica. El **almacenamiento** usa PostgreSQL con tablas de solo inserción protegidas por disparadores, índices únicos
por huella del aviso y mes, y un rol de mínimo privilegio para el proceso automático. El texto crudo de cada aviso se
conserva para recalcular con reglas nuevas sin volver a recolectar.

El **análisis estadístico** calcula la demanda como porcentaje de ofertas que piden cada habilidad. Las primas
salariales se estiman por mínimos cuadrados ordinarios según (1):

$$\log(\mathrm{salario}_i) = \beta_0 + \sum_{h} \beta_h H_{ih} + \gamma' \mathbf{x}_i + \varepsilon_i \qquad (1)$$

donde $H_{ih}$ vale 1 si el aviso $i$ pide la habilidad $h$ y $\mathbf{x}_i$ agrupa el nivel, el rol, el portal y el mes.
Los errores estándar son robustos (HC3), y las categorías de control con menos de cinco ofertas se agrupan, porque una
variable indicadora de una sola observación anula la matriz HC3. La prima es $\exp(\beta_h) - 1$, con intervalo de
confianza (IC) del 95 % y valor $q$ de Benjamini–Hochberg. Una prima es «concluyente» si $q \le 0{,}10$ y su IC no
incluye el cero; solo se evalúan habilidades pedidas en al menos 20 ofertas con salario. Para distinguir «sin prima
relevante» de «no concluyente» se aplicó una prueba de equivalencia de dos pruebas unilaterales (TOST)
[@lakens2017equivalence; @hartman2018equivalence]. El margen se fijó en ±15 % por un criterio sustantivo
[@lakens2018equivalence]: una diferencia salarial asociada menor no justificaría reordenar el peso de una habilidad en
un plan de estudios. Una habilidad es equivalente si su IC del 90 % cae completo dentro del margen, y para cada una se
reporta además el margen mínimo con el que lo sería [@fitzgerald2026need].

El **contexto de mercado** es un documento versionado, con identificador y fecha de corte, que contiene la demanda, los
roles, las primas con su estado (concluyente o no), las medianas salariales con su n y el cruce entre las habilidades
del mercado y las que ya enseñan los programas de UniCafam. Se entrega al modelo (Gemini 4 Argon, con Gemini 3.8 Flash
como respaldo) junto con reglas de evidencia: copiar las cifras tal cual, responder «dato no disponible» cuando falten,
no proyectar salarios y no hablar de tendencias con menos de tres cortes.

El **verificador de cifras** extrae los porcentajes, montos y conteos de ofertas del texto generado, busca cada cifra en
el contexto, comprueba que la habilidad o el rol mencionado junto a la cifra sea el dueño del dato, revisa la
consistencia entre créditos académicos y horas (1 crédito = 48 horas) y marca siempre las tarifas. El verificador marca,
pero no bloquea: en un **portal de revisión**, una persona con rol de aprobador de la institución ve cada marca con su
motivo y decide aprobar, rechazar o pedir un ajuste, que genera una nueva versión. Cada acción queda auditada.

![Fig. 1: Arquitectura del observatorio. Las evaluaciones se ubican sobre los componentes: E1, E2 y E6 sobre la
extracción; E3 sobre el análisis; E4 y E5 sobre la generación y la verificación; E7 sobre el ciclo mensual
completo.](figuras/arquitectura.png){width=100%}

Fuente: elaboración propia.

## C. Datos {-}

Se usaron los tres primeros cortes mensuales (septiembre, octubre y noviembre de 2026; corte vigente del 1 de noviembre
de 2026), con 907 avisos únicos, de los cuales 905 conservan el texto crudo; los análisis que recalculan desde el texto
usan estos 905 (Tabla II). Las primas salariales se estimaron con los 176 avisos del mercado local que publican salario.
Octubre acumula varias corridas de recolección y noviembre una sola, por lo que el número de ofertas no se compara entre
esos meses.

::: {custom-style="Table Caption"}
TABLA II\
OFERTAS POR FUENTE Y CORTE
:::

| Fuente | Mercado | Sep. 2026 | Oct. 2026 | Nov. 2026 | Únicas sep.–nov. |
|---|---|---|---|---|---|
| LinkedIn | Local | 146 | 247 | 169 | 435 |
| ElEmpleo | Local | 74 | 93 | 68 | 145 |
| Talent.com | Local | 36 | 99 | 43 | 140 |
| Magneto | Local | 0 | 89 | 62 | 94 |
| CompuTrabajo | Local | 15 | 23 | 15 | 37 |
| GetOnBoard | Remoto | 23 | 26 | 23 | 34 |
| Remotive | Remoto | 0 | 2 | 2 | 2 |
| Torre.ai | Remoto | 20 | 0 | 0 | 20 |
| **Total** | | **314** | **579** | **382** | **907** |
| Con salario publicado | | 70 | 146 | 105 | |

Fuente: elaboración propia. Una oferta vigente en varios meses cuenta en cada mes. Magneto y Remotive se incorporaron en
octubre; Torre.ai se desactivó. LinkedIn amplió sus términos de búsqueda el 17 de octubre de 2026.

## D. Procedimientos de evaluación {-}

**E1 y E2, extracción y rol frente a una referencia humana.** Se extrajo una muestra de 200 avisos estratificada por
portal y mes (semilla 2026). Un anotador etiquetó los 200 y un segundo anotador, independiente, 60 de ellos para medir el
acuerdo ($\kappa$ de Cohen), sin ver la salida del sistema, con una guía con casos difíciles y con correos y teléfonos
enmascarados. Los desacuerdos de la submuestra doble se adjudicaron con la guía. [PENDIENTE: adjudicación en curso; hasta entonces la referencia es la del anotador principal.] Se aplicó una única regla de
consistencia derivada de la guía: si se marca «Excel avanzado» explícito, se marca también Excel a cualquier nivel (8
avisos del primer anotador). Se
calcularon precisión, exhaustividad y F1 por habilidad (micro y macro), exactitud y F1 macro del rol, y exactitud del
nivel y de los años de experiencia, con IC por remuestreo (*bootstrap*) de 2000 réplicas. En E2 se compararon dos
versiones del clasificador de rol: la publicada y una corregida, cuyas reglas se ajustaron solo con los 705 avisos fuera
de la muestra.

**E3, poder explicativo de la taxonomía.** Siguiendo a Ao et al. [@ao2023skill], se midió la proporción de la variación del
logaritmo del salario que explican las habilidades extraídas, dentro y fuera de muestra (validación cruzada de 5
particiones repetida 50 veces), frente a los controles y frente al texto completo representado con TF-IDF.

**E4, precisión y exhaustividad del verificador.** Las cifras de las propuestas generadas en E5 se descompusieron en
afirmaciones atómicas [@min2023factscore] y se extrajo una muestra estratificada de 174: todas las marcadas (54), 80
revisadas sin marca y 40 números que el verificador no revisa. Se etiquetaron a ciegas frente a la condición y al
modelo, en cuatro categorías: respaldada, mal atribuida, sin respaldo y no verificable. Las métricas se ponderan por
estrato, con IC por remuestreo estratificado. No se usaron las propuestas con las que se ajustó el verificador, para no
evaluar dentro de la muestra de ajuste.

**E5, efecto del anclaje y del modelo.** Se generaron 36 propuestas curriculares: tres condiciones × dos modelos
(Gemini 4 Argon y Gemini 3.8 Flash) × dos solicitudes de UniCafam (un diplomado de 8 créditos en ingeniería de datos en
la nube y una microcredencial de 2 créditos sin enfoque definido) × tres repeticiones, sin modelo de respaldo. Las
condiciones fueron: *con contexto* (el prompt de producción); *sin datos, con reglas* (sin el bloque de datos, pero con
las instrucciones de evidencia); y *sin anclaje* (sin datos, sin reglas y con ejemplos neutros). Todas se verificaron
contra el mismo contexto. Para la tasa de cifras marcadas se reportan IC exactos de Clopper–Pearson, que tratan las
cifras como independientes; dado que las cifras de una misma generación pueden estar correlacionadas, se reporta también
un IC por remuestreo de generaciones.

**E6, línea base con LLM.** Un LLM (Gemini 4 Argon, temperatura 0) recibió la misma guía y los mismos textos
enmascarados que los anotadores, y se comparó con la misma referencia de E1.

**E7, caso real.** Se documentó la operación de los tres cortes mensuales y los fallos detectados y corregidos durante
la operación.

## E. Consideraciones éticas {-}

El estudio no involucró participantes humanos ni intervenciones. Se usaron avisos de empleo de acceso público; los
correos y teléfonos presentes en el texto se enmascararon antes de la anotación y de cualquier envío a servicios
externos, y el texto crudo no se publica, en atención a la Ley 1581 de 2012 de protección de datos personales. La
recolección respetó las restricciones de los portales: se descartaron fuentes que la prohíben en su archivo robots.txt y
se atribuye la fuente que lo exige. Por estas características, UniCafam no exigió el aval de un comité de ética.

# IV. RESULTADOS, ANÁLISIS E INTERPRETACIÓN {-}

## A. Extracción y rol (E1, E2 y E6) {-}

El acuerdo entre anotadores en los 60 avisos de la submuestra doble fue sustancial: $\kappa$ = 0,75 en el rol (80 % de
coincidencia), 0,73 en el nivel (78 %) y 0,90 en promedio en las habilidades; en los años de experiencia, ambos
anotadores coincidieron en si el aviso los declaraba en el 88 % de los casos y en el valor exacto en el 90 % de los que
ambos registraron.

La Tabla III compara el sistema de reglas con el LLM sobre la misma referencia. Las reglas extrajeron las 31 habilidades
con un F1 micro de 0,849 (precisión 0,804 y exhaustividad 0,900); el LLM obtuvo 0,879, una diferencia pequeña pero
concluyente (+0,029 [0,016; 0,041]) que se debe sobre todo a una mayor exhaustividad. En el rol no hubo diferencia
concluyente (0,785 frente a 0,805). El LLM fue claramente mejor en el nivel del cargo (+0,095) y, sobre todo, en detectar
los años de experiencia cuando el aviso los declara (0,849 frente a 0,599), con una precisión similar: las reglas casi
nunca inventan años (3 de 200 avisos), pero omiten muchas formas de expresarlos. El filtro de relevancia fue casi
perfecto con ambos métodos. El LLM tardó una mediana de 7,8 s por aviso; las reglas, milisegundos.

::: {custom-style="Table Caption"}
TABLA III\
EXTRACCIÓN FRENTE A LA REFERENCIA HUMANA: REGLAS Y LLM (N = 200)
:::

| Tarea | Métrica | Reglas | LLM | Diferencia [IC 95 % pareado] |
|---|---|---|---|---|
| Habilidades (31) | F1 micro | 0,849 | 0,879 | +0,029 [+0,016; +0,041] |
| | Precisión / exhaustividad | 0,804 / 0,900 | 0,812 / 0,958 | — |
| Rol (8 categorías) | Exactitud | 0,785 | 0,805 | +0,020 [−0,035; +0,080] |
| | F1 macro | 0,615 | 0,675 | — |
| Nivel del cargo | Exactitud | 0,685 | 0,780 | +0,095 [+0,020; +0,170] |
| Años de experiencia | Detección (exhaustividad) | 0,599 | 0,849 | +0,250 [+0,178; +0,322] |
| | Precisión de la detección | 0,968 | 0,963 | — |
| Relevancia temática | F1 | 0,982 | 0,987 | — |

Fuente: elaboración propia. LLM: Gemini 4 Argon, temperatura 0, con la guía de anotación. IC por remuestreo pareado de
avisos (2000 réplicas). Referencia: anotador principal [PENDIENTE: con la submuestra doble adjudicada].

En E2, el clasificador de rol corregido superó al publicado: la exactitud subió de 0,590 [0,525; 0,655] a 0,785
[0,725; 0,840], una mejora de 0,195 [0,140; 0,250], y el F1 macro pasó de 0,418 a 0,615. La versión publicada clasificaba
por subcadenas, de modo que «ia» o «bi» dentro de otras palabras activaban roles equivocados; la corregida cambió de rol
a 63 de los 200 avisos (y a 230 de los 705 avisos fuera de la muestra, que fueron los únicos usados para ajustarla). Por
eso, las primas por rol de la sección IV.D se estiman con el clasificador corregido.

## B. Poder explicativo de la taxonomía (E3) {-}

Las 31 habilidades explican dentro de muestra el 28,7 % de la variación del logaritmo del salario, una proporción
comparable al 20 % de los diccionarios estudiados por Ao et al. [@ao2023skill], pero fuera de muestra no mejoran a los controles: su
aporte es de −0,048 [−0,248; 0,100] (Tabla IV). El texto completo explica más que la taxonomía, lo que sugiere que esta
no capta información como el nivel educativo, el nivel del cargo y el sector. Con los roles corregidos, los controles
explican más fuera de muestra (0,485 frente a 0,431), una evidencia indirecta a favor del clasificador corregido.

::: {custom-style="Table Caption"}
TABLA IV\
PROPORCIÓN DE LA VARIANZA DEL LOGARITMO DEL SALARIO EXPLICADA (N = 176)
:::

| Modelo | R² dentro de muestra | R² fuera de muestra [P2,5; P97,5] |
|---|---|---|
| Controles (nivel, rol, portal, mes) | 0,604 | 0,485 [0,246; 0,680] |
| Habilidades | 0,287 | 0,115 [−0,176; 0,312] |
| Controles + habilidades | 0,670 | 0,438 [0,141; 0,626] |
| Texto completo (TF-IDF) | — | 0,509 [0,264; 0,699] |
| Controles + texto | — | 0,570 [0,281; 0,725] |

Fuente: elaboración propia. Fuera de muestra: validación cruzada 5 × 50 con regresión *ridge* para las habilidades y el
texto; dentro de muestra: mínimos cuadrados ordinarios. Ofertas locales con salario, septiembre a noviembre de 2026.

## C. Efecto del anclaje (E5) y desempeño del verificador (E4) {-}

Las 36 generaciones se completaron sin fallos. Con el contexto de mercado, los modelos citaron entre 6 y 20 veces más
cifras de mercado que en las otras condiciones, y el verificador marcó el 0,7 % de las cifras revisadas con Gemini 4
Argon y ninguna con Gemini 3.8 Flash (Tabla V). Sin datos pero con reglas de evidencia, ambos modelos se abstuvieron de
escribir cifras de mercado y respondieron «dato no disponible». Sin anclaje, el verificador marcó entre el 93,8 % y el
100 % de las cifras. Los intervalos de las condiciones con y sin anclaje no se solapan con ninguno de los dos métodos.
No hubo inconsistencias entre créditos y horas en ninguna generación. La mediana del tiempo de generación con contexto
fue de 69 s con Argon y de 33 s con Flash.

::: {custom-style="Table Caption"}
TABLA V\
CIFRAS MARCADAS POR EL VERIFICADOR SEGÚN CONDICIÓN Y MODELO (36 GENERACIONES)
:::

| Condición | Modelo | Cifras revisadas | Marcadas | % marcadas | IC 95 % exacto | IC 95 % por generación |
|---|---|---|---|---|---|---|
| Con contexto | Argon | 410 | 3 | 0,7 | [0,2; 2,1] | [0,0; 2,0] |
| Con contexto | Flash | 197 | 0 | 0,0 | [0,0; 1,9] | — |
| Sin datos, con reglas | Argon | 0 | 0 | — | — | — |
| Sin datos, con reglas | Flash | 0 | 0 | — | — | — |
| Sin anclaje | Argon | 21 | 21 | 100 | [83,9; 100] | — |
| Sin anclaje | Flash | 32 | 30 | 93,8 | [79,2; 99,2] | [83,3; 100] |

Fuente: elaboración propia. Seis generaciones por celda. IC exacto: Clopper–Pearson por cifra. IC por generación:
remuestreo de generaciones, no definido cuando todas las cifras coinciden. Contexto de mercado del corte del 1 de
noviembre de 2026.

[PENDIENTE: E4. Proporción de cifras sin respaldo o mal atribuidas en cada estrato, precisión y exhaustividad ponderadas
del verificador, y qué fracción de las cifras «sin anclaje» es inventada y cuál es externa pero verificable.]

## D. Hallazgos sobre el mercado de roles de datos (E7) {-}

En noviembre de 2026 (n = 382), las habilidades más pedidas fueron SQL (68,1 % de las ofertas), Python (63,9 %), ETL
(51,6 %), Power BI (32,2 %) y estadística (31,4 %). Con 176 ofertas locales con salario y frente al rol de analista de
datos, controlando nivel, portal y mes, las primas de ingeniero de datos (+69,5 % [+44,6; +98,8]; n = 39) y de
científico de datos (+52,1 % [+30,4; +77,4]; n = 44) fueron concluyentes (Tabla VI). Inteligencia de negocios (n = 7) y
los roles con menos de 20 ofertas no fueron evaluables.

::: {custom-style="Table Caption"}
TABLA VI\
PRIMAS SALARIALES POR ROL FRENTE A ANALISTA DE DATOS
:::

| Rol | n | Prima [IC 95 %] | Lectura |
|---|---|---|---|
| Ingeniero de datos | 39 | +69,5 % [+44,6; +98,8] | Concluyente |
| Científico de datos | 44 | +52,1 % [+30,4; +77,4] | Concluyente |
| Inteligencia de negocios | 7 | — | No evaluable (n < 20) |
| Sin clasificar | 22 | — | Fuera del modelo |

Fuente: elaboración propia. Mínimos cuadrados ordinarios sobre el logaritmo del salario con errores HC3, controlando
nivel, portal y mes. Ofertas locales con salario, septiembre a noviembre de 2026. Clasificador de rol corregido
(E2).

Ninguna prima por habilidad fue concluyente. La asociación negativa de Excel, que el portal había publicado como
concluyente con la versión anterior del clasificador de rol (−17,0 % [−27,1; −5,5]; $q$ = 0,052), dejó de serlo al
corregir el rol (−12,5 % [−24,2; +1,1]; $q$ = 0,56): parte de la asociación se debía a la composición de roles. El
resultado se mantuvo al usar el extremo inferior o superior del rango salarial, al controlar el nivel educativo y el
sector, y al excluir los duplicados entre portales (Tabla VII). Se estimaron 43 pares de avisos duplicados entre
portales, con 36 avisos sobrantes (4,0 %), casi todos entre LinkedIn y Talent.com.

::: {custom-style="Table Caption"}
TABLA VII\
ROBUSTEZ DE LAS PRIMAS POR HABILIDAD
:::

| Especificación | R² | Prima de Excel [IC 95 %] | Habilidades concluyentes |
|---|---|---|---|
| Base (punto medio del rango) | 0,564 | −12,5 % [−24,2; +1,1] | Ninguna |
| Extremo inferior del rango | 0,554 | −12,4 % [−24,2; +1,2] | Ninguna |
| Extremo superior del rango | 0,577 | −12,6 % [−24,3; +1,1] | Ninguna |
| + nivel educativo | 0,644 | −8,0 % [−20,1; +5,9] | Ninguna |
| + nivel educativo + sector | 0,658 | −8,9 % [−21,0; +5,1] | Ninguna |
| Sin duplicados entre portales | 0,571 | −14,2 % [−25,5; −1,3] | Ninguna |

Fuente: elaboración propia. n = 176 (175 sin duplicados); 87 ofertas publican el salario como rango.

La prueba de equivalencia solo ubicó a SQL dentro del margen de ±15 %: −0,2 %, IC 90 % [−11,4; +12,5], $p$ = 0,025, un
resultado que se mantuvo en las cinco especificaciones de robustez, pero no al corregir por las 11 habilidades evaluadas
($q$ = 0,27). Las demás habilidades fueron no concluyentes también en este sentido: los datos no permiten afirmar que
tengan prima ni que no la tengan. Los márgenes mínimos de equivalencia fueron de ±12,5 % (SQL) a ±37,9 % (Azure), de modo
que, con 176 ofertas, ningún margen menor de un 12 % habría permitido declarar equivalencia.

No hubo cambios concluyentes en la composición de roles entre meses: de septiembre a octubre, con portales comparables
(n = 146 y 241), el mayor cambio fue el de ingeniero de datos, de 17,8 % a 24,1 % ($q$ = 0,37); de octubre a noviembre
(n = 579 y 382), ningún rol cambió más de 2,1 puntos porcentuales ($q$ = 0,99). Al incluir LinkedIn, cuyo diseño de
búsqueda cambió en octubre, aparecía un falso aumento de ingenieros de datos, lo que ilustra por qué el sistema registra
los cambios de diseño. Durante la operación, la propia evaluación detectó y corrigió cuatro fallos: una caché de 30 días
en el tablero, un error de autenticación por credenciales truncadas, la clasificación de rol por subcadenas y la
degeneración de la matriz de covarianza HC3.

## E. Discusión {-}

**Anclaje y verificación (PI2 y PI3).** Los resultados de E5 indican que el anclaje cumple dos funciones distintas. Las
reglas de evidencia, por sí solas, bastan para que el modelo se abstenga de inventar cifras de mercado, pero no producen
evidencia; el contexto versionado es lo que permite que la propuesta contenga cifras, y casi todas quedan respaldadas.
Sin anclaje, casi ninguna cifra tiene respaldo en el observatorio, en línea con lo reportado sobre citas inexistentes en
economía [@buchanan2024chatgpt] y con el peor desempeño de las preguntas cuantitativas en sistemas con recuperación
[@iaroshev2024evaluating]. A diferencia de los enfoques que verifican con el propio modelo [@farquhar2024detecting], el
verificador es determinista, y su resultado no depende del modelo que se evalúa. [PENDIENTE: qué atrapa el verificador y
qué no (E4), por ejemplo cifras calculadas o redondeadas y números fuera de sus patrones.]

**Reglas frente a LLM en la extracción (PI1).** Con la misma guía, el LLM extrajo mejor que las reglas, pero la ventaja
depende de la tarea: es pequeña en las habilidades (3 puntos de F1), nula en el rol y grande en los años de experiencia,
donde la variedad de redacciones supera a cualquier lista de patrones. El resultado matiza lo reportado por Nguyen et al.
[@nguyen2024rethinking], que encontraron a los LLM por debajo del etiquetado supervisado en la extracción de habilidades, y
es coherente con Xu et al. [@xu2025from], para quienes el desempeño de los LLM depende de la estrategia de uso: aquí el
modelo recibió una guía detallada y una lista cerrada de 31 habilidades, una tarea más acotada que la extracción abierta.
Para un observatorio, la decisión no es solo de exactitud: las reglas son deterministas, auditables, gratuitas y
reproducibles mes a mes, mientras que el LLM tarda segundos por aviso, cambia con cada versión del modelo y debe
volver a validarse. Una arquitectura híbrida, con reglas para las habilidades y el rol y el LLM solo para los años de
experiencia, conservaría la auditabilidad donde la ventaja del modelo es pequeña.

**El observatorio como medidor honesto (PI4).** Con 176 ofertas con salario casi ninguna prima por habilidad es
concluyente, y el sistema lo declara en lugar de reportar estimaciones puntuales. Esto coincide con la dificultad que
documenta la literatura de primas desde avisos [@zhong2023feature; @camposgonzalez2025impact]. El caso de Excel muestra
por qué: una asociación publicada como concluyente desapareció al corregir el clasificador de rol, y la prueba de
equivalencia muestra que el límite actual es la precisión y no el método. Que la taxonomía no mejore la predicción fuera
de muestra (E3) coincide con la tensión entre interpretabilidad y poder explicativo que señalan Ao et al. [@ao2023skill], y con la
advertencia de Suárez-Rodríguez et al. [@suarezrodriguez2026semantic] sobre las taxonomías fijas. Dos de los fallos corregidos durante la
operación, la clasificación de rol por subcadenas y la covarianza degenerada, se detectaron al preparar la evaluación
del propio artefacto, lo que ilustra el ciclo de construcción y evaluación de DSR [@hevner2004design].

**Limitaciones.** Los avisos en línea no son representativos del mercado y dependen de los términos de búsqueda
[@kurekova2015using; @lovaglio2026analyzing]. Tres cortes no constituyen una tendencia. Solo el 27,5 % de las ofertas de
noviembre publica salario, casi todas de tres portales locales, y los rangos se toman en su punto medio, aunque los
extremos no cambian las conclusiones [@zhong2023feature]. Los duplicados entre portales (4,0 %) no se eliminan en el
flujo de datos [@zhao2021framework]. La taxonomía es fija frente a una terminología que cambia
[@suarezrodriguez2026semantic; @desanto2026skillens], y el rol se infiere del título. Las primas son asociaciones, no
efectos causales. Los LLM no son deterministas, y el verificador solo cubre porcentajes, montos y conteos de ofertas. Las
36 generaciones de E5 dan seis repeticiones por celda. El margen de equivalencia se fijó antes de calcular la prueba,
pero cuando las estimaciones puntuales ya eran públicas, por lo que no es un margen prerregistrado en sentido estricto;
por eso se reportan también los márgenes mínimos. La referencia de extracción proviene de un anotador principal, con
un segundo anotador en el 30 % de los avisos; el acuerdo fue sustancial, pero no perfecto, y el anotador principal es
también el autor del sistema, aunque anotó sin ver su salida. El LLM de E6 se evaluó con un solo modelo y una sola
ejecución.

# V. CONCLUSIONES {-}

[PENDIENTE: completar con E4.]

Este trabajo diseñó y evaluó un observatorio auditable del mercado laboral en roles de datos que integra inteligencia
artificial generativa anclada en evidencia. Anclar el modelo en un contexto de mercado versionado y verificar sus cifras
con reglas deterministas redujo las cifras sin respaldo de casi todas a casi ninguna, y las reglas de evidencia por sí
solas llevaron al modelo a abstenerse en lugar de inventar. En la extracción, las reglas alcanzaron un desempeño
cercano al de un LLM con la misma guía en las habilidades y el rol, con la ventaja de ser auditables y reproducibles; el
LLM fue superior en los años de experiencia. La evaluación también corrigió el propio sistema: el clasificador de rol
publicado tenía una exactitud de 0,59 y el corregido, de 0,79. En el plano analítico, el observatorio identificó primas
concluyentes por rol, pero no por habilidad, y lo declaró explícitamente, junto con la única habilidad cuya ausencia de
prima relevante tiene indicios.

# VI. RECOMENDACIONES {-}

Para las instituciones que usen LLM en el diseño curricular: (a) entregar al modelo las cifras del mercado como un
contexto versionado, con su tamaño de muestra y su fecha de corte, en lugar de pedirle que las recuerde; (b) verificar
cada cifra generada con reglas independientes del modelo y mostrar las marcas a quien aprueba; y (c) mantener la
aprobación humana como requisito, no como opción.

Para quienes construyan observatorios con avisos de empleo: (a) conservar el texto crudo para recalcular con reglas
nuevas; (b) registrar los cambios en el diseño de búsqueda y excluirlos de las comparaciones entre meses; y (c) reportar
cada estimación con su intervalo, su corrección por comparaciones múltiples y, cuando se quiera afirmar la ausencia de
efecto, una prueba de equivalencia.

Como trabajo futuro se proponen una taxonomía alineada con ESCO y la detección de términos nuevos
[@desanto2026skillens; @desanto2026using]; el análisis de la complementariedad de habilidades [@stephany2024what]; la
validación externa con estadística oficial [@beresewicz2021enhancing; @lovaglio2026analyzing]; la regresión por
intervalos para el salario [@zhong2023feature]; la deduplicación dentro del flujo de datos; y una prueba de
equivalencia con un margen prerregistrado y más ofertas.

# VII. AGRADECIMIENTOS O FINANCIAMIENTO {-}

Esta investigación se realizó con recursos propios del autor y no recibió financiación de entidades públicas,
comerciales o sin ánimo de lucro. El autor agradece a José Isaias Sala Hernandez, director del Semillero de
Investigación Codex de UniCafam, quien propuso la idea de este proyecto y lo ha acompañado durante todo el proceso, y a
la persona que actuó como segunda anotadora en la construcción de la referencia de evaluación. [PENDIENTE: nombre del
segundo anotador, si autoriza mencionarlo.]

**Contribución de autoría (CRediT).** Juan Felipe Bernal Peña: conceptualización, curación de datos, análisis formal,
investigación, metodología, software, visualización, redacción del borrador original y redacción, revisión y edición.

**Conflicto de intereses.** El autor declara que no existen conflictos de intereses relacionados con este trabajo.

**Disponibilidad de datos y código.** El código del observatorio, los scripts de evaluación y los resultados agregados
están disponibles en <https://github.com/jfbernalp/proyecto_investigativo> [PENDIENTE: versión evaluada]. Los
indicadores públicos se pueden consultar en <https://jfbernalp.dev>. El texto completo de los avisos no se publica
porque contiene datos de terceros y está sujeto a los términos de uso de los portales.

**Uso de inteligencia artificial generativa.** Gemini 4 Argon y Gemini 3.8 Flash (Google) forman parte del artefacto
evaluado y se usaron en las evaluaciones E5 y E6. El autor utilizó Claude (Anthropic) como asistente de programación,
análisis y redacción de borradores; todas las cifras provienen de scripts reproducibles del repositorio y fueron
verificadas por el autor, y las referencias se verificaron contra los registros de Crossref y DataCite. Scopus AI se
usó solo para orientar la búsqueda bibliográfica, no como fuente. El autor asume plena responsabilidad por el
contenido.

# VIII. REFERENCIAS {-}

::: {#refs}
:::
