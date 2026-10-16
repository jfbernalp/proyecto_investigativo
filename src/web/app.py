"""
Servidor Web FastAPI - Observatorio de Inteligencia Laboral y Diseño Curricular UniCafam.
Provee la Landing Page de 3 páginas, el Portal Directivo del Usuario Aprobador (HITL),
el ciclo de refinamiento asistido por IA y los endpoints de descarga de la Matriz MIG.
"""

import os
import re
import hmac
import hashlib
import base64
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Asegurar importación de módulos del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ai_curriculum.mig_excel_exporter import normalizar_propuesta_a_mig
from src.ai_curriculum.curriculum_schemas import (
    EstadoPropuesta,
    DecisionAprobador,
    SolicitudAjusteFeedback,
    SolicitudDecisionAprobador
)
from src.database.db_manager import DatabaseManager

app = FastAPI(
    title="Observatorio de Inteligencia Laboral & Gobernanza Curricular | UniCafam",
    description="Portal institucional de vigilancia de mercado, pertinencia curricular y aprobación directiva HITL",
    version="2.5.0"
)

TEMPLATES_DIR = ROOT_DIR / "src" / "web" / "templates"
STATIC_DIR = ROOT_DIR / "src" / "web" / "static"
MIG_DIR = ROOT_DIR / "data" / "curriculo_unicafam" / "mig_propuestas"
JSON_RECOMMENDATIONS_PATH = ROOT_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ==============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN DEL USUARIO APROBADOR (RBAC LIGERO)
# ==============================================================================
SECRET_KEY = os.getenv("APPROVER_SECRET_KEY", "unicafam-observatorio-hitl-secret-2026")
COOKIE_NAME = "unicafam_approver_session"

USUARIOS_APROBADORES = {
    "decanatura@unicafam.edu.co": {
        "password": os.getenv("APROBADOR_PASSWORD", "Unicafam2026*"),
        "nombre": "Ing. Decano de Escuela",
        "rol": "Decanatura de Ingeniería y Ciencias Empresariales"
    },
    "direccion@unicafam.edu.co": {
        "password": os.getenv("APROBADOR_PASSWORD", "Unicafam2026*"),
        "nombre": "Director de Programa Ciencia y Análisis de Datos",
        "rol": "Dirección de Programa"
    },
    "comite@unicafam.edu.co": {
        "password": os.getenv("APROBADOR_PASSWORD", "Unicafam2026*"),
        "nombre": "Comité Curricular Institucional",
        "rol": "Comité Curricular MEN"
    },
    "aprobador": {
        "password": os.getenv("APROBADOR_PASSWORD", "Unicafam2026*"),
        "nombre": "Decanatura / Comité Curricular UniCafam",
        "rol": "Aprobador Principal"
    }
}

class LoginPayload(BaseModel):
    username: str
    password: str
    nombre_personalizado: Optional[str] = None
    rol_personalizado: Optional[str] = None

def crear_token_sesion(usuario: str, rol: str, email: str) -> str:
    payload = json.dumps({"usuario": usuario, "rol": rol, "email": email}, ensure_ascii=False)
    b64_payload = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
    firma = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{firma}"

