"""
Ejecuta el análisis de primas salariales (src/analytics/primas_salariales.py) sobre la base activa
(solo lectura) y guarda el resultado en data/analytics/primas_salariales.json.

Uso:  python scripts/analisis_primas_salariales.py
"""
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.primas_salariales import (  # noqa: E402
    MIN_OFERTAS, Q_MAX, cargar_ofertas, describir_muestra, estimar, preparar, robustez_por_portal,
)
from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

SALIDA = ROOT_DIR / "data" / "analytics" / "primas_salariales.json"


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    with engine.connect() as c:
        corte = c.execute(text("SELECT MAX(fecha_extraccion) FROM fact_extracciones_historico")).scalar()
    df = preparar(cargar_ofertas(engine))
    resultado = estimar(df)
    resultado["muestra"] = describir_muestra(df)
    resultado["robustez_sin_cada_portal"] = robustez_por_portal(df, resultado["habilidades_evaluadas"])
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
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado en {SALIDA.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
