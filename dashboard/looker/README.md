# Dashboard en Looker Studio

Versión pública ligera del dashboard: cualquiera la abre con un enlace, sin instalar nada.
**Solo usa los marts agregados** de `exportes/marts/`. Las filas del dataset original no se
suben a ningún lado.

Diferencia con Power BI: aquí la lógica analítica (variaciones, rankings, ABC, cohortes) ya viene
calculada en SQL. Looker Studio solo la muestra y filtra. En Power BI esa lógica se rehace en DAX
sobre el modelo estrella.

## 1. Preparar los datos

```
python -m pipeline.build
```

## 2. Subir los marts

En <https://lookerstudio.google.com>: *Crear → Fuente de datos → Subida de archivos* (conector
*File Upload*). Crea **una fuente por archivo**:

| Fuente | Archivo | Página |
|---|---|---|
| KPIs | `mart_kpis.csv` | Resumen |
| Tendencia | `mart_tendencia_semanal.csv` | Resumen, Tendencia |
| Categorías | `mart_categorias.csv` | Resumen, Categorías |
| Comidas ABC | `mart_comidas_abc.csv` | Categorías |
| Promociones | `mart_promociones_matriz.csv` | Categorías |
| Índice promociones | `mart_promociones_indice.csv` | Categorías |
| Centros | `mart_centros.csv` | Centros |
| Tipos de centro | `mart_tipos_centro.csv` | Centros |
| Cohortes | `mart_cohortes.csv` | Cohortes |
| Bandas de precio | `mart_bandas_precio.csv` | Precio |
| Elasticidad RCS | `mart_elasticidad_rcs.csv` | Precio |
| Elasticidad por categoría | `mart_elasticidad_categoria.csv` | Precio |

Al crear cada fuente, revisa los tipos:

- `semana`, `decil_precio`, `cohorte_trimestre`, `periodo_desde_inicio`, `center_id`, `meal_id`,
  `codigo_region`, `codigo_ciudad`, `ranking_*`, `cuartil` → **Número**, agregación **Ninguna**
  (son identificadores u órdenes, no se suman).
- `participacion*`, `var_*_pct`, `tasa_retencion`, `pct_filas_con_promo` → **Porcentaje**.
  Vienen como fracción (0,25 = 25 %), que es lo que espera Looker Studio.
- `ingreso_estimado`, `precio_*` → Número con 2 decimales. **No** usar el tipo Moneda: el dataset no
  indica moneda.

## 3. Campos calculados

Se crean en la fuente (*Añadir un campo*):

| Fuente | Campo | Fórmula |
|---|---|---|
| Tendencia | `Año relativo (texto)` | `CONCAT("Año ", CAST(anio_relativo AS TEXT))` |
| Tendencia | `Tendencia semanal` | `CASE WHEN var_semanal_pct >= 0 THEN "Sube" ELSE "Baja" END` |
| Comidas ABC | `Comida` | `CONCAT(categoria, " · ", CAST(meal_id AS TEXT))` |
| Centros | `Centro` | `CONCAT("Centro ", CAST(center_id AS TEXT))` |

## 4. Páginas

Tema: *Tema y diseño → Personalizar*, colores `#2563A8`, `#E07B39`, `#3A9D74`, `#8C5BB5`
(iguales al tema de Power BI).

**1. Resumen**
- Cuadros de resultados desde *KPIs*: `pedidos_totales`, `ingreso_estimado`,
  `precio_promedio_ponderado`, `n_centros`, `n_comidas`.
- Serie temporal (gráfico de líneas) desde *Tendencia*: dimensión `semana`; métricas `pedidos` y
  `media_movil_4s`.
- Barras desde *Categorías*: `categoria` × `pedidos`, orden descendente.

**2. Categorías y promociones**
- Tabla desde *Categorías*: `categoria`, `pedidos`, `participacion_pedidos`, `ranking_pedidos`,
  `precio_promedio`.
- Gráfico combinado desde *Comidas ABC*: dimensión `Comida` ordenada por `ranking_global`; barras
  `pedidos`, línea `participacion_acumulada` en el eje derecho. Control de filtro por `clase_abc`.
- Barras desde *Promociones*: `tipo_promocion` × `pedidos_promedio_fila`.
- Tabla con mapa de calor desde *Índice promociones*: filas `categoria`, columnas
  `tipo_promocion`, métrica `indice_vs_sin_promo`. Con el mismo texto aclaratorio que en Power BI.

**3. Centros**
- Tabla desde *Centros*: `Centro`, `tipo_centro`, `codigo_region`, `pedidos`, `ranking_global`,
  `ranking_en_tipo`, `cuartil`. Controles de filtro: `tipo_centro`, `cuartil`.
- Dispersión desde *Centros*: `area_operativa` × `pedidos`, dimensión `Centro`.
- Barras desde *Tipos de centro*: `tipo_centro` × `pedidos_promedio_fila`.

**4. Tendencia semanal**
- Barras desde *Tendencia*: `semana` × `var_semanal_pct`, color por `Tendencia semanal`.
- Líneas desde *Tendencia*: dimensión `semana_del_anio`, desglose `Año relativo (texto)`,
  métrica `pedidos`.
- Líneas: `semana` × `var_interanual_pct` (solo desde la semana 53).

**5. Cohortes**
- Tabla dinámica desde *Cohortes*: filas `cohorte_trimestre`, columnas `periodo_desde_inicio`,
  métrica `tasa_retencion` con mapa de calor.

**6. Precio y elasticidad**
- Líneas desde *Bandas de precio*, con control de filtro por `categoria` (valor inicial
  `Todas`): `decil_precio` × `pedidos_promedio_fila`.
- Líneas desde *Elasticidad RCS*: `precio` × `elasticidad_rcs`.
- Barras desde *Elasticidad por categoría*: `categoria` × `elasticidad`.
- Texto obligatorio (el mismo de Power BI): elasticidades descriptivas, enlace al estudio y sus
  DOI, elasticidad promedio −0,76.

En el pie de todas las páginas: *"Datos: Food Demand Forecasting (Genpact / Analytics Vidhya,
Kaggle). Unidades monetarias anónimas. Una fila = semana × centro × comida."*

## 5. Publicar

*Compartir → Gestionar el acceso → Cualquier usuario de Internet puede ver*. Antes, en
*Archivo → Configuración del informe*, desactiva *Permitir que los lectores descarguen datos* si
no quieres que se bajen los CSV.

Copia el enlace en el README principal (sección *Dashboards*) y toma capturas con el mismo nombre
que las de Power BI pero con prefijo `looker_`.

## Actualizar

Si cambia el SQL: vuelve a correr el pipeline y, en cada fuente, *Editar conexión → Reemplazar
archivo*. Los gráficos se conservan mientras los nombres de las columnas no cambien.
