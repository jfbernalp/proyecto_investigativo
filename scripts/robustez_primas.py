"""
Robustez de las primas salariales (Artículo 1, mejoras M2, M3 y M6 del hito 56). Solo lectura.

- M2 · Salario como intervalo (Zhong et al., 2023): ElEmpleo publica rangos («$3,5 a $4 millones») y el modelo usa
  el punto medio. Se re-estima con el extremo inferior y con el superior; si la conclusión cambia, depende del supuesto.
- M3 · Nivel educativo y sector como controles (lo que el texto explica y la taxonomía no, hito 53). Ambos se extraen
  del texto con palabras clave: son exploratorios.
- M6 · Duplicados entre portales (#118): la huella del sistema es portal + código, así que el mismo aviso en dos
  portales cuenta dos veces. Se mide la tasa de casi duplicados en todas las ofertas únicas y se re-estima sin ellos.

Salida agregada en data/analytics/robustez_primas.json (sin texto de ofertas).
Uso:  python scripts/robustez_primas.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.primas_salariales import (MARGEN_EQUIVALENCIA_PCT, cargar_ofertas, estimar,  # noqa: E402
                                             estimar_roles, preparar)
from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

SALIDA = ROOT_DIR / "data" / "analytics" / "robustez_primas.json"
UMBRAL_COSENO = 0.9

# Nivel educativo más alto mencionado. Orden: de mayor a menor
NIVELES_EDUCATIVOS = [
    ("Posgrado (maestría o doctorado)", r"\bdoctorado\b|\bphd\b|\bmaestria\b|\bmagister\b|\bmasters?(?: s)? degree\b|\bmsc\b"),
    ("Especialización", r"\bespecializacion\b|\bposgrado\b|\bpostgrado\b"),
    ("Profesional", r"\bprofesional(?:es)?\b|\bpregrado\b|\buniversitari[oa]\b|\btitulo (?:universitario|profesional)\b"
                    r"|\bbachelor s?\b|\bingenier[oa]s? (?:de|en)\b|\bcarrera profesional\b"),
    ("Técnico o tecnólogo", r"\btecnolog[oa]\b|\btecnico\b|\btecnica\b"),
]
SECTORES = {
    "Salud": r"\bsalud\b|\bclinica\b|\bhospital\w*\b|\bfarmac\w*\b|\beps\b|\bips\b|\bmedic[oa]s?\b",
    "Financiero y seguros": r"\bbanc[oa]\w*\b|\bfinancier[oa]s?\b|\bseguros?\b|\baseguradora\b|\bfintech\b|\bcredito\b",
    # no «educación» ni «universidad»: aparecen en los requisitos («Educación: profesional en…»)
    "Educación": r"\bdocentes?\b|\bcolegios?\b|\binstitucion educativa\b|\bedtech\b",
    "Sector público": r"\bministerio\b|\balcaldia\b|\bgobernacion\b|\bentidad publica\b|\bsector publico\b",
    "Comercio y consumo": r"\bretail\b|\bconsumo masivo\b|\bsupermercado\w*\b|\be ?commerce\b",
}


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in t if not unicodedata.combining(c))).strip()


def nivel_educativo(texto: str) -> str:
    t = normalizar(texto)
    for nivel, patron in NIVELES_EDUCATIVOS:
        if re.search(patron, t):
            return nivel
    return "No se indica"


def sector(texto: str) -> str:
    """Sector con más menciones; «No identificado» si ninguno."""
    t = normalizar(texto)
    conteo = {s: len(re.findall(p, t)) for s, p in SECTORES.items()}
    mejor = max(conteo, key=conteo.get)
    return mejor if conteo[mejor] else "No identificado"


def rango_salario(valor: str):
    """(mínimo, máximo) en COP para rangos de ElEmpleo en millones; None si no es un rango cerrado."""
    v = str(valor).lower()
    if "mill" not in v or "más de" in v or "mas de" in v:
        return None
    nums = [float(n.replace(",", ".")) * 1_000_000 for n in re.findall(r"(\d+(?:[.,]\d+)?)", v)]
    return (min(nums), max(nums)) if len(nums) >= 2 else None


def _tfidf(textos):
    """Matriz TF-IDF normalizada (sin sklearn, que no está instalado)."""
    docs = [normalizar(t).split() for t in textos]
    vocab = {w: i for i, w in enumerate(sorted({w for d in docs for w in d}))}
    M = np.zeros((len(docs), len(vocab)))
    for i, d in enumerate(docs):
        for w in d:
            M[i, vocab[w]] += 1
    M *= np.log((1 + len(docs)) / (1 + (M > 0).sum(0))) + 1
    return M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-12)


def duplicados_entre_portales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pares de ofertas de portales DISTINTOS que son el mismo aviso: mismo título y empresa normalizados, o texto con
    coseno TF-IDF ≥ UMBRAL_COSENO. Devuelve los pares (sin texto).
    """
    clave = df["titulo"].map(normalizar) + "|" + df["empresa"].map(normalizar)
    sim = _tfidf((df["titulo"] + " " + df["texto"]).tolist())
    S = sim @ sim.T
    portal = df["portal"].to_numpy()
    pares = []
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if portal[i] == portal[j]:
                continue
            mismo = clave.iat[i] == clave.iat[j] and not clave.iat[i].endswith("|confidencial")
            if mismo or S[i, j] >= UMBRAL_COSENO:
                pares.append({"a": df.index[i], "b": df.index[j], "portal_a": portal[i], "portal_b": portal[j],
                              "criterio": "titulo+empresa" if mismo else "texto", "coseno": round(float(S[i, j]), 3)})
    return pd.DataFrame(pares)


