import duckdb
import pandas as pd

from pipeline.build import MARTS, TABLAS_ESTRELLA, exportar


def test_exporta_estrella_y_marts(con, crudo, tmp_path):
    exportar(con, tmp_path)
    for t in TABLAS_ESTRELLA:
        assert (tmp_path / "estrella" / f"{t}.parquet").exists()
    for m in MARTS:
        assert (tmp_path / "marts" / f"{m}.csv").exists()
        assert (tmp_path / "marts_parquet" / f"{m}.parquet").exists()

    n = duckdb.connect().execute(f"SELECT COUNT(*) FROM '{(tmp_path / 'estrella' / 'fct_demanda.parquet').as_posix()}'").fetchone()[0]
    assert n == len(crudo)

    # CSV con punto decimal y encabezado, como lo espera Looker Studio
    kpis = pd.read_csv(tmp_path / "marts" / "mart_kpis.csv")
    assert kpis.pedidos_totales.item() == crudo.num_orders.sum()
    texto = (tmp_path / "marts" / "mart_tendencia_semanal.csv").read_text(encoding="utf-8")
    assert texto.startswith("semana,") and "." in texto


def test_parquet_de_marts_conserva_decimales_y_tipos(con, tmp_path):
    exportar(con, tmp_path)
    c = duckdb.connect()
    abc = (tmp_path / "marts_parquet" / "mart_comidas_abc.parquet").as_posix()
    tipos = {r[0]: r[1] for r in c.execute(f"DESCRIBE SELECT * FROM '{abc}'").fetchall()}
    assert tipos["participacion_acumulada"] == "DOUBLE"
    assert tipos["pedidos"] == "BIGINT"            # no HUGEINT: Power BI no lo lee
    lo, hi = c.execute(f"SELECT MIN(participacion_acumulada), MAX(participacion_acumulada) FROM '{abc}'").fetchone()
    assert 0 < lo < 1 and abs(hi - 1) < 1e-9
    # Ningún archivo de marts lleva HUGEINT
    for f in (tmp_path / "marts_parquet").glob("*.parquet"):
        assert "HUGEINT" not in {r[1] for r in c.execute(f"DESCRIBE SELECT * FROM '{f.as_posix()}'").fetchall()}, f.name
