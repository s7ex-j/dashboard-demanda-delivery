"""
Genera los fondos de página del dashboard de Power BI y la tabla de posiciones de cada visual.

Diseño en una cuadrícula de 1920 × 1080 (tamaño de página recomendado en Power BI). Las imágenes
se exportan al doble (3840 × 2160) para que se vean nítidas en pantallas 4K y en las capturas.

Uso:  python dashboard/powerbi/fondos/generar_fondos.py
Salida: fondo_1_describir.png ... fondo_5_validacion.png y POSICIONES.md en esta carpeta.
Requiere Pillow (pip install pillow) y la fuente Inter (o cambia FUENTES).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DESTINO = Path(__file__).resolve().parent
sys.path.insert(0, str(DESTINO))
ESCALA = 2                     # 1920×1080 lógico -> 3840×2160 px
W, H = 1920, 1080
M, G = 40, 16                  # margen y separación

# Colores alineados con el tema "Marketing Gray & Charcoal"
FONDO = "#F5F6F7"
PANEL = "#FFFFFF"
BORDE = "#E0E0E0"
TEXTO = "#1A1A1A"
TEXTO_2 = "#595959"
TEXTO_3 = "#8C8C8C"
ACENTO = "#3599B8"
ACENTO_SUAVE = "#EAF4F8"
ALERTA = "#FB8281"
ALERTA_SUAVE = "#FDF0EF"

FUENTES = {
    "regular": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "C:/Windows/Fonts/segoeui.ttf"],
    "medium": ["/usr/share/fonts/opentype/inter/Inter-Medium.otf", "C:/Windows/Fonts/segoeui.ttf"],
    "semibold": ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "C:/Windows/Fonts/seguisb.ttf"],
    "bold": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "C:/Windows/Fonts/segoeuib.ttf"],
}


def fuente(peso: str, tam: float) -> ImageFont.FreeTypeFont:
    for ruta in FUENTES[peso]:
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, round(tam * ESCALA))
    return ImageFont.load_default(round(tam * ESCALA))


def s(*v):
    return [round(x * ESCALA) for x in v]


PIE = ("Datos: Food Demand Forecasting (Genpact / Analytics Vidhya, Kaggle)  ·  Unidades monetarias "
       "anónimas  ·  1 fila = semana × centro × comida  ·  n_filas no son pedidos")
FIRMA = "Jharol André Vilca Ramos  ·  github.com/s7ex-j  ·  Estudio: DOI 10.5281/zenodo.23586040"

# ---------------------------------------------------------------------------
# Páginas: cada panel es (clave, x, y, ancho, alto, título, pregunta, visual sugerido)
# Un panel sin título es una tarjeta (KPI) o un segmentador: el visual ocupa todo el panel.
# ---------------------------------------------------------------------------
def fila(y, h, anchos, claves_titulos):
    """Reparte paneles en una fila; 'anchos' son proporciones."""
    total = W - 2 * M - G * (len(anchos) - 1)
    suma = sum(anchos)
    x, out = M, []
    for i, (a, extra) in enumerate(zip(anchos, claves_titulos)):
        w = round(total * a / suma) if i < len(anchos) - 1 else (W - M) - x
        out.append((extra[0], x, y, w, h, *extra[1:]))
        x += w + G
    return out


FILTROS = ("filtros", M, 104, W - 2 * M, 64, None, None, "segmentadores")

PAGINAS = [
    {
        "archivo": "fondo_1_describir.png",
        "numero": "1", "nombre": "Describir",
        "pregunta": "¿Qué tamaño tiene el negocio y cómo se mueve la demanda?",
        "paneles": [FILTROS]
        + fila(184, 112, [1] * 5, [
            ("kpi_pedidos", None, None, "Tarjeta: Pedidos"),
            ("kpi_ingreso", None, None, "Tarjeta: Ingreso estimado"),
            ("kpi_precio", None, None, "Tarjeta: Precio promedio ponderado"),
            ("kpi_centros", None, None, "Tarjeta: Centros activos"),
            ("kpi_comidas", None, None, "Tarjeta: Comidas activas"),
        ])
        + fila(312, 400, [2, 1], [
            ("tendencia", "Pedidos por semana", "¿La demanda crece, cae o es estacional?",
             "Líneas: dim_semana[semana] × Pedidos y Media móvil 4 semanas"),
            ("categorias", "Pedidos por categoría", "¿Qué categorías concentran la demanda?",
             "Barras horizontales: dim_comida[categoria] × Pedidos"),
        ])
        + fila(728, 296, [1, 1, 1], [
            ("tipos_centro", "Pedidos por fila según tipo de centro", "¿Qué tipo de centro vende más por comida?",
             "Columnas: dim_centro[tipo_centro] × Pedidos por fila"),
            ("promocion", "Pedidos por fila según promoción", "¿Cuánto más se vende con promoción? (crudo)",
             "Columnas: fct_demanda[tipo_promocion] × Pedidos por fila"),
            ("lectura", "Cómo leer esta página", "Definiciones y límites",
             "Cuadro de texto (texto en GUIA_FONDOS.md)"),
        ]),
    },
    {
        "archivo": "fondo_2_comparar.png",
        "numero": "2", "nombre": "Comparar",
        "pregunta": "¿Qué categorías, comidas y centros sostienen el negocio?",
        "paneles": [FILTROS]
        + fila(184, 416, [1, 1], [
            ("matriz_categorias", "Categorías", "Participación, ranking y precio ponderado",
             "Matriz: categoria × Pedidos, Participación pedidos, Ranking categoría, Precio promedio ponderado"),
            ("pareto", "Clasificación ABC de comidas", "¿Cuántas comidas explican el 80 % de los pedidos?",
             "Gráfico combinado desde mart_comidas_abc: barras pedidos, línea participacion_acumulada"),
        ])
        + fila(616, 408, [2, 1, 1], [
            ("anios", "Pedidos por semana del año", "¿Se repite el patrón entre años relativos?",
             "Líneas: semana_del_anio × Pedidos, leyenda anio_relativo"),
            ("dispersion", "Área operativa y pedidos", "¿Los centros grandes venden más?",
             "Dispersión: area_operativa × Pedidos, detalle center_id, leyenda tipo_centro"),
            ("top_centros", "Ranking de centros", "Pedidos y participación por centro",
             "Tabla: center_id, tipo_centro, Pedidos, Ranking centro, Participación pedidos"),
        ]),
    },
    {
        "archivo": "fondo_3_diagnosticar.png",
        "numero": "3", "nombre": "Diagnosticar",
        "pregunta": "¿Qué se asocia con más o menos pedidos?",
        "aviso": ("Todo en esta página es descriptivo (datos observacionales). No son efectos causales ni "
                  "recomendaciones de precio. Las tablas de esta página no responden a los filtros."),
        "paneles": fila(176, 420, [1, 1], [
            ("indice_promos", "Promoción frente al mismo centro y comida sin promoción",
             "Índice 2,0 = el doble de pedidos que sin promoción",
             "Matriz desde mart_promociones_indice: categoria × tipo_promocion, valor indice_vs_sin_promo"),
            ("cohortes", "Permanencia de comidas en los centros",
             "% de pares centro × comida que siguen vendiendo, por trimestre",
             "Matriz desde mart_cohortes: cohorte_trimestre × periodo_desde_inicio, valor tasa_retencion"),
        ])
        + fila(612, 412, [1, 1, 1], [
            ("deciles", "Pedidos por decil de precio", "Sin controles: solo describe",
             "Líneas desde mart_bandas_precio (categoria = Todas): decil_precio × pedidos_promedio_fila"),
            ("rcs", "Elasticidad según el nivel de precio", "Curva RCS del estudio (promedio −0,76)",
             "Líneas desde mart_elasticidad_rcs: precio × elasticidad_rcs, línea constante en −1"),
            ("elasticidad_cat", "Elasticidad por categoría", "OLS log-log con controles (estudio)",
             "Barras desde mart_elasticidad_categoria: categoria × elasticidad"),
        ]),
    },
    {
        "archivo": "fondo_4_hallazgos.png",
        "numero": "4", "nombre": "Hallazgos y límites",
        "pregunta": "¿Qué dicen los datos y qué no se puede concluir?",
        "paneles": fila(104, 920, [1, 1, 1], [
            ("hallazgos", "Qué muestran los datos", "Hechos medidos en el periodo",
             "Cuadro de texto (texto en GUIA_FONDOS.md)"),
            ("limites", "Qué no se puede concluir", "Límites del dataset y del análisis",
             "Cuadro de texto (texto en GUIA_FONDOS.md)"),
            ("metodo", "Cómo se construyó", "Pipeline, pruebas y fuentes",
             "Cuadro de texto (texto en GUIA_FONDOS.md)"),
        ]),
    },
    {
        "archivo": "fondo_5_validacion.png",
        "numero": "5", "nombre": "Validación",
        "pregunta": "¿El modelo de Power BI da las mismas cifras que el SQL y el estudio?",
        "paneles": fila(104, 112, [1] * 4, [
            ("ctl_pedidos", None, None, "Tarjeta: Control pedidos totales"),
            ("ctl_filas", None, None, "Tarjeta: Control filas"),
            ("val_pedidos", None, None, "Tarjeta: Pedidos"),
            ("val_precio", None, None, "Tarjeta: Precio promedio fila"),
        ])
        + fila(232, 792, [1, 1], [
            ("calidad", "Reglas de calidad de datos", "17 reglas del pipeline SQL: todas deben estar en 0",
             "Tabla: calidad_resultados[regla], [descripcion], [filas_con_error] (No resumir)"),
            ("cuadre", "DAX frente a SQL", "Mismo total por dos caminos",
             "Tabla: mart_kpis (pedidos_totales, n_filas, precio_promedio_fila) junto a tarjetas DAX"),
        ]),
    },
]


def sombra(base: Image.Image, caja, radio):
    capa = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    x0, y0, x1, y1 = caja
    d.rounded_rectangle((x0, y0 + 2 * ESCALA, x1, y1 + 2 * ESCALA), radio, fill=(16, 24, 40, 14))
    base.alpha_composite(capa.filter(ImageFilter.GaussianBlur(4 * ESCALA)))


def panel(img, d, p):
    clave, x, y, w, h, titulo, pregunta, _ = p
    caja = s(x, y, x + w, y + h)
    sombra(img, caja, 10 * ESCALA)
    d.rounded_rectangle(caja, 10 * ESCALA, fill=PANEL, outline=BORDE, width=ESCALA)
    if clave == "filtros":
        d.text(s(x + 20, y + 32), "FILTROS", font=fuente("semibold", 11), fill=TEXTO_3, anchor="lm")
    if titulo:
        d.rectangle(s(x, y + 18, x + 3, y + 38), fill=ACENTO)
        d.text(s(x + 20, y + 16), titulo, font=fuente("semibold", 15), fill=TEXTO)
        d.text(s(x + 20, y + 39), pregunta, font=fuente("regular", 12), fill=TEXTO_2)
        d.line(s(x + 20, y + 62, x + w - 20, y + 62), fill="#F0F0F0", width=ESCALA)


def area_visual(p):
    """Rectángulo donde va el visual (coordenadas de Power BI, página 1920×1080)."""
    clave, x, y, w, h, titulo, _, _ = p
    if clave == "filtros":
        return (x + 112, y + 8, w - 120, h - 16)
    if titulo:
        return (x + 12, y + 70, w - 24, h - 82)
    return (x + 8, y + 8, w - 16, h - 16)


def dibujar(pag):
    img = Image.new("RGBA", s(W, H), FONDO)
    d = ImageDraw.Draw(img)

    # Encabezado
    d.text(s(M, 22), "DEMANDA EN DELIVERY  ·  145 SEMANAS  ·  77 CENTROS  ·  51 COMIDAS",
           font=fuente("semibold", 11), fill=TEXTO_3)
    cx, cy, r = M + 16, 62, 16
    d.ellipse(s(cx - r, cy - r, cx + r, cy + r), fill=ACENTO)
    d.text(s(cx, cy), pag["numero"], font=fuente("bold", 16), fill="#FFFFFF", anchor="mm")
    f_tit = fuente("semibold", 26)
    d.text(s(M + 44, cy), pag["nombre"], font=f_tit, fill=TEXTO, anchor="lm")
    ancho_tit = d.textlength(pag["nombre"], font=f_tit) / ESCALA
    d.text(s(M + 44 + ancho_tit + 16, cy + 2), pag["pregunta"], font=fuente("regular", 15),
           fill=TEXTO_2, anchor="lm")

    if "aviso" in pag:
        x, y, w, h = M, 104, W - 2 * M, 56
        d.rounded_rectangle(s(x, y, x + w, y + h), 10 * ESCALA, fill=ALERTA_SUAVE, outline="#F6C9C6", width=ESCALA)
        d.rectangle(s(x, y + 14, x + 3, y + h - 14), fill=ALERTA)
        d.text(s(x + 20, y + h / 2), "Cómo leer esta página", font=fuente("semibold", 13), fill=TEXTO, anchor="lm")
        d.text(s(x + 200, y + h / 2), pag["aviso"], font=fuente("regular", 13), fill=TEXTO_2, anchor="lm")

    for p in pag["paneles"]:
        panel(img, d, p)

    # Pie
    d.line(s(M, 1036, W - M, 1036), fill=BORDE, width=ESCALA)
    d.text(s(M, 1056), PIE, font=fuente("regular", 11), fill=TEXTO_3, anchor="lm")
    d.text(s(W - M, 1056), FIRMA, font=fuente("regular", 11), fill=TEXTO_3, anchor="rm")

    img.convert("RGB").save(DESTINO / pag["archivo"], optimize=True)


def _medidas_dax():
    """Lee medidas.dax y devuelve {nombre: texto completo de la medida}."""
    texto = (DESTINO.parent / "medidas.dax").read_text(encoding="utf-8")
    bloques = [b.strip() for b in texto.split("\n\n")]
    out = {}
    for b in bloques:
        lineas = [l for l in b.splitlines() if not l.strip().startswith("//")]
        if lineas and " =" in lineas[0]:
            out[lineas[0].split(" =")[0].strip()] = "\n".join(lineas)
    return out


def _campo(c):
    tipo, nombre = c.split(":", 1)
    return f"Medida **{nombre}** (tabla `_Medidas`)" if tipo == "M" else f"Columna `{nombre}`"


def _bloque(titulo, tipo, x, y, w, h, pozos, ajustes, comprueba=()):
    l = [f"#### {titulo}", "",
         f"**Visual:** {tipo}  ·  **X** {x} · **Y** {y} · **Ancho** {w} · **Alto** {h}", ""]
    if pozos:
        l += ["| Pozo | Arrastra | Agregación |", "|---|---|---|"]
        for pozo, campo, agg in pozos:
            if campo.startswith("M:"):
                agg = "— (es medida)"
            l.append(f"| {pozo} | {_campo(campo)} | {agg or '—'} |")
        l.append("")
    for a in ajustes:
        l.append(f"- {a}")
    if comprueba:
        l += ["", "**Comprueba:** " + " · ".join(comprueba)]
    return l + [""]


def tabla_posiciones():
    from detalle_visuales import COMPRUEBA, MARTS_POR_PAGINA, MEDIDAS, NO_RESUMIR, PREPARACION, V

    dax = _medidas_dax()
    L = [
        "# Visuales: posición, campos y formato",
        "",
        "Página **1920 × 1080**. Posición y tamaño se escriben en *Formato del visual → General → "
        "Propiedades* (Tamaño: Alto, Ancho · Posición: Horizontal = X, Vertical = Y).",
        "",
        "## Antes de seguir (una sola vez)",
        "",
    ]
    L += [f"{i}. {t}" for i, t in enumerate(PREPARACION, 1)]
    L += [
        "",
        "## Reglas que evitan los errores más comunes",
        "",
        "1. **Medida o columna.** Lo que dice *Medida* se arrastra desde la tabla `_Medidas` (ícono de "
        "calculadora) y ya viene calculado: no tiene agregación. Lo que dice *Columna* se arrastra "
        "desde su tabla y se le pone la agregación indicada (flecha del campo en el pozo).",
        "2. **Nunca promedies una columna para sacar un KPI.** Ejemplo: el precio ponderado no es "
        "`Promedio de precio_checkout` ni `Promedio de ingreso_estimado`: es la medida "
        "**Precio promedio ponderado** = ingreso ÷ pedidos. Los números con *E* (notación "
        "científica) aparecen justo cuando se agrega una columna que no corresponde.",
        "3. **Identificadores sin resumir.** Antes de empezar, en *Vista de modelo* selecciona cada "
        "columna de esta lista → *Propiedades → Resumir por: **Ninguno***:",
        "",
    ]
    L += [f"   - {x}" for x in NO_RESUMIR]
    L += ["",
          "4. **Los marts se cargan en Parquet, no en CSV.** *Obtener datos → Más… → Parquet* y la ruta "
          "completa del archivo en `exportes\\marts_parquet\\`. El Parquet guarda los tipos (decimal, "
          "entero, texto), así que no depende de la coma o el punto decimal de Windows. Los CSV de "
          "`exportes\\marts\\` son para Looker Studio. Si ya cargaste un mart desde CSV, bórralo "
          "(clic derecho → *Eliminar del modelo*) y cárgalo de nuevo desde Parquet con el mismo nombre.",
          "5. **Formato de una medida:** selecciónala en el panel *Datos* → pestaña *Herramientas de "
          "medidas* → *Formato*. Se hace una vez y vale para todos los visuales.",
          "6. **Navegador de páginas** (todas las páginas): *Insertar → Botones → Navegador → "
          "Navegador de páginas* · **X 1180 · Y 40 · Ancho 700 · Alto 44**.",
          ""]

    for pag in PAGINAS:
        n = pag["numero"]
        L += [f"## Página {n}. {pag['nombre']}", "", f"Fondo: `{pag['archivo']}`", ""]
        if n in MEDIDAS:
            L += ["**Antes: crea estas medidas** (clic derecho en `_Medidas` → *Nueva medida*, una por vez):", ""]
            for nombre, formula, formato in MEDIDAS[n]:
                cuerpo = f"{nombre} = {formula}" if formula else dax[nombre]
                L += ["```", cuerpo, "```", f"Formato: {formato}.", ""]
        if n in MARTS_POR_PAGINA:
            L += ["**Antes: carga estos Parquet** (*Obtener datos → Más… → Parquet*, desde `exportes\\marts_parquet\\`). "
                  "Después, en *Vista de modelo*, borra cualquier relación que Power BI cree con ellos:", ""]
            L += [f"- `{m}`" for m in MARTS_POR_PAGINA[n]] + [""]

        for p in pag["paneles"]:
            clave = p[0]
            x, y, w, h = area_visual(p)
            if clave == "filtros":
                ws = (w - 2 * G) // 3
                for i in range(3):
                    d = V[f"seg{i + 1}"]
                    L += _bloque(f"Segmentador {i + 1}", d["tipo"], x + i * (ws + G), y, ws, h,
                                 d["pozos"], d["ajustes"])
                continue
            d = V[clave]
            if "sub" in d:
                for titulo, tipo, sx, sy, sw, sh, pozos, ajustes in d["sub"]:
                    L += _bloque(f"{p[5]} · {titulo}", tipo, sx, sy, sw, sh, pozos, ajustes,
                                 ["Mismos tres números en las dos tablas"] if titulo == "Tabla DAX" else ())
                continue
            titulo = p[5] or p[7].replace("Tarjeta: ", "Tarjeta · ")
            L += _bloque(titulo, d["tipo"], x, y, w, h, d["pozos"], d["ajustes"],
                         COMPRUEBA.get(clave, ()))

    (DESTINO / "POSICIONES.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    for pag in PAGINAS:
        dibujar(pag)
        print("  ", pag["archivo"])
    tabla_posiciones()
    print("   POSICIONES.md")
