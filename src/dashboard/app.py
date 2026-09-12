import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Agregar la raíz del proyecto al sys.path para importar módulos internos
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.settings import ANALYTICS_DASHBOARD_FILE, HABILIDADES_LARGO_CSV, MATRIZ_OFERTAS_CSV

# Configuración de página
st.set_page_config(
    page_title="Labor Intelligence Dashboard | Data Science & Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    try:
        excel_path = ANALYTICS_DASHBOARD_FILE
        if not excel_path.exists():
            # Fallback a archivos locales si no están en data/analytics
            excel_path = ROOT_DIR / "dataset_dashboard_salarios.xlsx"

        df_ofertas = pd.read_excel(excel_path, sheet_name="Matriz_Ofertas_Modelado")
        df_largo = pd.read_excel(excel_path, sheet_name="Habilidades_Largo_BI")
        df_valor = pd.read_excel(excel_path, sheet_name="Valor_Economico_Habilidades")
        matriz_corr = pd.read_excel(excel_path, sheet_name="Matriz_Correlacion", index_col=0)
        return df_ofertas, df_largo, df_valor, matriz_corr
    except Exception as e:
        st.error(f"Error cargando datasets: {e}")
        return None, None, None, None

df_ofertas, df_largo, df_valor, matriz_corr = cargar_datos()

if df_ofertas is None:
    st.warning("No se encontraron los datasets procesados. Ejecuta 'python main.py --all' para generarlos.")
    st.stop()

# ==============================================================================
# SIDEBAR / FILTROS
# ==============================================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=60)
st.sidebar.title("Filtros Analíticos")

# Filtro por Segmento de Mercado (Local vs Internacional)
if "Tipo_Mercado" in df_ofertas.columns:
    mercados_disp = ["Todos los Mercados"] + sorted(df_ofertas["Tipo_Mercado"].dropna().unique().tolist())
    filtro_mercado = st.sidebar.selectbox("Segmento de Mercado:", mercados_disp)
else:
    filtro_mercado = "Todos los Mercados"

# Filtro por Portal
if "Portal" in df_ofertas.columns:
    portales_disp = ["Todos"] + sorted(df_ofertas["Portal"].dropna().unique().tolist())
    filtro_portal = st.sidebar.selectbox("Portal de Empleo:", portales_disp)
else:
    filtro_portal = "Todos"

# Filtro por Modalidad
modalidades_disp = ["Todas"] + sorted(df_ofertas["Modalidad"].dropna().unique().tolist())
filtro_modalidad = st.sidebar.selectbox("Modalidad de Trabajo:", modalidades_disp)

# Filtro por Seniority
seniority_disp = ["Todos"] + sorted(df_ofertas["Seniority"].dropna().unique().tolist())
filtro_seniority = st.sidebar.selectbox("Nivel de Seniority:", seniority_disp)

# Filtro por Habilidad
habilidades_disp = ["Todas"] + sorted(df_valor["Habilidad"].unique().tolist())
filtro_skill = st.sidebar.selectbox("Filtrar por Habilidad Técnica:", habilidades_disp)

# Filtro de Rango Salarial
salarios_validos = df_ofertas["Salario_Millones"].dropna()
min_sal = float(salarios_validos.min()) if len(salarios_validos) > 0 else 1.0
max_sal = float(salarios_validos.max()) if len(salarios_validos) > 0 else 70.0

rango_salario = st.sidebar.slider(
    "Rango Salarial (Millones COP):",
    min_value=round(min_sal, 1),
    max_value=round(max_sal, 1),
    value=(round(min_sal, 1), round(max_sal, 1)),
    step=0.5
)

# Aplicar filtros
df_filtrado = df_ofertas.copy()

if filtro_mercado != "Todos los Mercados" and "Tipo_Mercado" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Tipo_Mercado"] == filtro_mercado]

if filtro_portal != "Todos" and "Portal" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Portal"] == filtro_portal]

if filtro_modalidad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Modalidad"] == filtro_modalidad]

if filtro_seniority != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Seniority"] == filtro_seniority]

if filtro_skill != "Todas":
    col_skill = f"Skill_{filtro_skill}"
    if col_skill in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_skill] == 1]

# Filtro salarial (solo para ofertas que tienen salario)
df_filtrado_sal = df_filtrado.dropna(subset=["Salario_Millones"])
df_filtrado_sal = df_filtrado_sal[
    (df_filtrado_sal["Salario_Millones"] >= rango_salario[0]) & 
    (df_filtrado_sal["Salario_Millones"] <= rango_salario[1])
]

