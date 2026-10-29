"""
Verificador de cifras de las propuestas generadas por la IA (REGLA DE ORO: no inventar cifras ni datos).

Extrae de los campos de texto de una propuesta los porcentajes, los montos de dinero y los conteos de
ofertas, y busca cada uno en el contexto de mercado con el que se generó. Lo que no aparece se marca como
"cifra sin respaldo" para que el aprobador lo vea y decida; la propuesta NO se bloquea.

No se revisan créditos, horas, semestres ni números del decreto: son datos institucionales y los
patrones solo capturan %, dinero y "N ofertas/vacantes". Las tarifas (inversion) se marcan siempre: el
observatorio no tiene tarifas, las fija la institución.

Atribución: si un porcentaje o un conteo solo existe en el contexto como dato de una habilidad o de un
rol, la habilidad o el rol mencionado más cerca de la cifra en el texto debe ser ese mismo
("AWS: 45,4 %" se marca si 45,4 % es el dato de ETL). Si cerca de la cifra no se nombra ninguna
habilidad ni rol, también se marca: el aprobador no puede saber de dónde sale ("+45 % sobre la media").
"""
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

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


def _normalizar(texto: str) -> str:
    """Minúsculas sin tildes, conservando la longitud (las posiciones siguen valiendo en el texto original)."""
    def base(c):
        d = "".join(x for x in unicodedata.normalize("NFKD", c) if not unicodedata.combining(x))
        return d if len(d) == 1 else c
    return "".join(base(c) for c in texto.lower())


# Partes de un nombre demasiado generales para identificar una habilidad o un rol
ALIAS_GENERICOS = {"datos", "data", "software", "ia", "ai", "general", "visualizacion"}


def _alias(nombre: str) -> Set[str]:
    """'Google Cloud (GCP)' → {google cloud (gcp), google cloud, gcp}; 'ETL / Pipelines de Datos' → {…, etl, pipelines de datos}."""
    n = _normalizar(nombre).strip()
    alias = {n}
    fuera = re.sub(r"\(.*?\)", "", n).strip()
    alias.add(fuera)
    alias.update(x.strip() for x in re.findall(r"\((.*?)\)", n))
    for parte in re.split(r"\s+/\s+|\s+&\s+", fuera):
        alias.add(parte.strip())
    return {a for a in alias if a and a not in ALIAS_GENERICOS}


def _indexar(obj: Any, entidades: Tuple[str, ...] = (), salida=None) -> List[Tuple[float, Tuple[str, ...]]]:
    """
    (valor, entidades) de cada número del contexto: la habilidad o el rol de su registro y los que lo
    contienen (el % de ETL dentro del rol Data Engineer pertenece a ambos). () = cifra global.
    """
    salida = [] if salida is None else salida
    if isinstance(obj, dict):
        propia = entidades + tuple(x for x in (obj.get("habilidad"), obj.get("rol")) if x)
        for v in obj.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                salida.extend([(float(v), propia), (abs(float(v)), propia)])
            elif isinstance(v, (dict, list)):
                _indexar(v, propia, salida)
    elif isinstance(obj, list):
        for v in obj:
            _indexar(v, entidades, salida)
    return salida


def _menciones(texto_norm: str, alias_por_entidad: Dict[str, Set[str]]) -> List[Tuple[int, int, FrozenSet[str]]]:
    """Posiciones de cada mención de habilidad/rol en el texto, con las entidades que puede nombrar."""
    por_alias: Dict[str, Set[str]] = {}
    for ent, alias in alias_por_entidad.items():
        for a in alias:
            por_alias.setdefault(a, set()).add(ent)
    salida = []
    for a, ents in por_alias.items():
        # Cada palabra admite plural ("ingenieros de datos")
        patron = r"\s+".join(re.escape(w) + r"(?:e?s)?" for w in a.split())
        for m in re.finditer(rf"(?<!\w){patron}(?!\w)", texto_norm):
            salida.append((m.start(), m.end(), frozenset(ents)))
    return salida


