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

**Resumen**--- **Antecedentes:** las instituciones de educación superior deben ajustar sus programas en datos a un
mercado laboral cambiante, y los modelos de lenguaje propuestos para el diseño curricular producen cifras sin respaldo. **Objetivo:** diseñar y evaluar un observatorio auditable del mercado laboral en roles de
datos que integra inteligencia artificial generativa anclada en evidencia, desarrollado para la actualización curricular
de la Fundación Universitaria Cafam. **Métodos:** siguiendo la investigación en ciencia del diseño, se construyó un
sistema que recolecta cada mes avisos de portales de empleo, extrae habilidades, rol y experiencia con reglas
explícitas, estima la demanda y las primas salariales con intervalos de confianza y pruebas de equivalencia, y entrega a un modelo de lenguaje un contexto de mercado versionado como única
fuente de cifras; un verificador determinista revisa los porcentajes, montos y conteos generados y una persona aprueba cada propuesta. La
evaluación usó 472 avisos únicos de siete fuentes, de septiembre a noviembre de 2026, y 36 generaciones
controladas.
**Resultados:** con contexto, el verificador marcó entre 0 % y 0,7 % de las cifras revisadas; sin
anclaje, entre 93,8 % y 100 %. Sus marcas tuvieron una precisión de 0,91, y su
exhaustividad estimada fue de 0,74 [0,32; 0,98]. Frente a 105 avisos anotados, las reglas alcanzaron un F1 de 0,85 en
habilidades y una exactitud de 0,75 en el rol; un modelo de lenguaje con la misma guía obtuvo 0,89 y 0,80. Con 176 ofertas con salario, las primas de los roles de ingeniería y ciencia de datos frente
al analista fueron concluyentes, mientras que ninguna prima por habilidad lo fue. **Conclusión:** en condiciones controladas, el contexto
versionado se asoció con muchas menos cifras sin respaldo; esto respalda la factibilidad técnica del enfoque, no su
efecto sobre decisiones curriculares. Declarar la ausencia de evidencia es una función central del observatorio.

**Palabras clave:** ciencia de datos, diseño curricular, educación superior, inteligencia artificial, mercado de trabajo,
oferta de empleo, verificación de datos.

**Abstract**--- **Background:** higher education institutions must align their data programs with a changing labor
market, and the language models proposed for curriculum design produce unsupported figures.
**Objective:** to design and evaluate an auditable observatory of the labor market for data roles that integrates
evidence-grounded generative artificial intelligence, developed for curriculum updating at Fundación Universitaria
Cafam, Colombia. **Methods:** following design science research, we built a system that collects job postings monthly
from online job boards, extracts skills, role and experience with explicit rules, estimates demand and wage premiums with
confidence intervals and equivalence tests, and provides a language model with a
versioned market context as its only source of figures; a deterministic verifier checks the generated percentages,
amounts and counts, and a person approves each proposal. The evaluation used 472 unique postings from seven sources, from September to
November 2026, and 36 controlled generations. **Results:** with the market context, the verifier flagged between 0% and 0.7% of the
checked figures; without grounding, between 93.8% and 100%. Its flags had a precision of 0.91, and its estimated recall
was 0.74 [0.32, 0.98]. Against 105 hand-annotated postings, the rules reached an
F1 of 0.85 for skills and an accuracy of 0.75 for role; a language model given the same guide obtained 0.89 and 0.80.
With 176 postings reporting salary, the premiums of data engineering and data
science roles over the analyst role were conclusive, while no skill premium was. **Conclusion:** under controlled conditions, the
versioned context was associated with far fewer unsupported figures; this supports the technical feasibility of the
approach, not its effect on curriculum decisions. Reporting the absence of evidence is a core function of the observatory.

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
[@khaouja2021survey; @senger2024deep] y el uso de LLM en el diseño curricular. Sin embargo, los sistemas que hoy cruzan avisos y currículos son, en su
mayoría, soluciones comerciales cuyos procesos de extracción no están documentados, lo que impide replicarlos o
validarlos [@varpina2026enabled; @kapa2026reproducible], y en la extracción de habilidades todavía faltan definiciones
consistentes e información consolidada sobre los conjuntos de datos [@senger2024deep]. Faltan sistemas integrados, de la recolección a la propuesta
curricular, con una evaluación cuantitativa de cada componente.

