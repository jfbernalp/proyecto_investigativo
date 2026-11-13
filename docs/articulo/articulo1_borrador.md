# Artículo 1 · Borrador de trabajo

**Título provisional:** Diseño y evaluación de un observatorio auditable del mercado laboral en datos con IA
generativa anclada en evidencia

**Autor:** Juan Felipe Bernal · Data Scientist

**Estado:** esqueleto del 7-nov-2026 · entrega 15-nov-2026. Idioma, plantilla, extensión y estilo de citas
están pendientes de decisión (hito 56, D.1).

**Convenciones del borrador:**
- `[PENDIENTE: …]` marca un resultado o una decisión que falta.
- Toda cifra lleva su n, su corte y el script que la produce.
- Las referencias usan los # de `bibliografia/seleccion_final.md`; antes de citar una cifra o un método de la
  literatura, confirmarlo con el texto completo (la matriz se hizo con resúmenes).

---

## Resumen (≈ 250 palabras, se escribe al final)

[PENDIENTE: redactar cuando estén E1, E2 y, si se alcanzan, E4 y E5.]

Estructura prevista:
1. problema: brecha entre currículos y mercado en roles de datos, y LLM que inventan cifras;
2. artefacto: observatorio de punta a punta con un verificador determinista de cifras y aprobación humana;
3. método: Design Science Research con evaluación en rondas;
4. resultados principales con IC;
5. aporte.

## 1. Introducción

