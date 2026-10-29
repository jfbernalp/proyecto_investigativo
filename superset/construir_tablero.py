"""
Tablero público del Observatorio (Superset, dashboard ID 1, embebido en la landing) definido como código.

Idempotente: crea o actualiza datasets (vistas obs_*), gráficos (por nombre) y el diseño del tablero.
Los gráficos anteriores se desvinculan del tablero y se renombran "[Archivado] …" (no se borran).
El rol Public queda con lectura solo de los datasets que usa el tablero.

REGLA DE ORO: ninguna cifra escrita a mano. Todo valor viene de las vistas; los textos solo describen
método y fuentes. Cada métrica lleva su n en la tabla "Base de cálculo".

Uso (dentro del contenedor de Superset):  superset/ejecutar_en_servidor.sh superset/construir_tablero.py
"""
import json
import uuid

from ss_api import BASE, Superset

DASHBOARD_ID = 1
DATABASE_ID = 1
VISTAS = ["obs_ofertas_mes", "obs_demanda_habilidades", "obs_salarios_habilidad", "obs_diferencia_salarial",
          "obs_primas_rol", "obs_primas_habilidad"]
LOCAL = "Mercado Local (Colombia - COP)"
INTERNACIONAL = "Mercado Internacional (Remoto - USD)"

# Paleta categórica validada (skill dataviz). El color sigue a la entidad, nunca al ranking.
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COLORES = {
    # Portales (orden fijo)
    "LinkedIn": PALETA[0], "ElEmpleo": PALETA[1], "Magneto": PALETA[2], "Talent.com": PALETA[3],
    "CompuTrabajo": PALETA[4], "GetOnBoard": PALETA[5], "Torre.ai": PALETA[6], "Remotive": PALETA[7],
    # Mercados
    LOCAL: PALETA[0], INTERNACIONAL: PALETA[1],
    # Tipo de oferta
    "Nuevas en el mes": PALETA[2], "Ya vistas en meses anteriores": PALETA[6],
    # Habilidades con mayor demanda histórica (para la serie de evolución)
    "SQL": PALETA[0], "Python": PALETA[1], "ETL / Pipelines de Datos": PALETA[2], "Power BI": PALETA[3],
    "Estadística / Modelamiento": PALETA[4], "Machine Learning General": PALETA[5], "Azure": PALETA[6],
    "AWS": PALETA[7],
    # Series de una sola métrica (barras simples)
    "% de ofertas": PALETA[0], "Mediana salarial (COP/mes)": PALETA[0],
}


def metrica(sql, etiqueta):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": etiqueta, "hasCustomLabel": True,
            "optionName": f"metric_{uuid.uuid4().hex[:12]}"}


def filtro(columna, valor):
    return {"expressionType": "SIMPLE", "clause": "WHERE", "subject": columna, "operator": "==",
            "comparator": valor, "filterOptionName": f"filter_{uuid.uuid4().hex[:12]}"}


def sin_rango(columna="periodo"):
    return {"expressionType": "SIMPLE", "clause": "WHERE", "subject": columna, "operator": "TEMPORAL_RANGE",
            "comparator": "No filter", "filterOptionName": f"filter_{uuid.uuid4().hex[:12]}"}


OFERTAS = "COUNT(DISTINCT id_vacante_hash)"
MEDIANA = "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_cop_mensual)"
PCT_SALARIO = "ROUND(100.0 * SUM(CASE WHEN tiene_salario THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1)"
PCT_DEMANDA = "ROUND(100.0 * SUM(ofertas_con_habilidad) / NULLIF(SUM(ofertas_totales), 0), 1)"
LEYENDA = {"show_legend": True, "legendType": "scroll", "legendOrientation": "top", "rich_tooltip": True,
           "showTooltipTotal": True}
# Mes como categoría (AAAA-MM): un eje temporal agregaba meses vacíos de relleno ("Aug 2026")
EJE_MES = {"x_axis": "mes", "x_axis_sort": "mes", "x_axis_sort_asc": True}
ULTIMO_MES = {"expressionType": "SIMPLE", "clause": "WHERE", "subject": "es_ultimo_mes", "operator": "IS TRUE",
              "filterOptionName": "filter_ultimo_mes"}


