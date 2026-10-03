# Changelog — pyfug

Gráficos Jenkins-Treadway para el análisis de series temporales: el puerto a
Python de fug (C, Treadway y Guerrero). Registro de defectos en `bugs/`.
Etiquetas de publicación: `v*`.

## Unreleased

**The series + acf/pacf figure has fug C's geometry** (BUG-0007).
`plot_combined` now uses the C canvas in points, its panel positions, font
sizes and line widths, and places the title as GraphMaker does: left-aligned
from 80 % of the series panel. The acf/pacf axis stays adaptive.

**The seasonal year axis is aligned as in fug C** (BUG-0006). The axis
starts at the first period of the series' starting year, with a line and a
label every 2 years from that year. This is the alignment Treadway
corrected. It used to start at the preceding even year, and used a step of 1
in short series.

**Quarterly year labels have two digits, as in GraphMaker** (BUG-0005).
- A quarterly series labels every other year as `96`, `98`, `00`. With full
  years the labels overlapped once a series passed about 25 years.
- Monthly series keep the full year, as Treadway approved, and switch to two
  digits only if the labels would overlap.
- Annual series keep the full year every 20 years.

**Without statsmodels.** ACF, PACF and Ljung-Box are computed in
`pyfug.statistics` with numpy and scipy, with the same formulas as fue's
(`fue.acf`, `fue.pacf`, `fue.ljung_box`): the ACF to 2e-16, the PACF
(Yule-Walker by Durbin-Levinson) to 5e-14, and they also reproduce
statsmodels' `acf(adjusted=…)`, `pacf(method="ywm")` and `acorr_ljungbox`.
statsmodels leaves the dependencies. `jupyter.from_statsmodels_result` still
reads a statsmodels result if one is passed; it never imported the package.

## 2.0.1 — 2026-09-25

**La figura combinada se rompía en TODA serie anual** (BUG-0002). `x_pad` sólo se
asignaba en la rama de frecuencia > 1 y se usaba siempre: `plot_combined` lanzaba
`UnboundLocalError` con cualquier serie de frecuencia 1. La 2.0.0 publicada lo
tiene. El eje anual sigue ahora el convenio de fug C (el origen de los rótulos
es `begyear − outyear`, marcas cada 20 años).

Se estrena el registro de defectos (`bugs/`). Quedan **abiertos**, y esta versión
no los arregla:

* **BUG-0001** — los años del eje se solapan en series trimestrales largas.
* **BUG-0003** — una serie diferenciada con `diffgraph` se fecha dos veces: el
  primer punto se corre d + D·s periodos de más. No afecta a art, que llama a
  `plot_combined` con la serie ya fechada.
* **BUG-0004** — importar pyfug reescribe los `rcParams` globales de matplotlib
  (dpi, tamaño de letra, `savefig.bbox`…) y cambia las figuras de todo lo que se
  dibuje después en el mismo proceso.

*Aviso de empaquetado:* la versión está escrita dos veces, en `pyproject.toml` y
en `pyfug/__init__.py`. Es el defecto que fue corrigió en su BUG-0016 (su
`__version__` se quedó tres versiones atrás); aquí se han subido las dos a mano.

## 2.0.0

Primera versión publicada en PyPI.