El objetivo de este trabajo es diseñar y evaluar un observatorio auditable del mercado laboral en roles de datos que
integra inteligencia artificial generativa anclada en evidencia. El sistema se desarrolló para apoyar la actualización
curricular de la oferta en datos de la Fundación Universitaria Cafam (UniCafam), en Bogotá, que articula la Tecnología en
Análisis y Gestión de Datos con el programa profesional en Ciencia de Datos. El observatorio (a) recolecta cada mes
avisos de portales de empleo de Colombia y de trabajo remoto; (b) estima la demanda de habilidades y las primas salariales
con intervalos de confianza y control de comparaciones múltiples; (c) entrega a un LLM un contexto de mercado
versionado como única fuente de cifras; (d) verifica de forma determinista los porcentajes, montos y conteos que genera el modelo; y (e) exige
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
los tres primeros cortes mensuales. Su alcance es la factibilidad técnica del artefacto: la exactitud de la extracción,
la solidez de la inferencia y la fidelidad de las cifras generadas. La pertinencia pedagógica de las propuestas y su
efecto sobre las decisiones curriculares no se evalúan aquí.

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

Frente a estos trabajos, la contribución que se pretende generalizable es un principio de diseño y su evaluación: el
LLM no aporta cifras, solo las copia de un contexto versionado, y un verificador independiente del modelo comprueba que
lo haga. El estudio evalúa (a) el efecto del anclaje, separando el aporte de los datos del de las reglas de evidencia;
(b) la precisión y la exhaustividad del verificador frente a un etiquetado humano; y (c) un criterio de «concluyente» y
una prueba de equivalencia que permiten al sistema declarar cuándo no hay evidencia. La implementación concreta, con sus
portales, su taxonomía y los datos mensuales de un mercado latinoamericano, es el caso de demostración y no la
contribución en sí; ninguno de sus componentes es nuevo por separado.

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

La Fig. 1 resume la arquitectura. La **recolección** se dispara cada mes de forma automática. Este estudio usa siete
fuentes: CompuTrabajo, ElEmpleo, Talent.com y Magneto, por sus páginas públicas de búsqueda, y GetOnBoard, Remotive y
Torre.ai, por sus interfaces públicas de programación (Torre.ai solo en septiembre). LinkedIn, que el sistema también
consultó, se excluyó de todos los análisis de avisos por las razones de la sección III.E. Antes de cada escritura se genera un respaldo cifrado, y los cambios en el diseño de búsqueda quedan
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

El **verificador de cifras** extrae del texto generado los porcentajes, montos y conteos de ofertas que reconocen sus
patrones; los demás números no los revisa y quedan para la revisión humana. Busca cada cifra en el contexto, comprueba que la habilidad o el rol mencionado junto a la cifra sea el dueño del dato, revisa la
consistencia entre créditos académicos y horas (1 crédito = 48 horas) y marca siempre las tarifas. El verificador marca,
pero no bloquea: en un **portal de revisión**, una persona con rol de aprobador de la institución ve cada marca con su
motivo y decide aprobar, rechazar o pedir un ajuste, que genera una nueva versión. Cada acción queda auditada.

![Fig. 1: Arquitectura del observatorio. Las evaluaciones se ubican sobre los componentes: E1, E2 y E6 sobre la
extracción; E3 sobre el análisis; E4 y E5 sobre la generación y la verificación; E7 sobre el ciclo mensual
completo.](figuras/arquitectura.png){width=100%}

Fuente: elaboración propia.

## C. Datos {-}

Se usaron los tres primeros cortes mensuales (septiembre, octubre y noviembre de 2026; corte vigente del 1 de noviembre
de 2026). La unidad de análisis es el aviso único, identificado por una huella del portal y el contenido; un aviso
vigente en varios meses tiene un registro por mes. La Tabla II documenta la elegibilidad: de 907 avisos únicos
recolectados, se excluyeron los 435 de LinkedIn y quedaron 472 de siete fuentes, de los cuales 470 conservan el texto
crudo; los análisis que recalculan desde el texto usan estos 470. De ellos, 178 son del mercado local y publican
salario, todos de ElEmpleo, Magneto y CompuTrabajo (Talent.com no publica salario), y 176 tienen texto crudo en su
registro más reciente: esa es la muestra de las primas salariales, con un registro por aviso. De los 178, 97 aparecen
en más de un mes; por eso los avisos con salario por corte de la Tabla II suman más que los avisos únicos.
Octubre acumula varias corridas de recolección y noviembre una sola, por lo que el número de ofertas no se compara entre
esos meses.

::: {custom-style="Table Caption"}
TABLA II\
OFERTAS POR FUENTE Y CORTE
:::

