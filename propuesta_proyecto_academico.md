# PROPUESTA DE PROYECTO DE INVESTIGACIÓN APLICADA

---

## 1. INFORMACIÓN GENERAL DEL PROYECTO

* **Título del Proyecto:**  
  *Desarrollo de un Sistema Automatizado de Web Scraping y Minería de Datos para el Análisis de Brechas de Habilidades, Demanda Laboral y Valoración Salarial en los Roles de Científico y Analista de Datos.*
* **Línea de Investigación:** Ciencia de Datos, Minería de Texto (NLP) e Inteligencia del Mercado Laboral (*Labor Market Intelligence*).
* **Duración Estimada:** 6 meses (24 semanas).
* **Población / Dominio de Estudio:** Ofertas de empleo publicadas en plataformas web líderes de reclutamiento para perfiles de Analítica y Ciencia de Datos.

---

## 2. PLANTEAMIENTO DEL PROBLEMA

En la economía digital actual, las disciplinas de Ciencia de Datos y Analítica de Datos experimentan una rápida evolución tecnológica. Las herramientas, frameworks y competencias demandadas por la industria cambian con alta velocidad, generando una desconexión o asimetría de información entre:
1. Los programas de formación académica y técnica.
2. Los profesionales que buscan optimizar su perfil laboral.
3. Las necesidades reales y las compensaciones salariales ofrecidas por las organizaciones.

A pesar de que existen múltiples portales de empleo, la información se encuentra fragmentada, no estandarizada y en formatos de texto no estructurado. La mayoría de los requerimientos y paquetes salariales están ocultos o redactados de forma heterogénea, lo que impide a los investigadores y tomadores de decisiones realizar análisis cuantitativos rigurosos sobre qué habilidades específicas generan mayor valor económico en el mercado.

---

## 3. JUSTIFICACIÓN

El desarrollo de una plataforma automatizada de extracción y análisis de datos laborales permite transformar texto no estructurado en inteligencia accionable. Este proyecto aporta valor en tres dimensiones:
* **Académica:** Proporciona evidencia empírica cuantitativa sobre la brecha de habilidades (*skills gap*) para retroalimentar mallas curriculares universitarias.
* **Profesional:** Orienta a estudiantes y profesionales sobre qué tecnologías priorizar en su ruta de aprendizaje para maximizar su empleabilidad y retorno salarial.
* **Técnica:** Demuestra la aplicación de buenas prácticas de ingeniería de datos (scraping ético, orquestación, esquemas normalizados) y ciencia de datos (procesamiento de lenguaje natural, modelos hedónicos salariales y analítica visual).

---

## 4. OBJETIVOS DEL PROYECTO

### 4.1. Objetivo General
Desarrollar un sistema integral y automatizado de web scraping, minería de texto y análisis econométrico-estadístico sobre los principales portales de empleo, con el fin de cuantificar la demanda de habilidades técnicas y su impacto en la compensación salarial para los perfiles de Científico de Datos y Analista de Datos durante un periodo de 6 meses.

### 4.2. Objetivos Específicos
1. **Diseñar e implementar un motor modular de extracción automatizada (Web Scraping)** capaz de recopilar de forma continua y ética ofertas de empleo procedentes de múltiples portales (estáticos y dinámicos), estandarizándolas bajo un esquema de datos canónico y validado.
2. **Construir un módulo de Procesamiento de Lenguaje Natural (NLP) y Minería de Datos** para desagregar, clasificar y normalizar los requisitos de las vacantes (años de experiencia, nivel educativo, tecnologías y habilidades blandas), superando la falta de estructuración del texto original.
3. **Modelar estadísticamente la relación entre habilidades demandadas, nivel de experiencia y bandas salariales**, evaluando la prima económica asociada a cada competencia y desplegando los resultados en un dashboard interactivo de consulta pública y analítica.

---