def kpi(clave, nombre, vista, sql, etiqueta, formato, filtros=()):
    return clave, nombre, vista, "big_number", {
        "x_axis": "periodo", "time_grain_sqla": "P1M", "metric": metrica(sql, etiqueta),
        "adhoc_filters": [sin_rango(), *filtros], "show_trend_line": True, "start_y_axis_at_zero": True,
        "compare_lag": 1, "compare_suffix": "vs. mes anterior", "y_axis_format": formato,
        "show_timestamp": True, "time_format": "%b %Y", "header_font_size": 0.3, "subheader_font_size": 0.125,
        "color_picker": {"r": 42, "g": 120, "b": 214, "a": 1}, "rolling_type": "None",
    }


GRAFICOS = [
    kpi("kpi_ofertas", "Ofertas únicas en el mes", "obs_ofertas_mes", OFERTAS, "Ofertas únicas", "SMART_NUMBER"),
    kpi("kpi_mediana_local", "Mediana salarial · mercado local (COP/mes)", "obs_ofertas_mes", MEDIANA, "Mediana salarial local",
        "SMART_NUMBER", [filtro("tipo_mercado", LOCAL)]),
    kpi("kpi_mediana_internacional", "Mediana salarial · mercado internacional (COP/mes, n bajo)", "obs_ofertas_mes", MEDIANA,
        "Mediana salarial internacional", "SMART_NUMBER", [filtro("tipo_mercado", INTERNACIONAL)]),
    kpi("kpi_transparencia", "% de ofertas que publican salario", "obs_ofertas_mes", PCT_SALARIO, "% con salario", ",.1f"),
    ("demanda_ultimo_mes", "Habilidades más demandadas · último mes (% de ofertas que las piden)",
     "obs_demanda_habilidades", "echarts_timeseries_bar", {
        "x_axis": "habilidad", "metrics": [metrica(PCT_DEMANDA, "% de ofertas")], "groupby": [],
        "adhoc_filters": [ULTIMO_MES], "orientation": "horizontal", "row_limit": 15,
        "timeseries_limit_metric": metrica(PCT_DEMANDA, "% de ofertas"), "order_desc": True,
        "x_axis_sort": "% de ofertas", "x_axis_sort_asc": True, "show_value": True, "y_axis_format": ",.1f",
        "show_legend": False, "rich_tooltip": True,
    }),
    ("mejor_pagadas_local", "Mediana salarial por habilidad · mercado local, todo el histórico (descriptiva, no es prima)",
     "obs_salarios_habilidad", "echarts_timeseries_bar", {
        "x_axis": "habilidad", "metrics": [metrica(MEDIANA, "Mediana salarial (COP/mes)")], "groupby": [],
        "adhoc_filters": [filtro("tipo_mercado", LOCAL),
                          {"expressionType": "SQL", "clause": "HAVING", "sqlExpression": f"{OFERTAS} >= 5",
                           "filterOptionName": "filter_n_minimo"}],
        "orientation": "horizontal", "row_limit": 15,
        "timeseries_limit_metric": metrica(MEDIANA, "Mediana salarial (COP/mes)"), "order_desc": True,
        "x_axis_sort": "Mediana salarial (COP/mes)", "x_axis_sort_asc": True, "show_value": True,
        "y_axis_format": "SMART_NUMBER", "show_legend": False, "rich_tooltip": True,
    }),
    ("diferencia_salarial", "Diferencia frente a la mediana del mercado · todo el histórico (descriptiva, no es prima)",
     "obs_diferencia_salarial", "table", {
        "query_mode": "raw",
        "all_columns": ["habilidad", "mercado", "n_ofertas_con_salario", "mediana_habilidad_cop",
                        "mediana_mercado_cop", "diferencia_pct"],
        "order_by_cols": ['["diferencia_pct", false]'], "row_limit": 100, "adhoc_filters": [],
        "include_search": False, "show_cell_bars": False, "allow_rearrange_columns": False,
        "column_config": {"mediana_habilidad_cop": {"d3NumberFormat": ",.0f"},
                          "mediana_mercado_cop": {"d3NumberFormat": ",.0f"},
                          "diferencia_pct": {"d3NumberFormat": "+,.1f"}},
    }),
    ("ofertas_mes_portal", "Ofertas por mes y portal", "obs_ofertas_mes", "echarts_timeseries_bar", {
        **EJE_MES, "metrics": [metrica(OFERTAS, "Ofertas únicas")],
        "groupby": ["portal"], "adhoc_filters": [], "stack": "Stack", "only_total": True,
        "show_value": True, "y_axis_format": "SMART_NUMBER", "row_limit": 1000, **LEYENDA,
    }),
    ("ofertas_nuevas", "Ofertas nuevas vs. ya vistas en meses anteriores", "obs_ofertas_mes", "echarts_timeseries_bar", {
        **EJE_MES, "metrics": [metrica(OFERTAS, "Ofertas únicas")],
        "groupby": [{"expressionType": "SQL", "label": "Tipo de oferta", "sqlExpression":
                     "CASE WHEN es_nueva THEN 'Nuevas en el mes' ELSE 'Ya vistas en meses anteriores' END"}],
        "adhoc_filters": [], "stack": "Stack", "only_total": True, "show_value": True,
        "y_axis_format": "SMART_NUMBER", "row_limit": 1000, **LEYENDA,
    }),
    ("evolucion_demanda", "Evolución de la demanda · 8 habilidades más pedidas (% de ofertas)",
     "obs_demanda_habilidades", "echarts_timeseries_line", {
        **EJE_MES, "metrics": [metrica(PCT_DEMANDA, "% de ofertas")],
        "groupby": ["habilidad"], "adhoc_filters": [], "series_limit": 8,
        "series_limit_metric": metrica(PCT_DEMANDA, "% de ofertas"), "order_desc": True,
        "markerEnabled": True, "markerSize": 6, "y_axis_format": ",.1f", "row_limit": 10000, **LEYENDA,
    }),
    ("mediana_mes_mercado", "Mediana salarial por mes y mercado (COP/mes)", "obs_ofertas_mes", "echarts_timeseries_line", {
        **EJE_MES, "metrics": [metrica(MEDIANA, "Mediana salarial")],
        "groupby": ["tipo_mercado"], "adhoc_filters": [], "markerEnabled": True, "markerSize": 6,
        "y_axis_format": "SMART_NUMBER", "row_limit": 1000, **LEYENDA,
    }),
    ("base_calculo", "Base de cálculo por mes (n de cada cifra)", "obs_ofertas_mes", "table", {
        "query_mode": "aggregate", "groupby": ["mes"],
        "metrics": [metrica(OFERTAS, "Ofertas únicas"),
                    metrica("COUNT(DISTINCT portal)", "Portales"),
                    metrica("COUNT(DISTINCT id_vacante_hash) FILTER (WHERE tiene_salario)", "Con salario"),
                    metrica(f"COUNT(DISTINCT id_vacante_hash) FILTER (WHERE tiene_salario AND tipo_mercado = '{LOCAL}')",
                            "Con salario · local"),
                    metrica(f"COUNT(DISTINCT id_vacante_hash) FILTER (WHERE tiene_salario AND tipo_mercado = '{INTERNACIONAL}')",
                            "Con salario · internacional")],
        "adhoc_filters": [], "order_by_cols": ['["mes", false]'], "row_limit": 60,
        "include_search": False, "show_cell_bars": False,
    }),
    ("primas_rol", "Prima salarial por rol frente al rol de referencia (con controles)", "obs_primas_rol", "table", {
        "query_mode": "raw",
        "all_columns": ["rol", "n_ofertas", "prima_pct", "ic95_inferior_pct", "ic95_superior_pct", "q_bh", "resultado"],
        "order_by_cols": ['["orden", true]', '["prima_pct", false]'], "row_limit": 50, "adhoc_filters": [],
        "include_search": False, "show_cell_bars": False, "allow_rearrange_columns": False,
        "column_config": {"prima_pct": {"d3NumberFormat": "+,.1f"}, "ic95_inferior_pct": {"d3NumberFormat": "+,.1f"},
                          "ic95_superior_pct": {"d3NumberFormat": "+,.1f"}, "q_bh": {"d3NumberFormat": ",.3f"}},
    }),
    ("primas_habilidad", "Prima salarial por habilidad (con controles · n ≥ 20)", "obs_primas_habilidad", "table", {
        "query_mode": "raw",
        "all_columns": ["habilidad", "n_ofertas", "prima_pct", "ic95_inferior_pct", "ic95_superior_pct", "q_bh",
                        "concluyente"],
        "order_by_cols": ['["prima_pct", false]'], "row_limit": 100, "adhoc_filters": [],
        "include_search": False, "show_cell_bars": False, "allow_rearrange_columns": False,
        "column_config": {"prima_pct": {"d3NumberFormat": "+,.1f"}, "ic95_inferior_pct": {"d3NumberFormat": "+,.1f"},
                          "ic95_superior_pct": {"d3NumberFormat": "+,.1f"}, "q_bh": {"d3NumberFormat": ",.3f"}},
    }),
]

