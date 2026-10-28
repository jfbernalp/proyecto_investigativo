"""
Primas salariales por habilidad con controles (mercado local).

Modelo:  log(salario) = habilidades + nivel de experiencia + rol + portal + mes  (OLS, errores HC3)
- Prima de una habilidad = exp(β) − 1: diferencia porcentual del salario ofrecido entre ofertas
  comparables que la piden y que no la piden. Es una ASOCIACIÓN condicionada, no un efecto causal.
- Solo habilidades con al menos MIN_OFERTAS ofertas con salario que las pidan.
- Intervalo de confianza del 95 % y corrección por pruebas múltiples de Benjamini–Hochberg (q).
- Robustez: se re-estima dejando fuera cada portal.

Decisión de diseño (27-oct-2026): habilidades y experiencia se calculan desde el texto crudo guardado
(ofertas_raw_historico) con el método vigente, igual para todos los meses; no se usan las columnas
históricas de experiencia (sep–oct se calcularon con el extractor anterior).

REGLA DE ORO: si la muestra no alcanza, el resultado es "no concluyente"; no se reportan primas sin n,
sin intervalo o sin q.
"""
import json
from typing import Dict, List

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sqlalchemy import text
from statsmodels.stats.multitest import multipletests

from src.processing.cleaner import clasificar_rol_tecnico
from src.processing.requirements_parser import extraer_habilidades_texto
from src.processing.seniority import determinar_seniority

MERCADO_LOCAL = "Mercado Local (Colombia - COP)"
MIN_OFERTAS = 20
ALFA = 0.05
Q_MAX = 0.10
CAMPOS_TEXTO = ("Nombre Oferta", "Requisitos", "Descripcion", "Descripcion_detalle")


