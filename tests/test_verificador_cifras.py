"""El verificador marca las cifras que no están en el contexto y deja pasar las que sí (solo marca)."""
from src.ai_curriculum.curriculum_schemas import PropuestaPrograma
from src.ai_curriculum.verificador_cifras import verificar_propuesta

CONTEXTO = {
    "id": "ctx123", "ultimo_corte": "2026-10-28", "n_ofertas_mes": 570,
    "demanda_habilidades": [{"habilidad": "SQL", "n_ofertas": 355, "pct_ofertas": 62.3}],
    "primas_por_rol": [{"rol": "Analista de Datos", "prima_pct": -32.7, "ic95_inferior_pct": -42.0}],
    "salarios_por_mercado": [{"mercado": "Local", "n_con_salario": 133, "mediana_salarial_cop_mes": 4478000}],
}


def _propuesta(**cambios):
    base = dict(id_propuesta="PROP_X", tipo_propuesta="Electiva", nombre_programa="P", titulo_otorgado="T",
                nivel_academico="Pregrado", duracion_estimada="1 semestre", creditos_totales=6, horas_totales=288,
                modalidad_sugerida="100% virtual", perfil_ingreso="-", perfil_egreso="-",
                roles_ocupacionales_objetivo=["Data Engineer"], impacto_salarial_proyectado="Dato no disponible",
                plan_estudios=[{"nombre_modulo": "M1", "creditos": 3, "horas_tfd": 48, "horas_tti": 96,
                                "justificacion_demanda_laboral": "SQL aparece en el 62,3 % de las 570 ofertas."}])
    base.update(cambios)
    return PropuestaPrograma.model_validate(base)


def test_cifras_del_contexto_no_se_marcan():
    v = verificar_propuesta(_propuesta(justificacion_detallada=(
        "Mediana local de $4.478.000 COP (n=133); el Analista de Datos gana 32,7 % menos, "
        "unos 4,5 millones de pesos.")), CONTEXTO)
    assert v.sin_respaldo == [] and v.cifras_revisadas >= 5 and v.contexto_id == "ctx123"


def test_cifras_inventadas_se_marcan():
    v = verificar_propuesta(_propuesta(
        justificacion_detallada="Salario mediano de $65.833.333 COP y el 78.1% de la demanda.",
        impacto_salarial_proyectado="+45% sobre la media, hasta $15M COP"), CONTEXTO)
    marcadas = {c.cifra for c in v.sin_respaldo}
    assert {"$65.833.333", "78.1%", "45%", "$15M"} <= marcadas
    assert all("ctx123" in c.motivo for c in v.sin_respaldo)


def test_tarifas_siempre_se_marcan_y_creditos_no():
    v = verificar_propuesta(_propuesta(inversion={"publico_externo": "$4.478.000 COP (25% dcto)"},
                                       justificacion_detallada="6 créditos, 288 horas, Decreto 1330 de 2019."), CONTEXTO)
    assert [c.campo for c in v.sin_respaldo] == ["inversion.publico_externo", "inversion.publico_externo"]
    assert all("tarifa" in c.motivo.lower() for c in v.sin_respaldo)


def test_conteo_de_ofertas_inventado():
    v = verificar_propuesta(_propuesta(justificacion_detallada="Se analizaron 1200 vacantes."), CONTEXTO)
    assert [c.tipo for c in v.sin_respaldo] == ["conteo de ofertas"]