ENCABEZADO = """### Observatorio de Empleo en Ciencia y Analítica de Datos

Vacantes de **Ciencia, Ingeniería y Analítica de Datos** recolectadas cada mes en portales de empleo
(CompuTrabajo, ElEmpleo, Get on Board, LinkedIn, Talent.com, Magneto y
[Remotive](https://remotive.com)). Cada cifra se calcula sobre **ofertas distintas**; el tamaño de
muestra de cada mes está en *Base de cálculo*. Use los filtros de arriba para ver un mercado o un
portal."""

LECTURA_PRIMAS = """#### Cómo leer las primas

- **Prima** = diferencia porcentual del salario **ofrecido** entre ofertas comparables (mismo nivel de
  experiencia, portal y mes; en habilidades, también mismo rol). Modelo de regresión sobre el logaritmo
  del salario con errores robustos.
- **IC 95 %**: rango plausible de la prima. **q**: probabilidad de falso hallazgo corregida por comparar
  muchas habilidades o roles a la vez (Benjamini–Hochberg).
- **Concluyente** = q ≤ 0,10 y el intervalo no cruza 0. Lo no concluyente **no** prueba que no haya
  prima: indica que con la muestra actual no se puede afirmar.
- Solo mercado local y ofertas que **publican salario** (ElEmpleo, Magneto y CompuTrabajo); LinkedIn y
  Talent.com no publican salario. Es una asociación, **no** un efecto causal.
- Se recalcula automáticamente con cada corte mensual."""

