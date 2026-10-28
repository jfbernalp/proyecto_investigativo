"""
Roles emergentes y en descenso: cambio de la participación de cada rol en las ofertas frente al mes anterior.

- Rol desde el título guardado de la oferta (clasificar_rol_tecnico), igual que en primas salariales.
- Solo se comparan los PORTALES PRESENTES EN AMBOS MESES: si entra o sale un portal (p. ej. Magneto o
  Remotive en octubre, Torre en septiembre), la mezcla de ofertas cambia y movería las participaciones
  aunque el mercado no haya cambiado.
- Se excluyen también los portales cuyos términos de búsqueda cambiaron entre los dos meses
  (CAMBIOS_DISENO_BUSQUEDA): el cambio mediría el scraper, no el mercado.
- Prueba de dos proporciones por rol y corrección de Benjamini–Hochberg (q).
  Emergente / En descenso solo si q ≤ Q_MAX; "Nuevo" si el rol no tenía ofertas el mes anterior.

REGLA DE ORO: un cambio entre dos meses no es una tendencia. Con menos de MIN_CORTES_TENDENCIA cortes el
resultado se rotula "frente al mes anterior" y no se afirma que un rol esté "muriendo".
"""
import json
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm
from sqlalchemy import text
from statsmodels.stats.multitest import multipletests

from src.processing.cleaner import clasificar_rol_tecnico

Q_MAX = 0.10
MIN_OFERTAS_PAR = 10          # ofertas del rol sumando ambos meses para evaluarlo
MIN_CORTES_TENDENCIA = 3

# Cambios en los términos de búsqueda de un portal (mes desde el que rige el diseño nuevo). Comparar un
# mes con otro de diseño distinto mediría el cambio del scraper, no del mercado: ese portal se excluye.
# LinkedIn: 2026-10-17 (60ff450) pasó de buscar solo "científico de datos" a incluir analista e ingeniero.
CAMBIOS_DISENO_BUSQUEDA = {"LinkedIn": [202610]}

EMERGENTE, DESCENSO, NUEVO, SIN_CAMBIO, NO_EVALUABLE = (
    "Emergente", "En descenso", "Nuevo", "Sin cambio concluyente", "No evaluable (pocas ofertas)")


def cargar_roles(engine) -> pd.DataFrame:
    """Una fila por oferta y mes con su portal y su rol."""
    df = pd.read_sql_query(text("""
        SELECT r.mes_periodo, r.id_vacante_hash, d.portal, r.payload_json
        FROM ofertas_raw_historico r JOIN dim_ofertas d USING (id_vacante_hash)"""), engine)
    df["rol"] = df["payload_json"].apply(lambda p: clasificar_rol_tecnico(str(json.loads(p).get("Nombre Oferta") or "")))
    return df.drop(columns=["payload_json"])


def portales_comparables(df: pd.DataFrame, mes: int, mes_anterior: int) -> Tuple[List[str], List[str]]:
    """Portales con ofertas en ambos meses y sin cambio de diseño de búsqueda entre ellos (y los excluidos)."""
    comunes = set(df.loc[df.mes_periodo == mes, "portal"]) & set(df.loc[df.mes_periodo == mes_anterior, "portal"])
    cambiaron = {p for p, meses in CAMBIOS_DISENO_BUSQUEDA.items() if any(mes_anterior < m <= mes for m in meses)}
    return sorted(comunes - cambiaron), sorted(comunes & cambiaron)


def _dos_proporciones(x1, n1, x2, n2) -> float:
    p = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    return float(2 * norm.sf(abs((x1 / n1 - x2 / n2) / se)))


def comparar_meses(df: pd.DataFrame, mes: int, mes_anterior: Optional[int] = None) -> Dict:
    meses = sorted(df["mes_periodo"].unique())
    if mes_anterior is None:
        anteriores = [m for m in meses if m < mes]
        if not anteriores:
            return {"mes": int(mes), "filas": [], "conclusion": "No hay un mes anterior con el cual comparar."}
        mes_anterior = anteriores[-1]
    portales, excluidos = portales_comparables(df, mes, mes_anterior)
    sub = df[df.portal.isin(portales)]
    act, ant = sub[sub.mes_periodo == mes], sub[sub.mes_periodo == mes_anterior]
    n_act, n_ant = len(act), len(ant)
    resultado = {"mes": int(mes), "mes_anterior": int(mes_anterior), "portales_comparados": portales,
                 "portales_excluidos_por_cambio_de_busqueda": excluidos,
                 "n_ofertas": n_act, "n_ofertas_anterior": n_ant,
                 "cortes_disponibles": len(meses), "es_tendencia": len(meses) >= MIN_CORTES_TENDENCIA, "filas": []}
    if n_act == 0 or n_ant == 0:
        resultado["conclusion"] = "No hay portales con ofertas en ambos meses."
        return resultado
    c_act, c_ant = act["rol"].value_counts(), ant["rol"].value_counts()
    filas = []
    for rol in sorted(set(c_act.index) | set(c_ant.index)):
        x1, x2 = int(c_act.get(rol, 0)), int(c_ant.get(rol, 0))
        filas.append({"rol": rol, "n_ofertas": x1, "pct": round(100 * x1 / n_act, 1),
                      "n_ofertas_anterior": x2, "pct_anterior": round(100 * x2 / n_ant, 1),
                      "cambio_pp": round(100 * (x1 / n_act - x2 / n_ant), 1),
                      "p": _dos_proporciones(x1, n_act, x2, n_ant) if x1 + x2 >= MIN_OFERTAS_PAR else None})
    evaluables = [f for f in filas if f["p"] is not None]
    if evaluables:
        qs = multipletests([f["p"] for f in evaluables], method="fdr_bh")[1]
        for f, q in zip(evaluables, qs):
            f["q_bh"] = round(float(q), 4)
    for f in filas:
        f["p"] = None if f["p"] is None else round(f["p"], 4)
        f.setdefault("q_bh", None)
        if f["n_ofertas_anterior"] == 0 and f["n_ofertas"] > 0:
            f["estado"] = NUEVO
        elif f["q_bh"] is None:
            f["estado"] = NO_EVALUABLE
        elif f["q_bh"] <= Q_MAX:
            f["estado"] = EMERGENTE if f["cambio_pp"] > 0 else DESCENSO
        else:
            f["estado"] = SIN_CAMBIO
    resultado["filas"] = sorted(filas, key=lambda f: f["cambio_pp"], reverse=True)
    resultado["lectura"] = (
        "Cambio de la participación del rol entre dos cortes, en los portales presentes en ambos y sin "
        "cambios en sus términos de búsqueda. "
        + ("" if resultado["es_tendencia"] else
           f"Con {len(meses)} cortes no es una tendencia: confirme con al menos {MIN_CORTES_TENDENCIA} meses."))
    return resultado
