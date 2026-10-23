"""
Las reglas de calidad pasan con datos limpios y, sobre todo, FALLAN cuando se
introduce el error que cada una debe detectar. Un test de calidad que nunca
falla no prueba nada.
"""
import shutil

import pandas as pd
import pytest

from pipeline.build import ErrorCalidad, construir, verificar_calidad
from tests.conftest import FIXTURE_RAW


def test_todas_las_reglas_pasan_con_datos_limpios(con):
    filas = verificar_calidad(con)
    assert len(filas) == 17
    assert all(n == 0 for _, _, n in filas)


def _copia(tmp_path):
    destino = tmp_path / "raw"
    shutil.copytree(FIXTURE_RAW, destino)
    return destino


def _errores(raw):
    c = construir(raw)
    try:
        return dict(c.execute("SELECT regla, filas_con_error FROM calidad_resultados").fetchall())
    finally:
        c.close()


def _mutar_train(raw, f):
    t = pd.read_csv(raw / "train.csv")
    t = f(t)
    t.to_csv(raw / "train.csv", index=False)


@pytest.mark.parametrize("nombre, mutacion, regla, esperado", [
    ("fila duplicada",
     lambda t: pd.concat([t, t.iloc[[0]].assign(id=9_999_999)]), "pk_hechos_unica", 1),
    ("id repetido",
     lambda t: t.assign(id=t.id.where(t.index != 1, t.id.iloc[0])), "id_unico", 1),
    ("comida inexistente",
     lambda t: t.assign(meal_id=t.meal_id.where(t.index > 2, 9999)), "fk_comida", 3),
    ("centro inexistente",
     lambda t: t.assign(center_id=t.center_id.where(t.index > 0, 999)), "fk_centro", 1),
    ("semana faltante",
     lambda t: t[t.week != 30], "semanas_contiguas", 1),
    ("pedidos cero",
     lambda t: t.assign(num_orders=t.num_orders.where(t.index > 1, 0)), "pedidos_positivos", 2),
    ("precio negativo",
     lambda t: t.assign(checkout_price=t.checkout_price.where(t.index > 0, -5.0)), "precios_positivos", 1),
    ("bandera 2",
     lambda t: t.assign(homepage_featured=t.homepage_featured.where(t.index > 0, 2)), "banderas_binarias", 1),
    ("nulo en precio base",
     lambda t: t.assign(base_price=t.base_price.where(t.index > 0, None)), "hechos_sin_nulos", 1),
])
def test_cada_regla_detecta_su_error(tmp_path, nombre, mutacion, regla, esperado):
    raw = _copia(tmp_path)
    _mutar_train(raw, mutacion)
    errores = _errores(raw)
    assert errores[regla] == esperado, f"{nombre}: {errores}"


def test_dimension_con_nulo_y_clave_repetida(tmp_path):
    raw = _copia(tmp_path)
    m = pd.read_csv(raw / "meal_info.csv")
    m.loc[0, "cuisine"] = None
    pd.concat([m, m.iloc[[1]]]).to_csv(raw / "meal_info.csv", index=False)
    errores = _errores(raw)
    assert errores["dimensiones_sin_nulos"] == 1
    assert errores["pk_dim_comida_unica"] == 1


def test_verificar_calidad_detiene_el_pipeline(tmp_path):
    raw = _copia(tmp_path)
    _mutar_train(raw, lambda t: t[t.week != 10])
    c = construir(raw)
    with pytest.raises(ErrorCalidad, match="semanas_contiguas"):
        verificar_calidad(c)
    c.close()


def test_falta_un_archivo(tmp_path):
    raw = _copia(tmp_path)
    (raw / "meal_info.csv").unlink()
    with pytest.raises(FileNotFoundError, match="meal_info.csv"):
        construir(raw)