| Fuente | Mercado | Sep. 2026 | Oct. 2026 | Nov. 2026 | Únicas | Con texto | Locales con salario (con texto) |
|---|---|---|---|---|---|---|---|
| ElEmpleo | Local | 74 | 93 | 68 | 145 | 144 | 90 (89) |
| Talent.com | Local | 36 | 99 | 43 | 140 | 140 | 0 |
| Magneto | Local | 0 | 89 | 62 | 94 | 94 | 69 (69) |
| CompuTrabajo | Local | 15 | 23 | 15 | 37 | 36 | 19 (18) |
| GetOnBoard | Remoto | 23 | 26 | 23 | 34 | 34 | — |
| Remotive | Remoto | 0 | 2 | 2 | 2 | 2 | — |
| Torre.ai | Remoto | 20 | 0 | 0 | 20 | 20 | — |
| **Total elegible** | | **168** | **332** | **213** | **472** | **470** | **178 (176)** |
| Con salario publicado | | 70 | 146 | 105 | | | |
| LinkedIn (excluida) | Mixto | 146 | 247 | 169 | 435 | — | — |

Fuente: elaboración propia. Por corte, una oferta vigente en varios meses cuenta en cada mes; «Únicas» cuenta cada aviso
una vez en septiembre–noviembre. «Con salario publicado» incluye el mercado remoto. Magneto y Remotive se incorporaron en
octubre; Torre.ai se desactivó después de septiembre. LinkedIn no publicó salario en ningún aviso.

## D. Procedimientos de evaluación {-}

**E1 y E2, extracción y rol frente a una referencia humana.** Se extrajo una muestra de 200 avisos estratificada por
portal y mes (semilla 2026), de los cuales 105 corresponden a las siete fuentes del estudio; los resultados se reportan
sobre esos 105. Los otros 95, de LinkedIn, se anotaron con la misma guía antes de la exclusión; la guía se redactó antes
de anotar, y ni esos avisos ni los 105 se usaron para ajustar reglas. Un anotador etiquetó todos los avisos y un segundo anotador, independiente, una submuestra (37 de los 105)
para medir el acuerdo ($\kappa$ de Cohen), sin ver la salida del sistema, con una guía con casos difíciles y con correos y teléfonos
enmascarados. Los 48 desacuerdos de la submuestra doble (en 20 de los 37 avisos) los adjudicó
el anotador principal con la guía, con ambas etiquetas a la vista: 31 se resolvieron a favor de su etiqueta original y
17 a favor de la del segundo anotador (3 de rol, 2 de años de experiencia y 12 de habilidades). La referencia final es
la adjudicada. Se aplicó una única regla de
consistencia derivada de la guía: si se marca «Excel avanzado» explícito, se marca también Excel a cualquier nivel (8
avisos del primer anotador, 4 de ellos en las fuentes del estudio). Se calcularon precisión, exhaustividad y F1 por habilidad (micro y macro), exactitud y F1 macro del rol, y exactitud del
nivel y de los años de experiencia, con IC por remuestreo (*bootstrap*) de 2000 réplicas. En E2 se compararon dos
versiones del clasificador de rol: la publicada y una corregida, cuyas reglas se ajustaron solo con avisos fuera
de la muestra.

**E3, poder explicativo de la taxonomía.** Siguiendo a Ao et al. [@ao2023skill], se midió la proporción de la variación del
logaritmo del salario que explican las habilidades extraídas, dentro y fuera de muestra (validación cruzada de 5
particiones repetida 50 veces), frente a los controles y frente al texto completo representado con TF-IDF. Cada aviso
entra una sola vez, con su registro más reciente, de modo que el mismo aviso no queda a la vez en entrenamiento y prueba;
el vocabulario y los pesos TF-IDF se calculan solo con las particiones de entrenamiento, y la penalización *ridge* se
elige por validación cruzada interna dentro de cada una. Las particiones no se agrupan por empleador; el riesgo
residual son los avisos repetidos entre portales (dos pares).

**E4, precisión y exhaustividad del verificador.** Las cifras de las propuestas generadas en E5 se descompusieron en
afirmaciones atómicas [@min2023factscore] y se extrajo una muestra estratificada de 174: todas las marcadas (54), 80
revisadas sin marca y 40 números que el verificador no revisa. Se etiquetaron a ciegas frente a la condición y al
modelo, en cuatro categorías: respaldada, mal atribuida, sin respaldo y no verificable. Etiquetó una persona distinta
del autor. Para validar esas etiquetas, el autor reetiquetó a ciegas, sin ver la planilla principal, una submuestra aleatoria estratificada de
40 cifras (15 marcadas, 15 revisadas sin marca y 10 no revisadas), y se midió el acuerdo con κ de Cohen. Como la franja
no revisada aportó solo 4 cifras de mercado, se hizo además una inspección focal: esa franja se dividió según una pista
textual de mercado junto al número («n =», ofertas, salario, COP, %, prima o corte), y el autor etiquetó a ciegas 60
números adicionales de la subfranja con pista; los 40 de la muestra original se posestratificaron con la misma
regla. Quince etiquetas de esa inspección contradecían la guía o el contexto (12 fragmentos de la fecha de corte
etiquetados como cifras de mercado y 3 cifras que sí estaban en el contexto) y se corrigieron con su justificación
documentada en el repositorio. La precisión se calcula sobre el censo de las marcas, con IC por remuestreo; la
exhaustividad, la cobertura y la proporción de cifras respaldadas se estiman por subestrato con distribuciones
posteriores Beta de Jeffreys para la proporción de cifras de mercado y la de problemas, por simulación de Monte Carlo. No se usaron las propuestas con las que se ajustó el verificador, para no
evaluar dentro de la muestra de ajuste.

