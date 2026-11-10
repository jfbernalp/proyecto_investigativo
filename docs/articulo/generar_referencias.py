"""
Genera docs/articulo/referencias.bib con las 92 referencias de bibliografia/seleccion_final.md y verifica cada DOI en
Crossref (que el DOI exista y que su título coincida con el seleccionado).

- Metadatos desde las exportaciones de Scopus (bibliografia/*.bib, fuera de git); sin resúmenes ni palabras clave:
  el .bib resultante solo lleva datos bibliográficos.
- Si una referencia no está en las exportaciones (clásicos), se arma desde Crossref.
- Escribe bibliografia/claves.md: Id de la selección → clave BibTeX → resultado de la verificación.

Uso:  python docs/articulo/generar_referencias.py [--sin-red]
"""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

DIR = Path(__file__).resolve().parent
BIB = DIR / "bibliografia"
SALIDA = DIR / "referencias.bib"
CLAVES = BIB / "claves.md"
CAMPOS = ("author", "title", "journal", "booktitle", "year", "volume", "number", "pages", "publisher", "doi")


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in t if not unicodedata.combining(c))).strip()


def leer_bibs():
    """Entradas de todas las exportaciones: dict con tipo y campos. Claves de Scopus pueden tener espacios."""
    entradas = []
    for f in sorted(BIB.glob("*.bib")):
        texto = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"@(\w+)\s*\{\s*([^,{}\n]+?)\s*,(.*?)\n\}", texto, re.DOTALL):
            campos = {}
            for c in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\d+)", m.group(3)):
                campos[c.group(1).lower()] = c.group(2).strip("{}\"").strip()
            entradas.append({"tipo": m.group(1).lower(), **campos})
    return entradas


def leer_seleccion():
    filas = []
    for linea in (BIB / "seleccion_final.md").read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if not linea.startswith("|") or celdas[0] in ("Id", "Referencia", "Etapa") or set(celdas[0]) <= set("-"):
            continue
        if len(celdas) == 6 and celdas[0].isdigit():                       # Id | Año | Título | Fuente | DOI | Citas
            filas.append({"id": celdas[0], "anio": celdas[1], "titulo": celdas[2], "fuente": celdas[3],
                          "doi": None if celdas[4] in ("—", "") else celdas[4].lower()})
        elif len(celdas) == 5 and re.search(r"\(\d{4}\)", celdas[0]):     # clásicos: Referencia | Título | Fuente | DOI | Eje
            filas.append({"id": celdas[0], "anio": re.search(r"\((\d{4})\)", celdas[0]).group(1), "titulo": celdas[1],
                          "fuente": celdas[2], "doi": celdas[3].lower()})
    return filas


def crossref(doi: str):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "observatorio-articulo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["message"]
    except Exception as e:
        return {"_error": str(e)}


