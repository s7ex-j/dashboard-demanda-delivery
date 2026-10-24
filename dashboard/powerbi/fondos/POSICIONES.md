# Visuales: posición, campos y formato

Página **1920 × 1080**. Posición y tamaño se escriben en *Formato del visual → General → Propiedades* (Tamaño: Alto, Ancho · Posición: Horizontal = X, Vertical = Y).

## Reglas que evitan los errores más comunes

1. **Medida o columna.** Lo que dice *Medida* se arrastra desde la tabla `_Medidas` (ícono de calculadora) y ya viene calculado: no tiene agregación. Lo que dice *Columna* se arrastra desde su tabla y se le pone la agregación indicada (flecha del campo en el pozo).
2. **Nunca promedies una columna para sacar un KPI.** Ejemplo: el precio ponderado no es `Promedio de precio_checkout` ni `Promedio de ingreso_estimado`: es la medida **Precio promedio ponderado** = ingreso ÷ pedidos. Los números con *E* (notación científica) aparecen justo cuando se agrega una columna que no corresponde.
3. **Identificadores sin resumir.** Antes de empezar, en *Vista de modelo* selecciona cada columna de esta lista → *Propiedades → Resumir por: **Ninguno***:

   - dim_semana: semana, anio_relativo, semana_del_anio, trimestre_del_anio, bloque_4_semanas
   - dim_centro: center_id, codigo_ciudad, codigo_region
   - dim_comida: meal_id
   - fct_demanda: id, semana, center_id, meal_id, promo_email, destacado_home
   - mart_comidas_abc: meal_id, ranking_global, ranking_en_categoria
   - mart_cohortes: cohorte_trimestre, periodo_desde_inicio
   - mart_bandas_precio: decil_precio
   - mart_elasticidad_rcs: precio

4. **Los marts se cargan en Parquet, no en CSV.** *Obtener datos → Más… → Parquet* y la ruta completa del archivo en `exportes\marts_parquet\`. El Parquet guarda los tipos (decimal, entero, texto), así que no depende de la coma o el punto decimal de Windows. Los CSV de `exportes\marts\` son para Looker Studio. Si ya cargaste un mart desde CSV, bórralo (clic derecho → *Eliminar del modelo*) y cárgalo de nuevo desde Parquet con el mismo nombre.
5. **Formato de una medida:** selecciónala en el panel *Datos* → pestaña *Herramientas de medidas* → *Formato*. Se hace una vez y vale para todos los visuales.
6. **Navegador de páginas** (todas las páginas): *Insertar → Botones → Navegador → Navegador de páginas* · **X 1180 · Y 40 · Ancho 700 · Alto 44**.

## Página 1. Describir

Fondo: `fondo_1_describir.png`

**Antes: crea estas medidas** (clic derecho en `_Medidas` → *Nueva medida*, una por vez):

```
Ingreso estimado = SUM ( fct_demanda[ingreso_estimado] )
```
Formato: Número entero, unidades automáticas.

```
Precio promedio ponderado = DIVIDE ( [Ingreso estimado], [Pedidos] )
```
Formato: Decimal, 2 decimales.

```
Pedidos por fila = DIVIDE ( [Pedidos], [Filas] )
```
Formato: Decimal, 0 decimales.

```
Centros activos = DISTINCTCOUNT ( fct_demanda[center_id] )
```
Formato: Número entero.

```
Comidas activas = DISTINCTCOUNT ( fct_demanda[meal_id] )
```
Formato: Número entero.

```
Media móvil 4 semanas =
VAR s = SELECTEDVALUE ( dim_semana[semana] )
VAR ventana =
    CALCULATETABLE (
        VALUES ( dim_semana[semana] ),
        REMOVEFILTERS ( dim_semana ),
        dim_semana[semana] > s - 4,
        dim_semana[semana] <= s
    )
VAR semanasConDatos =
    CALCULATE ( DISTINCTCOUNT ( fct_demanda[semana] ), REMOVEFILTERS ( dim_semana ), ventana )
