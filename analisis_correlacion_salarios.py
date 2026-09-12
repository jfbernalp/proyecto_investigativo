import os
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".matplotlib_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Backend no interactivo sin ventanas
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from procesar_requisitos import TAXONOMIA_HABILIDADES

# Configuración visual de gráficos
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10

def limpiar_salario_numerico(val):
    """
    Convierte cadenas como '$ 7.000.000,00 (Mensual)' a valores flotantes (7000000.0).
    Retorna np.nan para salarios 'A convenir' o no especificados.
    """
    if not isinstance(val, str) or any(x in val.lower() for x in ["a convenir", "no especificado", "confidencial"]):
        return np.nan
    num_str = re.sub(r"[^\d,]", "", val)
    if not num_str:
        return np.nan
    if "," in num_str:
        num_str = num_str.split(",")[0]
    num_str = num_str.replace(".", "")
    try:
        return float(num_str)
    except:
        return np.nan

def categorizar_seniority(anios):
    """
    Agrupa los años de experiencia en niveles estándar de la industria.
    """
    if pd.isna(anios):
        return "No especificado"
    elif anios <= 1:
        return "Junior / Trainee (0-1 años)"
    elif 2 <= anios <= 3:
        return "Semi-Senior (2-3 años)"
    elif 4 <= anios <= 5:
        return "Senior (4-5 años)"
    else:
        return "Lead / Principal (> 5 años)"


def preparar_datasets_analiticos(ruta_origen="ofertas_analizadas.xlsx"):
    print("=" * 70)
    print("1. CARGANDO Y PREPARANDO VARIABLES (FEATURE ENGINEERING)")
    print("=" * 70)

    # Cargamos la hoja estructurada
    df = pd.read_excel(ruta_origen, sheet_name="Ofertas_Estructuradas")
    
    # 1. Limpieza de Salario
    df["Salario_COP"] = df["Salario"].apply(limpiar_salario_numerico)
    df["Salario_Millones"] = df["Salario_COP"] / 1_000_000.0

    # 2. Categorización de Seniority
    df["Seniority"] = df["Anios_Experiencia"].apply(categorizar_seniority)

    # 3. Mapeo Ordinal de Nivel Educativo
    educacion_map = {
        "Bachillerato / Educación Media": 1,
        "Educación Básica Secundaria": 1,
        "Universidad / Carrera técnica": 2,
        "Universidad / Carrera Tecnológica": 2,
        "Universidad / Carrera Profesional": 3,
        "Postgrado / Especialización": 4,
        "Maestría": 5,
        "Doctorado": 6
    }
    df["Nivel_Educativo_Ordinal"] = df["Nivel_Educacion"].map(educacion_map).fillna(2.5)

    # 4. One-Hot Encoding de Habilidades Técnicas (Variables Binarias 1 / 0)
    for skill in TAXONOMIA_HABILIDADES.keys():
        col_name = f"Skill_{skill}"
        df[col_name] = df["Habilidades_Tecnicas"].apply(
            lambda x: 1 if isinstance(x, str) and skill in x else 0
        )

    print(f"Total registros procesados: {len(df)}")
    print(f"Registros con Salario Numérico explícito: {df['Salario_COP'].notna().sum()}")
    print(f"Registros con Años de Experiencia explícitos: {df['Anios_Experiencia'].notna().sum()}")

    return df


