"""
Contexto de mercado para el modelo que diseña las mallas curriculares.

Se construye desde la base del observatorio (vistas obs_* y resultados del análisis de primas), con la
misma fuente que el tablero. Cada cifra lleva su n y la fecha de corte, y la evidencia va ordenada por
fuerza (ver PRIORIDADES). Se guarda versionado: cada propuesta registra con qué contexto se generó.

REGLA DE ORO: nada se rellena ni se estima aquí; si un dato no existe, se omite y se dice en
"limitaciones".
"""
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text

from src.analytics.tendencia_roles import cargar_roles, comparar_meses, portales_comparables

DIR_CONTEXTOS = Path(__file__).resolve().parent.parent.parent / "data" / "curriculo_unicafam" / "contextos"
TOP_HABILIDADES = 40
TOP_HABILIDADES_POR_ROL = 8

PRIORIDADES = [
    "1. DEMANDA (evidencia principal): porcentaje de ofertas que piden cada habilidad en el último corte. "
    "Decida contenidos sobre todo con esto. El cambio frente al mes anterior solo cuenta portales comparables "
    "y, con pocos cortes, no es una tendencia.",
    "2. ROLES: un rol es un conjunto de habilidades que se contratan juntas. Use los perfiles de rol para "
    "agrupar módulos y orientar cada programa a roles concretos.",
    "3. PRIMAS POR ROL CONCLUYENTES: diferencia salarial entre roles con controles. Solo las marcadas "
    "'concluyente' pueden usarse como argumento salarial, citando su rango.",
    "4. CONTEXTO (no concluyente): primas por habilidad y roles no evaluables. No las use como argumento "
    "principal ni afirme que una habilidad 'paga más'.",
]


def _redondear(x, d=1):
    return None if x is None or pd.isna(x) else round(float(x), d)


def _demanda(conn, mes: int, mes_anterior, portales_comparables_: List[str]) -> List[Dict[str, Any]]:
    """Nivel del último mes con todos los portales; el cambio, solo con los portales comparables."""
    df = pd.read_sql_query(text("""
        SELECT mes_periodo, portal, habilidad, SUM(ofertas_con_habilidad) AS n, SUM(ofertas_totales) AS total
        FROM obs_demanda_habilidades WHERE mes_periodo IN (:m, :a) GROUP BY 1, 2, 3"""),
        conn, params={"m": mes, "a": mes_anterior or -1})

    def porcentajes(d):
        g = d.groupby("habilidad")[["n", "total"]].sum()
        return g.assign(pct=100.0 * g["n"] / g["total"])

    act = porcentajes(df[df.mes_periodo == mes])
    comp = df[df.portal.isin(portales_comparables_)]
    comp_act = porcentajes(comp[comp.mes_periodo == mes]) if len(comp) else None
    comp_ant = porcentajes(comp[comp.mes_periodo == mes_anterior]) if len(comp) else None
    filas = []
    for h, r in act.sort_values("pct", ascending=False).head(TOP_HABILIDADES).iterrows():
        fila = {"habilidad": h, "n_ofertas": int(r["n"]), "pct_ofertas": _redondear(r["pct"])}
        if comp_act is not None and h in comp_act.index and h in comp_ant.index:
            fila["cambio_pp_portales_comparables"] = _redondear(comp_act.at[h, "pct"] - comp_ant.at[h, "pct"])
        filas.append(fila)
    return filas


def _roles(conn, roles_ofertas: pd.DataFrame, mes: int) -> List[Dict[str, Any]]:
    """Participación y perfil de habilidades de cada rol (rol desde el título, ver tendencia_roles)."""
    ofertas = roles_ofertas[roles_ofertas.mes_periodo == mes]
    habilidades = pd.read_sql_query(text("""
        SELECT id_vacante_hash, habilidad FROM fact_habilidades_historico WHERE mes_periodo = :m"""),
        conn, params={"m": mes})
    total = len(ofertas)
    salida = []
    for rol, grupo in ofertas.groupby("rol"):
        hab = habilidades[habilidades.id_vacante_hash.isin(grupo.id_vacante_hash)]
        perfil = (hab.groupby("habilidad").id_vacante_hash.nunique() / len(grupo) * 100).sort_values(ascending=False)
        salida.append({
            "rol": rol, "n_ofertas": int(len(grupo)), "pct_ofertas": _redondear(100.0 * len(grupo) / total),
            "habilidades_del_rol": [{"habilidad": h, "pct_ofertas_del_rol": _redondear(v)}
                                    for h, v in perfil.head(TOP_HABILIDADES_POR_ROL).items()],
        })
    return sorted(salida, key=lambda r: r["n_ofertas"], reverse=True)


def _primas(conn, vista: str, clave: str) -> List[Dict[str, Any]]:
    try:
        df = pd.read_sql_query(text(f"SELECT * FROM {vista}"), conn)
    except Exception:
        return []
    columnas = [clave, "n_ofertas", "prima_pct", "ic95_inferior_pct", "ic95_superior_pct", "q_bh"]
    columnas += ["resultado"] if "resultado" in df.columns else ["concluyente"]
    return [{k: (None if pd.isna(v) else (float(v) if isinstance(v, (float, int)) and k != "n_ofertas" else v))
             for k, v in fila.items()} for fila in df[columnas].to_dict(orient="records")]


