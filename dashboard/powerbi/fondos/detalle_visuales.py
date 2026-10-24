"""
Qué lleva cada visual: tipo, pozos de campos, origen de cada campo y ajustes.
Lo usa generar_fondos.py para escribir POSICIONES.md.

Notación:
  M:Pedidos            -> medida de la tabla _Medidas (se crea con DAX; ver MEDIDAS)
  C:dim_semana[semana] -> columna de una tabla del modelo, con la agregación indicada
"""

# Medidas que hay que crear antes de cada página (además de las 5 que ya tienes:
# Pedidos, Filas, Precio promedio fila, Control pedidos totales, Control filas).
MEDIDAS = {
    "1": [
        ("Ingreso estimado", "SUM ( fct_demanda[ingreso_estimado] )", "Número entero, unidades automáticas"),
        ("Precio promedio ponderado", "DIVIDE ( [Ingreso estimado], [Pedidos] )", "Decimal, 2 decimales"),
        ("Pedidos por fila", "DIVIDE ( [Pedidos], [Filas] )", "Decimal, 0 decimales"),
        ("Centros activos", "DISTINCTCOUNT ( fct_demanda[center_id] )", "Número entero"),
        ("Comidas activas", "DISTINCTCOUNT ( fct_demanda[meal_id] )", "Número entero"),
        ("Media móvil 4 semanas", None, "Número entero, separador de miles"),
    ],
    "2": [
        ("Participación pedidos", None, "Porcentaje, 1 decimal"),
        ("Ranking categoría", None, "Número entero"),
        ("Ranking centro", None, "Número entero"),
    ],
}

# Columnas que deben quedar en "No resumir" (Vista de modelo -> columna -> Propiedades ->
# Resumir por: Ninguno). Si no, Power BI las suma como si fueran cantidades.
NO_RESUMIR = [
    "dim_semana: semana, anio_relativo, semana_del_anio, trimestre_del_anio, bloque_4_semanas",
    "dim_centro: center_id, codigo_ciudad, codigo_region",
    "dim_comida: meal_id",
    "fct_demanda: id, semana, center_id, meal_id, promo_email, destacado_home",
    "mart_comidas_abc: meal_id, ranking_global, ranking_en_categoria",
    "mart_cohortes: cohorte_trimestre, periodo_desde_inicio",
    "mart_bandas_precio: decil_precio",
    "mart_elasticidad_rcs: precio",
]

# Parquet de exportes\marts_parquet que hay que cargar para cada página
MARTS_POR_PAGINA = {
    "2": ["mart_comidas_abc.parquet"],
    "3": ["mart_promociones_indice.parquet", "mart_cohortes.parquet", "mart_bandas_precio.parquet",
          "mart_elasticidad_rcs.parquet", "mart_elasticidad_categoria.parquet"],
    "5": ["mart_kpis.parquet (ya cargado)", "calidad_resultados.parquet (ya cargado)"],
}

V = {}  # clave del panel -> detalle

# ---- Página 1 ---------------------------------------------------------------
for i, (campo, nombre) in enumerate([("C:dim_centro[tipo_centro]", "Tipo de centro"),
                                     ("C:dim_comida[cocina]", "Cocina"),
                                     ("C:dim_comida[categoria]", "Categoría")]):
    V[f"seg{i + 1}"] = dict(
        tipo="Segmentación de datos",
        pozos=[("Campo", campo, "")],
        ajustes=["Formato → Configuración de segmentación → Opciones → Estilo: **Lista desplegable**",
                 "Selección: activar *Opción \"Seleccionar todo\"* y *Selección múltiple con Ctrl*",
                 f"Encabezado de segmentación: activado, texto \"{nombre}\", tamaño 10, color #595959",
                 "Valores: tamaño 11. Con 48 px de alto caben el encabezado y la lista; no lo hagas más bajo"],
    )

