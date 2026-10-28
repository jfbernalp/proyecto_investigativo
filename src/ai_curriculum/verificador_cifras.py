"""
Verificador de cifras de las propuestas generadas por la IA (REGLA DE ORO: no inventar cifras ni datos).

Extrae de los campos de texto de una propuesta los porcentajes, los montos de dinero y los conteos de
ofertas, y busca cada uno en el contexto de mercado con el que se generó. Lo que no aparece se marca como
"cifra sin respaldo" para que el aprobador lo vea y decida; la propuesta NO se bloquea.

No se revisan créditos, horas, semestres ni números del decreto: son datos institucionales y los
patrones solo capturan %, dinero y "N ofertas/vacantes". Las tarifas (inversion) se marcan siempre: el
observatorio no tiene tarifas, las fija la institución.
"""
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Set, Tuple

from src.ai_curriculum.curriculum_schemas import CifraSinRespaldo, PropuestaPrograma, VerificacionCifras

CAMPOS_EXCLUIDOS = {"id_propuesta", "tipo_propuesta", "estado", "version", "aprobado_por", "fecha_decision",
                    "motivo_rechazo", "historial_revisiones", "contexto_id", "verificacion_cifras",
                    "horario", "fecha_inicio_estimada", "fecha_terminacion_estimada", "proximas_ediciones",
                    "creditos_totales", "horas_totales"}
_NUM = r"\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?"
RE_PORCENTAJE = re.compile(rf"(?<![\w.,])({_NUM})\s?%")
RE_DINERO = re.compile(rf"(?:\$|\bCOP\b|\bUSD\b|\bUS\$)\s?({_NUM})\s*(millones|millón|mill\.?|M\b)?", re.IGNORECASE)
RE_DINERO_MILLONES = re.compile(rf"(?<![\w$.,])({_NUM})\s*(millones|millón|M)\s*(?:de\s+)?(?:pesos|COP)", re.IGNORECASE)
RE_CONTEO = re.compile(rf"(?<![\w.,%])({_NUM})\s+(?:ofertas|vacantes|avisos|empleos|publicaciones)", re.IGNORECASE)


def _a_numero(txt: str) -> float:
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", txt):          # separador de miles: 4.478.000 / 4,478,000
        return float(re.sub(r"[.,]", "", txt))
    return float(txt.replace(",", "."))


def _numeros_contexto(obj: Any) -> Set[float]:
    """Todos los valores numéricos del contexto (y sus valores absolutos: una prima -32,7 se lee '32,7 % menos')."""
    salida: Set[float] = set()
    if isinstance(obj, bool):
        return salida
    if isinstance(obj, (int, float)):
        salida.update({float(obj), abs(float(obj))})
    elif isinstance(obj, dict):
        for v in obj.values():
            salida |= _numeros_contexto(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            salida |= _numeros_contexto(v)
    return salida


def _textos(obj: Any, ruta: str = "") -> Iterable[Tuple[str, str]]:
    if isinstance(obj, str):
        yield ruta, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in CAMPOS_EXCLUIDOS:
                yield from _textos(v, f"{ruta}.{k}" if ruta else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _textos(v, f"{ruta}[{i}]")


def _respaldado(valor: float, texto_num: str, conocidos: Set[float], relativo: bool) -> bool:
    if relativo:   # dinero: tolera el redondeo a una cifra decimal en millones
        return any(c > 0 and abs(valor - c) / c <= 0.015 for c in conocidos)
    tolerancia = 0.05 if re.search(r"[.,]\d$|[.,]\d\d$", texto_num) else 0.5
    return any(abs(valor - c) <= tolerancia for c in conocidos)


def _fragmento(texto: str, inicio: int, fin: int, margen: int = 60) -> str:
    a, b = max(0, inicio - margen), min(len(texto), fin + margen)
    return ("…" if a else "") + texto[a:b].strip() + ("…" if b < len(texto) else "")


def verificar_propuesta(propuesta: PropuestaPrograma, contexto: Dict[str, Any]) -> VerificacionCifras:
    conocidos = _numeros_contexto({k: v for k, v in contexto.items() if k not in ("id", "fecha_contexto")})
    revisadas = 0
    sin_respaldo: List[CifraSinRespaldo] = []
    for campo, texto in _textos(propuesta.model_dump()):
        es_tarifa = campo.startswith("inversion")
        ocupados: List[Tuple[int, int]] = []
        hallazgos = []
        for patron, tipo in ((RE_DINERO_MILLONES, "dinero"), (RE_DINERO, "dinero"),
                             (RE_PORCENTAJE, "porcentaje"), (RE_CONTEO, "conteo de ofertas")):
            for m in patron.finditer(texto):
                if any(a <= m.start() < b or a < m.end() <= b for a, b in ocupados):
                    continue
                ocupados.append((m.start(), m.end()))
                hallazgos.append((m, tipo))
        for m, tipo in sorted(hallazgos, key=lambda x: x[0].start()):
            numero = m.group(1)
            valor = _a_numero(numero)
            if tipo == "dinero" and m.lastindex and m.lastindex >= 2 and m.group(2):
                valor *= 1_000_000
            if tipo == "porcentaje" and valor == 100 and not es_tarifa:
                continue    # "100 % práctico / virtual": retórica de modalidad, no una cifra de mercado
            revisadas += 1
            if es_tarifa:
                motivo = "Tarifa propuesta por la IA: el observatorio no tiene tarifas; la fija la institución."
            elif _respaldado(valor, numero, conocidos, relativo=(tipo == "dinero")):
                continue
            else:
                motivo = f"No aparece en el contexto de mercado {contexto.get('id')} (corte {contexto.get('ultimo_corte')})."
            sin_respaldo.append(CifraSinRespaldo(campo=campo, cifra=m.group(0).strip(), tipo=tipo, motivo=motivo,
                                                 fragmento=_fragmento(texto, m.start(), m.end())))
    return VerificacionCifras(contexto_id=contexto.get("id"), ultimo_corte=str(contexto.get("ultimo_corte")),
                              fecha_verificacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              cifras_revisadas=revisadas, sin_respaldo=sin_respaldo)
