"""
Evaluación del componente de IA del Artículo 1 (hito 56): E4 (verificador de cifras) y E5 (anclaje y modelo).

E4 · ¿El verificador marca bien las cifras?
    e4-planilla   Toma las versiones vigentes de las propuestas y lista TODOS los números de sus textos (no solo los
                  que el verificador revisa, para poder medir lo que se le escapa). Muestra estratificada:
                  todas las cifras marcadas + muestra de las revisadas sin marca + muestra de las no revisadas.
                  Planilla CIEGA (no dice qué marcó el verificador) en data/evaluacion_ia/e4_cifras.xlsx, con una
                  hoja con el contexto de mercado para consultar. La clave va aparte (e4_clave.csv).
    e4-evaluar    Lee la planilla etiquetada y calcula, ponderando por estrato: % de cifras de mercado respaldadas,
                  precisión y recall de las marcas, y cobertura (qué parte de las cifras de mercado revisa).

E5 · ¿Anclar en el contexto reduce las cifras sin respaldo? ¿Argon mejor que Flash?
    e5            Diseño 2×2 (con / sin contexto × modelo) con repeticiones (los LLM no son deterministas).
                  Sin --ejecutar solo muestra el plan y el tamaño de los prompts: NO llama a Gemini.
                  Con --ejecutar llama a Gemini (cuesta dinero: requiere autorización de Juan). Cada modelo se llama
                  sin respaldo (un fallo no se reemplaza con otro modelo). Nunca toca el portafolio del portal.
    e5-resumen    Cifras revisadas y marcadas por el verificador en cada condición, con IC 95 % por bootstrap.

«Sin contexto» quita del prompt los datos del observatorio y las reglas de evidencia (un LLM sin anclaje);
todo lo demás (contexto institucional, encargo, esquema) es idéntico. Ambas condiciones se verifican contra el
mismo contexto. Las tasas automáticas de E5 se leen junto con la precisión y el recall medidos en E4.

Salidas en data/evaluacion_ia/ (fuera de git: contenido curricular institucional y texto generado).
Uso:  python scripts/evaluacion_ia.py e4-planilla | e4-evaluar | e5 [--ejecutar] [--reps 3] | e5-resumen
"""
import argparse
import glob
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ai_curriculum import verificador_cifras as vc  # noqa: E402
from src.ai_curriculum.contexto_mercado import cargar_contexto  # noqa: E402
from src.ai_curriculum.curriculum_schemas import PropuestaPrograma  # noqa: E402

CARPETA = ROOT_DIR / "data" / "evaluacion_ia"
VERSIONES = ROOT_DIR / "data" / "curriculo_unicafam" / "versiones"
SEMILLA = 2026
NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
ES_MERCADO = ["Sí", "No"]
RESPALDO = ["Respaldada", "Mal atribuida", "Sin respaldo", "No verificable"]
PROBLEMA = {"Mal atribuida", "Sin respaldo"}

MODELOS_E5 = ["gemini-4-argon", "gemini-3.8-flash"]
SOLICITUDES_E5 = [
    {"tipo_propuesta": "Diplomado", "nivel_academico": "Educación Continua", "creditos": 8,
     "enfoque": "Ingeniería de datos en la nube", "notas": ""},
    {"tipo_propuesta": "Microcredencial / Certificación Corta", "nivel_academico": "Educación Continua",
     "creditos": 2, "enfoque": "", "notas": ""},
]
BLOQUE_DATOS = re.compile(r"=+\nDATOS DEL OBSERVATORIO LABORAL.*?(?==+\nFOCO ESTRATÉGICO)", re.DOTALL)


# --------------------------------------------------------------------------- E4

def versiones_vigentes():
    ultima = {}
    for f in glob.glob(str(VERSIONES / "PROP_*_v*.json")):
        pid, v = re.match(r".*(PROP_\d+)_v(\d+)\.json$", f).groups()
        if int(v) > ultima.get(pid, (0, None))[0]:
            ultima[pid] = (int(v), Path(f))
    return {pid: PropuestaPrograma(**json.loads(f.read_text(encoding="utf-8"))) for pid, (_, f) in sorted(ultima.items())}


