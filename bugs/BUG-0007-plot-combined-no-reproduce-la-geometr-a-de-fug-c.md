---
id: BUG-0007
title: plot_combined no reproduce la geometría de fug C — la serie ocupa el 75 % del alto (51 % en C), la acf/pacf es mayor y desigual y las fuentes son el doble
status: fixed
severity: medium
component: graphics
found_in: 2.0.1
fixed_in: 2.0.2.dev0
reported: 2026-10-03
reporter: David / Claude — revisión de fidelidad con GraphMaker y fug C
tags:
  - geometria
  - legado-treadway
references:
  - pyfug/graphics/combined.py, plot_combined y _draw_acf_panel
  - atsw-gui lib/fugplot/fugplot.c, plotser_corrser, series_panel, corr_panel, title, statistics
  - GraphMaker singletrim.cpp / singlemonth.cpp (title placement)
---

## Summary

`plot_combined` claimed «C-exact axes positions», but it laid out the panels
with a GridSpec and `constrained layout`, and approximate ratios.

| | fug C | pyfug before |
|---|---|---|
| canvas | 468×219 / 720×252 pt | 12×5.5 / 15×5.5 in |
| series panel height | 51 % (0.26–0.77 H) | ≈75 % |
| acf / pacf | 24 % × 24 %, equal, gap for Q | 30 % × 29 %, acf taller than pacf |
| fonts | 7.5–12 pt | 14–24 pt (relatively double) |
| title | bold, right-aligned on the series edge | centred over the figure |

Side by side with the fug figure, the two looked like different graphs.

## Impact

Medium. The figure art shows (residuals, identification) did not match the
format Treadway approved, which is the C one.

## Fix

Decided with the analyst, with fug C as the reference:

- **Canvas and panels.** The canvas has the C layout's size in points. The
  panels sit where `plotser_corrser` puts them: `sx0` from the width of the
  y labels, `sx1 = 0.632 W`, `cx0 = 0.738 W`, `cx1 = W − 12`, the series at
  0.26–0.77 H, the acf at 0.595–0.833 H and the pacf at 0.125–0.365 H.
- **Drawing.** Fonts, line widths, tick lengths, discs, bands and bars use
  the C's values. The font has Helvetica metrics (Nimbus Sans or Liberation
  Sans). The grey grid is gone.
- **Texts.** The statistics are centred under the series, `Q(k) = x` is
  centred under the acf, and the acf/pacf titles are not bold.
- **Title.** Placed as GraphMaker does: bold, left-aligned from 80 % of the
  series panel's width, never into the acf/pacf column. The same change is
  made in fugplot.c, so C and pyfug still match.
- **Unchanged, by decision:** the acf/pacf axis stays adaptive (GraphMaker
  used a fixed ±1).

Not covered:
- the default number of lags (annual: 10 here, 9 or 45 in C);
- `series.py`, the series-only figure.

## Validation

The C and pyfug figures were compared side by side, at the same scale, on a
31-year quarterly series, on WTI monthly and on a 1985–1999 quarterly
series, against GraphMaker's capture of «PS» in its user manual. The pyfug
suite passes (39). The monthly overlap test moves to 50 years, because with
the C's 8.6 pt year font a 35-year monthly axis fits in full, as in C.
