# Observatorio del mercado laboral en datos — contexto para retomar el trabajo

Leer primero este archivo. Luego, para el detalle histórico, `docs/bitacora_proyecto.md`, que es solo local
(ver "Reglas de trabajo"). Estado al **7-nov-2026**: versión `v0.13.1` en `main`; local, GitHub y Hetzner
sincronizados.

## Qué es

Observatorio que mide cada mes las tendencias del mercado laboral en roles de datos: análisis de datos,
ciencia de datos, ingeniería de datos y BI. Hace tres cosas:
- recolecta vacantes de portales de empleo;
- aplica análisis estadístico (demanda de habilidades, primas salariales con intervalos de confianza);
- integra un LLM que diseña propuestas curriculares usando solo cifras del observatorio, con verificación
  automática y aprobación humana.

Autor e identidad pública: **Juan Felipe Bernal · Data Scientist**. El sitio no menciona a UniCafam
(decisión del 28-oct-2026). El contenido curricular (prompt, propuestas, Excel MIG) sí describe los
programas de UniCafam; generalizarlo está pendiente de decisión.

Próximo frente (7-nov-2026): **artículo científico** sobre la plataforma y los hallazgos. Ver
"Artículo científico".

## Dónde vive

| Componente | Ubicación |
|---|---|
| Repositorio principal | `github.com/jfbernalp/proyecto_investigativo` (público). **Git es la fuente de verdad.** |
| Clon local | `/Users/juan/Documents/proyecto_investigativo` (`.venv` con Python 3.14) |
| Servidor | Hetzner `juan@2.29.41.159`, `/home/juan/proyecto_investigativo`, contenedor `unicafam-portal` (docker compose; `data/` y `docs/` montados). Sin credenciales de GitHub. |
| Landing y portal curricular | `https://jfbernalp.dev` (FastAPI + Jinja, Tailwind por CDN) |
| Tablero | `https://superset.jfbernalp.dev`, dashboard 1 (Superset 6.1, stack en `/home/juan/superset-stack`, contenedor `superset-stack-superset-1`, usuario de API `claude_api` con rol Alpha) |
| Base histórica | Supabase Postgres 17 (`DATABASE_URL` en el `.env` local) |
| Corte mensual | GitHub Actions `monthly_scraping.yml`, cron `0 0 1 * *` (31 de cada mes, 19:00 Colombia) → periodo del mes siguiente |
| Otro proyecto en el mismo servidor | HR Copilot (`/home/juan/hr-copilot`, `hr.jfbernalp.dev`): **no tocar** desde este proyecto |

## Cómo retomar ("reiniciemos")

1. Leer este archivo y las secciones recientes de `docs/bitacora_proyecto.md` (hitos 38 y siguientes).
2. Verificar acceso y sincronía:
   - local: `git pull`;
   - servidor: `ssh juan@2.29.41.159 'cd /home/juan/proyecto_investigativo && git log --oneline -1'`;
   - GitHub: `git ls-remote origin refs/heads/main`.

   Las tres deben coincidir.
3. Pruebas: `.venv/bin/python -m pytest -q` (120 pasan).
4. Después de un corte mensual: `.venv/bin/python scripts/revisar_corte.py` (solo lectura) y el checklist
   del hito 38.
5. Preguntar a Juan qué sigue.

## Arquitectura

```
Portales ──► src/scrapers/* ──► src/processing/* ──► Supabase (histórico protegido)
                                                         │
                    ┌────────────────────────────────────┼─────────────────────────────┐
                    ▼                                    ▼                             ▼
     superset/vistas_observatorio.sql      src/analytics/primas_salariales.py   src/ai_curriculum/contexto_mercado.py
     (vistas obs_*) ─► Superset            (OLS + IC 95 % + BH) ─► tablas         (contexto versionado con n y corte)
                    │                       analisis_primas_*                             │
                    ▼                                                                      ▼
     landing jfbernalp.dev (KPIs + tablero)          curriculum_engine.py (Gemini 4 Argon) ─► verificador_cifras.py
                                                      ─► portal: aprobar / rechazar / ajustar / nueva propuesta
```

- **Scrapers activos:** CompuTrabajo, ElEmpleo, GetOnBoard, LinkedIn, Talent.com, Magneto y Remotive (API
  pública; requiere atribución, que está en el pie de la landing). Torre.ai está desactivado (solo hay
  datos de sep-2026). Glassdoor se descartó (Cloudflare y robots.txt).