**E5, efecto del anclaje y del modelo.** Se generaron 36 propuestas curriculares: tres condiciones × dos modelos
(Gemini 4 Argon y Gemini 3.8 Flash) × dos solicitudes de UniCafam (un diplomado de 8 créditos en ingeniería de datos en
la nube y una microcredencial de 2 créditos sin enfoque definido) × tres repeticiones, sin modelo de respaldo. Las
condiciones fueron: *con contexto* (el prompt de producción); *sin datos, con reglas* (sin el bloque de datos, pero con
las instrucciones de evidencia); y *sin anclaje* (sin datos, sin reglas y con ejemplos neutros). Todas se verificaron
contra el mismo contexto: el del observatorio en producción para el corte del 1 de noviembre de 2026. Hay dos versiones
con cifras idénticas, que solo difieren en el identificador y la fecha de generación (SHA-256 025ea60f… y 41e25e2a…,
publicadas en el repositorio). Ese contexto se construyó antes de excluir LinkedIn: 169 de sus 382 ofertas de noviembre
(44 %) provienen de esa fuente, lo que afecta la demanda y la composición de roles, pero no las cifras salariales,
porque LinkedIn no publicó salario. Por eso E5 no es un análisis del corpus elegible, sino una prueba del comportamiento
de anclaje sobre un contexto de producción externo a él: mide si el modelo copia o inventa las cifras que recibe, y el
contexto es el mismo en todas las condiciones. Para la tasa de cifras marcadas se reportan IC exactos de Clopper–Pearson, que tratan las
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
legalidad y la ética de la recolección se revisaron con el marco de Krotov et al. [@krotov2020tutorial] y las
recomendaciones de Brown et al. [@brown2025scraping]: el uso es académico y no comercial, solo se publican agregados, no
se inicia sesión en ningún portal, las solicitudes se espacian (pausas aleatorias de 0,3 a 3 s y una corrida al mes) y
no se recolectan datos de quienes buscan empleo. Siguiendo a Kapa y Schaefer [@kapa2026reproducible], el archivo
robots.txt se tomó como línea base ética: en las cuatro fuentes consultadas por sus páginas públicas, las rutas usadas
están permitidas (revisión del 10 de noviembre de 2026; para CompuTrabajo, copia archivada del 6 de octubre de 2026);
GetOnBoard y Remotive se consultan mediante sus interfaces públicas, según sus condiciones, que en el caso de Remotive
exigen citarla como fuente. En Torre.ai, el robots.txt de su sitio restringe las páginas de búsqueda, pero el sistema
consultó su interfaz de búsqueda en otro dominio (search.torre.co), que no publica robots.txt (revisión del 13 de
noviembre de 2026); la fuente se desactivó después de septiembre. LinkedIn, que el sistema también consulta, declara en su robots.txt que el acceso
automatizado sin su permiso expreso está prohibido; por eso se excluyó de todos los análisis de este artículo. El permiso se solicitó a LinkedIn el 10 de noviembre de
2026 y, al cierre de este artículo, no se había recibido respuesta. El robots.txt se usó como línea base ética y no
sustituye un análisis jurídico de los términos de uso de cada portal, que no se realizó. Las dos personas que anotaron y
etiquetaron participaron de forma voluntaria como colaboradoras de la investigación, no como sujetos de estudio, y solo
se registraron sus etiquetas. Por estas características, UniCafam no exigió el aval de un comité de ética.

# IV. RESULTADOS, ANÁLISIS E INTERPRETACIÓN {-}

## A. Extracción y rol (E1, E2 y E6) {-}

El acuerdo entre anotadores en los 37 avisos de la submuestra doble fue sustancial: $\kappa$ = 0,70 en el rol (76 % de
coincidencia), 0,76 en el nivel (81 %) y 0,82 en promedio en las habilidades; en los años de experiencia, ambos
anotadores coincidieron en si el aviso los declaraba en el 89 % de los casos y en el valor exacto en el 91 % de los que
ambos registraron.