NOTAS = """#### Notas metodológicas

- **Mercado local** = ofertas en Colombia sin salario en moneda extranjera; **internacional** = salario
  en USD/EUR/GBP/CAD o portal de empleo remoto (Get on Board, Remotive, Torre.ai).
- Pocas ofertas internacionales publican salario: su mediana es **poco confiable** (ver su n).
- **Habilidades** detectadas por reglas de texto sobre el título y la descripción de cada oferta.
- Las ofertas de **LinkedIn** se enriquecieron con su descripción completa en octubre de 2026; las de
  **Talent.com** anteriores al 24-oct no tienen descripción, por lo que su demanda de habilidades está
  subestimada.
- **Torre.ai** solo aporta datos de septiembre de 2026 (su API dejó de estar disponible);
  **Magneto** y **Remotive** se incorporaron el 24-oct-2026.
- La *diferencia frente a la mediana* compara medianas: **no** mide el efecto causal de una habilidad
  (no controla experiencia, rol ni empresa)."""


def asegurar_datasets(ss):
    # get_or_create no depende de la visibilidad del usuario (el listado sí)
    ids = {}
    for vista in VISTAS:
        r = ss.post("dataset/get_or_create/", {"table_name": vista, "database_id": DATABASE_ID, "schema": "public"})
        ids[vista] = r["result"]["table_id"]
        ss.s.put(f"{BASE}/api/v1/dataset/{ids[vista]}/refresh")
        print(f"dataset {vista}: {ids[vista]}")
    return ids


