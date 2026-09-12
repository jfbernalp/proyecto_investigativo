# Sistema de Inteligencia Laboral: Web Scraping, Minería de Datos y Análisis Salarial

Proyecto de investigación aplicada enfocado en el desarrollo de un motor integral de Web Scraping, Minería de Lenguaje Natural (NLP) y Análisis Estadístico-Econométrico para cuantificar la demanda de habilidades y su impacto salarial en los roles de **Científico de Datos** y **Analista de Datos**.

---

## 📁 Estructura del Proyecto

```
proyecto_investigativo/
│
├── docs/                                  # Documentación formal de la investigación
│   ├── propuesta_proyecto_academico.md    # Propuesta formal y cronograma de 6 meses
│   └── arquitectura_sistema.md            # Diagramas y diseño de componentes
│
├── data/                                  # Almacenamiento estratificado de datos
│   ├── raw/                               # Datos crudos extraídos de los portales
│   ├── processed/                         # Datos estructurados tras minería NLP
│   └── analytics/                         # Modelos multidimensionales para BI y Dashboards
│
├── config/                                # Parámetros globales y configuraciones
│   ├── __init__.py
│   └── settings.py                        # URLs, User-Agents, rutas y constantes
│
├── src/                                   # Código fuente modular
│   ├── scrapers/                          # Motores de extracción modular por portal
│   │   ├── base_scraper.py                # Clase base abstracta
│   │   └── computrabajo_scraper.py        # Scraper robusto con manejo de errores HTTP
│   │
│   ├── processing/                        # Limpieza y Procesamiento de Lenguaje Natural
│   │   ├── cleaner.py                     # Estandarización de salarios y categorías
│   │   ├── taxonomies.py                  # Taxonomía de habilidades y tecnologías
│   │   └── requirements_parser.py         # Parsing atómico y minería de texto
│   │
│   ├── analytics/                         # Modelado estadístico y econométrico
│   │   └── correlation_engine.py          # Matrices de correlación y primas salariales
│   │
│   └── dashboard/                         # Aplicación Web Interactiva
│       └── app.py                         # Dashboard interactivo con Streamlit y Plotly
│
├── main.py                                # Orquestador y CLI para ejecución de punta a punta
├── requirements.txt                       # Lista de dependencias del entorno
└── README.md                              # Guía general de uso
```

---

## 🚀 Guía de Instalación y Uso

### 1. Activar el Entorno Virtual
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ejecutar el Pipeline por Módulos

El orquestador [main.py](main.py) permite ejecutar cada fase de forma independiente o completa:

* **Paso 1: Extracción Web (Scraping):**
  ```bash
  python main.py --scrape --role "cientifico-de-datos" --pages 5
  ```

* **Paso 2: Minería NLP y Desagregación de Habilidades:**
  ```bash
  python main.py --process
  ```

* **Paso 3: Análisis Estadístico y Modelado de Primas:**
  ```bash
  python main.py --analyze
  ```

* **Paso 4: Lanzar el Dashboard Web Interactivo:**
  ```bash
  python main.py --dashboard
  ```
  *(O directamente con `streamlit run src/dashboard/app.py`)*

* **Ejecutar todo de punta a punta:**
  ```bash
  python main.py --all
  ```

---

## 📊 Principales Hallazgos Empíricos

1. **Estratificación Salarial Tecnológica:** Las habilidades de Big Data distribuido (`Spark / Databricks`), Deep Learning (`PyTorch`) y Cloud (`GCP / AWS`) presentan **primas salariales superiores al +80%** respecto al promedio del mercado.
2. **Impacto de la Experiencia:** Fuerte correlación positiva ($r = +0.465$) entre años de experiencia requeridos y el salario ofrecido.
3. **Core del Científico de Datos:** `Python` ($r = +0.388$), `SQL` ($r = +0.343$) y `Machine Learning` ($r = +0.315$) son los tres pilares de mayor retorno económico.
