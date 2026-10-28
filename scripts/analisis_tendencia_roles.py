"""
Roles emergentes y en descenso del último corte (src/analytics/tendencia_roles.py), solo lectura salvo
--guardar-bd, que escribe el resultado en analisis_tendencia_roles (reemplaza las filas de ese mes).

Uso:  python scripts/analisis_tendencia_roles.py [--guardar-bd]
"""
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.tendencia_roles import cargar_roles, comparar_meses  # noqa: E402
from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402


def guardar_en_bd(engine, r):
    comunes = {"mes_periodo": r["mes"], "mes_anterior": r["mes_anterior"], "fecha_analisis": date.today().isoformat(),
               "portales_comparados": ", ".join(r["portales_comparados"]),
               "portales_excluidos": ", ".join(r["portales_excluidos_por_cambio_de_busqueda"]) or "ninguno",
               "n_total": r["n_ofertas"], "n_total_anterior": r["n_ofertas_anterior"],
               "cortes_disponibles": r["cortes_disponibles"], "es_tendencia": r["es_tendencia"]}
    filas = [{**comunes, **{k: f[k] for k in ("rol", "n_ofertas", "pct", "n_ofertas_anterior", "pct_anterior",
                                              "cambio_pp", "p", "q_bh", "estado")}} for f in r["filas"]]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM analisis_tendencia_roles WHERE mes_periodo = :m"), {"m": r["mes"]})
        if filas:
            columnas = list(filas[0])
            conn.execute(text(f"INSERT INTO analisis_tendencia_roles ({', '.join(columnas)}) "
                              f"VALUES ({', '.join(':' + c for c in columnas)})"), filas)
    print(f"[BD] {len(filas)} roles guardados para {r['mes']}")


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    df = cargar_roles(engine)
    r = comparar_meses(df, int(df["mes_periodo"].max()))
    if not r["filas"]:
        print(r["conclusion"])
        return
    print(f"{r['mes']} vs {r['mes_anterior']} · portales comparados: {r['portales_comparados']} "
          f"(excluidos por cambio de búsqueda: {r['portales_excluidos_por_cambio_de_busqueda'] or 'ninguno'})")
    print(f"n = {r['n_ofertas']} vs {r['n_ofertas_anterior']} ofertas · {r['lectura']}\n")
    print(f"{'Rol':<40}{'antes':>14}{'ahora':>14}{'cambio':>9}{'q':>8}  estado")
    for f in r["filas"]:
        q = "—" if f["q_bh"] is None else f"{f['q_bh']:.3f}"
        print(f"{f['rol']:<40}{f['n_ofertas_anterior']:>5} ({f['pct_anterior']:>4.1f}%){f['n_ofertas']:>5} ({f['pct']:>4.1f}%)"
              f"{f['cambio_pp']:>+8.1f}{q:>8}  {f['estado']}")
    if "--guardar-bd" in sys.argv:
        guardar_en_bd(engine, r)


if __name__ == "__main__":
    main()
