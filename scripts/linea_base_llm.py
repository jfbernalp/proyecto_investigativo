"""
E6 · Línea base con LLM para la extracción (Artículo 1, hito 56; #217, #238, #242, B30).

El LLM recibe lo mismo que las personas anotadoras: la guía de anotación (secciones 1–4) y, por oferta, el título
y el texto enmascarado de anotador_A.xlsx. Devuelve rol, años mínimos, nivel y habilidades con la misma lista de
columnas. Se compara contra la misma referencia que el sistema de reglas (evaluar_anotacion.cargar_referencia).

    python scripts/linea_base_llm.py                 plan: cuántas llamadas y tamaño del prompt (NO llama a Gemini)
    python scripts/linea_base_llm.py --ejecutar      llama a Gemini (cuesta dinero y envía los 200 textos
                                                     enmascarados a Google: requiere autorización de Juan)
    python scripts/linea_base_llm.py --evaluar       compara con la referencia (cuando estén las planillas)

Reanudable: cada oferta se guarda en data/evaluacion_ia/e6/<modelo>/<id_muestra>.json (fuera de git).
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import evaluar_anotacion as ev  # noqa: E402

SALIDA = ROOT_DIR / "data" / "evaluacion_ia" / "e6"
GUIA = ROOT_DIR / "docs" / "articulo" / "guia_anotacion.md"


def instrucciones() -> str:
    guia = GUIA.read_text(encoding="utf-8")
    secciones = guia[guia.index("## 1. Reglas generales"):guia.index("## 5. Acuerdo")]
    # Las reglas de logística (tiempo, columnas grises) no aplican al modelo
    secciones = re.sub(r"\n5\. \*\*No modifique.*?\n6\. \*\*Tiempo estimado:.*?\n(?=\n)", "\n", secciones, flags=re.DOTALL)
    columnas = [ev.EXCEL_CUALQUIER if h == "Excel Avanzado" else h for h in ev.HABILIDADES]
    return f"""Eres una persona anotadora experta. Sigue esta guía de anotación al pie de la letra:

{secciones}

Responde SOLO un objeto JSON con estas claves:
- "rol": uno de {json.dumps(ev.ROLES, ensure_ascii=False)}
- "anios_minimos": número o null (si la oferta no lo dice)
- "nivel": uno de {json.dumps(ev.NIVELES, ensure_ascii=False)}
- "habilidades": lista con los nombres EXACTOS de las columnas que la oferta pide, elegidos de
  {json.dumps(columnas, ensure_ascii=False)}