def asegurar_graficos(ss, ds_ids):
    """Busca cada gráfico por su clave estable (guardada en params), así se puede renombrar sin duplicar."""
    # Nombres con que se crearon los gráficos antes de tener clave (migración única, 27-oct-2026)
    nombres_previos = {
        "Habilidades más demandadas (% de ofertas que las piden)": "demanda_ultimo_mes",
        "Habilidades mejor pagadas · mercado local (mediana, n ≥ 5)": "mejor_pagadas_local",
        "Diferencia frente a la mediana del mercado (descriptiva, no causal)": "diferencia_salarial",
        "Evolución de la demanda · 8 habilidades más pedidas": "evolucion_demanda",
        **{x[1]: x[0] for x in GRAFICOS},
    }
    existentes = {}
    for c in ss.get("chart/", page_size=500, columns=["id", "params", "slice_name", "dashboards.id"])["result"]:
        try:
            clave = json.loads(c.get("params") or "{}").get("observatorio_clave")
        except ValueError:
            clave = None
        en_tablero = any(d["id"] == DASHBOARD_ID for d in c.get("dashboards", []))
        clave = clave or (nombres_previos.get(c["slice_name"]) if en_tablero else None)
        if clave:
            existentes[clave] = c["id"]
    ids = {}
    for clave, nombre, vista, viz, params in GRAFICOS:
        p = {"viz_type": viz, "datasource": f"{ds_ids[vista]}__table", "observatorio_clave": clave, **params}
        cuerpo = {"slice_name": nombre, "viz_type": viz, "datasource_id": ds_ids[vista], "datasource_type": "table",
                  "params": json.dumps(p, ensure_ascii=False), "dashboards": [DASHBOARD_ID]}
        if clave in existentes:
            ss.put(f"chart/{existentes[clave]}", cuerpo)
            ids[clave] = existentes[clave]
        else:
            ids[clave] = ss.post("chart/", cuerpo)["id"]
        print(f"gráfico {ids[clave]:>3}: {nombre}")
    return ids


NOMBRES_COLUMNAS = {
    "obs_diferencia_salarial": {
        "habilidad": "Habilidad", "mercado": "Mercado", "n_ofertas_con_salario": "Ofertas con salario (n)",
        "mediana_habilidad_cop": "Mediana con la habilidad (COP)", "mediana_mercado_cop": "Mediana del mercado (COP)",
        "diferencia_pct": "Diferencia (%)",
    },
    "obs_ofertas_mes": {"mes": "Mes", "portal": "Portal", "tipo_mercado": "Mercado"},
    "obs_demanda_habilidades": {"mes": "Mes", "habilidad": "Habilidad", "portal": "Portal", "tipo_mercado": "Mercado"},
    "obs_salarios_habilidad": {"habilidad": "Habilidad", "portal": "Portal", "tipo_mercado": "Mercado"},
    "obs_primas_rol": {"rol": "Rol", "n_ofertas": "Ofertas con salario (n)", "prima_pct": "Prima vs. referencia (%)",
                       "ic95_inferior_pct": "IC 95 % inferior", "ic95_superior_pct": "IC 95 % superior",
                       "q_bh": "q (BH)", "resultado": "¿Concluyente?"},
    "obs_primas_habilidad": {"habilidad": "Habilidad", "n_ofertas": "Ofertas con salario (n)", "prima_pct": "Prima (%)",
                             "ic95_inferior_pct": "IC 95 % inferior", "ic95_superior_pct": "IC 95 % superior",
                             "q_bh": "q (BH)", "concluyente": "¿Concluyente?"},
}
CAMPOS_COLUMNA = ("id", "column_name", "verbose_name", "type", "is_dttm", "groupby", "filterable", "expression",
                  "description", "python_date_format", "is_active", "extra", "uuid", "advanced_data_type")


def nombrar_columnas(ss, ds):
    """Nombres legibles en tablas, leyendas y filtros (verbose_name del dataset)."""
    for vista, nombres in NOMBRES_COLUMNAS.items():
        cols = ss.get(f"dataset/{ds[vista]}")["result"]["columns"]
        nuevas = []
        for col in cols:
            col = {k: col.get(k) for k in CAMPOS_COLUMNA if k in col}
            if col["column_name"] in nombres:
                col["verbose_name"] = nombres[col["column_name"]]
            nuevas.append(col)
        ss.put(f"dataset/{ds[vista]}", {"columns": nuevas})
    print("nombres de columnas actualizados")


