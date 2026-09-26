# 📊 Guía de Configuración: Tablero Curricular MIG en Apache Superset

**Institución:** Fundación Universitaria Cafam (UniCafam)  
**Entorno de Producción:** Apache Superset (`https://jfbernalp.dev`)  
**Base de Datos:** PostgreSQL (Hetzner / Supabase)  

---

## 1. Arquitectura de Integración

```
  [ GitHub Actions Pipeline ] 
             │ (Inferencia IA + Exportación Excel MIG)
             ▼
  [ PostgreSQL Database ] ──► Vistas SQL Optimizadas (MIG)
             │
             ▼
  [ Apache Superset (jfbernalp.dev) ] ──► Tablero Ejecutivo de Inteligencia Curricular
```

---

## 2. Vistas SQL Disponibles en PostgreSQL para Superset

La base de datos expone automáticamente 3 vistas diseñadas para dashboards:

| Nombre de la Vista | Tipo de Contenido | Uso Recomendado en Superset |
|---|---|---|
| `view_superset_oferta_academica_mig` | Propuestas completas, horarios, tarifas x4, botones de descarga | Tabla interactiva, filtros por nivel y modalidad |
| `view_superset_malla_curricular_mig` | Detalle de módulos, créditos, horas TFD/TTI, RAEs y docentes | Gráficos de barras, tablas de asignaturas |
| `view_superset_kpis_curriculares_mig` | Índice de competitividad (0-100), total de propuestas y horas | Gráficos tipo Big Number / Gauge / Scorecard |

---

## 3. Paso a Paso para Conectar en Superset UI

### Paso 1: Registrar el Dataset
1. En el menú superior de Apache Superset, ve a **Data ➔ Datasets**.
2. Haz clic en el botón azul **`+ Dataset`**.
3. Selecciona:
   - **Database:** `PostgreSQL_Hetzner` (o tu conexión a PostgreSQL).
   - **Schema:** `public`.
   - **Table / View:** Selecciona `view_superset_oferta_academica_mig`.
4. Haz clic en **Add**.

---

### Paso 2: Crear los Gráficos (Slices)

#### 📈 Slice 1: Scorecard de Competitividad Curricular (Big Number)
- **Dataset:** `view_superset_kpis_curriculares_mig`.
- **Chart Type:** `Big Number with Trendline` o `Big Number`.
- **Metric:** `MAX(indice_competitividad_mercado)`.
- **Subheader:** `Índice de alineación de la Tecnología en Análisis de Datos vs Mercado Laboral`.

#### 📋 Slice 2: Tabla de Ofertas Académicas MIG con Descargas Activas
- **Dataset:** `view_superset_oferta_academica_mig`.
- **Chart Type:** `Table`.
- **Columns to Display:**
  - `id_propuesta`
  - `nombre_programa`
  - `tipo_propuesta`
  - `nivel_academico`
  - `duracion_estimada`
  - `creditos_totales`
  - `horas_totales`
  - `inversion_publico_externo`
  - `inversion_comunidad_unicafam`
  - `impacto_salarial_proyectado`
  - `boton_descarga_html`
- **Configuración Clave:** En la pestaña *Customize*, activa **`Allow HTML`** o **`Render HTML columns`** para que el botón `📥 Descargar MIG (.xlsx)` se renderice como un botón interactivo.

#### 🧱 Slice 3: Desglose de Módulos y Carga Horaria
- **Dataset:** `view_superset_malla_curricular_mig`.
- **Chart Type:** `Bar Chart (Stacked)` o `Pivot Table`.
- **Dimensiones:** `nombre_programa`, `nombre_modulo`.
- **Métricas:** `SUM(horas_tfd)` (Acompañamiento Docente), `SUM(horas_tti)` (Trabajo Independiente).

#### 📝 Slice 4: Tarjeta de Justificación y Diagnóstico FODA
- **Chart Type:** `Markdown`.
- **Contenido:** Inserta el resumen ejecutivo y los objetivos estratégicos para la toma de decisiones del Consejo Académico de UniCafam.

---

## 4. Alojamiento y Descarga de Archivos Excel (.xlsx)

Cuando el pipeline de GitHub Actions se ejecuta:
1. Genera los archivos Excel en `data/curriculo_unicafam/mig_propuestas/`.
2. El servidor web Nginx en Hetzner publica el directorio en `https://jfbernalp.dev/downloads/mig/`.
3. Al hacer clic en el botón dentro de Superset, el navegador descarga directamente el archivo oficial con la estructura de la **MATRIZ INTEGRADA DE GESTIÓN (MIG)**.