**Problema práctico.** Las instituciones de educación superior necesitan ajustar sus programas en
análisis, ciencia e ingeniería de datos a un mercado que cambia rápido. La evidencia sobre ese mercado
suele venir de encuestas lentas o de informes privados poco transparentes. Los avisos de empleo en línea
son una fuente frecuente y granular (Hershbein & Kahn, 2018; Deming & Kahn, 2018), pero no son
representativos sin más (#117, #109).

**Problema con la IA generativa.** Los modelos de lenguaje ya se usan para diseñar programas (#504, #354,
#367; Kasneci et al., 2023, #469), pero producen cifras y citas fluidas sin respaldo:
- más del 30 % de las citas de GPT-3.5 en economía no existían (#311);
- en un sistema RAG sobre informes financieros, las preguntas cuantitativas fueron las de peor desempeño
  (#96);
- la verificación de afirmaciones contra tablas está cerca del azar en casi todos los modelos (#275).

Una propuesta curricular que afirma "SQL aparece en el 68 % de las ofertas" es tan útil como verificable
sea esa cifra.

**Hueco.** Los componentes por separado están estudiados: scraping de avisos, extracción de habilidades
(#234, #227) y LLM para currículo. Faltan sistemas integrados de punta a punta con una evaluación
estandarizada (B44; también el diagnóstico del informe de Scopus AI, sin citarlo como fuente).

**Aporte.** Diseñamos, desplegamos y evaluamos un observatorio que:
1. recolecta cada mes avisos de roles de datos de siete fuentes en Colombia y en remoto;
2. estima demanda de habilidades y primas salariales con intervalos de confianza y control de
   comparaciones múltiples;
3. entrega a un LLM un contexto de mercado versionado como única fuente de cifras;
4. verifica de forma determinista cada cifra que genera el modelo (existencia, atribución y consistencia);
5. exige aprobación humana.

**Preguntas de investigación (provisionales):**
- **PI1 · Extracción.** ¿Con qué exactitud el sistema de reglas extrae habilidades, rol, experiencia y nivel
  frente a una referencia humana, y frente a un LLM con las mismas instrucciones? (E1, E2, E6)
- **PI2 · Anclaje.** ¿El contexto de mercado reduce las cifras sin respaldo en las propuestas generadas, y
  cambia esto con el modelo? (E5)
- **PI3 · Verificación.** ¿Con qué precisión y recall detecta el verificador las cifras sin respaldo o mal
  atribuidas? (E4)
- **PI4 · Utilidad.** ¿Qué dice el observatorio sobre el mercado de roles de datos, con qué incertidumbre y
  con qué límites? (E3, E7, hallazgos preliminares)

## 2. Trabajos relacionados

Citas en formato pandoc (`[@clave]`, ver `referencias.bib` y `bibliografia/claves.md`). Las cifras
tomadas de la literatura llevan ‡ hasta confirmarlas con el texto completo (la matriz se hizo con
resúmenes).

### 2.1 Los avisos de empleo en línea como fuente de datos

**Validez.** Los avisos publicados en internet se han consolidado como fuente para medir los
requisitos de habilidades de los empleadores [@hershbein2018recessions; @deming2018skill]. Hay
evidencia de que las habilidades que piden los avisos corresponden a las que se usan en el puesto
[@daly2025skill].

**Representatividad.** No son una muestra representativa del mercado laboral:
- @kurekova2015using sistematizan los problemas metodológicos de las vacantes en línea.
- @lovaglio2026analyzing cuantifican la sobrerrepresentación de ciertos perfiles frente a la encuesta de
  fuerza laboral‡.
- Varios trabajos combinan avisos y estadística oficial mediante calibración o modelos de selección
  [@beresewicz2021enhancing; @lovaglio2026forecasting; @fernandezalvaro2025scraped].

**Duplicados.** Un mismo aviso aparece en varios portales, y detectarlo es un problema en sí mismo
[@zhao2021framework].

**América Latina.**
- Uso de avisos para medir la demanda laboral [@camposvazquez2021labor; @pazmino2018analysis;
  @cocon2023scraping].
- Extracción de habilidades [@anelli2023which].
- Mercados de IA alineados con ESCO [@guevararamirez2026characterization].
- El trabajo más cercano al nuestro, @suarezrodriguez2026semantic, analiza avisos de Computrabajo y
  Adzuna en siete países entre 2022 y 2025‡. Encuentra que, tras la aparición de ChatGPT, cambió sobre
  todo la terminología de las habilidades de IA, más que su volumen: una advertencia directa para las
  taxonomías fijas.
- En Colombia, @alvarez2014vacancies construyen un índice de vacantes con avisos de prensa desde 1976,
  y @farne2011observatories discuten qué es y cómo funciona un observatorio del mercado de trabajo.

### 2.2 Extracción de habilidades y su evaluación

**Revisiones.** Las revisiones de la tarea [@khaouja2021survey; @senger2024deep] distinguen entre
diccionarios o reglas, modelos supervisados de etiquetado de secuencias y, más recientemente, modelos
de lenguaje.

**Referencias anotadas.** La evaluación estándar compara contra avisos anotados a mano con guías y
acuerdo entre anotadores, como SkillSpan [@zhang2022skillspan].

**LLM frente a otros métodos.**
- Aprendizaje en contexto frente al etiquetado supervisado [@nguyen2024rethinking].
- Herramientas basadas en LLM frente a etiquetas de expertos, que reportan acuerdo, divergencias y no
  determinismo [@kavargyris2026have].
- Encoders frente a LLM sobre el mismo conjunto [@matkin2026comparative].
- Un LLM sin contexto rinde peor que el NLP tradicional, mientras que la versión con recuperación
  rinde mejor [@xu2025from]‡.
- Datos sintéticos y etiquetas incompletas inflan las métricas [@veys2026surface; @nkrumah2025skill].

**Evaluación sin etiquetado.** @ao2023skill proponen medir qué proporción de la variación salarial
explican las habilidades extraídas. Con ella comparan diccionarios y modelos de tópicos, y muestran una
tensión entre poder explicativo e interpretabilidad‡.

**Taxonomías que evolucionan.** Otra línea detecta habilidades nuevas y las enlaza con ESCO, con
revisión humana [@desanto2026skillens; @desanto2026using]. También se usan LLM para estructurar avisos
a escala nacional [@howison2025extracting].

**Roles de datos.** Los estudios del dominio han comparado:
- habilidades de BI frente a big data [@debortoli2014comparing];
- analistas de negocio, de BI, de datos y científicos de datos [@verma2019investigation];
- el perfil del científico de datos [@smaldone2022employability];
- la evolución de los avisos de analista de nivel inicial [@dong2020longitudinal];
- las brechas entre universidad y empresa [@zhang2023investigation].

@nakash2025decoding clasifican carreras de IA a partir de avisos, que es la tarea que nuestro sistema
resuelve con reglas sobre el título.

### 2.3 Habilidades y salarios en los avisos

**El valor de una habilidad depende de con cuáles se combina** [@stephany2024what]. Por eso tiene
sentido leer el rol, como conjunto de habilidades, además de la habilidad suelta.

**Avisos de científicos y analistas de datos.** @zhong2023feature tratan el salario como un intervalo
y no como el punto medio del rango. Encuentran que Excel, las herramientas de oficina y la recolección
de datos se asocian negativamente con el salario‡.

**Otros contextos y métodos:**
- primas por habilidades digitales dentro de ocupaciones [@garcialazaro2025digital];
- demanda de habilidades de IA [@alekseeva2021demand];
- contratación por habilidades en lugar de título [@bone2025skills];
- prima del inglés con avisos de Computrabajo México [@helleseter2020english];
- contenido de tareas en Chile, con evidencia débil [@camposgonzalez2025impact];
- habilidades blandas en TI [@ternikov2022wage];
- redes de habilidades [@duan2024skill].

En conjunto, la literatura muestra que obtener primas concluyentes desde avisos es difícil y depende
del tamaño de la muestra y de cómo se mide el salario.

### 2.4 Alucinación, anclaje y verificación en LLM

**Alucinación y su medición.** Los LLM producen afirmaciones fluidas sin respaldo
[@ji2023survey; @rawte2023troubling]. Inventan citas con frecuencia [@mcgowan2023chatgpt], también en
economía, donde además empeoran cuanto más específica es la pregunta [@buchanan2024chatgpt]‡.

**Anclaje.** La generación anclada en documentos recuperados [@lewis2020retrieval] reduce el problema,
pero no lo elimina. En un sistema RAG sobre informes financieros, las preguntas cuantitativas fueron las
de peor desempeño [@iaroshev2024evaluating]‡.

**Verificación.**
- **Afirmaciones atómicas:** FActScore descompone el texto en afirmaciones y verifica cada una contra la
  fuente [@min2023factscore]. Nuestro verificador hace lo mismo con las cifras.
- **Contra tablas:** verificar afirmaciones contra tablas es difícil para los propios LLM
  [@lu2023scitab]‡. Esto respalda verificar con reglas deterministas fuera del modelo.
- **Por incertidumbre del modelo:** otros enfoques detectan alucinaciones con la incertidumbre del propio
  modelo [@farquhar2024detecting]. El nuestro no depende del modelo.
- **Después de generar:** hay propuestas de verificar después de generar [@martin2024semantic] y en varias
  dimensiones (estructural, semántica, ejecutable) [@zuo2026veriflow]. También se ha evaluado la
  exactitud de LLM al citar normas, con supervisión de expertos [@lauritzen2026evaluating].

### 2.5 Design Science Research con LLM, y currículo con IA

**DSR.** Ofrece el marco para diseñar y evaluar artefactos [@hevner2004design; @peffers2007design].
Precedentes con LLM:
- RAG sobre informes financieros [@iaroshev2024evaluating];
- extracción de indicadores financieros con exactitud en muestra y fuera de ella [@li2025extracting];
- un sistema multiagente evaluado en tres rondas: expertos, cuasi-experimento y caso real
  [@schinckus2026large], que es la plantilla de nuestra evaluación;
- validación de datos con expertos en el ciclo [@dormehl2026domain].

**Currículo con IA.**
- Riesgos y oportunidades de los LLM en educación [@kasneci2023chatgpt].
- Diseño curricular con humano en el ciclo [@simon2026review; @lusi2026augmented; @brown2025toward].
- Comparación de versiones de ChatGPT diseñando programas, con rúbrica de expertos
  [@genc2026comparative].
- Analítica curricular que cruza oferta y demanda de habilidades [@varpina2026enabled].
- El caso más parecido al nuestro es @jekabsone2026bridging: ~30.000 avisos de Letonia‡, ESCO, el
  currículo y entrevistas con expertos para proponer microcredenciales. Advierte que emparejar uno a uno
  con ESCO sobreestima las brechas.
- @kapa2026reproducible describen un pipeline reproducible de avisos de un portal alemán, con validación
  externa y anonimización.

**El hueco.** Una revisión reciente del alineamiento currículo–industria con IA y NLP señala tres
problemas: el sesgo monolingüe, la falta de conjuntos de datos estándar y una validación limitada
[@handayani2026driven]. También se documentan brechas persistentes entre investigación, educación y
empleo [@borner2018skill; @jaiswal2025understanding].

### 2.6 Ética y legalidad del scraping

El scraping con fines de investigación tiene riesgos legales y éticos
[@krotov2020tutorial; @luscombe2022algorithmic], y hay recomendaciones prácticas para investigadores
[@brown2025scraping]. El caso hiQ Labs contra LinkedIn y la comparación entre Estados Unidos y Europa
indican que el scraping no es ilícito en sí mismo, pero debe respetar el derecho penal, la protección de
datos, la propiedad intelectual y los contratos [@silva2024right]. @kahlon2026systematic revisan las
técnicas recientes, incluidas las basadas en LLM, y sus aspectos legales.

### 2.7 Posicionamiento

Frente a @jekabsone2026bridging y @kapa2026reproducible, este trabajo aporta tres cosas:
1. una verificación determinista de cada cifra que produce el LLM contra un contexto versionado;
2. una evaluación cuantitativa del efecto del anclaje, con y sin datos, y con y sin reglas;
3. un mercado latinoamericano con datos mensuales.

Frente a @iaroshev2024evaluating, se verifica con reglas fuera del modelo en lugar de métricas calculadas
por otro LLM. Frente a la literatura de primas, el observatorio reporta cada estimación con su
intervalo, su corrección por comparaciones múltiples y un criterio de «concluyente» fijado de antemano,
y declara cuándo no hay evidencia.

## 3. Método

**Design Science Research** (Hevner et al., 2004; Peffers et al., 2007), en seis actividades:
problema → objetivos → diseño → demostración → evaluación → comunicación.

**Evaluación en rondas** (plantilla de #94):

| Ronda | Qué se evalúa | Evaluación |
|---|---|---|
| Automática | Componentes por separado | E3 (poder explicativo), E5 (tasa de cifras marcadas por condición) |
| Humana | Contra una referencia construida a mano | E1, E2 y E6 (200 avisos anotados a ciegas), E4 (cifras etiquetadas) |
| Caso real | Funcionamiento sostenido | E7 (cortes mensuales sep–nov 2026) |

**Objetivos del artefacto (requisitos de diseño):**
- R1 · Trazabilidad: toda cifra publicada se puede reconstruir desde los datos crudos guardados.
- R2 · Inmutabilidad del histórico: tablas append-only con triggers.
- R3 · Incertidumbre explícita: IC 95 %, corrección BH y un criterio de "concluyente" fijado de antemano, más una prueba
  de equivalencia (TOST, ±15 %) para distinguir "sin prima relevante" de "no concluyente".
- R4 · Anclaje: el LLM solo recibe cifras del contexto versionado.
- R5 · Verificación independiente del modelo.
- R6 · Decisión humana: el sistema marca, no bloquea; aprueba una persona.
- R7 · Reproducibilidad: código público, semillas y cortes fechados.

## 4. Diseño del artefacto

[FIGURA 1: `figuras/arquitectura.svg`]

**4.1 Recolección.**
- Siete fuentes: CompuTrabajo, ElEmpleo, GetOnBoard, LinkedIn, Talent.com, Magneto y Remotive (API pública,
  con atribución).
- Disparo mensual con GitHub Actions (cron); respaldo cifrado antes de cada escritura.
- Torre.ai está desactivado. Glassdoor se descartó por Cloudflare y robots.txt.
- Cambios en el diseño de búsqueda registrados (LinkedIn amplió sus términos el 17-oct-2026) y excluidos de
  las comparaciones entre meses.

**4.2 Limpieza y extracción (reglas explícitas, auditables).**
- Filtro de relevancia temática por título.
- Normalización del salario a COP mensuales. Los rangos se toman en su punto medio; ver la limitación y M2.
- Taxonomía de 31 habilidades con expresiones regulares.
- Experiencia y nivel solo cuando la oferta los dice, con la fuente registrada.
- Rol por título: frases de rol y luego palabras del tema; "Sin clasificar" si no hay coincidencia (hito 55).

**4.3 Almacenamiento.**
- Supabase Postgres con cuatro tablas protegidas (append-only con triggers), índices únicos por (huella, mes)
  y un rol de mínimo privilegio para el pipeline.
- El texto crudo se guarda para recalcular con reglas nuevas sin volver a recolectar.

**4.4 Análisis estadístico.**
- Demanda: % de ofertas por habilidad y mes.
- Primas: OLS de log(salario) con habilidades, nivel, rol, portal y mes; errores HC3.
- Categorías de control con menos de 5 ofertas agrupadas: una dummy de una sola oferta anula HC3 (hito 55).
- Prima = exp(β) − 1, con IC 95 % y q de BH.
- "Concluyente" = q ≤ 0,10 y un IC que no cruza 0. Solo habilidades con n ≥ 20. Robustez dejando fuera cada
  portal.

**4.5 Contexto de mercado e IA generativa.**
- Contexto versionado (id y corte): demanda, roles, primas con su estado y medianas salariales con su n.
- Reglas de evidencia en el prompt: copiar cifras tal cual, "dato no disponible", no proyectar salarios y no
  hablar de tendencia con menos de 3 cortes.
- Gemini 4 Argon con Flash de respaldo. Cada versión registra el modelo y el contexto.

**4.6 Verificador de cifras.**
- Extrae porcentajes, montos y conteos de ofertas.
- Busca cada cifra en el contexto (más el cruce currículo–mercado).
- Comprueba la atribución por cláusula: la habilidad o el rol mencionado junto a la cifra debe ser el dueño
  del dato.
- Comprueba la consistencia de créditos y horas (1 crédito = 48 h = 16 TFD + 32 TTI) y marca siempre las
  tarifas.
- Marca, no bloquea.

**4.7 Revisión humana.**
- Portal con roles (visualizador, aprobador, administrador).
- Acciones: aprobar, rechazar con motivo, ajustar con IA (genera la versión siguiente), reabrir y nueva
  propuesta.
- Auditoría de cada acción.

## 5. Demostración (E7 · caso real)

- **Cortes:** sep, oct y nov 2026. Corte vigente: 2026-11-01.
- **Muestra:** 907 vacantes únicas sep–nov. En noviembre, 382 ofertas de 7 fuentes, 27,5 % con salario
  (`/api/kpis`, corte 2026-11-01).
  Conciliación: 907 ofertas únicas en `dim_ofertas` y en las extracciones; 905 tienen el texto crudo
  guardado. Los análisis que recalculan desde el texto (E1, E3, primas, M6) usan esas 905.
- **Fallos detectados en operación y corregidos** (evidencia de la evaluación continua del DSR):
  - caché de 30 días del tablero (hito 50);
  - login por hashes truncados en compose;
  - clasificación de rol por subcadenas (hito 55);
  - covarianza HC3 degenerada (hito 55).
- **Advertencia:** octubre acumula varias corridas y noviembre una sola; el número de ofertas no se compara
  entre esos meses.

**Tabla 1.** Ofertas por fuente y corte (ofertas distintas en cada mes; consulta de solo lectura a
`fact_extracciones_historico`, 9-nov-2026).

| Fuente | Mercado | sep-2026 | oct-2026 | nov-2026 | Únicas sep–nov |
|---|---|---|---|---|---|
| LinkedIn | Local | 146 | 247 | 169 | 435 |
| ElEmpleo | Local | 74 | 93 | 68 | 145 |
| Talent.com | Local | 36 | 99 | 43 | 140 |
| Magneto | Local | 0 | 89 | 62 | 94 |
| CompuTrabajo | Local | 15 | 23 | 15 | 37 |
| GetOnBoard | Internacional (remoto) | 23 | 26 | 23 | 34 |
| Remotive | Internacional (remoto) | 0 | 2 | 2 | 2 |
| Torre.ai (desactivado) | Internacional (remoto) | 20 | 0 | 0 | 20 |
| **Total** | | **314** | **579** | **382** | **907** |
| Con salario publicado | | 70 | 146 | 105 (27,5 %) | |

Notas:
- Una oferta vigente en varios meses cuenta en cada mes.
- Magneto y Remotive se incorporaron en octubre, y Torre.ai se desactivó.
- LinkedIn amplió sus términos de búsqueda el 17-oct-2026.

## 6. Evaluación

### 6.1 E1 · Extracción frente a la referencia humana

- **Diseño:**
  - 200 avisos estratificados por portal y mes, de 905 únicos (semilla 2026);
  - anotador A los etiqueta todos y B etiqueta 60 para medir el acuerdo;
  - etiquetado ciego (las planillas no muestran la salida del sistema);
  - guía con casos difíciles (`guia_anotacion.md`);
  - correos y teléfonos enmascarados.
- **Métricas:**
  - kappa de Cohen;
  - P/R/F1 micro y macro por habilidad;
  - exactitud y F1 macro de rol;
  - exactitud de nivel y de años;
  - IC por bootstrap (2.000 remuestreos).
  - Excel se evalúa en dos lecturas: cualquier mención y "avanzado" explícito.
- **Herramienta:** `scripts/evaluar_anotacion.py`.

[PENDIENTE: resultados (planillas el 9-nov).]

### 6.2 E2 · Clasificador de rol, publicado frente a corregido

- Las reglas nuevas se ajustaron solo con los 705 avisos fuera de la muestra; los 200 no se miraron.
- En esos 705, cambian de rol 230 (33 %), y "Sin clasificar" queda con 55.

[PENDIENTE: exactitud y F1 macro de cada versión en las 200, con IC pareado.]

### 6.3 E3 · Poder explicativo de la taxonomía (Ao et al., 2023)

- **Datos:** 176 ofertas locales con salario, sep–nov 2026.
- **Validación:** cruzada 5 × 50, semilla 2026. Script: `scripts/analisis_poder_explicativo.py`, con roles
  corregidos (commit `324802e`).

| Modelo | R² dentro de muestra | R² fuera de muestra (media [P2,5; P97,5]) |
|---|---|---|
| Controles (nivel, rol, portal, mes) | 0,604 | 0,485 [0,246; 0,680] |
| Habilidades (ridge) | 0,287* | 0,115 [−0,176; 0,312] |
| Controles + habilidades (ridge) | 0,670* | 0,438 [0,141; 0,626] |
| Texto completo (TF-IDF) | — | 0,509 [0,264; 0,699] |
| Controles + texto | — | 0,570 [0,281; 0,725] |

\* Dentro de muestra, la estimación es OLS.

Lectura:
- Las habilidades explican dentro de muestra una proporción comparable al ~20 % de los diccionarios de #233.
- Fuera de muestra no mejoran a los controles: el aporte con ridge es −0,048 [−0,248; 0,100].
- Lo que el texto capta y la taxonomía no es el nivel educativo, el nivel de cargo y el sector (exploratorio).
- Con los roles corregidos, los controles explican más fuera de muestra (0,431 → 0,485): es evidencia
  indirecta a favor del clasificador nuevo.

[PENDIENTE: confirmar que "dentro de muestra" con controles cambió solo por el rol.]

### 6.4 E4 · Precisión y recall del verificador

- **Diseño:**
  - cifras atómicas (FActScore) de propuestas generadas;
  - muestra estratificada: todas las marcadas, 100 revisadas sin marca y 50 números que el verificador no
    revisa;
  - etiquetado ciego con cuatro categorías: respaldada, mal atribuida, sin respaldo y no verificable;
  - métricas ponderadas por estrato con IC por bootstrap estratificado.
- **Herramienta:** `scripts/evaluacion_ia.py e4-planilla` / `e4-evaluar`.
- **Advertencia metodológica:** el verificador se ajustó el 28-oct-2026 con las propuestas vigentes (commit
  `50a1747`). Sus 3 marcas originales eran falsos positivos que esa corrección eliminó, y hoy marca 0 de
  444 cifras revisadas. Evaluarlo con esas mismas propuestas sería medir dentro de la muestra de ajuste. La
  evaluación válida usa propuestas nuevas, las de E5.

[PENDIENTE: decisión de quién etiqueta y resultados.]

### 6.5 E5 · Efecto del anclaje y del modelo

- **Diseño:** 3 condiciones × 2 modelos (Gemini 4 Argon, Gemini 3.8 Flash) × 2 solicitudes (Diplomado de 8
  créditos en ingeniería de datos en la nube; Microcredencial de 2 créditos sin enfoque) × 3 repeticiones =
  36 generaciones (8-nov-2026), sin modelo de respaldo, temperatura por defecto, verificadas todas contra el
  mismo contexto (c0d2415dbc12, corte 2026-11-01).
- **Condiciones:**
  1. **con contexto**: el prompt de producción;
  2. **sin datos, con reglas**: sin el bloque de datos del observatorio, pero conservando las instrucciones
     contra inventar del encargo y del esquema;
  3. **sin anclaje**: sin datos, sin reglas y con ejemplos neutros en el esquema.

  La condición 2 no se había previsto como tal: era el primer intento de «sin contexto», y mostró que las
  instrucciones del encargo bastan para que el modelo se abstenga. La condición 3 se agregó para tener la
  línea base de un LLM sin anclaje.
- **Herramienta:** `scripts/evaluacion_ia.py e5`, `e5-resumen` (`data/evaluacion_ia/e5_resultados.json`).

| Condición | Modelo | Generaciones | Cifras revisadas | Marcadas | % marcadas [IC 95 % bootstrap por generación] |
|---|---|---|---|---|---|
| Con contexto | Argon | 6 | 410 | 3 | 0,7 % [0,0; 2,0] |
| Con contexto | Flash | 6 | 197 | 0 | 0,0 % |
| Sin datos, con reglas | Argon | 6 | 0 | 0 | — (no escribe cifras de mercado) |
| Sin datos, con reglas | Flash | 6 | 0 | 0 | — |
| Sin anclaje | Argon | 6 | 21 | 21 | 100 % |
| Sin anclaje | Flash | 6 | 32 | 30 | 93,8 % [83,3; 100] |

Lectura preliminar (hasta tener E4):
- Con el contexto, los modelos citan entre 6 y 20 veces más cifras de mercado y casi todas quedan
  respaldadas.
- Sin datos pero con reglas, se abstienen ("dato no disponible"): la regla evita inventar, pero no produce
  evidencia.
- Sin anclaje, casi todas las cifras quedan sin respaldo en el observatorio. Que sean inventadas o externas
  pero ciertas lo decide E4.
- No hay diferencia clara entre Argon y Flash en esta métrica; Argon tarda unas dos veces más (mediana 69 s
  frente a 33 s con contexto).
- Ninguna generación tuvo inconsistencias de créditos y horas.

Limitaciones de E5:
- 6 generaciones por celda.
- El IC por bootstrap se degenera con 0 % o 100 %: [PENDIENTE: reportar además Clopper–Pearson por cifra,
  sabiendo que las cifras de una misma generación no son independientes].
- La tasa de marcas depende de la precisión y el recall del verificador (E4).

### 6.6 E6 · Línea base LLM para la extracción

- El LLM recibe la misma guía (secciones 1–4) y los mismos textos enmascarados que las personas
  anotadoras, y se compara con la misma referencia que E1. Temperatura 0.
- **Herramienta:** `scripts/linea_base_llm.py --ejecutar` (requiere autorización del gasto y del envío
  de los textos).

[PENDIENTE.]

## 7. Hallazgos preliminares del observatorio (demostración, no tendencia)

**Demanda** (noviembre 2026, % de ofertas, n = 382, corte 2026-11-01): SQL 68,1; Python 63,9; ETL 51,6;
Power BI 32,2; Estadística 31,4; ML 29,6; AWS 28,8; Azure 25,1; GCP 23,3; Excel 19,1.
[PENDIENTE: re-generar desde el script del corte antes de citar.]

**Primas por rol** (176 ofertas locales con salario, sep–nov 2026; clasificador corregido; referencia
Analista de Datos):

| Rol | n | Prima | Lectura |
|---|---|---|---|
| Ingeniero de Datos | 39 | +69,5 % [+44,6; +98,8] | Concluyente |
| Científico de Datos | 44 | +52,1 % [+30,4; +77,4] | Concluyente |
| BI | 7 | — | No evaluable (n < 20) |
| ML/AI | 1 | — | No evaluable (n < 20) |
| Desarrollador | 1 | — | No evaluable (n < 20) |
| Sin clasificar | 22 | — | Fuera del modelo |

[PENDIENTE: depende de E2; si el clasificador nuevo no gana, se reporta el publicado.]

**Primas por habilidad.** Ninguna es concluyente con el clasificador corregido
(`data/analytics/robustez_primas.json`).

**Excel:**
- Con el clasificador original, −17,0 % [−27,1; −5,5], q = 0,052, publicado en el portal.
- Con los roles corregidos, −12,5 % [−24,2; +1,1], q = 0,56.
- La asociación negativa coincide en dirección con #195, pero aquí deja de ser concluyente al controlar bien
  el rol: parte de ella era composición de roles.
- La regla del sistema detecta cualquier mención de Excel, no solo "avanzado"; E1 mide ambas lecturas.

**Robustez** (`scripts/robustez_primas.py`, mismas 176 ofertas):

| Especificación | R² | Excel | Habilidades concluyentes |
|---|---|---|---|
| Base (roles corregidos, punto medio) | 0,564 | −12,5 % [−24,2; +1,1] | Ninguna |
| Salario = extremo inferior del rango (87 rangos) | 0,554 | −12,4 % [−24,2; +1,2] | Ninguna |
| Salario = extremo superior | 0,577 | −12,6 % [−24,3; +1,1] | Ninguna |
| + nivel educativo (texto) | 0,644 | −8,0 % [−20,1; +5,9] | Ninguna |
| + nivel educativo + sector (texto) | 0,658 | −8,9 % [−21,0; +5,1] | Ninguna |
| Sin duplicados entre portales | 0,571 | −14,2 % [−25,5; −1,3], q = 0,35 | Ninguna |

**Equivalencia: «sin prima relevante» frente a «no concluyente»** (TOST, margen ±15 %, IC 90 % con HC3;
mismas 176 ofertas):
- Criterio: una prima asociada menor que ±15 % no justificaría reordenar el peso de una habilidad en un plan
  de estudios (enfoque de margen sustantivo [@lakens2017equivalence; @lakens2018equivalence]; equivalencia sobre
  coeficientes de regresión, [@hartman2018equivalence]; en economía, [@fitzgerald2026need]).
- Solo **SQL** queda dentro del margen: −0,2 %, IC 90 % [−11,4; +12,5], p_TOST = 0,025. Se mantiene en las
  cinco especificaciones de robustez (IC 90 % entre [−8,3; +13,4] y [−11,5; +12,5]). Con corrección BH
  sobre las 11 habilidades no se sostiene (q = 0,27): es una indicación, no una conclusión.
- Las otras 10 habilidades son no concluyentes también en este sentido: los datos no permiten afirmar que
  tengan prima ni que no la tengan.
- Margen mínimo con el que cada habilidad sería equivalente (para que el lector aplique su propio
  criterio): SQL ±12,5 %; Python ±18,1 %; ML ±18,6 %; ETL ±20,1 %; AWS ±20,6 %; R ±20,7 %; Excel ±22,5 %;
  Power BI ±24,5 %; Spark ±27,7 %; Estadística ±36,3 %; Azure ±37,9 %.
- Con n = 176, ningún margen menor de ~12 % podría declarar equivalencia: la precisión, no el método, es el
  límite.

Lectura:
- Las conclusiones no dependen del supuesto del punto medio.
- El nivel educativo explica una parte importante del salario (R² +0,08) y absorbe parte del efecto de
  Excel.

**Duplicados entre portales** (905 ofertas únicas):
- 43 pares, que involucran 64 ofertas: 36 sobrantes (4,0 %).
- 34 de los pares son LinkedIn / Talent.com (Talent.com agrega avisos de otros portales).
- Criterio: mismo título y empresa (31), o coseno TF-IDF ≥ 0,9 (12). Título + empresa es una cota
  superior: algunos pares tienen texto muy distinto (puestos distintos con el mismo nombre en empresas
  grandes, o texto truncado).

**Cambio de roles entre meses:** sin cambios concluyentes sep → oct (portales comparables). Con LinkedIn
incluido aparecía un falso "Data Engineer emergente" por el cambio de búsqueda: un ejemplo de por qué se
registran los cambios de diseño. Con los roles corregidos (8-nov-2026), tampoco hay cambios
concluyentes: sep → oct, sin LinkedIn (n 146 → 241), el mayor cambio es Ingeniero de Datos, de 17,8 % a
24,1 % (q = 0,37); oct → nov, con los 7 portales (n 579 → 382), ningún rol cambia más de 2,1 pp (q = 0,99).
Octubre acumula varias corridas y noviembre una sola.

## 8. Discusión

[PENDIENTE: escribir con los resultados.]

Ejes previstos:
1. **Reglas frente a LLM** (E1 frente a E6): auditabilidad y costo frente a cobertura.
2. **Anclaje y verificación** (E4, E5): qué atrapa el verificador y qué no, por ejemplo cifras calculadas o
   redondeadas y números fuera de sus patrones.
3. **El valor del observatorio como "medidor honesto":** casi nada es concluyente con 176 ofertas, y decirlo
   es parte del diseño (R3).
4. **Errores encontrados por la propia evaluación** (rol, HC3, caché): el ciclo DSR en acción.

## 9. Limitaciones

1. Representatividad de los avisos en línea y sesgo por los términos de búsqueda (#117, #109).
2. Tres cortes no son una tendencia.
3. Salario publicado solo en el 27,5 % de las ofertas de noviembre, casi todo de tres portales locales;
   rangos tomados en su punto medio (#195; M2 muestra que no cambia las conclusiones).
4. Duplicados entre portales: 4,0 % estimado, no eliminados en el pipeline (#118).
5. Taxonomía fija de 31 habilidades frente a una terminología que cambia (#771, #152).
6. Rol por título.
7. Asociación, no causalidad.
8. LLM no determinista; el verificador solo cubre %, dinero y conteos de ofertas.
9. Ética y legalidad del scraping: términos de uso, LinkedIn y hiQ (#624), Krotov et al. (2020), #643.
10. Datos personales en el texto crudo: se enmascaran en las exportaciones (B43).
11. [PENDIENTE: límites propios de la anotación (dos anotadores, una sola guía).]
12. El margen de equivalencia (±15 %) se fijó el 9-nov-2026 por criterio curricular y antes de calcular la
    prueba, pero cuando las estimaciones puntuales ya eran públicas: no es un margen prerregistrado en
    sentido estricto. Por eso se reporta también el margen mínimo de cada habilidad.

## 10. Conclusiones y trabajo futuro

[PENDIENTE.]

Trabajo futuro:
- taxonomía alineada con ESCO y detección de términos nuevos (#152, #154), usando `otras_habilidades` de la
  anotación;
- complementariedad de habilidades (Stephany & Teutloff, 2024);
- validación externa con estadística oficial (#109, #122, #789);
- regresión por intervalos;
- deduplicación en el pipeline;
- prueba de equivalencia con un margen prerregistrado antes de ver cualquier estimación, y con más ofertas
  (la precisión actual solo permite márgenes de ~12 % o más).

## Disponibilidad, uso de IA y ética

- **Código:** `github.com/jfbernalp/proyecto_investigativo` (commit de la versión evaluada:
  [PENDIENTE]).
- **Datos:** agregados públicos. El texto de las ofertas no se publica: contiene datos de terceros y está
  sujeto a los términos de los portales.
- **Uso de IA:**
  - Gemini en el artefacto;
  - Claude como asistente de programación y redacción;
  - Scopus AI solo como mapa bibliográfico, no como fuente (`bibliografia/revision_informe_scopus_ai.md`).
- [PENDIENTE: conflicto de intereses y financiación.]

## Figuras y tablas previstas

1. Arquitectura (`figuras/arquitectura.svg`).
2. Ejemplo de propuesta con una cifra respaldada y una marcada.
3. Tabla de E1 (P/R/F1 por habilidad) y de E2 (rol).
4. Tabla o figura de E5 (tasa de cifras marcadas por condición).
5. Tabla de E3.
6. Primas por rol y robustez.
