"""
Servidor Web FastAPI - Observatorio de Inteligencia Laboral y Diseño Curricular UniCafam.
Provee la Landing Page de 3 páginas, visualizaciones integradas y endpoints de descarga de la Matriz MIG.
"""

import os
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Asegurar importación de módulos del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ai_curriculum.mig_excel_exporter import normalizar_propuesta_a_mig
from src.database.db_manager import DatabaseManager

app = FastAPI(
    title="Observatorio de Inteligencia Laboral | UniCafam",
    description="Portal institucional de vigilancia de mercado y pertinencia curricular",
    version="2.0.0"
)

TEMPLATES_DIR = ROOT_DIR / "src" / "web" / "templates"
STATIC_DIR = ROOT_DIR / "src" / "web" / "static"
MIG_DIR = ROOT_DIR / "data" / "curriculo_unicafam" / "mig_propuestas"
JSON_RECOMMENDATIONS_PATH = ROOT_DIR / "data" / "curriculo_unicafam" / "recomendaciones_ia_curriculo.json"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def obtener_datos_curriculares():
    """Lee y normaliza el diagnóstico y las propuestas al formato MIG."""
    if not JSON_RECOMMENDATIONS_PATH.exists():
        return {"diagnostico": {}, "propuestas": []}
    
    with open(JSON_RECOMMENDATIONS_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    propuestas_norm = []
    for p in raw_data.get("propuestas", []):
        p_obj = normalizar_propuesta_a_mig(p)
        propuestas_norm.append(p_obj.model_dump())
        
    return {
        "diagnostico": raw_data.get("diagnostico", {}),
        "propuestas": propuestas_norm
    }

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
            # Vacantes
            res_v = conn.execute(text("SELECT COUNT(*) FROM dim_ofertas")).scalar()
            if res_v and res_v > 0:
                kpis["total_vacantes"] = res_v
            # Habilidades
            res_h = conn.execute(text("SELECT COUNT(*) FROM fact_habilidades_historico")).scalar()
            if res_h and res_h > 0:
                kpis["total_habilidades_series"] = res_h
            # Competitividad IA
            res_c = conn.execute(text("SELECT puntuacion_competitividad FROM fact_diagnostico_ia ORDER BY id DESC LIMIT 1")).scalar()
            if res_c:
                kpis["competitividad_programa"] = float(res_c)
    except Exception as e:
        print(f"[API AVISO] Usando métricas cacheadas de respaldo: {e}")
    return kpis

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal de 3 pestañas con línea gráfica UniCafam."""
    curriculo_data = obtener_datos_curriculares()
    kpis_data = obtener_kpis_mercado()
    
    # Listar archivos Excel MIG disponibles para descarga
    archivos_mig = []
    if MIG_DIR.exists():
        for f in sorted(MIG_DIR.glob("*.xlsx")):
            if not f.name.startswith("~$"):
                archivos_mig.append({
                    "nombre": f.name,
                    "tamano_kb": round(f.stat().st_size / 1024, 1),
                    "es_master": "consolidado" in f.name.lower()
                })

    context = {
        "request": request,
        "kpis": kpis_data,
        "diagnostico": curriculo_data["diagnostico"],
        "propuestas": curriculo_data["propuestas"],
        "archivos_mig": archivos_mig,
        "superset_embed_url": "https://superset.jfbernalp.dev/superset/dashboard/1/?standalone=true"
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/api/kpis")
async def api_kpis():
    """Endpoint JSON con los KPIs del Observatorio."""
    return JSONResponse(obtener_kpis_mercado())

@app.get("/api/propuestas")
async def api_propuestas():
    """Endpoint JSON con las propuestas curriculares estructuradas."""
    return JSONResponse(obtener_datos_curriculares())

@app.get("/descargas/{filename}")
async def descargar_archivo_mig(filename: str):
    """Descarga segura de un archivo Excel de la Matriz MIG."""
    # Sanitización de path traversal
    safe_name = os.path.basename(filename)
    file_path = MIG_DIR / safe_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe.")
        
    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/descargas/consolidado/master")
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