def datacite(doi: str):
    """DOI de arXiv, Zenodo o algunas revistas: no están en Crossref sino en DataCite."""
    req = urllib.request.Request("https://api.datacite.org/dois/" + urllib.parse.quote(doi),
                                 headers={"User-Agent": "observatorio-articulo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            a = json.load(r)["data"]["attributes"]
    except Exception as e:
        return {"_error": str(e)}
    return {"title": [a["titles"][0]["title"]], "author": [{"family": c.get("familyName") or c["name"].split(",")[0],
                                                            "given": c.get("givenName", "")} for c in a.get("creators", [])],
            "issued": {"date-parts": [[a.get("publicationYear")]]}, "container-title": [a.get("publisher", "")],
            "publisher": a.get("publisher"), "DOI": doi, "type": "journal-article", "_fuente": "DataCite"}


def coincide(a: str, b: str) -> bool:
    """Mismo título: casi idéntico, o uno es el comienzo del otro (subtítulo omitido)."""
    a, b = normalizar(a), normalizar(b)
    return bool(a and b) and (SequenceMatcher(None, a, b).ratio() >= 0.8 or a.startswith(b) or b.startswith(a))


def desde_crossref(msg: dict) -> dict:
    autores = " and ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in msg.get("author", []))
    tipo = "inproceedings" if msg.get("type") == "proceedings-article" else "article"
    anio = (msg.get("published-print") or msg.get("published-online") or msg.get("issued") or {}).get("date-parts", [[None]])[0][0]
    titulo = re.sub(r"(?<=[a-z])\d+$", "", (msg.get("title") or [""])[0])     # «Research1»: nota al pie pegada
    d = {"tipo": tipo, "author": autores, "title": titulo, "year": str(anio or ""),
         "volume": msg.get("volume"), "number": msg.get("issue"), "pages": msg.get("page"),
         "publisher": msg.get("publisher"), "doi": msg.get("DOI", "").lower()}
    d["booktitle" if tipo == "inproceedings" else "journal"] = (msg.get("container-title") or [""])[0]
    return {k: v for k, v in d.items() if v}


def clave(entrada: dict, usadas: set) -> str:
    autor = entrada.get("author", "anonimo").split(" and ")[0]
    apellido = normalizar(autor.split(",")[0] if "," in autor else autor.split()[-1] if autor.split() else "anonimo").replace(" ", "")
    palabra = next((w for w in normalizar(entrada.get("title", "")).split() if len(w) > 3), "x")
    base = f"{apellido or 'anonimo'}{entrada.get('year', '')}{palabra}"
    k, i = base, 1
    while k in usadas:
        i += 1
        k = f"{base}{i}"
    usadas.add(k)
    return k


def a_bibtex(k: str, e: dict) -> str:
    lineas = [f"@{e.get('tipo', 'article')}{{{k},"]
    for c in CAMPOS:
        if e.get(c):
            lineas.append(f"  {c} = {{{e[c]}}},")
    return "\n".join(lineas) + "\n}"


def main():
    con_red = "--sin-red" not in sys.argv
    entradas = leer_bibs()
    por_doi = {e["doi"].lower(): e for e in entradas if e.get("doi")}
    por_titulo = {normalizar(e.get("title", "")): e for e in entradas}
    usadas, salida, filas_md = set(), [], []
    for s in leer_seleccion():
        e = por_doi.get(s["doi"]) if s["doi"] else None
        e = e or por_titulo.get(normalizar(s["titulo"]))
        origen = "exportación de Scopus" if e else None
        verificacion = "sin DOI: no verificable en Crossref"
        if s["doi"] and con_red:
            msg = crossref(s["doi"])
            if "_error" in msg:
                msg = datacite(s["doi"])
            time.sleep(0.2)
            registro = msg.get("_fuente", "Crossref")
            if "_error" in msg:
                verificacion = f"DOI NO resuelve en Crossref ni DataCite ({msg['_error'][:40]})"
            else:
                titulo_reg = (msg.get("title") or [""])[0]
                # títulos bilingües de Scopus: «Título en inglés; [Título original]»
                variantes = [s["titulo"]] + re.findall(r"\[([^\]]+)\]", s["titulo"]) + [s["titulo"].split("; [")[0]]
                verificacion = (f"DOI y título coinciden en {registro}" if any(coincide(v, titulo_reg) for v in variantes)
                                else f"REVISAR: título distinto en {registro}: «{titulo_reg[:60]}»")
                if not e:
                    e, origen = desde_crossref(msg), registro
        elif s["doi"]:
            verificacion = "no verificado (--sin-red)"
        if not e:
            filas_md.append(f"| {s['id']} | — | {s['titulo'][:70]} | SIN METADATOS: completar a mano |")
            continue
        e = {k: v for k, v in e.items() if k in CAMPOS or k == "tipo"}
        if e.get("doi"):
            e["doi"] = re.sub(r"^https?://(dx\.)?doi\.org/", "", e["doi"].strip())   # Scopus a veces trae la URL
        if e.get("tipo") != "article" and "journal" in e and "booktitle" not in e:
            e["booktitle"] = e.pop("journal")          # Scopus pone el nombre de las memorias en «journal»
        k = clave(e, usadas)
        salida.append(a_bibtex(k, e))
        filas_md.append(f"| {s['id']} | `{k}` | {s['titulo'][:70]} | {origen}; {verificacion} |")
    SALIDA.write_text("% Generado por generar_referencias.py desde bibliografia/seleccion_final.md\n\n"
                      + "\n\n".join(salida) + "\n", encoding="utf-8")
    CLAVES.write_text("# Claves BibTeX de la selección final\n\nGenerado por `docs/articulo/generar_referencias.py`. "
                      "Id = número de `seleccion_final.md` (los # que usa el borrador).\n\n"
                      "| Id | Clave | Título | Origen y verificación |\n|---|---|---|---|\n" + "\n".join(filas_md) + "\n",
                      encoding="utf-8")
    revisar = [f for f in filas_md if "REVISAR" in f or "NO resuelve" in f or "SIN METADATOS" in f]
    print(f"{len(salida)} referencias en {SALIDA.name}; {len(revisar)} para revisar:")
    for f in revisar:
        print(" ", f)


if __name__ == "__main__":
    main()
