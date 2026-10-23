-- =============================================================================
-- 02_modelo_estrella.sql
-- Esquema estrella: una tabla de hechos (semana × centro × comida) y tres
-- dimensiones. Es el modelo que importa Power BI.
--
--            dim_semana
--                |
--   dim_centro --+-- fct_demanda --+-- dim_comida
--
-- Grano de fct_demanda: una fila por semana, centro y comida con registro de
-- venta. Una combinación ausente significa "sin registro esa semana"; el
-- dataset no distingue entre "no ofrecida" y "cero pedidos".
-- =============================================================================

CREATE OR REPLACE TABLE dim_comida AS
SELECT
    meal_id,
    category AS categoria,
    cuisine  AS cocina
FROM stg_comidas;

CREATE OR REPLACE TABLE dim_centro AS
SELECT
    center_id,
    city_code   AS codigo_ciudad,
    region_code AS codigo_region,
    center_type AS tipo_centro,
    op_area     AS area_operativa
FROM stg_centros;

-- El dataset numera semanas (1, 2, ...) sin fechas de calendario. No se
-- inventan fechas: se derivan periodos relativos de 52 semanas.
-- La dimensión cubre todo el rango min..max para que los huecos se vean.
CREATE OR REPLACE TABLE dim_semana AS
WITH rango AS (
    SELECT MIN(week) AS semana_min, MAX(week) AS semana_max FROM stg_pedidos
)
SELECT
    s.semana,
    (s.semana - 1) // 52 + 1                  AS anio_relativo,
    (s.semana - 1) % 52 + 1                   AS semana_del_anio,
    ((s.semana - 1) % 52) // 13 + 1           AS trimestre_del_anio,
    'A' || ((s.semana - 1) // 52 + 1)
        || '-T' || (((s.semana - 1) % 52) // 13 + 1) AS etiqueta_trimestre,
    (s.semana - 1) // 4 + 1                   AS bloque_4_semanas
FROM rango,
     LATERAL (SELECT UNNEST(range(rango.semana_min, rango.semana_max + 1)) AS semana) AS s;

CREATE OR REPLACE TABLE fct_demanda AS
SELECT
    p.id,
    p.week                                    AS semana,
    p.center_id,
    p.meal_id,
    p.num_orders                              AS pedidos,
    p.checkout_price                          AS precio_checkout,
    p.base_price                              AS precio_base,
    p.emailer_for_promotion                   AS promo_email,
    p.homepage_featured                       AS destacado_home,
    CASE
        WHEN p.emailer_for_promotion = 1 AND p.homepage_featured = 1 THEN 'Email + home'
        WHEN p.emailer_for_promotion = 1 THEN 'Solo email'
        WHEN p.homepage_featured = 1 THEN 'Solo home'
        ELSE 'Sin promoción'
    END                                       AS tipo_promocion,
    -- Positivo: el precio pagado quedó por debajo del de referencia.
    -- Negativo: quedó por encima (pasa en ~25 % de las filas).
    (p.base_price - p.checkout_price) / p.base_price * 100 AS variacion_precio_pct,
    -- Pedidos × precio de checkout, en las unidades monetarias anónimas del
    -- dataset. Es una aproximación: no hay datos de ticket ni de costos.
    p.num_orders * p.checkout_price           AS ingreso_estimado
FROM stg_pedidos AS p;
