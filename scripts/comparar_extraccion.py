"""
E2 y comparación pareada de E1 frente a E6 (Artículo 1, hito 65).

- E2: el clasificador de rol **publicado** (el de `main`, por subcadenas) frente al **corregido** (rama de trabajo), sobre
  las mismas 200 ofertas y la misma referencia.
- Reglas frente a LLM: el sistema de reglas (habilidades recalculadas, rol corregido, nivel, años) frente a Gemini con la
  misma guía (E6).

Cada diferencia se reporta con un IC del 95 % por bootstrap **pareado** (se remuestrean ofertas y se calculan ambas
métricas sobre la misma réplica). Solo lectura en la base.

    python scripts/comparar_extraccion.py [--bootstrap 2000] [--semilla 2026] [--modelo gemini-4-argon]

Salida: data/analytics/comparacion_extraccion.json
"""
import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import evaluar_anotacion as ev  # noqa: E402
import linea_base_llm as llm  # noqa: E402

SALIDA = ROOT_DIR / "data" / "analytics" / "comparacion_extraccion.json"


def clasificador_publicado():
    """clasificar_rol_tecnico tal como está en main (versión publicada en el portal y el tablero)."""
    fuente = subprocess.run(["git", "show", "main:src/processing/cleaner.py"], cwd=ROOT_DIR, capture_output=True,
                            text=True, check=True).stdout
    nodo = next(n for n in ast.parse(fuente).body if isinstance(n, ast.FunctionDef) and n.name == "clasificar_rol_tecnico")
    espacio = {}
    exec(compile(ast.Module(body=[nodo], type_ignores=[]), "main:cleaner.py", "exec"), espacio)
    return espacio["clasificar_rol_tecnico"]


def titulos(clave: pd.DataFrame) -> pd.Series:
    from sqlalchemy import create_engine, text
    from src.database.db_manager import DATABASE_URL, normalizar_url_bd
    with create_engine(normalizar_url_bd(DATABASE_URL)).connect() as conn:
        crudo = pd.read_sql_query(text("""
            SELECT DISTINCT ON (id_vacante_hash) id_vacante_hash, payload_json FROM ofertas_raw_historico
            WHERE id_vacante_hash IN :h ORDER BY id_vacante_hash, mes_periodo DESC"""), conn,
            params={"h": tuple(clave["id_vacante_hash"])})
    por_hash = {h: str(json.loads(p).get("Nombre Oferta") or "") for h, p in zip(crudo.id_vacante_hash, crudo.payload_json)}
    return pd.Series({k.id_muestra: por_hash.get(k.id_vacante_hash, "") for _, k in clave.iterrows()})


# --------------------------------------------------------------------------- métricas por réplica

def f1_micro(gold: np.ndarray, pred: np.ndarray) -> float:
    vp = (gold & pred).sum(); fp = (~gold & pred).sum(); fn = (gold & ~pred).sum()
    return 2 * vp / (2 * vp + fp + fn) if vp else 0.0


def recall_anios(g: np.ndarray, p: np.ndarray) -> float:
    con = ~np.isnan(g)
    return float((~np.isnan(p[con])).mean()) if con.any() else float("nan")


