-- =============================================================================
-- Capa de datos compartida del observatorio (vistas obs_*)
-- La usan el tablero de Superset y, más adelante, la landing (narrativa con scroll).
-- Reglas: conteos de ofertas DISTINTAS; cada cifra debe poder acompañarse de su n;
-- nada se imputa (salario ausente = NULL, no cero).
-- Aplicar con: python superset/aplicar_vistas.py   (requiere el rol propietario)
-- =============================================================================

-- Una fila por oferta y mes en que fue detectada
CREATE OR REPLACE VIEW obs_ofertas_mes AS
SELECT
    e.mes_periodo,
    TO_DATE(e.mes_periodo::text || '01', 'YYYYMMDD') AS periodo,
    TO_CHAR(TO_DATE(e.mes_periodo::text || '01', 'YYYYMMDD'), 'YYYY-MM') AS mes,
    e.id_vacante_hash,
    d.portal,
    d.tipo_mercado,
    CASE WHEN d.tipo_mercado LIKE 'Mercado Local%' THEN 'Local' ELSE 'Internacional' END AS mercado,
    d.rol_buscado,
    d.modalidad,
    d.seniority,
    CASE WHEN e.salario_cop_mensual > 0 THEN e.salario_cop_mensual END AS salario_cop_mensual,
    (e.salario_cop_mensual > 0) IS TRUE AS tiene_salario,
    -- Nueva = primer mes en que el observatorio la vio (en el primer corte, todas son nuevas)
    e.mes_periodo = MIN(e.mes_periodo) OVER (PARTITION BY e.id_vacante_hash) AS es_nueva
FROM fact_extracciones_historico e
JOIN dim_ofertas d USING (id_vacante_hash);

-- Demanda de habilidades: periodo × mercado × portal × habilidad, con CEROS explícitos para que
-- 100·SUM(ofertas_con_habilidad)/SUM(ofertas_totales) sea correcto bajo cualquier filtro.
CREATE OR REPLACE VIEW obs_demanda_habilidades AS
WITH base AS (
    SELECT mes_periodo, periodo, mes, tipo_mercado, portal, COUNT(*) AS ofertas_totales
    FROM obs_ofertas_mes
    GROUP BY 1, 2, 3, 4, 5
),
habilidades AS (
    SELECT DISTINCT habilidad FROM fact_habilidades_historico
),
conteo AS (
    SELECT h.mes_periodo, d.tipo_mercado, d.portal, h.habilidad,
           COUNT(DISTINCT h.id_vacante_hash) AS n
    FROM fact_habilidades_historico h
    JOIN dim_ofertas d USING (id_vacante_hash)
    GROUP BY 1, 2, 3, 4
)
SELECT
    b.mes_periodo,
    b.periodo,
    b.mes,
    b.tipo_mercado,
    b.portal,
    hab.habilidad,
    COALESCE(c.n, 0) AS ofertas_con_habilidad,
    b.ofertas_totales,
    -- Último corte disponible (Superset no permite subconsultas en el SQL de un gráfico)
    b.mes_periodo = (SELECT MAX(mes_periodo) FROM fact_extracciones_historico) AS es_ultimo_mes
FROM base b
CROSS JOIN habilidades hab
LEFT JOIN conteo c
       ON c.mes_periodo = b.mes_periodo AND c.tipo_mercado = b.tipo_mercado
      AND c.portal = b.portal AND c.habilidad = hab.habilidad;

-- Salario por habilidad: una fila por oferta CON salario y habilidad (sin duplicar la misma oferta
-- vista en varios meses: se toma su último mes). Para medianas por habilidad con su n.
CREATE OR REPLACE VIEW obs_salarios_habilidad AS
SELECT DISTINCT ON (h.id_vacante_hash, h.habilidad)
    o.mes_periodo,
    o.periodo,
    h.id_vacante_hash,
    h.habilidad,
    o.tipo_mercado,
    o.portal,
    o.salario_cop_mensual
FROM fact_habilidades_historico h
JOIN obs_ofertas_mes o USING (id_vacante_hash, mes_periodo)
WHERE o.salario_cop_mensual IS NOT NULL
ORDER BY h.id_vacante_hash, h.habilidad, o.mes_periodo DESC;

