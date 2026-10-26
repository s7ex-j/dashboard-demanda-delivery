# Dashboard en Power BI

Versión principal del dashboard. Usa el **modelo estrella** exportado por el pipeline y las medidas
de [`medidas.dax`](medidas.dax). Los marts del SQL sirven aquí para dos cosas: alimentar las
páginas cuya lógica conviene dejar en SQL (ABC, cohortes, deciles, elasticidad) y **validar** que
las medidas DAX dan lo mismo que el SQL.

> **Rutas de los datos.** El modelo guarda rutas absolutas a `exportes/estrella/` y
> `exportes/marts_parquet/` (y, para `mart_kpis` y `calidad_resultados`, a `exportes/marts/`).
> Tras clonar el repositorio y correr `python -m pipeline.build`, cámbialas en *Transformar
> datos → Configuración de origen de datos → Cambiar origen*. Mejora pendiente: un parámetro
> `CarpetaExportes` en Power Query para cambiarlas en un solo lugar.

Se construye en Power BI Desktop (Windows, gratis). El archivo `.pbix` se guarda en esta carpeta.

## 1. Preparar los datos

```
python -m pipeline.build
```

Genera `exportes/estrella/*.parquet` (modelo) y `exportes/marts/*.csv` (marts y calidad).

## 2. Cargar el modelo

*Obtener datos → Parquet* para cada archivo de `exportes/estrella/`:
`fct_demanda`, `dim_comida`, `dim_centro`, `dim_semana`.

Los marts también se cargan en **Parquet**, desde `exportes/marts_parquet/` (*Obtener datos → Parquet*).
No uses los CSV de `exportes/marts/` en Power BI: son para Looker Studio, y con la configuración
regional en español Power BI lee `0.1996` como `1996`.

| Mart | Para qué |
|---|---|
| `mart_comidas_abc` | Página Comparar: clasificación ABC |
| `mart_promociones_indice` | Página Diagnosticar: índice controlado por par centro × comida |
| `mart_cohortes` | Página Diagnosticar: cohortes |
| `mart_bandas_precio` | Página Diagnosticar: deciles de precio |
| `mart_elasticidad_rcs`, `mart_elasticidad_categoria` | Página Diagnosticar (resultados del estudio) |
| `mart_kpis`, `calidad_resultados` | Página Validación |

El detalle de cada visual (campos, agregación, posición y formato) está en
[`fondos/POSICIONES.md`](fondos/POSICIONES.md).

## 3. Relaciones

En *Vista de modelo*, todas de varios a uno (*), dirección de filtro **única**:

| Desde (hechos) | Hacia (dimensión) |
|---|---|
| `fct_demanda[meal_id]` | `dim_comida[meal_id]` |
| `fct_demanda[center_id]` | `dim_centro[center_id]` |
| `fct_demanda[semana]` | `dim_semana[semana]` |

Los marts quedan **sin relaciones**: ya vienen agregados y no deben filtrarse con las dimensiones.

Ajustes recomendados:

- Ocultar en la vista de informe las columnas clave de `fct_demanda` (`meal_id`, `center_id`,
  `semana`) para que se use siempre la de la dimensión.
- `dim_semana[etiqueta_trimestre]` → *Ordenar por columna* → `semana`.
- `dim_centro[center_id]`, `codigo_region` y `codigo_ciudad`: *Resumir por → No resumir*.
- No marcar `dim_semana` como tabla de fechas: no hay fechas reales (ver nota en `medidas.dax`).

## 4. Medidas

1. *Inicio → Escribir datos* → tabla vacía llamada `_Medidas`.
2. Crea cada medida de [`medidas.dax`](medidas.dax) en esa tabla (*Nueva medida* y pegar).
3. Formatos: `Pedidos`, `Filas`, `Pedidos semana anterior`, `Pedidos hace 52 semanas` y
   `Pedidos acumulados año` → número entero con separador de miles. Las que terminan en `%` y
   `Participación pedidos` → porcentaje con 1 decimal. Precios e ingreso → 2 decimales.

| Medida | Qué calcula | Detalle que importa |
|---|---|---|
| `Pedidos por fila` | Pedidos promedio por fila semana × centro × comida | Una fila no es un pedido: es el registro de una comida en un centro una semana |
| `Precio promedio ponderado` | Ingreso / pedidos | Distinto del promedio simple por fila: pesa más lo que más se vende |
| `Participación pedidos` | Parte del total visible | `ALLSELECTED` respeta los filtros de la página |
| `Ranking categoría` / `centro` | Posición por pedidos | `HASONEVALUE` evita un ranking sin sentido en la fila de total |
| `Pedidos semana anterior`, `hace 52 semanas` | Desplazamiento manual de semana | Sin fechas no sirven las funciones de inteligencia de tiempo |
| `Media móvil 4 semanas` | Promedio de la semana y las 3 anteriores | En blanco si alguna de las 4 no tiene datos |
| `Pedidos acumulados año` | Suma dentro del año relativo | Se reinicia en las semanas 53 y 105 |
| `Ratio promo vs sin promo` | Pedidos por fila con promo ÷ sin promo | Comparación cruda; la controlada está en `mart_promociones_indice` |
| `Control …` | "OK" si el total coincide con el estudio | Página de validación |

## 5. Páginas

Tema: *Vista → Temas → Buscar temas* → [`tema_charcoal_demanda.json`](tema_charcoal_demanda.json). Fondos de página y posiciones de cada visual: [`fondos/GUIA_FONDOS.md`](fondos/GUIA_FONDOS.md).