La Tabla III compara el sistema de reglas con el LLM sobre la misma referencia. Las reglas extrajeron las 31 habilidades
con un F1 micro de 0,854 (precisión 0,819 y exhaustividad 0,891); el LLM obtuvo 0,888, una diferencia pequeña pero
concluyente (+0,034 [0,012; 0,056]) que se debe sobre todo a una mayor exhaustividad. En el rol no hubo diferencia
concluyente (0,752 frente a 0,800). El LLM fue mejor en el nivel del cargo (+0,105) y, sobre todo, en detectar los años de
experiencia cuando el aviso los declara (0,833 frente a 0,639), con una precisión similar: las reglas casi nunca inventan
años (1 de 105 avisos), pero omiten muchas formas de expresarlos. El filtro de relevancia fue casi
perfecto con ambos métodos. El LLM tardó una mediana de 7,8 s por aviso; las reglas, milisegundos.

::: {custom-style="Table Caption"}
TABLA III\
EXTRACCIÓN FRENTE A LA REFERENCIA HUMANA: REGLAS Y LLM (N = 105)
:::

| Tarea | Métrica | Reglas | LLM | Diferencia [IC 95 % pareado] |
|---|---|---|---|---|
| Habilidades (31) | F1 micro | 0,854 | 0,888 | +0,034 [+0,012; +0,056] |
| | Precisión / exhaustividad | 0,819 / 0,891 | 0,833 / 0,951 | — |
| Rol (8 categorías) | Exactitud | 0,752 | 0,800 | +0,048 [−0,038; +0,133] |
| | F1 macro | 0,659 | 0,772 | — |
| Nivel del cargo | Exactitud | 0,714 | 0,819 | +0,105 [+0,009; +0,210] |
| Años de experiencia | Detección (exhaustividad) | 0,639 | 0,833 | +0,194 [+0,106; +0,294] |
| | Precisión de la detección | 0,979 | 0,952 | — |
| Relevancia temática | F1 | 0,960 | 0,980 | — |

Fuente: elaboración propia. LLM: Gemini 4 Argon, temperatura 0, con la guía de anotación. IC por remuestreo pareado de
avisos (2000 réplicas). Referencia: anotador principal, con la submuestra doble adjudicada.

En E2, el clasificador de rol corregido superó al publicado: la exactitud subió de 0,524 [0,429; 0,619] a 0,752
[0,676; 0,838], una mejora de 0,229 [0,152; 0,314], y el F1 macro pasó de 0,442 a 0,659. La versión publicada clasificaba
por subcadenas, de modo que «ia» o «bi» dentro de otras palabras activaban roles equivocados; la corregida cambió de rol
a 40 de los 105 avisos (y a 157 de los 365 avisos de las mismas fuentes fuera de la muestra). Sus reglas se ajustaron
solo con avisos fuera de la muestra anotada, de estas fuentes y de LinkedIn. Por
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

En E4 se etiquetaron 234 cifras: las 174 de la muestra y 60 de la inspección focal (Tabla VIII). De las 35 cifras de mercado que el verificador marcó,
32 carecían de respaldo en el contexto, todas en la condición sin anclaje; las 3 restantes, de la condición con
contexto, sí estaban respaldadas y fueron falsas alarmas. La precisión de las marcas fue de 0,914 [0,811; 1,0]. Entre
las 108 cifras de mercado no marcadas de la muestra (75 revisadas y 33 no revisadas, tras la inspección focal) no se
observó ninguna sin respaldo o mal atribuida (Tabla VIII). Ese resultado no excluye errores en las cifras no examinadas:
la exhaustividad estimada es de 0,74 [0,32; 0,98] y, entre las cifras que el verificador revisa, de 0,95 [0,62; 1,0].
El intervalo es amplio porque la población de números es grande (2417) y los problemas, escasos. El verificador revisó
el 69 % [62; 75] de las unas 909 cifras de mercado estimadas; casi todas las demás eran tamaños de muestra («n = 43») de
la condición con contexto, escritos de formas que sus patrones no reconocen, y todas las de la muestra estaban
respaldadas. En conjunto, el 95,2 % [89,6; 96,4] de las cifras de mercado de las 36 propuestas tenía respaldo. Además de las cifras de mercado, el verificador marcó 19 números de la
condición sin anclaje que no son datos del mercado laboral: 17 tarifas y descuentos de matrícula inventados por el
modelo, que el diseño marca siempre, y 2 estadísticas externas sin fuente («más del 80 % de los modelos de machine
learning no llegan a generar valor»).