## 5. MARCO METODOLÓGICO Y FASES DE DESARROLLO

El proyecto se ejecutará bajo una metodología iterativa dividida en 5 fases secuenciales:

```
[ Fase 1: Fundamentación y Arquitectura ] (Mes 1)
                  │
                  ▼
[ Fase 2: Desarrollo de Scrapers e Ingesta ] (Mes 2)
                  │
                  ▼
[ Fase 3: Minería de Texto, Normalización y Deduplicación ] (Mes 3 - 4)
                  │
                  ▼
[ Fase 4: Modelado Estadístico y Análisis de Correlación ] (Mes 4 - 5)
                  │
                  ▼
[ Fase 5: Visualización, Dashboard y Divulgación ] (Mes 6)
```

---

### FASE 1: Fundamentación Teórica, Legal y Diseño de Arquitectura (Mes 1)
* **Revisión del Estado del Arte:** Estudio de marcos internacionales de clasificación de competencias laborales (ESCO, O*NET) y metodologías previas de scraping laboral.
* **Auditoría de Portales:** Análisis técnico de plataformas seleccionadas (inspección de APIs internas, comportamiento de carga JavaScript, mecanismos de protección anti-bot).
* **Protocolo Ético y Legal:** Establecimiento de directrices de scraping responsable (respeto de `robots.txt`, tasa controlada de peticiones, anonimización de datos de reclutadores).
* **Diseño del Esquema Canónico:** Definición del contrato de datos unificado mediante Pydantic (campos atómicos para título, empresa, salario, ubicación, requisitos).

---

### FASE 2: Desarrollo de Scrapers y Pipeline de Ingesta (Mes 2)
* **Desarrollo de Adaptadores por Portal:**
  * Scrapers asíncronos para sitios estáticos/paginados (ej. CompuTrabajo, Magneto).
  * Scrapers con emulación de navegador (Playwright) para portales dinámicos (ej. LinkedIn, Indeed).
* **Control de Resiliencia y Manejo de Errores:**
  * Captura y registro explícito de códigos HTTP (403, 404, 429, 500/505).
  * Rotación de encabezados (`User-Agent`, `Accept-Language`) y manejo de retardos aleatorios (*exponential backoff*).
* **Persistencia de Datos Crudos:** Almacenamiento en Data Lake local particionado por fecha y portal de origen (formatos JSONL y Parquet).

---

### FASE 3: Minería de Texto, Normalización y Deduplicación Cross-Portal (Mes 3 - 4)
* **Algoritmo de Deduplicación Multicanal:**
  * Detección y fusión de ofertas duplicadas publicadas simultáneamente en varios portales mediante similitud de cadenas (*Jaro-Winkler / TF-IDF Cosine Similarity*).
* **Extracción de Variables Atómicas:**
  * Normalización de salarios a valor numérico mensual homogéneo (COP / USD).
  * Extracción con expresiones regulares de Años de Experiencia y Nivel Educativo formal.
* **Motor de Clasificación de Habilidades (NLP):**
  * Taxonomía especializada de Data Science (Lenguajes, Big Data, Cloud, ML/AI, BI, Bases de Datos).
  * Generación de matrices en Formato Ancho (*One-Hot Encoding*) y Formato Largo (*Tidy Data / Explode*).

---

### FASE 4: Modelado Econométrico y Análisis Estadístico (Mes 4 - 5)
* **Análisis Descriptivo y de Frecuencia:** Participación de mercado por tecnología y rankings de demanda relativa.
* **Análisis de Correlación y Primas Salariales:**
  * Matrices de correlación de Pearson y correlación punto-biserial entre habilidades y salario.
  * Cálculo de la Prima Salarial Neta ($COP y %) por tecnología frente a la media del mercado.
  * Modelos de regresión multivariada para aislar el valor económico de cada habilidad controlando por años de experiencia y ubicación.
