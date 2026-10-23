import duckdb
import pandas as pd

from pipeline.build import MARTS, TABLAS_ESTRELLA, exportar


def test_exporta_estrella_y_marts(con, crudo, tmp_path):
    exportar(con, tmp_path)
    for t in TABLAS_ESTRELLA:
        assert (tmp_path / "estrella" / f"{t}.parquet").exists()
    for m in MARTS:
        assert (tmp_path / "marts" / f"{m}.csv").exists()

    n = duckdb.connect().execute(f"SELECT COUNT(*) FROM '{(tmp_path / 'estrella' / 'fct_demanda.parquet').as_posix()}'").fetchone()[0]
    assert n == len(crudo)

    # CSV con punto decimal y encabezado, como lo espera Looker Studio
    kpis = pd.read_csv(tmp_path / "marts" / "mart_kpis.csv")
    assert kpis.pedidos_totales.item() == crudo.num_orders.sum()
    texto = (tmp_path / "marts" / "mart_tendencia_semanal.csv").read_text(encoding="utf-8")
    assert texto.startswith("semana,") and "." in texto
