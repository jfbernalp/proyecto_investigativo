# Matriz comparativa: referencias clave para el Artículo 1

Artículo 1: **diseño y evaluación de un observatorio auditable con IA generativa anclada en datos**
(Design Science Research). Los hallazgos del observatorio entran como demostración preliminar; el núcleo
es la evaluación del componente de IA.

**Fuentes:**
- `scopus.bib`: biblioteca original, 66 referencias;
- búsquedas Q0–Q9 (`consultas_scopus.md`): 1.070 referencias únicas, de las que se seleccionaron 92
  (`seleccion_final.md`).

La matriz usa solo lo que dicen los resúmenes. **Confirmar con el texto completo antes de citar cifras o
métodos.** Los números (#) son el `Id` de `seleccion_final.md`; los de la biblioteca original llevan su
número de `clasificacion_preliminar.md` precedido de «B».

Actualizada el 7-nov-2026.

---

## 1. Método: Design Science Research (DSR) con LLM

| Ref. | Qué hace | Evaluación | Qué tomamos |
|---|---|---|---|
| Hevner et al. (2004), *MISQ*; Peffers et al. (2007), *JMIS* | Marco de DSR y su metodología en seis actividades | Directrices de diseño y de evaluación del artefacto | Estructura del artículo: problema → objetivos → diseño → demostración → evaluación → comunicación. |
| #96 Iaroshev et al. (2024), *Applied Sciences* | DSR para un sistema RAG sobre informes financieros | Fidelidad, relevancia de contexto y de respuesta, comparando configuraciones de modelos. **Las preguntas cuantitativas obtuvieron menos puntaje que las cualitativas.** | El precedente más cercano: DSR + LLM anclado + cifras. Su hallazgo de que los números son el punto débil motiva nuestro verificador. |
| #93 Li et al. (2025), *J. Information Systems* | DSR para extraer indicadores financieros de PDF con LLM | 99,5 % de exactitud en prueba y ~96 % fuera de muestra | Modelo de cómo reportar exactitud en muestra y fuera de muestra. |
| #94 Schinckus et al. (2026), *BISE* | DSR: 19 requisitos de diseño → sistema multiagente con LLM | Tres rondas: demostración con expertos, cuasi-experimento y caso real | **Plantilla de evaluación en rondas**, aplicable a la nuestra (métricas automáticas, revisión humana, caso real). |
| #60 (2026), *Information Systems* | Expertos en el ciclo para validar datos con IA generativa | Validación interactiva de la calidad de los datos | Respalda el papel del aprobador humano. |

## 2. Verificación de cifras y alucinación en LLM

| Ref. | Qué muestra | Relación con nuestro verificador |
|---|---|---|
| Ji et al. (2023), *ACM CSUR*; #294 (2023, EMNLP) | Definición, tipos y medición de la alucinación | Marco conceptual: lo nuestro es alucinación **factual numérica** y de **atribución**. |
| Lewis et al. (2020), RAG | Generación anclada en documentos recuperados | Nuestro «contexto de mercado» es una forma de anclaje (contexto estructurado en lugar de recuperación). |
| Min et al. (2023), FActScore | Precisión factual descomponiendo el texto en afirmaciones atómicas | **Análogo metodológico directo:** descomponemos el texto en cifras atómicas y verificamos cada una. |
| #275 SCITAB (2023, EMNLP) | Verificar afirmaciones contra **tablas** científicas; casi todos los modelos rinden cerca del azar salvo GPT-4 | Verificar números contra datos tabulares es difícil para los LLM: justifica hacerlo con **reglas deterministas** fuera del modelo. |
| #311 Buchanan et al. (2024), *American Economist* | **Más del 30 % de las citas** de GPT-3.5 en economía no existen; poca mejora en GPT-4; peor cuanto más específica la pregunta | Motivación cuantitativa: los LLM inventan con seguridad. |
| #332 (2023), *Psychiatry Research* (136 citas) | Fabricación espontánea de citas (ChatGPT, Bard) | Igual que #311, en otro dominio. |
| #255 (2024), *Nature* (1.099 citas) | Detectar alucinaciones con entropía semántica | Enfoque alternativo (incertidumbre del modelo); el nuestro verifica contra la fuente, sin depender del modelo. |
| #74 (2024), AAAI Spring Symposium | Verificación semántica en sistemas RAG (posición) | Antecedente conceptual de verificar después de generar. |
| B64 VeriFlow (2026), *LNBIP* | Verificación multidimensional (estructural, semántica, ejecutable) de salidas de LLM | **Análogo de diseño:** nuestras dimensiones son existencia, atribución, consistencia y tarifas. |
| B52 (2026), *LNCS* | Exactitud de LLM citando normativa; 143 preguntas validadas por expertos | Evaluación de anclaje con supervisión profesional. |

## 3. Extracción de habilidades: métodos y cómo evaluarlos

| Ref. | Tarea y datos | Métricas y resultado | Lección |
|---|---|---|---|
| #233 Ao et al. (2023), *IP&M* | Compara diccionarios vs. modelos de tópicos en 1.158.926 avisos (Reino Unido) | **Métrica: % de la variación salarial explicada por las habilidades extraídas.** Diccionarios ~20 %; LDA 48,3 % pero menos interpretable | **Evaluación aplicable ya a nuestras reglas** sin etiquetado manual; ilustra la tensión entre poder explicativo e interpretabilidad. |
| SkillSpan, Zhang et al. (2022), NAACL | Conjunto anotado de habilidades en avisos en inglés | Guías de anotación y acuerdo entre anotadores | **Base para nuestras guías de etiquetado.** |
| #234 (2021), *IEEE Access* (102 citas); #227 Senger et al. (2024), NLP4HR | Revisiones de la extracción de habilidades | Mapa de métodos, datos y terminología | Estado del arte de la tarea. |
| #217 (2024), NLP4HR | Aprendizaje en contexto con LLM frente a etiquetado BIO | Supera límites del enfoque supervisado | Línea base LLM natural. |
| #238 Kavargyris et al. (2026), *Applied Sciences* | Herramienta LLM (ESCOX) frente a etiquetas de expertos de EURES | Acuerdo, divergencias estructurales, alucinación y no determinismo | **Plantilla para evaluar nuestra línea base LLM** contra referencia humana. |
| #242 (2026), *CCIS* | NER con encoders vs. LLM en 4.000 avisos rusos etiquetados | Comparación directa | Diseño de comparación reglas o modelo vs. LLM sobre los mismos avisos. |
| B30 (2025), *LNCS* | LLM vs. NLP tradicional en 400 documentos curriculares estratificados | RAG fue lo mejor; LLM sin contexto, peor que el NLP tradicional | Muestra estratificada real y anclaje. |
| B61 (2026), *RecSys* | Sesgo de simplicidad en recomendadores de habilidades | Datos sintéticos y etiquetas incompletas inflan métricas | Usar avisos reales, no sintéticos. |
| B39 (2025), *FIE*, WIP | BERT vs. Gemini/Llama con datos sintéticos | Recall 0,78 (BERT), precisión 0,64 (generativos) | Referencia, no comparable directamente. |
| #152 SkiLLens (2026), EACL; #154 SkiLLink (2026) | Habilidades nuevas en millones de avisos con humano en el ciclo, enlazadas a ESCO | Validación con revisión humana | Taxonomía que evoluciona; nuestra taxonomía es fija y pequeña. |
| #156 (2025), *Digital Government* | IA generativa para extraer información estructurada de avisos de todo EE. UU. | Escala nacional | Alternativa LLM a nuestras reglas. |

## 4. Representatividad y validez de los avisos en línea (limitaciones)

| Ref. | Hallazgo | Implicación |
|---|---|---|
| Hershbein & Kahn (2018), *AER*; Deming & Kahn (2018), *JOLE* | Los avisos en línea como medida válida de requisitos de habilidades | Respaldo a nuestra fuente de datos. |
| #117 Kureková et al. (2015), *IZA J. Labor Econ.* (72 citas) | Problemas metodológicos de las vacantes en línea; difícil ajustar la representatividad | Marco de limitaciones. |
| #109 Lovaglio & Mezzanzanica (2026), *Labour* | Los avisos en línea **sobrerrepresentan** frente a la encuesta de fuerza laboral (+40 % frente a contratados recientes); los modelos de selección reducen el sesgo a la mitad | Cuantifica el sesgo; posible trabajo futuro (calibrar con datos oficiales). |
| #120 (2026), *J. Forecasting*; #122 (2021), *Survey Res. Methods*; #142 (2025), *Stat. J. IAOS* | Avisos no representativos combinados con estadística oficial mediante calibración | Vía de validación externa para el observatorio. |
| #163 Daly et al. (2025), *Labour Economics* | Las habilidades de los avisos reflejan las que se usan en el puesto (datos daneses) | Validez de medir habilidades desde avisos. |
| #118 (2021), ACM | Detección de avisos duplicados entre portales | Nuestra huella por portal y código no detecta el mismo aviso publicado en dos portales: limitación. |

## 5. Primas salariales desde avisos (contexto de los resultados preliminares)

| Ref. | Método y datos | Resultado | Relación |
|---|---|---|---|
| Stephany & Teutloff (2024), *Research Policy* | Valor de 962 habilidades según su complementariedad | El valor de una habilidad depende de con qué otras se combina | Respalda leer el rol (conjunto de habilidades) además de la habilidad suelta. |
| #195 Zhong et al. (2023), *JASA* | Salario como **intervalo**; avisos de **científicos y analistas de datos** en China | Usar el punto medio sesga los estimadores. **Excel, Office y recolección de datos se asocian negativamente con el salario** | **Coincide con nuestra prima negativa de Excel Avanzado (−17,0 %).** Y señala una limitación de nuestro método: usamos el punto medio. |
| #186 García-Lázaro et al. (2025), *Economics Letters* | Habilidades digitales y salario ofrecido dentro de ocupaciones (Reino Unido) | +5,8 % por habilidades digitales; IA y ciberseguridad +8,6 % a +9,7 % | Método comparable (dentro de ocupación); orden de magnitud de referencia. |
| #175 Alekseeva et al. (2021), *Labour Economics* (263 citas) | Demanda de habilidades de IA en vacantes de EE. UU., 2010–2019 | Aumento fuerte de la demanda | Contexto de demanda. |
| #176 (2025), *Technol. Forecast. Soc. Change* | Contratación por habilidades vs. título en 11 M de vacantes (Reino Unido) | Más peso a habilidades en IA y empleos verdes | Contexto. |
| #179 Delgado Helleseter (2020) | Prima del inglés con avisos de **Computrabajo México** | ~28 %, comparable a un título universitario | Antecedente latinoamericano con nuestra misma fuente. |
| #199 (2025), *Estudios de Economía* | Prima por contenido de tareas, 189.000 avisos de Chile (2009–2018) | Evidencia débil | Antecedente regional; muestra lo difícil de obtener resultados concluyentes. |
| #203, #202, #233 | Primas por conjuntos de habilidades (red), habilidades blandas en TI (Rusia), poder explicativo de la extracción | — | Métodos alternativos. |

## 6. Observatorios, alineación currículo–mercado y casos cercanos

| Ref. | Qué hace | Relación |
|---|---|---|
| B43 Kapa & Schaefer (2026), *MethodsX* | Pipeline reproducible de un portal alemán; validación externa (Spearman 0,91); anonimización con LLM | Antecedente de sistema más cercano. |
| #150 Jēkabsone et al. (2026), *Education Sciences* | ~30.000 avisos (Letonia) + ESCO + currículo + **entrevistas con expertos** → **microcredenciales** | **Caso de uso casi idéntico.** El emparejamiento estricto uno a uno con ESCO **sobreestima las brechas** curriculares. |
| #136 (2026), *Discover AI* | Marco de analítica curricular con IA (oferta vs. demanda de habilidades) | Marco comparable. |
| #504 Genç et al. (2026), *BMC* | Compara versiones de ChatGPT diseñando programas, con rúbrica de expertos, Friedman y Wilcoxon | **Diseño de evaluación para nuestra comparación Flash vs. Argon.** |
| #354 (2026), IEEE INES; #412 (2026), *Quality & Quantity*; #367 (2025), ASEE | LLM en diseño curricular con humano en el ciclo y gobernanza | Respalda la aprobación humana obligatoria. |
| #469 Kasneci et al. (2023), *Learning & Individual Differences* (6.736 citas) | Oportunidades y riesgos de los LLM en educación | Cita de contexto obligada. |
| B44 (2026), revisión PRISMA | Problemas del campo: sesgo monolingüe, sin datasets estándar, validación limitada | **Marco del aporte.** |
| #906 (2018), *PNAS*; #903 (2025), *Industry & Higher Education* | Brechas entre investigación, educación y empleo; brecha universidad–industria en IA (Reino Unido) | Contexto del problema. |

## 7. Roles de datos (nuestro dominio)

| Ref. | Datos | Relación |
|---|---|---|
| #941 Debortoli et al. (2014), *BISE* (215 citas) | Habilidades de BI vs. big data en avisos de monster.com | Antecedente clásico del dominio. |
| #951 (2019), *J. Education for Business* (97 citas) | Analista de negocio, analista de BI, analista de datos y científico de datos | Mismos roles que los nuestros. |
| #949 (2022), *European Management Journal* (86 citas) | Perfil de empleabilidad del científico de datos | Contexto del rol. |
| #946 Dong & Triche (2020), *JISE* | 9.000 avisos de analista de datos de nivel inicial, **2014–2018 (longitudinal)** | Diccionario propio; crecen Python, Tableau y R. **Antecedente longitudinal de nuestro dominio.** |
| #985 (2023), *J. Global Inf. Management* | 2.500 avisos de analista de datos en LinkedIn | Brecha entre universidad y empresa. |
| #926 (2025), *Employee Relations* | 18.947 avisos de IA: mapea habilidades y **clasifica carreras** | Relevante para corregir nuestra clasificación de rol. |

## 8. América Latina y Colombia

| Ref. | Datos | Relación |
|---|---|---|
| #771 Suárez-Rodríguez et al. (2026), *Social Sciences & Humanities Open* | 14.227 avisos de **Computrabajo** y Adzuna, 7 países, feb-2022 a sep-2025; series de tiempo interrumpidas | **Análogo regional más cercano.** Hallazgo: tras ChatGPT cambió sobre todo la **terminología** de las habilidades más que el volumen. Advierte que la taxonomía debe actualizarse. |
| #776 (2026), *Int. J. Information Management* | Mercado de IA en Chile con avisos alineados a ESCO | Antecedente regional. |
| #760 (2023), *Work Organisation, Labour & Globalisation* | Extractor de habilidades sobre avisos de Chile | Antecedente regional. |
| #753 (2021), *Latin American Economic Review* | Web scraping de avisos en México durante la covid-19 | Uso del scraping de avisos en la región. |
| #750 (2018), ICAI | Scraping de **Computrabajo Ecuador** | Misma fuente. |
| #789 (2014), *IZA J. Labor & Development* | **Índice de vacantes de Colombia 1976–2012** (avisos en prensa; Uniandes) | Antecedente colombiano y posible referencia para validar tendencias. |
| #759 (2011), *Revista de Economía Institucional* | ¿Qué son los observatorios del mercado de trabajo y cómo funcionan? | Marco conceptual de «observatorio» desde Colombia. **Sin resumen: leer el texto.** |
| B9 (2023), *RISTI* | Scraping de profesiones en México | Antecedente regional. |

## 9. Ética y legalidad del web scraping

| Ref. | Aporte | Relación |
|---|---|---|
| Krotov et al. (2020), *Commun. AIS* | Áreas de riesgo legal y ético del scraping | Marco base para la sección de ética. |
| #643 Brown et al. (2025), *Big Data & Society* | Marco legal, ético, institucional y científico para investigadores (EE. UU.) | Recomendaciones prácticas. |
| #624 Torre de Silva & López de Letona (2024), *Global Privacy Law Review* | Caso ***hiQ Labs v. LinkedIn***; EE. UU. vs. UE/RU: el scraping no es ilícito per se, pero debe respetar derecho penal, protección de datos, propiedad intelectual y contratos | **Referencia directa para la cuestión de LinkedIn.** |
| #604 (2022), *Quality & Quantity* | Obstáculos técnicos, legales y éticos del scraping en ciencias sociales | Marco. |
| #7 (2026), *Data & Knowledge Engineering* | Revisión sistemática del scraping, incluidos enfoques con LLM y aspectos legales y éticos | Estado del arte reciente. |
| B58 Posada (2026) | Trabajo de datos y colonialidad en América Latina | Perspectiva regional. |

## 10. Métodos estadísticos que usamos

Benjamini & Hochberg (1995), *JRSS-B*, para la corrección por comparaciones múltiples, y MacKinnon &
White (1985), *J. Econometrics*, para los errores robustos HC3.

---

## Implicaciones para la evaluación del Artículo 1

1. **Estructura DSR en rondas** (Peffers; #94):
   - métricas automáticas del verificador;
   - revisión humana de una muestra;
   - el sistema funcionando en un caso real (cortes mensuales).
2. **Evaluación de la extracción en dos frentes:**
   - **% de variación salarial explicada** (#233), aplicable ya;
   - **etiquetado manual de unos 200 avisos reales** con guías al estilo SkillSpan, dos anotadores y su
     acuerdo (B30, B61), con una **línea base LLM** sobre los mismos avisos (#238, #242, #217).
3. **Evaluación del verificador:** precisión y recall de sus marcas frente a la revisión humana. La
   descomposición en cifras atómicas se justifica con FActScore, y verificar con reglas fuera del modelo
   con SCITAB (#275) y #96.
4. **Comparación de modelos** (Flash vs. Argon) con rúbrica de expertos y pruebas no paramétricas (#504).
5. **Validez externa:** comparar tendencias con fuentes independientes (#109, #122, #789).
6. **Limitaciones que la literatura obliga a declarar:**
   - representatividad (#109, #117);
   - salario como intervalo (#195);
   - duplicados entre portales (#118);
   - taxonomía fija frente a la evolución terminológica (#771, #152);
   - datos personales en el texto crudo (B43);
   - legalidad del scraping (#624, Krotov).
7. **Coincidencia externa con nuestros resultados:** la asociación negativa de Excel con el salario en
   avisos de científicos y analistas de datos (#195) concuerda con nuestra prima de Excel Avanzado.
