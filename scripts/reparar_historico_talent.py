"""
Reparación única del histórico de Talent.com (24-oct-2026).

Hasta el 24-oct el scraper usaba un código posicional (TAL_página_índice): ofertas distintas en
meses distintos compartían hash, y el histórico mezcló sus datos. Este script re-clava cada oferta
por su contenido real (nombre + empresa + ubicación) usando las fotos de cada corrida:

  S1  202609 / 2026-09-12   CSV modelado y crudo del commit 3d6397a (+3 ofertas solo en dim_ofertas)
  S2  202610 / 2026-10-17   CSV modelado y crudo del commit 9eb25af
  S3  202610 / 2026-10-24   artefacto de la corrida 40108017249 de GitHub Actions

En UNA transacción con la excepción de mantenimiento:
  - re-asigna id_vacante_hash en fact_extracciones/fact_habilidades/ofertas_raw_historico
  - reemplaza las filas de Talent en dim_ofertas por una por oferta real (primera/última detección correctas)
  - inserta las ofertas de S3 que esa corrida descartó por el falso "ya registrada"
  - verifica conteos e integridad; si algo no cuadra, revierte todo.

Uso:  python scripts/reparar_historico_talent.py <dir_artefacto_S3>            (simulación)
      python scripts/reparar_historico_talent.py <dir_artefacto_S3> --ejecutar
"""

import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import (  # noqa: E402
    DATABASE_URL, DatabaseManager, SETTING_MANTENIMIENTO, normalizar_url_bd,
)
from src.processing.cleaner import clasificar_rol_tecnico  # noqa: E402

PORTAL = "Talent.com"
hash_vacante = DatabaseManager.generar_hash_vacante


def codigo_legado(nombre, empresa, ubicacion) -> str:
    clave = "|".join(str(x or "").strip().lower() for x in (nombre, empresa, ubicacion))
    return "LEG-" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:12]


def leer_git(commit: str, ruta: str) -> bytes:
    return subprocess.run(["git", "show", f"{commit}:{ruta}"], cwd=ROOT_DIR, capture_output=True, check=True).stdout


def cargar_fotos(dir_s3: Path):
    fotos = []
    for nombre, mes, fecha, modelado, crudo in (
        ("S1", 202609, "2026-09-12",
         pd.read_csv(io.BytesIO(leer_git("3d6397a", "data/analytics/matriz_ofertas_dashboard.csv"))),
         pd.read_excel(io.BytesIO(leer_git("3d6397a", "data/raw/ofertas_consolidadas.xlsx")))),
        ("S2", 202610, "2026-10-17",
         pd.read_csv(io.BytesIO(leer_git("9eb25af", "data/analytics/matriz_ofertas_dashboard.csv"))),
         pd.read_excel(io.BytesIO(leer_git("9eb25af", "data/raw/ofertas_consolidadas.xlsx")))),
        ("S3", 202610, "2026-10-24",
         pd.read_csv(dir_s3 / "analytics" / "matriz_ofertas_dashboard.csv"),
         pd.read_excel(dir_s3 / "raw" / "ofertas_consolidadas.xlsx")),
    ):
        m = modelado[modelado["Portal"] == PORTAL].copy()
        m["hash_viejo"] = [hash_vacante(PORTAL, c) for c in m["Codigo"]]
        r = crudo[crudo["Portal"] == PORTAL].copy()
        r["hash_viejo"] = [hash_vacante(PORTAL, c) for c in r["Codigo"]]
        fotos.append({"nombre": nombre, "mes": mes, "fecha": fecha, "modelado": m, "crudo": r})
    return fotos


def asignar_codigos(df: pd.DataFrame) -> pd.DataFrame:
    """Código por contenido; si dos ofertas de la misma foto coinciden, se diferencian con sufijo."""
    df = df.copy()
    base = [codigo_legado(n, e, u) for n, e, u in zip(df["Nombre Oferta"], df["Empresa"], df["Ubicacion"])]
    vistos, codigos = {}, []
    for b in base:
        vistos[b] = vistos.get(b, 0) + 1
        codigos.append(b if vistos[b] == 1 else f"{b}-{vistos[b]}")
    df["codigo_nuevo"] = codigos
    df["hash_nuevo"] = [hash_vacante(PORTAL, c) for c in codigos]
    return df