for clave, medida, etiqueta in [
    ("kpi_pedidos", "Pedidos", "Pedidos totales"),
    ("kpi_ingreso", "Ingreso estimado", "Ingreso estimado"),
    ("kpi_precio", "Precio promedio ponderado", "Precio ponderado"),
    ("kpi_centros", "Centros activos", "Centros"),
    ("kpi_comidas", "Comidas activas", "Comidas"),
]:
    V[clave] = dict(
        tipo="Tarjeta",
        pozos=[("Campos / Valor", f"M:{medida}", "")],
        ajustes=[f"Doble clic en el campo del pozo → renombrar a \"{etiqueta}\" (es la etiqueta pequeña)",
                 "Valor: unidades de visualización **Automático**"],
    )

V["tendencia"] = dict(
    tipo="Gráfico de líneas",
    pozos=[("Eje X", "C:dim_semana[semana]", "No resumir"),
           ("Eje Y", "M:Pedidos", ""),
           ("Eje Y", "M:Media móvil 4 semanas", "segunda línea")],
    ajustes=["Eje X → Tipo: **Continuo**; título del eje: desactivado",
             "Eje Y → título desactivado; unidades de visualización **Miles**",
             "Líneas: `Pedidos` gris claro (#A6A6A6), `Media móvil 4 semanas` azul (#3599B8), 2 px",
             "Leyenda: arriba a la izquierda"],
)
V["categorias"] = dict(
    tipo="Gráfico de barras agrupadas",
    pozos=[("Eje Y", "C:dim_comida[categoria]", ""),
           ("Eje X", "M:Pedidos", "")],
    ajustes=["Ordenar: *…* (más opciones) → Ordenar eje → **Pedidos**, **Descendente**",
             "Etiquetas de datos: activadas, unidades **Millones**, 1 decimal",
             "Eje X: desactivado (las etiquetas ya dan el valor)"],
)
V["tipos_centro"] = dict(
    tipo="Gráfico de columnas agrupadas",
    pozos=[("Eje X", "C:dim_centro[tipo_centro]", ""),
           ("Eje Y", "M:Pedidos por fila", "")],
    ajustes=["Etiquetas de datos activadas, 0 decimales", "Eje Y desactivado"],
)
V["promocion"] = dict(
    tipo="Gráfico de columnas agrupadas",
    pozos=[("Eje X", "C:fct_demanda[tipo_promocion]", ""),
           ("Eje Y", "M:Pedidos por fila", "")],
    ajustes=["Ordenar eje → **Pedidos por fila**, **Ascendente** (de Sin promoción a Email + home)",
             "Etiquetas de datos activadas, 0 decimales", "Eje Y desactivado"],
)
V["lectura"] = dict(
    tipo="Cuadro de texto",
    pozos=[],
    ajustes=["Insertar → Cuadro de texto; texto de GUIA_FONDOS.md (Página 1 · Cómo leer esta página)",
             "Segoe UI 12, color #333333, sin fondo"],
)

