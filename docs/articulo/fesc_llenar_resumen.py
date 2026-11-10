"""Llena FORMATO RESUMEN (FESC 2026) conservando estilos: reemplaza el texto de runs existentes."""
import re, sys
from xml.sax.saxutils import escape
sys.path.insert(0, sys.argv[2]); import textos_resumen as T

doc = sys.argv[1]
t = open(doc, encoding="utf-8").read()
TT = re.compile(r'(<w:t)(?: [^>]*)?>([^<]*)(</w:t>)')

def texto(p): return "".join(m.group(2) for m in TT.finditer(p))

def fijar(p, nuevos):
    """nuevos: {índice de run: texto}; los runs con texto fuera del dict quedan vacíos."""
    runs = list(re.finditer(r'<w:r[ >].*?</w:r>', p, re.S))
    out, prev = [], 0
    for i, m in enumerate(runs):
        r = m.group(0)
        if TT.search(r):
            nuevo = escape(nuevos.get(i, ""))
            r = TT.sub(lambda x: f'<w:t xml:space="preserve">{nuevo}</w:t>', r, count=1)
            r = TT.sub("", r)  # por si había más de un w:t
            # restaurar el primero si el sub anterior lo borró
            if "<w:t " not in r: r = r.replace("</w:rPr>", f'</w:rPr><w:t xml:space="preserve">{nuevo}</w:t>', 1)
        out.append(p[prev:m.start()] + r); prev = m.end()
    return "".join(out) + p[prev:]

parrafos = list(re.finditer(r'<w:p[ >].*?</w:p>', t, re.S))
reemplazos, afiliaciones = [], 0
for m in parrafos:
    p, x = m.group(0), texto(m.group(0))
    if x == "TÍTULO EN ESPAÑOL": n = fijar(p, {0: T.TITULO_ES})
    elif x == "TÍTULO EN INGLÉS": n = fijar(p, {0: T.TITULO_EN})
    elif x.startswith("Autor1"): n = fijar(p, {0: "Juan Felipe Bernal", 1: "1"})
    elif x.startswith("Último nivel"):
        afiliaciones += 1
        n = fijar(p, {0: T.AFILIACION}) if afiliaciones == 1 else ""
    elif x.startswith("Resumen:"): n = fijar(p, {0: "Resumen:", 1: " " + T.RESUMEN})
    elif x.startswith("Palabras clave:"): n = fijar(p, {0: "Palabras clave:", 1: " " + T.PALABRAS})
    elif x.startswith("Abstract:"): n = fijar(p, {0: "Abstract:", 1: " " + T.ABSTRACT})
    elif x.startswith("Keywords:"): n = fijar(p, {0: "Keywords:", 1: " " + T.KEYWORDS})
    else: continue
    reemplazos.append((m.start(), m.end(), n))
for a, b, n in sorted(reemplazos, reverse=True):
    t = t[:a] + n + t[b:]

# Tabla de autores: primera fila vacía después del encabezado → nombre y correo (documento y teléfono: Juan)
filas = list(re.finditer(r'<w:tr[ >].*?</w:tr>', t, re.S))
for f in filas:
    if not texto(f.group(0)).strip():
        celdas = list(re.finditer(r'<w:tc>.*?</w:tc>', f.group(0), re.S))
        fila = f.group(0)
        for idx, valor in sorted(((0, "Juan Felipe Bernal"), (3, "juan.bernal@unicafam.edu.co")), reverse=True):
            c = celdas[idx]
            nueva = re.sub(r'(<w:p[ >].*?)(</w:p>)', lambda m: m.group(1) + f'<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="18"/></w:rPr><w:t>{valor}</w:t></w:r>' + m.group(2), c.group(0), count=1, flags=re.S)
            fila = fila[:c.start()] + nueva + fila[c.end():]
        t = t[:f.start()] + fila + t[f.end():]
        break
open(doc, "w", encoding="utf-8").write(t)
print("párrafos reemplazados:", len(reemplazos), "afiliaciones:", afiliaciones)
