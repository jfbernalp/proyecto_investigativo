# Observatorio del mercado laboral en datos

Plataforma que mide cada mes las tendencias del mercado laboral en roles de datos (análisis de datos,
ciencia de datos, ingeniería de datos y BI). Recolecta vacantes publicadas, las procesa con reglas de
texto, aplica análisis estadístico (demanda de habilidades y primas salariales con intervalos de confianza)
e integra un LLM que diseña propuestas formativas usando solo cifras del observatorio, con verificación
automática y aprobación humana.

- **Sitio:** https://jfbernalp.dev · **Tablero:** https://superset.jfbernalp.dev
- **Autor:** Juan Felipe Bernal · Data Scientist
- **Contexto completo para desarrollo:** [`CLAUDE.md`](CLAUDE.md)

**Regla del observatorio:** no se inventan cifras. Si un dato no existe o la muestra no alcanza, la
respuesta es «dato no disponible» o «no concluyente», y toda cifra se publica con su tamaño de muestra
(n) y su fecha de corte.

## Componentes

| Capa | Código | Qué hace |
|---|---|---|
| Recolección | `src/scrapers/` | Siete fuentes de vacantes (portales nacionales e internacionales y una API pública de empleo remoto), con reintentos y reporte de salud. |
| Procesamiento | `src/processing/` | Taxonomía de habilidades, detección explícita de experiencia y nivel (con su fuente), clasificación de rol y de mercado, normalización salarial. |
| Persistencia | `src/database/db_manager.py`, `scripts/` | Histórico en PostgreSQL (Supabase) con tablas append-only, índices únicos por mes, rol de mínimo privilegio y respaldo cifrado antes de cada corte. |
| Análisis | `src/analytics/` | Primas salariales (OLS sobre log del salario, errores HC3, IC 95 %, Benjamini–Hochberg, robustez por portal) y comparación de roles entre meses con portales comparables. |
| Visualización | `superset/`, `src/web/templates/index.html` | Vistas `obs_*` y tablero de Apache Superset definidos como código; landing con narrativa por escenas. |
| IA curricular | `src/ai_curriculum/` | Contexto de mercado versionado → Gemini → propuestas en formato MIG → verificador de cifras (existencia, atribución, créditos y horas) → aprobación humana con auditoría. |
| Portal | `src/web/app.py` | FastAPI: revisión, aprobación, ajuste con IA y generación de propuestas por rol. |

## Uso

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q                       # pruebas
.venv/bin/python main.py --all --pages 5            # corte completo (lo hace GitHub Actions cada mes)
.venv/bin/python scripts/analisis_primas_salariales.py   # primas salariales (solo lectura)
.venv/bin/python scripts/revisar_corte.py           # revisión posterior a un corte (solo lectura)
.venv/bin/python main.py --web                      # portal local
```

Variables de entorno (en `.env`, nunca en el repositorio): `DATABASE_URL`, `GEMINI_API_KEY`,
`APPROVER_SECRET_KEY` y `PORTAL_HASH_*` (generadas con `scripts/generar_credenciales_portal.py`).

## Corte mensual

`.github/workflows/monthly_scraping.yml` corre el día 1 de cada mes a las 00:00 UTC:
1. respaldo cifrado de la base;
2. recolección, procesamiento y guardado del histórico;
3. análisis de primas salariales.

El tablero refleja el corte en menos de 5 minutos.

## Hallazgos

Las cifras vigentes, con su n y su fecha de corte, están en el tablero y en la sección «Hallazgos
vigentes» de [`CLAUDE.md`](CLAUDE.md). Las cifras exploratorias de septiembre de 2026 que este archivo
mostraba antes se retiraron: venían de un método con errores corregidos en octubre de 2026 (primas sin
controles, SQL inflado por NoSQL, ofertas mal clasificadas por mercado).
