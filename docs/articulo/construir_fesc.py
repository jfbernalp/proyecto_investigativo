"""
Construye los entregables del Congreso FESC 2026 (hito 61) y de la revista AiBi (hito 62) en docs/articulo/salida/
(fuera de git):
- Articulo_FESC2026_JuanFelipeBernal.docx: manuscrito_fesc.md con APA 7 (estilos/apa.csl) y estilos de la plantilla.
- Resumen_FESC2026_JuanFelipeBernal.docx: el Formato de Resumen oficial con textos_resumen.py.
- Articulo_AiBi_JuanFelipeBernal.docx y Figura1.jpg: manuscrito_aibi.md con IEEE (estilos/ieee.csl) y
  estilos/referencia_aibi.docx (generado por estilos/hacer_referencia_aibi.py).
Las plantillas oficiales están en docs/articulo/fesc/ (descargadas del sitio del congreso, fuera de git).

Uso:  python docs/articulo/construir_fesc.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

DIR = Path(__file__).resolve().parent
SALIDA = DIR / "salida"
CAMPO = ('<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rpr}<w:instrText xml:space="preserve"> {campo} '
         '</w:instrText></w:r><w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rpr}<w:t>1</w:t></w:r>'
         '<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>')


def reescribir_zip(docx: Path, cambios):
    """cambios: {ruta interna: función(texto) -> texto}. Reescribe sin entradas de carpeta."""
    tmp = docx.with_suffix(".tmp")
    with zipfile.ZipFile(docx) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.endswith("/"):
                continue
            datos = zin.read(item.filename)
            if item.filename in cambios:
                datos = cambios[item.filename](datos.decode("utf-8")).encode("utf-8")
            zout.writestr(item, datos)
    tmp.replace(docx)


def numeros_de_pagina(xml: str) -> str:
    """La plantilla trae «Página 1 de 2» como texto fijo: se reemplaza por los campos PAGE y NUMPAGES."""
    for valor, campo in (("1", "PAGE"), ("2", "NUMPAGES")):
        m = re.search(r'<w:r(?: [^>]*)?>(?:(?!</w:r>).)*?<w:t(?: [^>]*)?>' + valor + r'</w:t></w:r>', xml, re.S)
        if m:
            rpr = (re.search(r"<w:rPr>.*?</w:rPr>", m.group(0), re.S) or [""])[0]
            xml = xml[:m.start()] + CAMPO.format(rpr=rpr, campo=campo) + xml[m.end():]
    return xml


def declarar_png(xml: str) -> str:
    """pandoc no declara la extensión png cuando la plantilla de referencia no traía imágenes."""
    if 'Extension="png"' in xml:
        return xml
    return re.sub(r"(<Types[^>]*>)", r'\1<Default Extension="png" ContentType="image/png"/>', xml, count=1)


def articulo(fuente="manuscrito_fesc.md", referencia="fesc/plantilla_articulo.docx",
             nombre="Articulo_FESC2026_JuanFelipeBernal.docx"):
    destino = SALIDA / nombre
    subprocess.run(["pandoc", fuente, "--citeproc", "--resource-path=.",
                    f"--reference-doc={referencia}", "-o", str(destino)], cwd=DIR, check=True)
    with zipfile.ZipFile(destino) as z:
        pies = [n for n in z.namelist() if re.match(r"word/footer\d+\.xml", n)]
    cambios = {p: numeros_de_pagina for p in pies}
    cambios["[Content_Types].xml"] = declarar_png
    reescribir_zip(destino, cambios)
    return destino


def articulo_aibi():
    """AiBi (UDES): IEEE, Times New Roman 9 pt; la figura va además aparte en .jpg de 580 px de ancho."""
    destino = articulo("manuscrito_aibi.md", "estilos/referencia_aibi.docx", "Articulo_AiBi_JuanFelipeBernal.docx")
    subprocess.run(["sips", "-s", "format", "jpeg", "--resampleWidth", "580", str(DIR / "figuras" / "arquitectura.png"),
                    "--out", str(SALIDA / "Figura1.jpg")], check=True, capture_output=True)
    return destino


def resumen():
    destino = SALIDA / "Resumen_FESC2026_JuanFelipeBernal.docx"
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(DIR / "fesc" / "formato_resumen.docx") as z:
            z.extractall(tmp)
        subprocess.run([sys.executable, str(DIR / "fesc_llenar_resumen.py"), str(Path(tmp) / "word" / "document.xml"),
                        str(DIR)], check=True)
        shutil.make_archive(str(destino.with_suffix("")), "zip", tmp)
        destino.with_suffix(".zip").replace(destino)
    reescribir_zip(destino, {})
    return destino


if __name__ == "__main__":
    SALIDA.mkdir(exist_ok=True)
    for f in (articulo(), resumen(), articulo_aibi()):
        print(f.relative_to(DIR))
