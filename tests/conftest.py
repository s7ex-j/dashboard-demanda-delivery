from pathlib import Path

import pandas as pd
import pytest

from pipeline.build import construir

RAIZ = Path(__file__).resolve().parents[1]
FIXTURE_RAW = RAIZ / "tests" / "fixtures" / "raw"
REAL_RAW = RAIZ / "data" / "raw"


@pytest.fixture(scope="session")
def con():
    """Base DuckDB construida sobre el dataset sintético."""
    c = construir(FIXTURE_RAW)
    yield c
    c.close()


@pytest.fixture(scope="session")
def crudo():
    """El mismo dataset sintético, unido en pandas (oráculo independiente del SQL)."""
    t = pd.read_csv(FIXTURE_RAW / "train.csv")
    m = pd.read_csv(FIXTURE_RAW / "meal_info.csv")
    c = pd.read_csv(FIXTURE_RAW / "fulfilment_center_info.csv")
    return t.merge(m, on="meal_id").merge(c, on="center_id")


def df(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()
