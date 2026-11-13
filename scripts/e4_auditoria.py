"""
Auditoría del etiquetado de E4 (hito 70): una segunda persona reetiqueta a ciegas una submuestra aleatoria de las cifras
y se mide el acuerdo con la planilla principal. Motivo: no se pudo descartar que la planilla principal se llenara con
ayuda de una herramienta de IA; el acuerdo con un etiquetado humano independiente valida (o no) esas etiquetas.

    python scripts/e4_auditoria.py planilla    → data/evaluacion_ia/e4_auditoria.xlsx (sin etiquetas; no sobrescribe)
    python scripts/e4_auditoria.py evaluar     → acuerdo (κ de Cohen) por pregunta, sobre las filas auditadas

La submuestra es estratificada (15 marcadas, 15 revisadas sin marca, 10 no revisadas; semilla 2026) y parte de la
planilla original sin etiquetar (e4_cifras_original_20261108.xlsx), con la hoja «contexto» de un solo contexto_id.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parent.parent
CARPETA = ROOT_DIR / "data" / "evaluacion_ia"
ORIGINAL = CARPETA / "e4_cifras_original_20261108.xlsx"
PRINCIPAL = CARPETA / "e4_cifras.xlsx"
AUDITORIA = CARPETA / "e4_auditoria.xlsx"
SALIDA = CARPETA / "e4_auditoria_resultados.json"
POR_ESTRATO = {"marcada": 15, "revisada": 15, "no revisada": 10}
CONTEXTO = "c0d2415dbc12"


def leer(ruta: Path) -> pd.DataFrame:
    filas = list(load_workbook(ruta, data_only=True)["cifras"].iter_rows(values_only=True))
    return pd.DataFrame(filas[1:], columns=filas[0]).dropna(subset=["id_cifra"])


def planilla():
    if AUDITORIA.exists():
        sys.exit(f"{AUDITORIA.name} ya existe: no se sobrescribe.")
    clave = pd.read_csv(CARPETA / "e4_clave.csv")
    rng = np.random.default_rng(2026)
    elegidas = set()
    for estrato, n in POR_ESTRATO.items():
        ids = clave.loc[clave.estrato == estrato, "id_cifra"].to_numpy()
        elegidas |= set(rng.choice(ids, size=min(n, len(ids)), replace=False))
    wb = load_workbook(ORIGINAL)
    ws = wb["cifras"]
    for fila in range(ws.max_row, 1, -1):          # de abajo hacia arriba para no correr los índices
        if ws.cell(fila, 1).value not in elegidas:
            ws.delete_rows(fila)
    ctx = wb["contexto"]
    filas_ctx = [r for r in ctx.iter_rows(min_row=2, values_only=True) if r[0] == CONTEXTO]
    ctx.delete_rows(2, ctx.max_row)
    for r in filas_ctx:
        ctx.append(list(r))
    ctx.auto_filter.ref = f"A1:C{ctx.max_row}"
    ws.auto_filter.ref = f"A1:H{ws.max_row}"
    ins = wb["instrucciones"]
    ins.insert_rows(1, 2)
    ins["A1"] = ("AUDITORÍA: etiquete estas cifras con las mismas instrucciones, sin mirar e4_cifras.xlsx ni usar "
                 "herramientas de IA. Use el filtro de la hoja «contexto» para buscar.")
    wb.save(AUDITORIA)
    print(f"{AUDITORIA.relative_to(ROOT_DIR)}: {len(elegidas)} cifras ({POR_ESTRATO})")


def kappa(a: pd.Series, b: pd.Series) -> float:
    cats = sorted(set(a) | set(b))
    po = float((a == b).mean())
    pe = sum(float((a == c).mean()) * float((b == c).mean()) for c in cats)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def evaluar():
    a, b = leer(PRINCIPAL).set_index("id_cifra"), leer(AUDITORIA).set_index("id_cifra")
    b = b[b["es_cifra_de_mercado"].notna()]
    ids = b.index.intersection(a.index)
    a, b = a.loc[ids], b.loc[ids]
    resp = lambda d: d.apply(lambda r: r["respaldo"] if r["es_cifra_de_mercado"] == "Sí" else "(no mercado)", axis=1)
    ra, rb = resp(a), resp(b)
    resultado = {
        "n_auditadas": int(len(ids)),
        "es_cifra_de_mercado": {"acuerdo": round(float((a.es_cifra_de_mercado == b.es_cifra_de_mercado).mean()), 3),
                                "kappa": kappa(a.es_cifra_de_mercado, b.es_cifra_de_mercado)},
        "etiqueta_completa": {"acuerdo": round(float((ra == rb).mean()), 3), "kappa": kappa(ra, rb)},
        "desacuerdos": [{"id_cifra": i, "principal": ra[i], "auditoria": rb[i]} for i in ids if ra[i] != rb[i]],
    }
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    {"planilla": planilla, "evaluar": evaluar}[sys.argv[1] if len(sys.argv) > 1 else "planilla"]()
