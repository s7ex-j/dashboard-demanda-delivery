"""
Prepara los datos de Looker Studio a partir de los marts exportados por el pipeline.

Lee   exportes/marts/*.csv            (los genera: python -m pipeline.build)
Crea  dashboard/looker/datos/ls_*.csv (se versionan: son agregados, sin filas del dataset)

Qué cambia respecto a los marts:
  - Solo las columnas que usa el dashboard, con nombres en español listos para mostrar
    (Looker Studio toma el encabezado como nombre del campo; así no hay que renombrar a mano).
  - Identificadores como texto ("Centro 13", "Comida 2290", "Año 1") para que Looker no los sume.
  - Columnas de orden explícitas (Orden, Puesto) donde el orden alfabético no sirve.
  - Decimales redondeados a 6 cifras: los CSV no cambian por el último decimal de una suma en
    paralelo, y Looker los lee igual con punto decimal en cualquier configuración regional.
  - Las tasas y participaciones quedan como fracción (0,25 = 25 %): es lo que espera el tipo
    Porcentaje de Looker Studio.

Uso:  python -m pipeline.exportar_looker
      python -m pipeline.exportar_looker --marts otra/carpeta --destino otra/salida
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DECIMALES = 6


def _texto_id(prefijo: str, serie: pd.Series, ancho: int = 0) -> pd.Series:
    return prefijo + serie.astype(int).astype(str).str.zfill(ancho)


def _kpis(m: dict[str, pd.DataFrame]) -> pd.DataFrame:
    k = m["mart_kpis"]
    return pd.DataFrame({
        "Filas": k.n_filas,
        "Pedidos": k.pedidos_totales,
        "Ingreso estimado": k.ingreso_estimado,
        "Precio por fila": k.precio_promedio_fila,
        "Precio por pedido": k.precio_promedio_ponderado,
        "Centros": k.n_centros,
        "Comidas": k.n_comidas,
        "Semanas": k.n_semanas,
        "Pedidos por semana": k.pedidos_por_semana,
    })


def _tendencia(m):
    t = m["mart_tendencia_semanal"]
    return pd.DataFrame({
        "Semana": t.semana,
        "Año relativo": _texto_id("Año ", t.anio_relativo),
        "Semana del año": t.semana_del_anio,
        "Trimestre": t.etiqueta_trimestre,
        "Pedidos": t.pedidos,
        "Media móvil 4 semanas": t.media_movil_4s,
        "Pedidos semana anterior": t.pedidos_semana_anterior,
        "Var. semanal": t.var_semanal_pct,
        "Pedidos hace 52 semanas": t.pedidos_hace_52s,
        "Var. interanual": t.var_interanual_pct,
        "Filas con promoción": t.pct_filas_con_promo,
    })


def _categorias(m):
    c = m["mart_categorias"]
    return pd.DataFrame({
        "Categoría": c.categoria,
        "Ranking": c.ranking_pedidos,
        "Pedidos": c.pedidos,
        "Participación": c.participacion_pedidos,
        "Ingreso estimado": c.ingreso_estimado,
        "Precio por pedido": c.ingreso_estimado / c.pedidos,
        "Pedidos por fila": c.pedidos_promedio_fila,
        "Comidas": c.n_comidas,
    }).sort_values("Ranking")


def _comidas_abc(m):
    a = m["mart_comidas_abc"]
    return pd.DataFrame({
        "Puesto": a.ranking_global,
        "Comida": _texto_id("Comida ", a.meal_id),
        "Categoría": a.categoria,
        "Cocina": a.cocina,
        "Clase ABC": a.clase_abc,
        "Pedidos": a.pedidos,
        "Participación": a.participacion,
        "% acumulado": a.participacion_acumulada,
    }).sort_values("Puesto")


ORDEN_PROMO = {"Sin promoción": 1, "Solo email": 2, "Solo home": 3, "Email + home": 4}


def _promociones(m):
    p = m["mart_promociones_matriz"]
    return pd.DataFrame({
        "Tipo de promoción": p.tipo_promocion,
        "Orden": p.tipo_promocion.map(ORDEN_PROMO),
        "Filas": p.n_filas,
        "Pedidos por fila": p.pedidos_promedio_fila,
        "Precio promedio": p.precio_promedio,
    }).sort_values("Orden")


def _indice_promociones(m):
    i = m["mart_promociones_indice"]
    return pd.DataFrame({
        "Categoría": i.categoria,
        "Tipo de promoción": i.tipo_promocion,
        "Índice vs. sin promoción": i.indice_vs_sin_promo,
        "Índice mediano": i.indice_mediano_vs_sin_promo,
        "Filas": i.n_filas,
    })


def _centros(m):
    c = m["mart_centros"]
    return pd.DataFrame({
        "Centro": _texto_id("Centro ", c.center_id),
        "Tipo de centro": c.tipo_centro,
        "Región": _texto_id("Región ", c.codigo_region),
        "Área operativa": c.area_operativa,
        "Pedidos": c.pedidos,
        "Participación": c.participacion_pedidos,
        "Ranking": c.ranking_global,
        "Ranking en su tipo": c.ranking_en_tipo,
        "Cuartil": _texto_id("Q", c.cuartil),
        "Pedidos por semana activa": c.pedidos_por_semana_activa,
    }).sort_values("Ranking")


def _tipos_centro(m):
    t = m["mart_tipos_centro"]
    return pd.DataFrame({
        "Tipo de centro": t.tipo_centro,
        "Centros": t.n_centros,
        "Pedidos": t.pedidos,
        "Participación": t.participacion_pedidos,
        "Pedidos por fila": t.pedidos_promedio_fila,
    })


def _cohortes(m):
    c = m["mart_cohortes"]
    # Sin columna de tasa a propósito: en Looker se calcula SUM(activos) / SUM(observables),
    # que da el valor correcto con cualquier agregación (ver ESPECIFICACION.md).
    return pd.DataFrame({
        "Cohorte": _texto_id("Cohorte ", c.cohorte_trimestre, 2),
        "Trimestres desde la primera venta": c.periodo_desde_inicio,
        "Pares observables": c.pares_observables,
        "Pares activos": c.pares_activos,
    })


def _bandas_precio(m):
    b = m["mart_bandas_precio"]
    return pd.DataFrame({
        "Categoría": b.categoria,
        "Decil de precio": b.decil_precio,
        "Precio mínimo": b.precio_min,
        "Precio máximo": b.precio_max,
        "Precio promedio": b.precio_promedio,
        "Pedidos por fila": b.pedidos_promedio_fila,
        "Mediana de pedidos por fila": b.pedidos_mediana_fila,
        "Filas": b.n_filas,
    })


def _elasticidad_rcs(m):
    r = m["mart_elasticidad_rcs"]
    return pd.DataFrame({"Precio": r.precio, "Elasticidad": r.elasticidad_rcs})


def _elasticidad_categoria(m):
    e = m["mart_elasticidad_categoria"]
    return pd.DataFrame({"Categoría": e.categoria, "Elasticidad": e.elasticidad}) \
        .sort_values("Elasticidad")


def _calidad(m):
    q = m["calidad_resultados"]
    return pd.DataFrame({
        "Regla": q.regla,
        "Descripción": q.descripcion,
        "Filas con error": q.filas_con_error,
    }).sort_values("Regla")


SALIDAS = {
    "ls_kpis": _kpis,
    "ls_tendencia": _tendencia,
    "ls_categorias": _categorias,
    "ls_comidas_abc": _comidas_abc,
    "ls_promociones": _promociones,
    "ls_indice_promociones": _indice_promociones,
    "ls_centros": _centros,
    "ls_tipos_centro": _tipos_centro,
    "ls_cohortes": _cohortes,
    "ls_bandas_precio": _bandas_precio,
    "ls_elasticidad_rcs": _elasticidad_rcs,
    "ls_elasticidad_categoria": _elasticidad_categoria,
    "ls_calidad": _calidad,
}


def leer_marts(carpeta: Path) -> dict[str, pd.DataFrame]:
    marts = {p.stem: pd.read_csv(p) for p in sorted(carpeta.glob("*.csv"))}
    if not marts:
        raise FileNotFoundError(f"No hay CSV en {carpeta}. Corre antes: python -m pipeline.build")
    return marts


def exportar(marts_dir: Path, destino: Path) -> dict[str, pd.DataFrame]:
    marts = leer_marts(marts_dir)
    destino.mkdir(parents=True, exist_ok=True)
    salidas = {}
    for nombre, f in SALIDAS.items():
        try:
            df = f(marts)
        except (KeyError, AttributeError) as e:
            raise RuntimeError(f"{nombre}: falta un mart o una columna ({e}). "
                               "¿Cambió el SQL? Actualiza pipeline/exportar_looker.py") from e
        df = df.round(DECIMALES).reset_index(drop=True)
        df.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8", lineterminator="\n")
        salidas[nombre] = df
    return salidas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marts", type=Path, default=RAIZ / "exportes" / "marts")
    ap.add_argument("--destino", type=Path, default=RAIZ / "dashboard" / "looker" / "datos")
    a = ap.parse_args(argv)
    salidas = exportar(a.marts, a.destino)
    for nombre, df in salidas.items():
        print(f"  {nombre + '.csv':<30} {len(df):>4} filas · {len(df.columns):>2} columnas")
    print(f"Listo: {len(salidas)} archivos en {a.destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