def _verificar(propuesta: PropuestaPrograma, contexto: dict):
    from src.ai_curriculum.gap_analyzer import contexto_para_verificar
    return vc.verificar_propuesta(propuesta, contexto_para_verificar(contexto))


def cifras_de_propuesta(pid: str, propuesta: PropuestaPrograma, verificacion) -> list:
    """
    Cada número de los textos, con su estrato: «marcada» (el verificador la marcó), «revisada» (la revisó y la dio
    por respaldada) o «no revisada» (no coincide con sus patrones de %, dinero o conteo de ofertas).
    """
    marcadas = {}
    for h in verificacion.sin_respaldo:
        if h.tipo != "consistencia":
            marcadas.setdefault(h.campo, []).append(h.cifra)
    filas = []
    for campo, texto in vc._textos(propuesta.model_dump()):
        revisadas = []
        for patron in (vc.RE_DINERO_MILLONES, vc.RE_DINERO, vc.RE_PORCENTAJE, vc.RE_CONTEO):
            for m in patron.finditer(texto):
                if not any(a <= m.start() < b or a < m.end() <= b for a, b, _ in revisadas):
                    revisadas.append((m.start(), m.end(), m.group(0).strip()))
        pendientes = list(marcadas.get(campo, []))
        marcado_span = set()
        for a, b, cifra in sorted(revisadas):
            if cifra in pendientes:
                pendientes.remove(cifra)
                marcado_span.add((a, b))
        for m in NUMERO.finditer(texto):
            span = next(((a, b) for a, b, _ in revisadas if a <= m.start() < b), None)
            estrato = "no revisada" if span is None else ("marcada" if span in marcado_span else "revisada")
            filas.append({"propuesta": pid, "campo": campo, "cifra": m.group(0), "estrato": estrato,
                          "fragmento": vc._fragmento(texto, m.start(), m.end(), margen=90)})
    return filas


