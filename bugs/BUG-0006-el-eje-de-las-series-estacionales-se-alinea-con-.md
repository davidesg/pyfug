---
id: BUG-0006
title: El eje de las series estacionales se alinea con el año PAR anterior y cambia a paso 1 en series cortas — fug C, con la corrección de Treadway, arranca en el año de comienzo y va cada 2 años
status: fixed
severity: medium
component: graphics
found_in: 2.0.1
fixed_in: 2.0.2.dev0
reported: 2026-10-03
reporter: David / Claude — revisión de fidelidad con GraphMaker y fug C
tags:
  - rotulos
  - legado-treadway
references:
  - pyfug/graphics/combined.py, series.py — eje de años de las series estacionales
  - fug-1.12/1.13 src/gnuplot_graphics.c (líneas en -tmornsop + 2f·i, rótulo tsby + 2i)
  - atsw-gui lib/fugplot/fugplot.c series_panel; fug.c timeout = ornsop + begtime - 1
---

## Summary

pyfug drew the year lines and labels of a seasonal series from the even year
at or before the first plotted observation, `(int(x0)//2)*2`, and used a step
of 1 year in series shorter than 5 years. A quarterly series starting in 1995
came out as «94, 96, 98…», with an empty year on the left. Its comment said
«matches C: even years», and the C does not do that.

## Impact

Medium. The year labels are not those of fug C, which is the alignment
Treadway corrected and approved: the axis starts at the first period of the
year in which the series starts, and labels go every 2 years from that year.

## Reproduction

`plot_combined` on a quarterly series with `begyear=1995`: the labels read
94, 96, … (expected 95, 97, …).

## Root cause

In fug C (gnuplot 1.12/1.13 and fugplot.c):
- `timeout = ornsop + begtime - 1`: the axis starts at period 1 of the
  starting year, filling in what differencing loses and what is missing up to
  that period;
- a line every `2·f` from there (`-tmornsop + 2·f·i`), labelled `tsby + 2i`;
- no line past the last observation.

pyfug rounded down to an even year, changed the step for short series, and
allowed a line one period past the end.

## Fix

In both figures, `first_yr = begyear` (of the original series), `step = 2`,
the axis starts exactly at `begyear`, and no line goes past the last
observation. The ACF/PACF axis stays adaptive and the panel proportions are
unchanged, both decided with the analyst.

## Validation

`tests/test_bug_0005_rotulos_de_dos_digitos.py` (block BUG-0006):
- a 1995 series starts at «95, 97, 99, 01»;
- the axis starts at 1995.0;
- a 4-year series also goes every 2 years and stops at the last observation.