La auditoría humana de 40 cifras coincidió con el etiquetado principal en el 90,0 % de los casos sobre si la cifra es un
dato de mercado (κ = 0,80) y en el 80,0 % en la etiqueta completa (κ = 0,69), un acuerdo sustancial. Al revisar los 8
desacuerdos contra el contexto, 6 se resolvieron a favor de la etiqueta principal: eran numerales de lista, el nivel de
confianza «95 %» o cifras que el contexto sí contenía. Los 2 restantes diferían entre «sin respaldo» y «no verificable»,
y ninguna de las dos etiquetas daba la cifra por respaldada. Ningún desacuerdo cambia las métricas, que se reportan con
la etiqueta principal.

::: {custom-style="Table Caption"}
TABLA VIII\
ETIQUETADO DE LAS CIFRAS SEGÚN EL ESTRATO DEL VERIFICADOR (E4)
:::

| Estrato (población) | Cifras etiquetadas | De mercado | Respaldadas | Sin respaldo | Mal atribuidas |
|---|---|---|---|---|---|
| Marcadas (54) | 54 | 35 | 3 | 32 | 0 |
| Revisadas sin marca (635) | 80 | 75 | 75 | 0 | 0 |
| No revisadas, con pista de mercado (548) | 68 | 33 | 33 | 0 | 0 |
| No revisadas, sin pista (1180) | 32 | 0 | — | — | — |

Fuente: elaboración propia. Cifras de las 36 propuestas de E5, etiquetadas sin conocer la condición ni el modelo. La
franja no revisada incluye 8 cifras de la muestra original y 60 de la inspección focal con pista, y 32 de la muestra
original sin pista. Matriz de confusión de la muestra entre cifras de mercado: 32 verdaderos positivos, 3 falsos
positivos, 0 falsos negativos y 108 verdaderos negativos.

## D. Hallazgos sobre el mercado de roles de datos (E7) {-}

En noviembre de 2026 (n = 213), las habilidades más pedidas fueron SQL (59,6 % de las ofertas), Python (54,9 %), ETL
(40,4 %), estadística (36,6 %) y Power BI (30,0 %). Con 176 ofertas locales con salario y frente al rol de analista de
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
concluyente con la versión anterior del clasificador de rol (−17,0 % [−27,1; −5,5]; $q$ de Benjamini–Hochberg = 0,052), dejó de serlo al
corregir el rol (−12,5 % [−24,2; +1,1]; $q$ = 0,56): parte de la asociación se debía a la composición de roles. El
resultado se mantuvo al usar el extremo inferior o superior del rango salarial, al controlar el nivel educativo y el
sector, y al excluir los duplicados entre portales (Tabla VII). Entre las siete fuentes solo se
detectaron dos pares de avisos duplicados (CompuTrabajo con ElEmpleo y con Magneto).

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

SQL mostró evidencia nominal de equivalencia dentro del margen de ±15 % (−0,2 %, IC 90 % [−11,4; +12,5]; TOST, $p$ =
0,025), que se mantuvo en las cinco especificaciones de robustez; sin embargo, no se sostuvo tras corregir por las 11
habilidades evaluadas ($q$ = 0,27). Por tanto, no se concluye equivalencia para ninguna habilidad: los datos no permiten
afirmar que tengan prima ni que no la tengan. Los márgenes mínimos de equivalencia fueron de ±12,5 % (SQL) a ±37,9 % (Azure), de modo
que, con 176 ofertas, ningún margen menor de un 12 % habría permitido declarar equivalencia.

No hubo cambios concluyentes en la composición de roles entre meses: de septiembre a octubre, con portales comparables
(n = 146 y 241), el mayor cambio fue el de ingeniero de datos, de 17,8 % a 24,1 % ($q$ = 0,37); de octubre a noviembre
(n = 332 y 213), ningún rol cambió más de 2,2 puntos porcentuales ($q$ = 0,91). Durante la operación, la propia evaluación detectó y corrigió cuatro fallos: una caché de 30 días
en el tablero, un error de autenticación por credenciales truncadas, la clasificación de rol por subcadenas y la
degeneración de la matriz de covarianza HC3.

## E. Discusión {-}

