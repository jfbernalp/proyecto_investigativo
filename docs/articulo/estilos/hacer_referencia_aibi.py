"""Documento de referencia de pandoc con las especificaciones de AiBi (Políticas editoriales, 2.2–2.4):
Times New Roman; cuerpo 9 pt; subtítulos 10 pt; título 24 pt; autores 11 pt; tablas y leyendas 8 pt; interlineado
sencillo; carta 8,5 × 11 in; márgenes sup. 4 cm, inf. 3, der. 3, izq. 4."""
import re
import sys
import zipfile
from pathlib import Path

DIR = Path(__file__).resolve().parent
ORIGEN, DESTINO = DIR / "ref_base.docx", DIR / "referencia_aibi.docx"
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
TAMANOS = {"Title": 48, "Subtitle": 22, "Author": 22, "Date": 18, "Abstract": 18, "Heading1": 20, "Heading2": 20,
           "Heading3": 18, "BodyText": 18, "FirstParagraph": 18, "Compact": 16, "TableCaption": 16,
           "ImageCaption": 16, "CaptionedFigure": 16, "Bibliography": 16, "FootnoteText": 16}
CM = 567  # twips por centímetro


def estilos(xml: str) -> str:
    # Fuente y tamaño por defecto
    xml = re.sub(r"<w:rPrDefault>.*?</w:rPrDefault>",
                 f'<w:rPrDefault><w:rPr>{TNR}<w:sz w:val="18"/><w:szCs w:val="18"/><w:lang w:val="es-CO"/></w:rPr></w:rPrDefault>',
                 xml, flags=re.S)
    xml = re.sub(r"<w:pPrDefault>.*?</w:pPrDefault>",
                 '<w:pPrDefault><w:pPr><w:spacing w:after="80" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault>',
                 xml, flags=re.S)

    def un_estilo(m):
        bloque, sid = m.group(0), m.group(1)
        bloque = re.sub(r"<w:rPr\s*/>", "<w:rPr></w:rPr>", bloque)  # <w:rPr /> vacío: se rellena, no se duplica
        bloque = re.sub(r"<w:rFonts[^>]*/>", "", bloque)            # quitar fuentes de tema (Calibri/Cambria)
        bloque = re.sub(r'<w:color w:val="[^"]*"[^>]*/>', '<w:color w:val="000000"/>', bloque)
        if sid in TAMANOS:
            t = TAMANOS[sid]
            bloque = re.sub(r"<w:sz w:val=\"\d+\"\s*/>", f'<w:sz w:val="{t}"/>', bloque)
            bloque = re.sub(r"<w:szCs w:val=\"\d+\"\s*/>", f'<w:szCs w:val="{t}"/>', bloque)
            if "<w:sz " not in bloque:
                bloque = (bloque.replace("</w:rPr>", f'<w:sz w:val="{t}"/><w:szCs w:val="{t}"/></w:rPr>', 1)
                          if "<w:rPr>" in bloque else bloque.replace("</w:style>", f'<w:rPr><w:sz w:val="{t}"/><w:szCs w:val="{t}"/></w:rPr></w:style>'))
        if sid in ("BodyText", "FirstParagraph"):
            bloque = re.sub(r"<w:spacing[^>]*/>", '<w:spacing w:before="0" w:after="80"/><w:jc w:val="both"/>', bloque)
        if sid in ("Title",):
            bloque = re.sub(r"<w:jc [^>]*/>", "", bloque).replace("</w:pPr>", '<w:jc w:val="center"/></w:pPr>', 1)
        return bloque

    return re.sub(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>.*?</w:style>', un_estilo, xml, flags=re.S)


def pagina(xml: str) -> str:
    sect = (f'<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="{4*CM}" w:right="{3*CM}" w:bottom="{3*CM}" '
            f'w:left="{4*CM}" w:header="708" w:footer="708" w:gutter="0"/>')
    xml = re.sub(r"<w:pgSz[^>]*/>", "", xml)
    xml = re.sub(r"<w:pgMar[^>]*/>", "", xml)
    return xml.replace("</w:sectPr>", sect + "</w:sectPr>", 1)  # pgSz y pgMar van después de footnotePr


with zipfile.ZipFile(ORIGEN) as zin, zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        datos = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            datos = estilos(datos.decode("utf-8")).encode("utf-8")
        elif item.filename == "word/document.xml":
            datos = pagina(datos.decode("utf-8")).encode("utf-8")
        zout.writestr(item, datos)
print(DESTINO.relative_to(DIR.parent))