RETURN
    IF (
        NOT ISBLANK ( s ) && semanasConDatos = 4,
        CALCULATE ( [Pedidos], REMOVEFILTERS ( dim_semana ), ventana ) / 4
    )
```
Formato: Número entero, separador de miles.

#### Segmentador 1

**Visual:** Segmentación de datos  ·  **X** 152 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_centro[tipo_centro]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Tipo de centro", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Segmentador 2

**Visual:** Segmentación de datos  ·  **X** 730 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_comida[cocina]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Cocina", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Segmentador 3

**Visual:** Segmentación de datos  ·  **X** 1308 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_comida[categoria]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Categoría", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Tarjeta · Pedidos

**Visual:** Tarjeta  ·  **X** 48 · **Y** 192 · **Ancho** 339 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |

- Doble clic en el campo del pozo → renombrar a "Pedidos totales" (es la etiqueta pequeña)
- Valor: unidades de visualización **Automático**

#### Tarjeta · Ingreso estimado

**Visual:** Tarjeta  ·  **X** 419 · **Y** 192 · **Ancho** 339 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Ingreso estimado** (tabla `_Medidas`) | — (es medida) |

- Doble clic en el campo del pozo → renombrar a "Ingreso estimado" (es la etiqueta pequeña)
- Valor: unidades de visualización **Automático**

#### Tarjeta · Precio promedio ponderado

**Visual:** Tarjeta  ·  **X** 790 · **Y** 192 · **Ancho** 339 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Precio promedio ponderado** (tabla `_Medidas`) | — (es medida) |

- Doble clic en el campo del pozo → renombrar a "Precio ponderado" (es la etiqueta pequeña)
- Valor: unidades de visualización **Automático**

#### Tarjeta · Centros activos

**Visual:** Tarjeta  ·  **X** 1161 · **Y** 192 · **Ancho** 339 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Centros activos** (tabla `_Medidas`) | — (es medida) |

- Doble clic en el campo del pozo → renombrar a "Centros" (es la etiqueta pequeña)
- Valor: unidades de visualización **Automático**

#### Tarjeta · Comidas activas

**Visual:** Tarjeta  ·  **X** 1532 · **Y** 192 · **Ancho** 340 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Comidas activas** (tabla `_Medidas`) | — (es medida) |

- Doble clic en el campo del pozo → renombrar a "Comidas" (es la etiqueta pequeña)
- Valor: unidades de visualización **Automático**

#### Pedidos por semana

**Visual:** Gráfico de líneas  ·  **X** 52 · **Y** 382 · **Ancho** 1192 · **Alto** 318

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `dim_semana[semana]` | No resumir |
| Eje Y | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Eje Y | Medida **Media móvil 4 semanas** (tabla `_Medidas`) | — (es medida) |

- Eje X → Tipo: **Continuo**; título del eje: desactivado
- Eje Y → título desactivado; unidades de visualización **Miles**
- Líneas: `Pedidos` gris claro (#A6A6A6), `Media móvil 4 semanas` azul (#3599B8), 2 px
- Leyenda: arriba a la izquierda

#### Pedidos por categoría

**Visual:** Gráfico de barras agrupadas  ·  **X** 1284 · **Y** 382 · **Ancho** 584 · **Alto** 318

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje Y | Columna `dim_comida[categoria]` | — |
| Eje X | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |

- Ordenar: *…* (más opciones) → Ordenar eje → **Pedidos**, **Descendente**
- Etiquetas de datos: activadas, unidades **Millones**, 1 decimal
- Eje X: desactivado (las etiquetas ya dan el valor)

#### Pedidos por fila según tipo de centro

**Visual:** Gráfico de columnas agrupadas  ·  **X** 52 · **Y** 798 · **Ancho** 579 · **Alto** 214

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `dim_centro[tipo_centro]` | — |
| Eje Y | Medida **Pedidos por fila** (tabla `_Medidas`) | — (es medida) |

- Etiquetas de datos activadas, 0 decimales
- Eje Y desactivado

#### Pedidos por fila según promoción

**Visual:** Gráfico de columnas agrupadas  ·  **X** 671 · **Y** 798 · **Ancho** 579 · **Alto** 214

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `fct_demanda[tipo_promocion]` | — |
| Eje Y | Medida **Pedidos por fila** (tabla `_Medidas`) | — (es medida) |

- Ordenar eje → **Pedidos por fila**, **Ascendente** (de Sin promoción a Email + home)
- Etiquetas de datos activadas, 0 decimales
- Eje Y desactivado

#### Cómo leer esta página

**Visual:** Cuadro de texto  ·  **X** 1290 · **Y** 798 · **Ancho** 578 · **Alto** 214

- Insertar → Cuadro de texto; texto de GUIA_FONDOS.md (Página 1 · Cómo leer esta página)
- Segoe UI 12, color #333333, sin fondo

## Página 2. Comparar

Fondo: `fondo_2_comparar.png`

**Antes: crea estas medidas** (clic derecho en `_Medidas` → *Nueva medida*, una por vez):

```
Participación pedidos =
DIVIDE (
    [Pedidos],
    CALCULATE ( [Pedidos], ALLSELECTED ( dim_comida ), ALLSELECTED ( dim_centro ) )
)
```
Formato: Porcentaje, 1 decimal.

```
Ranking categoría =
IF (
    HASONEVALUE ( dim_comida[categoria] ),
    RANKX ( ALLSELECTED ( dim_comida[categoria] ), [Pedidos], , DESC, DENSE )
)
```
Formato: Número entero.

```
Ranking centro =
IF (
    HASONEVALUE ( dim_centro[center_id] ),
    RANKX ( ALLSELECTED ( dim_centro[center_id] ), [Pedidos], , DESC, SKIP )
)
```
Formato: Número entero.

**Antes: carga estos Parquet** (*Obtener datos → Más… → Parquet*, desde `exportes\marts_parquet\`). Después, en *Vista de modelo*, borra cualquier relación que Power BI cree con ellos:

- `mart_comidas_abc.parquet`

#### Segmentador 1

**Visual:** Segmentación de datos  ·  **X** 152 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_centro[tipo_centro]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Tipo de centro", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Segmentador 2

**Visual:** Segmentación de datos  ·  **X** 730 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_comida[cocina]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Cocina", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Segmentador 3

**Visual:** Segmentación de datos  ·  **X** 1308 · **Y** 112 · **Ancho** 562 · **Alto** 48

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campo | Columna `dim_comida[categoria]` | — |

- Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**
- Selección: activar *Opción "Seleccionar todo"* y *Selección múltiple con Ctrl*
- Encabezado de segmentación: activado, texto "Categoría", tamaño 10, color #595959
- Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo

#### Categorías

**Visual:** Matriz  ·  **X** 52 · **Y** 254 · **Ancho** 888 · **Alto** 334

| Pozo | Arrastra | Agregación |
|---|---|---|
| Filas | Columna `dim_comida[categoria]` | — |
| Valores | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Valores | Medida **Participación pedidos** (tabla `_Medidas`) | — (es medida) |
| Valores | Medida **Ranking categoría** (tabla `_Medidas`) | — (es medida) |
| Valores | Medida **Precio promedio ponderado** (tabla `_Medidas`) | — (es medida) |

- Ordenar por **Pedidos**, descendente (clic en el encabezado de la columna)
- Formato condicional → `Participación pedidos` → **Barras de datos** (color #3599B8)
- Renombrar en el pozo: "Participación", "Ranking", "Precio ponderado"

#### Clasificación ABC de comidas

**Visual:** Gráfico de líneas y columnas apiladas  ·  **X** 980 · **Y** 254 · **Ancho** 888 · **Alto** 334

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `mart_comidas_abc[ranking_global]` | No resumir |
| Eje Y de columna | Columna `mart_comidas_abc[pedidos]` | Suma |
| Leyenda de columna | Columna `mart_comidas_abc[clase_abc]` | — |
| Eje Y de línea | Columna `mart_comidas_abc[participacion_acumulada]` | Suma |
| Información sobre herramientas | Columna `mart_comidas_abc[meal_id]` | No resumir |
| Información sobre herramientas | Columna `mart_comidas_abc[categoria]` | — |

- Antes de armarlo, comprueba en *Vista de tabla* que `participacion_acumulada` va de 0 a 1 (0,1996 … 1)
- Eje X = puesto de la comida (1 = la que más vende), así las barras ya salen ordenadas. Eje X → Tipo: **Categórico**; título "Comidas ordenadas por pedidos"
- Colores de leyenda: A #404040, B #A6A6A6, C #DCDCDC
- Línea: interpolación **Lineal** (no suavizada), color #3599B8, 2 px
- Eje Y secundario (línea): formato **Porcentaje**, mínimo 0, máximo 1
- Analítica (lupa) → Línea constante en el eje Y secundario: 0,8, discontinua, etiqueta "80 %"

#### Pedidos por semana del año

**Visual:** Gráfico de líneas  ·  **X** 52 · **Y** 686 · **Ancho** 880 · **Alto** 326

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `dim_semana[semana_del_anio]` | No resumir |
| Eje Y | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Leyenda | Columna `dim_semana[anio_relativo]` | — |

- Eje X → Tipo: **Continuo**
- Colores: año 1 #BFBFBF, año 2 #737373, año 3 #3599B8 (el año 3 solo tiene 41 semanas)

#### Área operativa y pedidos

**Visual:** Gráfico de dispersión  ·  **X** 972 · **Y** 686 · **Ancho** 428 · **Alto** 326

| Pozo | Arrastra | Agregación |
|---|---|---|
| Valores | Columna `dim_centro[center_id]` | No resumir |
| Eje X | Columna `dim_centro[area_operativa]` | Promedio |
| Eje Y | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Leyenda | Columna `dim_centro[tipo_centro]` | — |

- Marcadores tamaño 6
- Títulos de eje: activados ("Área operativa", "Pedidos")

#### Ranking de centros

**Visual:** Tabla  ·  **X** 1440 · **Y** 686 · **Ancho** 428 · **Alto** 326

| Pozo | Arrastra | Agregación |
|---|---|---|
| Columnas | Columna `dim_centro[center_id]` | No resumir |
| Columnas | Columna `dim_centro[tipo_centro]` | — |
| Columnas | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Columnas | Medida **Ranking centro** (tabla `_Medidas`) | — (es medida) |
| Columnas | Medida **Participación pedidos** (tabla `_Medidas`) | — (es medida) |

- Ordenar por **Pedidos**, descendente
- Totales: desactivados
- Renombrar: "Centro", "Tipo", "Ranking", "Participación"

## Página 3. Diagnosticar

Fondo: `fondo_3_diagnosticar.png`

**Antes: carga estos Parquet** (*Obtener datos → Más… → Parquet*, desde `exportes\marts_parquet\`). Después, en *Vista de modelo*, borra cualquier relación que Power BI cree con ellos:

- `mart_promociones_indice.parquet`
- `mart_cohortes.parquet`
- `mart_bandas_precio.parquet`
- `mart_elasticidad_rcs.parquet`
- `mart_elasticidad_categoria.parquet`

#### Promoción frente al mismo centro y comida sin promoción

**Visual:** Matriz  ·  **X** 52 · **Y** 246 · **Ancho** 888 · **Alto** 338

| Pozo | Arrastra | Agregación |
|---|---|---|
| Filas | Columna `mart_promociones_indice[categoria]` | — |
| Columnas | Columna `mart_promociones_indice[tipo_promocion]` | — |
| Valores | Columna `mart_promociones_indice[indice_vs_sin_promo]` | Promedio |

- En el panel Datos, selecciona `indice_vs_sin_promo` → Herramientas de columna → Formato decimal, **2** decimales
- Formato condicional → **Color de fondo** → Escala de colores: mínimo #FFFFFF, máximo #3599B8
- Subtotales de filas y columnas: desactivados (un promedio de índices no tiene sentido)

#### Permanencia de comidas en los centros

**Visual:** Matriz  ·  **X** 980 · **Y** 246 · **Ancho** 888 · **Alto** 338

| Pozo | Arrastra | Agregación |
|---|---|---|
| Filas | Columna `mart_cohortes[cohorte_trimestre]` | No resumir |
| Columnas | Columna `mart_cohortes[periodo_desde_inicio]` | No resumir |
| Valores | Columna `mart_cohortes[tasa_retencion]` | Promedio |

- En el panel Datos, selecciona `tasa_retencion` → Herramientas de columna → Formato **Porcentaje**, 0 decimales
- Formato condicional → Color de fondo → escala #FFFFFF → #3599B8
- Subtotales desactivados; tamaño de texto 10 si no cabe

#### Pedidos por decil de precio

**Visual:** Gráfico de líneas  ·  **X** 52 · **Y** 682 · **Ancho** 579 · **Alto** 330

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `mart_bandas_precio[decil_precio]` | No resumir |
| Eje Y | Columna `mart_bandas_precio[pedidos_promedio_fila]` | Promedio |

- Panel Filtros → *Filtros en este objeto visual* → `categoria` → solo **Todas**
- Eje X → Tipo: **Categórico**; marcadores activados

#### Elasticidad según el nivel de precio

**Visual:** Gráfico de líneas  ·  **X** 671 · **Y** 682 · **Ancho** 579 · **Alto** 330

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje X | Columna `mart_elasticidad_rcs[precio]` | No resumir |
| Eje Y | Columna `mart_elasticidad_rcs[elasticidad_rcs]` | Promedio |

- Eje X → Tipo: **Continuo**
- Analítica (ícono de lupa) → **Línea constante** → valor −1, color #FB8281, discontinua, etiqueta "Elasticidad = −1"
- Color de la línea #3599B8, marcadores activados

#### Elasticidad por categoría

**Visual:** Gráfico de barras agrupadas  ·  **X** 1290 · **Y** 682 · **Ancho** 578 · **Alto** 330

| Pozo | Arrastra | Agregación |
|---|---|---|
| Eje Y | Columna `mart_elasticidad_categoria[categoria]` | — |
| Eje X | Columna `mart_elasticidad_categoria[elasticidad]` | Promedio |

- Ordenar eje → **Promedio de elasticidad**, **Ascendente** (la más negativa arriba)
- Etiquetas de datos activadas, 2 decimales
- Color #404040

## Página 4. Hallazgos y límites

Fondo: `fondo_4_hallazgos.png`

#### Qué muestran los datos

**Visual:** Cuadro de texto  ·  **X** 52 · **Y** 174 · **Ancho** 579 · **Alto** 838

- Texto de GUIA_FONDOS.md (Página 4 · Qué muestran los datos), con viñetas
- Segoe UI 13, color #333333, interlineado cómodo

#### Qué no se puede concluir

**Visual:** Cuadro de texto  ·  **X** 671 · **Y** 174 · **Ancho** 579 · **Alto** 838

- Texto de GUIA_FONDOS.md (Página 4 · Qué no se puede concluir), con viñetas
- Segoe UI 13, color #333333, interlineado cómodo

#### Cómo se construyó

**Visual:** Cuadro de texto  ·  **X** 1290 · **Y** 174 · **Ancho** 578 · **Alto** 838

- Texto de GUIA_FONDOS.md (Página 4 · Cómo se construyó), con viñetas
- Segoe UI 13, color #333333, interlineado cómodo

## Página 5. Validación

Fondo: `fondo_5_validacion.png`

**Antes: carga estos Parquet** (*Obtener datos → Más… → Parquet*, desde `exportes\marts_parquet\`). Después, en *Vista de modelo*, borra cualquier relación que Power BI cree con ellos:

- `mart_kpis.parquet (ya cargado)`
- `calidad_resultados.parquet (ya cargado)`

#### Tarjeta · Control pedidos totales

**Visual:** Tarjeta  ·  **X** 48 · **Y** 112 · **Ancho** 432 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Control pedidos totales** (tabla `_Medidas`) | — (es medida) |

- Renombrar en el pozo: "Control: pedidos = 119 557 485"

#### Tarjeta · Control filas

**Visual:** Tarjeta  ·  **X** 512 · **Y** 112 · **Ancho** 432 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Control filas** (tabla `_Medidas`) | — (es medida) |

- Renombrar en el pozo: "Control: filas = 456 548"

#### Tarjeta · Pedidos

**Visual:** Tarjeta  ·  **X** 976 · **Y** 112 · **Ancho** 432 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |

- Renombrar en el pozo: "Pedidos (DAX)"

#### Tarjeta · Precio promedio fila

**Visual:** Tarjeta  ·  **X** 1440 · **Y** 112 · **Ancho** 432 · **Alto** 96

| Pozo | Arrastra | Agregación |
|---|---|---|
| Campos / Valor | Medida **Precio promedio fila** (tabla `_Medidas`) | — (es medida) |

- Renombrar en el pozo: "Precio promedio fila (DAX)"

#### Reglas de calidad de datos

**Visual:** Tabla  ·  **X** 52 · **Y** 302 · **Ancho** 888 · **Alto** 710

| Pozo | Arrastra | Agregación |
|---|---|---|
| Columnas | Columna `calidad_resultados[regla]` | — |
| Columnas | Columna `calidad_resultados[descripcion]` | — |
| Columnas | Columna `calidad_resultados[filas_con_error]` | Suma (cada regla es una fila) |

- Totales activados: el total de `filas_con_error` debe ser **0**
- Formato condicional en `filas_con_error`: color de fuente rojo #D70C0C si > 0

#### DAX frente a SQL · Tabla SQL

**Visual:** Tabla  ·  **X** 980 · **Y** 302 · **Ancho** 888 · **Alto** 120

| Pozo | Arrastra | Agregación |
|---|---|---|
| Columnas | Columna `mart_kpis[pedidos_totales]` | Suma |
| Columnas | Columna `mart_kpis[n_filas]` | Suma |
| Columnas | Columna `mart_kpis[precio_promedio_fila]` | Suma |

- Renombrar: "Pedidos (SQL)", "Filas (SQL)", "Precio promedio (SQL)"
- Totales desactivados

#### DAX frente a SQL · Tabla DAX

**Visual:** Tabla  ·  **X** 980 · **Y** 438 · **Ancho** 888 · **Alto** 120

| Pozo | Arrastra | Agregación |
|---|---|---|
| Columnas | Medida **Pedidos** (tabla `_Medidas`) | — (es medida) |
| Columnas | Medida **Filas** (tabla `_Medidas`) | — (es medida) |
| Columnas | Medida **Precio promedio fila** (tabla `_Medidas`) | — (es medida) |

- Renombrar: "Pedidos (DAX)", "Filas (DAX)", "Precio promedio (DAX)"
- Debe mostrar exactamente los mismos tres números que la tabla SQL

#### DAX frente a SQL · Nota

**Visual:** Cuadro de texto  ·  **X** 980 · **Y** 574 · **Ancho** 888 · **Alto** 120

- Texto: "Arriba, el total calculado en DuckDB (mart_kpis). Abajo, el mismo total con medidas DAX sobre el modelo estrella. Si coinciden, el modelo de Power BI está bien relacionado y sin filtros ocultos."
