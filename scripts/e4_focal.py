"""
Inspección focal de E4 (hito 72): la franja «no revisada» (números que los patrones del verificador no reconocen) solo
aportó 4 cifras de mercado a la muestra de 40, y la exhaustividad quedaba con un IC muy ancho. Se subestratifica esa
franja con una pista textual de mercado alrededor del número (n =, ofertas, salario, COP, %, prima, …) y se etiqueta a
ciegas una muestra adicional de la subfranja «con pista», donde se concentran las cifras de mercado.

    python scripts/e4_focal.py planilla   → data/evaluacion_ia/e4_focal.xlsx (no sobrescribe)
    python scripts/e4_focal.py evaluar    → exhaustividad con IC (Jeffreys, Monte Carlo) por estratos y subestratos

Estimación: las 40 cifras no revisadas de la muestra original se posestratifican por la misma pista y se suman a la
muestra focal en la subfranja «con pista». Para cada subestrato se simula la proporción de cifras de mercado y la de
problemas (sin respaldo o mal atribuida) entre ellas con posteriores Beta de Jeffreys; exhaustividad = problemas
marcados / (marcados + problemas estimados sin marca).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import evaluacion_ia as ev  # noqa: E402

CARPETA = ev.CARPETA
FOCAL = CARPETA / "e4_focal.xlsx"
CLAVE_FOCAL = CARPETA / "e4_focal_clave.csv"
SALIDA = CARPETA / "e4_focal_resultados.json"
ADJUDICACION = CARPETA / "e4_focal_adjudicacion.csv"
N_FOCAL = 60
SEMILLA = 2027
CONTEXTO = "c0d2415dbc12"     # los dos contextos de E5 tienen las mismas cifras (solo cambian id y fecha)
PISTA = re.compile(r"(\bn\s*[=_:]|n_con_salario|ofertas?|vacantes?|avisos?|salari|sueldo|prima|mediana|COP|USD|%|"
                   r"millones|corte|demanda|IC\s*95)", re.I)
PROBLEMA = {"Sin respaldo", "Mal atribuida"}


def con_pista(cifra: str, fragmento: str) -> bool:
    """Pista de mercado en ±30 caracteres alrededor de la aparición del número más cercana al centro del fragmento."""
    centro = len(fragmento) // 2
    pos = [m.start() for m in re.finditer(re.escape(str(cifra)), fragmento)] or [centro]
    i = min(pos, key=lambda p: abs(p - centro))
    return bool(PISTA.search(fragmento[max(0, i - 30): i + len(str(cifra)) + 25]))


def poblacion() -> pd.DataFrame:
    filas, contextos = [], {}
    for pid, p in ev.propuestas_e5().items():
        ctx = contextos.setdefault(p.contexto_id, ev.cargar_contexto(p.contexto_id))
        filas += ev.cifras_de_propuesta(pid, p, ev._verificar(p, ctx))
    df = pd.DataFrame(filas)
    df["pista"] = [con_pista(c, f) for c, f in zip(df.cifra, df.fragmento)]
    return df


def leer(ruta: Path) -> pd.DataFrame:
    filas = list(load_workbook(ruta, data_only=True)["cifras"].iter_rows(values_only=True))
    return pd.DataFrame(filas[1:], columns=filas[0]).dropna(subset=["id_cifra"])


def planilla():
    if FOCAL.exists():
        sys.exit(f"{FOCAL.name} ya existe: no se sobrescribe.")
    df = poblacion()
    clave = pd.read_csv(CARPETA / "e4_clave.csv")
    ya = set(zip(clave.propuesta, clave.campo, clave.cifra.astype(str)))
    candidatas = df[(df.estrato == "no revisada") & df.pista]
    candidatas = candidatas[[(p, c, str(x)) not in ya for p, c, x in zip(candidatas.propuesta, candidatas.campo, candidatas.cifra)]]
    muestra = candidatas.sample(n=min(N_FOCAL, len(candidatas)), random_state=SEMILLA).reset_index(drop=True)
    muestra["id_cifra"] = [f"F{i + 1:03d}" for i in range(len(muestra))]
    codigos = clave.drop_duplicates("propuesta").set_index("propuesta")["codigo"].to_dict()
    muestra["codigo"] = muestra["propuesta"].map(codigos).fillna("P??")

    wb = load_workbook(CARPETA / "e4_auditoria.xlsx")      # misma estructura, validaciones y hoja «contexto»
    ws = wb["cifras"]
    ws.delete_rows(2, ws.max_row)
    for _, r in muestra.iterrows():
        ws.append([r.id_cifra, r.codigo, r.campo, r.cifra, r.fragmento, None, None, None])
    ws.auto_filter.ref = f"A1:H{ws.max_row}"
    ws.data_validations.dataValidation = []
    for col, opciones in (("F", ev.ES_MERCADO), ("G", ev.RESPALDO)):
        dv = DataValidation(type="list", formula1='"' + ",".join(opciones) + '"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{ws.max_row}")
    wb["instrucciones"]["A1"] = ("INSPECCIÓN FOCAL: mismas instrucciones. Sin mirar e4_cifras.xlsx ni usar herramientas "
                                 "de IA. Use el filtro de la hoja «contexto» para buscar.")
    wb.save(FOCAL)
    muestra[["id_cifra", "codigo", "propuesta", "campo", "cifra", "estrato", "pista"]].to_csv(CLAVE_FOCAL, index=False)
    print(f"{FOCAL.relative_to(ROOT_DIR)}: {len(muestra)} cifras de la subfranja no revisada con pista "
          f"(población {len(df[(df.estrato == 'no revisada') & df.pista])} con pista, "
          f"{len(df[(df.estrato == 'no revisada') & ~df.pista])} sin pista)")


def evaluar(sims: int = 200_000):
    df = poblacion()
    pob = {"marcada": int((df.estrato == "marcada").sum()), "revisada": int((df.estrato == "revisada").sum()),
           "no revisada con pista": int(((df.estrato == "no revisada") & df.pista).sum()),
           "no revisada sin pista": int(((df.estrato == "no revisada") & ~df.pista).sum())}

    clave = pd.read_csv(CARPETA / "e4_clave.csv").set_index("id_cifra")
    princ = leer(CARPETA / "e4_cifras.xlsx").set_index("id_cifra")
    orig = clave.join(princ[["fragmento", "es_cifra_de_mercado", "respaldo"]])
    orig["sub"] = orig["estrato"]
    nr = orig.estrato == "no revisada"
    orig.loc[nr, "sub"] = ["no revisada con pista" if con_pista(c, f) else "no revisada sin pista"
                           for c, f in zip(orig.loc[nr, "cifra"].astype(str), orig.loc[nr, "fragmento"])]
    foc = leer(FOCAL)
    foc = foc[foc.es_cifra_de_mercado.notna()].set_index("id_cifra")
    sin_adjudicar = foc.copy()
    if ADJUDICACION.exists():                      # desacuerdos con la guía, revisados contra el contexto
        adj = pd.read_csv(ADJUDICACION, dtype=str).set_index("id_cifra")
        foc.loc[adj.index, ["es_cifra_de_mercado", "respaldo"]] = adj[["es_cifra_de_mercado", "respaldo"]].values
    foc["sub"] = "no revisada con pista"
    m = pd.concat([orig[["sub", "es_cifra_de_mercado", "respaldo"]], foc[["sub", "es_cifra_de_mercado", "respaldo"]]])
    m["mercado"] = m.es_cifra_de_mercado == "Sí"
    m["problema"] = m.mercado & m.respaldo.isin(PROBLEMA)

    resumen = {s: {"poblacion": pob[s], "etiquetadas": int((m["sub"] == s).sum()), "de_mercado": int(m[m["sub"] == s].mercado.sum()),
                   "problemas": int(m[m["sub"] == s].problema.sum())} for s in pob}
    tp = resumen["marcada"]["problemas"]
    rng = np.random.default_rng(2026)
    fn, merc = {}, {}
    for s in ("revisada", "no revisada con pista", "no revisada sin pista"):
        r = resumen[s]
        merc[s] = r["poblacion"] * rng.beta(r["de_mercado"] + .5, r["etiquetadas"] - r["de_mercado"] + .5, sims)
        fn[s] = merc[s] * rng.beta(r["problemas"] + .5, r["de_mercado"] - r["problemas"] + .5, sims)
    m_marc = resumen["marcada"]["de_mercado"]
    total_merc = m_marc + sum(merc.values())
    cobertura = (m_marc + merc["revisada"]) / total_merc
    respaldadas = 1 - (tp + sum(fn.values())) / total_merc
    total_fn = sum(fn.values())
    recall = tp / (tp + total_fn)
    recall_rev = tp / (tp + fn["revisada"])
    q = lambda x: [round(float(v), 3) for v in np.percentile(x, [2.5, 50, 97.5])]
    res = {"inspeccion_focal": {"etiquetadas": int(len(foc)),
                                "problemas_sin_adjudicar": int((sin_adjudicar.es_cifra_de_mercado.eq("Sí") & sin_adjudicar.respaldo.isin(PROBLEMA)).sum()),
                                "adjudicadas": int(len(pd.read_csv(ADJUDICACION))) if ADJUDICACION.exists() else 0},
           "estratos": resumen, "problemas_marcados": tp,
           "exhaustividad_total": {"puntual_muestral": 1.0 if all(resumen[s]["problemas"] == 0 for s in fn) else None,
                                   "mediana_e_ic95": q(recall), "cota_inferior_95_una_cola": round(float(np.percentile(recall, 5)), 3)},
           "exhaustividad_entre_revisadas": {"mediana_e_ic95": q(recall_rev)},
           "cobertura_mediana_e_ic95": q(cobertura), "pct_mercado_respaldadas_mediana_e_ic95": q(100 * respaldadas),
           "cifras_de_mercado_estimadas": q(total_merc),
           "falsos_negativos_esperados": {s: q(v) for s, v in fn.items()},
           "metodo": "Posteriores Beta de Jeffreys por subestrato para P(mercado) y P(problema | mercado); Monte Carlo "
                     f"{sims}; la franja no revisada se posestratifica por pista textual de mercado."}
    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    {"planilla": planilla, "evaluar": evaluar}[sys.argv[1] if len(sys.argv) > 1 else "planilla"]()
