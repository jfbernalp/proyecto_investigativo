# 📓 BITÁCORA DEL PROYECTO DE INVESTIGACIÓN

**Proyecto:** Observatorio e Inteligencia de Mercado Laboral en Ciencia y Analítica de Datos Mediante Web Scraping, Minería de Texto y Modelado Econométrico  
**Fecha de Actualización:** 12 de Septiembre de 2026  
**Roles del Equipo:** Científico de Datos, Ingeniero de Datos, Arquitecto de Software  
**Entorno de Ejecución:** macOS / Python 3.14 / SQLite / PostgreSQL / Streamlit / GitHub Actions  

---

## 1. Contexto, Motivación y Objetivos del Proyecto

### 1.1 Planteamiento del Problema
El mercado laboral en tecnología (particularmente en **Ciencia de Datos**, **Analítica de Datos** e **Ingeniería de Datos**) se caracteriza por una rápida evolución en las habilidades técnicas exigidas y una alta heterogeneidad salarial. La información se encuentra fragmentada en múltiples portales de empleo con formatos no estructurados, descripciones cualitativas y rangos salariales dispares.

### 1.2 Objetivo General
Desarrollar un sistema integral y automatizado de **Web Scraping, Minería de Texto (NLP) y Persistencia Relacional** para consolidar ofertas laborales de múltiples portales, desagregar los requisitos técnicos y evaluar empíricamente el valor económico y la correlación de las habilidades frente a la remuneración salarial en el tiempo.

### 1.3 Objetivos Específicos
1. **Extracción y Estandarización Multi-Portal:** Construir scrapers modulares y consumidores de API que extraigan ofertas de empleo de portales nacionales e internacionales bajo un **Esquema Canónico Unificado**.
2. **Minería de Requisitos y Desagregación Atómica:** Procesar mediante expresiones regulares y taxonomías técnicas el texto de las ofertas para estructurar años de experiencia, educación, modalidad y habilidades técnicas individuales (*Tidy Data*).
3. **Modelado Econométrico, Persistencia y Visualización BI:** Calcular primas salariales, matrices de correlación de Pearson, segmentar mercados (Local COP vs. Remoto USD) y desplegar un Dashboard interactivo en Streamlit conectado a una base de datos relacional con series de tiempo.
4. **Automatización Serverless en la Nube:** Programar la extracción desatendida mensual mediante **GitHub Actions** persistiendo los snapshots en **PostgreSQL (Supabase/Neon)**.

---

## 2. Decisiones de Arquitectura y Diseño de Software

```mermaid
flowchart TD
    subgraph CRON["⏰ Disparador Automático (GitHub Actions CI/CD)"]
        GHA["Cron mensual ('0 0 1 * *')\no Disparo Manual (workflow_dispatch)"]
    end

    subgraph INGESTION["1. Ingestión Multi-Portal (6 Fuentes Activas)"]
        CT["CompuTrabajo (HTML)"]
        EE["ElEmpleo (HTML + GA4)"]
        GOB["Get on Board (REST API)"]
        TOR["Torre.ai (Semantic Search API)"]
        LI["LinkedIn Jobs (Guest Search API)"]
        TAL["Talent.com Colombia (HTML Parsing)"]
    end

    subgraph QUALITY["2. Puerta de Calidad y Filtro Temprano (Pre-Fetch)"]
        GATE["Validador Semántico de Pertinencia\n(Data Science / Analytics Gatekeeper)"]
    end

    subgraph PROCESSING["3. Procesamiento & NLP (src/processing)"]
        NLP["Minería de Requisitos & Taxonomías"]
        CLEAN["Normalización Multidivisa (COP / USD / EUR / GBP)"]
        SEG["Segmentador de Mercado (Local vs Remoto)"]
    end

    subgraph PERSISTENCE["4. Modelo Dimensional de Datos (Esquema Estrella)"]
        DB[("DatabaseManager (SQLAlchemy)\nSQLite Local / Cloud PostgreSQL")]
        D1[("dim_ofertas (Clave Inmutable SHA256)")]
        F1[("fact_extracciones_historico (Snapshots YYYYMM)")]
        F2[("fact_habilidades_historico (Series Temporales 1 a N)")]
        A1[("agg_metricas_mensuales (KPIs y Fluctuación MoM)")]
    end

    subgraph VISUALIZATION["5. Analítica & Dashboard (src/dashboard)"]
        DASH["Streamlit Dashboard (Plotly BI)\nConectado a Vistas Relacionales"]
    end

    CRON -->|Ejecuta runner en la nube| INGESTION
    INGESTION --> GATE
    GATE --> PROCESSING
    PROCESSING --> PERSISTENCE
    PERSISTENCE --> VISUALIZATION
```

