"""
Construye la base DuckDB del dashboard y exporta los datos para Power BI y Looker Studio.

Pasos:
  1. Ejecuta sql/01..05 en orden (staging, estrella, marts, referencias, calidad).
  2. Detiene el proceso si alguna regla de calidad falla.
  3. Exporta:
       exportes/estrella/*.parquet  -> modelo estrella para Power BI (no se versiona:
                                       contiene datos a nivel de fila del dataset)
       exportes/marts/*.csv         -> tablas agregadas para Looker Studio y Power BI,
                                       más el resultado de las reglas de calidad

Uso (desde la raíz del repositorio, también en cmd de Windows):
    python -m pipeline.build
    python -m pipeline.build --raw ruta\\a\\raw --db salida.duckdb --sin-exportar
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
SQL_DIR = RAIZ / "sql"
REF_DIR = RAIZ / "referencias"

TABLAS_ESTRELLA = ["fct_demanda", "dim_comida", "dim_centro", "dim_semana"]
MARTS = [
    "mart_kpis",
    "mart_tendencia_semanal",
    "mart_categorias",
    "mart_comidas_abc",
    "mart_promociones_matriz",
    "mart_promociones_indice",
    "mart_centros",
    "mart_tipos_centro",
    "mart_cohortes",
    "mart_bandas_precio",
    "mart_elasticidad_rcs",
    "mart_elasticidad_categoria",
    "calidad_resultados",
]


class ErrorCalidad(RuntimeError):
    """Alguna regla de calidad de datos tiene registros con error."""


def _ruta_sql(p: Path) -> str:
    # DuckDB acepta "/" también en Windows; así se evitan escapes de "\".
    return p.resolve().as_posix().replace("'", "''")


def construir(raw_dir: Path, db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    """Ejecuta todos los scripts SQL y devuelve la conexión abierta."""
    faltan = [f for f in ("train.csv", "meal_info.csv", "fulfilment_center_info.csv")
              if not (raw_dir / f).exists()]
    if faltan:
        raise FileNotFoundError(
            f"Faltan {', '.join(faltan)} en {raw_dir}. Ver data/raw/README.md."
        )

    con = duckdb.connect(db_path)
    con.execute(f"SET VARIABLE raw_dir = '{_ruta_sql(raw_dir)}'")
    con.execute(f"SET VARIABLE ref_dir = '{_ruta_sql(REF_DIR)}'")

    for script in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
        t0 = time.perf_counter()
        con.execute(script.read_text(encoding="utf-8"))
        print(f"  {script.name:<30} {time.perf_counter() - t0:6.2f} s")
    return con


def verificar_calidad(con: duckdb.DuckDBPyConnection) -> list[tuple]:
    """Imprime el resultado de las reglas y lanza ErrorCalidad si alguna falla."""
    filas = con.execute(
        "SELECT regla, descripcion, filas_con_error FROM calidad_resultados ORDER BY regla"
    ).fetchall()
    for regla, desc, n in filas:
        marca = "OK   " if n == 0 else "FALLA"
        print(f"  [{marca}] {regla:<24} {n:>8}  {desc}")
    fallas = [f for f in filas if f[2] != 0]
    if fallas:
        raise ErrorCalidad(f"{len(fallas)} regla(s) de calidad fallaron: "
                           + ", ".join(f[0] for f in fallas))
    return filas


def exportar(con: duckdb.DuckDBPyConnection, destino: Path) -> None:
    (destino / "estrella").mkdir(parents=True, exist_ok=True)
    (destino / "marts").mkdir(parents=True, exist_ok=True)
    for t in TABLAS_ESTRELLA:
        p = destino / "estrella" / f"{t}.parquet"
        con.execute(f"COPY {t} TO '{_ruta_sql(p)}' (FORMAT parquet)")
    for m in MARTS:
        p = destino / "marts" / f"{m}.csv"
        # Punto decimal y UTF-8: lo que esperan Google Sheets y Looker Studio.
        con.execute(f"COPY (SELECT * FROM {m}) TO '{_ruta_sql(p)}' (HEADER, DELIMITER ',')")
    print(f"  Exportado en {destino.relative_to(RAIZ) if destino.is_relative_to(RAIZ) else destino}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=RAIZ / "data" / "raw",
                    help="carpeta con train.csv, meal_info.csv y fulfilment_center_info.csv")
    ap.add_argument("--db", default=str(RAIZ / "salida" / "demanda.duckdb"),
                    help="archivo DuckDB de salida (':memory:' para no escribir)")
    ap.add_argument("--exportes", type=Path, default=RAIZ / "exportes")
    ap.add_argument("--sin-exportar", action="store_true")
    a = ap.parse_args(argv)

    if a.db != ":memory:":
        Path(a.db).parent.mkdir(parents=True, exist_ok=True)

    print("1/3 Ejecutando SQL")
    con = construir(a.raw, a.db)
    print("2/3 Calidad de datos")
    try:
        verificar_calidad(con)
    except ErrorCalidad as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    if a.sin_exportar:
        print("3/3 Exportación omitida")
    else:
        print("3/3 Exportando")
        exportar(con, a.exportes)
    kpi = con.execute("SELECT n_filas, pedidos_totales, n_centros, n_comidas, n_semanas FROM mart_kpis").fetchone()
    print(f"\nListo: {kpi[0]:,} filas · {kpi[1]:,} pedidos · {kpi[2]} centros · "
          f"{kpi[3]} comidas · {kpi[4]} semanas")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