# ---- Página 2 ---------------------------------------------------------------
V["matriz_categorias"] = dict(
    tipo="Matriz",
    pozos=[("Filas", "C:dim_comida[categoria]", ""),
           ("Valores", "M:Pedidos", ""),
           ("Valores", "M:Participación pedidos", ""),
           ("Valores", "M:Ranking categoría", ""),
           ("Valores", "M:Precio promedio ponderado", "")],
    ajustes=["Ordenar por **Pedidos**, descendente (clic en el encabezado de la columna)",
             "Formato condicional → `Participación pedidos` → **Barras de datos** (color #3599B8)",
             "Renombrar en el pozo: \"Participación\", \"Ranking\", \"Precio ponderado\""],
)
V["pareto"] = dict(
    tipo="Gráfico de líneas y columnas apiladas",
    pozos=[("Eje X", "C:mart_comidas_abc[ranking_global]", "No resumir"),
           ("Eje Y de columna", "C:mart_comidas_abc[pedidos]", "Suma"),
           ("Leyenda de columna", "C:mart_comidas_abc[clase_abc]", ""),
           ("Eje Y de línea", "C:mart_comidas_abc[participacion_acumulada]", "Suma"),
           ("Información sobre herramientas", "C:mart_comidas_abc[meal_id]", "No resumir"),
           ("Información sobre herramientas", "C:mart_comidas_abc[categoria]", "")],
    ajustes=["Antes de armarlo, comprueba en *Vista de tabla* que `participacion_acumulada` va de 0 a 1 "
             "(0,1996 … 1)",
             "Eje X = puesto de la comida (1 = la que más vende), así las barras ya salen ordenadas. "
             "Eje X → Tipo: **Categórico**; título \"Comidas ordenadas por pedidos\"",
             "Colores de leyenda: A #404040, B #A6A6A6, C #DCDCDC",
             "Línea: interpolación **Lineal** (no suavizada), color #3599B8, 2 px",
             "Eje Y secundario (línea): formato **Porcentaje**, mínimo 0, máximo 1",
             "Analítica (lupa) → Línea constante en el eje Y secundario: 0,8, discontinua, etiqueta \"80 %\""],
)
V["anios"] = dict(
    tipo="Gráfico de líneas",
    pozos=[("Eje X", "C:dim_semana[semana_del_anio]", "No resumir"),
           ("Eje Y", "M:Pedidos", ""),
           ("Leyenda", "C:dim_semana[anio_relativo]", "")],
    ajustes=["Eje X → Tipo: **Continuo**",
             "Colores: año 1 #BFBFBF, año 2 #737373, año 3 #3599B8 (el año 3 solo tiene 41 semanas)"],
)
V["dispersion"] = dict(
    tipo="Gráfico de dispersión",
    pozos=[("Valores", "C:dim_centro[center_id]", "No resumir"),
           ("Eje X", "C:dim_centro[area_operativa]", "Promedio"),
           ("Eje Y", "M:Pedidos", ""),
           ("Leyenda", "C:dim_centro[tipo_centro]", "")],
    ajustes=["Marcadores tamaño 6", "Títulos de eje: activados (\"Área operativa\", \"Pedidos\")"],
)
V["top_centros"] = dict(
    tipo="Tabla",
    pozos=[("Columnas", "C:dim_centro[center_id]", "No resumir"),
           ("Columnas", "C:dim_centro[tipo_centro]", ""),
           ("Columnas", "M:Pedidos", ""),
           ("Columnas", "M:Ranking centro", ""),
           ("Columnas", "M:Participación pedidos", "")],
    ajustes=["Ordenar por **Pedidos**, descendente", "Totales: desactivados",
             "Renombrar: \"Centro\", \"Tipo\", \"Ranking\", \"Participación\""],
)

# ---- Página 3 ---------------------------------------------------------------
V["indice_promos"] = dict(
    tipo="Matriz",
    pozos=[("Filas", "C:mart_promociones_indice[categoria]", ""),
           ("Columnas", "C:mart_promociones_indice[tipo_promocion]", ""),
           ("Valores", "C:mart_promociones_indice[indice_vs_sin_promo]", "Promedio")],
    ajustes=["En el panel Datos, selecciona `indice_vs_sin_promo` → Herramientas de columna → Formato decimal, **2** decimales",
             "Formato condicional → **Color de fondo** → Escala de colores: mínimo #FFFFFF, máximo #3599B8",
             "Subtotales de filas y columnas: desactivados (un promedio de índices no tiene sentido)"],
)
V["cohortes"] = dict(
    tipo="Matriz",
    pozos=[("Filas", "C:mart_cohortes[cohorte_trimestre]", "No resumir"),
           ("Columnas", "C:mart_cohortes[periodo_desde_inicio]", "No resumir"),
           ("Valores", "C:mart_cohortes[tasa_retencion]", "Promedio")],
    ajustes=["En el panel Datos, selecciona `tasa_retencion` → Herramientas de columna → Formato **Porcentaje**, 0 decimales",
             "Formato condicional → Color de fondo → escala #FFFFFF → #3599B8",
             "Subtotales desactivados; tamaño de texto 10 si no cabe"],
)
V["deciles"] = dict(
    tipo="Gráfico de líneas",
    pozos=[("Eje X", "C:mart_bandas_precio[decil_precio]", "No resumir"),
           ("Eje Y", "C:mart_bandas_precio[pedidos_promedio_fila]", "Promedio")],
    ajustes=["Panel Filtros → *Filtros en este objeto visual* → `categoria` → solo **Todas**",
             "Eje X → Tipo: **Categórico**; marcadores activados"],
)
V["rcs"] = dict(
    tipo="Gráfico de líneas",
    pozos=[("Eje X", "C:mart_elasticidad_rcs[precio]", "No resumir"),
           ("Eje Y", "C:mart_elasticidad_rcs[elasticidad_rcs]", "Promedio")],
    ajustes=["Eje X → Tipo: **Continuo**",
             "Analítica (ícono de lupa) → **Línea constante** → valor −1, color #FB8281, discontinua, etiqueta \"Elasticidad = −1\"",
             "Color de la línea #3599B8, marcadores activados"],
)
V["elasticidad_cat"] = dict(
    tipo="Gráfico de barras agrupadas",
    pozos=[("Eje Y", "C:mart_elasticidad_categoria[categoria]", ""),
           ("Eje X", "C:mart_elasticidad_categoria[elasticidad]", "Promedio")],
    ajustes=["Ordenar eje → **Promedio de elasticidad**, **Ascendente** (la más negativa arriba)",
             "Etiquetas de datos activadas, 2 decimales", "Color #404040"],
)