### 2.1 Estructura Modular de Carpetas
Se estableció una estructura estándar de grado de producción:
- **`.github/workflows/`**: Flujo de trabajo de automatización mensual (`monthly_scraping.yml`).
- **`config/`**: Configuración centralizada (`settings.py`), constantes, rutas absolutas y cabeceras HTTP.
- **`data/`**:
  - `data/raw/`: Almacenamiento de extracciones crudas consolidadas (`.xlsx`, `.csv`).
  - `data/processed/`: Archivos transformados por el pipeline de NLP.
  - `data/analytics/`: Datasets dimensionales preparados para herramientas de BI.
  - `data/labor_market.db`: Base de datos SQLite local relacional con modelo dimensional.
- **`src/scrapers/`**: Implementaciones polimórficas basadas en `BaseScraper` (6 scrapers activos).
- **`src/processing/`**: Limpieza (`cleaner.py`), taxonomías (`taxonomies.py`) y minería de texto (`requirements_parser.py`).
- **`src/analytics/`**: Motor de correlación, primas salariales y preparación dimensional (`correlation_engine.py`).
- **`src/database/`**: Gestor de base de datos (`db_manager.py`) con soporte SQLAlchemy para SQLite y Cloud PostgreSQL.
- **`src/dashboard/`**: Aplicación web analítica interactiva (`app.py`) en Streamlit y Plotly.
- **`docs/`**: Documentación académica, bitácoras y especificaciones del proyecto.
- **`main.py`**: Orquestador por línea de comandos con soporte para banderas (`--scrape`, `--process`, `--analyze`, `--dashboard`, `--all`).

---

## 3. Registro Cronológico de Hitos y Decisiones Técnicas

| Hito | Problema / Reto Detectado | Decisión Técnica / Solución Implementada | Estado |
| :--- | :--- | :--- | :---: |
| **Hito 1: Scraper CompuTrabajo** | Bloqueo `HTTP 403 Forbidden` por User-Agent genérico. | Configuración de encabezados de navegador (`Accept`, `Referer`), manejo de códigos HTTP y pausas de cortesía. | ✅ Resuelto |
| **Hito 2: Desagregación NLP de Requisitos** | Requisitos en bloques de texto no estructurados. | Taxonomía Regex de tecnologías clave y generación de estructura *Tidy Data* con `.explode()`. | ✅ Resuelto |
| **Hito 3: Modelado Econométrico y Correlaciones** | Medición del retorno económico de habilidades. | Cálculo de primas salariales ($\Delta\%$, $\Delta\$$) frente al salario general y correlaciones de Pearson ($r$). | ✅ Resuelto |
| **Hito 4: Expansión ElEmpleo** | Necesidad de capturar metadatos analíticos enriquecidos. | Scraper extrayendo atributos JSON de Google Analytics 4 (`data-ga4-offerdata`) y normalización salarial en millones. | ✅ Resuelto |
| **Hito 5: Capa de Base de Datos Relacional** | Necesidad de desacoplar datos de archivos planos locales. | `DatabaseManager` con SQLAlchemy compatible con SQLite local y PostgreSQL en la nube vía `DATABASE_URL`. | ✅ Resuelto |
| **Hito 6: Puerta de Calidad y Filtro Temprano** | Presencia de vacantes no relacionadas (enfermería, ventas). | **Validador Semántico de Pertinencia** (`es_oferta_relevante`) y **Filtro Temprano Pre-Fetch** en tarjeta (-75% de latencia). | ✅ Resuelto |
| **Hito 7: Sanitización de Caracteres Ilegales XML** | `openpyxl` fallaba por caracteres ASCII no imprimibles (0-31). | `sanitizar_dataframe_para_excel()` con `ILLEGAL_CHARACTERS_RE` en todos los puntos de guardado. | ✅ Resuelto |
| **Hito 8: Integración de APIs (Get on Board y Torre.ai)** | Bloqueo WAF en Glassdoor; necesidad de fuentes tech directas. | Scrapers para APIs públicas de **Get on Board** y búsqueda semántica de **Torre.ai** (extracción en segundos). | ✅ Resuelto |
| **Hito 9: Segmentación Econométrica de Mercado** | Sesgo en la media por salarios en USD de hasta $68M COP. | Creación de `Tipo_Mercado` (`Local COP` vs `Internacional USD`), normalización multidivisa y uso de **Mediana Salarial**. | ✅ Resuelto |
| **Hito 10: Modelo Dimensional (Esquema Estrella)** | Necesidad de persistir snapshots históricos para series de tiempo. | Creación de `dim_ofertas` con hash SHA256 inmutable, `fact_extracciones_historico`, `fact_habilidades_historico` y `agg_metricas_mensuales`. | ✅ Resuelto |
| **Hito 11: Scrapers LinkedIn Jobs y Talent.com** | Requerimiento de maximizar cobertura del mercado colombiano. | Integración de **LinkedIn Jobs Guest API** y **Talent.com Colombia Scraper**, alcanzando **153 vacantes activas**. | ✅ Resuelto |
| **Hito 12: Automatización Serverless en la Nube** | Necesidad de ejecutar el pipeline de forma autónoma una vez al mes. | Creación del workflow de **GitHub Actions** (`.github/workflows/monthly_scraping.yml`) con cron mensual (`0 0 1 * *`), inyección de secretos (`DATABASE_URL`) y persistencia en la nube. | ✅ Resuelto |