# ==============================================================================
# ENCABEZADO Y KPIS PRINCIPALES
# ==============================================================================
st.markdown('<div class="main-title">Labor Market Intelligence: Data Science & Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Plataforma de Investigación sobre Demanda de Habilidades, Brechas y Valoración Salarial (Local vs Remoto)</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Ofertas", f"{len(df_filtrado):,}")

with col2:
    n_sal = len(df_filtrado_sal)
    pct_sal = (n_sal / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.metric("Con Salario Explícito", f"{n_sal:,} ({pct_sal:.0f}%)")

with col3:
    sal_med = df_filtrado_sal["Salario_Millones"].median() if len(df_filtrado_sal) > 0 else 0
    st.metric("Mediana Salarial (Robusta)", f"${sal_med:.2f}M COP" if sal_med > 0 else "N/A")

with col4:
    sal_prom = df_filtrado_sal["Salario_Millones"].mean() if len(df_filtrado_sal) > 0 else 0
    st.metric("Salario Promedio", f"${sal_prom:.2f}M COP" if sal_prom > 0 else "N/A")

with col5:
    exp_prom = df_filtrado["Anios_Experiencia"].dropna().mean() if len(df_filtrado) > 0 else 0
    st.metric("Experiencia Promedio", f"{exp_prom:.1f} Años" if exp_prom > 0 else "N/A")

st.markdown("---")

# ==============================================================================
# PESTAÑAS PRINCIPALES DEL DASHBOARD
# ==============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Demanda de Habilidades",
    "💰 Valoración Salarial & Primas",
    "🔥 Mapas de Calor & Correlación",
    "🔍 Explorador de Vacantes",
    "📄 Ficha del Proyecto"
])