# ---- Página 4 ---------------------------------------------------------------
for clave, seccion in [("hallazgos", "Qué muestran los datos"),
                       ("limites", "Qué no se puede concluir"),
                       ("metodo", "Cómo se construyó")]:
    V[clave] = dict(
        tipo="Cuadro de texto",
        pozos=[],
        ajustes=[f"Texto de GUIA_FONDOS.md (Página 4 · {seccion}), con viñetas",
                 "Segoe UI 13, color #333333, interlineado cómodo"],
    )

# ---- Página 5 ---------------------------------------------------------------
for clave, medida, etiqueta in [
    ("ctl_pedidos", "Control pedidos totales", "Control: pedidos = 119 557 485"),
    ("ctl_filas", "Control filas", "Control: filas = 456 548"),
    ("val_pedidos", "Pedidos", "Pedidos (DAX)"),
    ("val_precio", "Precio promedio fila", "Precio promedio fila (DAX)"),
]:
    V[clave] = dict(
        tipo="Tarjeta",
        pozos=[("Campos / Valor", f"M:{medida}", "")],
        ajustes=[f"Renombrar en el pozo: \"{etiqueta}\""],
    )
V["calidad"] = dict(
    tipo="Tabla",
    pozos=[("Columnas", "C:calidad_resultados[regla]", ""),
           ("Columnas", "C:calidad_resultados[descripcion]", ""),
           ("Columnas", "C:calidad_resultados[filas_con_error]", "Suma (cada regla es una fila)")],
    ajustes=["Totales activados: el total de `filas_con_error` debe ser **0**",
             "Formato condicional en `filas_con_error`: color de fuente rojo #D70C0C si > 0"],
)
# El panel "cuadre" lleva tres visuales apilados (posiciones propias)
V["cuadre"] = dict(
    sub=[
        ("Tabla SQL", "Tabla", 980, 302, 888, 120,
         [("Columnas", "C:mart_kpis[pedidos_totales]", "Suma"),
          ("Columnas", "C:mart_kpis[n_filas]", "Suma"),
          ("Columnas", "C:mart_kpis[precio_promedio_fila]", "Suma")],
         ["Renombrar: \"Pedidos (SQL)\", \"Filas (SQL)\", \"Precio promedio (SQL)\"", "Totales desactivados"]),
        ("Tabla DAX", "Tabla", 980, 438, 888, 120,
         [("Columnas", "M:Pedidos", ""), ("Columnas", "M:Filas", ""),
          ("Columnas", "M:Precio promedio fila", "")],
         ["Renombrar: \"Pedidos (DAX)\", \"Filas (DAX)\", \"Precio promedio (DAX)\"",
          "Debe mostrar exactamente los mismos tres números que la tabla SQL"]),
        ("Nota", "Cuadro de texto", 980, 574, 888, 120, [],
         ["Texto: \"Arriba, el total calculado en DuckDB (mart_kpis). Abajo, el mismo total con "
          "medidas DAX sobre el modelo estrella. Si coinciden, el modelo de Power BI está bien "
          "relacionado y sin filtros ocultos.\""]),
    ],
)
