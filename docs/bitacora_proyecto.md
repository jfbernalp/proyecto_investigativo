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