**Anclaje y verificación (PI2 y PI3).** Los resultados de E5 indican que el anclaje cumple dos funciones distintas. Las
reglas de evidencia, por sí solas, bastan para que el modelo se abstenga de inventar cifras de mercado, pero no producen
evidencia; el contexto versionado es lo que permite que la propuesta contenga cifras, y casi todas quedan respaldadas.
Sin anclaje, casi ninguna cifra tiene respaldo en el observatorio, en línea con lo reportado sobre citas inexistentes en
economía [@buchanan2024chatgpt] y con el peor desempeño de las preguntas cuantitativas en sistemas con recuperación
[@iaroshev2024evaluating]. A diferencia de los enfoques que verifican con el propio modelo [@farquhar2024detecting], el
verificador es determinista, y su resultado no depende del modelo que se evalúa. En la muestra evaluada, el verificador identificó 32 cifras de mercado sin respaldo y emitió tres marcas incorrectas.
La ausencia de falsos negativos observados debe leerse con cautela, porque sus patrones cubren el 69 % de las cifras de
mercado y la exhaustividad estimada tiene un intervalo amplio. Sus tres falsas alarmas
surgieron de la regla de atribución: la oración mencionaba varias habilidades o roles, y el verificador asoció una cifra
correcta a uno distinto del que la sustentaba.
Su límite principal es de cobertura: cerca de un tercio de las cifras de mercado, sobre todo tamaños de muestra, está
escrito de formas que sus patrones no revisan, aunque en la muestra todas eran correctas. Esos números requieren
revisión humana, y ampliar los patrones a los tamaños de muestra es la mejora más directa. Marcar las tarifas y descuentos resultó útil: sin anclaje, el modelo
inventó precios de matrícula verosímiles, un tipo de error que una persona podría no notar.

**Reglas frente a LLM en la extracción (PI1).** Con la misma guía, el LLM extrajo mejor que las reglas, pero la ventaja
depende de la tarea: es pequeña en las habilidades (3 puntos de F1), no concluyente en el rol y grande en los años de experiencia,
donde la variedad de redacciones supera a cualquier lista de patrones. El resultado matiza lo reportado por Nguyen et al.
[@nguyen2024rethinking], que encontraron a los LLM por debajo del etiquetado supervisado en la extracción de habilidades, y
es coherente con Xu et al. [@xu2025from], para quienes el desempeño de los LLM depende de la estrategia de uso: aquí el
modelo recibió una guía detallada y una lista cerrada de 31 habilidades, una tarea más acotada que la extracción abierta.
La comparación sugiere que el mecanismo de extracción no debe elegirse por una sola métrica. Aunque el LLM mejoró el F1
de habilidades (0,888 frente a 0,854), las reglas permiten rastrear cada decisión de extracción y mantener un
procedimiento estable entre meses, mientras que el LLM tarda segundos por aviso y debe volver a validarse con cada
versión del modelo. Por ello se plantea una arquitectura híbrida, con reglas para las habilidades y el rol y el LLM
para los años de experiencia, como hipótesis de diseño; su superioridad operativa requeriría una evaluación
prospectiva de costos, fallos y mantenimiento.

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
[@kurekova2015using; @lovaglio2026analyzing]. Tres cortes no constituyen una tendencia. La exclusión de LinkedIn, un canal
importante para los cargos de datos, reduce la cobertura del mercado. El 49,3 % de las ofertas de noviembre publica
salario, todas de tres portales locales, y los rangos se toman en su punto medio, aunque los
extremos no cambian las conclusiones [@zhong2023feature]. Los duplicados entre portales no se eliminan en el flujo de
datos [@zhao2021framework]. La taxonomía es fija frente a una terminología que cambia
[@suarezrodriguez2026semantic; @desanto2026skillens], y el rol se infiere del título. Las primas son asociaciones, no
efectos causales. Los LLM no son deterministas, y el verificador solo cubre porcentajes, montos y conteos de ofertas. Las
36 generaciones de E5 dan seis repeticiones por celda, con dos solicitudes, y no incluyen escenarios adversos como datos
contradictorios o perturbaciones del contexto; además, el contexto de E5 incluía LinkedIn (sección III.D). La utilidad
curricular no se evaluó: no hubo jueces expertos que valoraran la pertinencia pedagógica de las propuestas, por lo que
los resultados no demuestran su efecto sobre decisiones curriculares. El texto de los avisos no se puede redistribuir,
lo que permite auditar y reproducir los cálculos, pero no replicar el corpus de forma independiente. El margen de equivalencia se fijó antes de calcular la prueba,
pero cuando las estimaciones puntuales ya eran públicas, por lo que no es un margen prerregistrado en sentido estricto;
por eso se reportan también los márgenes mínimos. La referencia de extracción proviene de un anotador principal, con
un segundo anotador en el 35 % de los avisos; el acuerdo fue sustancial, pero no perfecto, y el anotador principal es
también el autor del sistema, aunque anotó sin ver su salida; él mismo adjudicó los desacuerdos, sin un tercer
evaluador externo. El LLM de E6 se evaluó con un solo modelo y una sola
ejecución. La auditoría del etiquetado de E4 cubre el 23 % de la muestra, y tanto esa auditoría como la inspección
focal las hizo el autor del sistema.