def disenio(g):
    """position_json: secciones con encabezado y filas (ancho total 12)."""
    pos = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
           "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
           "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": "Observatorio del mercado laboral en datos"}}}

    def agregar(componente):
        pos[componente["id"]] = componente
        pos["GRID_ID"]["children"].append(componente["id"])

    def titulo(texto):
        agregar({"type": "HEADER", "id": f"HEADER-{uuid.uuid4().hex[:8]}", "children": [],
                 "parents": ["ROOT_ID", "GRID_ID"],
                 "meta": {"text": texto, "headerSize": "MEDIUM_HEADER", "background": "BACKGROUND_TRANSPARENT"}})

    def fila(*celdas):
        rid = f"ROW-{uuid.uuid4().hex[:8]}"
        hijos = []
        for celda in celdas:
            cid = f"{celda['tipo']}-{uuid.uuid4().hex[:8]}"
            if celda["tipo"] == "CHART":
                nombre = next(x[1] for x in GRAFICOS if x[0] == celda["nombre"])
                meta = {"chartId": g[celda["nombre"]], "width": celda["ancho"], "height": celda["alto"],
                        "sliceName": nombre}
            else:
                meta = {"width": celda["ancho"], "height": celda["alto"], "code": celda["texto"]}
            pos[cid] = {"type": celda["tipo"], "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid], "meta": meta}
            hijos.append(cid)
        agregar({"type": "ROW", "id": rid, "children": hijos, "parents": ["ROOT_ID", "GRID_ID"],
                 "meta": {"background": "BACKGROUND_TRANSPARENT"}})

    graf = lambda nombre, ancho, alto: {"tipo": "CHART", "nombre": nombre, "ancho": ancho, "alto": alto}
    texto = lambda contenido, ancho, alto: {"tipo": "MARKDOWN", "texto": contenido, "ancho": ancho, "alto": alto}
    n = [x[0] for x in GRAFICOS]

    fila(texto(ENCABEZADO, 12, 15))
    fila(graf(n[0], 3, 34), graf(n[1], 3, 34), graf(n[2], 3, 34), graf(n[3], 3, 34))
    titulo("Habilidades más demandadas")
    fila(graf(n[4], 12, 64))
    titulo("Salario por rol y por habilidad")
    fila(graf("primas_rol", 6, 56), texto(LECTURA_PRIMAS, 6, 56))
    fila(graf("primas_habilidad", 12, 52))
    titulo("Diferencias salariales descriptivas (no son primas)")
    fila(graf(n[5], 6, 64), graf(n[6], 6, 64))
    titulo("Evolución en el tiempo")
    fila(graf(n[7], 6, 50), graf(n[8], 6, 50))
    fila(graf(n[9], 6, 50), graf(n[10], 6, 50))
    titulo("Base de cálculo y notas metodológicas")
    fila(graf(n[11], 6, 44), texto(NOTAS, 6, 44))
    return pos


def filtros_nativos(g, ds):
    todos = list(g.values())

    def nativo(fid, nombre, dataset, columna, en_alcance, controles, descripcion):
        return {"id": fid, "name": nombre, "filterType": "filter_select", "type": "NATIVE_FILTER",
                "targets": [{"datasetId": ds[dataset], "column": {"name": columna}}],
                "controlValues": {"enableEmptyFilter": False, "multiSelect": True, "searchAllOptions": False,
                                  "inverseSelection": False, **controles},
                "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
                "cascadeParentIds": [], "description": descripcion,
                "scope": {"rootPath": ["ROOT_ID"], "excluded": [c for c in todos if c not in en_alcance]},
                "chartsInScope": en_alcance, "tabsInScope": []}

    sin_columnas = ("primas_rol", "primas_habilidad")   # resultados del modelo: sin mercado ni portal
    sin_mercado_fijo = [g[k] for k in g if k not in ("kpi_mediana_local", "kpi_mediana_internacional",
                                                       "mejor_pagadas_local", "base_calculo", *sin_columnas)]
    # Sin filtro de mes: los gráficos de evolución muestran todos los meses y el ranking usa el último
    # corte (un valor por defecto en el filtro no se aplicaba al cargar el tablero embebido).
    return [
        nativo("NATIVE_FILTER-mercado", "Mercado", "obs_ofertas_mes", "tipo_mercado", sin_mercado_fijo, {},
               "Mercado local (Colombia, COP) o internacional (remoto, moneda extranjera)."),
        nativo("NATIVE_FILTER-portal", "Portal", "obs_ofertas_mes", "portal",
               [g[k] for k in g if k not in ("diferencia_salarial", *sin_columnas)], {}, "Portal de empleo de origen."),
    ]


CSS = """
/* Integración limpia en la landing: fondo blanco y tipografía coherente */
.dashboard, .dashboard-content, .grid-container { background: #ffffff !important; }
.dashboard-markdown h3 { margin-top: 0; }
.dashboard-component-header .header-title { font-weight: 600; letter-spacing: -0.01em; }
"""


def actualizar_tablero(ss, g, ds):
    actual = ss.get(f"dashboard/{DASHBOARD_ID}")["result"]
    meta = json.loads(actual.get("json_metadata") or "{}")
    meta.update({
        "native_filter_configuration": filtros_nativos(g, ds),
        "label_colors": COLORES, "shared_label_colors": [], "color_scheme": "",
        "cross_filters_enabled": False, "filter_bar_orientation": "HORIZONTAL",
        "chart_configuration": {}, "global_chart_configuration": {
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []}, "chartsInScope": list(g.values())},
        "expanded_slices": {}, "timed_refresh_immune_slices": [], "refresh_frequency": 0,
        "default_filters": "{}", "show_chart_timestamps": False,
    })
    ss.put(f"dashboard/{DASHBOARD_ID}", {
        "dashboard_title": "Observatorio del mercado laboral en datos", "css": CSS, "published": True,
        "position_json": json.dumps(disenio(g), ensure_ascii=False),
        "json_metadata": json.dumps(meta, ensure_ascii=False),
    })
    print("tablero actualizado")


