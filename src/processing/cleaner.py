import re
from typing import Any, Optional
import pandas as pd
import numpy as np
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

def limpiar_caracteres_ilegales(x: Any) -> Any:
    """
    Remueve caracteres de control no imprimibles (ASCII 0-31) que rompen openpyxl y Excel.
    Soporta strings, listas y valores escalares.
    """
    if isinstance(x, str):
        return ILLEGAL_CHARACTERS_RE.sub("", x)
    elif isinstance(x, list):
        return [limpiar_caracteres_ilegales(i) for i in x]
    return x

def sanitizar_dataframe_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitiza todas las columnas de un DataFrame para que puedan ser escritas a Excel sin error.
    """
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].apply(limpiar_caracteres_ilegales)
    return df_clean

def detectar_moneda_y_mercado(portal: str, val: Any) -> tuple:
    """
    Identifica la moneda original y clasifica el tipo de mercado.
    Retorna: (moneda_str, tipo_mercado_str)
    """
    portal_str = str(portal) if pd.notna(portal) else ""
    val_lower = str(val).lower() if pd.notna(val) else ""

    if "usd" in val_lower or ("$" in val_lower and any(t in val_lower for t in ["monthly", "yearly", "hourly", "hour", "year", "month"])):
        return "USD", "Mercado Internacional (Remoto - USD)"
    elif "cad" in val_lower:
        return "CAD", "Mercado Internacional (Remoto - USD)"
    elif "eur" in val_lower or "€" in val_lower:
        return "EUR", "Mercado Internacional (Remoto - USD)"
    elif "gbp" in val_lower or "£" in val_lower:
        return "GBP", "Mercado Internacional (Remoto - USD)"
    elif portal_str in ["Torre.ai", "GetOnBoard"]:
        return "USD", "Mercado Internacional (Remoto - USD)"
    else:
        return "COP", "Mercado Local (Colombia - COP)"

def limpiar_salario_numerico(val) -> float:
    """
    Convierte textos salariales heterogéneos de múltiples portales a valor numérico mensual en COP:
    - CompuTrabajo: '$ 7.000.000,00 (Mensual)' -> 7000000.0
    - ElEmpleo: '$2,5 a $3 millones' -> 2750000.0
    - Get on Board: 'USD 5.000 a 5.000' -> 20000000.0
    - Torre.ai: 'USD 97.600 a 139.000 (yearly)' -> 39433333.3
    - Torre.ai: 'USD 40 (hourly)' -> 25600000.0
    """
    if not isinstance(val, str) or any(x in val.lower() for x in ["a convenir", "no especificado", "confidencial", "sin especificar"]):
        return np.nan

    val_clean = val.lower().strip()

    # Tasas de cambio representativas respecto al COP
    TASAS_CAMBIO = {
        "usd": 4000.0,
        "cad": 2900.0,
        "eur": 4300.0,
        "gbp": 5100.0
    }

    # Detectar si es moneda extranjera
    tasa_aplicable = None
    for cur, tasa in TASAS_CAMBIO.items():
        if cur in val_clean:
            tasa_aplicable = tasa
            break
    if not tasa_aplicable and any(t in val_clean for t in ["monthly", "yearly", "hourly"]):
        tasa_aplicable = 4000.0  # Default a USD si usa términos anglosajones

    if tasa_aplicable:
        nums = re.findall(r"(\d+(?:[.,]\d+)?)", val_clean.replace(".", ""))
        if nums:
            vals_float = [float(n.replace(",", ".")) for n in nums]
            prom_ext = float(np.mean(vals_float))
            
            # Normalizar periodicidad a mensual
            if "hourly" in val_clean or "hora" in val_clean:
                prom_ext = prom_ext * 160.0  # 160 horas laborales mensuales
            elif "yearly" in val_clean or "año" in val_clean or prom_ext > 20000:
                prom_ext = prom_ext / 12.0   # Anual a mensual
                
            return prom_ext * tasa_aplicable

    # Caso ElEmpleo: formato '$X,X a $Y,Y millones' o '$X a $Y millones'
    if "mill" in val_clean:
        # Buscar números (posiblemente con comas o puntos decimales)
        nums = re.findall(r"(\d+(?:[.,]\d+)?)", val_clean)
        if nums:
            vals_float = [float(n.replace(",", ".")) * 1_000_000 for n in nums]
            return float(np.mean(vals_float))

    # Caso CompuTrabajo / Formato estándar con puntos y comas
    # Si contiene ' a ' (rango tradicional ej. '$ 3.000.000 a $ 4.000.000')
    if " a " in val_clean:
        partes = val_clean.split(" a ")
        partes_nums = []
        for p in partes:
            num_str = re.sub(r"[^\d]", "", p)
            if num_str:
                partes_nums.append(float(num_str))
        if partes_nums:
            return float(np.mean(partes_nums))

    # Valor único con formato '$ 7.000.000,00 (Mensual)'
    num_str = re.sub(r"[^\d,]", "", val_clean)
    if not num_str:
        return np.nan
    if "," in num_str:
        num_str = num_str.split(",")[0]
    num_str = num_str.replace(".", "")
    try:
        res = float(num_str)
        # Control de escala: si es menor a 1000, asumimos millones
        if 0 < res <= 50:
            return res * 1_000_000
        return res
    except:
        return np.nan

def categorizar_seniority(anios: Optional[float] = None) -> str:
    """
    Agrupa los años de experiencia en niveles estándar de la industria.
    """
    if pd.isna(anios):
        return "No especificado"
    anios_num = float(anios)
    if anios_num <= 1:
        return "Junior / Trainee (0-1 años)"
    elif 2 <= anios_num <= 3:
        return "Semi-Senior (2-3 años)"
    elif 4 <= anios_num <= 5:
        return "Senior (4-5 años)"
    else:
        return "Lead / Principal (> 5 años)"

def mapear_educacion_ordinal(nivel_str: str) -> float:
    """
    Convierte niveles educativos a escala ordinal numérica.
    """
    if not isinstance(nivel_str, str):
        return 2.5
    mapping = {
        "Bachillerato / Educación Media": 1.0,
        "Educación Básica Secundaria": 1.0,
        "Universidad / Carrera técnica": 2.0,
        "Universidad / Carrera Tecnológica": 2.0,
        "Universidad / Carrera Profesional": 3.0,
        "Postgrado / Especialización": 4.0,
        "Maestría": 5.0,
        "Doctorado": 6.0
    }
    for k, v in mapping.items():
        if k.lower() in nivel_str.lower():
            return v
    return 2.5


# ==============================================================================
# FILTRO DE RELEVANCIA TEMÁTICA ESTRICTO (DATA SCIENCE & ANALYTICS)
# ==============================================================================

PALABRAS_CLAVE_RELEVANTES = [
    r"\bdat[oa]s?\b", r"\bdata\b", r"\bscientist\b", r"\bcient[ií]fic[ao]\b", 
    r"\bdata\s*analyst\b", r"\banalista\s*de\s*datos\b", r"\bbi\b", r"\bbusiness\s*intelligence\b",
    r"\bmachine\s*learning\b", r"\bia\b", r"\bai\b", r"\bestad[ií]stic[ao]\b",
    r"\binteligencia\s*de\s*negocios\b", r"\bbig\s*data\b", r"\bpython\b", r"\bsql\b",
    r"\bpower\s*bi\b", r"\btableau\b", r"\betl\b", r"\bdeep\s*learning\b",
    r"\bdata\s*engineer\b", r"\bingenier[oa]\s*de\s*datos\b"
]

PALABRAS_CLAVE_EXCLUSION = [
    r"\benfermer[ií]a\b", r"\bqu[ií]mic[ao]\b", r"\bmicrobi[oó]log[ao]\b",
    r"\bcirug[ií]a\b", r"\bhospitalizaci[oó]n\b", r"\boperari[ao]\b",
    r"\bconductor[a]?\b", r"\bventas?\b", r"\bcajero[a]?\b", r"\bcocina\b",
    r"\basistente\s*de\s*ventas\b", r"\bencuestador[a]?\b", r"\bmec[aá]nic[ao]\b",
    r"\barchivo\b", r"\binterventor[ií]a\b", r"\blaboratorio\s*sector\s*[oó]ptico\b",
    r"\bauxiliar\s*financiero\b", r"\bcontable\b", r"\bn[oó]mina\b", r"\bdise[nñ]o\s*gr[aá]fico\b",
    r"\bselecci[oó]n\b", r"\brecursos\s*humanos\b", r"\brrhh\b", r"\bpsic[oó]log[ao]\b",
    r"\belectr[oó]nic[ao]\b", r"\bmecatr[oó]nic[ao]\b", r"\bseguridad\s*y\s*salud\b"
]

def es_oferta_relevante(titulo: str, descripcion: str = "") -> bool:
    """
    Validador semántico estricto: asegura que la vacante pertenezca exclusivamente
    a Ciencia de Datos, Análisis de Datos, Ingeniería de Datos o BI.
    """
    if not isinstance(titulo, str) or not titulo.strip():
        return False

    titulo_lower = titulo.lower().strip()

    # 1. Descartar si el título contiene palabras explícitas de exclusión
    for exc_pattern in PALABRAS_CLAVE_EXCLUSION:
        if re.search(exc_pattern, titulo_lower):
            return False

    # 2. Requerir que el título contenga al menos una palabra clave de analítica/datos
    for inc_pattern in PALABRAS_CLAVE_RELEVANTES:
        if re.search(inc_pattern, titulo_lower):
            return True

    return False
