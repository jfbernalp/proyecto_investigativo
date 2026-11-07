"""
Evaluación de la extracción contra el etiquetado manual (Artículo 1).

Lee las planillas llenas de data/anotacion/ (ver docs/articulo/guia_anotacion.md) y calcula:
  1. Validación de las planillas: valores fuera de lista, años no numéricos, filas sin rol o nivel.
  2. Acuerdo entre anotadores (ofertas etiquetadas por A y B): kappa de Cohen y % de acuerdo por
     habilidad, rol y nivel; años exactos y a ±1.
  3. Desempeño del sistema contra la referencia:
     - habilidades: precisión, recall y F1 por habilidad y en conjunto (micro y macro), en dos versiones:
       «publicado» (habilidades guardadas en fact_habilidades_historico) y «recalculado» (código actual
       sobre el texto original);
     - Excel: la regla del sistema contra «cualquier nivel» y contra «avanzado explícito»;
     - filtro de relevancia y rol: exactitud, F1 macro y matriz de confusión;
     - años y nivel: detección, exactitud y error absoluto.
     Intervalos de confianza del 95 % por bootstrap sobre ofertas.

Referencia: para las ofertas con doble anotación se usa la planilla adjudicada si existe
(data/anotacion/adjudicado.xlsx, mismo formato); si no, la de A, y el informe lo marca como provisional.

Solo lectura en la base. La salida solo contiene cifras agregadas (sin texto de ofertas):
  data/analytics/evaluacion_extraccion.json

Uso:  python scripts/evaluar_anotacion.py [--bootstrap 2000] [--semilla 2026]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.processing.taxonomies import TAXONOMIA_HABILIDADES  # noqa: E402

CARPETA = ROOT_DIR / "data" / "anotacion"
SALIDA = ROOT_DIR / "data" / "analytics" / "evaluacion_extraccion.json"
HABILIDADES = list(TAXONOMIA_HABILIDADES)
EXCEL_CUALQUIER = "Excel u hojas de cálculo (cualquier nivel)"
EXCEL_AVANZADO = "Excel AVANZADO (lo dice explícitamente)"
ROLES = ["Científico de Datos", "Analista de Datos", "Ingeniero de Datos", "Machine Learning / AI Engineer",
         "Analista de BI y Visualización", "Desarrollador de Software / Datos", "Otro rol", "No es del tema"]
NIVELES = ["Junior", "Semi-Senior", "Senior", "Líder", "No se indica"]
ROL_SISTEMA = {
    "Científico de Datos (Data Scientist)": "Científico de Datos",
    "Analista de Datos (Data Analyst)": "Analista de Datos",
    "Ingeniero de Datos (Data Engineer)": "Ingeniero de Datos",
    "Machine Learning / AI Engineer": "Machine Learning / AI Engineer",
    "Analista de BI & Visualización": "Analista de BI y Visualización",
    "Desarrollador de Software / Datos": "Desarrollador de Software / Datos",
    "Sin clasificar": "Otro rol",          # relevante pero sin rol reconocible en el título
}
# El sistema distingue «Practicante»; la guía no: se compara como Junior
NIVEL_SISTEMA = {"Practicante": "Junior", "Junior": "Junior", "Semi-Senior": "Semi-Senior", "Senior": "Senior",
                 "Líder": "Líder", "No especificado": "No se indica", None: "No se indica"}


# --------------------------------------------------------------------------- lectura y validación

def leer_planilla(ruta: Path):
    """Devuelve (DataFrame normalizado, lista de problemas). Habilidades como 0/1; años como float o NaN."""
    ws = load_workbook(ruta, data_only=True)["anotacion"]
    filas = list(ws.iter_rows(values_only=True))
    cab = [str(c) if c is not None else "" for c in filas[0]]
    problemas, registros = [], []
    for fila in filas[1:]:
        d = dict(zip(cab, fila))
        if not d.get("id_muestra"):
            continue
        idm = str(d["id_muestra"])
        rol = (str(d.get("rol")).strip() if d.get("rol") is not None else "")
        nivel = (str(d.get("nivel")).strip() if d.get("nivel") is not None else "")
        if rol not in ROLES:
            problemas.append(f"{idm}: rol vacío o fuera de la lista ({rol!r})")
        if nivel not in NIVELES:
            problemas.append(f"{idm}: nivel vacío o fuera de la lista ({nivel!r})")
        anios = d.get("anios_minimos")
        if anios in (None, ""):
            anios = np.nan
        else:
            try:
                anios = float(str(anios).replace(",", "."))
            except ValueError:
                problemas.append(f"{idm}: años no numéricos ({anios!r})"); anios = np.nan
        reg = {"id_muestra": idm, "rol": rol, "nivel": nivel, "anios": anios}
        for h in HABILIDADES + ["Excel avanzado explícito"]:
            col = {"Excel Avanzado": EXCEL_CUALQUIER, "Excel avanzado explícito": EXCEL_AVANZADO}.get(h, h)
            v = d.get(col)
            if v in (None, ""):
                reg[h] = 0
            elif str(v).strip() in ("1", "1.0"):
                reg[h] = 1
            else:
                problemas.append(f"{idm}: valor no válido en «{col}» ({v!r}); se toma como 0"); reg[h] = 0
        registros.append(reg)
    return pd.DataFrame(registros).set_index("id_muestra"), problemas


# --------------------------------------------------------------------------- métricas

def kappa_cohen(a, b):
    """Kappa de Cohen para dos listas de etiquetas. None si no está definido (sin variación esperada)."""
    a, b = list(a), list(b)
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else (po - pe) / (1 - pe)


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if (p == 0 or r == 0) else None)
    return p, r, f


def conteos(gold: np.ndarray, pred: np.ndarray):
    return int(((gold == 1) & (pred == 1)).sum()), int(((gold == 0) & (pred == 1)).sum()), int(((gold == 1) & (pred == 0)).sum())


def bootstrap(fn, n_filas: int, reps: int, rng):
    """IC 95 % de una métrica remuestreando filas (ofertas). fn recibe índices y devuelve un número o None."""
    vals = [fn(rng.integers(0, n_filas, n_filas)) for _ in range(reps)]
    vals = [v for v in vals if v is not None]
    return [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)] if vals else None


def r3(x):
    return None if x is None else round(float(x), 3)


def acuerdo(A: pd.DataFrame, B: pd.DataFrame):
    comunes = A.index.intersection(B.index)
    a, b = A.loc[comunes], B.loc[comunes]
    por_habilidad = {}
    for h in HABILIDADES + ["Excel avanzado explícito"]:
        por_habilidad[h] = {"kappa": r3(kappa_cohen(a[h], b[h])), "acuerdo": r3((a[h] == b[h]).mean()),
                            "positivos_A": int(a[h].sum()), "positivos_B": int(b[h].sum())}
    ambos_con_anios = a["anios"].notna() & b["anios"].notna()
    return {
        "n_ofertas": int(len(comunes)),
        "rol": {"kappa": r3(kappa_cohen(a["rol"], b["rol"])), "acuerdo": r3((a["rol"] == b["rol"]).mean())},
        "nivel": {"kappa": r3(kappa_cohen(a["nivel"], b["nivel"])), "acuerdo": r3((a["nivel"] == b["nivel"]).mean())},
        "anios": {"ambos_detectan_o_ambos_vacio": r3((a["anios"].notna() == b["anios"].notna()).mean()),
                  "exactos_cuando_ambos_dan_valor": r3((a.loc[ambos_con_anios, "anios"] == b.loc[ambos_con_anios, "anios"]).mean()) if ambos_con_anios.any() else None,
                  "a_un_anio_cuando_ambos_dan_valor": r3(((a.loc[ambos_con_anios, "anios"] - b.loc[ambos_con_anios, "anios"]).abs() <= 1).mean()) if ambos_con_anios.any() else None},
        "habilidades": por_habilidad,
        "kappa_medio_habilidades": r3(np.mean([v["kappa"] for v in por_habilidad.values() if v["kappa"] is not None])),
    }


def evaluar_habilidades(gold: pd.DataFrame, pred: pd.DataFrame, reps: int, rng):
    """gold y pred: DataFrames 0/1 con las mismas filas (ofertas) y columnas (habilidades)."""
    G, P = gold.to_numpy(), pred.to_numpy()
    por_habilidad = {}
    for j, h in enumerate(gold.columns):
        tp, fp, fn = conteos(G[:, j], P[:, j])
        p, r, f = prf(tp, fp, fn)
        por_habilidad[h] = {"positivos_referencia": int(G[:, j].sum()), "tp": tp, "fp": fp, "fn": fn,
                            "precision": r3(p), "recall": r3(r), "f1": r3(f)}
    def micro(idx):
        tp, fp, fn = conteos(G[idx].ravel(), P[idx].ravel())
        return prf(tp, fp, fn)
    def macro_f1(idx):
        fs = [prf(*conteos(G[idx, j], P[idx, j]))[2] for j in range(G.shape[1]) if G[idx, j].sum() > 0]
        fs = [f for f in fs if f is not None]
        return float(np.mean(fs)) if fs else None
    p, r, f = micro(np.arange(len(G)))
    return {
        "micro": {"precision": r3(p), "recall": r3(r), "f1": r3(f),
                  "ic95_precision": bootstrap(lambda i: micro(i)[0], len(G), reps, rng),
                  "ic95_recall": bootstrap(lambda i: micro(i)[1], len(G), reps, rng),
                  "ic95_f1": bootstrap(lambda i: micro(i)[2], len(G), reps, rng)},
        "macro_f1": r3(macro_f1(np.arange(len(G)))), "ic95_macro_f1": bootstrap(macro_f1, len(G), reps, rng),
        "por_habilidad": por_habilidad,
    }


def evaluar_categorias(gold: pd.Series, pred: pd.Series, etiquetas, reps: int, rng):
    g, p = gold.to_numpy(), pred.to_numpy()
    def exactitud(idx):
        return float((g[idx] == p[idx]).mean())
    def f1_macro(idx):
        fs = []
        for e in etiquetas:
            tp = int(((g[idx] == e) & (p[idx] == e)).sum()); fp = int(((g[idx] != e) & (p[idx] == e)).sum())
            fn = int(((g[idx] == e) & (p[idx] != e)).sum())
            if tp + fn:
                fs.append(prf(tp, fp, fn)[2] or 0.0)
        return float(np.mean(fs)) if fs else None
    todo = np.arange(len(g))
    matriz = pd.crosstab(pd.Series(g, name="referencia"), pd.Series(p, name="sistema"))
    return {"exactitud": r3(exactitud(todo)), "ic95_exactitud": bootstrap(exactitud, len(g), reps, rng),
            "f1_macro": r3(f1_macro(todo)), "ic95_f1_macro": bootstrap(f1_macro, len(g), reps, rng),
            "matriz_confusion": {str(k): {str(c): int(v) for c, v in fila.items()} for k, fila in matriz.iterrows()}}


def evaluar_anios(gold: pd.Series, pred: pd.Series):
    g, p = gold.to_numpy(dtype=float), pred.to_numpy(dtype=float)
    ref, sis = ~np.isnan(g), ~np.isnan(p)
    ambos = ref & sis
    return {
        "ofertas_con_anios_en_referencia": int(ref.sum()),
        "recall_deteccion": r3(ambos.sum() / ref.sum()) if ref.sum() else None,
        "precision_deteccion": r3(ambos.sum() / sis.sum()) if sis.sum() else None,
        "sistema_da_anios_que_la_oferta_no_dice": int((sis & ~ref).sum()),
        "exactos_cuando_ambos": r3((g[ambos] == p[ambos]).mean()) if ambos.any() else None,
        "error_absoluto_medio": r3(np.abs(g[ambos] - p[ambos]).mean()) if ambos.any() else None,
    }


# --------------------------------------------------------------------------- predicciones del sistema

def predicciones_sistema(clave: pd.DataFrame) -> pd.DataFrame:
    """Lo que el sistema dice de cada oferta de la muestra (solo lectura en la base)."""
    from sqlalchemy import create_engine, text
    from src.database.db_manager import DATABASE_URL, normalizar_url_bd
    from src.processing.cleaner import clasificar_rol_tecnico, es_oferta_relevante
    from src.processing.requirements_parser import extraer_habilidades_texto
    from src.processing.seniority import determinar_seniority

    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    hashes = tuple(clave["id_vacante_hash"])
    with engine.connect() as conn:
        crudo = pd.read_sql_query(text("""
            SELECT DISTINCT ON (id_vacante_hash) id_vacante_hash, payload_json FROM ofertas_raw_historico
            WHERE id_vacante_hash IN :h ORDER BY id_vacante_hash, mes_periodo DESC"""), conn, params={"h": hashes})
        guardadas = pd.read_sql_query(text("""
            SELECT DISTINCT id_vacante_hash, habilidad FROM fact_habilidades_historico WHERE id_vacante_hash IN :h"""),
            conn, params={"h": hashes})
    cargas = dict(zip(crudo.id_vacante_hash, crudo.payload_json.apply(json.loads)))
    por_hash = guardadas.groupby("id_vacante_hash")["habilidad"].apply(set).to_dict()
    filas = []
    for _, k in clave.iterrows():
        d = cargas.get(k.id_vacante_hash, {})
        titulo = str(d.get("Nombre Oferta") or "")
        texto = " ".join(str(d.get(c) or "") for c in ("Nombre Oferta", "Requisitos", "Descripcion", "Descripcion_detalle"))
        relevante = es_oferta_relevante(titulo, str(d.get("Descripcion") or ""))
        anios, nivel, _ = determinar_seniority(d)
        recalculadas = set(extraer_habilidades_texto(texto))
        fila = {"id_muestra": k.id_muestra, "relevante": relevante,
                "rol": ROL_SISTEMA.get(clasificar_rol_tecnico(titulo), "Otro rol") if relevante else "No es del tema",
                "anios": np.nan if anios is None else float(anios), "nivel": NIVEL_SISTEMA.get(nivel, "No se indica")}
        for h in HABILIDADES:
            fila[f"pub::{h}"] = int(h in por_hash.get(k.id_vacante_hash, set()))
            fila[f"rec::{h}"] = int(h in recalculadas)
        filas.append(fila)
    return pd.DataFrame(filas).set_index("id_muestra")


# --------------------------------------------------------------------------- principal

def evaluar(gold: pd.DataFrame, sis: pd.DataFrame, reps: int, rng) -> dict:
    ids = gold.index.intersection(sis.index)
    gold, sis = gold.loc[ids], sis.loc[ids]
    resultado = {"n_ofertas": int(len(ids))}
    for version in ("pub", "rec"):
        pred = sis[[f"{version}::{h}" for h in HABILIDADES]].set_axis(HABILIDADES, axis=1)
        resultado[{"pub": "habilidades_publicado", "rec": "habilidades_recalculado"}[version]] = \
            evaluar_habilidades(gold[HABILIDADES], pred, reps, rng)
    excel = sis["pub::Excel Avanzado"].to_numpy()
    resultado["excel"] = {
        "contra_cualquier_nivel": dict(zip(("precision", "recall", "f1"), map(r3, prf(*conteos(gold["Excel Avanzado"].to_numpy(), excel))))),
        "contra_avanzado_explicito": dict(zip(("precision", "recall", "f1"), map(r3, prf(*conteos(gold["Excel avanzado explícito"].to_numpy(), excel))))),
    }
    tema_ref = (gold["rol"] != "No es del tema").astype(int).to_numpy()
    resultado["filtro_relevancia"] = dict(zip(("precision", "recall", "f1"), map(r3, prf(*conteos(tema_ref, sis["relevante"].astype(int).to_numpy())))))
    resultado["rol"] = evaluar_categorias(gold["rol"], sis["rol"], ROLES, reps, rng)
    resultado["nivel"] = evaluar_categorias(gold["nivel"], sis["nivel"], NIVELES, reps, rng)
    resultado["anios"] = evaluar_anios(gold["anios"], sis["anios"])
    return resultado


def cargar_referencia():
    """(A, B, referencia, problemas): la referencia es A con las ofertas adjudicadas reemplazadas, si existen."""
    A, prob_a = leer_planilla(CARPETA / "anotador_A.xlsx")
    B, prob_b = leer_planilla(CARPETA / "anotador_B.xlsx")
    problemas = [f"A · {p}" for p in prob_a] + [f"B · {p}" for p in prob_b]
    adjudicado = CARPETA / "adjudicado.xlsx"
    gold = A.copy()
    if adjudicado.exists():
        ADJ, prob_adj = leer_planilla(adjudicado)
        problemas += [f"adjudicado · {p}" for p in prob_adj]
        gold.loc[ADJ.index.intersection(gold.index)] = ADJ.loc[ADJ.index.intersection(gold.index)]
    return A, B, gold, problemas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--semilla", type=int, default=2026)
    args = ap.parse_args()
    rng = np.random.default_rng(args.semilla)

    A, B, gold, problemas = cargar_referencia()
    adjudicado = CARPETA / "adjudicado.xlsx"
    sin_llenar = int((A["rol"] == "").sum())
    if problemas:
        print(f"[AVISO] {len(problemas)} problemas en las planillas (primeros 20):")
        for p in problemas[:20]:
            print("  -", p)
    if sin_llenar == len(A):
        print("La planilla de A está vacía: no hay nada que evaluar todavía."); return

    clave = pd.read_csv(CARPETA / "clave_muestra.csv")
    sis = predicciones_sistema(clave)
    resultado = {
        "fecha_referencia": "adjudicada" if adjudicado.exists() else "provisional (A sin adjudicar)",
        "problemas_en_planillas": len(problemas),
        "acuerdo_entre_anotadores": acuerdo(A, B),
        "sistema_vs_referencia": evaluar(gold[gold["rol"] != ""], sis, args.bootstrap, rng),
        "bootstrap": f"{args.bootstrap} remuestreos de ofertas, semilla {args.semilla}",
    }
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    s = resultado["sistema_vs_referencia"]; ac = resultado["acuerdo_entre_anotadores"]
    print(f"Referencia: {resultado['fecha_referencia']} · {s['n_ofertas']} ofertas · acuerdo A–B en {ac['n_ofertas']}")
    print(f"Acuerdo: kappa rol {ac['rol']['kappa']} · nivel {ac['nivel']['kappa']} · habilidades (media) {ac['kappa_medio_habilidades']}")
    for v in ("habilidades_publicado", "habilidades_recalculado"):
        m = s[v]["micro"]
        print(f"{v}: P {m['precision']} {m['ic95_precision']} · R {m['recall']} {m['ic95_recall']} · F1 {m['f1']} {m['ic95_f1']} · F1 macro {s[v]['macro_f1']}")
    print(f"Excel: {s['excel']} · filtro de relevancia: {s['filtro_relevancia']}")
    print(f"Rol: exactitud {s['rol']['exactitud']} {s['rol']['ic95_exactitud']} · F1 macro {s['rol']['f1_macro']}")
    print(f"Nivel: exactitud {s['nivel']['exactitud']} · años: {s['anios']}")
    print(f"Guardado en {SALIDA}")


if __name__ == "__main__":
    main()