def analizar_correlaciones_y_valor(df):
    print("\n" + "=" * 70)
    print("2. ANÁLISIS DE CORRELACIÓN Y PRIMA SALARIAL POR HABILIDAD")
    print("=" * 70)

    # Subconjunto con salarios válidos para el análisis cuantitativo
    df_sal = df.dropna(subset=["Salario_COP"]).copy()

    # Identificamos las columnas de habilidades presentes en los datos
    skill_cols = [f"Skill_{s}" for s in TAXONOMIA_HABILIDADES.keys() if df_sal[f"Skill_{s}"].sum() > 0]
    
    # --------------------------------------------------------------------------
    # Matriz de Correlación
    # --------------------------------------------------------------------------
    cols_analisis = ["Salario_Millones", "Anios_Experiencia", "Nivel_Educativo_Ordinal"] + skill_cols
    matriz_corr = df_sal[cols_analisis].corr()

    # Correlación directa de cada variable con el Salario
    corr_con_salario = matriz_corr["Salario_Millones"].drop("Salario_Millones").sort_values(ascending=False)

    # --------------------------------------------------------------------------
    # Cálculo de Valor Económico y Prima Salarial (Premium %) por Habilidad
    # --------------------------------------------------------------------------
    salario_promedio_general = df_sal["Salario_COP"].mean()
    salario_mediano_general = df_sal["Salario_COP"].median()

    resumen_valor = []
    for skill in TAXONOMIA_HABILIDADES.keys():
        col = f"Skill_{skill}"
        con_skill = df_sal[df_sal[col] == 1]
        sin_skill = df_sal[df_sal[col] == 0]
        
        n_con = len(con_skill)
        if n_con >= 1:
            prom_con = con_skill["Salario_COP"].mean()
            med_con = con_skill["Salario_COP"].median()
            prom_sin = sin_skill["Salario_COP"].mean() if len(sin_skill) > 0 else salario_promedio_general
            
            prima_cop = prom_con - prom_sin
            prima_pct = ((prom_con - prom_sin) / prom_sin) * 100 if prom_sin > 0 else 0
            
            # Coeficiente de correlación punto-biserial
            coef_corr = matriz_corr.loc["Salario_Millones", col] if col in matriz_corr.columns else 0
            
            # Prueba estadística de diferencia de medias (si hay suficientes muestras)
            p_val = np.nan
            if n_con >= 2 and len(sin_skill) >= 2:
                try:
                    _, p_val = stats.ttest_ind(con_skill["Salario_COP"], sin_skill["Salario_COP"], equal_var=False)
                except:
                    p_val = np.nan

            resumen_valor.append({
                "Habilidad": skill,
                "Ofertas_Con_Salario": n_con,
                "Salario_Promedio_COP": round(prom_con, 2),
                "Salario_Mediano_COP": round(med_con, 2),
                "Salario_Sin_Skill_COP": round(prom_sin, 2),
                "Prima_Salarial_COP": round(prima_cop, 2),
                "Prima_Salarial_%": round(prima_pct, 2),
                "Correlacion_Con_Salario": round(coef_corr, 4),
                "P_Valor_Significancia": round(p_val, 4) if pd.notna(p_val) else "N/A"
            })

    df_valor = pd.DataFrame(resumen_valor).sort_values("Salario_Promedio_COP", ascending=False)

    print("\n---> TOP 10 HABILIDADES MEJOR PAGADAS EN EL MERCADO:")
    print(df_valor[["Habilidad", "Ofertas_Con_Salario", "Salario_Promedio_COP", "Prima_Salarial_%", "Correlacion_Con_Salario"]].head(10).to_string(index=False))

    return matriz_corr, df_valor, df_sal


def generar_visualizaciones(matriz_corr, df_valor, df_sal):
    print("\n" + "=" * 70)
    print("3. GENERANDO MAPAS DE CALOR Y GRÁFICOS ANALÍTICOS")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # GRÁFICO 1: Mapa de Calor (Heatmap) de Correlaciones
    # --------------------------------------------------------------------------
    # Seleccionamos las top 12 variables más correlacionadas con el salario
    top_vars = matriz_corr["Salario_Millones"].abs().sort_values(ascending=False).head(12).index.tolist()
    sub_matriz = matriz_corr.loc[top_vars, top_vars]
    
    # Nombres limpios para visualización
    nombres_limpios = [v.replace("Skill_", "").replace("Salario_Millones", "Salario ($COP)").replace("Nivel_Educativo_Ordinal", "Nivel Educativo") for v in top_vars]

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        sub_matriz, 
        annot=True, 
        fmt=".2f", 
        cmap="coolwarm", 
        vmin=-0.5, 
        vmax=1.0, 
        xticklabels=nombres_limpios, 
        yticklabels=nombres_limpios,
        cbar_kws={"label": "Coeficiente de Correlación de Pearson"}
    )
    plt.title("Mapa de Calor: Correlación entre Salario, Experiencia y Habilidades Clave", fontsize=13, weight="bold", pad=15)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("mapa_calor_correlacion.png", dpi=300)
    plt.close()
    print("[OK] Gráfico generado: mapa_calor_correlacion.png")

    # --------------------------------------------------------------------------
    # GRÁFICO 2: Ranking de Valor Económico por Habilidad (Barras Horizontales)
    # --------------------------------------------------------------------------
    plt.figure(figsize=(11, 7))
    df_top_skills = df_valor.head(15).sort_values("Salario_Promedio_COP", ascending=True)

    colores = ["#2b5c8f" if p > 30 else "#5c82a6" if p > 0 else "#d9534f" for p in df_top_skills["Prima_Salarial_%"]]

    bars = plt.barh(df_top_skills["Habilidad"], df_top_skills["Salario_Promedio_COP"] / 1_000_000, color=colores, edgecolor="black", alpha=0.85)
    
    # Línea de referencia del salario promedio general
    prom_gen = df_sal["Salario_COP"].mean() / 1_000_000
    plt.axvline(prom_gen, color="red", linestyle="--", linewidth=1.5, label=f"Salario Promedio General: ${prom_gen:.2f}M COP")

    for bar, pct in zip(bars, df_top_skills["Prima_Salarial_%"]):
        plt.text(
            bar.get_width() + 0.1, 
            bar.get_y() + bar.get_height()/2, 
            f"${bar.get_width():.2f}M ({'+' if pct>0 else ''}{pct:.1f}%)", 
            va="center", 
            fontsize=9, 
            weight="bold"
        )

    plt.xlabel("Salario Promedio Ofrecido (Millones de COP)", fontsize=11, weight="bold")
    plt.ylabel("Habilidad Requerida", fontsize=11, weight="bold")
    plt.title("Impacto Económico de las Habilidades en el Salario (Ciencia de Datos)", fontsize=13, weight="bold", pad=15)
    plt.xlim(0, max(df_top_skills["Salario_Promedio_COP"] / 1_000_000) * 1.25)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("valor_salarial_habilidades.png", dpi=300)
    plt.close()
    print("[OK] Gráfico generado: valor_salarial_habilidades.png")

    # --------------------------------------------------------------------------
    # GRÁFICO 3: Salario vs Años de Experiencia (Dispersión y Boxplot)
    # --------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Scatter con regresión
    sns.regplot(
        data=df_sal, 
        x="Anios_Experiencia", 
        y="Salario_Millones", 
        ax=ax1, 
        color="#1f77b4",
        scatter_kws={"alpha": 0.7, "s": 50},
        line_kws={"color": "#d62728", "linewidth": 2}
    )
    ax1.set_title("Relación Salario vs Años de Experiencia", fontsize=12, weight="bold")
    ax1.set_xlabel("Años de Experiencia", fontsize=10, weight="bold")
    ax1.set_ylabel("Salario (Millones COP)", fontsize=10, weight="bold")

    # Boxplot por Seniority
    orden_seniority = ["Junior / Trainee (0-1 años)", "Semi-Senior (2-3 años)", "Senior (4-5 años)", "Lead / Principal (> 5 años)"]
    orden_existente = [s for s in orden_seniority if s in df_sal["Seniority"].unique()]
    
    sns.boxplot(
        data=df_sal, 
        x="Seniority", 
        y="Salario_Millones", 
        order=orden_existente, 
        ax=ax2, 
        palette="Set2"
    )
    ax2.set_title("Distribución Salarial por Nivel de Seniority", fontsize=12, weight="bold")
    ax2.set_xlabel("Seniority", fontsize=10, weight="bold")
    ax2.set_ylabel("Salario (Millones COP)", fontsize=10, weight="bold")
    ax2.tick_params(axis="x", rotation=25)

    plt.tight_layout()
    plt.savefig("salario_vs_experiencia.png", dpi=300)
    plt.close()
    print("[OK] Gráfico generado: salario_vs_experiencia.png")


