-- =============================================================================
-- 03_marts.sql
-- Vistas de negocio ("marts"). Cada una responde una pregunta concreta, que va
-- en su encabezado. Alimentan Looker Studio (como CSV) y sirven de referencia
-- para las medidas DAX de Power BI.
--
-- Convenciones:
--   n_filas  = filas semana × centro × comida (NO es número de pedidos)
--   pedidos  = suma de num_orders
--   ingreso_estimado = suma de pedidos × precio_checkout (unidades anónimas)
-- Todo es descriptivo: ninguna vista estima efectos causales.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- mart_kpis
-- Pregunta: ¿cuál es el tamaño del negocio en el periodo observado?
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_kpis AS
SELECT
    COUNT(*)                                   AS n_filas,
    SUM(pedidos)                               AS pedidos_totales,
    SUM(ingreso_estimado)                      AS ingreso_estimado,
    AVG(precio_checkout)                       AS precio_promedio_fila,
    SUM(ingreso_estimado) / SUM(pedidos)       AS precio_promedio_ponderado,
    COUNT(DISTINCT center_id)                  AS n_centros,
    COUNT(DISTINCT meal_id)                    AS n_comidas,
    COUNT(DISTINCT semana)                     AS n_semanas,
    SUM(pedidos) / COUNT(DISTINCT semana)      AS pedidos_por_semana
FROM fct_demanda;


