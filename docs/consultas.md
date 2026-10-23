# Consultas de negocio

Cada mart de [`sql/03_marts.sql`](../sql/03_marts.sql) responde una pregunta. Esta página resume
qué pregunta es, cómo se calcula y qué **no** dice. Las cifras de ejemplo vienen del estudio
v3.3.0 con los datos completos.

Convenciones: *fila* = semana × centro × comida; *pedidos* = suma de `num_orders`;
*ingreso estimado* = pedidos × precio de checkout, en unidades monetarias anónimas.

| Mart | Pregunta | Técnica SQL | Cuidado al leerlo |
|---|---|---|---|
| `mart_kpis` | ¿Qué tamaño tiene el negocio en el periodo? | Agregados | 119 557 485 pedidos en 456 548 filas, 145 semanas, 77 centros, 51 comidas |
| `mart_tendencia_semanal` | ¿Cómo evoluciona la demanda semana a semana y frente a hace 52 semanas? | CTE, `LAG`, media móvil con marco `ROWS`, acumulado con `PARTITION BY` | Parte de `dim_semana` para que un hueco no haga que `LAG` compare semanas no consecutivas |
| `mart_categorias` | ¿Qué categorías concentran la demanda y a qué precio? | `SUM() OVER ()`, `RANK` | La participación es sobre pedidos, no sobre filas |
| `mart_comidas_abc` | ¿Qué comidas sostienen el negocio? | Suma acumulada, `ROW_NUMBER`, `DENSE_RANK` por categoría | Regla ABC: A si lo acumulado *antes* de la comida es < 80 %; B si es < 95 % |
| `mart_promociones_matriz` | ¿Cuántos pedidos tiene una fila según la promoción? | Agregado 2 × 2 | Comparación cruda: mezcla centros y comidas distintas |
| `mart_promociones_indice` | Con promoción, ¿cuánto vende una comida en un centro frente a ella misma sin promoción? | `AVG(CASE …) OVER (PARTITION BY centro, comida)` | Descriptivo: las semanas con promoción también cambian de precio y de temporada |
| `mart_centros` | ¿Qué centros venden más, en total y dentro de su tipo? | `RANK` global y por partición, `NTILE(4)` | `pedidos_por_unidad_area` usa `op_area`, una medida anónima del dataset |
| `mart_tipos_centro` | ¿Cómo se comparan los tipos de centro? | Agregado + ventana sobre agregado | TYPE_A tiene 43 de los 77 centros |
| `mart_cohortes` | Cuando un centro empieza a vender una comida, ¿la sigue vendiendo? | `MIN` por par, generación de periodos con `range`, `LEFT JOIN` | Solo cuenta bloques de 13 semanas observados completos (control de censura) |
| `mart_bandas_precio` | ¿Cómo cambia el volumen según el nivel de precio? | `NTILE(10)`, `UNION ALL`, desempate por `id` | Bivariado, sin controles. No es una elasticidad |
| `mart_elasticidad_rcs` | ¿Cómo varía la elasticidad según el precio? | Lectura del resultado publicado | Tomado del estudio; elasticidad puntual descriptiva |
| `mart_elasticidad_categoria` | ¿Cómo cambia la asociación precio-demanda entre categorías? | Lectura del resultado publicado | Tomado del estudio; asociación observacional |

## Por qué `n_filas` y no "pedidos"

Cada fila del dataset es el registro de una comida en un centro durante una semana, con su
número de pedidos (`num_orders`). Contar filas dice cuántas combinaciones hubo, no cuántos
pedidos. Todas las tablas llevan las dos cosas por separado.

## Por qué el dashboard no da recomendaciones de precio

El estudio estimó varias elasticidades (OLS log-log −0,759; panel con efectos fijos −1,5985;
IV 2SLS −0,841; curva RCS de +0,04 a −1,51) y muestra que **no es constante**. Cada una mide
algo distinto, y ninguna permite afirmar qué pasaría al mover un precio. Juntarlas en una regla de
precios no está respaldado. Por eso la página de precio muestra la curva como descriptiva y
enlaza al informe.

## Reglas de calidad

[`sql/05_calidad.sql`](../sql/05_calidad.sql) define 17 reglas: unicidad, integridad referencial,
nulos, rangos, semanas contiguas, conservación de filas y pedidos entre el CSV y los hechos, y
cuadre de los marts con los KPI. El pipeline se detiene si alguna falla. Los tests comprueban que
cada regla **detecta** el error para el que existe (se inyecta el error y se verifica el conteo).
