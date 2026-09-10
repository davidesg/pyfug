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

## Fix — el convenio de fug C, no un parche

El primer arreglo, que estaba **ya aplicado en el árbol de trabajo** sin informe
y sin prueba cuando se montó este registro, asignaba `x_pad = 0.3 / f` en la
rama anual. Quita el error y **no es el convenio**. Decisión del analista:
seguir el de `fug` C en su última versión (`fug-1.12.02_win`).

El convenio sale de cinco sitios:

```c
fug.c:332              ornsop  = nrdiff + freq*nadiff
fug.c:382              timeout = ornsop + ser->outyear          /* sólo f == 1 */
fug.c:404              ... , ser->begyear - ser->outyear , ...  /* sólo f == 1 */
gnuplot_i.c:1275       plot [-timeout : n-1][-AbsMax : AbsMax]
gnuplot_graphics.c
  :493-497             líneas verticales en  -tmornsop + 2*f*i*10,  i = 1 …
  :510-514             rótulos  tsby + 2*i*10  en esas posiciones,  i = 0 …
```

Con `f == 1`, `2*f*i*10` es **cada 20 años**, no cada 10. Y el rótulo i-ésimo
es `tsby + 20i`, con `tsby = begyear - outyear`: el primero es el **origen**,
no el múltiplo del paso que quede por debajo.

**Y `outyear` es la pieza que faltaba.** «Year before graph (only yearly data)»
(`fug.h:58`), leída del `.inp` (`fug.c:231`). Es un margen izquierdo **en años,
declarado por el usuario**, que existe **sólo** en las anuales, y C lo usa dos
veces: alarga el eje por la izquierda y corre el origen de los rótulos. `pyfug`
la llevaba en el `Tseries` —está en su firma— y `plot_combined` **no la miraba**.
De ahí sale el hueco de la izquierda: no había que inventarlo con un pad.

Así que el arreglo no es asignar `x_pad`: es que la rama anual haga lo que hace
C. El eje arranca en el primer rótulo, `begyear - outyear`, y los datos quedan
inset por lo que se comió la diferenciación.

## Lo que esto deja a la vista para BUG-0001

Con el convenio aplicado, una serie anual de 15 años sale con **un solo
rótulo** — y es correcto, es lo que hace C (`i = 0 … (n+tmornsop-1)/20` da 0).

Es el **mismo defecto que BUG-0001, por el otro extremo**: el paso del eje está
fijo, y por eso queda demasiado denso en trimestrales largas —trece rótulos
pisados en 25 años— y demasiado ralo en anuales cortas. Cuando BUG-0001 se
arregle con un paso adaptativo, la rama anual tiene que recibir el mismo
tratamiento, y entonces las dos **se apartarán del convenio a sabiendas**. Eso
es una decisión distinta de ésta, y conviene que quede escrito cuál es cuál.

Quedan además dos desviaciones de C que este arreglo **no** toca porque son de
la rama `f > 1` y del `set_xlim` común, o sea territorio de BUG-0001:

- `first_yr = (int(x0) // step) * step` redondea hacia abajo al año par; C
  rotula desde `begyear`. Es lo que pone un `1994` en una serie que empieza en
  1995 — que BUG-0001 anota como defecto menor y resulta ser el convenio roto.
- `set_xlim(..., xs[-1] + 0.3/f)` añade margen a la derecha; C cierra en `n-1`
  exacto.

## Validation

`tests/test_bug_0002_frecuencia_anual.py` — ocho pruebas. Las tres frecuencias
por la misma puerta (falla con `UnboundLocalError` sin el arreglo), y cuatro que
fijan el convenio con la cita del C al lado: paso de 20 años, primer rótulo en
`begyear` y no en un múltiplo redondeado, `outyear` como margen y como origen de
los rótulos, y que las de `f > 1` **no se toquen**.

Y una nota para BUG-0001: cuando se rehaga el paso del eje temporal, **las dos
ramas tienen que salir por el mismo sitio**. Si esa reescritura vuelve a dejar
una variable definida en una sola rama, este defecto vuelve.