def _salarios(conn, mes: int) -> List[Dict[str, Any]]:
    df = pd.read_sql_query(text("""
        SELECT tipo_mercado, COUNT(*) AS n_ofertas, COUNT(salario_cop_mensual) AS n_con_salario,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_cop_mensual) AS mediana
        FROM obs_ofertas_mes WHERE mes_periodo = :m GROUP BY 1"""), conn, params={"m": mes})
    return [{"mercado": r.tipo_mercado, "n_ofertas": int(r.n_ofertas), "n_con_salario": int(r.n_con_salario),
             "mediana_salarial_cop_mes": None if pd.isna(r.mediana) else round(float(r.mediana))}
            for r in df.itertuples()]


def construir_contexto(engine) -> Dict[str, Any]:
    with engine.connect() as conn:
        meses = [r[0] for r in conn.execute(text(
            "SELECT DISTINCT mes_periodo FROM fact_extracciones_historico ORDER BY 1 DESC LIMIT 2"))]
        if not meses:
            raise RuntimeError("No hay cortes registrados: no se puede construir el contexto de mercado.")
        mes, mes_anterior = meses[0], (meses[1] if len(meses) > 1 else None)
        roles_ofertas = cargar_roles(conn)
        comparables, excluidos = (portales_comparables(roles_ofertas, mes, mes_anterior)
                                  if mes_anterior else ([], []))
        tendencia = comparar_meses(roles_ofertas, mes, mes_anterior) if mes_anterior else None
        corte = conn.execute(text("SELECT MAX(fecha_extraccion) FROM fact_extracciones_historico")).scalar()
        n_mes = conn.execute(text("SELECT COUNT(*) FROM obs_ofertas_mes WHERE mes_periodo = :m"), {"m": mes}).scalar()
        portales = [r[0] for r in conn.execute(text(
            "SELECT DISTINCT portal FROM obs_ofertas_mes WHERE mes_periodo = :m ORDER BY 1"), {"m": mes})]
        contexto = {
            "fuente": "Observatorio de Empleo UniCafam (Supabase), vistas obs_* y análisis de primas salariales",
            "ultimo_corte": str(corte),
            "mes": mes,
            "mes_anterior": mes_anterior,
            "n_ofertas_mes": int(n_mes),
            "portales_del_mes": portales,
            "prioridades_de_evidencia": PRIORIDADES,
            "portales_comparables_con_mes_anterior": comparables,
            "portales_excluidos_por_cambio_de_busqueda": excluidos,
            "demanda_habilidades": _demanda(conn, mes, mes_anterior, comparables),
            "roles": _roles(conn, roles_ofertas, mes),
            "cambio_roles_vs_mes_anterior": tendencia,
            "primas_por_rol": _primas(conn, "obs_primas_rol", "rol"),
            "primas_por_habilidad": _primas(conn, "obs_primas_habilidad", "habilidad"),
            "salarios_por_mercado": _salarios(conn, mes),
            "limitaciones": [
                "Las primas salariales solo cubren el mercado local y ofertas que publican salario (ElEmpleo, "
                "Magneto y CompuTrabajo); LinkedIn y Talent.com no publican salario.",
                "Las primas son asociaciones con controles (nivel, rol, portal, mes), no efectos causales.",
                "Pocas ofertas internacionales publican salario: su mediana es poco confiable (ver n).",
                "Las habilidades se detectan por reglas de texto sobre el título y la descripción de la oferta.",
                "La muestra sale de búsquedas por términos en cada portal: la participación de un rol refleja "
                "también qué se busca. Los cambios mensuales excluyen portales cuyos términos cambiaron.",
            ],
        }
    contexto["fecha_contexto"] = date.today().isoformat()
    contexto["id"] = hashlib.sha256(json.dumps(contexto, sort_keys=True, ensure_ascii=False, default=str)
                                    .encode()).hexdigest()[:12]
    return contexto


def guardar_contexto(contexto: Dict[str, Any]) -> Path:
    DIR_CONTEXTOS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_CONTEXTOS / f"contexto_{contexto['ultimo_corte']}_{contexto['id']}.json"
    if not ruta.exists():
        ruta.write_text(json.dumps(contexto, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return ruta


def obtener_contexto_vigente() -> Dict[str, Any]:
    """Contexto desde la base (y archivado); si la base no responde, el último contexto archivado."""
    from sqlalchemy import create_engine
    from src.database.db_manager import DATABASE_URL, normalizar_url_bd
    try:
        contexto = construir_contexto(create_engine(normalizar_url_bd(DATABASE_URL)))
        guardar_contexto(contexto)
        return contexto
    except Exception as e:
        archivados = sorted(DIR_CONTEXTOS.glob("contexto_*.json"), key=lambda r: r.stat().st_mtime)
        if not archivados:
            raise RuntimeError(f"Sin contexto de mercado: la base no respondió ({e}) y no hay contextos archivados.")
        print(f"[CONTEXTO AVISO] La base no respondió ({e}); se usa el último contexto archivado: {archivados[-1].name}")
        return json.loads(archivados[-1].read_text(encoding="utf-8"))


def cargar_contexto(contexto_id: str) -> Dict[str, Any]:
    archivos = list(DIR_CONTEXTOS.glob(f"contexto_*_{contexto_id}.json"))
    if not archivos:
        raise FileNotFoundError(f"No existe el contexto {contexto_id}")
    return json.loads(archivos[0].read_text(encoding="utf-8"))
