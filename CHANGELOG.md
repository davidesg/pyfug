# Changelog — pyfug

Gráficos Jenkins-Treadway para el análisis de series temporales: el puerto a
Python de fug (C, Treadway y Guerrero). Registro de defectos en `bugs/`.
Etiquetas de publicación: `v*`.

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
