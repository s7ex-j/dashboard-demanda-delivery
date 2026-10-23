"""
Cada mart se recalcula en pandas, sin SQL, y se compara con DuckDB.
Si la lógica de una ventana (LAG, marcos ROWS, NTILE, particiones) está mal,
los dos caminos no coinciden.
"""
import numpy as np
import pandas as pd
import pytest

from tests.conftest import df

TOL = dict(rtol=1e-9, atol=1e-9)


def test_kpis(con, crudo):
    k = df(con, "SELECT * FROM mart_kpis").iloc[0]
    assert k.n_filas == len(crudo)
    assert k.pedidos_totales == crudo.num_orders.sum()
    assert k.n_centros == crudo.center_id.nunique()
    assert k.n_comidas == crudo.meal_id.nunique()
    assert k.n_semanas == crudo.week.nunique()
    ingreso = (crudo.num_orders * crudo.checkout_price).sum()
    np.testing.assert_allclose(k.ingreso_estimado, ingreso, **TOL)
    np.testing.assert_allclose(k.precio_promedio_ponderado, ingreso / crudo.num_orders.sum(), **TOL)
    np.testing.assert_allclose(k.precio_promedio_fila, crudo.checkout_price.mean(), **TOL)


def test_tendencia_semanal(con, crudo):
    sql = df(con, "SELECT * FROM mart_tendencia_semanal ORDER BY semana").set_index("semana")
    s = crudo.groupby("week").num_orders.sum()
    s = s.reindex(range(s.index.min(), s.index.max() + 1))
    esperado = pd.DataFrame({
        "pedidos": s,
        "pedidos_semana_anterior": s.shift(1),
        "var_semanal_pct": s / s.shift(1) - 1,
        "media_movil_4s": s.rolling(4, min_periods=4).mean(),
        "pedidos_hace_52s": s.shift(52),
        "var_interanual_pct": s / s.shift(52) - 1,
    })
    for col in esperado:
        np.testing.assert_allclose(sql[col].astype(float), esperado[col].astype(float),
                                   equal_nan=True, err_msg=col, **TOL)
    # El acumulado se reinicia al empezar cada año relativo (semana 53)
    anio = (s.index - 1) // 52 + 1
    np.testing.assert_allclose(sql.pedidos_acumulados_anio, s.groupby(anio).cumsum(), **TOL)
    assert sql.loc[53, "pedidos_acumulados_anio"] == s.loc[53]
    # Las primeras 52 semanas no tienen comparación interanual
    assert sql.loc[:52, "var_interanual_pct"].isna().all()
    assert sql.loc[53:, "var_interanual_pct"].notna().all()


def test_categorias(con, crudo):
    sql = df(con, "SELECT * FROM mart_categorias").set_index("categoria").sort_index()
    sql.index.name = "category"
    g = crudo.groupby("category")
    assert (sql.pedidos == g.num_orders.sum()).all()
    np.testing.assert_allclose(sql.participacion_pedidos.sum(), 1.0, **TOL)
    rank = g.num_orders.sum().rank(ascending=False, method="min")
    assert (sql.ranking_pedidos == rank).all()
    np.testing.assert_allclose(sql.precio_promedio, g.checkout_price.mean(), **TOL)


def test_comidas_abc(con, crudo):
    sql = df(con, "SELECT * FROM mart_comidas_abc ORDER BY ranking_global").set_index("meal_id")
    tot = crudo.groupby("meal_id").num_orders.sum().reset_index()
    tot = tot.sort_values(["num_orders", "meal_id"], ascending=[False, True]).set_index("meal_id")
    part = tot.num_orders / tot.num_orders.sum()
    acum_previo = part.cumsum() - part
    abc = np.where(acum_previo < 0.80, "A", np.where(acum_previo < 0.95, "B", "C"))
    assert list(sql.index) == list(tot.index)
    assert list(sql.clase_abc) == list(abc)
    assert sql.clase_abc.iloc[0] == "A"                       # la primera siempre es A
    np.testing.assert_allclose(sql.participacion_acumulada.iloc[-1], 1.0, **TOL)
    cat = crudo.drop_duplicates("meal_id").set_index("meal_id").category
    rk = tot.num_orders.groupby(cat).rank(ascending=False, method="dense")
    assert (sql.ranking_en_categoria == rk.loc[sql.index]).all()


def test_promociones_matriz(con, crudo):
    sql = df(con, "SELECT * FROM mart_promociones_matriz")
    assert len(sql) == 4
    g = crudo.groupby(["emailer_for_promotion", "homepage_featured"]).num_orders
    for _, r in sql.iterrows():
        np.testing.assert_allclose(r.pedidos_promedio_fila, g.mean()[(r.promo_email, r.destacado_home)], **TOL)
    assert sql.n_filas.sum() == len(crudo)


def test_promociones_indice(con, crudo):
    sql = df(con, "SELECT * FROM mart_promociones_indice").set_index(["categoria", "tipo_promocion"])
    d = crudo.copy()
    sin = (d.emailer_for_promotion == 0) & (d.homepage_featured == 0)
    base = d[sin].groupby(["center_id", "meal_id"]).num_orders.mean().rename("base")
    d = d.join(base, on=["center_id", "meal_id"])
    d = d[~sin & d.base.notna()]
    d["tipo"] = np.select(
        [(d.emailer_for_promotion == 1) & (d.homepage_featured == 1), d.emailer_for_promotion == 1],
        ["Email + home", "Solo email"], "Solo home")
    d["indice"] = d.num_orders / d.base
    esp = d.groupby(["category", "tipo"]).indice.agg(["mean", "median", "size"])
    esp.index.names = ["categoria", "tipo_promocion"]
    esp = esp.loc[sql.index]
    np.testing.assert_allclose(sql.indice_vs_sin_promo, esp["mean"], **TOL)
    np.testing.assert_allclose(sql.indice_mediano_vs_sin_promo, esp["median"], **TOL)
    assert (sql.n_filas == esp["size"]).all()


