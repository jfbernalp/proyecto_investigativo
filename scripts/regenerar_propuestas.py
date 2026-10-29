"""
Regenera propuestas existentes con el contexto de mercado verificado (decisión de Juan, 27-oct-2026).

Por cada propuesta: si está APROBADA o RECHAZADA se reabre (queda en la auditoría y el Excel aprobado se
conserva); luego pasa a EN_AJUSTE y la IA la refina a v+1 con el contexto vigente y las reglas de
evidencia. El verificador marca las cifras sin respaldo y la nueva versión queda PENDIENTE de aprobación:
la decisión final es del aprobador. Si la IA falla, la propuesta vuelve a su versión anterior.

Uso:  python scripts/regenerar_propuestas.py                 # simulación: muestra qué haría
      python scripts/regenerar_propuestas.py --ejecutar [PROP_01 PROP_03 ...]
      python scripts/regenerar_propuestas.py --reverificar   # solo recalcula las marcas (tras mejorar el
                                                              # verificador); no cambia el contenido
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ai_curriculum.contexto_mercado import cargar_contexto  # noqa: E402
from src.ai_curriculum.curriculum_engine import (  # noqa: E402
    ESTADOS_REABRIBLES, LOCK_PORTAFOLIO, CurriculumIntelligenceEngine,
)
from src.ai_curriculum.curriculum_schemas import EstadoPropuesta  # noqa: E402
from src.ai_curriculum.gap_analyzer import contexto_para_verificar  # noqa: E402
from src.ai_curriculum.verificador_cifras import verificar_propuesta  # noqa: E402

USUARIO = "Observatorio UniCafam"
ROL = "Regeneración con contexto verificado"
FEEDBACK = (
    "Regeneración institucional con el contexto de mercado verificado del observatorio. Mantenga el tipo de "
    "programa, su nivel, créditos y horas. Revise el enfoque y los módulos a la luz de la demanda de "
    "habilidades y de los roles del contexto, y reemplace TODAS las cifras de mercado por cifras del contexto "
    "(con su n y el corte) o por 'Dato no disponible en el observatorio'. Tarifas: 'Por definir según "
    "tarifario institucional'."
)


def reverificar(engine):
    """Recalcula verificacion_cifras de cada versión vigente con el contexto con que se generó."""
    with LOCK_PORTAFOLIO:
        portafolio = engine.cargar_portafolio()
        for p in portafolio.propuestas:
            if not p.contexto_id:
                print(f"{p.id_propuesta}: sin contexto (versión anterior al verificador), se omite")
                continue
            antes = len(p.verificacion_cifras.sin_respaldo) if p.verificacion_cifras else None
            p.verificacion_cifras = verificar_propuesta(p, contexto_para_verificar(cargar_contexto(p.contexto_id)))
            print(f"{p.id_propuesta} v{p.version}: marcas {antes} → {len(p.verificacion_cifras.sin_respaldo)}")
        engine.guardar_portafolio(portafolio)


def main():
    if "--reverificar" in sys.argv:
        reverificar(CurriculumIntelligenceEngine())
        return
    ejecutar = "--ejecutar" in sys.argv
    pedidas = [a for a in sys.argv[1:] if not a.startswith("--")]
    engine = CurriculumIntelligenceEngine()
    propuestas = [p for p in engine.cargar_portafolio().propuestas if not pedidas or p.id_propuesta in pedidas]
    for p in propuestas:
        pasos = (["reabrir"] if p.estado in ESTADOS_REABRIBLES else []) + [f"refinar v{p.version} → v{p.version + 1}"]
        if p.estado == EstadoPropuesta.EN_AJUSTE:
            print(f"{p.id_propuesta}: OMITIDA, ya está en ajuste con IA")
            continue
        print(f"{p.id_propuesta} [{p.estado.value}] {p.nombre_programa}: {' + '.join(pasos)}")
        if not ejecutar:
            continue
        if p.estado in ESTADOS_REABRIBLES:
            engine.reabrir_propuesta(p.id_propuesta, USUARIO, ROL)
        engine.marcar_en_ajuste(p.id_propuesta)
        try:
            nueva, _ = engine.refinar_propuesta_con_feedback(p.id_propuesta, FEEDBACK, USUARIO, ROL)
        except Exception as e:
            engine.revertir_ajuste_fallido(p.id_propuesta, str(e), USUARIO, ROL)
            print(f"   [ERROR] {e}: la propuesta conserva su versión anterior")
            continue
        v = nueva.verificacion_cifras
        print(f"   → v{nueva.version} pendiente de aprobación · {v.cifras_revisadas} cifras revisadas, "
              f"{len(v.sin_respaldo)} sin respaldo (contexto {v.contexto_id})")
    if not ejecutar:
        print("\nSimulación: no se cambió nada. Agregue --ejecutar para regenerar.")


if __name__ == "__main__":
    main()