-- -----------------------------------------------------------------------------
-- mart_tendencia_semanal
-- Pregunta: ¿cómo evoluciona la demanda semana a semana y frente a la misma
-- semana del año relativo anterior?
-- Técnicas: CTE, LAG, media móvil con marco ROWS, acumulado por partición.
-- Se parte de dim_semana (LEFT JOIN) para que una semana sin datos aparezca
-- como hueco y LAG no compare semanas que no son consecutivas.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_tendencia_semanal AS
WITH semanal AS (
    SELECT
        semana,
        COUNT(*)              AS n_filas,
        SUM(pedidos)          AS pedidos,
        SUM(ingreso_estimado) AS ingreso_estimado,
        AVG(precio_checkout)  AS precio_promedio,
        AVG(CASE WHEN tipo_promocion <> 'Sin promoción' THEN 1.0 ELSE 0.0 END) AS pct_filas_con_promo
    FROM fct_demanda
    GROUP BY semana
),
con_calendario AS (
    SELECT d.semana, d.anio_relativo, d.semana_del_anio, d.etiqueta_trimestre,
           s.n_filas, s.pedidos, s.ingreso_estimado, s.precio_promedio, s.pct_filas_con_promo
    FROM dim_semana AS d
    LEFT JOIN semanal AS s USING (semana)
)
SELECT
    *,
    LAG(pedidos) OVER w                                        AS pedidos_semana_anterior,
    pedidos / NULLIF(LAG(pedidos) OVER w, 0) - 1               AS var_semanal_pct,
    CASE WHEN COUNT(pedidos) OVER w4 = 4
         THEN AVG(pedidos) OVER w4 END                         AS media_movil_4s,
    LAG(pedidos, 52) OVER w                                    AS pedidos_hace_52s,
    pedidos / NULLIF(LAG(pedidos, 52) OVER w, 0) - 1           AS var_interanual_pct,
    SUM(pedidos) OVER (PARTITION BY anio_relativo ORDER BY semana
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS pedidos_acumulados_anio
FROM con_calendario
WINDOW w  AS (ORDER BY semana),
       w4 AS (ORDER BY semana ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
ORDER BY semana;


-- -----------------------------------------------------------------------------
-- mart_categorias
-- Pregunta: ¿qué categorías concentran la demanda y a qué precio se venden?
-- Técnicas: participación con SUM() OVER (), RANK.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_categorias AS
WITH por_categoria AS (
    SELECT
        c.categoria,
        COUNT(*)                AS n_filas,
        SUM(f.pedidos)          AS pedidos,
        AVG(f.pedidos)          AS pedidos_promedio_fila,
        SUM(f.ingreso_estimado) AS ingreso_estimado,
        AVG(f.precio_checkout)  AS precio_promedio,
        AVG(f.precio_base)      AS precio_base_promedio,
        COUNT(DISTINCT f.meal_id) AS n_comidas
    FROM fct_demanda AS f
    JOIN dim_comida AS c USING (meal_id)
    GROUP BY c.categoria
)
SELECT
    *,
    pedidos / SUM(pedidos) OVER ()                   AS participacion_pedidos,
    ingreso_estimado / SUM(ingreso_estimado) OVER () AS participacion_ingreso,
    RANK() OVER (ORDER BY pedidos DESC)              AS ranking_pedidos
FROM por_categoria
ORDER BY ranking_pedidos;


-- -----------------------------------------------------------------------------
-- mart_comidas_abc
-- Pregunta: ¿qué comidas sostienen el negocio? Clasificación ABC (Pareto) y
-- ranking dentro de su categoría.
-- Regla ABC: una comida es A si los pedidos acumulados ANTES de ella suman
-- menos del 80 %; B si suman menos del 95 %; C en otro caso. Así la comida que
-- cruza el umbral del 80 % cuenta como A.
-- Técnicas: suma acumulada con marco ROWS, DENSE_RANK por partición.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_comidas_abc AS
WITH por_comida AS (
    SELECT
        f.meal_id, c.categoria, c.cocina,
        SUM(f.pedidos)          AS pedidos,
        SUM(f.ingreso_estimado) AS ingreso_estimado,
        AVG(f.precio_checkout)  AS precio_promedio,
        COUNT(DISTINCT f.center_id) AS n_centros
    FROM fct_demanda AS f
    JOIN dim_comida AS c USING (meal_id)
    GROUP BY f.meal_id, c.categoria, c.cocina
),
acumulado AS (
    SELECT
        *,
        pedidos / SUM(pedidos) OVER () AS participacion,
        SUM(pedidos) OVER (ORDER BY pedidos DESC, meal_id
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            / SUM(pedidos) OVER ()     AS participacion_acumulada
    FROM por_comida
)
SELECT
    *,
    CASE
        WHEN participacion_acumulada - participacion < 0.80 THEN 'A'
        WHEN participacion_acumulada - participacion < 0.95 THEN 'B'
        ELSE 'C'
    END                                                        AS clase_abc,
    ROW_NUMBER() OVER (ORDER BY pedidos DESC, meal_id)         AS ranking_global,
    DENSE_RANK() OVER (PARTITION BY categoria ORDER BY pedidos DESC) AS ranking_en_categoria,
    pedidos / SUM(pedidos) OVER (PARTITION BY categoria)       AS participacion_en_categoria
FROM acumulado
ORDER BY ranking_global;


-- -----------------------------------------------------------------------------
-- mart_promociones_matriz
-- Pregunta: ¿cuántos pedidos tiene en promedio una fila según el tipo de
-- promoción? (Matriz 2 × 2 email × home, igual a la del estudio v3.3.0.)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_promociones_matriz AS
SELECT
    promo_email,
    destacado_home,
    tipo_promocion,
    COUNT(*)              AS n_filas,
    AVG(pedidos)          AS pedidos_promedio_fila,
    AVG(precio_checkout)  AS precio_promedio,
    AVG(variacion_precio_pct) AS variacion_precio_pct_promedio
FROM fct_demanda
GROUP BY promo_email, destacado_home, tipo_promocion
ORDER BY promo_email, destacado_home;


-- -----------------------------------------------------------------------------
-- mart_promociones_indice
-- Pregunta: en las semanas con promoción, ¿cuánto vende una comida en un
-- centro frente a lo que esa misma comida vende en ese mismo centro sin
-- promoción?
-- El índice compara cada fila con la media sin promoción de su par
-- centro × comida (1,00 = igual; 2,00 = el doble). Así no se mezclan centros
-- grandes con chicos. Sigue siendo descriptivo: las semanas con promoción
-- también suelen tener otro precio y otra temporada.
-- Técnicas: AVG condicional como función de ventana por partición.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_promociones_indice AS
WITH con_base AS (
    SELECT
        f.*,
        AVG(CASE WHEN f.tipo_promocion = 'Sin promoción' THEN f.pedidos END)
            OVER (PARTITION BY f.center_id, f.meal_id) AS base_sin_promo
    FROM fct_demanda AS f
)
SELECT
    c.categoria,
    b.tipo_promocion,
    COUNT(*)                          AS n_filas,
    AVG(b.pedidos)                    AS pedidos_promedio_fila,
    AVG(b.pedidos / b.base_sin_promo) AS indice_vs_sin_promo,
    MEDIAN(b.pedidos / b.base_sin_promo) AS indice_mediano_vs_sin_promo,
    AVG(b.variacion_precio_pct)       AS variacion_precio_pct_promedio
FROM con_base AS b
JOIN dim_comida AS c USING (meal_id)
WHERE b.base_sin_promo IS NOT NULL        -- pares que alguna vez vendieron sin promoción
  AND b.tipo_promocion <> 'Sin promoción'
GROUP BY c.categoria, b.tipo_promocion
ORDER BY c.categoria, b.tipo_promocion;


-- -----------------------------------------------------------------------------
-- mart_centros
-- Pregunta: ¿qué centros venden más, en total y dentro de su tipo, y cómo se
-- reparten en cuartiles?
-- Técnicas: RANK global y por partición, NTILE, participación.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_centros AS
WITH por_centro AS (
    SELECT
        f.center_id,
        COUNT(*)                  AS n_filas,
        SUM(f.pedidos)            AS pedidos,
        SUM(f.ingreso_estimado)   AS ingreso_estimado,
        AVG(f.precio_checkout)    AS precio_promedio,
        COUNT(DISTINCT f.meal_id) AS n_comidas,
        COUNT(DISTINCT f.semana)  AS n_semanas_activas
    FROM fct_demanda AS f
    GROUP BY f.center_id
)
SELECT
    p.center_id,
    d.tipo_centro, d.codigo_region, d.codigo_ciudad, d.area_operativa,
    p.n_filas, p.pedidos, p.ingreso_estimado, p.precio_promedio,
    p.n_comidas, p.n_semanas_activas,
    p.pedidos / p.n_semanas_activas                         AS pedidos_por_semana_activa,
    p.pedidos / d.area_operativa                            AS pedidos_por_unidad_area,
    p.pedidos / SUM(p.pedidos) OVER ()                      AS participacion_pedidos,
    RANK() OVER (ORDER BY p.pedidos DESC)                   AS ranking_global,
    RANK() OVER (PARTITION BY d.tipo_centro ORDER BY p.pedidos DESC) AS ranking_en_tipo,
    NTILE(4) OVER (ORDER BY p.pedidos DESC, p.center_id)    AS cuartil   -- 1 = los que más venden
FROM por_centro AS p
JOIN dim_centro AS d USING (center_id)
ORDER BY ranking_global;


-- -----------------------------------------------------------------------------
-- mart_tipos_centro
-- Pregunta: ¿cómo se comparan los tipos de centro? (Igual a la tabla del
-- estudio v3.3.0, más ingreso y participación.)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_tipos_centro AS
SELECT
    d.tipo_centro,
    COUNT(*)                    AS n_filas,
    AVG(f.pedidos)              AS pedidos_promedio_fila,
    SUM(f.pedidos)              AS pedidos,
    SUM(f.ingreso_estimado)     AS ingreso_estimado,
    AVG(f.precio_checkout)      AS precio_promedio,
    COUNT(DISTINCT f.center_id) AS n_centros,
    SUM(f.pedidos) / SUM(SUM(f.pedidos)) OVER () AS participacion_pedidos
FROM fct_demanda AS f
JOIN dim_centro AS d USING (center_id)
GROUP BY d.tipo_centro
ORDER BY d.tipo_centro;


-- -----------------------------------------------------------------------------
-- mart_cohortes
-- Pregunta: cuando un centro empieza a vender una comida, ¿sigue vendiéndola
-- en los trimestres siguientes?
-- Cohorte = trimestre relativo (13 semanas) de la primera venta del par
-- centro × comida. Periodo k = el bloque de 13 semanas que empieza
-- 13·k semanas después de esa primera venta. Un par está "activo" en el
-- periodo k si tiene al menos una fila en ese bloque.
-- Control de censura: solo cuentan los pares cuyo bloque k cae completo dentro
-- de las semanas observadas; si no, las cohortes recientes parecerían
-- abandonar comidas que en realidad aún no se pueden observar.
-- Técnicas: MIN() OVER por partición, generación de periodos, agregados
-- condicionales.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_cohortes AS
WITH primera AS (
    SELECT center_id, meal_id, MIN(semana) AS semana_inicio
    FROM fct_demanda
    GROUP BY center_id, meal_id
),
limites AS (
    SELECT MAX(semana) AS semana_max FROM dim_semana
),
actividad AS (
    SELECT
        f.center_id, f.meal_id,
        (f.semana - p.semana_inicio) // 13 AS periodo
    FROM fct_demanda AS f
    JOIN primera AS p USING (center_id, meal_id)
    GROUP BY ALL
),
pares_periodos AS (
    -- Todos los periodos observables completos de cada par
    SELECT
        p.center_id, p.meal_id, p.semana_inicio,
        (p.semana_inicio - 1) // 13 + 1 AS cohorte_trimestre,
        k.periodo
    FROM primera AS p, limites AS l,
         LATERAL (SELECT UNNEST(range(0, (l.semana_max - p.semana_inicio + 1) // 13)) AS periodo) AS k
)
SELECT
    pp.cohorte_trimestre,
    pp.periodo                                  AS periodo_desde_inicio,
    COUNT(*)                                    AS pares_observables,
    COUNT(a.periodo)                            AS pares_activos,
    COUNT(a.periodo) / COUNT(*)                 AS tasa_retencion
FROM pares_periodos AS pp
LEFT JOIN actividad AS a
       ON a.center_id = pp.center_id
      AND a.meal_id   = pp.meal_id
      AND a.periodo   = pp.periodo
GROUP BY pp.cohorte_trimestre, pp.periodo
ORDER BY pp.cohorte_trimestre, pp.periodo;


-- -----------------------------------------------------------------------------
-- mart_bandas_precio
-- Pregunta: ¿cómo cambia el volumen promedio por fila según el nivel de
-- precio, en general y dentro de cada categoría?
-- Deciles con NTILE(10); el desempate por id hace el resultado reproducible.
-- Es un descriptivo bivariado (sin controles); la curva de elasticidad con
-- controles está en mart_elasticidad_rcs.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_bandas_precio AS
WITH con_decil AS (
    SELECT 'Todas' AS categoria, f.precio_checkout, f.pedidos,
           NTILE(10) OVER (ORDER BY f.precio_checkout, f.id) AS decil_precio
    FROM fct_demanda AS f
    UNION ALL
    SELECT c.categoria, f.precio_checkout, f.pedidos,
           NTILE(10) OVER (PARTITION BY c.categoria ORDER BY f.precio_checkout, f.id)
    FROM fct_demanda AS f
    JOIN dim_comida AS c USING (meal_id)
)
SELECT
    categoria,
    decil_precio,
    COUNT(*)              AS n_filas,
    MIN(precio_checkout)  AS precio_min,
    MAX(precio_checkout)  AS precio_max,
    AVG(precio_checkout)  AS precio_promedio,
    AVG(pedidos)          AS pedidos_promedio_fila,
    MEDIAN(pedidos)       AS pedidos_mediana_fila
FROM con_decil
GROUP BY categoria, decil_precio
ORDER BY categoria, decil_precio;