-- Diferencia salarial por habilidad frente a la mediana de su mercado (todo el histórico,
-- ofertas sin duplicar). Solo habilidades con al menos 5 ofertas con salario.
-- Es una comparación descriptiva de medianas, NO un efecto causal (no controla experiencia ni rol).
CREATE OR REPLACE VIEW obs_diferencia_salarial AS
WITH ofertas AS (
    SELECT DISTINCT ON (id_vacante_hash) id_vacante_hash, tipo_mercado, salario_cop_mensual
    FROM obs_ofertas_mes
    WHERE salario_cop_mensual IS NOT NULL
    ORDER BY id_vacante_hash, mes_periodo DESC
),
mercado AS (
    SELECT tipo_mercado,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_cop_mensual) AS mediana_mercado,
           COUNT(*) AS n_mercado
    FROM ofertas GROUP BY 1
),
habilidad AS (
    SELECT tipo_mercado, habilidad,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_cop_mensual) AS mediana_habilidad,
           COUNT(*) AS n_ofertas_con_salario
    FROM obs_salarios_habilidad GROUP BY 1, 2
)
SELECT
    h.tipo_mercado,
    CASE WHEN h.tipo_mercado LIKE 'Mercado Local%' THEN 'Local' ELSE 'Internacional' END AS mercado,
    h.habilidad,
    h.n_ofertas_con_salario,
    ROUND(h.mediana_habilidad::numeric) AS mediana_habilidad_cop,
    ROUND(m.mediana_mercado::numeric) AS mediana_mercado_cop,
    m.n_mercado AS n_ofertas_mercado,
    ROUND((100.0 * (h.mediana_habilidad - m.mediana_mercado) / m.mediana_mercado)::numeric, 1) AS diferencia_pct
FROM habilidad h
JOIN mercado m USING (tipo_mercado)
WHERE h.n_ofertas_con_salario >= 5;

-- Primas salariales con controles (scripts/analisis_primas_salariales.py), último corte analizado.
-- Asociación condicionada en ofertas locales que publican salario; no es un efecto causal.
CREATE OR REPLACE VIEW obs_primas_habilidad AS
SELECT
    habilidad,
    n_ofertas,
    prima_pct,
    ic95_inferior_pct,
    ic95_superior_pct,
    q_bh,
    CASE WHEN concluyente THEN 'Sí' ELSE 'No' END AS concluyente,
    n_muestra,
    ultimo_corte
FROM analisis_primas_habilidad
WHERE ultimo_corte = (SELECT MAX(ultimo_corte) FROM analisis_primas_habilidad);

CREATE OR REPLACE VIEW obs_primas_rol AS
SELECT
    rol,
    rol_referencia,
    n_ofertas,
    prima_pct,
    ic95_inferior_pct,
    ic95_superior_pct,
    q_bh,
    CASE WHEN NOT evaluable THEN 'No evaluable (n < 20)'
         WHEN rol = rol_referencia THEN 'Referencia'
         WHEN concluyente THEN 'Sí' ELSE 'No' END AS resultado,
    n_muestra,
    ultimo_corte,
    -- Orden de lectura: referencia, roles estimados, roles sin muestra suficiente
    CASE WHEN rol = rol_referencia THEN 0 WHEN evaluable THEN 1 ELSE 2 END AS orden
FROM analisis_primas_rol
WHERE ultimo_corte = (SELECT MAX(ultimo_corte) FROM analisis_primas_rol);

-- Roles emergentes / en descenso: cambio de participación frente al mes anterior en portales comparables
-- (presentes en ambos meses y sin cambios en sus términos de búsqueda). Resultado de
-- scripts/analisis_tendencia_roles.py; con menos de 3 cortes no es una tendencia (es_tendencia = false).
CREATE OR REPLACE VIEW obs_tendencia_roles AS
SELECT
    rol,
    n_ofertas_anterior,
    pct_anterior,
    n_ofertas,
    pct,
    cambio_pp,
    q_bh,
    estado,
    to_char(to_date(mes_anterior::text, 'YYYYMM'), 'YYYY-MM') AS mes_anterior,
    to_char(to_date(mes_periodo::text, 'YYYYMM'), 'YYYY-MM') AS mes,
    portales_comparados,
    portales_excluidos,
    n_total,
    n_total_anterior,
    es_tendencia,
    cortes_disponibles
FROM analisis_tendencia_roles
WHERE mes_periodo = (SELECT MAX(mes_periodo) FROM analisis_tendencia_roles);
