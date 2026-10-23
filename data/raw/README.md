# Datos originales (no incluidos)

Este repositorio no redistribuye los datos. Son los de la competencia *Food Demand Forecasting*
(Genpact / Analytics Vidhya), publicados en Kaggle:
<https://www.kaggle.com/datasets/kannanaikkal/food-demand-forecasting>

Pon aquí estos tres archivos, sin cambiarles el nombre:

| Archivo | SHA-256 de la versión usada |
|---|---|
| `train.csv` | `a2ed2d7c6905d63a9361d8dd35bc06c8a597831f7185644e0f33ad7bfe20cc81` |
| `meal_info.csv` | `9d8045af391c492f531c928d7f3d58581c80d0594776d1f4e53c8b29bbff8f75` |
| `fulfilment_center_info.csv` | `c874f74fa392b2c4dd24a167f32a5bee68a444b8bf151acf295cd5d66aa0517f` |

Formas de conseguirlos:

1. **Si ya tienes el estudio de elasticidad**, cópialos desde su carpeta `data/raw/` (en `cmd`):
   ```
   copy ..\demanda-delivery-v2\data\raw\*.csv data\raw\
   ```
2. **Con la API de Kaggle** (credenciales en `%USERPROFILE%\.kaggle\kaggle.json`, nunca en el repo):
   ```
   kaggle datasets download -d kannanaikkal/food-demand-forecasting -p data/raw --unzip
   ```
3. **A mano**, desde la página de Kaggle.

Para comprobar el hash en Windows: `certutil -hashfile data\raw\train.csv SHA256`.
`tests/test_conciliacion_v330.py` también lo verifica.
