---
id: BUG-0005
title: En series estacionales los años se rotulan enteros y se montan a partir de ~25 años — GraphMaker los rotulaba con dos dígitos
status: fixed
severity: medium
component: graphics
found_in: 2.0.1
fixed_in: 2.0.2.dev0
reported: 2026-10-03
reporter: David / Claude
tags:
  - rotulos
  - legado-treadway
references:
  - pyfug/graphics/combined.py, series.py — eje de años de las series estacionales
  - GraphMaker/Projects/graphmakertri2/singletrim.cpp ≈380-400, singlemonth.cpp ≈488-513
  - atsw-gui lib/fugplot/fugplot.c ≈186-198 (el mismo defecto en el C)
---

## Summary

En una serie estacional (trimestral o mensual), el eje de la figura de la serie
rotula un año de cada dos con el año ENTERO («1996»). Pasados unos 25 años los
rótulos se montan: una trimestral 1995–2025 (124 obs.) los pisa todos.

## Impact

Medio: la figura es la primera que mira el analista y en una serie larga el eje
de fechas no se lee. Las trimestrales macro de 25 a 60 años, que son el caso
habitual, caen todas aquí.

## Reproduction

```python
import numpy as np
from pyfug.core import Tseries
from pyfug.graphics import plot_combined
y = 100 * np.exp(np.cumsum(0.02 + 0.05 * np.random.default_rng(0).standard_normal(124)))
plot_combined(Tseries(name="Q", nobs=124, freq=4, begyear=1995, begtime=1, data=y))
```

## Root cause

El legado de Treadway en GraphMaker rotula los años de una serie estacional
con sus DOS últimos dígitos: `singletrim.cpp` y `singlemonth.cpp` usan
`FormatFloat("00", …)`, un rótulo cada 8 (trimestral) o 24 (mensual)
observaciones, y tratan aparte el cambio de siglo. pyfug, como el fug en C de
atsw-gui, puso el año entero. Mantuvo la regla de cada 2 años, pero no el
formato, que es lo que hacía que cupieran.

## Fix

The rule, decided with the analyst:
- **Quarterly:** the year's last two digits, always (`96`, `98`, `00`). That
  is GraphMaker's format and its solution.
- **Monthly** (and any other seasonal frequency): the full year, as Treadway
  approved the monthly graph. `_compacta_si_se_montan` switches to two digits
  only if the full-year labels actually overlap, measured on the drawn figure.
  In pyfug that happens past about 30 years.
- **Annual:** untouched, on purpose. They keep the full year every 20 years,
  the fug C convention (BUG-0002). In long historical series (the wheat
  data, for one) two digits would be ambiguous: «20» could be 1820, 1920 or
  2020.

The lines and the step are unchanged.

Note from the GraphMaker review: `FormatFloat("00", …)` sets a minimum of
two digits. Labels came out as «85» because the years were typed with two
digits; a year typed as 1985 would print in full. Two digits for quarterly
data is therefore the format the legacy graphs show, and the analyst's
decision, not a truncation the code enforced.

## Validation

`tests/test_bug_0005_rotulos_de_dos_digitos.py`:
- el formato, con el cambio de siglo;
- quarterly every other year, across 2000;
- a monthly series that fits (WTI, 2002–2019) keeps the full year;
- a 35-year monthly series switches to two digits without overlap;
- in the 31-year quarterly series, no two labels overlap.