- "excel_avanzado_explicito": true o false
"""


def ofertas() -> pd.DataFrame:
    ws = load_workbook(ev.CARPETA / "anotador_A.xlsx", read_only=True)["anotacion"]
    filas = list(ws.iter_rows(values_only=True))
    df = pd.DataFrame(filas[1:], columns=filas[0])
    return df[["id_muestra", "titulo", "texto"]].dropna(subset=["id_muestra"]).set_index("id_muestra")


def llamar(cliente, modelo: str, prompt: str) -> str:
    from google.genai import types as gt
    config = gt.GenerateContentConfig(
        temperature=0, response_mime_type="application/json", thinking_config=gt.ThinkingConfig(thinking_level="low"),
        http_options=gt.HttpOptions(timeout=180_000, retry_options=gt.HttpRetryOptions(
            attempts=3, initial_delay=5, max_delay=60, http_status_codes=[429, 500, 503, 504])))
    return (cliente.models.generate_content(model=modelo, contents=prompt, config=config).text or "").strip()


def ejecutar(modelo: str, limite):
    import os
    from google import genai
    from src.ai_curriculum.curriculum_engine import cargar_variables_entorno
    cargar_variables_entorno()
    cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    carpeta = SALIDA / modelo
    carpeta.mkdir(parents=True, exist_ok=True)
    base = instrucciones()
    for idm, r in list(ofertas().iterrows())[:limite]:
        destino = carpeta / f"{idm}.json"
        if destino.exists():
            continue
        t0 = time.time()
        registro = {"id_muestra": idm, "modelo": modelo}
        try:
            texto = llamar(cliente, modelo, f"{base}\nTÍTULO: {r.titulo}\n\nTEXTO DE LA OFERTA:\n{r.texto}")
            registro.update({"respuesta": texto, "json": json.loads(texto)})
        except Exception as e:
            registro["error"] = f"{type(e).__name__}: {e}"
        registro["segundos"] = round(time.time() - t0, 1)
        destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {idm}: {registro.get('error') or 'ok'} ({registro['segundos']} s)")


def predicciones(modelo: str) -> pd.DataFrame:
    """Mismo formato que evaluar_anotacion.predicciones_sistema (columnas pub:: y rec:: iguales)."""
    columna_a_habilidad = {ev.EXCEL_CUALQUIER if h == "Excel Avanzado" else h: h for h in ev.HABILIDADES}
    filas = []
    for f in sorted((SALIDA / modelo).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        j = d.get("json") or {}
        habs = {columna_a_habilidad[h] for h in j.get("habilidades", []) if h in columna_a_habilidad}
        anios = j.get("anios_minimos")
        fila = {"id_muestra": d["id_muestra"], "valida": "json" in d,
                "rol": j.get("rol") if j.get("rol") in ev.ROLES else "Otro rol",
                "relevante": j.get("rol") != "No es del tema",
                "nivel": j.get("nivel") if j.get("nivel") in ev.NIVELES else "No se indica",
                "anios": float(anios) if isinstance(anios, (int, float)) else np.nan,
                "excel_explicito": int(bool(j.get("excel_avanzado_explicito")))}
        for h in ev.HABILIDADES:
            fila[f"pub::{h}"] = fila[f"rec::{h}"] = int(h in habs)
        filas.append(fila)
    return pd.DataFrame(filas).set_index("id_muestra")


def evaluar(modelo: str):
    _, _, gold, problemas = ev.cargar_referencia()
    gold = gold[gold["rol"] != ""]
    if gold.empty:
        print("Las planillas están vacías: no hay referencia todavía."); return
    pred = predicciones(modelo)
    r = ev.evaluar(gold, pred, 2000, np.random.default_rng(2026))
    r["respuestas_invalidas"] = int((~pred["valida"]).sum())
    r["excel_explicito_llm"] = dict(zip(("precision", "recall", "f1"), map(ev.r3, ev.prf(*ev.conteos(
        gold.loc[gold.index.intersection(pred.index), "Excel avanzado explícito"].to_numpy(),
        pred.loc[gold.index.intersection(pred.index), "excel_explicito"].to_numpy())))))
    salida = ROOT_DIR / "data" / "evaluacion_ia" / f"e6_resultados_{modelo}.json"
    salida.write_text(json.dumps(r, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    m = r["habilidades_publicado"]["micro"]
    print(f"{modelo} · {r['n_ofertas']} ofertas · habilidades P {m['precision']} R {m['recall']} F1 {m['f1']} {m['ic95_f1']}"
          f" · rol exactitud {r['rol']['exactitud']} · inválidas {r['respuestas_invalidas']} → {salida}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="gemini-4-argon")
    ap.add_argument("--ejecutar", action="store_true", help="llamar a Gemini (cuesta dinero; requiere autorización)")
    ap.add_argument("--evaluar", action="store_true")
    ap.add_argument("--limite", type=int, default=None, help="solo las primeras N ofertas (prueba piloto)")
    a = ap.parse_args()
    if a.evaluar:
        evaluar(a.modelo)
    elif a.ejecutar:
        ejecutar(a.modelo, a.limite)
    else:
        o = ofertas()
        largo = o["texto"].fillna("").str.len()
        print(f"{len(o)} ofertas → {len(o) if a.limite is None else a.limite} llamadas a {a.modelo}")
        print(f"prompt base: {len(instrucciones()):,} caracteres; texto por oferta: mediana {int(largo.median()):,}, "
              f"máximo {int(largo.max()):,}")
        print("Plan solamente: no se llamó a Gemini. Use --ejecutar (con autorización).")


if __name__ == "__main__":
    main()