def test_centros(con, crudo):
    sql = df(con, "SELECT * FROM mart_centros").set_index("center_id")
    tot = crudo.groupby("center_id").num_orders.sum()
    assert (sql.pedidos == tot.loc[sql.index]).all()
    assert (sql.ranking_global == tot.rank(ascending=False, method="min").loc[sql.index]).all()
    tipo = crudo.drop_duplicates("center_id").set_index("center_id").center_type
    rk_tipo = tot.groupby(tipo).rank(ascending=False, method="min")
    assert (sql.ranking_en_tipo == rk_tipo.loc[sql.index]).all()
    # NTILE(4) con 4 centros: un centro por cuartil, ordenados por pedidos
    assert list(sql.sort_values("ranking_global").cuartil) == [1, 2, 3, 4]
    semanas = crudo.groupby("center_id").week.nunique()
    np.testing.assert_allclose(sql.pedidos_por_semana_activa, (tot / semanas).loc[sql.index], **TOL)


def test_tipos_centro(con, crudo):
    sql = df(con, "SELECT * FROM mart_tipos_centro").set_index("tipo_centro")
    g = crudo.groupby("center_type")
    assert (sql.pedidos == g.num_orders.sum()).all()
    assert (sql.n_centros == g.center_id.nunique()).all()


def _ntile(n, k):
    """Asignación de NTILE de SQL: los primeros n % k grupos llevan una fila más."""
    base, resto = divmod(n, k)
    tamanos = [base + (1 if i < resto else 0) for i in range(k)]
    return np.repeat(np.arange(1, k + 1), tamanos)


def test_bandas_precio(con, crudo):
    sql = df(con, "SELECT * FROM mart_bandas_precio").set_index(["categoria", "decil_precio"])
    partes = []
    todos = crudo.sort_values(["checkout_price", "id"]).assign(categoria="Todas")
    todos["decil"] = _ntile(len(todos), 10)
    partes.append(todos)
    for cat, g in crudo.groupby("category"):
        g = g.sort_values(["checkout_price", "id"]).assign(categoria=cat)
        g["decil"] = _ntile(len(g), 10)
        partes.append(g)
    e = pd.concat(partes).groupby(["categoria", "decil"]).agg(
        n=("num_orders", "size"), media=("num_orders", "mean"),
        pmin=("checkout_price", "min"), pmax=("checkout_price", "max"))
    e.index.names = sql.index.names
    e = e.loc[sql.index]
    assert (sql.n_filas == e.n).all()
    np.testing.assert_allclose(sql.pedidos_promedio_fila, e.media, **TOL)
    assert (sql.precio_min == e.pmin).all() and (sql.precio_max == e.pmax).all()
    assert len(sql) == 10 * (crudo.category.nunique() + 1)


def test_cohortes(con, crudo):
    sql = df(con, "SELECT * FROM mart_cohortes").set_index(["cohorte_trimestre", "periodo_desde_inicio"])
    semana_max = crudo.week.max()
    inicio = crudo.groupby(["center_id", "meal_id"]).week.min().rename("inicio")
    d = crudo.join(inicio, on=["center_id", "meal_id"])
    d["periodo"] = (d.week - d.inicio) // 13
    activos = set(map(tuple, d[["center_id", "meal_id", "periodo"]].drop_duplicates().values))
    filas = []
    for (c, m), s0 in inicio.items():
        for k in range((semana_max - s0 + 1) // 13):
            assert s0 + 13 * k + 12 <= semana_max          # el bloque cae completo
            filas.append(((s0 - 1) // 13 + 1, k, (c, m, k) in activos))
    e = pd.DataFrame(filas, columns=["cohorte", "periodo", "activo"]) \
          .groupby(["cohorte", "periodo"]).activo.agg(["size", "sum"])
    e.index.names = sql.index.names
    assert list(sql.index) == list(e.index)
    assert (sql.pares_observables == e["size"]).all()
    assert (sql.pares_activos == e["sum"]).all()
    # En el periodo 0 todo par está activo por definición
    assert (sql.xs(0, level="periodo_desde_inicio").tasa_retencion == 1).all()
    # El fixture tiene pares que dejan de vender: la retención baja de 1 en algún punto
    assert (sql.tasa_retencion < 1).any()


def test_referencias_estudio(con):
    rcs = df(con, "SELECT * FROM mart_elasticidad_rcs ORDER BY precio")
    assert len(rcs) == 22
    # Valores publicados en v3.3.0: no deben cambiar al copiarse aquí
    assert rcs.loc[rcs.precio == 125, "elasticidad_rcs"].item() == pytest.approx(0.0358)
    assert rcs.especificacion.str.contains("RCS").all()
    cat = df(con, "SELECT * FROM mart_elasticidad_categoria")
    assert len(cat) == 14 and cat.nota.str.contains("no es una recomendación").all()
