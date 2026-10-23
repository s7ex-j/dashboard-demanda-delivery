-- =============================================================================
-- 01_staging.sql
-- Carga los tres CSV originales de Kaggle con tipos explícitos.
-- La ruta de la carpeta raw llega como variable: SET VARIABLE raw_dir = '...'.
-- Fijar los tipos evita que DuckDB infiera mal una columna y falle en silencio.
-- =============================================================================

CREATE OR REPLACE TABLE stg_pedidos AS
SELECT *
FROM read_csv(
    getvariable('raw_dir') || '/train.csv',
    header = true,
    columns = {
        'id': 'BIGINT',
        'week': 'INTEGER',
        'center_id': 'INTEGER',
        'meal_id': 'INTEGER',
        'checkout_price': 'DOUBLE',
        'base_price': 'DOUBLE',
        'emailer_for_promotion': 'INTEGER',
        'homepage_featured': 'INTEGER',
        'num_orders': 'INTEGER'
    }
);

CREATE OR REPLACE TABLE stg_comidas AS
SELECT *
FROM read_csv(
    getvariable('raw_dir') || '/meal_info.csv',
    header = true,
    columns = {'meal_id': 'INTEGER', 'category': 'VARCHAR', 'cuisine': 'VARCHAR'}
);

CREATE OR REPLACE TABLE stg_centros AS
SELECT *
FROM read_csv(
    getvariable('raw_dir') || '/fulfilment_center_info.csv',
    header = true,
    columns = {
        'center_id': 'INTEGER',
        'city_code': 'INTEGER',
        'region_code': 'INTEGER',
        'center_type': 'VARCHAR',
        'op_area': 'DOUBLE'
    }
);