# ------------------------------------------------------------------------------
# TAB 1: DEMANDA DE HABILIDADES
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Frecuencia y Demanda Relativa de Habilidades Técnicas")
    
    col_t1_a, col_t1_b = st.columns([3, 2])

    with col_t1_a:
        # Ranking de habilidades
        df_ranking = df_valor.sort_values("Ofertas_Con_Salario", ascending=True)
        
        fig_demanda = px.bar(
            df_valor.sort_values("Ofertas_Con_Salario", ascending=True).tail(15),
            x="Ofertas_Con_Salario",
            y="Habilidad",
            orientation="h",
            text="Ofertas_Con_Salario",
            title="Top Habilidades más Frecuentes en el Mercado",
            color="Ofertas_Con_Salario",
            color_continuous_scale="Blues"
        )
        fig_demanda.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_demanda, use_container_width=True)

    with col_t1_b:
        st.markdown("#### Distribución de la Muestra")
        fig_pie = px.pie(
            df_filtrado,
            names="Seniority",
            title="Distribución de Ofertas por Nivel de Seniority",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(height=500)
        st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: VALORACIÓN SALARIAL & PRIMAS
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("¿Cuáles son las Habilidades Técnicas con Mayor Retorno Económico?")
    
    df_valor_plot = df_valor.sort_values("Salario_Promedio_COP", ascending=True)
    df_valor_plot["Salario_Promedio_M"] = df_valor_plot["Salario_Promedio_COP"] / 1_000_000.0
    df_valor_plot["Color_Prima"] = df_valor_plot["Prima_Salarial_%"].apply(
        lambda x: "Alta Prima (>30%)" if x > 30 else "Prima Moderada (0-30%)" if x > 0 else "Por debajo de la media"
    )

    fig_salarios = px.bar(
        df_valor_plot,
        x="Salario_Promedio_M",
        y="Habilidad",
        orientation="h",
        color="Color_Prima",
        color_discrete_map={
            "Alta Prima (>30%)": "#1E3A8A",
            "Prima Moderada (0-30%)": "#3B82F6",
            "Por debajo de la media": "#EF4444"
        },
        text=df_valor_plot["Salario_Promedio_M"].apply(lambda x: f"${x:.2f}M"),
        title="Salario Promedio Ofrecido por Requisito Tecnológico",
        labels={"Salario_Promedio_M": "Salario Promedio (Millones COP)", "Habilidad": "Tecnología"}
    )
    
    prom_general_val = df_ofertas["Salario_Millones"].mean()
    fig_salarios.add_vline(
        x=prom_general_val, 
        line_dash="dash", 
        line_color="red", 
        annotation_text=f"Promedio Mercado: ${prom_general_val:.2f}M", 
        annotation_position="bottom right"
    )
    fig_salarios.update_layout(height=600)
    st.plotly_chart(fig_salarios, use_container_width=True)

    st.markdown("#### Comparativa Salarial: Mercado Local vs. Remoto Internacional")
    if "Tipo_Mercado" in df_ofertas.columns and len(df_ofertas.dropna(subset=["Salario_Millones"])) > 0:
        fig_box = px.box(
            df_ofertas.dropna(subset=["Salario_Millones"]),
            x="Portal",
            y="Salario_Millones",
            color="Tipo_Mercado",
            points="all",
            title="Distribución y Dispersión Salarial por Portal y Tipo de Mercado",
            labels={"Salario_Millones": "Salario Mensual (Millones COP)", "Portal": "Portal de Empleo"},
            color_discrete_map={
                "Mercado Local (Colombia - COP)": "#3B82F6",
                "Mercado Internacional (Remoto - USD)": "#10B981"
            }
        )
        fig_box.update_layout(height=450)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("#### Tabla Resumen de Primas Salariales y Correlación")
    st.dataframe(
        df_valor[[
            "Habilidad", "Ofertas_Con_Salario", "Salario_Promedio_COP", 
            "Salario_Mediano_COP", "Prima_Salarial_%", "Correlacion_Con_Salario"
        ]].style.format({
            "Salario_Promedio_COP": "${:,.0f}",
            "Salario_Mediano_COP": "${:,.0f}",
            "Prima_Salarial_%": "{:+.1f}%",
            "Correlacion_Con_Salario": "{:.4f}"
        }),
        use_container_width=True
    )

# ------------------------------------------------------------------------------
# TAB 3: MAPAS DE CALOR & CORRELACIÓN
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Matrices de Correlación y Relación Experiencia vs Salario")

    col_t3_a, col_t3_b = st.columns([1, 1])

    with col_t3_a:
        # Mapa de Calor interactivo
        top_corr_vars = matriz_corr["Salario_Millones"].abs().sort_values(ascending=False).head(10).index.tolist()
        sub_corr = matriz_corr.loc[top_corr_vars, top_corr_vars]
        nombres_limpios = [v.replace("Skill_", "").replace("Salario_Millones", "Salario").replace("Nivel_Educativo_Ordinal", "Educación") for v in top_corr_vars]

        fig_heat = px.imshow(
            sub_corr,
            x=nombres_limpios,
            y=nombres_limpios,
            color_continuous_scale="RdBu_r",
            zmin=-0.5,
            zmax=1.0,
            text_auto=".2f",
            title="Mapa de Calor: Correlaciones con el Salario"
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_t3_b:
        # Scatter Plot Salario vs Experiencia
        fig_scatter = px.scatter(
            df_filtrado_sal,
            x="Anios_Experiencia",
            y="Salario_Millones",
            color="Seniority",
            hover_data=["Nombre Oferta", "Empresa", "Ubicacion"],
            trendline="ols",
            title="Salario vs Años de Experiencia (Regresión Lineal)",
            labels={"Anios_Experiencia": "Años de Experiencia Requeridos", "Salario_Millones": "Salario (Millones COP)"}
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 4: EXPLORADOR DE VACANTES
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("Directorio Filtrable de Ofertas Extraídas")
    
    cols_mostrar = [
        "Nombre Oferta", "Empresa", "Ubicacion", "Modalidad", "Salario", 
        "Anios_Experiencia", "Nivel_Educacion", "Habilidades_Tecnicas", "URL"
    ]
    
    st.dataframe(
        df_filtrado[cols_mostrar],
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("Enlace de Oferta")
        }
    )

    # Botones de descarga
    csv_data = df_filtrado.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv_data,
        file_name="ofertas_data_science_filtradas.csv",
        mime="text/csv"
    )

# ------------------------------------------------------------------------------
# TAB 5: FICHA DEL PROYECTO
# ------------------------------------------------------------------------------
with tab5:
    st.subheader("Sobre el Proyecto de Investigación")
    st.markdown("""
    **Título:** *Desarrollo de un Sistema Automatizado de Web Scraping y Minería de Datos para el Análisis de Brechas de Habilidades, Demanda Laboral y Valoración Salarial en los Roles de Científico y Analista de Datos.*
    
    **Duración:** 6 Meses (24 Semanas)
    
    **Objetivo General:**  
    Desarrollar un sistema integral y automatizado de web scraping, minería de texto y análisis econométrico-estadístico sobre los principales portales de empleo, con el fin de cuantificar la demanda de habilidades técnicas y su impacto en la compensación salarial para los perfiles de Científico de Datos y Analista de Datos.
    
    **Estructura del Repositorio:**
    - `docs/`: Documentación formal, propuesta académica y manuales de arquitectura.
    - `data/`: Almacenamiento estratificado (`raw/`, `processed/`, `analytics/`).
    - `src/scrapers/`: Motores de extracción modular por portal web.
    - `src/processing/`: Algoritmos de NLP, parsing de requisitos y taxonomías.
    - `src/analytics/`: Modelado estadístico, cálculo de primas salariales y correlaciones.
    - `src/dashboard/`: Aplicación interactiva de visualización.
    """)
