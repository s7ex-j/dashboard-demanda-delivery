# Dashboard en Looker Studio

Versión pública del dashboard (enlace: *pendiente*). Usa solo las tablas agregadas de
[`datos/`](datos/); ninguna fila del dataset original sale del equipo.

| Fuente | Contenido |
|---|---|
| `ls_kpis` | Totales del periodo |
| `ls_tendencia` | Pedidos por semana, media móvil y variaciones |
| `ls_categorias`, `ls_tipos_centro`, `ls_centros` | Participación y rankings |
| `ls_comidas_abc` | Clasificación ABC (Pareto) de las 51 comidas |
| `ls_promociones`, `ls_indice_promociones` | Promociones: comparación cruda e índice por centro y comida |
| `ls_cohortes` | Pares centro × comida activos por trimestre desde la primera venta |
| `ls_bandas_precio` | Pedidos por decil de precio, total y por categoría |
| `ls_elasticidad_rcs`, `ls_elasticidad_categoria` | Resultados publicados del estudio (descriptivos) |
| `ls_calidad` | Las 17 reglas de calidad del pipeline |

Los genera `python -m pipeline.exportar_looker` a partir de `exportes/marts/`, con nombres de
campo en español y tasas como fracción (0,25 = 25 %). `tests/test_exportar_looker.py` comprueba
que los totales cuadran con los KPI y que los archivos versionados están al día.
