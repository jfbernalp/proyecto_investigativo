"""
Muestra estratificada de ofertas para etiquetado manual (conjunto de referencia del Artículo 1).

- 200 ofertas únicas, estratificadas por portal y mes (asignación proporcional, con un mínimo por portal).
- Anotador A etiqueta las 200; anotador B etiqueta un subconjunto de 60 para medir el acuerdo.
- **Etiquetado ciego**: las planillas no muestran lo que detectó el sistema.
- Correos y teléfonos enmascarados en el texto.
- Salida en data/anotacion/ (fuera de git: contiene el texto de las ofertas y el repositorio es público).

Solo lectura en la base. Semilla fija: la muestra es reproducible.

Uso:  python scripts/muestra_anotacion.py [--n 200] [--doble 60] [--semilla 2026]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db_manager import DATABASE_URL, normalizar_url_bd  # noqa: E402
from src.processing.taxonomies import TAXONOMIA_HABILIDADES  # noqa: E402

SALIDA = ROOT_DIR / "data" / "anotacion"
MIN_POR_PORTAL = 5
EXCEL_CUALQUIER_NIVEL = "Excel u hojas de cálculo (cualquier nivel)"
EXCEL_AVANZADO_EXPLICITO = "Excel AVANZADO (lo dice explícitamente)"
ROLES = ["Científico de Datos", "Analista de Datos", "Ingeniero de Datos", "Machine Learning / AI Engineer",
         "Analista de BI y Visualización", "Desarrollador de Software / Datos", "Otro rol", "No es del tema"]
NIVELES = ["Junior", "Semi-Senior", "Senior", "Líder", "No se indica"]
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# Solo formatos telefónicos reales: celular colombiano (3xx), fijo (60x) y números con prefijo internacional.
# Un patrón más amplio enmascaraba salarios («3.500.000») y códigos de oferta de 10 dígitos que empiezan por 18.
TELEFONO = re.compile(r"(?<![\d.])(?:\+57[\s.-]?)?(?:3\d{2}|60\d)[\s.-]?\d{3}[\s.-]?\d{4}(?![\d.])"
                      r"|\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?![\d.])")


def enmascarar(t: str) -> str:
    t = CORREO.sub("[CORREO]", t)
    return TELEFONO.sub("[TELÉFONO]", t)


def cargar(engine) -> pd.DataFrame:
    df = pd.read_sql_query(text("""
        SELECT DISTINCT ON (r.id_vacante_hash) r.id_vacante_hash, r.mes_periodo, d.portal, r.payload_json
        FROM ofertas_raw_historico r JOIN dim_ofertas d USING (id_vacante_hash)
        ORDER BY r.id_vacante_hash, r.mes_periodo DESC"""), engine)
    cargas = df["payload_json"].apply(json.loads)
    df["titulo"] = cargas.apply(lambda d: str(d.get("Nombre Oferta") or ""))
    df["texto"] = cargas.apply(lambda d: "\n\n".join(str(d.get(k)) for k in ("Requisitos", "Descripcion", "Descripcion_detalle")
                                                   if d.get(k) and str(d.get(k)).strip() not in ("", "nan", "None")))
    return df.drop(columns=["payload_json"])


def estratificar(df: pd.DataFrame, n: int, rng) -> pd.DataFrame:
    estratos = df.groupby(["portal", "mes_periodo"]).size()
    cuota = (estratos / estratos.sum() * n).round().astype(int).clip(lower=1)
    por_portal = cuota.groupby(level=0).sum()
    for portal, total in por_portal.items():             # mínimo por portal, si hay ofertas suficientes
        faltan = min(MIN_POR_PORTAL, int(estratos[portal].sum())) - total
        if faltan > 0:
            mayor = estratos[portal].idxmax()
            cuota[(portal, mayor)] += faltan
    partes = []
    for (portal, mes), k in cuota.items():
        grupo = df[(df.portal == portal) & (df.mes_periodo == mes)]
        partes.append(grupo.sample(n=min(k, len(grupo)), random_state=int(rng.integers(1e9))))
    muestra = pd.concat(partes)
    if len(muestra) > n:                                  # el redondeo puede pasarse: recortar al azar
        muestra = muestra.sample(n=n, random_state=int(rng.integers(1e9)))
    return muestra.sample(frac=1, random_state=int(rng.integers(1e9))).reset_index(drop=True)


def planilla(muestra: pd.DataFrame, ruta: Path, anotador: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "anotacion"
    habilidades = list(TAXONOMIA_HABILIDADES)
    # La regla «Excel Avanzado» del sistema detecta cualquier mención de Excel: se etiqueta así (cualquier nivel) y
    # aparte si la oferta pide explícitamente Excel avanzado, para poder evaluar las dos lecturas
    encabezados = [EXCEL_CUALQUIER_NIVEL if h == "Excel Avanzado" else h for h in habilidades]
    columnas = (["id_muestra", "portal", "mes", "titulo", "texto", "rol", "anios_minimos", "nivel"] + encabezados
                + [EXCEL_AVANZADO_EXPLICITO, "otras_habilidades", "comentario"])
    ws.append(columnas)
    for _, r in muestra.iterrows():
        ws.append([r.id_muestra, r.portal, str(r.mes_periodo), r.titulo, enmascarar(r.texto)[:32000], None, None, None]
                  + [None] * (len(habilidades) + 1) + [None, None])
    gris, amarillo = PatternFill("solid", fgColor="E8EDF3"), PatternFill("solid", fgColor="FFF4D6")
    for i, nombre in enumerate(columnas, 1):
        celda = ws.cell(row=1, column=i)
        celda.font = Font(bold=True)
        celda.fill = gris if i <= 5 else amarillo
        celda.alignment = Alignment(wrap_text=True, vertical="top",
                                    text_rotation=90 if (nombre in encabezados or nombre == EXCEL_AVANZADO_EXPLICITO) else 0)
    ws.row_dimensions[1].height = 150
    for letra, ancho in (("A", 11), ("B", 13), ("C", 8), ("D", 40), ("E", 90), ("F", 26), ("G", 9), ("H", 13)):
        ws.column_dimensions[letra].width = ancho
    for fila in ws.iter_rows(min_row=2):
        for celda in fila[:5]:
            celda.alignment = Alignment(wrap_text=True, vertical="top")
    ultima = len(muestra) + 1
    def lista(col, opciones):
        dv = DataValidation(type="list", formula1='"' + ",".join(opciones) + '"', allow_blank=True)
        ws.add_data_validation(dv); dv.add(f"{col}2:{col}{ultima}")
    lista("F", ROLES)
    lista("H", NIVELES)
    from openpyxl.utils import get_column_letter
    for j in range(9, 9 + len(habilidades) + 1):
        lista(get_column_letter(j), ["1"])
    ws.freeze_panes = "F2"
    guia = wb.create_sheet("instrucciones")
    for linea in [f"Anotador {anotador}. Lea la guía completa en docs/articulo/guia_anotacion.md antes de empezar.",
                  "Trabaje solo, sin consultar a la otra persona ni los resultados del sistema.",
                  "rol y nivel: elija de la lista. anios_minimos: número, solo si la oferta lo dice; si no, deje vacío.",
                  "Habilidades: escriba 1 si la oferta PIDE o MENCIONA como parte del trabajo esa habilidad; deje vacío si no.",
                  "otras_habilidades: habilidades técnicas importantes que no estén en las columnas (separadas por ;).",
                  "comentario: dudas o casos difíciles. No modifique las columnas grises."]:
        guia.append([linea])
    guia.column_dimensions["A"].width = 120
    wb.save(ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--doble", type=int, default=60)
    ap.add_argument("--semilla", type=int, default=2026)
    args = ap.parse_args()
    rng = np.random.default_rng(args.semilla)
    df = cargar(create_engine(normalizar_url_bd(DATABASE_URL)))
    muestra = estratificar(df, args.n, rng)
    muestra["id_muestra"] = [f"M{i + 1:03d}" for i in range(len(muestra))]
    doble = muestra.sample(n=min(args.doble, len(muestra)), random_state=int(rng.integers(1e9))).sort_values("id_muestra")
    SALIDA.mkdir(parents=True, exist_ok=True)
    planilla(muestra, SALIDA / "anotador_A.xlsx", "A")
    planilla(doble, SALIDA / "anotador_B.xlsx", "B")
    # Clave (no se entrega a los anotadores): vincula cada id_muestra con la oferta
    muestra[["id_muestra", "id_vacante_hash", "portal", "mes_periodo"]].assign(doble=muestra.id_muestra.isin(doble.id_muestra)) \
        .to_csv(SALIDA / "clave_muestra.csv", index=False)
    print(f"población: {len(df)} ofertas únicas | muestra: {len(muestra)} | doble anotación: {len(doble)} | semilla {args.semilla}")
    print("por portal (población → muestra):")
    comp = pd.DataFrame({"poblacion": df.portal.value_counts(), "muestra": muestra.portal.value_counts()}).fillna(0).astype(int)
    comp["% pob"] = (100 * comp.poblacion / comp.poblacion.sum()).round(1)
    comp["% muestra"] = (100 * comp.muestra / comp.muestra.sum()).round(1)
    print(comp.sort_values("poblacion", ascending=False).to_string())
    print("por mes (muestra):", muestra.mes_periodo.value_counts().sort_index().to_dict())
    print("textos con correo o teléfono enmascarado:", int(muestra.texto.apply(lambda t: enmascarar(t) != t).sum()))
    print(f"archivos en {SALIDA}")


if __name__ == "__main__":
    main()