def e4_planilla(n_revisadas: int, n_no_revisadas: int):
    rng = np.random.default_rng(SEMILLA)
    propuestas = versiones_vigentes()
    filas, contextos = [], {}
    for pid, p in propuestas.items():
        ctx = contextos.setdefault(p.contexto_id, cargar_contexto(p.contexto_id))
        filas += cifras_de_propuesta(pid, p, _verificar(p, ctx))
    df = pd.DataFrame(filas)
    tamanos = df["estrato"].value_counts().to_dict()
    partes = [df[df.estrato == "marcada"]]
    for estrato, n in (("revisada", n_revisadas), ("no revisada", n_no_revisadas)):
        g = df[df.estrato == estrato]
        partes.append(g.sample(n=min(n, len(g)), random_state=int(rng.integers(1e9))))
    muestra = pd.concat(partes).sample(frac=1, random_state=int(rng.integers(1e9))).reset_index(drop=True)
    muestra["id_cifra"] = [f"C{i + 1:03d}" for i in range(len(muestra))]

    CARPETA.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "cifras"
    columnas = ["id_cifra", "propuesta", "campo", "cifra", "fragmento", "es_cifra_de_mercado", "respaldo", "comentario"]
    ws.append(columnas)
    for _, r in muestra.iterrows():
        ws.append([r.id_cifra, r.propuesta, r.campo, r.cifra, r.fragmento, None, None, None])
    for i in range(1, len(columnas) + 1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="E8EDF3" if i <= 5 else "FFF4D6")
    for letra, ancho in zip("ABCDEFGH", (9, 10, 28, 12, 90, 14, 16, 40)):
        ws.column_dimensions[letra].width = ancho
    for fila in ws.iter_rows(min_row=2):
        fila[4].alignment = Alignment(wrap_text=True, vertical="top")
    for col, opciones in (("F", ES_MERCADO), ("G", RESPALDO)):
        dv = DataValidation(type="list", formula1='"' + ",".join(opciones) + '"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{len(muestra) + 1}")
    ws.freeze_panes = "F2"
    # Contexto de mercado aplanado: ruta → valor, para buscar cada cifra
    hc = wb.create_sheet("contexto")
    hc.append(["contexto_id", "dato", "valor"])
    for cid, ctx in contextos.items():
        for ruta, valor in _aplanar({k: v for k, v in ctx.items() if k != "prioridades_de_evidencia"}):
            hc.append([cid, ruta, str(valor)])
    hc.column_dimensions["B"].width = 90
    hc.column_dimensions["C"].width = 30
    guia = wb.create_sheet("instrucciones")
    for linea in [
        "Una fila por número que aparece en una propuesta generada por la IA. Trabaje sin mirar las marcas del portal.",
        "es_cifra_de_mercado: Sí si es un dato del mercado laboral (% de ofertas, n de ofertas, salario, prima, IC).",
        "  No si es institucional o retórico (créditos, horas, semestres, decreto, fechas, «Python 3», numeración).",
        "respaldo (solo si es de mercado), comparando con la hoja «contexto» del mismo contexto_id:",
        "  Respaldada: el número está en el contexto y se atribuye al dato correcto (habilidad, rol, mes).",
        "  Mal atribuida: el número está en el contexto, pero es de otra habilidad, rol o mes.",
        "  Sin respaldo: no está en el contexto (inventada, calculada o redondeada de forma que cambia el dato).",
        "  No verificable: el texto no permite saber a qué dato se refiere.",
        "comentario: dudas. Tiempo estimado: ~30 s por fila.",
    ]:
        guia.append([linea])
    guia.column_dimensions["A"].width = 120
    wb.save(CARPETA / "e4_cifras.xlsx")
    muestra[["id_cifra", "propuesta", "campo", "cifra", "estrato"]].to_csv(CARPETA / "e4_clave.csv", index=False)
    (CARPETA / "e4_estratos.json").write_text(json.dumps({"poblacion": tamanos, "semilla": SEMILLA,
                                                          "propuestas": {pid: p.contexto_id for pid, p in propuestas.items()}},
                                                         ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"propuestas: {list(propuestas)} | números en sus textos por estrato: {tamanos}")
    print(f"muestra: {muestra.estrato.value_counts().to_dict()} → {CARPETA / 'e4_cifras.xlsx'}")


def _aplanar(obj, ruta=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _aplanar(v, f"{ruta}.{k}" if ruta else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            nombre = next((v.get(k) for k in ("habilidad", "rol", "mercado", "nombre") if isinstance(v, dict) and v.get(k)), i)
            yield from _aplanar(v, f"{ruta}[{nombre}]")
    else:
        yield ruta, obj


def metricas_e4(df: pd.DataFrame, pesos: dict) -> dict:
    """df: id_cifra, estrato, es_cifra_de_mercado, respaldo. pesos: estrato → tamaño poblacional / tamaño muestral."""
    w = df["estrato"].map(pesos).astype(float)
    mercado = df["es_cifra_de_mercado"] == "Sí"
    problema = mercado & df["respaldo"].isin(PROBLEMA)
    marcada = df["estrato"] == "marcada"
    revisada = df["estrato"] != "no revisada"
    suma = lambda m: float((w * m).sum())
    div = lambda a, b: round(a / b, 3) if b else None
    return {
        "cifras_de_mercado_estimadas": round(suma(mercado), 1),
        "pct_respaldadas": div(suma(mercado & (df["respaldo"] == "Respaldada")), suma(mercado)),
        "pct_problema": div(suma(problema), suma(mercado)),
        "precision_marcas": div(suma(problema & marcada), suma(marcada & mercado)),
        "recall_marcas": div(suma(problema & marcada), suma(problema)),
        "cobertura_revision": div(suma(mercado & revisada), suma(mercado)),
    }


def e4_evaluar(reps: int):
    clave = pd.read_csv(CARPETA / "e4_clave.csv")
    wb = load_workbook(CARPETA / "e4_cifras.xlsx", data_only=True)
    filas = list(wb["cifras"].iter_rows(values_only=True))
    etiquetas = pd.DataFrame(filas[1:], columns=filas[0])[["id_cifra", "es_cifra_de_mercado", "respaldo"]]
    df = clave.merge(etiquetas, on="id_cifra")
    faltan = df[df.es_cifra_de_mercado.isna() | ((df.es_cifra_de_mercado == "Sí") & df.respaldo.isna())]
    if len(faltan):
        print(f"[AVISO] {len(faltan)} filas sin etiquetar o sin respaldo; se excluyen: {faltan.id_cifra.tolist()[:10]}…")
        df = df.drop(faltan.index)
    poblacion = json.loads((CARPETA / "e4_estratos.json").read_text(encoding="utf-8"))["poblacion"]
    pesos = {e: poblacion.get(e, 0) / n for e, n in df["estrato"].value_counts().items()}
    res = {"n_etiquetadas": int(len(df)), "por_estrato": df["estrato"].value_counts().to_dict(), **metricas_e4(df, pesos)}
    rng = np.random.default_rng(SEMILLA)
    boot = []
    for _ in range(reps):      # bootstrap estratificado
        b = pd.concat([g.sample(n=len(g), replace=True, random_state=int(rng.integers(1e9))) for _, g in df.groupby("estrato")])
        boot.append(metricas_e4(b, pesos))
    for k in ("pct_respaldadas", "pct_problema", "precision_marcas", "recall_marcas", "cobertura_revision"):
        v = [b[k] for b in boot if b[k] is not None]
        res[f"{k}_ic95"] = [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)] if v else None
    (CARPETA / "e4_resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------- E5

def prompt_e5(engine, contexto: dict, solicitud: dict, con_contexto: bool) -> str:
    from src.ai_curriculum.curriculum_engine import encargo_propuesta_individual
    datos = engine.gap_analyzer.calcular_matriz_brechas(contexto)
    prompt = engine._construir_prompt_contextual(datos, contexto, encargo_propuesta_individual(solicitud, "evaluacion", "experimento"))
    if not con_contexto:
        prompt, n = BLOQUE_DATOS.subn("=" * 70 + "\nDATOS DE MERCADO: no se proporcionan.\n", prompt)
        assert n == 1, "No se encontró el bloque de datos del observatorio en el prompt"
    return prompt


def _llamar(engine, modelo: str, prompt: str):
    """Una llamada a un modelo fijo, sin respaldo: en un experimento un fallo no se reemplaza por otro modelo."""
    from google.genai import types as gt
    from src.ai_curriculum.curriculum_engine import TIMEOUT_GEMINI_MS
    config = gt.GenerateContentConfig(
        thinking_config=gt.ThinkingConfig(thinking_level="low"), response_mime_type="application/json",
        http_options=gt.HttpOptions(timeout=TIMEOUT_GEMINI_MS, retry_options=gt.HttpRetryOptions(
            attempts=3, initial_delay=5, max_delay=60, http_status_codes=[500, 503, 504])))
    r = engine.client.models.generate_content(model=modelo, contents=prompt, config=config)
    return (r.text or "").strip(), getattr(r, "model_version", None) or modelo


def e5(ejecutar: bool, reps: int, modelos, n_solicitudes: int):
    from src.ai_curriculum.contexto_mercado import obtener_contexto_vigente
    from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine, extraer_json_robusto
    engine = CurriculumIntelligenceEngine()
    contexto = obtener_contexto_vigente()
    salida = CARPETA / "e5"
    plan = [(s_i, sol, cc, mod, r) for s_i, sol in enumerate(SOLICITUDES_E5[:n_solicitudes])
            for cc in (True, False) for mod in modelos for r in range(1, reps + 1)]
    print(f"contexto {contexto['id']} (corte {contexto['ultimo_corte']}) | {len(plan)} llamadas: "
          f"{n_solicitudes} solicitudes × 2 condiciones × {len(modelos)} modelos × {reps} repeticiones")
    for s_i, sol in enumerate(SOLICITUDES_E5[:n_solicitudes]):
        for cc in (True, False):
            p = prompt_e5(engine, contexto, sol, cc)
            print(f"  solicitud {s_i + 1} ({sol['tipo_propuesta']}), {'con' if cc else 'sin'} contexto: {len(p):,} caracteres")
    if not ejecutar:
        print("Plan solamente: no se llamó a Gemini. Use --ejecutar (con autorización) para correrlo.")
        return
    salida.mkdir(parents=True, exist_ok=True)
    for s_i, sol, cc, mod, r in plan:
        nombre = f"s{s_i + 1}_{'con' if cc else 'sin'}_{mod}_r{r}.json"
        if (salida / nombre).exists():
            continue                                    # reanudable
        prompt = prompt_e5(engine, contexto, sol, cc)
        registro = {"solicitud": sol, "con_contexto": cc, "modelo_pedido": mod, "repeticion": r,
                    "contexto_id": contexto["id"], "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "fecha": datetime.now().isoformat(timespec="seconds")}
        t0 = time.time()
        try:
            texto, modelo = _llamar(engine, mod, prompt)
            registro.update({"modelo_respuesta": modelo, "segundos": round(time.time() - t0, 1), "respuesta": texto})
            datos = extraer_json_robusto(texto)
            props = datos.get("propuestas") if isinstance(datos.get("propuestas"), list) else [datos]
            propuesta = PropuestaPrograma.model_validate(props[0])
            propuesta.creditos_totales, propuesta.horas_totales = int(sol["creditos"]), int(sol["creditos"]) * 48
            ver = _verificar(propuesta, contexto)
            registro.update({"propuesta": propuesta.model_dump(mode="json"), "verificacion": ver.model_dump(mode="json")})
        except Exception as e:                          # se registra: la tasa de fallos también es un resultado
            registro.update({"error": f"{type(e).__name__}: {e}", "segundos": round(time.time() - t0, 1)})
        (salida / nombre).write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {nombre}: {registro.get('error') or str(len(registro['verificacion']['sin_respaldo'])) + ' marcadas'}")


def e5_resumen(reps: int):
    filas = []
    for f in sorted((CARPETA / "e5").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        v = d.get("verificacion") or {}
        marcas = [h for h in v.get("sin_respaldo", []) if h["tipo"] != "consistencia"]
        filas.append({"condicion": f"{'con' if d['con_contexto'] else 'sin'} contexto · {d['modelo_pedido']}",
                      "solicitud": d["solicitud"]["tipo_propuesta"], "ok": "error" not in d,
                      "revisadas": v.get("cifras_revisadas", 0), "marcadas": len(marcas),
                      "inconsistencias": sum(h["tipo"] == "consistencia" for h in v.get("sin_respaldo", [])),
                      "segundos": d.get("segundos")})
    df = pd.DataFrame(filas)
    rng = np.random.default_rng(SEMILLA)
    res = {}
    for cond, g in df.groupby("condicion"):
        ok = g[g.ok]
        tasa = lambda x: x["marcadas"].sum() / x["revisadas"].sum() if x["revisadas"].sum() else np.nan
        boot = [tasa(ok.sample(len(ok), replace=True, random_state=int(rng.integers(1e9)))) for _ in range(reps)] if len(ok) else []
        res[cond] = {"generaciones": int(len(g)), "fallidas": int((~g.ok).sum()),
                     "cifras_revisadas": int(ok.revisadas.sum()), "cifras_marcadas": int(ok.marcadas.sum()),
                     "tasa_marcadas": None if not len(ok) else round(float(tasa(ok)), 3),
                     "tasa_marcadas_ic95": None if not boot else [round(float(np.nanpercentile(boot, q)), 3) for q in (2.5, 97.5)],
                     "con_inconsistencias_de_creditos": int((ok.inconsistencias > 0).sum()),
                     "segundos_mediana": None if not len(ok) else float(ok.segundos.median())}
    (CARPETA / "e5_resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["e4-planilla", "e4-evaluar", "e5", "e5-resumen"])
    ap.add_argument("--revisadas", type=int, default=100, help="E4: muestra de cifras revisadas sin marca")
    ap.add_argument("--no-revisadas", type=int, default=50, help="E4: muestra de números que el verificador no revisa")
    ap.add_argument("--reps", type=int, default=3, help="E5: repeticiones por condición")
    ap.add_argument("--solicitudes", type=int, default=1, choices=[1, 2])
    ap.add_argument("--modelos", nargs="+", default=MODELOS_E5)
    ap.add_argument("--ejecutar", action="store_true", help="E5: llamar a Gemini (cuesta dinero)")
    a = ap.parse_args()
    if a.accion == "e4-planilla":
        e4_planilla(a.revisadas, a.no_revisadas)
    elif a.accion == "e4-evaluar":
        e4_evaluar(reps=2000)
    elif a.accion == "e5":
        e5(a.ejecutar, a.reps, a.modelos, a.solicitudes)
    else:
        e5_resumen(reps=2000)


if __name__ == "__main__":
    main()