# V. CONCLUSIONES {-}

Este trabajo diseñó y evaluó un observatorio auditable del mercado laboral en roles de datos que integra inteligencia
artificial generativa anclada en evidencia. Con dos solicitudes curriculares y 36 generaciones controladas, el contexto
versionado se asoció con una proporción de cifras marcadas cercana a cero, frente a casi todas en la condición sin
anclaje, y las reglas de evidencia por sí solas llevaron al modelo a abstenerse en lugar de inventar. Las marcas del verificador tuvieron una precisión de 0,91 y
no se observaron cifras sin respaldo sin marcar en la muestra, pero su exhaustividad sigue siendo incierta y sus
patrones no revisan cerca de un tercio de las cifras de mercado. En la extracción, las reglas alcanzaron un desempeño
cercano al de un LLM con la misma guía en las habilidades y el rol, con la ventaja de ser auditables y reproducibles; el
LLM fue superior en los años de experiencia. La evaluación también corrigió el propio sistema: el clasificador de rol
publicado tenía una exactitud de 0,52 y el corregido, de 0,75. En el plano analítico, el observatorio identificó primas
concluyentes por rol, pero no por habilidad, y lo declaró explícitamente; ninguna habilidad resultó equivalente tras
corregir por comparaciones múltiples. Estos resultados respaldan la factibilidad técnica del enfoque, pero todavía no
demuestran su efecto sobre las decisiones curriculares de una institución, que requeriría una evaluación con expertos
curriculares y un seguimiento de las decisiones tomadas.

# VI. RECOMENDACIONES {-}

Para las instituciones que usen LLM en el diseño curricular: (a) entregar al modelo las cifras del mercado como un
contexto versionado, con su tamaño de muestra y su fecha de corte, en lugar de pedirle que las recuerde; (b) verificar
las cifras generadas con reglas independientes del modelo y mostrar las marcas a quien aprueba; y (c) mantener la
aprobación humana como requisito, no como opción.

Para quienes construyan observatorios con avisos de empleo: (a) revisar los términos de uso y el archivo robots.txt
de cada fuente antes de recolectar, documentar la decisión y pedir permiso cuando el acceso automatizado esté prohibido;
(b) conservar el texto crudo para recalcular con reglas
nuevas; (c) registrar los cambios en el diseño de búsqueda y excluirlos de las comparaciones entre meses; y (d) reportar
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
Eva María Bernal, quien actuó como segunda anotadora en la construcción de la referencia de evaluación y etiquetó las
cifras de E4.

**Contribución de autoría (CRediT).** Juan Felipe Bernal Peña: conceptualización, curación de datos, análisis formal,
investigación, metodología, software, visualización, redacción del borrador original y redacción, revisión y edición.

**Conflicto de intereses.** El autor declara que no existen conflictos de intereses relacionados con este trabajo.

**Disponibilidad de datos y código.** El código del observatorio, los scripts de evaluación y los resultados agregados
están disponibles en <https://github.com/jfbernalp/proyecto_investigativo>, versión `v0.14.0-articulo`. Los
indicadores públicos se pueden consultar en <https://jfbernalp.dev>. El texto completo de los avisos no se publica
porque contiene datos de terceros y está sujeto a los términos de uso de los portales. En consecuencia, el estudio es
auditable (cada cifra se rastrea hasta su script y su corte) y computacionalmente reproducible para quien tenga acceso
a la base, pero un tercero no puede replicar el corpus. Sí se publican los dos contextos de E5, las 36 propuestas
generadas y los resultados de E4, con los que se pueden repetir la verificación y las métricas de ambas evaluaciones.

**Uso de inteligencia artificial generativa.** Gemini 4 Argon y Gemini 3.8 Flash (Google) forman parte del artefacto
evaluado y se usaron en las evaluaciones E5 y E6. El autor utilizó Claude (Anthropic) como asistente de programación,
análisis y redacción de borradores; todas las cifras provienen de scripts reproducibles del repositorio y fueron
verificadas por el autor, y las referencias se verificaron contra los registros de Crossref y DataCite. Scopus AI se
usó solo para orientar la búsqueda bibliográfica, no como fuente. Quien etiquetó las cifras de E4 se apoyó en una
herramienta de IA generativa; una auditoría humana ciega de 40 de esas cifras mostró un acuerdo sustancial
($\kappa$ = 0,80). El autor asume plena responsabilidad por el
contenido.

# VIII. REFERENCIAS {-}

::: {#refs}
:::
