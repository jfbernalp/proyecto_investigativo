"""
Reclasificación única del tipo de mercado (24-oct-2026).

detectar_moneda_y_mercado() buscaba la subcadena "cad" en el salario, y "A convenir / No
especifiCADo" la contiene: toda oferta sin salario quedó como "Mercado Internacional (CAD)", aunque
estuviera en Bogotá. Este script recalcula tipo_mercado y moneda_original de cada oferta con la
función corregida, a partir del salario crudo de su registro más reciente, y propaga el mercado a
fact_habilidades_historico. Una transacción con la excepción de mantenimiento; luego recalcula
agg_metricas_mensuales.

Uso:  python scripts/reclasificar_mercado.py            (simulación)
      python scripts/reclasificar_mercado.py --ejecutar
"""

import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, DatabaseManager, SETTING_MANTENIMIENTO, normalizar_url_bd  # noqa: E402
from src.processing.cleaner import detectar_moneda_y_mercado  # noqa: E402


def main(ejecutar: bool):
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    dim = pd.read_sql_query(text("SELECT id_vacante_hash, portal, tipo_mercado, moneda_original FROM dim_ofertas"), engine)
    crudo = pd.read_sql_query(text(
        "SELECT DISTINCT ON (id_vacante_hash) id_vacante_hash, payload_json FROM ofertas_raw_historico "
        "ORDER BY id_vacante_hash, mes_periodo DESC"), engine)
    salario = {h: json.loads(p).get("Salario") for h, p in zip(crudo.id_vacante_hash, crudo.payload_json)}

    nuevos = [detectar_moneda_y_mercado(p, salario.get(h)) for h, p in zip(dim.id_vacante_hash, dim.portal)]
    dim["moneda_nueva"] = [n[0] for n in nuevos]
    dim["mercado_nuevo"] = [n[1] for n in nuevos]
    cambios = dim[(dim.tipo_mercado != dim.mercado_nuevo) | (dim.moneda_original != dim.moneda_nueva)]

    print(f"Ofertas: {len(dim)} | sin crudo (se usa la regla por portal): {(~dim.id_vacante_hash.isin(salario)).sum()}")
    print(f"Cambian: {len(cambios)}")
    print(pd.crosstab([cambios.portal, cambios.tipo_mercado], cambios.mercado_nuevo).to_string())
    print("\nMercado por portal después:")
    print(pd.crosstab(dim.portal, dim.mercado_nuevo).to_string())

    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(text(f"SET LOCAL {SETTING_MANTENIMIENTO} = 'on'"))
            cambios[["id_vacante_hash", "moneda_nueva", "mercado_nuevo"]].to_sql(
                "tmp_reclasificacion", conn, if_exists="replace", index=False)
            n_dim = conn.execute(text("""
                UPDATE dim_ofertas d SET tipo_mercado = t.mercado_nuevo, moneda_original = t.moneda_nueva
                FROM tmp_reclasificacion t WHERE d.id_vacante_hash = t.id_vacante_hash""")).rowcount
            n_hab = conn.execute(text("""
                UPDATE fact_habilidades_historico h SET tipo_mercado = d.tipo_mercado
                FROM dim_ofertas d WHERE h.id_vacante_hash = d.id_vacante_hash
                  AND h.tipo_mercado IS DISTINCT FROM d.tipo_mercado""")).rowcount
            conn.execute(text("DROP TABLE tmp_reclasificacion"))
            incoherentes = conn.execute(text("""
                SELECT COUNT(*) FROM fact_habilidades_historico h JOIN dim_ofertas d USING (id_vacante_hash)
                WHERE h.tipo_mercado IS DISTINCT FROM d.tipo_mercado""")).scalar()
            print(f"\nActualizadas: dim_ofertas {n_dim}, fact_habilidades_historico {n_hab} | incoherencias restantes: {incoherentes}")
            print(pd.read_sql_query(text("""
                SELECT e.mes_periodo, d.tipo_mercado, COUNT(*) AS ofertas,
                       COUNT(*) FILTER (WHERE e.salario_cop_mensual > 0) AS con_salario,
                       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salario_cop_mensual)
                              FILTER (WHERE e.salario_cop_mensual > 0))::numeric) AS mediana_cop
                FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
                GROUP BY 1, 2 ORDER BY 1, 2"""), conn).to_string(index=False))
            if n_dim != len(cambios) or incoherentes:
                raise RuntimeError("Verificación fallida: se revierte todo.")
            if ejecutar:
                tx.commit()
                print("[APLICADO] Mercado reclasificado.")
            else:
                tx.rollback()
                print("[SIMULACIÓN] Verificado y revertido. Use --ejecutar para aplicar.")
        except Exception:
            tx.rollback()
            raise
    if ejecutar:
        print(f"[MÉTRICAS] Recalculadas para {DatabaseManager().recalcular_todas_las_metricas()}")


if __name__ == "__main__":
    main("--ejecutar" in sys.argv)