* **Pruebas de Hipótesis:** Validación de significancia estadística (t-test / Mann-Whitney U) entre perfiles especializados vs. perfiles tradicionales de BI.

---

### FASE 5: Visualización, Dashboard y Divulgación de Resultados (Mes 6)
* **Desarrollo de Dashboard Analítico:**
  * Construcción de una aplicación web interactiva (Streamlit / Power BI) con mapas de calor, distribuciones salariales, filtros dinámicos por ciudad, seniority y stack.
* **Generación de Dataset Abierto (Open Data):** Publicación del dataset curado y anonimizado para la comunidad académica.
* **Elaboración del Informe Final y Artículo Científico:** Redacción del manuscrito con hallazgos clave, discusión metodológica y recomendaciones curriculares.

---

## 6. CRONOGRAMA DE ACTIVIDADES (PLAN DE 6 MESES / 24 SEMANAS)

| Actividad / Hito | Mes 1 | Mes 2 | Mes 3 | Mes 4 | Mes 5 | Mes 6 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1.1. Revisión de literatura y taxonomías (ESCO/O*NET) | **X** | | | | | |
| 1.2. Auditoría técnica de portales y protocolo ético | **X** | | | | | |
| 1.3. Diseño del esquema de datos canónico | **X** | | | | | |
| 2.1. Programación de scrapers para portales estáticos | | **X** | | | | |
| 2.2. Programación de scrapers dinámicos (Playwright) | | **X** | | | | |
| 2.3. Pruebas de resiliencia y manejo de errores HTTP | | **X** | | | | |
| 3.1. Algoritmo de deduplicación cross-portal | | | **X** | | | |
| 3.2. Normalización de salarios, experiencia y educación | | | **X** | **X** | | |
| 3.3. Motor de extracción y etiquetado de habilidades (NLP)| | | | **X** | | |
| 4.1. Análisis exploratorio y matrices de correlación | | | | **X** | **X** | |
| 4.2. Modelado de primas salariales y pruebas de hipótesis | | | | | **X** | |
| 5.1. Diseño e implementación del Dashboard interactivo | | | | | **X** | **X** |
| 5.2. Redacción del informe final y artículo académico | | | | | | **X** |

---

## 7. STACK TECNOLÓGICO Y HERRAMIENTAS

* **Lenguaje Principal:** Python 3.11+
* **Extracción y Scraping:** `Scrapy`, `Requests`, `Playwright`, `BeautifulSoup4`
* **Procesamiento y Modelado de Datos:** `Pandas`, `Polars`, `NumPy`, `Pydantic`
* **Procesamiento de Lenguaje Natural (NLP):** `spaCy`, `Regex`, `scikit-learn`
* **Análisis Estadístico y Econométrico:** `SciPy`, `Statsmodels`
* **Visualización y Dashboard:** `Matplotlib`, `Seaborn`, `Plotly`, `Streamlit` / `Power BI`
* **Almacenamiento de Datos:** Archivos estructurados `Parquet`, `Excel (OpenPyXL)` y base de datos relacional `PostgreSQL` / `DuckDB`

---

## 8. RESULTADOS Y ENTREGABLES ESPERADOS

1. **Software y Código Fuente:** Repositorio en GitHub con la arquitectura modular de web scraping, scripts de procesamiento NLP y análisis estadístico debidamente documentados.
2. **Base de Datos Consolidada (Open Dataset):** Conjunto de datos limpio, anonimizado y estructurado en formato Parquet/Excel que sirva como insumo para futuras investigaciones en economía laboral y educación.
3. **Dashboard Web Interactivo:** Herramienta interactiva de visualización para que estudiantes, universidades y empresas consulten la demanda de habilidades y bandas salariales en tiempo real.
4. **Documento de Investigación / Artículo Científico:** Informe final de investigación con rigor metodológico, análisis econométrico de las habilidades más valoradas y recomendaciones para el cierre de la brecha formativa.
