"""
Conciliación con el estudio v3.3.0 (s7ex-j/demanda-delivery-v2).

Con los datos REALES en data/raw/, los marts de DuckDB deben reproducir las
tablas que publicó el estudio (generadas con SQLite + pandas). Si coinciden, la
capa SQL nueva no cambió ningún número.

En GitHub Actions estos tests se omiten porque los datos de Kaggle no se
redistribuyen. Se corren en local con:  python -m pytest tests/test_conciliacion_v330.py -v
"""
import hashlib

import numpy as np
import pandas as pd
import pytest

from pipeline.build import construir
from tests.conftest import RAIZ, REAL_RAW

REF = RAIZ / "tests" / "referencia_v330"
SHA256_TRAIN = "a2ed2d7c6905d63a9361d8dd35bc06c8a597831f7185644e0f33ad7bfe20cc81"

pytestmark = pytest.mark.skipif(
    not (REAL_RAW / "train.csv").exists(),
    reason="Datos reales ausentes en data/raw/ (ver data/raw/README.md)",
)
TOL = dict(rtol=1e-9)


@pytest.fixture(scope="module")
def real():
    c = construir(REAL_RAW)
    yield c
    c.close()


def test_es_el_archivo_del_estudio():
    h = hashlib.sha256((REAL_RAW / "train.csv").read_bytes()).hexdigest()
    assert h == SHA256_TRAIN, "train.csv no es la versión usada en v3.3.0"


def test_kpis(real):
    ref = pd.read_csv(REF / "kpis_ejecutivos.csv").set_index("metrica").valor
    k = real.execute("SELECT * FROM mart_kpis").df().iloc[0]
    assert k.pedidos_totales == ref["Total órdenes"] == 119_557_485
    assert k.n_filas == ref["N observaciones"] == 456_548
    assert k.n_centros == ref["N centros únicos"] == 77
    assert k.n_comidas == ref["N comidas únicas"] == 51
    assert k.n_semanas == ref["Semanas cubiertas"] == 145
    assert round(k.precio_promedio_fila, 2) == ref["Precio promedio"]


def test_categorias(real):
    ref = pd.read_csv(REF / "demanda_por_categoria.csv").set_index("category").sort_index()
    sql = real.execute("SELECT * FROM mart_categorias").df().set_index("categoria").sort_index()
    assert list(sql.index) == list(ref.index)
    assert (sql.n_filas == ref.n_obs).all()
    assert (sql.pedidos == ref.demanda_total).all()
    np.testing.assert_allclose(sql.pedidos_promedio_fila, ref.demanda_promedio, **TOL)
    np.testing.assert_allclose(sql.precio_promedio, ref.precio_promedio, **TOL)
    np.testing.assert_allclose(sql.precio_base_promedio, ref.precio_base_promedio, **TOL)


def test_promociones(real):
    ref = pd.read_csv(REF / "efecto_promociones.csv").set_index(["emailer_for_promotion", "homepage_featured"])
    sql = real.execute("SELECT * FROM mart_promociones_matriz").df().set_index(["promo_email", "destacado_home"])
    sql.index.names = ref.index.names
    sql = sql.loc[ref.index]
    assert (sql.n_filas == ref.n_obs).all()
    np.testing.assert_allclose(sql.pedidos_promedio_fila, ref.demanda_promedio, **TOL)
    np.testing.assert_allclose(sql.precio_promedio, ref.precio_promedio, **TOL)


def test_tipos_centro(real):
    ref = pd.read_csv(REF / "comparacion_centros.csv").set_index("center_type")
    sql = real.execute("SELECT * FROM mart_tipos_centro").df().set_index("tipo_centro").loc[ref.index]
    assert (sql.n_filas == ref.n_obs).all()
    assert (sql.pedidos == ref.demanda_total).all()
    assert (sql.n_centros == ref.n_centros).all()
    np.testing.assert_allclose(sql.pedidos_promedio_fila, ref.demanda_promedio, **TOL)


def test_tendencia_semanal(real):
    ref = pd.read_csv(REF / "tendencia_semanal.csv").set_index("week")
    sql = real.execute("SELECT * FROM mart_tendencia_semanal").df().set_index("semana").loc[ref.index]
    assert len(ref) == 145
    assert (sql.n_filas == ref.n_obs).all()
    assert (sql.pedidos == ref.demanda_total).all()
    np.testing.assert_allclose(sql.precio_promedio, ref.precio_promedio, **TOL)
