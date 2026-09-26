"""
Exportador de Propuestas Curriculares y Oferta Académica a Excel en formato
MATRIZ INTEGRADA DE GESTIÓN (MIG) - Estándar UniCafam.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ai_curriculum.curriculum_schemas import (
    PropuestaPrograma, 
    ModuloAsignatura, 
    PerfilDocente, 
    InversionPrograma, 
    PortafolioRecomendacionesIA
)
DEFAULT_INPUT_JSON = BASE_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "curriculo_unicafam" / "mig_propuestas"

# Paleta Institucional UniCafam / MIG
COLOR_NAVY_HEADER = "0D233A"        # Azul institucional oscuro
COLOR_NAVY_ACCENT = "1F4E79"        # Azul encabezado secundario
COLOR_BLUE_LIGHT = "D9E1F2"         # Azul claro para fondos de títulos de sección
COLOR_GRAY_LIGHT = "F2F4F7"         # Gris suave para fondos alternados
COLOR_BORDER = "A6B8C7"             # Borde suave

font_title = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
font_section_header = Font(name="Calibri", size=11, bold=True, color=COLOR_NAVY_HEADER)
font_table_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
font_bold = Font(name="Calibri", size=10, bold=True, color="000000")
font_regular = Font(name="Calibri", size=10, bold=False, color="000000")
font_meta = Font(name="Calibri", size=9, bold=False, color="333333")

fill_main_header = PatternFill(start_color=COLOR_NAVY_HEADER, end_color=COLOR_NAVY_HEADER, fill_type="solid")
fill_accent_header = PatternFill(start_color=COLOR_NAVY_ACCENT, end_color=COLOR_NAVY_ACCENT, fill_type="solid")
fill_section = PatternFill(start_color=COLOR_BLUE_LIGHT, end_color=COLOR_BLUE_LIGHT, fill_type="solid")
fill_zebra = PatternFill(start_color=COLOR_GRAY_LIGHT, end_color=COLOR_GRAY_LIGHT, fill_type="solid")

thin_side = Side(border_style="thin", color=COLOR_BORDER)
medium_side = Side(border_style="medium", color=COLOR_NAVY_HEADER)

box_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
header_border = Border(left=thin_side, right=thin_side, top=medium_side, bottom=medium_side)

align_left_top = Alignment(horizontal="left", vertical="top", wrap_text=True)
align_left_center = Alignment(horizontal="left", vertical="center", wrap_text=True)
align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
align_right_center = Alignment(horizontal="right", vertical="center", wrap_text=True)

def aplicar_borde_rango(ws, start_row, start_col, end_row, end_col, border=box_border):
    """Aplica bordes a todas las celdas de un rango combinado."""
    for r in range(start_row, end_row + 1):
        for c in range(start_col, end_col + 1):
            ws.cell(row=r, column=c).border = border

def normalizar_propuesta_a_mig(p: Union[PropuestaPrograma, Dict[str, Any]]) -> PropuestaPrograma:
    """Asegura que la propuesta contenga todos los campos MIG con valores contextuales coherentes."""
    if isinstance(p, dict):
        p_obj = PropuestaPrograma.model_validate(p)
    else:
        p_obj = p

    # Autocompletar campos MIG si venían vacíos de generaciones previas
    if not p_obj.horario or "sesiones" not in p_obj.horario.lower():
        if "Microcredencial" in p_obj.tipo_propuesta or "Certificación" in p_obj.tipo_propuesta:
            p_obj.horario = "Martes y Jueves de 6:00 p.m. a 9:00 p.m. (Virtual Sincrónico)"
        elif "Electiva" in p_obj.tipo_propuesta:
            p_obj.horario = "Viernes 6:00 p.m. - 10:00 p.m. y Sábados 8:00 a.m. - 12:00 m."
        elif "Especialización" in p_obj.tipo_propuesta:
            p_obj.horario = "Viernes de 5:00 p.m. a 10:00 p.m. y Sábados de 8:00 a.m. a 2:00 p.m."
        else:
            p_obj.horario = "Jornada Nocturna y Concentrada en Fines de Semana (Híbrida)"

    if not p_obj.justificacion_detallada:
        p_obj.justificacion_detallada = (
            f"El presente programa responde a las demandas urgentes del mercado laboral identificadas por el "
            f"Observatorio de Inteligencia Laboral de UniCafam. El análisis de vacantes revela una brecha del sector productivo "
            f"en competencias de {p_obj.nombre_programa}. El impacto salarial proyectado ({p_obj.impacto_salarial_proyectado}) "
            f"sustenta la pertinencia de formar talento especializado con alta tasa de empleabilidad y proyección nacional e internacional."
        )

    if not p_obj.objetivos_programa:
        p_obj.objetivos_programa = [
            f"Desarrollar competencias especializadas en {p_obj.nombre_programa} para responder a los desafíos tecnológicos del mercado.",
            "Implementar soluciones técnicas reales mediante proyectos aplicados utilizando herramientas líderes de la industria.",
            "Integrar metodologías ágiles y estándares internacionales en el ciclo de vida de los datos e inteligencia artificial."
        ]

    if not p_obj.dirigido_a:
        p_obj.dirigido_a = p_obj.perfil_ingreso

    if not p_obj.metodologia_detallada:
        p_obj.metodologia_detallada = (
            "Metodología 100% teórico-práctica con enfoque en Aprendizaje Basado en Retos y Proyectos Reales (PBL). "
            "Las sesiones combinan fundamentación conceptual, laboratorios guiados en la nube y trabajo autónomo "
            "con acompañamiento de expertos de la industria. Cada módulo concluye con un entregable técnico aplicable."
        )

    if not p_obj.valores_agregados:
        p_obj.valores_agregados = [
            "Alineación directa con los requisitos reales de vacantes analizadas en el Observatorio Laboral.",
            f"Enfoque en tecnologías de alta prima salarial ({p_obj.impacto_salarial_proyectado}).",
            "Certificación institucional respaldada por la Fundación Universitaria Cafam.",
            "Docentes activos y líderes técnicos en empresas multinacionales de tecnología."
        ]

    # Asegurar números ordinales en módulos
    for idx, mod in enumerate(p_obj.plan_estudios, start=1):
        if not mod.numero_modulo:
            mod.numero_modulo = idx
        if not mod.horas_totales_modulo:
            mod.horas_totales_modulo = (mod.horas_tfd + mod.horas_tti) if (mod.horas_tfd and mod.horas_tti) else (mod.creditos * 48)
        if not mod.contenido_detallado:
            stack_txt = ", ".join(mod.stack_tecnologico) if mod.stack_tecnologico else "Tecnologías aplicadas"
            raes_txt = " | ".join(mod.resultados_aprendizaje_esperados_rae) if mod.resultados_aprendizaje_esperados_rae else "Resultados de aprendizaje"
            mod.contenido_detallado = f"Unidades Temáticas:\n1. Fundamentación y Arquitectura.\n2. Implementación Práctica y Laboratorios ({stack_txt}).\n3. Proyecto de Aplicación y Evaluación.\n\nResultados de Aprendizaje:\n{raes_txt}"
        if not mod.cronograma_fechas:
            mod.cronograma_fechas = f"Módulo {idx} - Semanas {((idx-1)*4)+1} a {idx*4}"

    # Asegurar perfiles docentes si vienen vacíos
    if not p_obj.docentes_perfiles or len(p_obj.docentes_perfiles) == 0:
        docentes = []
        for m in p_obj.plan_estudios:
            stack_hint = m.stack_tecnologico[0] if m.stack_tecnologico else "Tecnología y Analítica"
            docentes.append(PerfilDocente(
                nombre_o_rol=f"Especialista / Magíster en {stack_hint}",
                modulo_asignado=m.nombre_modulo,
                perfil_experto=f"Profesional con más de 5 años de experiencia liderando proyectos de {m.nombre_modulo} en el sector productivo, con certificaciones internacionales en el stack tecnológico enseñado."
            ))
        p_obj.docentes_perfiles = docentes

    return p_obj


class MIGExcelExporter:
    """Generador especializado para la Matriz Integrada de Gestión (MIG) en formato Excel."""

    def __init__(self):
        pass

    def crear_hoja_mig(self, ws, propuesta: PropuestaPrograma):
        """Construye una hoja de cálculo completa con la estructura exacta de la plantilla MIG."""
        prop = normalizar_propuesta_a_mig(propuesta)

        # Configurar vistas y anchos de columna (Columnas A a H)
        ws.views.sheetView[0].showGridLines = True
        ws.column_dimensions["A"].width = 3
        ws.column_dimensions["B"].width = 24
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 26
        ws.column_dimensions["E"].width = 34
        ws.column_dimensions["F"].width = 16
        ws.column_dimensions["G"].width = 20
        ws.column_dimensions["H"].width = 16

        # ----------------------------------------------------------------------
        # 1. ENCABEZADO INSTITUCIONAL MIG
        # ----------------------------------------------------------------------
        # Fila 1: Logo/Título MIG + Metadatos
        ws.merge_cells("B1:E4")
        cell_mig = ws["B1"]
        cell_mig.value = "MATRIZ INTEGRADA DE GESTION MIG\nOFERTA Y DISEÑO CURRICULAR ACADÉMICO"
        cell_mig.font = font_title
        cell_mig.fill = fill_main_header
        cell_mig.alignment = align_center
        aplicar_borde_rango(ws, 1, 2, 4, 5, box_border)

        # Meta-información (Col F, G, H)
        meta_items = [
            (1, "Código:", "MIDOFO05"),
            (2, "Versión:", "1.0"),
            (3, "Fecha:", "2025/2026"),
            (4, "Página:", "1 de 1")
        ]
        for r_idx, label, val in meta_items:
            ws.cell(row=r_idx, column=6, value=label).font = font_bold
            ws.cell(row=r_idx, column=6).fill = fill_zebra
            ws.cell(row=r_idx, column=6).alignment = align_right_center
            ws.cell(row=r_idx, column=6).border = box_border

            ws.merge_cells(start_row=r_idx, start_column=7, end_row=r_idx, end_column=8)
            cell_v = ws.cell(row=r_idx, column=7, value=val)
            cell_v.font = font_meta
            cell_v.alignment = align_left_center
            aplicar_borde_rango(ws, r_idx, 7, r_idx, 8, box_border)

        # Fila 5: Espacio en blanco separador
        ws.row_dimensions[5].height = 10

        # ----------------------------------------------------------------------
        # 2. FICHA TÉCNICA DEL PROGRAMA
        # ----------------------------------------------------------------------
        campos_basicos = [
            (6, "NOMBRE DEL PROGRAMA", prop.nombre_programa.upper()),
            (7, "TIPO / NIVEL", f"{prop.tipo_propuesta} ({prop.nivel_academico}) - {prop.titulo_otorgado}"),
            (8, "HORARIO", prop.horario),
            (9, "DURACIÓN", f"{prop.duracion_estimada} | {prop.creditos_totales} Créditos ({prop.horas_totales} Horas totales)"),
            (10, "FECHA DE INICIO", prop.fecha_inicio_estimada),
            (11, "FECHA DE TERMINACIÓN", prop.fecha_terminacion_estimada),
        ]

        for r_idx, label, val in campos_basicos:
            ws.row_dimensions[r_idx].height = 24
            cell_lbl = ws.cell(row=r_idx, column=2, value=label)
            cell_lbl.font = font_section_header
            cell_lbl.fill = fill_section
            cell_lbl.alignment = align_left_center
            cell_lbl.border = box_border

            ws.merge_cells(start_row=r_idx, start_column=3, end_row=r_idx, end_column=8)
            cell_val = ws.cell(row=r_idx, column=3, value=val)
            cell_val.font = font_bold if r_idx in [6, 7] else font_regular
            cell_val.alignment = align_left_center
            aplicar_borde_rango(ws, r_idx, 3, r_idx, 8, box_border)

        # INVERSIÓN (Filas 12-15)
        ws.merge_cells("B12:B15")
        cell_inv = ws["B12"]
        cell_inv.value = "INVERSIÓN"
        cell_inv.font = font_section_header
        cell_inv.fill = fill_section
        cell_inv.alignment = align_center
        aplicar_borde_rango(ws, 12, 2, 15, 2, box_border)

        inversion_items = [
            (12, "Público externo", prop.inversion.publico_externo if prop.inversion else "Tarifa regular"),
            (13, "Comunidad UniCafam", prop.inversion.comunidad_unicafam if prop.inversion else "Descuento afiliados/estudiantes"),
            (14, "Egresados", prop.inversion.egresados if prop.inversion else "Tarifa preferencial"),
            (15, "Grupos / Empresas", prop.inversion.grupos_empresas if prop.inversion else "Tarifa corporativa")
        ]

        for r_idx, cat_name, cat_val in inversion_items:
            ws.row_dimensions[r_idx].height = 20
            cell_cat = ws.cell(row=r_idx, column=3, value=cat_name)
            cell_cat.font = font_bold
            cell_cat.fill = fill_zebra
            cell_cat.alignment = align_left_center
            cell_cat.border = box_border

            ws.merge_cells(start_row=r_idx, start_column=4, end_row=r_idx, end_column=8)
            cell_costo = ws.cell(row=r_idx, column=4, value=cat_val)
            cell_costo.font = font_regular
            cell_costo.alignment = align_left_center
            aplicar_borde_rango(ws, r_idx, 4, r_idx, 8, box_border)

        # PRÓXIMAS EDICIONES (Fila 16)
        ws.row_dimensions[16].height = 22
        cell_prox = ws.cell(row=16, column=2, value="PRÓXIMAS EDICIONES")
        cell_prox.font = font_section_header
        cell_prox.fill = fill_section
        cell_prox.alignment = align_left_center
        cell_prox.border = box_border

        ws.merge_cells("C16:H16")
        cell_prox_val = ws["C16"]
        cell_prox_val.value = prop.proximas_ediciones
        cell_prox_val.font = font_regular
        cell_prox_val.alignment = align_left_center
        aplicar_borde_rango(ws, 16, 3, 16, 8, box_border)

        # Espaciador Fila 17
        ws.row_dimensions[17].height = 8

        # ----------------------------------------------------------------------
        # 3. SECCIONES NARRATIVAS / DESCRIPTIVAS CON MERGED BLOCKS
        # ----------------------------------------------------------------------
        current_row = 18

        def agregar_bloque_narrativo(titulo: str, contenido: str, num_filas: int = 4):
            nonlocal current_row
            end_row = current_row + num_filas - 1

            ws.merge_cells(start_row=current_row, start_column=2, end_row=end_row, end_column=2)
            cell_t = ws.cell(row=current_row, column=2, value=titulo)
            cell_t.font = font_section_header
            cell_t.fill = fill_section
            cell_t.alignment = align_center
            aplicar_borde_rango(ws, current_row, 2, end_row, 2, box_border)

            ws.merge_cells(start_row=current_row, start_column=3, end_row=end_row, end_column=8)
            cell_c = ws.cell(row=current_row, column=3, value=contenido)
            cell_c.font = font_regular
            cell_c.alignment = align_left_top
            aplicar_borde_rango(ws, current_row, 3, end_row, 8, box_border)

            for r in range(current_row, end_row + 1):
                ws.row_dimensions[r].height = 20

            current_row = end_row + 1

        # JUSTIFICACIÓN
        agregar_bloque_narrativo("JUSTIFICACIÓN", prop.justificacion_detallada, num_filas=4)

        # OBJETIVOS
        objetivos_txt = "\n".join([f"• {obj}" for obj in prop.objetivos_programa])
        agregar_bloque_narrativo("OBJETIVOS", objetivos_txt, num_filas=4)

        # DIRIGIDO A
        agregar_bloque_narrativo("DIRIGIDO A", prop.dirigido_a, num_filas=3)

        # METODOLOGÍA
        agregar_bloque_narrativo("METODOLOGÍA", prop.metodologia_detallada, num_filas=4)

        # VALOR(ES) AGREGADO(S)
        valores_txt = "\n".join([f"✔ {val}" for val in prop.valores_agregados])
        agregar_bloque_narrativo("VALOR(ES) AGREGADO(S)", valores_txt, num_filas=3)

        # Espaciador
        ws.row_dimensions[current_row].height = 10
        current_row += 1

        # ----------------------------------------------------------------------
        # 4. TABLA PROGRAMA ACADÉMICO / MALLA DE MÓDULOS
        # ----------------------------------------------------------------------
        # Encabezado de la tabla (2 filas combinadas como en plantilla MIG)
        header_row_1 = current_row
        header_row_2 = current_row + 1

        ws.row_dimensions[header_row_1].height = 20
        ws.row_dimensions[header_row_2].height = 20

        # Col B: "PROGRAMA ACADÉMICO"
        ws.merge_cells(start_row=header_row_1, start_column=2, end_row=header_row_2, end_column=2)
        cell_pa = ws.cell(row=header_row_1, column=2, value="PROGRAMA ACADÉMICO")
        cell_pa.font = font_table_header
        cell_pa.fill = fill_main_header
        cell_pa.alignment = align_center
        aplicar_borde_rango(ws, header_row_1, 2, header_row_2, 2, header_border)

        # Col C: "No. Módulo"
        ws.cell(row=header_row_1, column=3, value="No.").font = font_table_header
        ws.cell(row=header_row_1, column=3).fill = fill_accent_header
        ws.cell(row=header_row_1, column=3).alignment = align_center
        ws.cell(row=header_row_2, column=3, value="Módulo").font = font_table_header
        ws.cell(row=header_row_2, column=3).fill = fill_accent_header
        ws.cell(row=header_row_2, column=3).alignment = align_center
        aplicar_borde_rango(ws, header_row_1, 3, header_row_2, 3, header_border)

        # Col D: "Nombre Módulo"
        ws.cell(row=header_row_1, column=4, value="Nombre").font = font_table_header
        ws.cell(row=header_row_1, column=4).fill = fill_accent_header
        ws.cell(row=header_row_1, column=4).alignment = align_center
        ws.cell(row=header_row_2, column=4, value="Módulo").font = font_table_header
        ws.cell(row=header_row_2, column=4).fill = fill_accent_header
        ws.cell(row=header_row_2, column=4).alignment = align_center
        aplicar_borde_rango(ws, header_row_1, 4, header_row_2, 4, header_border)

        # Col E, F: "Contenido Módulo"
        ws.merge_cells(start_row=header_row_1, start_column=5, end_row=header_row_1, end_column=6)
        cell_c1 = ws.cell(row=header_row_1, column=5, value="Contenido")
        cell_c1.font = font_table_header
        cell_c1.fill = fill_accent_header
        cell_c1.alignment = align_center

        ws.merge_cells(start_row=header_row_2, start_column=5, end_row=header_row_2, end_column=6)
        cell_c2 = ws.cell(row=header_row_2, column=5, value="Módulo / Temáticas y Stack")
        cell_c2.font = font_table_header
        cell_c2.fill = fill_accent_header
        cell_c2.alignment = align_center
        aplicar_borde_rango(ws, header_row_1, 5, header_row_2, 6, header_border)

        # Col G, H: "Cronograma de clases" (Fecha, No. Horas)
        ws.merge_cells(start_row=header_row_1, start_column=7, end_row=header_row_1, end_column=8)
        cell_cron = ws.cell(row=header_row_1, column=7, value="Cronograma de clases")
        cell_cron.font = font_table_header
        cell_cron.fill = fill_accent_header
        cell_cron.alignment = align_center

        ws.cell(row=header_row_2, column=7, value="Fecha / Semanas").font = font_table_header
        ws.cell(row=header_row_2, column=7).fill = fill_accent_header
        ws.cell(row=header_row_2, column=7).alignment = align_center

        ws.cell(row=header_row_2, column=8, value="No. Horas").font = font_table_header
        ws.cell(row=header_row_2, column=8).fill = fill_accent_header
        ws.cell(row=header_row_2, column=8).alignment = align_center
        aplicar_borde_rango(ws, header_row_1, 7, header_row_2, 8, header_border)

        current_row += 2

        # Filas de Módulos (cada módulo toma 3-4 filas o 1 fila expandida para legibilidad)
        for mod_idx, modulo in enumerate(prop.plan_estudios, start=1):
            m_start = current_row
            m_end = current_row + 2  # 3 filas de alto para contenido detallado

            # Merge Col B vacío o etiqueta
            ws.merge_cells(start_row=m_start, start_column=2, end_row=m_end, end_column=2)
            cell_b = ws.cell(row=m_start, column=2, value="")
            cell_b.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 2, m_end, 2, box_border)

            # Col C: Número del módulo
            ws.merge_cells(start_row=m_start, start_column=3, end_row=m_end, end_column=3)
            cell_num = ws.cell(row=m_start, column=3, value=modulo.numero_modulo or mod_idx)
            cell_num.font = Font(name="Calibri", size=11, bold=True)
            cell_num.alignment = align_center
            cell_num.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 3, m_end, 3, box_border)

            # Col D: Nombre del Módulo
            ws.merge_cells(start_row=m_start, start_column=4, end_row=m_end, end_column=4)
            cell_nom = ws.cell(row=m_start, column=4, value=modulo.nombre_modulo)
            cell_nom.font = font_bold
            cell_nom.alignment = align_left_center
            cell_nom.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 4, m_end, 4, box_border)

            # Col E, F: Contenido del Módulo
            ws.merge_cells(start_row=m_start, start_column=5, end_row=m_end, end_column=6)
            stack_badge = f" [Stack: {', '.join(modulo.stack_tecnologico)}]" if modulo.stack_tecnologico else ""
            contenido_txt = f"{modulo.contenido_detallado or 'Temario integral'}{stack_badge}"
            cell_cont = ws.cell(row=m_start, column=5, value=contenido_txt)
            cell_cont.font = font_regular
            cell_cont.alignment = align_left_top
            cell_cont.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 5, m_end, 6, box_border)

            # Col G: Cronograma / Fechas
            ws.merge_cells(start_row=m_start, start_column=7, end_row=m_end, end_column=7)
            cell_fec = ws.cell(row=m_start, column=7, value=modulo.cronograma_fechas or f"Semanas {((mod_idx-1)*4)+1} a {mod_idx*4}")
            cell_fec.font = font_regular
            cell_fec.alignment = align_center
            cell_fec.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 7, m_end, 7, box_border)

            # Col H: No. Horas
            ws.merge_cells(start_row=m_start, start_column=8, end_row=m_end, end_column=8)
            horas_val = f"{modulo.horas_totales_modulo or (modulo.creditos * 48)} h"
            cell_hrs = ws.cell(row=m_start, column=8, value=horas_val)
            cell_hrs.font = font_bold
            cell_hrs.alignment = align_center
            cell_hrs.fill = fill_zebra if mod_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, m_start, 8, m_end, 8, box_border)

            for r in range(m_start, m_end + 1):
                ws.row_dimensions[r].height = 22

            current_row = m_end + 1

        # Espaciador
        ws.row_dimensions[current_row].height = 10
        current_row += 1

        # ----------------------------------------------------------------------
        # 5. TABLA DOCENTES Y PERFILES EXPERTOS
        # ----------------------------------------------------------------------
        doc_header_1 = current_row
        doc_header_2 = current_row + 1

        ws.row_dimensions[doc_header_1].height = 20
        ws.row_dimensions[doc_header_2].height = 20

        # Col B: "DOCENTES"
        ws.merge_cells(start_row=doc_header_1, start_column=2, end_row=doc_header_2, end_column=2)
        cell_doc_title = ws.cell(row=doc_header_1, column=2, value="DOCENTES")
        cell_doc_title.font = font_table_header
        cell_doc_title.fill = fill_main_header
        cell_doc_title.alignment = align_center
        aplicar_borde_rango(ws, doc_header_1, 2, doc_header_2, 2, header_border)

        # Col C, D: "Nombre del Docente"
        ws.merge_cells(start_row=doc_header_1, start_column=3, end_row=doc_header_2, end_column=4)
        cell_doc_nom = ws.cell(row=doc_header_1, column=3, value="Nombre del Docente / Rol")
        cell_doc_nom.font = font_table_header
        cell_doc_nom.fill = fill_accent_header
        cell_doc_nom.alignment = align_center
        aplicar_borde_rango(ws, doc_header_1, 3, doc_header_2, 4, header_border)

        # Col E: "Contenido Módulo"
        ws.merge_cells(start_row=doc_header_1, start_column=5, end_row=doc_header_2, end_column=5)
        cell_doc_mod = ws.cell(row=doc_header_1, column=5, value="Módulo Asignado")
        cell_doc_mod.font = font_table_header
        cell_doc_mod.fill = fill_accent_header
        cell_doc_mod.alignment = align_center
        aplicar_borde_rango(ws, doc_header_1, 5, doc_header_2, 5, header_border)

        # Col F, G, H: "Experto"
        ws.merge_cells(start_row=doc_header_1, start_column=6, end_row=doc_header_2, end_column=8)
        cell_doc_exp = ws.cell(row=doc_header_1, column=6, value="Perfil de Experto / Requisitos y Credenciales")
        cell_doc_exp.font = font_table_header
        cell_doc_exp.fill = fill_accent_header
        cell_doc_exp.alignment = align_center
        aplicar_borde_rango(ws, doc_header_1, 6, doc_header_2, 8, header_border)

        current_row += 2

        docentes_list = prop.docentes_perfiles or []
        for d_idx, doc in enumerate(docentes_list, start=1):
            d_start = current_row
            d_end = current_row + 1

            ws.merge_cells(start_row=d_start, start_column=2, end_row=d_end, end_column=2)
            ws.cell(row=d_start, column=2, value="").fill = fill_zebra if d_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, d_start, 2, d_end, 2, box_border)

            # Nombre Docente (Col C, D)
            ws.merge_cells(start_row=d_start, start_column=3, end_row=d_end, end_column=4)
            cell_dn = ws.cell(row=d_start, column=3, value=doc.nombre_o_rol)
            cell_dn.font = font_bold
            cell_dn.alignment = align_left_center
            cell_dn.fill = fill_zebra if d_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, d_start, 3, d_end, 4, box_border)

            # Módulo Asignado (Col E)
            ws.merge_cells(start_row=d_start, start_column=5, end_row=d_end, end_column=5)
            cell_dm = ws.cell(row=d_start, column=5, value=doc.modulo_asignado)
            cell_dm.font = font_regular
            cell_dm.alignment = align_left_center
            cell_dm.fill = fill_zebra if d_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, d_start, 5, d_end, 5, box_border)

            # Perfil Experto (Col F, G, H)
            ws.merge_cells(start_row=d_start, start_column=6, end_row=d_end, end_column=8)
            cell_de = ws.cell(row=d_start, column=6, value=doc.perfil_experto)
            cell_de.font = font_regular
            cell_de.alignment = align_left_top
            cell_de.fill = fill_zebra if d_idx % 2 == 0 else PatternFill(fill_type=None)
            aplicar_borde_rango(ws, d_start, 6, d_end, 8, box_border)

            for r in range(d_start, d_end + 1):
                ws.row_dimensions[r].height = 24

            current_row = d_end + 1

        return ws

    def exportar_propuesta_individual(self, propuesta: PropuestaPrograma, output_file: Path) -> Path:
        """Genera un archivo Excel (.xlsx) individual para una propuesta específica."""
        wb = openpyxl.Workbook()
        ws = wb.active
        # Limpiar nombre de hoja para que no exceda 31 caracteres ni tenga caracteres inválidos
        sheet_title = re.sub(r"[\\/*?:\[\]]", "_", propuesta.id_propuesta)[:30]
        ws.title = sheet_title or "MIG_Propuesta"

        self.crear_hoja_mig(ws, propuesta)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_file)
        print(f"[EXCEL MIG] Archivo generado exitosamente: {output_file}")
        return output_file

    def exportar_portafolio_completo(self, json_path: Path = DEFAULT_INPUT_JSON, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
        """
        Lee el JSON de recomendaciones y exporta:
        1. Un archivo Excel individual por cada propuesta académica.
        2. Un archivo Excel consolidado con todas las propuestas en pestañas separadas.
        """
        if not json_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de recomendaciones: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        portafolio = PortafolioRecomendacionesIA.model_validate(data)
        output_dir.mkdir(parents=True, exist_ok=True)

        archivos_generados = []

        # 1. Archivo consolidado multi-hoja
        wb_master = openpyxl.Workbook()
        wb_master.remove(wb_master.active)  # Quitar hoja por defecto

        for idx, prop in enumerate(portafolio.propuestas, start=1):
            clean_name = re.sub(r"[^A-Za-z0-9_]", "_", prop.nombre_programa)[:25]
            nombre_archivo = f"{prop.id_propuesta}_{clean_name}_MIG.xlsx"
            ruta_individual = output_dir / nombre_archivo

            # Guardar individual
            self.exportar_propuesta_individual(prop, ruta_individual)
            archivos_generados.append(ruta_individual)

            # Agregar a master
            sheet_title = f"{prop.id_propuesta}_{prop.tipo_propuesta[:15]}"[:31]
            sheet_title = re.sub(r"[\\/*?:\[\]]", "_", sheet_title)
            ws_master = wb_master.create_sheet(title=sheet_title)
            self.crear_hoja_mig(ws_master, prop)

        ruta_master = output_dir / "ofertas_academicas_mig_consolidado.xlsx"
        wb_master.save(ruta_master)
        print(f"[EXCEL MIG] Libro consolidado generado exitosamente: {ruta_master}")

        return {
            "master": ruta_master,
            "individuales": archivos_generados,
            "total_propuestas": len(portafolio.propuestas)
        }

if __name__ == "__main__":
    exporter = MIGExcelExporter()
    res = exporter.exportar_portafolio_completo()
    print(f"\nProceso finalizado. Se generaron {res['total_propuestas']} propuestas en formato MIG.")
