"""
Servidor Web FastAPI - Observatorio del mercado laboral en datos y portal curricular con IA.
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
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Asegurar importación de módulos del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ai_curriculum.mig_excel_exporter import normalizar_propuesta_a_mig
from src.ai_curriculum.curriculum_schemas import DecisionAprobador
from src.ai_curriculum.curriculum_engine import (
    NIVELES_ACADEMICOS, TIPOS_PROPUESTA, TransicionInvalidaError, ruta_excel_aprobado,
)
from src.database.db_manager import DatabaseManager

@asynccontextmanager
async def ciclo_de_vida(_app):
    recuperar_ajustes_al_arrancar()
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Observatorio del mercado laboral en datos · Portal curricular",
    description="Observatorio de Inteligencia Laboral con Superset embebido y Portal de Generación y Validación Curricular (RBAC 3 Roles)",
    version="3.0.0"
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
# CONFIGURACIÓN DE AUTENTICACIÓN MULTI-ROL (VISUALIZADOR, APROBADOR, ADMINISTRADOR)
# ==============================================================================
# La clave que firma las sesiones es obligatoria: sin ella la app no arranca (antes había un valor
# por defecto público con el que se podía fabricar una cookie de administrador).
SECRET_KEY = os.getenv("APPROVER_SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("APPROVER_SECRET_KEY debe estar definida en el entorno (mínimo 32 caracteres).")
COOKIE_NAME = "observatorio_sesion"
DURACION_SESION_SEG = int(os.getenv("PORTAL_SESION_HORAS", "8")) * 3600
# Detrás de Traefik el sitio es HTTPS; solo para desarrollo local por HTTP se puede poner en 0.
COOKIE_SEGURA = os.getenv("PORTAL_COOKIE_SECURE", "1") != "0"

# Contraseña por rol, guardada SOLO como hash PBKDF2 en el entorno
# (formato pbkdf2_sha256$iteraciones$sal_b64$hash_b64; ver scripts/generar_credenciales_portal.py).
# Un rol sin hash configurado no puede iniciar sesión.
HASHES_POR_ROL = {
    "visualizador": os.getenv("PORTAL_HASH_VISUALIZADOR", ""),
    "aprobador": os.getenv("PORTAL_HASH_APROBADOR", ""),
    "administrador": os.getenv("PORTAL_HASH_ADMINISTRADOR", ""),
}

USUARIOS_APROBADORES = {
    "visualizador": {"nombre": "Consultor curricular", "rol": "Usuario Visualizador", "role_code": "visualizador"},
    "aprobador": {"nombre": "Comité curricular", "rol": "Usuario Aprobador", "role_code": "aprobador"},
    "administrador": {"nombre": "Administrador del observatorio", "rol": "Usuario Administrador", "role_code": "administrador"},
    "admin": {"nombre": "Administrador del observatorio", "rol": "Usuario Administrador", "role_code": "administrador"},
}


# Límite de intentos fallidos de login, por IP y por usuario (en memoria: el portal corre con 1 worker).
# Un hash con otra forma no valida ninguna contraseña: avisarlo al arrancar en lugar de fallar en silencio
# (pasó el 28-oct-2026: docker compose borraba partes de los hashes al leer el .env sin comillas)
for _rol, _hash in HASHES_POR_ROL.items():
    if _hash and (_hash.count("$") != 3 or not _hash.startswith("pbkdf2_sha256$")):
        print(f"[AUTH AVISO] El hash de '{_rol}' está mal formado: ningún inicio de sesión de ese rol funcionará. "
              "Revise que PORTAL_HASH_* esté entre comillas simples en el .env.")

MAX_INTENTOS_LOGIN = 5
VENTANA_INTENTOS_SEG = 15 * 60
_intentos_fallidos: Dict[str, List[float]] = {}


def _ip_cliente(request: Request) -> str:
    # Detrás de Cloudflare, X-Real-Ip es la IP del nodo de Cloudflare (compartida por muchos visitantes);
    # la del visitante llega en CF-Connecting-IP. El puerto 8000 no está expuesto públicamente.
    return (request.headers.get("cf-connecting-ip") or request.headers.get("x-real-ip")
            or (request.client.host if request.client else "desconocida"))


def _bloqueado(claves: List[str]) -> int:
    """Segundos restantes de bloqueo (0 si no está bloqueado)."""
    ahora = time.time()
    restante = 0
    for clave in claves:
        recientes = [t for t in _intentos_fallidos.get(clave, []) if ahora - t < VENTANA_INTENTOS_SEG]
        _intentos_fallidos[clave] = recientes
        if len(recientes) >= MAX_INTENTOS_LOGIN:
            restante = max(restante, int(VENTANA_INTENTOS_SEG - (ahora - recientes[0])) + 1)
    return restante


def verificar_password(password: str, hash_guardado: str) -> bool:
    """Compara en tiempo constante contra un hash pbkdf2_sha256$iter$sal$hash."""
    try:
        algoritmo, iteraciones, sal_b64, hash_b64 = hash_guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculado = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.b64decode(sal_b64), int(iteraciones)
        )
        return hmac.compare_digest(calculado, base64.b64decode(hash_b64))
    except (ValueError, TypeError):
        return False


ROLES_DECISORES = ("aprobador", "administrador")
# Solo el administrador encarga propuestas nuevas a la IA (el aprobador decide sobre ellas)
ROLES_GENERADORES = ("administrador",)

class LoginPayload(BaseModel):
    username: str
    password: str

def crear_token_sesion(usuario: str, rol: str, email: str, role_code: str = "aprobador") -> str:
    payload = json.dumps({
        "usuario": usuario, "rol": rol, "email": email, "role_code": role_code,
        "exp": int(time.time()) + DURACION_SESION_SEG,
    }, ensure_ascii=False)
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
        # Sin expiración firmada (tokens anteriores) o vencido → sesión inválida
        if not isinstance(datos.get("exp"), int) or datos["exp"] < time.time():
            return None
        if datos.get("role_code") not in HASHES_POR_ROL:
            return None
        return datos
    except Exception:
        return None

def obtener_aprobador_actual(request: Request) -> Optional[Dict[str, str]]:
    token = request.cookies.get(COOKIE_NAME)
    return verificar_token_sesion(token)

def requerir_sesion(request: Request, roles: Optional[tuple] = None) -> Dict[str, str]:
    """Exige sesión válida (y opcionalmente uno de los roles indicados). La firma de auditoría sale de aquí."""
    sesion = obtener_aprobador_actual(request)
    if not sesion:
        raise HTTPException(status_code=401, detail="Sesión no iniciada o expirada. Ingrese nuevamente.")
    if roles and sesion.get("role_code") not in roles:
        raise HTTPException(status_code=403, detail="Su rol no tiene permisos para realizar esta acción.")
    return sesion

def puede_decidir(sesion: Optional[Dict[str, str]]) -> bool:
    return bool(sesion) and sesion.get("role_code") in ROLES_DECISORES

def puede_generar(sesion: Optional[Dict[str, str]]) -> bool:
    return bool(sesion) and sesion.get("role_code") in ROLES_GENERADORES

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
        # mode="json": los estados son texto plano; con el Enum, Jinja escribía "EstadoPropuesta.PENDIENTE_REVISION"
        # en data-estado y los filtros del portal no encontraban nada
        p_dict = p_obj.model_dump(mode="json")
        p_dict["archivo_mig_nombre"] = resolver_nombre_archivo_mig(p_obj.id_propuesta, p_obj.nombre_programa)
        p_dict["tiene_excel_aprobado"] = ruta_excel_aprobado(p_obj.id_propuesta, p_obj.version).exists()
        propuestas_norm.append(p_dict)

        est = p_dict.get("estado", "PENDIENTE_REVISION")
        if est == "APROBADO":
            aprobadas.append(p_dict)
        elif est == "RECHAZADO":
            rechazadas.append(p_dict)
        else:
            pendientes.append(p_dict)

    en_ajuste = sum(1 for p in propuestas_norm if p.get("estado") == "EN_AJUSTE")
    return {
        "diagnostico": raw_data.get("diagnostico", {}),
        "propuestas": propuestas_norm,
        "propuestas_aprobadas": aprobadas,
        "propuestas_pendientes": pendientes,
        "propuestas_rechazadas": rechazadas,
        "resumen_estados": {
            "total": len(propuestas_norm),
            "aprobadas": len(aprobadas),
            "pendientes": len(pendientes) - en_ajuste,
            "en_ajuste": en_ajuste,
            "rechazadas": len(rechazadas)
        }
    }

def buscar_propuesta_dict(datos: Dict[str, Any], id_propuesta: str) -> Optional[Dict[str, Any]]:
    return next((p for p in datos["propuestas"] if p["id_propuesta"] == id_propuesta), None)

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

MESES_ES = ("ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic.")


def _formatear_periodo(mes_periodo: int) -> str:
    return f"{MESES_ES[mes_periodo % 100 - 1]} {mes_periodo // 100}"


def obtener_kpis_mercado() -> Dict[str, Any]:
    """
    Cifras del observatorio calculadas en la base de datos.
    REGLA DE ORO: no hay valores de respaldo. Si una cifra no se puede calcular queda en None
    y la interfaz muestra "Dato no disponible" (antes se mostraban cifras fijas como si fueran reales).
    """
    kpis: Dict[str, Any] = {
        "disponible": False,
        "motivo": None,
        "total_vacantes": None,
        "periodo_inicial": None,
        "periodo_final": None,
        "ultimo_corte": None,
        "ofertas_ultimo_mes": None,
        "fuentes_ultimo_mes": None,
        "mediana_local_cop": None,
        "n_salarios_local": None,
        "mediana_internacional_cop": None,
        "n_salarios_internacional": None,
        "tasa_transparencia_pct": None,
        "competitividad_programa": None,
        "competitividad_origen": "Puntaje asignado por el modelo de IA en el diagnóstico curricular; no es una medición.",
    }
    try:
        from sqlalchemy import text
        db = DatabaseManager()
        with db.engine.connect() as conn:
            q = lambda sql: conn.execute(text(sql)).fetchone()
            kpis["total_vacantes"] = q("SELECT COUNT(*) FROM dim_ofertas")[0]
            ini, fin, corte = q("SELECT MIN(mes_periodo), MAX(mes_periodo), MAX(fecha_extraccion) FROM fact_extracciones_historico")
            if fin is None:
                kpis["motivo"] = "Aún no hay cortes registrados."
                return kpis
            kpis["periodo_inicial"], kpis["periodo_final"] = _formatear_periodo(ini), _formatear_periodo(fin)
            kpis["ultimo_corte"] = corte.isoformat() if hasattr(corte, "isoformat") else str(corte)
            ofertas, fuentes, con_salario = q(f"""
                SELECT COUNT(DISTINCT e.id_vacante_hash), COUNT(DISTINCT d.portal),
                       COUNT(DISTINCT e.id_vacante_hash) FILTER (WHERE e.salario_cop_mensual > 0)
                FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
                WHERE e.mes_periodo = {int(fin)}""")
            kpis["ofertas_ultimo_mes"], kpis["fuentes_ultimo_mes"] = ofertas, fuentes
            kpis["tasa_transparencia_pct"] = round(100.0 * con_salario / ofertas, 1) if ofertas else None
            for mercado, clave in (("Mercado Local (Colombia - COP)", "local"), ("Mercado Internacional (Remoto - USD)", "internacional")):
                mediana, n = conn.execute(text(f"""
                    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salario_cop_mensual), COUNT(*)
                    FROM fact_extracciones_historico e JOIN dim_ofertas d USING (id_vacante_hash)
                    WHERE e.mes_periodo = {int(fin)} AND e.salario_cop_mensual > 0 AND d.tipo_mercado = :m"""),
                    {"m": mercado}).fetchone()
                kpis[f"n_salarios_{clave}"] = n
                kpis[f"mediana_{clave}_cop"] = round(float(mediana)) if mediana is not None else None
            fila = q("SELECT puntuacion_competitividad FROM fact_diagnostico_ia ORDER BY id DESC LIMIT 1")
            kpis["competitividad_programa"] = float(fila[0]) if fila and fila[0] is not None else None
            kpis["disponible"] = True
    except Exception as e:
        print(f"[API AVISO] No fue posible calcular los indicadores: {e}")
        kpis["motivo"] = "La base de datos del observatorio no respondió."
    return kpis

# ==============================================================================
# RUTAS DE VISTAS HTML (PORTAL PÚBLICO Y PANEL DEL APROBADOR)
# ==============================================================================
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index(request: Request):
    """Landing pública del observatorio (narrativa por escenas y tablero embebido)."""
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
        "superset_embed_url": "https://superset.jfbernalp.dev/superset/dashboard/1/?standalone=2",
        "superset_url_completa": "https://superset.jfbernalp.dev/superset/dashboard/1/?standalone=1"
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.api_route("/login", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def pagina_login(request: Request):
    """Página de autenticación para ingresar al Portal de Generación y Validación de Contenidos Programáticos."""
    aprobador_actual = obtener_aprobador_actual(request)
    if aprobador_actual:
        return RedirectResponse(url="/portal-programatico", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
    )

def recuperar_ajustes_al_arrancar():
    """Un ajuste con IA corre en segundo plano: si el contenedor se reinició a mitad, la propuesta
    quedaría para siempre en EN_AJUSTE. Se devuelve a PENDIENTE_REVISION dejando constancia."""
    try:
        from src.ai_curriculum.curriculum_engine import recuperar_ajustes_interrumpidos
        recuperadas = recuperar_ajustes_interrumpidos()
        if recuperadas:
            print(f"[ARRANQUE] Propuestas recuperadas de EN_AJUSTE: {recuperadas}")
    except Exception as e:
        print(f"[ARRANQUE AVISO] No se pudieron revisar ajustes interrumpidos: {e}")


@app.api_route("/portal-programatico", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def portal_programatico(request: Request):
    """Landing del Portal de Contenidos Programáticos: tarjetas de propuestas (común a los 3 roles)."""
    sesion = obtener_aprobador_actual(request)
    if not sesion:
        return RedirectResponse(url="/login", status_code=302)

    curriculo_data = obtener_datos_curriculares()
    return templates.TemplateResponse(
        request=request,
        name="portal.html",
        context={
            "request": request,
            "propuestas": curriculo_data["propuestas"],
            "resumen_estados": curriculo_data["resumen_estados"],
            "aprobador": sesion,
            "puede_decidir": puede_decidir(sesion),
            "puede_generar": puede_generar(sesion),
            "generacion_en_curso": generacion_en_curso(),
        }
    )

@app.api_route("/portal-programatico/propuestas/{id_propuesta}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def detalle_propuesta(request: Request, id_propuesta: str):
    """Vista completa de una propuesta con la barra de decisión del aprobador."""
    sesion = obtener_aprobador_actual(request)
    if not sesion:
        return RedirectResponse(url="/login", status_code=302)

    propuesta = buscar_propuesta_dict(obtener_datos_curriculares(), id_propuesta)
    if not propuesta:
        raise HTTPException(status_code=404, detail=f"No existe la propuesta {id_propuesta}.")

    return templates.TemplateResponse(
        request=request,
        name="propuesta_detalle.html",
        context={
            "request": request,
            "p": propuesta,
            "aprobador": sesion,
            "puede_decidir": puede_decidir(sesion)
        }
    )

@app.api_route("/portal-programatico/nueva", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def formulario_nueva_propuesta(request: Request):
    """Formulario para encargar a la IA una propuesta nueva (solo administrador)."""
    sesion = obtener_aprobador_actual(request)
    if not sesion:
        return RedirectResponse(url="/login", status_code=302)
    if not puede_generar(sesion):
        return RedirectResponse(url="/portal-programatico", status_code=302)
    return templates.TemplateResponse(request=request, name="nueva_propuesta.html", context={
        "request": request, "aprobador": sesion, "tipos": TIPOS_PROPUESTA, "niveles": NIVELES_ACADEMICOS,
        "en_curso": generacion_en_curso(),
    })

@app.api_route("/aprobador", methods=["GET", "HEAD"])
@app.api_route("/admin/curriculo", methods=["GET", "HEAD"])
async def redireccion_portal_legado():
    """Rutas del panel anterior: se conservan como alias del portal."""
    return RedirectResponse(url="/portal-programatico", status_code=301)

# ==============================================================================
# ENDPOINTS DE AUTENTICACIÓN MULTI-ROL (VISUALIZADOR, APROBADOR, ADMINISTRADOR)
# ==============================================================================
@app.post("/api/auth/login")
async def login_aprobador(payload: LoginPayload, request: Request):
    """Autentica al usuario (Visualizador, Aprobador o Administrador) y establece cookie firmada."""
    user_key = payload.username.strip().lower()
    user_info = USUARIOS_APROBADORES.get(user_key)
    claves_limite = [f"ip:{_ip_cliente(request)}", f"usuario:{user_key}"]
    espera = _bloqueado(claves_limite)
    if espera:
        print(f"[AUTH] Inicio de sesión bloqueado por intentos fallidos: {claves_limite}")
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos. Intente más tarde.",
                            headers={"Retry-After": str(espera)})

    hash_rol = HASHES_POR_ROL.get(user_info["role_code"], "") if user_info else ""
    if not user_info or not hash_rol or not verificar_password(payload.password, hash_rol):
        for clave in claves_limite:
            _intentos_fallidos.setdefault(clave, []).append(time.time())
        print(f"[AUTH] Intento de inicio de sesión fallido para '{user_key[:60]}' desde {_ip_cliente(request)}")
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    for clave in claves_limite:
        _intentos_fallidos.pop(clave, None)

    nombre_final = user_info["nombre"]
    rol_final = user_info["rol"]
    role_code = user_info.get("role_code", "aprobador")

    token = crear_token_sesion(nombre_final, rol_final, user_key, role_code=role_code)
    resp = JSONResponse({
        "status": "ok",
        "autenticado": True,
        "usuario": nombre_final,
        "rol": rol_final,
        "role_code": role_code,
        "email": user_key,
        "redirect_url": "/portal-programatico"
    })
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=DURACION_SESION_SEG,
        samesite="lax",
        secure=COOKIE_SEGURA
    )
    return resp

@app.post("/api/auth/logout")
async def logout_aprobador():
    """Cierra la sesión del usuario."""
    resp = JSONResponse({"status": "ok", "autenticado": False})
    resp.delete_cookie(COOKIE_NAME, httponly=True, samesite="lax", secure=COOKIE_SEGURA)
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
async def api_propuestas(request: Request, solo_aprobadas: bool = False):
    """Endpoint JSON con las propuestas curriculares. Sin sesión solo se exponen las aprobadas."""
    datos = obtener_datos_curriculares()
    if solo_aprobadas or not obtener_aprobador_actual(request):
        return JSONResponse({
            "diagnostico": datos["diagnostico"],
            "propuestas": datos["propuestas_aprobadas"],
            "resumen_estados": datos["resumen_estados"]
        })
    return JSONResponse(datos)

@app.get("/api/propuestas/{id_propuesta}/estado")
async def estado_propuesta(id_propuesta: str, request: Request):
    """Estado y versión actuales (la vista de detalle lo consulta mientras la IA ajusta)."""
    requerir_sesion(request)
    propuesta = buscar_propuesta_dict(obtener_datos_curriculares(), id_propuesta)
    if not propuesta:
        raise HTTPException(status_code=404, detail=f"No existe la propuesta {id_propuesta}.")
    ultimo = propuesta["historial_revisiones"][-1] if propuesta["historial_revisiones"] else None
    return JSONResponse({
        "id_propuesta": id_propuesta,
        "estado": propuesta["estado"],
        "version": propuesta["version"],
        "ultimo_evento": ultimo
    })

def _crear_engine():
    from src.ai_curriculum.curriculum_engine import CurriculumIntelligenceEngine
    return CurriculumIntelligenceEngine()

def _error_http(e: Exception) -> HTTPException:
    if isinstance(e, TransicionInvalidaError):
        return HTTPException(status_code=409, detail=str(e))
    if isinstance(e, ValueError):
        return HTTPException(status_code=404, detail=str(e))
    print(f"[ERROR] {type(e).__name__}: {e}")
    return HTTPException(status_code=500, detail="Error interno. Intente de nuevo o contacte al administrador.")

@app.post("/api/propuestas/{id_propuesta}/aprobar")
async def aprobar_propuesta(id_propuesta: str, request: Request, background_tasks: BackgroundTasks):
    """Aprueba la propuesta y congela su Excel MIG final. La firma se toma de la sesión."""
    sesion = requerir_sesion(request, ROLES_DECISORES)
    try:
        prop_actualizada = _crear_engine().registrar_decision_formal(
            id_propuesta=id_propuesta,
            decision=DecisionAprobador.APROBAR,
            usuario_aprobador=sesion["usuario"],
            rol_usuario=sesion["rol"]
        )
    except Exception as e:
        raise _error_http(e)
    background_tasks.add_task(sincronizar_db_background)
    return JSONResponse({
        "status": "ok",
        "mensaje": f"Propuesta {id_propuesta} aprobada. Se generó la Matriz MIG final de la versión v{prop_actualizada.version}.",
        "propuesta": prop_actualizada.model_dump()
    })

class SolicitudRechazo(BaseModel):
    motivo_rechazo: str

@app.post("/api/propuestas/{id_propuesta}/rechazar")
async def rechazar_propuesta(
    id_propuesta: str,
    solicitud: SolicitudRechazo,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Rechaza la propuesta registrando el motivo en la bitácora de auditoría."""
    sesion = requerir_sesion(request, ROLES_DECISORES)
    motivo = solicitud.motivo_rechazo.strip()
    if len(motivo) < 10:
        raise HTTPException(status_code=400, detail="Debe especificar un motivo académico válido (mínimo 10 caracteres).")
    try:
        prop_actualizada = _crear_engine().registrar_decision_formal(
            id_propuesta=id_propuesta,
            decision=DecisionAprobador.RECHAZAR,
            usuario_aprobador=sesion["usuario"],
            rol_usuario=sesion["rol"],
            motivo_rechazo=motivo
        )
    except Exception as e:
        raise _error_http(e)
    background_tasks.add_task(sincronizar_db_background)
    return JSONResponse({
        "status": "ok",
        "mensaje": f"Propuesta {id_propuesta} rechazada. El motivo quedó registrado en la bitácora.",
        "propuesta": prop_actualizada.model_dump()
    })