---

## 4. Estado Actual de la Base de Datos (6 Portales Activos)

### 4.1 Resumen por Portal en la Base de Datos (`data/labor_market.db`)

| Portal | Tipo de Mercado | Vacantes Únicas | Con Salario Explícito | Salario Promedio ($ COP) | Salario Mínimo ($ COP) | Salario Máximo ($ COP) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Torre.ai** | Internacional (USD) | **40** | 26 | \$46.145.385 COP | \$13.000.000 | \$68.333.333 COP |
| **Talent.com** | Local / Remoto | **31** | -- | *A convenir* | -- | -- |
| **ElEmpleo** | Local (Colombia - COP) | **25** | 37 | \$4.385.135 COP | \$1.250.000 | \$7.000.000 COP |
| **Get on Board** | Tech LatAm / Remoto | **23** | 20 | \$15.780.000 COP | \$7.000.000 | \$20.000.000 COP |
| **LinkedIn** | Multinacional / Local | **20** | -- | *A convenir* | -- | -- |
| **CompuTrabajo** | Local (Colombia - COP) | **14** | 20 | \$4.760.290 COP | \$3.000.000 | \$12.000.000 COP |
| **Total Global** | **6 Fuentes** | **153** | **103** | **\$14.908.411 COP** | **\$1.250.000** | **\$68.333.333 COP** |

---

## 5. Guía de Conexión y Despliegue en la Nube

