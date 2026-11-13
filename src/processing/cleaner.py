import re
import unicodedata
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

def neutralizar_formula(x: Any) -> Any:
    """
    Evita la inyección de fórmulas al abrir el archivo en Excel: un texto extraído de un portal que
    empiece por =, +, @, tabulación o "-letra" se guardaría como fórmula. Se antepone un apóstrofo.
    "-5" o "- viñeta" no se tocan (no son fórmulas ejecutables).
    """
    if not isinstance(x, str) or not x:
        return x
    if x[0] in "=+@\t\r" or (x[0] == "-" and len(x) > 1 and x[1].isalpha()):
        return "'" + x
    return x


def sanitizar_dataframe_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitiza todas las columnas de un DataFrame para que puedan ser escritas a Excel sin error.
    """
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].apply(lambda v: neutralizar_formula(limpiar_caracteres_ilegales(v)))
    return df_clean

# Portales cuyas vacantes son remotas para empresas del exterior (pagan en moneda extranjera)
PORTALES_INTERNACIONALES = {"Torre.ai", "GetOnBoard", "Remotive"}
MERCADO_INTERNACIONAL = "Mercado Internacional (Remoto - USD)"
MERCADO_LOCAL = "Mercado Local (Colombia - COP)"
# Solo palabras completas o símbolos: "cad" dentro de "No especificado" no es dólar canadiense.
PATRONES_MONEDA = (
    ("USD", r"\busd\b|\bus\$"),
    ("CAD", r"\bcad\b|\bc\$"),
    ("EUR", r"\beur\b|€"),
    ("GBP", r"\bgbp\b|£"),
)


def detectar_moneda_y_mercado(portal: str, val: Any) -> tuple:
    """
    Identifica la moneda original y clasifica el tipo de mercado.
    Internacional: salario en moneda extranjera, o portal de empleo remoto internacional.
    Local: el resto (todas las búsquedas se hacen con ubicación Colombia).
    Retorna: (moneda_str, tipo_mercado_str)
    """
    portal_str = str(portal) if pd.notna(portal) else ""
    val_lower = str(val).lower() if pd.notna(val) else ""

    for moneda, patron in PATRONES_MONEDA:
        if re.search(patron, val_lower):
            return moneda, MERCADO_INTERNACIONAL
    if "$" in val_lower and any(t in val_lower for t in ["monthly", "yearly", "hourly", "hour", "year", "month"]):
        return "USD", MERCADO_INTERNACIONAL
    if portal_str in PORTALES_INTERNACIONALES:
        return "USD", MERCADO_INTERNACIONAL
    return "COP", MERCADO_LOCAL

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
    # Rangos contiguos: antes 1,5 o 3,5 años no cabían en ningún rango y caían en "Lead / Principal"
    if anios_num < 2:
        return "Junior / Trainee (0-1 años)"
    elif anios_num < 4:
        return "Semi-Senior (2-3 años)"
    elif anios_num < 6:
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

ROL_CIENTIFICO = "Científico de Datos (Data Scientist)"
ROL_ML = "Machine Learning / AI Engineer"
ROL_INGENIERO = "Ingeniero de Datos (Data Engineer)"
ROL_BI = "Analista de BI & Visualización"
ROL_ANALISTA = "Analista de Datos (Data Analyst)"
ROL_DESARROLLADOR = "Desarrollador de Software / Datos"
ROL_SIN_CLASIFICAR = "Sin clasificar"

_IA = r"(?:machine learning|ml|ai|ia|mlops|llms?|genai|gen ai|deep learning|nlp|inteligencia artificial|aprendizaje automatico|computer vision|vision artificial)"
# Lo que no es del tema aunque diga «data»: centros de datos, digitación, privacidad
_RUIDO_ROL = re.compile(r"\bdata cent(?:er|re)s?\b|\bdata entry\b|\bvoz y datos\b|\bproteccion de datos\b|\bdatos personales\b")

# Nivel 1: frases que nombran el rol. Nivel 2: palabras del tema, solo si ninguna frase coincide.
# Dentro de un nivel gana la coincidencia más temprana: en los títulos el cargo va primero
# («Data Engineer - Data Science», «Analista de datos (power bi/etl)»).
# Todo con límites de palabra sobre el título sin tildes: «ia» ya no coincide dentro de «gerencia» ni «bi» dentro de «bilingüe».
_REGLAS_ROL_N1 = [
    (ROL_CIENTIFICO, r"\bdata scien(?:tist|ce)s?\b|\bcientific[oa]s? de datos\b|\bciencias? de datos\b|\bscientists?\b"),
    (ROL_ML, rf"\b{_IA}(?: \w+){{0,2}} (?:engineers?|ingenier[oa]s?|developers?|desarrollador(?:es)?|architects?|arquitect[oa]s?|especialistas?|specialists?)\b"
             rf"|\b(?:ingenier[oa]s?|desarrollador(?:es)?|especialistas?|arquitect[oa]s?) (?:de |en )?{_IA}\b|\bmlops\b"),
    (ROL_INGENIERO, r"\bingenier[oa]s?(?: \w+){0,4} datos\b|\bingenieria de datos\b|\bdata engineering\b|\barquitect[oa]s? de datos\b"
                    r"|\b(?:data|analytics|database|etl|big data)(?: (?!visuali)\w+)? (?:engineers?|architects?|modell?ers?|builders?)\b"
                    r"|\b(?:administrador(?:es)?|desarrollador(?:es)?|ingenier[oa]s?)(?: de)? bases? de datos\b|\bdba\b|\bmodelador de datos\b"),
    (ROL_BI, r"\bbi\b|\bbusiness intelligence\b|\binteligencia de negocios?\b|\bpower bi\b|\btableau\b|\bqlik\b|\blooker\b"
             r"|\bvisualizacion de datos\b|\bdata visuali[sz]ation\b"),
    (ROL_ANALISTA, r"\banalistas?(?: \w+){0,3} (?:de )?datos\b|\bdata analy(?:st|sts|ts|tics|sis)\b|\banalisis de datos\b"),
    (ROL_DESARROLLADOR, r"\bdesarrollador(?:es)?\b|\bdevelopers?\b|\bsoftware\b|\bfull ?stack\b|\bback ?end\b|\bprogramador(?:es)?\b"),
]
_REGLAS_ROL_N2 = [
    (ROL_ML, rf"\b{_IA}\b"),
    (ROL_INGENIERO, r"\betl\b|\belt\b|\bbig data\b|\bdata warehouse\b|\bdatabricks\b|\bdata platform\b|\bintegracion de datos\b|\bbases? (?:de )?datos\b"),
    (ROL_ANALISTA, r"\banalistas?\b|\banalysts?\b|\banalytics\b|\banalitica\b|\banalisis\b"),
    (ROL_CIENTIFICO, r"\bcientific[oa]s?\b|\bscience\b|\binvestigador(?:es|a)?\b|\bestadistic[oa]s?\b|\bestadistica\b|\bdata mining\b|\bmineria de datos\b"),
]
_REGLAS_ROL = [[(rol, re.compile(patron)) for rol, patron in nivel] for nivel in (_REGLAS_ROL_N1, _REGLAS_ROL_N2)]


def _normalizar_titulo(titulo: str) -> str:
    """Minúsculas, sin tildes, sin marcas de género («ingeniero(a)», «ingeniero/a») y solo letras y números."""
    t = unicodedata.normalize("NFKD", titulo.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\((?:a|as|os|es)\)|/(?:a|as)\b", "", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def clasificar_rol_tecnico(titulo: str) -> str:
    """
    Clasifica el rol a partir del título del cargo (Nombre Oferta), en dos niveles: primero frases que nombran el
    rol («ingeniero de datos», «data scientist»), luego palabras del tema («etl», «analytics»); en cada nivel gana la
    que aparece primero en el título. Si nada coincide,
    devuelve «Sin clasificar» en vez de asignar un rol por defecto (antes: Científico de Datos, 23 % de las ofertas).
    """
    if not isinstance(titulo, str) or not titulo.strip():
        return ROL_SIN_CLASIFICAR
    t = _RUIDO_ROL.sub(" ", _normalizar_titulo(titulo))
    for nivel in _REGLAS_ROL:
        coincidencias = [(m.start(), i, rol) for i, (rol, patron) in enumerate(nivel) if (m := patron.search(t))]
        if coincidencias:
            return min(coincidencias)[2]
    return ROL_SIN_CLASIFICAR
    t = titulo.lower().strip()
    
    # 1. Machine Learning & MLOps / AI Engineer
    if any(k in t for k in ["machine learning", "ml engineer", "ai engineer", "inteligencia artificial", "deep learning", "nlp", "ia"]):
        return "Machine Learning / AI Engineer"
    
    # 2. Data Engineer / Arquitecto / ETL / Big Data
    if any(k in t for k in ["ingeniero de datos", "data engineer", "arquitecto de datos", "data architect", "etl", "big data", "data governance"]):
        return "Ingeniero de Datos (Data Engineer)"
        
    # 3. BI / Business Intelligence / Visualización
    if any(k in t for k in ["bi", "business intelligence", "power bi", "tableau", "inteligencia de negocios", "storytelling"]):
        return "Analista de BI & Visualización"
        
    # 4. Data Analyst / Analista de Datos
    if any(k in t for k in ["analista de datos", "data analyst", "analista de informaci", "analitica", "analítica", "analyst"]):
        return "Analista de Datos (Data Analyst)"
        
    # 5. Data Scientist / Científico de Datos
    if any(k in t for k in ["científico", "cientifico", "data scientist", "science", "investigador", "scientist"]):
        return "Científico de Datos (Data Scientist)"
        
    # 6. Desarrollador / Developer
    if any(k in t for k in ["desarrollador", "developer", "software", "full stack", "backend"]):
        return "Desarrollador de Software / Datos"
        
    return "Científico de Datos (Data Scientist)"

