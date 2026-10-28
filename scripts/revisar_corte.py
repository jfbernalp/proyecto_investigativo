"""
Revisión posterior a un corte mensual (solo lectura). Compara el último mes con el anterior y
señala lo que requiere atención. No inventa umbrales de "normalidad": muestra las cifras y marca
solo condiciones objetivas (portal en cero, duplicados, ofertas sin texto, sitio caído).

Uso:  python scripts/revisar_corte.py
"""
import sys
from pathlib import Path

import requests
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402

URLS = {
    "Landing": "https://jfbernalp.dev/",
    "KPIs públicos": "https://jfbernalp.dev/api/kpis",
    "Tablero Superset (público)": "https://superset.jfbernalp.dev/superset/dashboard/1/?standalone=2",
}
alertas = []


def main():
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    with engine.connect() as c:
        q = lambda sql, **p: c.execute(text(sql), p).fetchall()
        meses = [r[0] for r in q("SELECT DISTINCT mes_periodo FROM fact_extracciones_historico ORDER BY 1 DESC LIMIT 2")]
        if not meses:
            print("No hay cortes registrados.")
            return 1
        actual, previo = meses[0], (meses[1] if len(meses) > 1 else None)
        fecha = q("SELECT MAX(fecha_extraccion) FROM fact_extracciones_historico WHERE mes_periodo = :m", m=actual)[0][0]
        print(f"Último corte: {actual} (última extracción {fecha}) · mes anterior: {previo or 'no hay'}\n")

        print(f"{'Portal':<14}{'ofertas':>9}{'mes ant.':>10}{'con salario':>13}{'hab./oferta':>13}{'con texto':>11}")
        filas = q("""
            WITH act AS (
                SELECT d.portal, COUNT(*) n, COUNT(*) FILTER (WHERE e.salario_cop_mensual > 0) sal,
                       AVG(e.total_habilidades_detectadas) hab
                FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
                WHERE e.mes_periodo = :a GROUP BY 1),
            ant AS (
                SELECT d.portal, COUNT(*) n FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
                WHERE e.mes_periodo = :p GROUP BY 1),
            txt AS (
                SELECT portal, AVG(CASE WHEN LENGTH(COALESCE(payload_json::json->>'Descripcion', '')) >= 200
                                   OR payload_json LIKE '%Descripcion_detalle%' THEN 1.0 ELSE 0 END) pct
                FROM ofertas_raw_historico WHERE mes_periodo = :a GROUP BY 1)
            SELECT COALESCE(act.portal, ant.portal), COALESCE(act.n, 0), COALESCE(ant.n, 0), COALESCE(act.sal, 0),
                   act.hab, txt.pct
            FROM act FULL JOIN ant USING (portal) LEFT JOIN txt ON txt.portal = COALESCE(act.portal, ant.portal)
            ORDER BY 2 DESC""", a=actual, p=previo or -1)
        for portal, n, n_ant, sal, hab, pct in filas:
            hab_txt = f"{hab:.1f}" if hab is not None else "—"
            pct_txt = f"{100 * pct:.0f} %" if pct is not None else "—"
            print(f"{portal:<14}{n:>9}{n_ant:>10}{sal:>13}{hab_txt:>13}{pct_txt:>11}")
            if n == 0 and n_ant > 0 and portal not in ("Torre.ai",):
                alertas.append(f"{portal}: 0 ofertas en {actual} (tenía {n_ant} en {previo})")
            if pct is not None and pct < 0.5:
                alertas.append(f"{portal}: solo {100 * pct:.0f} % de ofertas con descripción en {actual}")

        dup = q("""SELECT (SELECT COUNT(*) FROM (SELECT 1 FROM fact_extracciones_historico
                       GROUP BY id_vacante_hash, mes_periodo HAVING COUNT(*) > 1) a),
                          (SELECT COUNT(*) FROM (SELECT 1 FROM fact_habilidades_historico
                       GROUP BY id_vacante_hash, habilidad, mes_periodo HAVING COUNT(*) > 1) b)""")[0]
        print(f"\nDuplicados (extracciones, habilidades): {dup}")
        if any(dup):
            alertas.append(f"Hay duplicados en el histórico: {dup}")

        print("Mercado:", ", ".join(f"{m}: {n}" for m, n in q("""
            SELECT d.tipo_mercado, COUNT(*) FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
            WHERE e.mes_periodo = :a GROUP BY 1 ORDER BY 1""", a=actual)))
        agg = q("SELECT COUNT(*) FROM agg_metricas_mensuales WHERE mes_periodo = :a", a=actual)[0][0]
        print(f"Métricas agregadas del mes: {agg} filas")
        if agg == 0:
            alertas.append(f"agg_metricas_mensuales no tiene filas para {actual}")
        ultimo = q("SELECT MAX(mes_periodo) FROM obs_demanda_habilidades WHERE es_ultimo_mes")[0][0]
        print(f"Vistas del tablero apuntan al último mes: {ultimo}")
        if ultimo != actual:
            alertas.append(f"obs_demanda_habilidades marca como último mes {ultimo}, no {actual}")

    print()
    for nombre, url in URLS.items():
        try:
            estado = requests.get(url, timeout=30).status_code
        except requests.RequestException as e:
            estado = f"error ({type(e).__name__})"
        print(f"{nombre:<28} → {estado}")
        if estado != 200:
            alertas.append(f"{nombre} responde {estado}")

    print("\n" + ("ALERTAS:\n- " + "\n- ".join(alertas) if alertas else "Sin alertas."))
    return 1 if alertas else 0


if __name__ == "__main__":
    sys.exit(main())
