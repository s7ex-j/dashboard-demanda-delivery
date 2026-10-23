"""
Genera un dataset SINTÉTICO y pequeño con el mismo esquema que los CSV de Kaggle.

Sirve para que los tests y GitHub Actions corran sin descargar ni redistribuir los
datos reales. Los números no significan nada: solo están pensados para ejercitar
los casos difíciles del SQL (pares que empiezan tarde, pares que dejan de vender,
huecos dentro de un par, las cuatro combinaciones de promoción y empates de precio).

Uso: python tests/fixtures/generar_fixture.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DESTINO = Path(__file__).resolve().parent / "raw"
SEMILLA = 20261023
N_SEMANAS = 60


def generar() -> None:
    rng = np.random.default_rng(SEMILLA)

    comidas = pd.DataFrame({
        "meal_id": [1001, 1002, 1003, 1004, 1005, 1006],
        "category": ["Beverages", "Beverages", "Pizza", "Pizza", "Soup", "Soup"],
        "cuisine": ["Thai", "Indian", "Italian", "Italian", "Thai", "Continental"],
    })
    centros = pd.DataFrame({
        "center_id": [10, 20, 30, 40],
        "city_code": [590, 590, 526, 647],
        "region_code": [56, 56, 34, 77],
        "center_type": ["TYPE_A", "TYPE_B", "TYPE_C", "TYPE_A"],
        "op_area": [4.0, 3.5, 2.0, 6.3],
    })

    precio_ref = {1001: 150.0, 1002: 180.0, 1003: 600.0, 1004: 650.0, 1005: 300.0, 1006: 320.0}
    escala = {10: 1.0, 20: 1.4, 30: 0.6, 40: 2.0}

    filas = []
    for c in centros.center_id:
        for m in comidas.meal_id:
            # Semana de inicio variada para tener varias cohortes
            inicio = 1 if (c + m) % 3 else int(rng.integers(5, 40))
            # Algunos pares dejan de vender a mitad de periodo
            fin = N_SEMANAS if (c * m) % 5 else int(rng.integers(inicio + 10, N_SEMANAS + 1))
            for w in range(inicio, fin + 1):
                if rng.random() < 0.08:          # huecos esporádicos dentro del par
                    continue
                email = int(rng.random() < 0.15)
                home = int(rng.random() < 0.2)
                base = precio_ref[m]
                # Precios redondeados a múltiplos de 5 para forzar empates en NTILE
                checkout = round(base * rng.uniform(0.8, 1.1) / 5) * 5
                demanda = escala[c] * 200 * (base / checkout) ** 1.2
                demanda *= 1 + 0.6 * email + 0.4 * home
                demanda *= 1 + 0.2 * np.sin(w / 8)
                pedidos = max(13, int(round(demanda * rng.uniform(0.85, 1.15))))
                filas.append((w, c, m, float(checkout), float(base), email, home, pedidos))

    pedidos = pd.DataFrame(filas, columns=[
        "week", "center_id", "meal_id", "checkout_price", "base_price",
        "emailer_for_promotion", "homepage_featured", "num_orders",
    ]).sort_values(["week", "center_id", "meal_id"]).reset_index(drop=True)
    pedidos.insert(0, "id", np.arange(1_000_000, 1_000_000 + len(pedidos)))

    assert set(range(1, N_SEMANAS + 1)) <= set(pedidos.week), "Hay semanas sin datos"
    assert pedidos.groupby(["emailer_for_promotion", "homepage_featured"]).size().shape[0] == 4

    DESTINO.mkdir(parents=True, exist_ok=True)
    pedidos.to_csv(DESTINO / "train.csv", index=False, lineterminator="\n")
    comidas.to_csv(DESTINO / "meal_info.csv", index=False, lineterminator="\n")
    centros.to_csv(DESTINO / "fulfilment_center_info.csv", index=False, lineterminator="\n")
    print(f"Fixture: {len(pedidos)} filas, {N_SEMANAS} semanas -> {DESTINO}")


if __name__ == "__main__":
    generar()
