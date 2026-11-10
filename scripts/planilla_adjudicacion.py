"""
Planilla para adjudicar los desacuerdos entre el anotador A y el segundo anotador (C) en la submuestra doble (hito 65).

Copia la planilla del segundo anotador (mismo formato que lee evaluar_anotacion.leer_planilla) y llena cada fila con los
valores de A. Cada celda donde C dijo otra cosa queda en amarillo, con un comentario «A: … | C: …». Quien adjudica deja
o cambia el valor y, al terminar, renombra el archivo a `adjudicado.xlsx`: desde ese momento la referencia de E1, E2 y E6
usa esas 60 filas (las otras 140 siguen siendo las de A).

    python scripts/planilla_adjudicacion.py      → data/anotacion/adjudicacion_pendiente.xlsx (no sobrescribe)
"""
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import evaluar_anotacion as ev  # noqa: E402

DESTINO = ev.CARPETA / "adjudicacion_pendiente.xlsx"
CAMPOS = ["rol", "anios_minimos", "nivel"] + [ev.EXCEL_CUALQUIER if h == "Excel Avanzado" else h for h in ev.HABILIDADES] \
    + [ev.EXCEL_AVANZADO]
AMARILLO = PatternFill("solid", fgColor="FFF2A8")


def valores(ruta: Path):
    ws = load_workbook(ruta, data_only=True)["anotacion"]
    filas = list(ws.iter_rows(values_only=True))
    cab = [str(c) if c is not None else "" for c in filas[0]]
    return {str(f[0]): dict(zip(cab, f)) for f in filas[1:] if f[0]}


def normal(v):
    if v is None or str(v).strip() == "":
        return ""
    s = str(v).strip()
    return s[:-2] if s.endswith(".0") else s


def main():
    if DESTINO.exists():
        sys.exit(f"{DESTINO.name} ya existe: no se sobrescribe.")
    segundo = ev.segundo_anotador()
    origen = ev.CARPETA / f"anotador_{segundo}.xlsx"
    A, S = valores(ev.CARPETA / "anotador_A.xlsx"), valores(origen)
    wb = load_workbook(origen)
    ws = wb["anotacion"]
    cab = [c.value for c in ws[1]]
    col = {nombre: i + 1 for i, nombre in enumerate(cab)}
    celdas, ofertas = 0, set()
    for fila in range(2, ws.max_row + 1):
        idm = ws.cell(fila, col["id_muestra"]).value
        if not idm:
            continue
        a, s = A[str(idm)], S[str(idm)]
        for campo in CAMPOS + ["otras_habilidades", "comentario"]:
            ws.cell(fila, col[campo]).value = a.get(campo)
        for campo in CAMPOS:
            if normal(a.get(campo)) != normal(s.get(campo)):
                celda = ws.cell(fila, col[campo])
                celda.fill = AMARILLO
                celda.comment = Comment(f"A: {normal(a.get(campo)) or '(vacío)'} | {segundo}: {normal(s.get(campo)) or '(vacío)'}",
                                        "adjudicación")
                celdas += 1
                ofertas.add(idm)
        if s.get("comentario"):
            ws.cell(fila, col["comentario"]).value = f"A: {a.get('comentario') or ''} | {segundo}: {s.get('comentario')}"
    instr = wb["instrucciones"]
    instr.insert_rows(1, 3)
    instr["A1"] = ("ADJUDICACIÓN: cada celda amarilla es un desacuerdo entre A y " + segundo + " (el comentario muestra los "
                   "dos valores). Deje el valor de A o cámbielo según la guía. No toque las demás celdas.")
    instr["A2"] = "Al terminar, guarde y renombre este archivo a adjudicado.xlsx."
    wb.save(DESTINO)
    print(f"{DESTINO.relative_to(ROOT_DIR)}: {celdas} celdas en desacuerdo en {len(ofertas)} ofertas (A frente a {segundo})")


if __name__ == "__main__":
    main()