def _resumen(r: dict, habilidades=None) -> dict:
    filas = [f for f in r.get("filas", []) if habilidades is None or f["habilidad"] in habilidades]
    return {"n_ofertas": r["n_ofertas"], "r2": r.get("r2"),
            "primas": {f["habilidad"]: {k: f[k] for k in ("prima_pct", "ic95_inferior_pct", "ic95_superior_pct",
                                                          "q_bh", "concluyente", "ic90_inferior_pct",
                                                          "ic90_superior_pct", "p_tost", "q_tost_bh", "equivalente",
                                                          "margen_minimo_equivalencia_pct")} for f in filas}}


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    crudo = cargar_ofertas(engine)
    cargas = crudo["payload_json"].apply(json.loads)
    df = preparar(crudo)
    textos = cargas.apply(lambda d: " ".join(str(d.get(k) or "") for k in ("Nombre Oferta", "Requisitos", "Descripcion",
                                                                          "Descripcion_detalle", "Empresa")))
    df["educacion"] = textos.apply(nivel_educativo).values
    df["sector"] = textos.apply(sector).values
    rangos = cargas.apply(lambda d: rango_salario(d.get("Salario")))
    df["log_salario_min"] = np.log([r[0] if r else s for r, s in zip(rangos, df["salario_cop_mensual"].astype(float))])
    df["log_salario_max"] = np.log([r[1] if r else s for r, s in zip(rangos, df["salario_cop_mensual"].astype(float))])

    res = {"corte": "sep–nov 2026, ofertas locales con salario", "n_ofertas": int(len(df)),
           "base": _resumen(estimar(df)), "roles": estimar_roles(df)}

    # M2
    res["M2_intervalo"] = {
        "n_con_rango": int(rangos.notna().sum()),
        "extremo_inferior": _resumen(estimar(df, y="log_salario_min")),
        "extremo_superior": _resumen(estimar(df, y="log_salario_max")),
    }
    # M3
    res["M3_controles"] = {
        "distribucion_educacion": df["educacion"].value_counts().to_dict(),
        "distribucion_sector": df["sector"].value_counts().to_dict(),
        "con_educacion": _resumen(estimar(df, controles_extra=("educacion",))),
        "con_educacion_y_sector": _resumen(estimar(df, controles_extra=("educacion", "sector"))),
    }
    # M6, sobre todas las ofertas únicas (no solo las que tienen salario)
    todas = pd.read_sql_query(text("""
        SELECT DISTINCT ON (r.id_vacante_hash) r.id_vacante_hash, d.portal, r.payload_json
        FROM ofertas_raw_historico r JOIN dim_ofertas d USING (id_vacante_hash)
        ORDER BY r.id_vacante_hash, r.mes_periodo DESC"""), engine).set_index("id_vacante_hash")
    c = todas.pop("payload_json").apply(json.loads)
    todas["titulo"] = c.apply(lambda d: str(d.get("Nombre Oferta") or ""))
    todas["empresa"] = c.apply(lambda d: str(d.get("Empresa") or ""))
    todas["texto"] = c.apply(lambda d: " ".join(str(d.get(k) or "") for k in ("Requisitos", "Descripcion")))
    pares = duplicados_entre_portales(todas)
    en_pares = set(pares["a"]) | set(pares["b"]) if len(pares) else set()
    # de cada par se conserva una oferta: se descartan las «b»
    sobrantes = set(pares["b"]) if len(pares) else set()
    sin_dup = df[~df["id_vacante_hash"].isin(sobrantes)]
    res["M6_duplicados"] = {
        "n_ofertas_unicas": int(len(todas)), "umbral_coseno": UMBRAL_COSENO,
        "pares_entre_portales": int(len(pares)),
        "ofertas_involucradas": len(en_pares), "ofertas_sobrantes": len(sobrantes),
        "pct_sobrantes": round(100 * len(sobrantes) / len(todas), 1),
        "por_criterio": pares["criterio"].value_counts().to_dict() if len(pares) else {},
        "por_par_de_portales": pares.apply(lambda f: " / ".join(sorted((f.portal_a, f.portal_b))), axis=1).value_counts().to_dict() if len(pares) else {},
        "con_salario_descartadas": int(len(df) - len(sin_dup)),
        "sin_duplicados": _resumen(estimar(sin_dup)),
    }
    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def linea(nombre, r):
        p = r["primas"]
        conc = [f"{h} {v['prima_pct']:+.1f}% [{v['ic95_inferior_pct']:+.1f}; {v['ic95_superior_pct']:+.1f}]"
                for h, v in p.items() if v["concluyente"]]
        ex = p.get("Excel Avanzado")
        print(f"{nombre:28} n={r['n_ofertas']:3} R²={r['r2']}  Excel {ex['prima_pct']:+.1f}% "
              f"[{ex['ic95_inferior_pct']:+.1f}; {ex['ic95_superior_pct']:+.1f}] q={ex['q_bh']}  concluyentes: {conc or 'ninguna'}")
    linea("base (roles nuevos)", res["base"])
    linea("M2 extremo inferior", res["M2_intervalo"]["extremo_inferior"])
    linea("M2 extremo superior", res["M2_intervalo"]["extremo_superior"])
    linea("M3 + educación", res["M3_controles"]["con_educacion"])
    linea("M3 + educación + sector", res["M3_controles"]["con_educacion_y_sector"])
    linea("M6 sin duplicados", res["M6_duplicados"]["sin_duplicados"])
    print(f"Equivalencia (TOST, margen ±{MARGEN_EQUIVALENCIA_PCT:.0f} %, base):")
    for h, v in res["base"]["primas"].items():
        print(f"  {h:28} IC90 [{v['ic90_inferior_pct']:+.1f}; {v['ic90_superior_pct']:+.1f}]  p_TOST={v['p_tost']:.3f}"
              f"  q={v['q_tost_bh']:.3f}  margen mínimo ±{v['margen_minimo_equivalencia_pct']:.1f} %"
              f"  {'SIN PRIMA RELEVANTE' if v['equivalente'] else ''}")
    print("rangos:", res["M2_intervalo"]["n_con_rango"], "| educación:", res["M3_controles"]["distribucion_educacion"])
    print("sector:", res["M3_controles"]["distribucion_sector"])
    print("duplicados:", {k: v for k, v in res["M6_duplicados"].items() if k != "sin_duplicados"})
    print(f"Guardado en {SALIDA.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