### 5.1 Base de Datos PostgreSQL en la Nube (Gratuita)
1. Crear una cuenta y proyecto en [Supabase](https://supabase.com) o [Neon.tech](https://neon.tech).
2. Obtener la cadena de conexión URI (ejemplo: `postgresql://postgres.xxx:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres`).
3. En GitHub, ir a **Settings > Secrets and variables > Actions** y crear el secreto `DATABASE_URL`.

### 5.2 Dashboard en Streamlit Community Cloud
1. Conectar el repositorio de GitHub en [share.streamlit.io](https://share.streamlit.io).
2. Configurar el archivo principal como `src/dashboard/app.py`.
3. En los *Secrets* de Streamlit, añadir `DATABASE_URL`.

---

## 6. Hito 13: Análisis Exploratorio de Datos (EDA) y Diagnóstico de Calidad

- **Archivo Generado:** [`notebooks/analisis_exploratorio_datos.ipynb`](file:///Users/juan/Documents/proyecto_investigativo/notebooks/analisis_exploratorio_datos.ipynb)
- **Estatus:** Ejecutado y validado de punta a punta.
- **Hallazgos Clave:**
  1. **Integridad y Claves Únicas:** 153 ofertas analizadas con 0% de duplicados gracias al hash SHA256.
  2. **Transparencia Salarial:** ElEmpleo (100%) y CompuTrabajo (85%) lideran la revelación salarial en Colombia, mientras LinkedIn y Talent.com concentran vacantes con remuneración a convenir.
  3. **Dispersión Bimodal:** Marcada polarización entre el mercado local (\$4.25M COP mediana) y el mercado remoto en USD (\$25.6M COP mediana).
  4. **Correlaciones y Retorno:** Tecnologías cloud e infraestructura (*Docker/Kubernetes, MLOps, AWS/GCP, Deep Learning*) muestran las correlaciones más altas ($r > 0.40$) y primas salariales superiores al $+100\%$.

---

## 7. Hito 14: Publicación en Repositorio GitHub y CI/CD Habilitado

- **Repositorio Oficial:** [`https://github.com/jfbernalp/proyecto_investigativo`](https://github.com/jfbernalp/proyecto_investigativo)
- **Rama Principal:** `main`
- **Seguridad:** Archivo `.gitignore` protegiendo variables locales (`.env`), entornos virtuales (`.venv`) y bases de datos locales.
- **Flujo de Automatización:** Workflow `.github/workflows/monthly_scraping.yml` sincronizado y listo para ejecución programada mensual.

---

## 8. Hito 15: Infraestructura Dedicada en Hetzner Cloud, Dominio `jfbernalp.dev` y Apache Superset

- **Fecha:** 15 de Septiembre de 2026
- **Servidor:** VPS Dedicado en Hetzner Cloud.
- **Dominio Asociado:** `jfbernalp.dev` (Base para el portafolio profesional e inteligencia de datos).
- **Entorno BI:** **Apache Superset** desplegado en contenedores Docker y conectado con éxito a **Supabase PostgreSQL**.
- **Objetivo Actual:** Construcción y estructuración de los datasets semánticos, métricas métricas calculadas y Dashboards interactivos de nivel corporativo en Apache Superset.

---

## 9. Hito 16: Configuración de Reverse Proxy Traefik, Certificados SSL y Soporte Handlebars en Superset

- **Fecha:** 15 de Septiembre de 2026
- **Dominio Superset:** `https://superset.jfbernalp.dev`
- **Componentes de Infraestructura:**
  1. **Traefik v3.1 / Latest:** Reverse Proxy con terminación SSL automática mediante Let's Encrypt (`acme.json`) y enrutamiento en red `superset-stack_web`.
  2. **ProxyFix Middleware:** Activación de `ENABLE_PROXY_FIX = True` y `FORWARDED_ALLOW_IPS = "*"` en `superset_config.py` para sincronizar cabeceras HTTPS (`X-Forwarded-Proto`, `X-Forwarded-Host`).
  3. **Content Security Policy (CSP):** Desactivación controlada de restricciones CSP (`TALISMAN_ENABLED = False`) y activación de `ENABLE_TEMPLATE_PROCESSING = True` para permitir la ejecución e inyección de plantillas personalizadas en plugins como **Handlebars** y componentes interactivos HTML/JS.

---

## 10. Hito 17: Implementación de Tarjetas KPI Visuales con Handlebars y HTML/CSS

- **Fecha:** 15 de Septiembre de 2026
- **Tecnología:** Plugin Handlebars de Apache Superset con renderizado HTML5 y CSS en línea.
- **Configuración de Seguridad:** Desactivación de `HTML_SANITIZATION = False` en `superset_config.py` para permitir diseño moderno con gradientes, sombras y tipografía avanzada.
- **Métricas Renderizadas:**
  1. **Muestra Activa:** Vacantes únicas consolidadas de 6 fuentes de empleo.
  2. **Mercado Local:** Mediana salarial en Colombia ($4.25M COP).
  3. **Mercado Remoto / Internacional:** Mediana internacional ($25.6M COP / ~$6.4K USD).
  4. **Tasa de Transparencia:** Porcentaje de vacantes con remuneración explícita (29.1%).

---

## 11. Hito 18: Construcción del Gráfico de Frecuencia de Habilidades (Top 15) en Superset

- **Fecha:** 15 de Septiembre de 2026
- **Gráfico:** `02 - Top 15 Habilidades Demandadas` (Apache ECharts Bar Chart Horizontal).
- **Dataset Relacional:** `fact_habilidades_historico` registrado en Superset.
- **Métrica de Negocio:** `COUNT(DISTINCT id_vacante_hash)` para asegurar deduplicación exacta de vacantes sobre la muestra activa.
- **Segmentación:** Desglose visual por `tipo_mercado` (Nacional vs. Internacional).

---

## 12. Hito 19: Construcción de la Matriz Dinámica de Co-ocurrencia Tecnológica (Heatmap)

- **Fecha:** 15 de Septiembre de 2026
- **Gráfico:** `03 - Matriz de Co-ocurrencia Tecnológica` (Apache ECharts Heatmap).
- **Dataset Semántico:** Vista `view_matriz_coocurrencia_bi` generada con CTE dinámico sobre `fact_habilidades_historico`.
- **Lógica de Agregación:** Auto-join relacional sobre el Top 15 de habilidades más demandadas sin hardcoding, deduplicando por `COUNT(DISTINCT id_vacante_hash)`.
- **Aporte Analítico:** Identificación de clusters de herramientas que se contratan juntas en el mercado laboral para el empaquetamiento de asignaturas en el diseño curricular de UniCafam.

---

## 13. Hito 20: Ensamblaje y Finalización de la Hoja 1 del Dashboard en Apache Superset

- **Fecha:** 15 de Septiembre de 2026
- **Dashboard:** `Observatorio Laboral de Ciencia de Datos - UniCafam` en `https://superset.jfbernalp.dev`.
- **Estructura Visual de la Hoja 1:**
  1. **Banner Institucional:** Encabezado con estado del pipeline en vivo, badges y alcance institucional UniCafam.
  2. **Tarjetas KPI Principales (Handlebars):** Muestra activa, mediana salarial local ($4.25M COP), mediana internacional ($25.6M COP) y tasa de transparencia (29.1%).
  3. **Top 15 Habilidades Demandadas:** Gráfico de barras horizontal con deduplicación exacta por vacante.
  4. **Distribución por Perfil / Rol:** Gráfico Donut con la proporción de demanda de perfiles.
  5. **Matriz de Co-ocurrencia Tecnológica:** Heatmap interactivo con clusters de herramientas exigidas conjuntamente.
  6. **Filtros Nativos (Cross-Filtering):** Segmentación transversal por Portal, Rol, Seniority y Modalidad.

---

## 14. Hito 21: Habilitación de Acceso Público y Visualización Móvil Responsiva

- **Fecha:** 15 de Septiembre de 2026
- **Configuración de Seguridad:** Sincronización del rol `Public` con permisos de lectura derivados de `Gamma` y `all_database_access` / `all_datasource_access` en la base interna de Superset.
- **Visualización Multi-Dispositivo:** Publicación del dashboard `Observatorio Laboral de Ciencia de Datos - UniCafam` con acceso anónimo directo en `https://superset.jfbernalp.dev`.
- **Experiencia de Usuario:** Rendimiento y responsividad móvil verificados en smartphones (cuadrículas adaptativas en tarjetas Handlebars, tooltips interactivos de ECharts y banners adaptables).

---

## 15. Hito 22: Filtros Nativos Transversales y Sincronización de Datasets para BI

- **Fecha:** 15 de Septiembre de 2026
- **Filtros Implementados:**
  1. **Portal de Empleo:** CompuTrabajo, ElEmpleo, LinkedIn, Talent.com, Torre, GetOnBoard.
  2. **Tipo de Mercado:** Mercado Nacional (COP) vs. Mercado Internacional / Remoto (USD).
- **Ingeniería de Datos:** Actualización de la vista `view_matriz_coocurrencia_bi` y adopción de `fact_habilidades_historico` para asegurar propagación homogénea de filtros en todos los gráficos (KPIs, Top Habilidades, Salarios y Heatmap) sin desacoples semánticos.

---

## 16. Hito 23: Ingesta Curricular de UniCafam y Persistencia Privada en Hetzner (Fase 2)

- **Fecha:** 16 de Septiembre de 2026
- **Fuente de Datos:** 32 microcurrículos oficiales en Excel de la *Tecnología en Análisis y Gestión de Datos*.
- **Módulos Desarrollados:**
  1. [`src/curriculum/curriculum_parser.py`](file:///Users/juan/Documents/proyecto_investigativo/src/curriculum/curriculum_parser.py): Extractor automatizado de códigos, créditos, horas TFD/TTI, competencias y saberes específicos.
  2. [`src/curriculum/curriculum_db_sync.py`](file:///Users/juan/Documents/proyecto_investigativo/src/curriculum/curriculum_db_sync.py): Generador de script SQL DDL/DML para PostgreSQL en Hetzner.
- **Esquema Relacional Académico:** Creación de `dim_malla_curricular` (32 asignaturas, 83 créditos), `fact_habilidades_academicas` (141 competencias tecnológicas mapeadas) y `fact_saberes_academicos`.
- **Gobernanza y Privacidad:** Almacenamiento 100% privado en el servidor Hetzner para proteger la confidencialidad de la información institucional.

---

## 17. Visión Estratégica: Observatorio Laboral y Diseño Curricular UniCafam

- **Institución Destino:** Fundación Universitaria Cafam (Universidad Cafam - UniCafam).
- **Alcance Final del Ecosistema:**
  1. **Capa BI:** Dashboard analítico en Apache Superset desplegado en Hetzner (`jfbernalp.dev`).
  2. **Capa IA (Próxima Fase):** Motor de Inteligencia Artificial para análisis semántico de vacantes, detección de brechas (*Curriculum Gap Analysis*) y generación automatizada de mallas curriculares y microcurrículos alineados con el MEN (Decreto 1330).








