# Fondos de página: cómo usarlos

Cinco fondos (uno por página) con los paneles, títulos y pie ya dibujados. Encima van los visuales,
sin fondo ni borde propio. Las posiciones exactas de cada visual están en
[`POSICIONES.md`](POSICIONES.md).

| Página | Fondo |
|---|---|
| 1 Describir | `fondo_1_describir.png` |
| 2 Comparar | `fondo_2_comparar.png` |
| 3 Diagnosticar | `fondo_3_diagnosticar.png` |
| 4 Hallazgos y límites | `fondo_4_hallazgos.png` |
| 5 Validación | `fondo_5_validacion.png` |

Si cambias un título o un panel, edita `generar_fondos.py` y vuelve a generarlos:
`python dashboard/powerbi/fondos/generar_fondos.py` (requiere `pip install pillow`).

## 1. Tamaño de página: 1920 × 1080

*Formato de página → Configuración del lienzo → Tipo: Personalizado → 1920 × 1080*.

Por qué no 3840 × 2160: en Power BI el tamaño de letra no escala con el lienzo. En una página 4K,
un texto de 12 pt ocupa la mitad de espacio y queda diminuto al ver la página entera. Las
imágenes ya vienen a 3840 × 2160, así que se ven nítidas igual.

## 2. Tema

*Vista → Temas → Buscar temas* → `dashboard/powerbi/tema_charcoal_demanda.json`.

Es tu tema *Marketing Gray & Charcoal* con cuatro cambios para encajar con los fondos:

1. Visuales sin fondo, borde, sombra ni título (todo eso ya viene en la imagen).
2. Colores de datos: gris carbón `#404040` como principal y azul `#3599B8` como acento.
3. Segmentadores sin borde propio.
4. Gris `#F5F6F7` como respaldo detrás de la imagen.

> Si un visual que ya creaste sigue con borde o fondo blanco, es porque lo formateaste a mano y
> esa configuración manda sobre el tema. Clic derecho en el visual → *Restablecer al valor
> predeterminado* (o desactiva *Fondo*, *Borde*, *Sombra* y *Título* en *Formato → General*).

## 3. Poner el fondo en cada página

En la página, sin ningún visual seleccionado:

1. *Formato de página → Fondo del lienzo*: *Examinar* → el PNG de la página.
2. *Ajuste de la imagen*: **Ajustar**.
3. *Transparencia*: **0 %**.
4. *Fondo del papel tapiz*: color `#F5F6F7` (se ve en los bordes si la ventana no es 16:9).

## 4. Colocar cada visual

1. Crea el visual con los campos que indica `POSICIONES.md`.
2. Selecciónalo → *Formato del visual → General → Propiedades*.
3. Escribe *Tamaño* (Alto, Ancho) y *Posición* (Horizontal, Vertical) tal cual la tabla.

Es más rápido y exacto que arrastrar. Para repetir el formato de un visual en otro, usa la
*Copiar formato* (brocha) de la pestaña *Inicio*.

Ajustes que más cambian el aspecto:

- **Ejes:** sin título de eje cuando el panel ya dice qué se mide; líneas de cuadrícula en gris
  claro (`#F0F0F0`) o apagadas.
- **Etiquetas de datos:** solo en barras y columnas, con unidades automáticas (119,6 M).
- **Tarjetas:** etiqueta de categoría visible (es el texto pequeño arriba del número). Renómbrala
  con doble clic en el campo, por ejemplo `Pedidos` → "Pedidos totales".
- **Un solo color por gráfico** salvo que la leyenda signifique algo (por ejemplo `anio_relativo`).

## 5. Navegador de páginas

*Insertar → Botones → Navegador → Navegador de páginas*. Posición **X 1180 · Y 40 · Ancho 700 ·
Alto 44** en las cinco páginas. Copia el mismo navegador de una página a otra (Ctrl+C / Ctrl+V
conserva la posición).

Ocultar páginas auxiliares: si no quieres que la página Validación salga en el navegador, clic
derecho en su pestaña → *Ocultar página*.

## 6. Textos para los cuadros de texto

Pégalos en *Insertar → Cuadro de texto*, sin fondo, con letra Segoe UI 12 y color `#333333`.
Las cifras vienen del estudio v3.3.0 y del pipeline. Las marcadas con **[completar]** se
leen en el propio dashboard cuando esté armado: no las inventes.

### Página 1 · Cómo leer esta página

- **Pedidos:** suma de `num_orders`. **Fila:** una comida en un centro durante una semana; 456 548
  filas no son 456 548 pedidos.
- **Ingreso estimado:** pedidos × precio de checkout. Unidades monetarias anónimas: el dataset no
  dice moneda ni país.
- **Precio ponderado:** ingreso ÷ pedidos. Pesa más lo que más se vende.
- Las semanas son relativas (1 a 145), sin fechas de calendario.
- Los filtros de arriba afectan a toda la página.

### Página 4 · Qué muestran los datos

- 119,6 millones de pedidos en 145 semanas, 77 centros y 51 comidas: unos 824 mil por semana.
- La semana con más pedidos es la 48 (1,30 millones).
- El promedio semanal del segundo año relativo es 5,6 % mayor que el del primero.
- **Beverages** concentra el 33,9 % de los pedidos. Con Rice Bowl y Sandwich, las tres primeras
  categorías suman el 66,1 %.
- Rice Bowl tiene más pedidos por fila (625) que Beverages (317): aparece en menos combinaciones
  semana × centro, pero cada una vende más.
- Los centros TYPE_A son 43 de 77 y generan el 57,7 % de los pedidos. Por fila, los TYPE_B
  venden más (319 frente a 262 de TYPE_A y 207 de TYPE_C).
- Una fila con email y portada a la vez tiene 3,9 veces los pedidos de una fila sin promoción
  (comparación cruda). **[completar]** el índice controlado por centro y comida de la página 3.
- **[completar]** cuántas comidas son clase A (80 % de los pedidos).
- La elasticidad promedio del modelo principal es −0,76 (IC 95 % [−0,843; −0,675]), pero no es
  constante: cambia con el nivel de precio.

### Página 4 · Qué no se puede concluir

- **Que una promoción cause más ventas.** Las semanas con promoción también tienen otro precio y
  otra temporada. El índice compara, no aísla el efecto.
- **Qué precio poner.** Las elasticidades vienen de modelos distintos que miden cosas distintas;
  juntarlas en una regla de precios no está respaldado.
- **Por qué una comida deja de venderse en un centro.** El dataset no distingue entre "retirada
  del menú" y "sin registro esa semana".
- **Rentabilidad.** No hay costos ni márgenes: el ingreso es una estimación de facturación.
- **Fechas, moneda o país.** Los datos son anónimos.

### Página 4 · Cómo se construyó

- Datos públicos de Kaggle, verificados con SHA-256 y no redistribuidos.
- SQL en DuckDB: staging, esquema estrella y 10 consultas de negocio con CTE y funciones de
  ventana.
- 17 reglas de calidad que detienen el proceso si alguna falla.
- Tests: cada consulta se recalcula en pandas; con los datos reales, las cifras coinciden con el
  estudio v3.3.0.
- Medidas DAX validadas contra el SQL (página 5).
- Código: github.com/s7ex-j/dashboard-demanda-delivery
- Estudio: DOI 10.5281/zenodo.23586040
