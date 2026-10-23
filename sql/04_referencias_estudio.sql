-- =============================================================================
-- 04_referencias_estudio.sql
-- Carga dos tablas publicadas por el estudio de elasticidad v3.3.0
-- (https://github.com/s7ex-j/demanda-delivery-v2, DOI 10.5281/zenodo.23585772).
-- Este repositorio NO vuelve a estimar modelos: solo muestra sus resultados.
-- La ruta de la carpeta llega como variable: SET VARIABLE ref_dir = '...'.
-- =============================================================================

-- Pregunta: ¿cómo varía la elasticidad estimada según el nivel de precio?
-- Curva RCS (splines cúbicos restringidos, nudos P5/P35/P65/P95) con
-- controles. Es una elasticidad puntual descriptiva, no un efecto causal ni
-- una recomendación de precio. Las bandas bootstrap están en el informe.
CREATE OR REPLACE TABLE mart_elasticidad_rcs AS
SELECT
    precio,
    elasticidad_rcs,
    especificacion,
    nota
FROM read_csv(getvariable('ref_dir') || '/elasticidad_rcs_por_precio.csv', header = true);

-- Pregunta: ¿cómo cambia la asociación precio-demanda entre categorías?
-- OLS log-log con interacción precio × categoría y controles.
CREATE OR REPLACE TABLE mart_elasticidad_categoria AS
SELECT
    category AS categoria,
    elasticidad,
    especificacion,
    nota
FROM read_csv(getvariable('ref_dir') || '/elasticidad_por_categoria_detallada.csv', header = true);
