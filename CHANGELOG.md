# Cambios

## [1.0.0] - 2026-10-28

Primera versión publicada.

- **SQL (DuckDB):** staging con tipos explícitos, esquema estrella (`fct_demanda` y tres
  dimensiones) y 10 marts de negocio: KPI, tendencia semanal, categorías, ABC de comidas,
  promociones (comparación cruda e índice por centro y comida), centros, tipos de centro,
  cohortes y deciles de precio.
- **Calidad:** 17 reglas que detienen el pipeline si alguna falla.
- **Tests:** cada mart se recalcula en pandas; con 11 errores inyectados, cada regla los detecta;
  con los datos reales, los totales concilian con el estudio v3.3.0. CI en Ubuntu y Windows.
- **Power BI:** proyecto PBIP de cinco páginas con medidas DAX y página de validación SQL = DAX.
- **Looker Studio:** versión pública con fuentes agregadas (`dashboard/looker/datos/`).
- **Documentación:** README con capturas de ambos dashboards, PDFs en `docs/` y detalle de las
  consultas en `docs/consultas.md`.