def main(dir_s3: Path, ejecutar: bool):
    engine = create_engine(normalizar_url_bd(DATABASE_URL))
    fotos = cargar_fotos(dir_s3)
    dim_viejo = pd.read_sql_query(text("SELECT * FROM dim_ofertas WHERE portal = :p"), engine, params={"p": PORTAL})
    hashes_viejos = set(dim_viejo["id_vacante_hash"])

    # --- Mapeo (hash_viejo, mes, fecha) -> hash_nuevo y filas de la nueva dimensión ---
    mapeo, ocurrencias = [], []
    for f in fotos:
        m = asignar_codigos(f["modelado"])
        f["modelado"] = m
        for _, r in m.iterrows():
            mapeo.append((r["hash_viejo"], f["mes"], f["fecha"], r["hash_nuevo"], r["codigo_nuevo"], 0))
            ocurrencias.append({
                "id_vacante_hash": r["hash_nuevo"], "fecha": f["fecha"], "nombre_oferta": r["Nombre Oferta"],
                "empresa": r["Empresa"], "ubicacion": r["Ubicacion"], "modalidad": r.get("Modalidad"),
                "seniority": r.get("Seniority"), "tipo_mercado": r.get("Tipo_Mercado"),
                "moneda_original": r.get("Moneda_Original"),
            })
    # Ofertas de septiembre presentes en los hechos pero no en el CSV de esa foto (otra corrida de sep):
    # su contenido es el de dim_ofertas, cuya primera detección fue septiembre.
    with engine.connect() as conn:
        sep_en_hechos = {r[0] for r in conn.execute(text(
            "SELECT DISTINCT id_vacante_hash FROM fact_extracciones_historico WHERE mes_periodo = 202609"
        )) if r[0] in hashes_viejos}
    sep_en_csv = set(fotos[0]["modelado"]["hash_viejo"])
    for _, d in dim_viejo[dim_viejo["id_vacante_hash"].isin(sep_en_hechos - sep_en_csv)].iterrows():
        codigo = codigo_legado(d["nombre_oferta"], d["empresa"], d["ubicacion"])
        nuevo = hash_vacante(PORTAL, codigo)
        mapeo.append((d["id_vacante_hash"], 202609, "2026-09-12", nuevo, codigo, 1))
        ocurrencias.append({
            "id_vacante_hash": nuevo, "fecha": "2026-09-12", "nombre_oferta": d["nombre_oferta"],
            "empresa": d["empresa"], "ubicacion": d["ubicacion"], "modalidad": d["modalidad"],
            "seniority": d["seniority"], "tipo_mercado": d["tipo_mercado"], "moneda_original": d["moneda_original"],
        })

    df_map = pd.DataFrame(mapeo, columns=["hash_viejo", "mes", "fecha", "hash_nuevo", "codigo_nuevo", "prioridad"])
    # Dos códigos posicionales de la misma foto que resultan ser la MISMA oferta (vino en corridas
    # distintas del mismo día en otra posición): se conserva una, las demás son duplicados reales.
    df_map = df_map.sort_values(["hash_nuevo", "mes", "fecha", "prioridad"])
    df_map["duplicado"] = df_map.duplicated(subset=["hash_nuevo", "mes", "fecha"], keep="first")
    occ = pd.DataFrame(ocurrencias).sort_values("fecha")
    primero = occ.groupby("id_vacante_hash").first()
    ultimo = occ.groupby("id_vacante_hash").last()
    dim_nuevo = pd.DataFrame({
        "id_vacante_hash": primero.index,
        "portal": PORTAL,
        "rol_buscado": [clasificar_rol_tecnico(n) for n in primero["nombre_oferta"]],
        "nombre_oferta": primero["nombre_oferta"].values,
        "empresa": primero["empresa"].values,
        "ubicacion": primero["ubicacion"].values,
        "modalidad": ultimo["modalidad"].values,
        "seniority": ultimo["seniority"].values,
        "tipo_mercado": primero["tipo_mercado"].values,
        "moneda_original": primero["moneda_original"].values,
        "url": "",
        "primera_fecha_deteccion": primero["fecha"].values,
        "ultima_fecha_deteccion": ultimo["fecha"].values,
    })

    # Ofertas de S3 que la corrida del 24-oct no registró (su hash posicional "ya existía" en 202610)
    hashes_s2 = set(fotos[1]["modelado"]["hash_nuevo"])
    s3 = fotos[2]
    s3_nuevas = s3["modelado"][~s3["modelado"]["hash_nuevo"].isin(hashes_s2)]

    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(text(f"SET LOCAL {SETTING_MANTENIMIENTO} = 'on'"))
            antes = {
                "ext": dict(conn.execute(text(
                    "SELECT mes_periodo, COUNT(*) FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash) "
                    "WHERE d.portal = :p GROUP BY 1"), {"p": PORTAL}).fetchall()),
                "hab": conn.execute(text(
                    "SELECT COUNT(*) FROM fact_habilidades_historico h JOIN dim_ofertas d USING (id_vacante_hash) WHERE d.portal = :p"),
                    {"p": PORTAL}).scalar(),
            }

            df_map.to_sql("tmp_mapeo_talent", conn, if_exists="replace", index=False)
            n_ext_dup = conn.execute(text("""
                DELETE FROM fact_extracciones_historico f USING tmp_mapeo_talent m
                WHERE m.duplicado AND f.id_vacante_hash = m.hash_viejo AND f.mes_periodo = m.mes
                  AND f.fecha_extraccion = m.fecha::date
            """)).rowcount
            n_ext = conn.execute(text("""
                UPDATE fact_extracciones_historico f SET id_vacante_hash = m.hash_nuevo
                FROM tmp_mapeo_talent m
                WHERE f.id_vacante_hash = m.hash_viejo AND f.mes_periodo = m.mes AND f.fecha_extraccion = m.fecha::date
            """)).rowcount
            # Habilidades: si dos fotos del mismo mes son la misma oferta con la misma habilidad, sobra una
            n_hab_dup = conn.execute(text("""
                DELETE FROM fact_habilidades_historico f USING tmp_mapeo_talent m
                WHERE f.id_vacante_hash = m.hash_viejo AND f.mes_periodo = m.mes AND f.fecha_extraccion = m.fecha::date
                  AND EXISTS (
                    SELECT 1 FROM fact_habilidades_historico g JOIN tmp_mapeo_talent m2
                      ON g.id_vacante_hash = m2.hash_viejo AND g.mes_periodo = m2.mes AND g.fecha_extraccion = m2.fecha::date
                    WHERE m2.hash_nuevo = m.hash_nuevo AND g.mes_periodo = f.mes_periodo AND g.habilidad = f.habilidad
                      AND (g.fecha_extraccion, m2.prioridad, g.id_registro) < (f.fecha_extraccion, m.prioridad, f.id_registro))
            """)).rowcount
            n_hab = conn.execute(text("""
                UPDATE fact_habilidades_historico f SET id_vacante_hash = m.hash_nuevo
                FROM tmp_mapeo_talent m
                WHERE f.id_vacante_hash = m.hash_viejo AND f.mes_periodo = m.mes AND f.fecha_extraccion = m.fecha::date
            """)).rowcount
            conn.execute(text("""
                DELETE FROM ofertas_raw_historico r USING tmp_mapeo_talent m
                WHERE m.duplicado AND r.id_vacante_hash = m.hash_viejo AND r.mes_periodo = m.mes
                  AND r.fecha_extraccion = m.fecha::date
            """))
            n_raw = conn.execute(text("""
                UPDATE ofertas_raw_historico r SET id_vacante_hash = m.hash_nuevo, codigo = m.codigo_nuevo
                FROM tmp_mapeo_talent m
                WHERE r.id_vacante_hash = m.hash_viejo AND r.mes_periodo = m.mes AND r.fecha_extraccion = m.fecha::date
            """)).rowcount
            conn.execute(text("DROP TABLE tmp_mapeo_talent"))

            conn.execute(text("DELETE FROM dim_ofertas WHERE portal = :p"), {"p": PORTAL})
            dim_nuevo.to_sql("dim_ofertas", conn, if_exists="append", index=False)

            # Insertar lo que la corrida del 24-oct descartó
            ext_s3 = pd.DataFrame({
                "id_vacante_hash": s3_nuevas["hash_nuevo"], "fecha_extraccion": s3["fecha"], "mes_periodo": s3["mes"],
                "salario_original": s3_nuevas.get("Salario"), "salario_cop_mensual": s3_nuevas.get("Salario_COP"),
                "salario_millones": s3_nuevas.get("Salario_Millones"), "anios_experiencia": s3_nuevas.get("Anios_Experiencia"),
                "nivel_educativo_ordinal": s3_nuevas.get("Nivel_Educativo_Ordinal"),
                "total_habilidades_detectadas": s3_nuevas.get("Total_Habilidades_Detectadas"),
            })
            ext_s3.to_sql("fact_extracciones_historico", conn, if_exists="append", index=False)
            crudo_s3 = asignar_codigos(s3["crudo"])
            crudo_s3 = crudo_s3[crudo_s3["hash_nuevo"].isin(set(s3_nuevas["hash_nuevo"]))]
            raw_s3 = pd.DataFrame({
                "id_vacante_hash": crudo_s3["hash_nuevo"], "mes_periodo": s3["mes"], "fecha_extraccion": s3["fecha"],
                "portal": PORTAL, "codigo": crudo_s3["codigo_nuevo"], "nombre_oferta": crudo_s3["Nombre Oferta"],
                "empresa": crudo_s3["Empresa"], "url": "",
                "payload_json": [json.dumps({k: (None if pd.isna(v) else v) for k, v in row.items()
                                             if k not in ("hash_viejo", "codigo_nuevo", "hash_nuevo")},
                                            ensure_ascii=False, default=str)
                                 for _, row in crudo_s3.iterrows()],
            })
            raw_s3.to_sql("ofertas_raw_historico", conn, if_exists="append", index=False)

            # --- Verificaciones ---
            q = lambda s, **p: conn.execute(text(s), p).scalar()
            restos = q("SELECT COUNT(*) FROM fact_extracciones_historico WHERE id_vacante_hash = ANY(:h)", h=list(hashes_viejos)) \
                + q("SELECT COUNT(*) FROM fact_habilidades_historico WHERE id_vacante_hash = ANY(:h)", h=list(hashes_viejos)) \
                + q("SELECT COUNT(*) FROM ofertas_raw_historico WHERE id_vacante_hash = ANY(:h)", h=list(hashes_viejos))
            huerfanos = q("SELECT COUNT(*) FROM fact_extracciones_historico f LEFT JOIN dim_ofertas d USING (id_vacante_hash) WHERE d.id_vacante_hash IS NULL") \
                + q("SELECT COUNT(*) FROM fact_habilidades_historico f LEFT JOIN dim_ofertas d USING (id_vacante_hash) WHERE d.id_vacante_hash IS NULL")
            despues_ext = dict(conn.execute(text(
                "SELECT mes_periodo, COUNT(*) FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash) "
                "WHERE d.portal = :p GROUP BY 1"), {"p": PORTAL}).fetchall())
            persistentes = q("SELECT COUNT(*) FROM dim_ofertas WHERE portal = :p AND primera_fecha_deteccion <> ultima_fecha_deteccion", p=PORTAL)

            print(f"Mapeo: {len(df_map)} (oferta, foto) → {df_map['hash_nuevo'].nunique()} ofertas reales")
            print(f"dim_ofertas Talent: {len(dim_viejo)} → {len(dim_nuevo)} | 'persistentes' {int((dim_viejo.primera_fecha_deteccion != dim_viejo.ultima_fecha_deteccion).sum())} → {persistentes}")
            print(f"Duplicados reales (misma oferta, dos códigos posicionales en la misma foto): {n_ext_dup} extracciones")
            print(f"Re-clavado: extracciones {n_ext}, habilidades {n_hab} (+{n_hab_dup} duplicadas eliminadas), crudo {n_raw}")
            print(f"Insertadas de la corrida 24-oct: {len(ext_s3)} extracciones, {len(raw_s3)} crudas")
            print(f"Extracciones Talent por mes: {antes['ext']} → {despues_ext}")
            print(f"Restos de hashes posicionales: {restos} | hechos huérfanos: {huerfanos}")

            ok = (restos == 0 and huerfanos == 0
                  and n_ext_dup == int(df_map["duplicado"].sum())
                  and sum(despues_ext.values()) == sum(antes["ext"].values()) - n_ext_dup + len(ext_s3))
            if not ok:
                raise RuntimeError("Verificación fallida: se revierte todo.")
            if ejecutar:
                tx.commit()
                print("[APLICADO] Histórico de Talent.com reparado.")
            else:
                tx.rollback()
                print("[SIMULACIÓN] Todo verificado y revertido. Use --ejecutar para aplicar.")
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