def archivar_anteriores(ss, g):  # noqa: D103
    nuevos = set(g.values())
    for c in ss.get("chart/", page_size=500, columns=["id", "slice_name", "dashboards.id"])["result"]:
        en_tablero = any(d["id"] == DASHBOARD_ID for d in c.get("dashboards", []))
        if c["id"] not in nuevos and en_tablero:
            nombre = c["slice_name"] if c["slice_name"].startswith("[Archivado]") else f"[Archivado] {c['slice_name']}"
            ss.put(f"chart/{c['id']}", {"slice_name": nombre, "dashboards": []})
            print(f"archivado {c['id']}: {nombre}")


def permisos_datasets(ss, ds):
    """
    Public (tablero embebido, anónimo): lectura SOLO de los datasets del tablero.
    Alpha (usuario claude_api de la API): se le AGREGA lectura de estos datasets, sin quitarle nada;
    Superset solo le muestra un tablero si puede leer algún dataset de sus gráficos.
    """
    roles = {r["name"]: r["id"] for r in ss.s.get(f"{BASE}/api/v1/security/roles/?q=(page_size:50)").json()["result"]}
    todos, page = [], 0
    while True:
        rr = ss.s.get(f"{BASE}/api/v1/security/permissions-resources/", params={"q": json.dumps({"page_size": 100, "page": page})}).json()
        todos += rr["result"]
        page += 1
        if len(todos) >= rr["count"] or not rr["result"]:
            break
    acceso_ds = {x["id"]: x["view_menu"]["name"] for x in todos if x["permission"]["name"] == "datasource_access"}
    permitidos = {pid for pid, nombre in acceso_ds.items() if any(nombre.endswith(f"(id:{i})") for i in ds.values())}
    if len(permitidos) != len(ds):
        raise RuntimeError(f"No se encontraron los permisos datasource_access de todos los datasets: {permitidos}")
    for rol, solo_estos in (("Public", True), ("Alpha", False)):
        actuales = ss.s.get(f"{BASE}/api/v1/security/roles/{roles[rol]}/permissions/").json()["result"]
        base = [p["id"] for p in actuales if not (solo_estos and p["permission_name"] == "datasource_access")]
        nuevos = sorted(set(base) | permitidos)
        ss.post(f"security/roles/{roles[rol]}/permissions", {"permission_view_menu_ids": nuevos})
        print(f"rol {rol}: lectura de datasets {sorted(ds.values())} ({len(actuales)} → {len(nuevos)} permisos)")


if __name__ == "__main__":
    ss = Superset()
    ds = asegurar_datasets(ss)
    # Primero los permisos: el usuario de la API (Alpha) y el público solo ven datasets, gráficos y
    # tableros cuyos datos pueden leer; sin esto, los datasets nuevos dan 404 en los pasos siguientes.
    permisos_datasets(ss, ds)
    g = asegurar_graficos(ss, ds)
    nombrar_columnas(ss, ds)
    archivar_anteriores(ss, g)
    actualizar_tablero(ss, g, ds)
