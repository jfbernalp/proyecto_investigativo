"""
Descarga los PDF de acceso abierto de las referencias citadas (referencias.bib + referencias_metodo.bib) usando OpenAlex
(ubicaciones de acceso abierto por DOI; sin DOI, búsqueda por título). Guarda <clave>.pdf en bibliografia/pdf/ (fuera de
git: los PDF tienen derechos de autor) y escribe bibliografia/pdf/estado.csv con lo encontrado y lo que falta.
Solo descarga enlaces que OpenAlex declara de acceso abierto; no intenta saltar muros de pago ni bloqueos antibots.
Segunda vía: en una página de acceso abierto sin PDF directo, la etiqueta estándar citation_pdf_url. Tercera: una versión
en arXiv con el mismo título (búsqueda por título exacto en la API de arXiv).

Uso:  python docs/articulo/descargar_pdfs.py
"""
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

DIR = Path(__file__).resolve().parent
DESTINO = DIR / "bibliografia" / "pdf"
AGENTE = {"User-Agent": "observatorio-articulo/1.0 (descarga de PDF de acceso abierto)"}


def entradas():
    texto = (DIR / "referencias.bib").read_text(encoding="utf-8") + (DIR / "referencias_metodo.bib").read_text(encoding="utf-8")
    for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", texto, re.S):
        campos = dict(re.findall(r"(\w+) = \{(.*?)\},?\n", m.group(2) + "\n", re.S))
        yield m.group(1), campos.get("doi", "").lower(), re.sub(r"\s+", " ", campos.get("title", ""))


def obtener(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def obra(doi, titulo):
    try:
        if doi:
            return json.loads(obtener("https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi))[0])
        q = urllib.parse.quote(titulo[:200])
        res = json.loads(obtener(f"https://api.openalex.org/works?search={q}&per-page=1")[0]).get("results", [])
        return res[0] if res else None
    except Exception:
        return None


def candidatos(w):
    urls = []
    for loc in [w.get("best_oa_location")] + (w.get("locations") or []):
        if loc and loc.get("is_oa") and loc.get("pdf_url") and loc["pdf_url"] not in urls:
            urls.append(loc["pdf_url"])
    return urls


def pdf_desde_pagina(url):
    """Las páginas de artículos (Highwire/Google Scholar) declaran el PDF en <meta name="citation_pdf_url">."""
    try:
        html, _ = obtener(url)
    except Exception:
        return None
    m = re.search(rb'<meta[^>]+name="citation_pdf_url"[^>]+content="([^"]+)"', html) or \
        re.search(rb'<meta[^>]+content="([^"]+)"[^>]+name="citation_pdf_url"', html)
    return m.group(1).decode() if m else None


def pdf_arxiv(titulo):
    """Versión en arXiv solo si el título coincide (normalizado)."""
    norm = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    q = urllib.parse.quote(f'ti:"{titulo[:150]}"')
    try:
        xml = obtener(f"https://export.arxiv.org/api/query?search_query={q}&max_results=3")[0].decode("utf-8", "replace")
    except Exception:
        return None
    for entrada in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", entrada, re.S)
        pdf = re.search(r'<link[^>]+title="pdf"[^>]+href="([^"]+)"', entrada)
        if t and pdf and norm(t.group(1)) == norm(titulo):
            return pdf.group(1)
    return None


def bajar(url, archivo):
    try:
        datos, tipo = obtener(url)
    except Exception as e:
        return f"falló la descarga ({type(e).__name__})"
    if datos[:5] == b"%PDF-":
        archivo.write_bytes(datos)
        return "descargado"
    return f"el enlace no devolvió un PDF ({tipo.split(';')[0]})"


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    filas = []
    for clave, doi, titulo in entradas():
        archivo = DESTINO / f"{clave}.pdf"
        if archivo.exists():
            filas.append({"clave": clave, "doi": doi, "estado": "ya estaba", "fuente": ""}); continue
        w = obra(doi, titulo)
        time.sleep(0.2)
        estado, fuente = "sin acceso abierto conocido", ""
        if w is None:
            estado = "no encontrado en OpenAlex"
        else:
            urls = candidatos(w)
            if not urls and w.get("open_access", {}).get("is_oa"):
                estado = f"acceso abierto sin PDF directo: {w['open_access'].get('oa_url') or ''}"
            oa = (w.get("open_access") or {}).get("oa_url")
            if oa and oa not in urls:
                urls.append(oa)
            for url in urls:
                estado = bajar(url, archivo)
                if estado == "descargado":
                    fuente = url; break
                if "no devolvió un PDF" in estado and (directo := pdf_desde_pagina(url)):
                    estado = bajar(directo, archivo)
                    if estado == "descargado":
                        fuente = directo; break
        if estado != "descargado" and titulo and (url := pdf_arxiv(titulo)):
            estado = bajar(url, archivo)
            fuente = url if estado == "descargado" else ""
            if estado == "descargado":
                estado = "descargado (versión de arXiv)"
            time.sleep(3)
        filas.append({"clave": clave, "doi": doi, "estado": estado, "fuente": fuente})
        print(f"{clave}: {estado}")
    with open(DESTINO / "estado.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["clave", "doi", "estado", "fuente"]); w.writeheader(); w.writerows(filas)
    ok = sum(f["estado"].startswith("descargado") or f["estado"] == "ya estaba" for f in filas)
    print(f"\n{ok} de {len(filas)} PDF en {DESTINO.relative_to(DIR.parent.parent)}; detalle en estado.csv")


if __name__ == "__main__":
    main()