def verificar_token_sesion(token: Optional[str]) -> Optional[Dict[str, str]]:
    if not token or "." not in token:
        return None
    try:
        b64_payload, firma = token.rsplit(".", 1)
        firma_esperada = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, firma_esperada):
            return None
        datos = json.loads(base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8"))
        return datos
    except Exception:
        return None

def obtener_aprobador_actual(request: Request) -> Optional[Dict[str, str]]:
    token = request.cookies.get(COOKIE_NAME)
    return verificar_token_sesion(token)

# ==============================================================================
# FUNCIONES DE ACCESO A DATOS Y SINCRONIZACIÓN
# ==============================================================================
def resolver_nombre_archivo_mig(id_propuesta: str, nombre_programa: str) -> str:
    """Localiza el archivo Excel MIG real en el directorio para evitar enlaces rotos."""
    if MIG_DIR.exists():
        matches = list(MIG_DIR.glob(f"{id_propuesta}_*_MIG.xlsx"))
        if matches:
            return matches[0].name
    clean_name = re.sub(r"[^A-Za-z0-9_]", "_", nombre_programa)[:25]
    return f"{id_propuesta}_{clean_name}_MIG.xlsx"

def obtener_datos_curriculares() -> Dict[str, Any]:
    """Lee y normaliza el diagnóstico y todas las propuestas junto con sus estados de aprobación."""
    if not JSON_RECOMMENDATIONS_PATH.exists():
        return {
            "diagnostico": {},
            "propuestas": [],
            "propuestas_aprobadas": [],
            "propuestas_pendientes": [],
            "propuestas_rechazadas": [],
            "resumen_estados": {"total": 0, "aprobadas": 0, "pendientes": 0, "rechazadas": 0}
        }
    
    with open(JSON_RECOMMENDATIONS_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    propuestas_norm = []
    aprobadas = []
    pendientes = []
    rechazadas = []

    for p in raw_data.get("propuestas", []):
        p_obj = normalizar_propuesta_a_mig(p)
        p_dict = p_obj.model_dump()
        p_dict["archivo_mig_nombre"] = resolver_nombre_archivo_mig(p_obj.id_propuesta, p_obj.nombre_programa)
        propuestas_norm.append(p_dict)

        est = p_dict.get("estado", "PENDIENTE_REVISION")
        if est == "APROBADO":
            aprobadas.append(p_dict)
        elif est == "RECHAZADO":
            rechazadas.append(p_dict)
        else:
            pendientes.append(p_dict)
        
    return {
        "diagnostico": raw_data.get("diagnostico", {}),
        "propuestas": propuestas_norm,
        "propuestas_aprobadas": aprobadas,
        "propuestas_pendientes": pendientes,
        "propuestas_rechazadas": rechazadas,
        "resumen_estados": {
            "total": len(propuestas_norm),
            "aprobadas": len(aprobadas),
            "pendientes": len(pendientes),
            "rechazadas": len(rechazadas)
        }
    }

def sincronizar_db_background():
    """Tarea en segundo plano para sincronizar cambios de estado/versiones en PostgreSQL/SQLite."""
    try:
        from src.ai_curriculum.report_generator import CurriculumReportGenerator
        gen = CurriculumReportGenerator()
        gen.generar_informe_markdown()
        gen.generar_script_sql()
        gen.sincronizar_propuestas_a_base_de_datos()
    except Exception as e:
        print(f"[BACKGROUND SYNC AVISO] No se pudo sincronizar la BD remota: {e}")

def obtener_kpis_mercado():
    """Obtiene métricas agregadas del mercado laboral desde PostgreSQL o SQLite."""
    kpis = {
        "total_vacantes": 317,
        "mediana_local_cop": "$4.250.000 COP",
        "mediana_remoto_usd": "$25.600.000 COP (~$6.400 USD)",
        "tasa_transparencia": "29.1%",
        "total_habilidades_series": 4236,
        "fuentes_activas": 6,
        "competitividad_programa": 72.5
    }
    try:
        db = DatabaseManager()
        from sqlalchemy import text
        with db.engine.connect() as conn:
            res_v = conn.execute(text("SELECT COUNT(*) FROM dim_ofertas")).scalar()
            if res_v and res_v > 0:
                kpis["total_vacantes"] = res_v
            res_h = conn.execute(text("SELECT COUNT(*) FROM fact_habilidades_historico")).scalar()
            if res_h and res_h > 0:
                kpis["total_habilidades_series"] = res_h
            res_c = conn.execute(text("SELECT puntuacion_competitividad FROM fact_diagnostico_ia ORDER BY id DESC LIMIT 1")).scalar()
            if res_c:
                kpis["competitividad_programa"] = float(res_c)
    except Exception as e:
        print(f"[API AVISO] Usando métricas cacheadas de respaldo: {e}")
    return kpis

# ==============================================================================
# RUTAS DE VISTAS HTML (PORTAL PÚBLICO Y PANEL DEL APROBADOR)
# ==============================================================================
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index(request: Request):
    """Página principal de 3 pestañas con línea gráfica UniCafam y Gatekeeper de aprobación."""
    curriculo_data = obtener_datos_curriculares()
    kpis_data = obtener_kpis_mercado()
    aprobador_actual = obtener_aprobador_actual(request)
    
    # Listar archivos Excel MIG disponibles (filtrando solo los de propuestas aprobadas o master)
    ids_aprobados = {p["id_propuesta"] for p in curriculo_data["propuestas_aprobadas"]}
    archivos_mig = []
    if MIG_DIR.exists():
        for f in sorted(MIG_DIR.glob("*.xlsx")):
            if not f.name.startswith("~$"):
                es_master = "consolidado" in f.name.lower()
                pertenece_aprobada = any(f.name.startswith(pid) for pid in ids_aprobados)
                if es_master or pertenece_aprobada:
                    archivos_mig.append({
                        "nombre": f.name,
                        "tamano_kb": round(f.stat().st_size / 1024, 1),
                        "es_master": es_master
                    })

    context = {
        "request": request,
        "kpis": kpis_data,
        "diagnostico": curriculo_data["diagnostico"],
        "propuestas": curriculo_data["propuestas_aprobadas"],
        "propuestas_pendientes": curriculo_data["propuestas_pendientes"],
        "propuestas_rechazadas": curriculo_data["propuestas_rechazadas"],
        "resumen_estados": curriculo_data["resumen_estados"],
        "archivos_mig": archivos_mig,
        "aprobador": aprobador_actual,
        "superset_embed_url": "https://superset.jfbernalp.dev/superset/dashboard/1/?standalone=true"
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.api_route("/aprobador", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/admin/curriculo", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def panel_aprobador(request: Request):
    """Panel Directivo del Usuario Aprobador para revisar, retroalimentar con IA, aprobar o rechazar currículos."""
    curriculo_data = obtener_datos_curriculares()
    kpis_data = obtener_kpis_mercado()
    aprobador_actual = obtener_aprobador_actual(request)

    context = {
        "request": request,
        "kpis": kpis_data,
        "diagnostico": curriculo_data["diagnostico"],
        "propuestas": curriculo_data["propuestas"],
        "resumen_estados": curriculo_data["resumen_estados"],
        "aprobador": aprobador_actual
    }

    return templates.TemplateResponse(
        request=request,
        name="aprobador.html",
        context=context
    )

# ==============================================================================
# ENDPOINTS DE AUTENTICACIÓN DEL APROBADOR
# ==============================================================================
@app.post("/api/auth/login")
async def login_aprobador(payload: LoginPayload, response: Response):
    """Autentica al directivo aprobador y establece cookie firmada."""
    user_key = payload.username.strip().lower()
    user_info = USUARIOS_APROBADORES.get(user_key)

    if not user_info or payload.password != user_info["password"]:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas. Verifique su usuario institucional o contraseña."
        )

    nombre_final = (payload.nombre_personalizado or "").strip() or user_info["nombre"]
    rol_final = (payload.rol_personalizado or "").strip() or user_info["rol"]

    token = crear_token_sesion(nombre_final, rol_final, user_key)
    resp = JSONResponse({
        "status": "ok",
        "autenticado": True,
        "usuario": nombre_final,
        "rol": rol_final,
        "email": user_key
    })
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax"
    )
    return resp

@app.post("/api/auth/logout")
async def logout_aprobador():
    """Cierra la sesión del usuario aprobador."""
    resp = JSONResponse({"status": "ok", "autenticado": False})
    resp.delete_cookie(COOKIE_NAME)
    return resp

@app.get("/api/auth/me")
async def estado_sesion_aprobador(request: Request):
    """Devuelve la sesión activa del aprobador."""
    aprobador = obtener_aprobador_actual(request)
    if not aprobador:
        return JSONResponse({"autenticado": False})
    return JSONResponse({"autenticado": True, **aprobador})

# ==============================================================================
# ENDPOINTS DE GOBERNANZA CURRICULAR Y REFINAMIENTO CON IA (HITL)
# ==============================================================================
@app.api_route("/api/kpis", methods=["GET", "HEAD"])
async def api_kpis():
    """Endpoint JSON con los KPIs del Observatorio."""
    return JSONResponse(obtener_kpis_mercado())

@app.api_route("/api/propuestas", methods=["GET", "HEAD"])
async def api_propuestas(solo_aprobadas: bool = False):
    """Endpoint JSON con las propuestas curriculares estructuradas."""
    datos = obtener_datos_curriculares()
    if solo_aprobadas:
        return JSONResponse({
            "diagnostico": datos["diagnostico"],
            "propuestas": datos["propuestas_aprobadas"],
            "resumen_estados": datos["resumen_estados"]
        })
    return JSONResponse(datos)

@app.post("/api/propuestas/{id_propuesta}/aprobar")
async def aprobar_propuesta(
    id_propuesta: str,
    request: Request,
    background_tasks: BackgroundTasks,
    payload: Optional[Dict[str, Any]] = None
):
    """Aprueba formalmente una propuesta curricular para su despliegue público y exportación MIG."""
    aprobador = obtener_aprobador_actual(request)
    body = payload or {}
    usuario = body.get("usuario_aprobador") or (aprobador["usuario"] if aprobador else "Decanatura de Escuela")
    rol = body.get("rol_usuario") or (aprobador["rol"] if aprobador else "Comité Curricular UniCafam")

    try:
        from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
        engine = CurriculumIntelligenceEngine()
        prop_actualizada = engine.registrar_decision_formal(
            id_propuesta=id_propuesta,
            decision=DecisionAprobador.APROBAR,
            usuario_aprobador=usuario,
            rol_usuario=rol
        )
        background_tasks.add_task(sincronizar_db_background)
        return JSONResponse({
            "status": "ok",
            "mensaje": f"Propuesta {id_propuesta} aprobada y publicada exitosamente en el portal institucional.",
            "propuesta": prop_actualizada.model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/propuestas/{id_propuesta}/rechazar")
async def rechazar_propuesta(
    id_propuesta: str,
    request: Request,
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any]
):
    """Rechaza formalmente una propuesta curricular registrando el motivo en la bitácora de auditoría."""
    aprobador = obtener_aprobador_actual(request)
    motivo = (payload.get("motivo_rechazo") or "").strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=400, detail="Debe especificar un motivo académico válido para el rechazo.")

    usuario = payload.get("usuario_aprobador") or (aprobador["usuario"] if aprobador else "Decanatura de Escuela")
    rol = payload.get("rol_usuario") or (aprobador["rol"] if aprobador else "Comité Curricular UniCafam")

    try:
        from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
        engine = CurriculumIntelligenceEngine()
        prop_actualizada = engine.registrar_decision_formal(
            id_propuesta=id_propuesta,
            decision=DecisionAprobador.RECHAZAR,
            usuario_aprobador=usuario,
            rol_usuario=rol,
            motivo_rechazo=motivo
        )
        background_tasks.add_task(sincronizar_db_background)
        return JSONResponse({
            "status": "ok",
            "mensaje": f"Propuesta {id_propuesta} marcada como RECHAZADA y archivada en bitácora.",
            "propuesta": prop_actualizada.model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/propuestas/{id_propuesta}/ajustar")
async def ajustar_propuesta_ia(
    id_propuesta: str,
    solicitud: SolicitudAjusteFeedback,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Envía retroalimentación del aprobador a Gemini 3.5 Flash para reajustar la propuesta curricular,
    generando una nueva versión (v+1) y actualizando su Matriz MIG.
    """
    aprobador = obtener_aprobador_actual(request)
    usuario = solicitud.usuario_aprobador or (aprobador["usuario"] if aprobador else "Comité Curricular")
    rol = solicitud.rol_usuario or (aprobador["rol"] if aprobador else "Director de Programa")

    try:
        from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
        engine = CurriculumIntelligenceEngine()
        prop_refinada, resumen_cambios = engine.refinar_propuesta_con_feedback(
            id_propuesta=id_propuesta,
            feedback_humano=solicitud.feedback_usuario,
            usuario_aprobador=usuario,
            rol_usuario=rol
        )
        background_tasks.add_task(sincronizar_db_background)
        p_dict = prop_refinada.model_dump()
        p_dict["archivo_mig_nombre"] = resolver_nombre_archivo_mig(prop_refinada.id_propuesta, prop_refinada.nombre_programa)
        return JSONResponse({
            "status": "ok",
            "mensaje": f"La IA ha ajustado la propuesta {id_propuesta} a la versión v{prop_refinada.version}.",
            "resumen_cambios": resumen_cambios,
            "propuesta": p_dict
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el refinamiento con IA: {e}")

@app.post("/api/propuestas/{id_propuesta}/restaurar")
async def restaurar_a_pendiente(
    id_propuesta: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Reabre una propuesta aprobada o rechazada pasándola nuevamente a estado PENDIENTE_REVISION."""
    aprobador = obtener_aprobador_actual(request)
    usuario = aprobador["usuario"] if aprobador else "Comité Curricular"
    rol = aprobador["rol"] if aprobador else "Aprobador"

    try:
        from datetime import datetime
        import time
        from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
        from src.ai_curriculum.curriculum_schemas import RegistroAuditoriaFeedback
        engine = CurriculumIntelligenceEngine()
        portafolio = engine.cargar_portafolio()
        target = None
        for p in portafolio.propuestas:
            if p.id_propuesta == id_propuesta:
                target = p
                break
        if not target:
            raise ValueError(f"Propuesta {id_propuesta} no encontrada.")

        target.estado = EstadoPropuesta.PENDIENTE_REVISION
        target.aprobado_por = None
        target.motivo_rechazo = None
        target.fecha_decision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target.historial_revisiones.append(
            RegistroAuditoriaFeedback(
                id_registro=f"REOPEN_{id_propuesta}_V{target.version}_{int(time.time())}",
                version_resultante=target.version,
                usuario_aprobador=usuario,
                rol_usuario=rol,
                decision="REAPERTURA_REVISION",
                comentarios_feedback="Propuesta reabierta para nueva deliberación o ajustes curriculares.",
                cambios_aplicados_resumen="Estado retornado a PENDIENTE_REVISION.",
                fecha_registro=target.fecha_decision
            )
        )
        engine.guardar_portafolio(portafolio)
        background_tasks.add_task(sincronizar_db_background)
        return JSONResponse({
            "status": "ok",
            "mensaje": f"Propuesta {id_propuesta} retornada a estado PENDIENTE_REVISION.",
            "propuesta": target.model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auditoria/men")
async def obtener_bitacora_auditoria_men():
    """Devuelve el consolidado de trazabilidad de todas las propuestas para el Decreto 1330 del MEN."""
    datos = obtener_datos_curriculares()
    bitacora = []
    for p in datos["propuestas"]:
        for rev in p.get("historial_revisiones", []):
            bitacora.append({
                "id_propuesta": p["id_propuesta"],
                "nombre_programa": p["nombre_programa"],
                "tipo_propuesta": p["tipo_propuesta"],
                "estado_actual": p["estado"],
                **rev
            })
    return JSONResponse({
        "institucion": "Fundación Universitaria Cafam (UniCafam)",
        "normativa": "Decreto 1330 de 2019 - Ministerio de Educación Nacional (MEN)",
        "resumen_estados": datos["resumen_estados"],
        "total_eventos_auditoria": len(bitacora),
        "eventos": bitacora
    })

# ==============================================================================
# ENDPOINTS DE DESCARGA DE ARCHIVOS EXCEL FORMATO MIG
# ==============================================================================
@app.api_route("/descargas/{filename}", methods=["GET", "HEAD"])
async def descargar_archivo_mig(filename: str):
    """Descarga segura de un archivo Excel de la Matriz MIG."""
    safe_name = os.path.basename(filename)
    file_path = MIG_DIR / safe_name
    
    if not file_path.exists():
        # Intentar buscar por prefijo de ID de propuesta (ej. PROP_01)
        m = re.match(r"^(PROP_\d+)", safe_name)
        if m and MIG_DIR.exists():
            candidatos = list(MIG_DIR.glob(f"{m.group(1)}_*_MIG.xlsx"))
            if candidatos:
                file_path = candidatos[0]
                safe_name = file_path.name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe.")
        
    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.api_route("/descargas/consolidado/master", methods=["GET", "HEAD"])
async def descargar_consolidado():
    """Descarga directa del libro maestro consolidado de propuestas."""
    consolidado_path = MIG_DIR / "ofertas_academicas_mig_consolidado.xlsx"
    if not consolidado_path.exists():
        raise HTTPException(status_code=404, detail="El libro consolidado no se encuentra disponible.")
        
    return FileResponse(
        path=str(consolidado_path),
        filename="MATRIZ_MIG_MASTER_PROPUESTAS_UNICAFAM.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