**1. Resumen ejecutivo**
- Tarjetas: `Pedidos`, `Ingreso estimado`, `Precio promedio ponderado`, `Centros activos`,
  `Comidas activas`.
- Líneas: eje `dim_semana[semana]`; valores `Pedidos` y `Media móvil 4 semanas`.
- Barras horizontales: `dim_comida[categoria]` × `Pedidos`, ordenadas de mayor a menor.
- Segmentadores: `dim_centro[tipo_centro]`, `dim_comida[cocina]`.

**2. Categorías y promociones**
- Matriz: filas `dim_comida[categoria]`; valores `Pedidos`, `Participación pedidos`,
  `Ranking categoría`, `Precio promedio ponderado`.
- Columnas agrupadas: eje `fct_demanda[tipo_promocion]`, valor `Pedidos por fila`.
- Tabla desde `mart_promociones_indice`: `categoria`, `tipo_promocion`, `indice_vs_sin_promo`,
  `n_filas`. Cuadro de texto: *"Índice 2,0 = el doble de pedidos que el mismo centro y comida sin
  promoción. Descriptivo: las semanas con promoción también cambian de precio."*
- Tabla desde `mart_comidas_abc` con formato condicional por `clase_abc`; o gráfico combinado
  (barras `pedidos`, línea `participacion_acumulada`) para el Pareto.

**3. Centros**
- Tabla: `dim_centro[center_id]`, `tipo_centro`, `codigo_region`, `Pedidos`, `Ranking centro`,
  `Participación pedidos`.
- Dispersión: eje X `dim_centro[area_operativa]` (*No resumir*), eje Y `Pedidos`, detalles
  `center_id`, leyenda `tipo_centro`.
- Columnas: `tipo_centro` × `Pedidos por fila`.

**4. Tendencia semanal**
- Columnas: `semana` × `Var semanal %` (formato condicional: verde positivo, rojo negativo).
- Líneas: `dim_semana[semana_del_anio]` en el eje, `dim_semana[anio_relativo]` en la leyenda,
  `Pedidos` como valor. Superpone los años relativos para comparar estacionalidad.
- Tarjeta con `Var interanual %` filtrada a la última semana.

**5. Cohortes**
- Matriz desde `mart_cohortes`: filas `cohorte_trimestre`, columnas `periodo_desde_inicio`,
  valor `tasa_retencion` (*No resumir*, porcentaje). Formato condicional → escala de colores.
- Nota: *"Periodo = bloques de 13 semanas desde la primera venta del par centro × comida. Solo se
  cuentan bloques observados completos."*

**6. Precio y elasticidad**
- Líneas desde `mart_bandas_precio`, filtro `categoria = "Todas"`: eje `decil_precio`, valor
  `pedidos_promedio_fila`.
- Líneas desde `mart_elasticidad_rcs`: eje `precio`, valor `elasticidad_rcs`; línea de
  referencia constante en −1.
- Barras desde `mart_elasticidad_categoria`: `categoria` × `elasticidad`.
- Cuadro de texto obligatorio: *"Elasticidades estimadas con datos observacionales en el estudio
  [DOI 10.5281/zenodo.23586040]. Son descriptivas: no son efectos causales ni recomendaciones de
  precio. Elasticidad promedio del modelo principal: −0,76 (IC 95 % [−0,843; −0,675])."*

**7. Validación** (se puede ocultar en la versión publicada)
- Tarjetas: `Control pedidos totales`, `Control filas`.
- Tabla `calidad_resultados` completa (17 reglas, todas en 0).
- Tabla con `mart_kpis[pedidos_totales]` al lado de la tarjeta `Pedidos` sin filtros: deben ser
  iguales.

## 6. Validar DAX contra SQL

Antes de publicar capturas, comprueba con evidencia que las medidas coinciden con el SQL:

| Vista en Power BI | Debe coincidir con |
|---|---|
| Tarjeta `Pedidos` sin filtros | `mart_kpis.pedidos_totales` = 119 557 485 |
| Tarjeta `Precio promedio fila` | `mart_kpis.precio_promedio_fila` ≈ 332,24 |
| Matriz por categoría: `Pedidos`, `Ranking categoría` | `mart_categorias.pedidos`, `ranking_pedidos` |
| Tabla por semana: `Var semanal %`, `Media móvil 4 semanas`, `Var interanual %` (semanas 1–5, 53, 145) | mismas columnas de `mart_tendencia_semanal` |
| Matriz por `tipo_promocion`: `Pedidos por fila` | `mart_promociones_matriz.pedidos_promedio_fila` |
| Tabla por centro: `Ranking centro` | `mart_centros.ranking_global` |

Si algo no coincide, casi siempre es una relación en dirección doble o un segmentador activo.

## 7. Entregables en el repositorio

- Proyecto **PBIP**: `dashboard_demanda.pbip` en esta carpeta (contiene `SemanticModel/` y
  `Report/`; la caché local `.pbi/` está en `.gitignore`).
- Capturas en `docs/capturas/` (JPG, 1600 px de ancho): una por página, con nombre
  `powerbi_01_describir.jpg`, `powerbi_02_comparar.jpg`, `powerbi_03_diagnosticar.jpg`,
  `powerbi_04_hallazgos.jpg`, `powerbi_05_validacion.jpg`.

**Publicar en la web.** *Publicar en la web* de Power BI Service necesita una cuenta profesional
o educativa con licencia y que la organización lo permita. Si tu correo de UPN o ISIL tiene
Power BI, se puede usar. Si no, el enlace público lo da la versión de Looker Studio.