def diferencia(metrica, a, b, gold, reps, rng):
    """metrica(gold, pred) sobre índices; devuelve valores y la diferencia b − a con IC pareado."""
    n = len(gold[0]) if isinstance(gold, tuple) else len(gold)
    va, vb = metrica(gold, a, slice(None)), metrica(gold, b, slice(None))
    difs = []
    for _ in range(reps):
        i = rng.integers(0, n, n)
        difs.append(metrica(gold, b, i) - metrica(gold, a, i))
    lo, hi = np.percentile(difs, [2.5, 97.5])
    return {"a": ev.r3(va), "b": ev.r3(vb), "diferencia_b_menos_a": ev.r3(vb - va), "ic95": [ev.r3(lo), ev.r3(hi)],
            "concluyente": bool(lo > 0 or hi < 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--modelo", default="gemini-4-argon")
    a = ap.parse_args()
    rng = np.random.default_rng(a.semilla)

    _, _, gold, _ = ev.cargar_referencia()
    gold = gold[gold["rol"] != ""]
    clave = pd.read_csv(ev.CARPETA / "clave_muestra.csv")
    sis = ev.predicciones_sistema(clave)
    lm = llm.predicciones(a.modelo)
    ids = gold.index.intersection(sis.index).intersection(lm.index)
    gold, sis, lm = gold.loc[ids], sis.loc[ids], lm.loc[ids]

    # Rol publicado: misma lógica de relevancia que el sistema; solo cambia el clasificador
    publicado = clasificador_publicado()
    tit = titulos(clave).loc[ids]
    rol_pub = pd.Series([ev.ROL_SISTEMA.get(publicado(t), "Otro rol") if rel else "No es del tema"
                         for t, rel in zip(tit, sis["relevante"])], index=ids)

    exacto = lambda g, p, i: float((np.asarray(g)[i] == np.asarray(p)[i]).mean())
    g_rol = gold["rol"].to_numpy()
    habs = ev.HABILIDADES
    G = gold[habs].to_numpy().astype(bool)
    f1 = lambda g, p, i: f1_micro(g[i].ravel(), p[i].ravel())
    rec = sis[[f"rec::{h}" for h in habs]].to_numpy().astype(bool)
    lmh = lm[[f"rec::{h}" for h in habs]].to_numpy().astype(bool)
    g_anios = gold["anios"].to_numpy(dtype=float)

    resultado = {
        "n_ofertas": int(len(ids)),
        "referencia": "adjudicada" if (ev.CARPETA / "adjudicado.xlsx").exists() else "provisional (A sin adjudicar)",
        "E2_rol_publicado_vs_corregido": {
            "exactitud": diferencia(exacto, rol_pub.to_numpy(), sis["rol"].to_numpy(), g_rol, a.bootstrap, rng),
            "ofertas_que_cambian_de_rol": int((rol_pub != sis["rol"]).sum()),
            "publicado": ev.evaluar_categorias(gold["rol"], rol_pub, ev.ROLES, a.bootstrap, rng),
            "corregido": ev.evaluar_categorias(gold["rol"], sis["rol"], ev.ROLES, a.bootstrap, rng),
        },
        "reglas_vs_llm": {
            "modelo": a.modelo,
            "habilidades_f1_micro": diferencia(f1, rec, lmh, G, a.bootstrap, rng),
            "rol_exactitud": diferencia(exacto, sis["rol"].to_numpy(), lm["rol"].to_numpy(), g_rol, a.bootstrap, rng),
            "nivel_exactitud": diferencia(exacto, sis["nivel"].to_numpy(), lm["nivel"].to_numpy(),
                                          gold["nivel"].to_numpy(), a.bootstrap, rng),
            "anios_recall_deteccion": diferencia(lambda g, p, i: recall_anios(g[i], p[i]), sis["anios"].to_numpy(dtype=float),
                                                 lm["anios"].to_numpy(dtype=float), g_anios, a.bootstrap, rng),
        },
        "bootstrap": f"{a.bootstrap} remuestreos pareados de ofertas, semilla {a.semilla}; a = reglas (o rol publicado), b = LLM (o rol corregido)",
    }
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    e2 = resultado["E2_rol_publicado_vs_corregido"]
    print(f"Referencia {resultado['referencia']} · {resultado['n_ofertas']} ofertas")
    print(f"E2 rol: publicado {e2['exactitud']['a']} → corregido {e2['exactitud']['b']} · Δ {e2['exactitud']['diferencia_b_menos_a']} "
          f"{e2['exactitud']['ic95']} · F1 macro {e2['publicado']['f1_macro']} → {e2['corregido']['f1_macro']} · cambian {e2['ofertas_que_cambian_de_rol']}")
    for k, v in resultado["reglas_vs_llm"].items():
        if isinstance(v, dict):
            print(f"{k}: reglas {v['a']} · LLM {v['b']} · Δ {v['diferencia_b_menos_a']} {v['ic95']}{' (concluyente)' if v['concluyente'] else ''}")
    print(f"Guardado en {SALIDA.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
