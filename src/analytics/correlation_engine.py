import os
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any

from src.processing.taxonomies import TAXONOMIA_HABILIDADES
from src.processing.cleaner import limpiar_salario_numerico, categorizar_seniority, mapear_educacion_ordinal

def ejecutar_analisis_correlacion_y_modelado(
    input_file: Path,
    output_excel: Path,
    output_matriz_csv: Path,
    output_largo_csv: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Realiza la ingeniería de características, análisis de correlación, primas salariales
    y exportación de datasets optimizados para Dashboards.
    """
    print("=" * 70)
    print("EJECUTANDO ANÁLISIS DE CORRELACIÓN, VALORACIÓN SALARIAL Y PREPARACIÓN DE BI")
    print("=" * 70)

    # 1. Carga de datos
    df = pd.read_excel(input_file, sheet_name="Ofertas_Estructuradas")

    # 2. Feature Engineering
    from src.processing.cleaner import detectar_moneda_y_mercado
    mercado_info = df.apply(lambda r: detectar_moneda_y_mercado(r.get("Portal"), r.get("Salario")), axis=1)
    df["Moneda_Original"] = [m[0] for m in mercado_info]
    df["Tipo_Mercado"] = [m[1] for m in mercado_info]

    df["Salario_COP"] = df["Salario"].apply(limpiar_salario_numerico)
    df["Salario_Millones"] = df["Salario_COP"] / 1_000_000.0
    df["Seniority"] = df["Anios_Experiencia"].apply(categorizar_seniority)
    df["Nivel_Educativo_Ordinal"] = df["Nivel_Educacion"].apply(mapear_educacion_ordinal)

    # One-Hot Encoding de habilidades
    for skill in TAXONOMIA_HABILIDADES.keys():
        df[f"Skill_{skill}"] = df["Habilidades_Tecnicas"].apply(
            lambda x: 1 if isinstance(x, str) and skill in x else 0
        )

    # 3. Subconjunto para análisis cuantitativo
    df_sal = df.dropna(subset=["Salario_COP"]).copy()
    skill_cols = [f"Skill_{s}" for s in TAXONOMIA_HABILIDADES.keys() if df_sal[f"Skill_{s}"].sum() > 0]
    
    cols_analisis = ["Salario_Millones", "Anios_Experiencia", "Nivel_Educativo_Ordinal"] + skill_cols
    matriz_corr = df_sal[cols_analisis].corr()

    # 4. Primas salariales y valoración económica por habilidad
    salario_promedio_general = df_sal["Salario_COP"].mean()
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
            coef_corr = matriz_corr.loc["Salario_Millones", col] if col in matriz_corr.columns else 0
            
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

    # 5. Formato largo enriquecido para BI (Tidy Data atómico: 1 fila por habilidad)
    df_temp = df.copy()
    df_temp["_skills_list"] = df_temp["Habilidades_Tecnicas"].apply(
        lambda x: [s.strip() for s in str(x).split(",") if s.strip()] if pd.notna(x) and str(x).strip() != "" and str(x) != "nan" else []
    )
    df_largo = df_temp.explode("_skills_list").dropna(subset=["_skills_list"])
    df_largo = df_largo[df_largo["_skills_list"] != ""]
    df_largo = df_largo.rename(columns={"_skills_list": "Habilidad"})
    
    cols_largo = [
        "Portal", "Tipo_Mercado", "Moneda_Original", "Codigo", "Nombre Oferta", "Empresa", "Ubicacion", "Modalidad", "Seniority",
        "Nivel_Educacion", "Anios_Experiencia", "Salario_COP", "Salario_Millones", "Habilidad", "URL"
    ]
    df_largo_dashboard = df_largo[[c for c in cols_largo if c in df_largo.columns]].copy()

    # 6. Exportación a Excel y CSV
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    from src.processing.cleaner import sanitizar_dataframe_para_excel
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        sanitizar_dataframe_para_excel(df).to_excel(writer, sheet_name="Matriz_Ofertas_Modelado", index=False)
        sanitizar_dataframe_para_excel(df_largo_dashboard).to_excel(writer, sheet_name="Habilidades_Largo_BI", index=False)
        sanitizar_dataframe_para_excel(df_valor).to_excel(writer, sheet_name="Valor_Economico_Habilidades", index=False)
        sanitizar_dataframe_para_excel(matriz_corr.reset_index()).to_excel(writer, sheet_name="Matriz_Correlacion", index=False)

    df.to_csv(output_matriz_csv, index=False, encoding="utf-8-sig")
    df_largo_dashboard.to_csv(output_largo_csv, index=False, encoding="utf-8-sig")

    print(f"[ANALYTICS] Datasets para Dashboards exportados a:\n  - {output_excel}\n  - {output_matriz_csv}\n  - {output_largo_csv}")

    return df, df_valor, matriz_corr