- **Cambios de diseño de búsqueda:** LinkedIn amplió sus términos el 17-oct-2026 (`60ff450`). Al
  comparar meses hay que excluirlo (`CAMBIOS_DISENO_BUSQUEDA` en `src/analytics/tendencia_roles.py`).
- **Base de datos:**
  - tablas protegidas append-only con triggers: `dim_ofertas`, `fact_extracciones_historico`,
    `fact_habilidades_historico`, `ofertas_raw_historico`;
  - mantenimiento solo con `SET LOCAL observatorio.permitir_mantenimiento='on'`;
  - índices únicos por (hash, mes);
  - rol `pipeline_observatorio` de mínimo privilegio (secreto `DATABASE_URL` de GitHub);
  - respaldo cifrado (AES-256, secreto `BACKUP_PASSPHRASE`) antes de cada escritura del pipeline.
- **Pipeline mensual:**
  1. respaldo;
  2. `main.py --all` (scraping, NLP, guardado);
  3. paso 6b, `scripts/analisis_primas_salariales.py --guardar-bd`.

  Corre en Python 3.12.
- **Portal curricular:**
  - **Roles:** visualizador, aprobador y administrador. Son cuentas por rol, no por persona; los hashes
    PBKDF2 están en el `.env` del servidor **entre comillas simples**.
  - **Acciones:** aprobar (congela el Excel MIG), rechazar con motivo, "Comentar y ajustar con IA"
    (genera v+1), reabrir, y "+ Nueva propuesta" (solo administrador; una a la vez).
  - **Auditoría:** cada acción queda registrada.
  - **Modelo y verificación:** Gemini 4 Argon por defecto, con Flash de respaldo. Cada versión guarda
    `modelo_ia`, `contexto_id` y `verificacion_cifras`.
- **Verificador de cifras** (`src/ai_curriculum/verificador_cifras.py`):
  - marca los porcentajes, montos y conteos que no están en el contexto o que se atribuyen a otra
    habilidad o rol;
  - marca las tarifas;
  - marca las inconsistencias de créditos y horas (1 crédito = 48 h = 16 TFD + 32 TTI).

  **Marca, no bloquea**: el aprobador decide.
- **Superset como código** (`superset/construir_tablero.py`, idempotente): 14 gráficos, filtros Mercado y
  Portal, `label_colors`. Cada dataset fija `cache_timeout = 300` s porque la conexión tiene 30 días.
  Se ejecuta con `superset/ejecutar_en_servidor.sh superset/construir_tablero.py`; las vistas se
  aplican con `superset/aplicar_vistas.py`.
- **Landing:**
  - narrativa por escenas con GSAP 3.13 (ScrollTrigger, SplitText) y Lenis 1.3.4, replicando
    davidecattaneo.it (análisis hecho con REA, hito 48);
  - respeta "reducir movimiento";
  - si el CDN falla, todo queda visible.

## Métodos estadísticos (base del artículo)

- **Primas salariales** (`src/analytics/primas_salariales.py`):
  - **Datos:** ofertas locales con salario publicado (ElEmpleo, Magneto, CompuTrabajo). Habilidades,
    experiencia y rol se calculan desde el texto crudo guardado, igual para todos los meses.
  - **Modelo:** OLS `log(salario) ~ habilidades + nivel + rol + portal + mes`, con errores robustos HC3.
  - **Lectura:** prima = exp(β) − 1; IC 95 %; q de Benjamini–Hochberg.
  - **Criterios:** solo habilidades con n ≥ 20. "Concluyente" = q ≤ 0,10 y un IC que no cruza 0.
    Robustez: se estima dejando fuera cada portal.
  - **Prima por rol:** frente al rol más frecuente, controlando nivel, portal y mes.
  - Es una asociación, no causalidad.
- **Seniority** (`src/processing/seniority.py`): años solo si la oferta los dice; nivel por título o
  portal solo cuando es inequívoco. Cada dato guarda su fuente.
- **Cambio de roles entre meses** (`src/analytics/tendencia_roles.py`): prueba de dos proporciones + BH,
  solo con portales comparables. Juan decidió no publicarlo en el tablero.
- **Pendiente propuesto:** prueba de equivalencia (TOST, margen a fijar antes de ver resultados) para
  distinguir "sin prima relevante" de "no concluyente".

## Hallazgos vigentes (citar siempre con corte y n)

