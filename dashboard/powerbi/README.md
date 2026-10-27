# Dashboard en Power BI

Informe de cinco páginas guardado como proyecto **PBIP**
([`dashboard_demanda.pbip`](dashboard_demanda.pbip)): el diseño del informe y el modelo
semántico están en texto (`dashboard_demanda.Report/`, `dashboard_demanda.SemanticModel/`), sin
datos ni caché. Vista previa en [PDF](../../docs/dashboard_demanda.pdf).

## Modelo

| Tabla | Origen | Rol |
|---|---|---|
| `fct_demanda` | `exportes/estrella/fct_demanda.parquet` | Hechos: una fila por semana × centro × comida |
| `dim_comida`, `dim_centro`, `dim_semana` | `exportes/estrella/*.parquet` | Dimensiones (relación varios a uno, filtro único) |
| `mart_*`, `calidad_resultados` | `exportes/marts_parquet/`, `exportes/marts/` | Resultados del SQL para ABC, cohortes, deciles, elasticidad y validación (sin relaciones) |

Las medidas están en [`medidas.dax`](medidas.dax) y en la tabla `_Medidas` del modelo:

| Medida | Qué calcula |
|---|---|
| `Pedidos`, `Filas`, `Ingreso estimado` | Suma de pedidos, número de filas, pedidos × precio de checkout |
| `Precio promedio ponderado` | Ingreso ÷ pedidos: precio por pedido (267,01) |
| `Precio promedio fila` | Promedio simple de `precio_checkout` (332,24, la cifra del estudio) |
| `Pedidos por fila`, `Centros activos`, `Comidas activas` | Promedio por fila y conteos distintos |
| `Media móvil 4 semanas` | Promedio de la semana y las 3 anteriores; en blanco si falta alguna (semanas relativas, sin fechas) |
| `Participación pedidos` | Parte del total visible, con `ALLSELECTED` |
| `Ranking categoría`, `Ranking centro` | `RANKX` sobre lo seleccionado; el de centros es global aunque la tabla muestre el tipo |
| `Tasa de retención` | Pares activos ÷ pares observables (cohortes) |
| `Control pedidos totales`, `Control filas` | "OK" si el modelo reproduce los totales del estudio |

## Validación

La página 5 compara el modelo con el SQL: pedidos (119 557 485), filas (456 548) y precio promedio
por fila (332,24) coinciden por los dos caminos, y las 17 reglas de calidad están en 0.

## Abrirlo

Requiere Power BI Desktop (Windows). Primero genera los datos con `python -m pipeline.build`.
El modelo guarda rutas absolutas a la carpeta `exportes/` del equipo donde se creó: en otro
equipo, cámbialas en *Transformar datos → Configuración de origen de datos → Cambiar origen*.