def _entidades_referidas(texto: str, menciones, inicio: int, fin: int, fin_cifra_anterior: int,
                         antes: int = 150, despues: int = 40) -> Optional[FrozenSet[str]]:
    """
    Habilidades o roles a los que puede referirse la cifra:
    1. los nombrados entre la cifra anterior y esta ("SQL en el 62,3 %, AWS en el 45,4 %" → 45,4 es de AWS;
       "AWS y Azure en el 44,5 % y 36,3 %" → AWS o Azure);
    2. si ahí no hay ninguno, los nombrados antes en la misma oración ("ETL… (259 ofertas, 45,4 %)");
    3. si tampoco, el siguiente sin separador de por medio ("el 45,4 % pide ETL").
    """
    oracion = max(inicio - antes, *(m.end() for m in re.finditer(r"\.(?!\d)\s", texto[:inicio])), 0)
    for desde in (max(oracion, fin_cifra_anterior), oracion):
        previas = frozenset(e for a, b, ents in menciones if desde <= a and b <= inicio for e in ents)
        if previas:
            return previas
    siguientes = [(a, ents) for a, b, ents in menciones
                  if fin <= a <= fin + despues and not re.search(r"[,;.]\s", texto[fin:a])]
    return min(siguientes, key=lambda x: x[0])[1] if siguientes else None


def _candidatos(valor: float, texto_num: str, indice) -> List[Tuple[str, ...]]:
    tolerancia = 0.05 if re.search(r"[.,]\d$|[.,]\d\d$", texto_num) else 0.5
    return [ent for v, ent in indice if abs(valor - v) <= tolerancia]


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
    datos = {k: v for k, v in contexto.items() if k not in ("id", "fecha_contexto")}
    conocidos = _numeros_contexto(datos)
    indice = _indexar(datos)
    alias_por_entidad = {ent: _alias(ent) for _, ents in indice for ent in ents}
    revisadas = 0
    sin_respaldo: List[CifraSinRespaldo] = []
    for campo, texto in _textos(propuesta.model_dump()):
        es_tarifa = campo.startswith("inversion")
        menciones = _menciones(_normalizar(texto), alias_por_entidad)
        ocupados: List[Tuple[int, int]] = []
        hallazgos = []
        for patron, tipo in ((RE_DINERO_MILLONES, "dinero"), (RE_DINERO, "dinero"),
                             (RE_PORCENTAJE, "porcentaje"), (RE_CONTEO, "conteo de ofertas")):
            for m in patron.finditer(texto):
                if any(a <= m.start() < b or a < m.end() <= b for a, b in ocupados):
                    continue
                ocupados.append((m.start(), m.end()))
                hallazgos.append((m, tipo))
        fin_anterior = 0
        for m, tipo in sorted(hallazgos, key=lambda x: x[0].start()):
            fin_cifra_anterior, fin_anterior = fin_anterior, m.end()
            numero = m.group(1)
            valor = _a_numero(numero)
            if tipo == "dinero" and m.lastindex and m.lastindex >= 2 and m.group(2):
                valor *= 1_000_000
            if tipo == "porcentaje" and valor == 100 and not es_tarifa:
                continue    # "100 % práctico / virtual": retórica de modalidad, no una cifra de mercado
            if tipo == "porcentaje" and re.search(r"(IC|intervalo de confianza|confianza( del)?)\s*(al\s*)?$",
                                                   texto[max(0, m.start() - 30):m.start()], re.IGNORECASE):
                continue    # "IC 95 %": nivel de confianza, no una cifra de mercado
            revisadas += 1
            if es_tarifa:
                motivo = "Tarifa propuesta por la IA: el observatorio no tiene tarifas; la fija la institución."
            elif tipo != "dinero" and _candidatos(valor, numero, indice):
                candidatos = _candidatos(valor, numero, indice)
                cercana = _entidades_referidas(texto, menciones, m.start(), m.end(), fin_cifra_anterior)
                if () in candidatos or (cercana and any(cercana & set(c) for c in candidatos)):
                    continue
                duenos = ", ".join(sorted({c[-1] for c in candidatos})[:3])
                motivo = (f"La cifra está en el contexto {contexto.get('id')}, pero corresponde a {duenos}, "
                          f"no a {', '.join(sorted(cercana))}." if cercana else
                          f"No se identifica de qué dato del observatorio sale: el texto no nombra la habilidad o el "
                          f"rol, y en el contexto {contexto.get('id')} el número solo coincide con el dato de {duenos}.")
            elif _respaldado(valor, numero, conocidos, relativo=(tipo == "dinero")):
                continue
            else:
                motivo = f"No aparece en el contexto de mercado {contexto.get('id')} (corte {contexto.get('ultimo_corte')})."
            sin_respaldo.append(CifraSinRespaldo(campo=campo, cifra=m.group(0).strip(), tipo=tipo, motivo=motivo,
                                                 fragmento=_fragmento(texto, m.start(), m.end())))
    return VerificacionCifras(contexto_id=contexto.get("id"), ultimo_corte=str(contexto.get("ultimo_corte")),
                              fecha_verificacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              cifras_revisadas=revisadas, sin_respaldo=sin_respaldo)