def cargar_ofertas(engine) -> pd.DataFrame:
    """Una fila por oferta local con salario (su registro más reciente) con el texto crudo."""
    return pd.read_sql_query(text("""
        SELECT DISTINCT ON (x.id_vacante_hash)
               x.id_vacante_hash, x.mes_periodo, x.salario_cop_mensual, d.portal, d.rol_buscado, r.payload_json
        FROM fact_extracciones_historico x
        JOIN dim_ofertas d USING (id_vacante_hash)
        JOIN ofertas_raw_historico r USING (id_vacante_hash, mes_periodo)
        WHERE x.salario_cop_mensual > 0 AND d.tipo_mercado = :mercado
        ORDER BY x.id_vacante_hash, x.mes_periodo DESC"""), engine, params={"mercado": MERCADO_LOCAL})


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Habilidades, nivel de experiencia (con su fuente) y log del salario, desde el texto crudo."""
    df = df.copy()
    cargas = df["payload_json"].apply(json.loads)
    textos = cargas.apply(lambda d: " ".join(str(d.get(k) or "") for k in CAMPOS_TEXTO))
    df["habilidades"] = textos.apply(lambda t: sorted(set(extraer_habilidades_texto(t))))
    seniority = cargas.apply(determinar_seniority)
    df["anios_experiencia"] = seniority.apply(lambda x: x[0])
    df["nivel"] = seniority.apply(lambda x: x[1])
    df["fuente_nivel"] = seniority.apply(lambda x: x[2])
    # Rol desde el título guardado: en dim_ofertas algunas filas tienen la palabra clave de búsqueda
    # ("cientifico-de-datos") en lugar del rol clasificado, lo que partía un mismo rol en dos categorías
    df["rol"] = cargas.apply(lambda d: clasificar_rol_tecnico(str(d.get("Nombre Oferta") or "")))
    df["log_salario"] = np.log(df["salario_cop_mensual"].astype(float))
    df["mes"] = df["mes_periodo"].astype(str)
    return df.drop(columns=["payload_json"])


def _matriz(df: pd.DataFrame, habilidades: List[str]) -> pd.DataFrame:
    X = pd.DataFrame({f"hab::{h}": df["habilidades"].apply(lambda hs, h=h: int(h in hs)) for h in habilidades},
                     index=df.index)
    controles = pd.get_dummies(df[["nivel", "rol", "portal", "mes"]], drop_first=True, dtype=int)
    X = pd.concat([X, controles], axis=1)
    X = X.loc[:, X.std() > 0]          # columnas constantes (p. ej. un portal ausente) no son estimables
    return sm.add_constant(X, has_constant="add")


def estimar(df: pd.DataFrame, min_ofertas: int = MIN_OFERTAS) -> Dict:
    conteo = pd.Series([h for hs in df["habilidades"] for h in hs]).value_counts()
    habilidades = sorted(conteo[conteo >= min_ofertas].index)
    resultado = {"n_ofertas": int(len(df)), "min_ofertas_por_habilidad": min_ofertas,
                 "habilidades_evaluadas": habilidades, "filas": []}
    if len(habilidades) == 0 or len(df) < 30:
        resultado["conclusion"] = "No concluyente: muestra insuficiente."
        return resultado

    X = _matriz(df, habilidades)
    modelo = sm.OLS(df["log_salario"], X).fit(cov_type="HC3")
    columnas = [c for c in X.columns if c.startswith("hab::")]
    p = modelo.pvalues[columnas]
    q = multipletests(p, alpha=ALFA, method="fdr_bh")[1]
    ic = modelo.conf_int(alpha=ALFA)
    for col, qv in zip(columnas, q):
        h = col.split("::", 1)[1]
        filas = {
            "habilidad": h,
            "n_ofertas_con_habilidad": int(conteo[h]),
            "prima_pct": round(float(100 * (np.exp(modelo.params[col]) - 1)), 1),
            "ic95_inferior_pct": round(float(100 * (np.exp(ic.loc[col, 0]) - 1)), 1),
            "ic95_superior_pct": round(float(100 * (np.exp(ic.loc[col, 1]) - 1)), 1),
            "p": round(float(p[col]), 4),
            "q_bh": round(float(qv), 4),
        }
        filas["concluyente"] = bool(qv <= Q_MAX and (filas["ic95_inferior_pct"] > 0 or filas["ic95_superior_pct"] < 0))
        resultado["filas"].append(filas)
    resultado["filas"].sort(key=lambda f: f["prima_pct"], reverse=True)
    resultado.update({"r2": round(float(modelo.rsquared), 3), "r2_ajustado": round(float(modelo.rsquared_adj), 3),
                      "parametros": int(X.shape[1])})
    return resultado


def estimar_roles(df: pd.DataFrame, min_ofertas: int = MIN_OFERTAS) -> Dict:
    """
    Prima por rol (un rol = un conjunto de habilidades que se contratan juntas), frente al rol más frecuente,
    controlando nivel, portal y mes:  log(salario) ~ rol + nivel + portal + mes  (HC3).
    Los roles con menos de min_ofertas ofertas con salario se reportan con su n pero no se evalúan.
    """
    conteo = df["rol"].value_counts()
    referencia = conteo.index[0]
    evaluables = [r for r in conteo.index if conteo[r] >= min_ofertas]
    resultado = {"referencia": referencia, "n_ofertas": int(len(df)), "min_ofertas_por_rol": min_ofertas,
                 "no_evaluables": {r: int(conteo[r]) for r in conteo.index if r not in evaluables}, "filas": []}
    sub = df[df["rol"].isin(evaluables)]
    if len(evaluables) < 2 or len(sub) < 30:
        resultado["conclusion"] = "No concluyente: muestra insuficiente."
        return resultado
    roles = pd.get_dummies(sub["rol"], dtype=int).drop(columns=[referencia])
    roles.columns = [f"rol::{c}" for c in roles.columns]
    controles = pd.get_dummies(sub[["nivel", "portal", "mes"]], drop_first=True, dtype=int)
    X = pd.concat([roles, controles], axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    modelo = sm.OLS(sub["log_salario"], X).fit(cov_type="HC3")
    columnas = [c for c in X.columns if c.startswith("rol::")]
    q = multipletests(modelo.pvalues[columnas], alpha=ALFA, method="fdr_bh")[1]
    ic = modelo.conf_int(alpha=ALFA)
    for col, qv in zip(columnas, q):
        rol = col.split("::", 1)[1]
        fila = {
            "rol": rol, "n_ofertas": int(conteo[rol]),
            "prima_pct": round(float(100 * (np.exp(modelo.params[col]) - 1)), 1),
            "ic95_inferior_pct": round(float(100 * (np.exp(ic.loc[col, 0]) - 1)), 1),
            "ic95_superior_pct": round(float(100 * (np.exp(ic.loc[col, 1]) - 1)), 1),
            "p": round(float(modelo.pvalues[col]), 4), "q_bh": round(float(qv), 4),
        }
        fila["concluyente"] = bool(qv <= Q_MAX and (fila["ic95_inferior_pct"] > 0 or fila["ic95_superior_pct"] < 0))
        resultado["filas"].append(fila)
    resultado["filas"].sort(key=lambda f: f["prima_pct"], reverse=True)
    resultado["r2"] = round(float(modelo.rsquared), 3)
    return resultado


def robustez_por_portal(df: pd.DataFrame, habilidades: List[str], min_ofertas: int = MIN_OFERTAS) -> Dict[str, Dict]:
    """Re-estima sin cada portal; devuelve la prima de cada habilidad en cada submuestra."""
    salida = {}
    for portal in sorted(df["portal"].unique()):
        sub = df[df["portal"] != portal]
        r = estimar(sub, min_ofertas=min(min_ofertas, max(5, int(len(sub) * 0.1))))
        salida[f"sin {portal}"] = {
            "n_ofertas": r["n_ofertas"],
            "primas": {f["habilidad"]: float(f["prima_pct"]) for f in r.get("filas", []) if f["habilidad"] in habilidades},
        }
    return salida


def describir_muestra(df: pd.DataFrame) -> Dict:
    return {
        "por_portal": df["portal"].value_counts().to_dict(),
        "por_mes": df["mes"].value_counts().sort_index().to_dict(),
        "por_nivel": df["nivel"].value_counts().to_dict(),
        "fuente_nivel": df["fuente_nivel"].value_counts().to_dict(),
        "por_rol": df["rol"].value_counts().to_dict(),
        "mediana_salario_cop": float(df["salario_cop_mensual"].median()),
    }
