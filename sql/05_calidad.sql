-- =============================================================================
-- 05_calidad.sql
-- Tests de calidad de datos. Cada fila de calidad_resultados es una regla y
-- cuenta cuántos registros la incumplen. El pipeline se detiene si algún
-- conteo es mayor que cero (ver pipeline/build.py).
-- =============================================================================

CREATE OR REPLACE TABLE calidad_resultados AS

-- Unicidad --------------------------------------------------------------------
SELECT 'pk_hechos_unica' AS regla,
       'Una sola fila por semana × centro × comida' AS descripcion,
       COALESCE(SUM(n - 1), 0) AS filas_con_error
FROM (SELECT COUNT(*) AS n FROM fct_demanda
      GROUP BY semana, center_id, meal_id HAVING COUNT(*) > 1)

UNION ALL
SELECT 'id_unico', 'El id original no se repite',
       COUNT(*) - COUNT(DISTINCT id)
FROM fct_demanda

UNION ALL
SELECT 'pk_dim_comida_unica', 'meal_id no se repite en dim_comida',
       COUNT(*) - COUNT(DISTINCT meal_id)
FROM dim_comida

UNION ALL
SELECT 'pk_dim_centro_unica', 'center_id no se repite en dim_centro',
       COUNT(*) - COUNT(DISTINCT center_id)
FROM dim_centro

-- Integridad referencial ------------------------------------------------------
UNION ALL
SELECT 'fk_comida', 'Toda comida de los hechos existe en dim_comida',
       COUNT(*)
FROM fct_demanda f ANTI JOIN dim_comida c USING (meal_id)

UNION ALL
SELECT 'fk_centro', 'Todo centro de los hechos existe en dim_centro',
       COUNT(*)
FROM fct_demanda f ANTI JOIN dim_centro c USING (center_id)

UNION ALL
SELECT 'fk_semana', 'Toda semana de los hechos existe en dim_semana',
       COUNT(*)
FROM fct_demanda f ANTI JOIN dim_semana s USING (semana)

-- Completitud -----------------------------------------------------------------
UNION ALL
SELECT 'hechos_sin_nulos', 'Ninguna columna clave o medida es nula',
       COUNT(*)
FROM fct_demanda
WHERE id IS NULL OR semana IS NULL OR center_id IS NULL OR meal_id IS NULL
   OR pedidos IS NULL OR precio_checkout IS NULL OR precio_base IS NULL
   OR promo_email IS NULL OR destacado_home IS NULL

UNION ALL
SELECT 'dimensiones_sin_nulos', 'Atributos de comida y centro completos',
       (SELECT COUNT(*) FROM dim_comida WHERE categoria IS NULL OR cocina IS NULL)
     + (SELECT COUNT(*) FROM dim_centro
        WHERE tipo_centro IS NULL OR codigo_region IS NULL
           OR codigo_ciudad IS NULL OR area_operativa IS NULL)

UNION ALL
SELECT 'semanas_contiguas', 'Todas las semanas entre la mínima y la máxima tienen datos',
       COUNT(*)
FROM dim_semana s ANTI JOIN fct_demanda f USING (semana)

-- Rangos ----------------------------------------------------------------------
UNION ALL
SELECT 'pedidos_positivos', 'num_orders > 0',
       COUNT(*) FROM fct_demanda WHERE pedidos <= 0

UNION ALL
SELECT 'precios_positivos', 'checkout_price y base_price > 0',
       COUNT(*) FROM fct_demanda WHERE precio_checkout <= 0 OR precio_base <= 0

UNION ALL
SELECT 'banderas_binarias', 'Las banderas de promoción solo valen 0 o 1',
       COUNT(*) FROM fct_demanda
WHERE promo_email NOT IN (0, 1) OR destacado_home NOT IN (0, 1)

UNION ALL
SELECT 'area_positiva', 'op_area > 0',
       COUNT(*) FROM dim_centro WHERE area_operativa <= 0

-- Conservación (staging → hechos) ---------------------------------------------
UNION ALL
SELECT 'conserva_filas', 'Los hechos tienen las mismas filas que el CSV original',
       ABS((SELECT COUNT(*) FROM stg_pedidos) - (SELECT COUNT(*) FROM fct_demanda))

UNION ALL
SELECT 'conserva_pedidos', 'La suma de pedidos no cambia entre el CSV y los hechos',
       ABS((SELECT SUM(num_orders) FROM stg_pedidos) - (SELECT SUM(pedidos) FROM fct_demanda))

UNION ALL
SELECT 'marts_cuadran_kpis', 'Los marts suman lo mismo que los KPI',
       (SELECT COUNT(*) FROM (
            SELECT (SELECT pedidos_totales FROM mart_kpis) AS total
        ) t
        WHERE total <> (SELECT SUM(pedidos) FROM mart_categorias)
           OR total <> (SELECT SUM(pedidos) FROM mart_centros)
           OR total <> (SELECT SUM(pedidos) FROM mart_tipos_centro)
           OR total <> (SELECT SUM(pedidos) FROM mart_tendencia_semanal)
           OR total <> (SELECT SUM(pedidos) FROM mart_comidas_abc));