Corte **2026-11-01** (fuentes: `/api/kpis`, `scripts/revisar_corte.py`, log de la corrida `41274337334`):

- **Muestra:** 907 vacantes únicas sep–nov 2026. En noviembre, 382 ofertas de 7 fuentes; 27,5 % publican
  salario.
- **Medianas de noviembre:** local 5.000.000 COP/mes (n = 93); internacional 12.800.000 COP/mes (n = 12,
  poco confiable).
- **Demanda de habilidades en noviembre (% de ofertas):** SQL 68,1, Python 63,9, ETL 51,6, Power BI 32,2,
  Estadística 31,4, ML 29,6, AWS 28,8, Azure 25,1, GCP 23,3, Excel Avanzado 19,1.
- **Primas** (176 ofertas locales con salario, sep–nov):
  - Analista de Datos frente a Científico de Datos: **−35,3 % [−45,0; −24,0]**, concluyente.
  - Data Engineer (n = 12) y BI (n = 11): no evaluables.
  - **Excel Avanzado: −17,0 % [−27,1; −5,5], q = 0,052, n = 58**. Es la primera prima por habilidad
    concluyente; es negativa y robusta al excluir cada portal (entre −14,8 % y −25,9 %). Hay que
    confirmarla en diciembre.
  - Ninguna prima positiva es concluyente (Azure +17,8 % [−6,1; +47,8]).
- **Roles sep→oct** (portales comparables, n 146 → 238): ningún cambio concluyente (q = 0,70). Con
  LinkedIn incluido aparecía un falso "Data Engineer emergente", efecto del cambio de búsqueda.
- **Cuidado al comparar:** octubre acumula varias corridas y noviembre una sola. El "−34 %" del tablero no
  es una caída del mercado.

## Reglas de trabajo (obligatorias)

1. **REGLA DE ORO: no inventar cifras ni datos.** "Dato no disponible" o "no concluyente" son respuestas
   válidas. Toda cifra lleva su n y su corte. Las cifras de la IA se verifican y se rotulan.
2. **Una rama por sesión.** Merge, push y despliegue solo con validación explícita de Juan, que quiere
   ver una vista previa local antes de autorizar cambios visuales.
3. **Producción** (Supabase, Superset, `.env`, despliegues): con autorización explícita. Primero simular,
   luego aplicar por separado.
4. **Secretos:** nunca imprimirlos ni repetirlos. Las contraseñas del portal se entregan en
   `/home/juan/credenciales_portal_20261026.txt` (pendiente de borrar).
5. **`docs/bitacora_proyecto.md` está fuera de git.** Respaldarla en
   `/Users/juan/Documents/backups_observatorio/` antes de cualquier checkout o merge.
6. **Sincronizar datos del servidor a git:**
   - `rsync` de `data/curriculo_unicafam/` (y `docs/informe_recomendaciones_unicafam_ia.md` si cambió)
     al local, commit y push;
   - en el servidor, `git fetch && git reset origin/main` (sin `--hard`).
7. **Base curricular:** `data/curriculo_unicafam/curriculo_unicafam.db` no se versiona. Si falta, se
   construye con `python src/curriculum/curriculum_db_sync.py`.

## Pendientes

- **Artículo científico:** definir el enfoque (en discusión desde el 7-nov-2026).
- **Decisiones de Juan:**
  - generalizar el contenido curricular sin UniCafam;
  - error 502 intermitente entre Traefik y Superset (keep-alive);
  - margen de equivalencia (TOST);
  - crédito a Remotive.
- **Seguridad:**
  - borrar el archivo de credenciales;
  - cuentas por persona (P2);
  - contraseña demo de HR Copilot en texto plano en su repo (otro proyecto; avisado).
- **Calidad de datos:**
  - inconsistencia de `rol_buscado` en `dim_ofertas` (mezcla palabra clave y rol clasificado);
  - la experiencia histórica sep–oct se calculó con el extractor anterior: no comparar esa columna entre
    meses.
- **Auditoría P2:**
  - portafolio en Postgres con cola de trabajos;
  - revisión ética y legal del scraping (sobre todo LinkedIn);
  - accesibilidad y Tailwind compilado;
  - aviso de IA en los Excel MIG;
  - contenedor sin root;
  - evaluar mover el cron a Hetzner.
- **Corte de diciembre (1-dic-2026):** primera comparación mes a mes limpia (una corrida contra una).
  Confirmar la prima de Excel Avanzado.
