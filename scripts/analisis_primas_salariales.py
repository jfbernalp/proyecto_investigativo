"""
Ejecuta el análisis de primas salariales (src/analytics/primas_salariales.py) sobre la base activa
(solo lectura) y guarda el resultado en data/analytics/primas_salariales.json.

Uso:  python scripts/analisis_primas_salariales.py [--guardar-bd]
      --guardar-bd escribe el resultado del corte en analisis_primas_habilidad / analisis_primas_rol
"""
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.primas_salariales import (  # noqa: E402
    MIN_OFERTAS, Q_MAX, cargar_ofertas, describir_muestra, estimar, estimar_roles, preparar, robustez_por_portal,
)
from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

SALIDA = ROOT_DIR / "data" / "analytics" / "primas_salariales.json"


def guardar_en_bd(engine, resultado):
    """Reemplaza las filas del mismo corte (una transacción); los cortes anteriores se conservan."""
    corte, mercado = resultado["ultimo_corte"], resultado["mercado"]
    comunes = {"ultimo_corte": corte, "fecha_analisis": resultado["fecha_analisis"], "mercado": mercado}
    habilidades = [{**comunes, "habilidad": f["habilidad"], "n_muestra": resultado["n_ofertas"],
                    "n_ofertas": f["n_ofertas_con_habilidad"], "evaluable": True, "r2_modelo": resultado.get("r2"),
                    **{k: f[k] for k in ("prima_pct", "ic95_inferior_pct", "ic95_superior_pct", "p", "q_bh", "concluyente")}}
                   for f in resultado["filas"]]
    roles = resultado["roles"]
    filas_rol = [{**comunes, "rol": f["rol"], "rol_referencia": roles["referencia"], "n_muestra": roles["n_ofertas"],
                  "n_ofertas": f["n_ofertas"], "evaluable": True, "r2_modelo": roles.get("r2"),
                  **{k: f[k] for k in ("prima_pct", "ic95_inferior_pct", "ic95_superior_pct", "p", "q_bh", "concluyente")}}
                 for f in roles["filas"]]
    filas_rol += [{**comunes, "rol": r, "rol_referencia": roles["referencia"], "n_muestra": roles["n_ofertas"],
                   "n_ofertas": n, "evaluable": False} for r, n in roles["no_evaluables"].items()]
    # La referencia también se publica (prima 0 por definición) para que la tabla muestre su n
    n_ref = resultado["muestra"]["por_rol"].get(roles["referencia"])
    filas_rol.append({**comunes, "rol": roles["referencia"], "rol_referencia": roles["referencia"],
                      "n_muestra": roles["n_ofertas"], "n_ofertas": n_ref, "evaluable": True, "prima_pct": 0})
    with engine.begin() as conn:
        for tabla, filas in (("analisis_primas_habilidad", habilidades), ("analisis_primas_rol", filas_rol)):
            conn.execute(text(f"DELETE FROM {tabla} WHERE ultimo_corte = :c AND mercado = :m"), {"c": corte, "m": mercado})
            if filas:
                columnas = sorted({k for f in filas for k in f})
                conn.execute(text(f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join(':' + c for c in columnas)})"),
                             [{c: f.get(c) for c in columnas} for f in filas])
    print(f"[BD] {len(habilidades)} habilidades y {len(filas_rol)} roles guardados para el corte {corte}")


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    with engine.connect() as c:
        corte = c.execute(text("SELECT MAX(fecha_extraccion) FROM fact_extracciones_historico")).scalar()
    df = preparar(cargar_ofertas(engine))
    resultado = estimar(df)
    resultado["muestra"] = describir_muestra(df)
    resultado["robustez_sin_cada_portal"] = robustez_por_portal(df, resultado["habilidades_evaluadas"])
    resultado["roles"] = estimar_roles(df)
    resultado.update({"fecha_analisis": date.today().isoformat(), "ultimo_corte": str(corte),
                      "mercado": "Local (Colombia, COP)",
                      "modelo": "OLS log(salario) ~ habilidades + nivel + rol + portal + mes; errores HC3",
                      "lectura": "Asociación condicionada en ofertas publicadas con salario; no es un efecto causal."})

    m = resultado["muestra"]
    print(f"Muestra: {resultado['n_ofertas']} ofertas locales con salario · corte {corte}")
    print(f"  portales: {m['por_portal']} · meses: {m['por_mes']}")
    print(f"  nivel: {m['por_nivel']} · fuente: {m['fuente_nivel']}")
    print(f"  rol: {m['por_rol']}")
    if not resultado["filas"]:
        print(resultado.get("conclusion"))
    else:
        print(f"\nModelo: {resultado['parametros']} parámetros · R² {resultado['r2']} (ajustado {resultado['r2_ajustado']})")
        print(f"Habilidades con n ≥ {MIN_OFERTAS}: {len(resultado['habilidades_evaluadas'])}\n")
        print(f"{'Habilidad':<28}{'n':>5}{'prima':>9}{'IC 95 %':>20}{'q (BH)':>9}  concluyente")
        for f in resultado["filas"]:
            ic = f"[{f['ic95_inferior_pct']:+.1f}, {f['ic95_superior_pct']:+.1f}]"
            print(f"{f['habilidad']:<28}{f['n_ofertas_con_habilidad']:>5}{f['prima_pct']:>+8.1f}%{ic:>20}"
                  f"{f['q_bh']:>9.3f}  {'sí' if f['concluyente'] else 'no'}")
        print(f"\nConcluyente = q ≤ {Q_MAX} y el intervalo no cruza 0.")
        print("\nRobustez (prima % sin cada portal):")
        for nombre, r in resultado["robustez_sin_cada_portal"].items():
            print(f"  {nombre:<20} n={r['n_ofertas']:<4}", {k: v for k, v in r["primas"].items()})
    roles = resultado["roles"]
    print(f"\nPrima por rol frente a «{roles['referencia']}» (controla nivel, portal y mes):")
    for f in roles["filas"]:
        ic = f"[{f['ic95_inferior_pct']:+.1f}, {f['ic95_superior_pct']:+.1f}]"
        print(f"  {f['rol']:<38}{f['n_ofertas']:>5}{f['prima_pct']:>+8.1f}%{ic:>20}{f['q_bh']:>9.3f}  {'sí' if f['concluyente'] else 'no'}")
    print(f"  No evaluables (n < {roles['min_ofertas_por_rol']}): {roles['no_evaluables']}")
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado en {SALIDA.relative_to(ROOT_DIR)}")
    if "--guardar-bd" in sys.argv:
        guardar_en_bd(engine, resultado)


if __name__ == "__main__":
    main()
