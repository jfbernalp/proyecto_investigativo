"""
Enriquecimiento único de LinkedIn (24-oct-2026).

Hasta el 24-oct el scraper de LinkedIn no descargaba la descripción de las ofertas, así que la
minería de habilidades casi no tuvo texto (0,3 habilidades por oferta). Este script consulta el
detalle público de cada oferta del histórico que siga publicada y:
  - agrega a fact_habilidades_historico SOLO las habilidades nuevas (mismo mes y fecha de la foto),
  - actualiza total_habilidades_detectadas en fact_extracciones_historico,
  - agrega la descripción y los criterios al payload del crudo (conservando el original).
Todo en una transacción con la excepción de mantenimiento; nunca borra filas.

Las descripciones descargadas se guardan en un caché JSON (también sirve de respaldo).

Uso:  python scripts/enriquecer_linkedin.py <cache.json>             (simulación)
      python scripts/enriquecer_linkedin.py <cache.json> --ejecutar
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, DatabaseManager, SETTING_MANTENIMIENTO, normalizar_url_bd  # noqa: E402
from src.processing.requirements_parser import extraer_habilidades_texto  # noqa: E402
from src.scrapers.linkedin_scraper import LinkedInScraper  # noqa: E402

TEXTO_MINIMO = 200


def descargar_detalles(codigos, cache_path: Path) -> dict:
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    pendientes = [c for c in codigos if c not in cache]
    scraper = LinkedInScraper()
    for i, codigo in enumerate(pendientes, 1):
        descripcion, criterios = scraper._obtener_detalle(codigo)
        cache[codigo] = {"descripcion": descripcion, "criterios": criterios}
        if i % 20 == 0 or i == len(pendientes):
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  detalle {i}/{len(pendientes)}")
    return cache


def main(cache_path: Path, ejecutar: bool):
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    raw = pd.read_sql_query(text(
        "SELECT r.id_vacante_hash, r.mes_periodo, r.codigo, r.nombre_oferta, r.payload_json, "
        "       e.fecha_extraccion, e.salario_cop_mensual, d.tipo_mercado "
        "FROM ofertas_raw_historico r "
        "JOIN fact_extracciones_historico e USING (id_vacante_hash, mes_periodo) "
        "JOIN dim_ofertas d USING (id_vacante_hash) "
        "WHERE r.portal = 'LinkedIn'"), engine)
    raw["payload"] = raw["payload_json"].apply(json.loads)
    sin_texto = raw[raw["payload"].apply(lambda p: len(str(p.get("Descripcion") or "")) < TEXTO_MINIMO
                                         and "Descripcion_detalle" not in p)]
    codigos = sorted({c for c in sin_texto["codigo"].astype(str) if c.isdigit()})
    print(f"Ofertas de LinkedIn sin descripción en el histórico: {len(sin_texto)} filas, {len(codigos)} ofertas distintas")
    detalles = descargar_detalles(codigos, cache_path)

    existentes = pd.read_sql_query(text(
        "SELECT id_vacante_hash, mes_periodo, habilidad FROM fact_habilidades_historico WHERE portal = 'LinkedIn'"), engine)
    ya = set(zip(existentes.id_vacante_hash, existentes.mes_periodo, existentes.habilidad))

    nuevas_hab, totales, payloads = [], [], []
    for _, r in sin_texto.iterrows():
        det = detalles.get(str(r["codigo"]))
        if not det or len(det["descripcion"]) < TEXTO_MINIMO:
            continue  # la oferta ya no está publicada
        criterios = " | ".join(f"{k}: {v}" for k, v in det["criterios"].items())
        habilidades = extraer_habilidades_texto(f"{r['nombre_oferta']} {criterios} {det['descripcion']}")
        for h in habilidades:
            if (r["id_vacante_hash"], r["mes_periodo"], h) not in ya:
                nuevas_hab.append({
                    "id_vacante_hash": r["id_vacante_hash"], "habilidad": h,
                    "fecha_extraccion": r["fecha_extraccion"], "mes_periodo": r["mes_periodo"],
                    "portal": "LinkedIn", "tipo_mercado": r["tipo_mercado"],
                    "salario_cop_mensual": r["salario_cop_mensual"],
                })
        totales.append({"h": r["id_vacante_hash"], "m": int(r["mes_periodo"]),
                        "n": len(set(habilidades) | {x[2] for x in ya if x[0] == r["id_vacante_hash"] and x[1] == r["mes_periodo"]})})
        p = dict(r["payload"])
        p.update({"Descripcion_detalle": det["descripcion"], "Criterios_detalle": det["criterios"],
                  "Enriquecido_el": date.today().isoformat()})
        payloads.append({"h": r["id_vacante_hash"], "m": int(r["mes_periodo"]),
                         "p": json.dumps(p, ensure_ascii=False, default=str)})

    df_hab = pd.DataFrame(nuevas_hab)
    por_mes = sin_texto.groupby("mes_periodo").size().to_dict()
    enriquecidas = pd.DataFrame(payloads).groupby("m").size().to_dict() if payloads else {}
    print(f"Ofertas aún publicadas y enriquecidas por mes: {enriquecidas} (de {por_mes})")
    print(f"Habilidades nuevas a insertar: {len(df_hab)}"
          + (f" | por mes: {df_hab.groupby('mes_periodo').size().to_dict()}" if len(df_hab) else ""))
    if len(df_hab):
        print("Top habilidades agregadas:", df_hab["habilidad"].value_counts().head(8).to_dict())

    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(text(f"SET LOCAL {SETTING_MANTENIMIENTO} = 'on'"))
            antes = conn.execute(text("SELECT COUNT(*) FROM fact_habilidades_historico")).scalar()
            if len(df_hab):
                df_hab.to_sql("fact_habilidades_historico", conn, if_exists="append", index=False)
            for t in totales:
                conn.execute(text("UPDATE fact_extracciones_historico SET total_habilidades_detectadas = :n "
                                  "WHERE id_vacante_hash = :h AND mes_periodo = :m"), t)
            for p in payloads:
                conn.execute(text("UPDATE ofertas_raw_historico SET payload_json = :p "
                                  "WHERE id_vacante_hash = :h AND mes_periodo = :m"), p)
            despues = conn.execute(text("SELECT COUNT(*) FROM fact_habilidades_historico")).scalar()
            print(f"fact_habilidades_historico: {antes} → {despues}")
            if despues != antes + len(df_hab):
                raise RuntimeError("Verificación fallida: se revierte todo.")
            if ejecutar:
                tx.commit()
                print("[APLICADO] LinkedIn enriquecido.")
            else:
                tx.rollback()
                print("[SIMULACIÓN] Verificado y revertido. Use --ejecutar para aplicar.")
        except Exception:
            tx.rollback()
            raise
    if ejecutar:
        print(f"[MÉTRICAS] Recalculadas para {DatabaseManager().recalcular_todas_las_metricas()}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    main(Path(args[0]), "--ejecutar" in sys.argv)