def exportar_para_dashboards(df, df_valor, matriz_corr, ruta_excel="dataset_dashboard_salarios.xlsx"):
    print("\n" + "=" * 70)
    print("4. EXPORTANDO ESTRUCTURA MODELADA PARA DASHBOARDS (POWER BI / TABLEAU)")
    print("=" * 70)

    # 1. Dataset en Formato Largo Enriquecido (1 fila por habilidad con Salario y Experiencia)
    # Esto permite en Power BI / Tableau hacer slicers de 'Habilidad' que recalculen el salario promedio
    df_largo = df.explode("Habilidades_Tecnicas").dropna(subset=["Habilidades_Tecnicas"])
    df_largo = df_largo.rename(columns={"Habilidades_Tecnicas": "Habilidad"})
    
    cols_largo = [
        "Codigo", "Nombre Oferta", "Empresa", "Ubicacion", "Modalidad", "Seniority",
        "Nivel_Educacion", "Anios_Experiencia", "Salario_COP", "Salario_Millones", "Habilidad", "URL"
    ]
    df_largo_dashboard = df_largo[cols_largo].copy()

    # 2. Guardamos tanto en Excel con múltiples hojas como en CSVs limpios
    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Matriz_Ofertas_Modelado", index=False)
        df_largo_dashboard.to_excel(writer, sheet_name="Habilidades_Largo_BI", index=False)
        df_valor.to_excel(writer, sheet_name="Valor_Economico_Habilidades", index=False)
        matriz_corr.to_excel(writer, sheet_name="Matriz_Correlacion")

    # CSV para importación directa rápida en BI tools
    df.to_csv("matriz_ofertas_dashboard.csv", index=False, encoding="utf-8-sig")
    df_largo_dashboard.to_csv("habilidades_largo_dashboard.csv", index=False, encoding="utf-8-sig")

    print(f"[EXITO] Libro Excel analítico creado: {ruta_excel}")
    print(f"[EXITO] Archivos CSV creados: matriz_ofertas_dashboard.csv y habilidades_largo_dashboard.csv")


def main():
    df = preparar_datasets_analiticos()
    matriz_corr, df_valor, df_sal = analizar_correlaciones_y_valor(df)
    generar_visualizaciones(matriz_corr, df_valor, df_sal)
    exportar_para_dashboards(df, df_valor, matriz_corr)
    print("\n" + "=" * 70)
    print("PROCESO DE PREPARACIÓN Y ANÁLISIS DE CORRELACIÓN FINALIZADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
