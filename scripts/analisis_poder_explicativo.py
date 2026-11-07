"""
Poder explicativo de la taxonomía de habilidades sobre el salario ofrecido (solo lectura).

Método de Ao et al. (2023, Information Processing & Management): la proporción de la variación salarial
que explican las habilidades extraídas sirve como métrica para comparar métodos de extracción.

Con muestras pequeñas el R² dentro de la muestra se infla, así que se reporta **fuera de muestra**
(validación cruzada de 5 particiones, repetida) junto al R² dentro de muestra:
  A. controles: nivel + rol + portal + mes
  B. habilidades de la taxonomía (31 reglas)
  C. controles + habilidades  → aporte de las habilidades = C − A
  B_ridge, C_ridge: lo mismo con regresión ridge, para comparar en igualdad con el texto (D, E), que
  también usa ridge; OLS con ~20 indicadoras y ~140 ofertas de entrenamiento se sobreajusta
  D. todo el texto (TF-IDF de palabras, regresión ridge): referencia de lo que el texto puede explicar
  E. controles + texto

Mismos datos que el análisis de primas: ofertas locales con salario publicado, un registro por oferta.

Uso:  python scripts/analisis_poder_explicativo.py [--repeticiones 50] [--semilla 2026]
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.primas_salariales import CAMPOS_TEXTO, cargar_ofertas, preparar  # noqa: E402
from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

MIN_HABILIDAD = 5          # habilidades con al menos 5 ofertas (evita columnas casi vacías)
MIN_PALABRA = 5            # vocabulario TF-IDF: palabras en al menos 5 ofertas
LAMBDAS = [0.1, 1, 3, 10, 30, 100, 300]
# Con --sin-salario se excluyen del texto las palabras sobre remuneración: si la descripción menciona el
# salario («salario integral», «3 millones») o el auxilio de transporte (en Colombia, solo hasta 2 salarios
# mínimos), el modelo de texto estaría usando el salario para predecirse a sí mismo
PALABRAS_SALARIO = re.compile(r"^(salari|sueld|remunera|millon|mill[oó]n|mil$|pesos?$|cop$|usd$|integral|smmlv|smlv|"
                              r"devenga|bonifica|comisi|prestaci|pago|pagos|ingreso|ingresos|compensa|salary|wage|pay|auxilio|"
                              r"\$)")
SALIDA = ROOT_DIR / "data" / "analytics" / "poder_explicativo.json"


SIN_SALARIO = False


def tokens(texto: str):
    palabras = re.findall(r"[a-záéíóúñü][a-záéíóúñü+#.]{1,}", texto.lower())
    return [p for p in palabras if not PALABRAS_SALARIO.match(p)] if SIN_SALARIO else palabras


def tfidf(textos_train, textos_test):
    docs_train = [set(tokens(t)) for t in textos_train]
    df = Counter(p for d in docs_train for p in d)
    vocab = sorted(p for p, n in df.items() if n >= MIN_PALABRA)
    idx = {p: i for i, p in enumerate(vocab)}
    idf = np.log((1 + len(docs_train)) / (1 + np.array([df[p] for p in vocab]))) + 1

    def matriz(textos):
        X = np.zeros((len(textos), len(vocab)))
        for i, t in enumerate(textos):
            for p, n in Counter(tokens(t)).items():
                if p in idx:
                    X[i, idx[p]] = n
        X = np.log1p(X) * idf
        normas = np.linalg.norm(X, axis=1, keepdims=True)
        return X / np.where(normas == 0, 1, normas)

    return matriz(textos_train), matriz(textos_test)


def ajustar_ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return lambda Z: np.column_stack([np.ones(len(Z)), Z]) @ beta


def ajustar_ridge(X, y, lam):
    mx, my = X.mean(0), y.mean()
    Xc = X - mx
    beta = np.linalg.solve(Xc.T @ Xc + lam * np.eye(X.shape[1]), Xc.T @ (y - my))
    return lambda Z: (Z - mx) @ beta + my


def ridge_cv_interno(X, y, rng, k=5):
    """Elige lambda con validación cruzada interna sobre el entrenamiento."""
    pliegues = np.array_split(rng.permutation(len(y)), k)
    errores = []
    for lam in LAMBDAS:
        sse = 0.0
        for f in pliegues:
            tr = np.setdiff1d(np.arange(len(y)), f)
            sse += ((y[f] - ajustar_ridge(X[tr], y[tr], lam)(X[f])) ** 2).sum()
        errores.append(sse)
    return LAMBDAS[int(np.argmin(errores))]


def r2(y, pred, media_ref):
    return 1 - ((y - pred) ** 2).sum() / ((y - media_ref) ** 2).sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeticiones", type=int, default=50)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--sin-salario", action="store_true", help="excluir del texto las palabras sobre remuneración")
    args = ap.parse_args()
    global SIN_SALARIO
    SIN_SALARIO = args.sin_salario

    crudo = cargar_ofertas(create_engine(normalizar_url_bd(DATABASE_URL)))
    textos = crudo["payload_json"].apply(json.loads).apply(lambda d: " ".join(str(d.get(k) or "") for k in CAMPOS_TEXTO)).to_numpy()
    df = preparar(crudo).reset_index(drop=True)
    y = df["log_salario"].to_numpy()

    conteo = Counter(h for hs in df["habilidades"] for h in hs)
    habilidades = sorted(h for h, n in conteo.items() if n >= MIN_HABILIDAD)
    H = np.column_stack([df["habilidades"].apply(lambda hs, h=h: int(h in hs)) for h in habilidades]).astype(float)
    C = pd.get_dummies(df[["nivel", "rol", "portal", "mes"]], drop_first=True, dtype=float).to_numpy()

    # Dentro de la muestra (comparable con Ao et al., 2023)
    dentro = {
        "A_controles": r2(y, ajustar_ols(C, y)(C), y.mean()),
        "B_habilidades": r2(y, ajustar_ols(H, y)(H), y.mean()),
        "C_controles_mas_habilidades": r2(y, ajustar_ols(np.hstack([C, H]), y)(np.hstack([C, H])), y.mean()),
    }

    rng = np.random.default_rng(args.semilla)
    fuera = {k: [] for k in ("A_controles", "A_controles_ridge", "B_habilidades", "B_habilidades_ridge", "C_controles_mas_habilidades",
                             "C_controles_mas_habilidades_ridge", "D_texto_tfidf", "E_controles_mas_texto")}
    for _ in range(args.repeticiones):
        for f in np.array_split(rng.permutation(len(y)), 5):
            tr = np.setdiff1d(np.arange(len(y)), f)
            ref = y[tr].mean()
            for nombre, X in (("A_controles", C), ("B_habilidades", H), ("C_controles_mas_habilidades", np.hstack([C, H]))):
                fuera[nombre].append(r2(y[f], ajustar_ols(X[tr], y[tr])(X[f]), ref))
            for nombre, X in (("A_controles_ridge", C), ("B_habilidades_ridge", H), ("C_controles_mas_habilidades_ridge", np.hstack([C, H]))):
                lam = ridge_cv_interno(X[tr], y[tr], rng)
                fuera[nombre].append(r2(y[f], ajustar_ridge(X[tr], y[tr], lam)(X[f]), ref))
            T_tr, T_te = tfidf(textos[tr], textos[f])
            lam = ridge_cv_interno(T_tr, y[tr], rng)
            fuera["D_texto_tfidf"].append(r2(y[f], ajustar_ridge(T_tr, y[tr], lam)(T_te), ref))
            CT_tr, CT_te = np.hstack([C[tr], T_tr]), np.hstack([C[f], T_te])
            lam = ridge_cv_interno(CT_tr, y[tr], rng)
            fuera["E_controles_mas_texto"].append(r2(y[f], ajustar_ridge(CT_tr, y[tr], lam)(CT_te), ref))

    resumen = {k: {"media": round(float(np.mean(v)), 3), "p2_5": round(float(np.percentile(v, 2.5)), 3),
                   "p97_5": round(float(np.percentile(v, 97.5)), 3)} for k, v in fuera.items()}
    aporte = np.array(fuera["C_controles_mas_habilidades"]) - np.array(fuera["A_controles"])
    aporte_ridge = np.array(fuera["C_controles_mas_habilidades_ridge"]) - np.array(fuera["A_controles_ridge"])
    resultado = {
        "n_ofertas": int(len(y)), "habilidades_en_modelo": len(habilidades), "columnas_controles": int(C.shape[1]),
        "r2_dentro_de_muestra": {k: round(float(v), 3) for k, v in dentro.items()},
        "r2_fuera_de_muestra": resumen,
        "aporte_habilidades_fuera_de_muestra": {"media": round(float(aporte.mean()), 3),
                                                 "p2_5": round(float(np.percentile(aporte, 2.5)), 3),
                                                 "p97_5": round(float(np.percentile(aporte, 97.5)), 3)},
        "aporte_habilidades_fuera_de_muestra_ridge": {"media": round(float(aporte_ridge.mean()), 3),
                                                       "p2_5": round(float(np.percentile(aporte_ridge, 2.5)), 3),
                                                       "p97_5": round(float(np.percentile(aporte_ridge, 97.5)), 3)},
        "texto_sin_palabras_de_salario": SIN_SALARIO,
        "validacion": f"5 particiones x {args.repeticiones} repeticiones, semilla {args.semilla}",
        "lectura": "R² fuera de muestra: proporción de la variación del log del salario que el modelo predice en ofertas no usadas para estimarlo.",
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    salida = SALIDA.with_name("poder_explicativo_sin_salario.json") if SIN_SALARIO else SALIDA
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
