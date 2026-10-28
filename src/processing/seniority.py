"""
Detección de la experiencia y el nivel (seniority) que pide una oferta.

REGLA DE ORO: solo se registra lo que la oferta dice de forma explícita. Si no lo dice, el resultado
es None / "No especificado" (nunca un valor por defecto). Cada nivel queda con su fuente:
"años explícitos", "título" o "portal".
"""
import re
from typing import Any, Dict, Optional, Tuple

NO_ESPECIFICADO = "No especificado"
NIVELES = ("Practicante", "Junior", "Semi-Senior", "Senior", "Líder")

_NUM = r"(\d{1,2}(?:[.,]5)?)"
_ANIOS = r"(?:años?|anos?|years?|yrs?)"
# Requisito explícito de experiencia, en orden de aparición en el texto. Se toma el primero
# (suele ser el requisito general; los siguientes suelen ser subrequisitos: "al menos 1 en X").
_PATRONES_ANIOS = [
    re.compile(rf"{_NUM}\s*(?:a|-|–|y|to)\s*{_NUM}\s*{_ANIOS}", re.I),                                   # 3 a 5 años
    re.compile(rf"(?:m[ií]nimo|al menos|at least|minimum(?: of)?)\s*(?:de\s*)?{_NUM}\s*{_ANIOS}", re.I),  # mínimo 2 años
    re.compile(rf"experiencia(?:\s+(?:laboral|profesional|comprobable|m[ií]nima|relacionada))*"
               rf"\s*(?:de|:|m[ií]nima de)?\s*{_NUM}\+?\s*{_ANIOS}", re.I),                              # experiencia: 2 años
    re.compile(rf"{_NUM}\+?\s*{_ANIOS}\s*(?:(?:de|of)\s+)?(?:experiencia|experience)", re.I),             # 3 años de experiencia
]
_MESES = re.compile(r"(\d{1,2})\s*meses\s*de\s*experiencia", re.I)
_SIN_EXPERIENCIA = re.compile(r"sin experiencia|no requiere experiencia|menos de (?:1|un) año de experiencia|"
                              r"no experience required", re.I)
# "empresa con más de 30 años de experiencia" habla de la compañía, no del cargo
_DE_LA_EMPRESA = re.compile(r"(?:empresa|compañ[ií]a|organizaci[oó]n|grupo|somos|trayectoria|"
                            r"m[aá]s de\s*\d{2}\s*años)", re.I)
MAX_ANIOS_PLAUSIBLES = 15

_NIVEL_TITULO = [
    ("Practicante", re.compile(r"\b(practicante|pr[aá]cticas?|aprendiz|trainee|intern(ship)?|pasant[ei])\b", re.I)),
    ("Semi-Senior", re.compile(r"\b(semi[\s-]?senior|ssr|mid[\s-]?level)\b", re.I)),
    ("Junior", re.compile(r"\b(junior|jr\.?)\b", re.I)),
    ("Senior", re.compile(r"\b(senior|sr\.?)\b", re.I)),
    ("Líder", re.compile(r"\b(l[ií]der|lead|principal|head of|jefe|gerente|manager|director[a]?)\b", re.I)),
]

# Criterios publicados por el portal (LinkedIn "Nivel de antigüedad"; ElEmpleo en el texto de requisitos).
# Solo los inequívocos: "Intermedio"/"Mid-Senior level" y "Algo de responsabilidad"/"Associate" abarcan
# más de un nivel y no se traducen.
_NIVEL_PORTAL = {
    "prácticas": "Practicante", "practicas": "Practicante", "internship": "Practicante",
    "sin experiencia": "Junior", "entry level": "Junior",
    "director": "Líder", "ejecutivo": "Líder", "executive": "Líder",
}


def _a_float(texto: str) -> float:
    return float(texto.replace(",", "."))


def extraer_anios_experiencia(texto: Any) -> Optional[float]:
    """Mínimo de años de experiencia que la oferta pide explícitamente, o None si no lo dice."""
    if not isinstance(texto, str) or not texto.strip():
        return None
    candidatos = []
    for patron in _PATRONES_ANIOS:
        for m in patron.finditer(texto):
            contexto = texto[max(0, m.start() - 40):m.start()]
            if _DE_LA_EMPRESA.search(contexto + m.group(0)):
                continue
            valor = min(_a_float(g) for g in m.groups() if g)
            if valor <= MAX_ANIOS_PLAUSIBLES:
                candidatos.append((m.start(), valor))
    for m in _MESES.finditer(texto):
        candidatos.append((m.start(), round(int(m.group(1)) / 12, 2)))
    for m in _SIN_EXPERIENCIA.finditer(texto):
        candidatos.append((m.start(), 0.0))
    return min(candidatos)[1] if candidatos else None


def nivel_por_anios(anios: Optional[float]) -> Optional[str]:
    """
    Misma convención que categorizar_seniority() (0-1 Junior, 2-3 Semi-Senior, 4-5 Senior, > 5 Líder),
    con rangos contiguos: antes 1,5 o 3,5 años caían en "Lead / Principal".
    """
    if anios is None:
        return None
    if anios < 2:
        return "Junior"
    if anios < 4:
        return "Semi-Senior"
    if anios < 6:
        return "Senior"
    return "Líder"


def nivel_por_titulo(titulo: Any) -> Optional[str]:
    if not isinstance(titulo, str):
        return None
    for nivel, patron in _NIVEL_TITULO:
        if patron.search(titulo):
            return nivel
    return None


def nivel_por_portal(oferta: Dict[str, Any]) -> Optional[str]:
    criterios = oferta.get("Criterios_detalle") or {}
    if isinstance(criterios, dict):
        valor = (criterios.get("Nivel de antigüedad") or criterios.get("Seniority level") or "").strip().lower()
        if valor in _NIVEL_PORTAL:
            return _NIVEL_PORTAL[valor]
    requisitos = str(oferta.get("Requisitos") or "")
    if re.search(r"\|\s*Profesional Senior\s*\|", requisitos):
        return "Senior"
    return None


def determinar_seniority(oferta: Dict[str, Any]) -> Tuple[Optional[float], str, str]:
    """
    (años mínimos explícitos, nivel, fuente). Prioridad: años explícitos > título > portal.
    Si nada lo indica: (None, "No especificado", "no especificado").
    """
    texto = " ".join(str(oferta.get(k) or "") for k in ("Requisitos", "Descripcion", "Descripcion_detalle"))
    anios = extraer_anios_experiencia(texto)
    if anios is not None:
        return anios, nivel_por_anios(anios), "años explícitos"
    nivel = nivel_por_titulo(oferta.get("Nombre Oferta"))
    if nivel:
        return None, nivel, "título"
    nivel = nivel_por_portal(oferta)
    if nivel:
        return None, nivel, "portal"
    return None, NO_ESPECIFICADO, "no especificado"
