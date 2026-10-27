"""Los CSV de Looker Studio salen completos, con tipos y rangos que Looker lee bien."""
import pandas as pd
import pytest

from pipeline.build import exportar as exportar_marts
from pipeline.exportar_looker import SALIDAS, exportar
from tests.conftest import RAIZ


@pytest.fixture(scope="module")
def looker(con, tmp_path_factory):
    base = tmp_path_factory.mktemp("exp")
    exportar_marts(con, base)
    return exportar(base / "marts", base / "looker"), base / "looker"


def test_genera_todos_los_archivos(looker):
    salidas, carpeta = looker
    assert set(salidas) == set(SALIDAS)
    for nombre in SALIDAS:
        assert (carpeta / f"{nombre}.csv").exists()


def test_totales_cuadran_con_kpis(looker, crudo):
    s, _ = looker
    total = crudo.num_orders.sum()
    assert s["ls_kpis"]["Pedidos"].item() == total
    for nombre in ["ls_tendencia", "ls_categorias", "ls_comidas_abc", "ls_centros", "ls_tipos_centro"]:
        assert s[nombre]["Pedidos"].sum() == total, nombre


def test_fracciones_entre_0_y_1(looker):
    s, _ = looker
    for nombre, col in [("ls_categorias", "Participación"), ("ls_comidas_abc", "% acumulado"),
                        ("ls_centros", "Participación"), ("ls_tipos_centro", "Participación")]:
        v = s[nombre][col]
        assert v.between(0, 1).all(), (nombre, col)
    assert s["ls_comidas_abc"]["% acumulado"].iloc[-1] == pytest.approx(1)
    co = s["ls_cohortes"]
    assert (co["Pares activos"] <= co["Pares observables"]).all()


def test_identificadores_como_texto(looker):
    s, carpeta = looker
    assert s["ls_centros"]["Centro"].str.startswith("Centro ").all()
    assert s["ls_comidas_abc"]["Comida"].str.startswith("Comida ").all()
    assert s["ls_tendencia"]["Año relativo"].str.startswith("Año ").all()
    # Cohorte con dos dígitos: así el orden alfabético es el numérico
    assert s["ls_cohortes"]["Cohorte"].str.match(r"^Cohorte \d{2}$").all()


def test_orden_promociones(looker):
    s, _ = looker
    assert list(s["ls_promociones"]["Tipo de promoción"]) == \
        ["Sin promoción", "Solo email", "Solo home", "Email + home"]


def test_csv_con_punto_decimal_y_utf8(looker):
    _, carpeta = looker
    texto = (carpeta / "ls_categorias.csv").read_text(encoding="utf-8")
    assert texto.startswith("Categoría,Ranking,Pedidos,Participación")
    assert "." in texto.splitlines()[1]
    assert "\r\n" not in texto
    # Ninguna celda con más de 6 decimales
    for f in carpeta.glob("*.csv"):
        df = pd.read_csv(f, dtype=str)
        dec = df.stack().str.extract(r"\.(\d+)$")[0].dropna().str.len()
        assert dec.empty or dec.max() <= 6, f.name


def test_error_claro_si_falta_un_mart(con, tmp_path):
    exportar_marts(con, tmp_path)
    (tmp_path / "marts" / "mart_cohortes.csv").unlink()
    with pytest.raises(RuntimeError, match="ls_cohortes"):
        exportar(tmp_path / "marts", tmp_path / "looker")


def test_datos_versionados_estan_al_dia(tmp_path):
    """Los CSV versionados de Looker corresponden a los marts versionados del repo."""
    marts = RAIZ / "exportes" / "marts"
    datos = RAIZ / "dashboard" / "looker" / "datos"
    if not (datos / "ls_kpis.csv").exists() or not (marts / "mart_kpis.csv").exists():
        pytest.skip("Sin datos versionados de Looker")
    exportar(marts, tmp_path)
    for nombre in SALIDAS:
        esperado = pd.read_csv(tmp_path / f"{nombre}.csv")
        actual = pd.read_csv(datos / f"{nombre}.csv")
        pd.testing.assert_frame_equal(actual, esperado, check_dtype=False, rtol=1e-6, obj=nombre)
