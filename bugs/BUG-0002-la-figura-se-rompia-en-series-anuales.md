---
id: BUG-0002
title: La figura combinada se rompía en TODA serie anual — `x_pad` sólo se asignaba en la rama f>1 y se usaba siempre
status: fixed
severity: high
component: graphics
found_in: 2.0.0
fixed_in: 2.0.1
reported: 2026-09-10
reporter: David
tags:
  - graphics
  - frecuencia-anual
references:
  - pyfug BUG-0001 (el mismo `plot_combined`, el mismo eje temporal)
---

## Summary

`plot_combined` —la figura estándar de la escuela: serie tipificada más acf y
pacf— **lanzaba `UnboundLocalError` con cualquier serie anual**. No dibujaba una
figura fea: no dibujaba ninguna.

`x_pad` se calcula dentro de la rama `f > 1`:

```python
if f > 1:
    ...
    x_pad = max(0.3 / f, x0 - first_yr + 0.5 / f)
else:
    step = 10                      # ← la rama anual no lo asignaba
    ...
ax_s.set_xlim(xs[0] - x_pad, xs[-1] + 0.3 / f)   # ← y aquí se usa siempre
```

## Impact

Toda serie anual, en todo lo que llame a `plot_combined`. Incluye la figura que
devuelven `identification_analysis` y `guided_identification` de `art`, que es
la primera que se mira de una serie. Las anuales son minoría en la práctica
docente frente a mensuales y trimestrales, y por eso pudo durar hasta 2.0.0.

## Reproduction

```python
import matplotlib; matplotlib.use("Agg")
import numpy as np
from pyfug.core import Tseries
from pyfug.graphics import plot_combined

rng = np.random.default_rng(0)
y = 100 * np.exp(np.cumsum(0.02 + 0.05 * rng.standard_normal(40)))

for freq, etiqueta in ((1, "ANUAL"), (4, "TRIMESTRAL"), (12, "MENSUAL")):
    s = Tseries(name=etiqueta, nobs=len(y), freq=freq, begyear=1980,
                begtime=1, data=np.asarray(y, dtype=float))
    try:
        plot_combined(s); print(f"{etiqueta}: sin error")
    except Exception as e:
        print(f"{etiqueta}: {type(e).__name__}: {e}")
```

Antes:

    ANUAL       UnboundLocalError: cannot access local variable 'x_pad'…
    TRIMESTRAL  sin error
    MENSUAL     sin error

## Root cause

`pyfug/graphics/combined.py`, `plot_combined`. Una variable calculada en una
rama y consumida fuera de las dos. Es el mismo bloque de código que BUG-0001 —el
eje temporal— y la misma causa de fondo: **el eje temporal se construye con
ramas independientes por frecuencia**, cada una con sus propias decisiones, y
nada obliga a que las dos dejen definido lo que la salida común necesita.

## Fix

Tres líneas: asignar `x_pad = 0.3 / f` en la rama anual, con el comentario que
dice por qué está ahí.

El arreglo estaba **ya aplicado en el árbol de trabajo**, sin informe y sin
prueba, cuando se montó este registro. Éste es el informe.

## Validation

`tests/test_bug_0002_frecuencia_anual.py` — las tres frecuencias por la misma
puerta, y la anual la primera. Falla con `UnboundLocalError` sin el arreglo.

Y una nota para BUG-0001: cuando se rehaga el paso del eje temporal, **las dos
ramas tienen que salir por el mismo sitio**. Si esa reescritura vuelve a dejar
una variable definida en una sola rama, este defecto vuelve.
