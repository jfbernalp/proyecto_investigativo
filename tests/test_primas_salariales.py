"""El método recupera un efecto conocido y no inventa conclusiones con muestras pequeñas."""
import numpy as np
import pandas as pd

from src.analytics.primas_salariales import estimar


def _datos(n=200, efecto_spark=0.30, semilla=0):
    rng = np.random.default_rng(semilla)
    filas = []
    for i in range(n):
        habilidades = [h for h, p in (("Spark", 0.35), ("SQL", 0.6), ("Excel", 0.3)) if rng.random() < p]
        nivel = rng.choice(["Junior", "Semi-Senior", "Senior"])
        base = {"Junior": 14.8, "Semi-Senior": 15.2, "Senior": 15.6}[nivel]
        log_salario = base + (efecto_spark if "Spark" in habilidades else 0) + rng.normal(0, 0.15)
        filas.append({"habilidades": habilidades, "nivel": nivel, "rol": rng.choice(["A", "B"]),
                      "portal": rng.choice(["P1", "P2"]), "mes": "202610", "log_salario": log_salario})
    return pd.DataFrame(filas)


def test_recupera_efecto_conocido():
    r = estimar(_datos(), min_ofertas=20)
    spark = next(f for f in r["filas"] if f["habilidad"] == "Spark")
    # exp(0.30) − 1 ≈ 35 %; el intervalo debe contenerlo y ser concluyente
    assert spark["ic95_inferior_pct"] < 35 < spark["ic95_superior_pct"]
    assert spark["concluyente"]
    # Sin efecto real: estimación cercana a 0. (Un IC del 95 % puede excluir 0 por azar; para eso está q.)
    sin_efecto = [f for f in r["filas"] if f["habilidad"] in ("SQL", "Excel")]
    assert all(abs(f["prima_pct"]) < 10 for f in sin_efecto)


def test_respeta_minimo_de_ofertas():
    r = estimar(_datos(), min_ofertas=500)
    assert r["filas"] == [] and "No concluyente" in r["conclusion"]


def test_muestra_pequena_no_concluye():
    r = estimar(_datos(n=20), min_ofertas=5)
    assert r["filas"] == [] and "No concluyente" in r["conclusion"]
