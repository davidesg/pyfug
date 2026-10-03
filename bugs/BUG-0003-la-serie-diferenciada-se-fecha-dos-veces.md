---
id: BUG-0003
title: La serie diferenciada se fecha DOS veces — `diffgraph` ya desplaza el inicio y `plot_combined` le vuelve a sumar las observaciones consumidas
status: fixed
severity: medium
component: graphics
found_in: 2.0.0
fixed_in: 2.0.2.dev0
reported: 2026-09-25
reporter: David — revisión de las figuras de la suite (art BUG-0165)
tags:
  - graphics
  - eje-temporal
  - diferenciacion
references:
  - pyfug BUG-0001, BUG-0002 (el mismo eje temporal)
  - art/bugs/BUG-0172, BUG-0185 (el mismo desfase, en art)
---

## Summary

`diffgraph` construye la serie diferenciada con el inicio ya desplazado
(`begyear`/`begtime` de la primera observación que sobrevive,
`graphics/engine.py:150-160`), y `plot_combined` vuelve a sumar las
observaciones perdidas por la diferenciación al dibujar el eje
(`graphics/combined.py:125-131`). El primer punto queda corrido el doble.

## Reproduction

Serie mensual de 120 datos desde 2000/1, `boxlam=0`, medida la línea de la serie:

| d | D | primer punto dibujado | debería |
|---|---|---|---|
| 0 | 0 | 2000.000 | 2000.000 |
| 1 | 0 | **2000.167** (marzo) | 2000.083 (febrero) |
| 1 | 1 | **2002.167** (marzo de 2002) | 2001.083 (febrero de 2001) |

```python
from pyfug.core import Tseries
from pyfug.graphics.engine import diffgraph
out = diffgraph(ser, boxlam=0.0, nrdiff=1, nadiff=1, case_a=True,
                case_ascii=False, save=False, return_figs=True)
```

## Impact

Medio: el eje de una figura de identificación diferenciada miente en la fecha
(d + D·s periodos). No afecta a art, que llama a `plot_combined` con la serie
ya fechada y sin `timeout`; sí a quien use `diffgraph` o la línea de órdenes.

## Root cause

Dos sitios hacen la misma cuenta. La de `plot_combined` es la del convenio de
fug C (`timeout`), la de `diffgraph` es la de pyfug; sumadas, se cuenta dos
veces.

## Fix

Una sola: o `diffgraph` pasa el inicio ORIGINAL y `timeout`, o pasa el inicio
desplazado y `timeout=0`. Lo primero es el convenio de C.

## Validation

Que el primer punto dibujado sea el de la primera observación que sobrevive,
para d y D; los tests de BUG-0002 sólo usan series sin diferenciar.

## Resolution (2026-10-03)

The first option, fug C's convention. `diffgraph` draws a series that keeps
the ORIGINAL start, with the observations lost to differencing in `timeout`.
The panel adds `begtime − 1` itself, so `timeout` no longer includes it. The
series with the moved start (`res_ser`) stays for the statistics and the text
output.

This also follows the convention every engine was given the same day (art,
drtran and sima pass the original start and `timeout`). `diffgraph` was the
one case left that counted twice.

**Validation:** `tests/test_bug_0003_diffgraph_fecha_una_vez.py`:
- the report's table, for the series alone and the combined figure: first
  point at 2000.000, 2000.083 and 2001.083, axis from 2000.0;
- the statistics series still dated at its first observation.