class SolicitudAjuste(BaseModel):
    feedback_usuario: str

def ejecutar_refinamiento_background(id_propuesta: str, feedback: str, usuario: str, rol: str):
    """Corre el refinamiento con Gemini fuera del ciclo de la petición HTTP."""
    engine = _crear_engine()
    try:
        engine.refinar_propuesta_con_feedback(
            id_propuesta=id_propuesta,
            feedback_humano=feedback,
            usuario_aprobador=usuario,
            rol_usuario=rol
        )
    except Exception as e:
        print(f"[HITL IA ERROR] {id_propuesta}: {e}")
        engine.revertir_ajuste_fallido(id_propuesta, str(e), usuario, rol)
    sincronizar_db_background()

@app.post("/api/propuestas/{id_propuesta}/ajustar", status_code=202)
async def ajustar_propuesta_ia(
    id_propuesta: str,
    solicitud: SolicitudAjuste,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Envía los comentarios del aprobador a Gemini para generar la versión v+1.
    Responde de inmediato (202) con la propuesta en EN_AJUSTE; el cliente consulta /estado.
    """
    sesion = requerir_sesion(request, ROLES_DECISORES)
    feedback = solicitud.feedback_usuario.strip()
    if len(feedback) < 10:
        raise HTTPException(status_code=400, detail="Describa los ajustes requeridos (mínimo 10 caracteres).")
    try:
        prop = _crear_engine().marcar_en_ajuste(id_propuesta)
    except Exception as e:
        raise _error_http(e)
    background_tasks.add_task(
        ejecutar_refinamiento_background, id_propuesta, feedback, sesion["usuario"], sesion["rol"]
    )
    return JSONResponse(status_code=202, content={
        "status": "en_ajuste",
        "mensaje": f"La IA está generando la versión v{prop.version + 1} de {id_propuesta}.",
        "version_actual": prop.version
    })

# Generaciones de propuestas nuevas en segundo plano (en memoria: si el contenedor se reinicia, la
# generación en curso se pierde y el portafolio queda como estaba)
_generaciones: Dict[str, Dict[str, Any]] = {}
_lock_generaciones = threading.Lock()

class SolicitudNuevaPropuesta(BaseModel):
    tipo_propuesta: str
    nivel_academico: str
    creditos: int
    enfoque: str = ""
    notas: str = ""

def generacion_en_curso() -> Optional[Dict[str, Any]]:
    return next((g for g in _generaciones.values() if g["estado"] == "en_curso"), None)

def ejecutar_generacion_background(id_trabajo: str, solicitud: Dict[str, Any], usuario: str, rol: str):
    """Genera la propuesta con Gemini fuera del ciclo de la petición HTTP."""
    trabajo = _generaciones[id_trabajo]
    try:
        nueva = _crear_engine().generar_propuesta_individual(solicitud, usuario, rol)
        trabajo.update(estado="lista", id_propuesta=nueva.id_propuesta)
        sincronizar_db_background()
    except Exception as e:
        print(f"[NUEVA PROPUESTA ERROR] {type(e).__name__}: {e}")
        trabajo.update(estado="error", error="La IA no pudo generar la propuesta. Intente de nuevo en unos minutos.")
    trabajo["fin"] = time.time()

@app.post("/api/propuestas/nueva", status_code=202)
async def nueva_propuesta_ia(solicitud: SolicitudNuevaPropuesta, request: Request, background_tasks: BackgroundTasks):
    """
    Encarga a la IA UNA propuesta con el tipo, créditos y enfoque indicados. Responde de inmediato (202)
    con el id del trabajo; el cliente consulta /api/generaciones/{id}. Una generación a la vez.
    """
    sesion = requerir_sesion(request, ROLES_GENERADORES)
    if solicitud.tipo_propuesta not in TIPOS_PROPUESTA or solicitud.nivel_academico not in NIVELES_ACADEMICOS:
        raise HTTPException(status_code=400, detail="Tipo de programa o nivel académico no válido.")
    if not 1 <= solicitud.creditos <= 60:
        raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 60.")
    if len(solicitud.enfoque) > 300 or len(solicitud.notas) > 1500:
        raise HTTPException(status_code=400, detail="El enfoque admite 300 caracteres y las indicaciones 1.500.")
    with _lock_generaciones:
        if generacion_en_curso():
            raise HTTPException(status_code=409, detail="Ya hay una propuesta generándose. Espere a que termine.")
        id_trabajo = uuid.uuid4().hex[:12]
        _generaciones[id_trabajo] = {"id_trabajo": id_trabajo, "estado": "en_curso", "inicio": time.time(),
                                     "solicitante": sesion["usuario"], "tipo_propuesta": solicitud.tipo_propuesta,
                                     "id_propuesta": None, "error": None}
    background_tasks.add_task(ejecutar_generacion_background, id_trabajo, solicitud.model_dump(),
                              sesion["usuario"], sesion["rol"])
    return JSONResponse(status_code=202, content={
        "status": "en_curso", "id_trabajo": id_trabajo,
        "mensaje": "La IA está diseñando la propuesta. Puede tardar unos minutos."})

@app.get("/api/generaciones/{id_trabajo}")
async def estado_generacion(id_trabajo: str, request: Request):
    requerir_sesion(request, ROLES_GENERADORES)
    trabajo = _generaciones.get(id_trabajo)
    if not trabajo:
        raise HTTPException(status_code=404, detail="No se encontró la generación (¿se reinició el servidor?).")
    return JSONResponse(trabajo)

@app.post("/api/propuestas/{id_propuesta}/restaurar")
async def restaurar_a_pendiente(id_propuesta: str, request: Request, background_tasks: BackgroundTasks):
    """Reabre una propuesta aprobada o rechazada (queda auditado; el Excel aprobado se conserva)."""
    sesion = requerir_sesion(request, ROLES_DECISORES)
    try:
        prop = _crear_engine().reabrir_propuesta(id_propuesta, sesion["usuario"], sesion["rol"])
    except Exception as e:
        raise _error_http(e)
    background_tasks.add_task(sincronizar_db_background)
    return JSONResponse({
        "status": "ok",
        "mensaje": f"Propuesta {id_propuesta} reabierta para revisión.",
        "propuesta": prop.model_dump()
    })

@app.get("/api/auditoria/men")
async def obtener_bitacora_auditoria_men(request: Request):
    """Devuelve el consolidado de trazabilidad de todas las propuestas para el Decreto 1330 del MEN."""
    requerir_sesion(request)
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
        "normativa": "Decreto 1330 de 2019 - Ministerio de Educación Nacional (MEN)",
        "resumen_estados": datos["resumen_estados"],
        "total_eventos_auditoria": len(bitacora),
        "eventos": bitacora
    })

# ==============================================================================
# ENDPOINTS DE DESCARGA DE ARCHIVOS EXCEL FORMATO MIG
# ==============================================================================
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

@app.api_route("/descargas/{filename}", methods=["GET", "HEAD"])
async def descargar_archivo_mig(filename: str, request: Request):
    """
    Descarga la Matriz MIG de una propuesta. Si está aprobada se entrega el Excel congelado
    (público); los borradores solo los descargan aprobador y administrador.
    """
    safe_name = os.path.basename(filename)
    m = re.match(r"^(PROP_\d+)", safe_name)
    propuesta = buscar_propuesta_dict(obtener_datos_curriculares(), m.group(1)) if m else None
    if not propuesta:
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe.")

    if propuesta["estado"] == "APROBADO":
        congelado = ruta_excel_aprobado(propuesta["id_propuesta"], propuesta["version"])
        if congelado.exists():
            return FileResponse(path=str(congelado), filename=congelado.name, media_type=XLSX_MEDIA_TYPE)
    elif not puede_decidir(obtener_aprobador_actual(request)):
        raise HTTPException(status_code=403, detail="La propuesta aún no está aprobada.")

    candidatos = list(MIG_DIR.glob(f"{propuesta['id_propuesta']}_*_MIG.xlsx")) if MIG_DIR.exists() else []
    if not candidatos:
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe.")
    return FileResponse(path=str(candidatos[0]), filename=candidatos[0].name, media_type=XLSX_MEDIA_TYPE)

@app.api_route("/descargas/consolidado/master", methods=["GET", "HEAD"])
async def descargar_consolidado():
    """Descarga directa del libro maestro consolidado de propuestas."""
    consolidado_path = MIG_DIR / "ofertas_academicas_mig_consolidado.xlsx"
    if not consolidado_path.exists():
        raise HTTPException(status_code=404, detail="El libro consolidado no se encuentra disponible.")
        
    return FileResponse(
        path=str(consolidado_path),
        filename="MATRIZ_MIG_MASTER_PROPUESTAS.xlsx",
        media_type=XLSX_MEDIA_TYPE
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
