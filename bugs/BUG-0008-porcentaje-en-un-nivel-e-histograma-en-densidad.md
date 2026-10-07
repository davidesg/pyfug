---
id: BUG-0008
title: La línea de estadísticos va siempre en % y el histograma rotula «%» lo que es 100·densidad — el convenio de fug C, sin forma de apagarlo para un nivel o una densidad
status: fixed
severity: low
component: graphics
found_in: 2.0.1
fixed_in: 2.0.2
reported: 2026-10-06
reporter: David / Claude — art BUG-0219
tags:
  - rotulos
  - legado-treadway
references:
  - pyfug/graphics/fugplot.py — statistics()
  - pyfug/graphics/series.py, combined.py — plot_series, plot_combined
  - pyfug/graphics/histogram.py — plot_histogram
  - fug-1.13/src/gnuplot_graphics.c ≈191-197 (w̄ ×100 con %), ≈764, 797, 807 (histograma)
  - art-python/bugs/BUG-0219-escalas-y-rotulos.md
---

## Summary

`statistics()` escribe «w̄ (σ̂w̄) = m % (e.t. %)   σ̂w = sd %» multiplicando
siempre por 100. Es el convenio de fug C, que da por hecho que lo dibujado es
una tasa (100·∇ln y). Sobre un nivel en logaritmos sale «w̄ = 446,45 %» (ln del
IPC de España), y sobre una serie sin transformar el % no tiene sentido.

`plot_histogram()` dibuja `200·counts/n` y la normal ×100 —100·densidad, como
el C— y rotula el eje «%». No es el porcentaje de observaciones: con residuos
muy apuntados una barra pasa del 100 %.

## Impact

Cifras sin sentido delante del alumno (art BUG-0219). art tenía que reescribir
la figura después de dibujada, buscando el texto de pyfug: frágil.

## Root cause

Fidelidad al C sin opción: ni `statistics` ni `plot_histogram` sabían qué se
dibujaba.

## Fix

Opciones, no un cambio de comportamiento: por defecto sigue el convenio del C.

- `statistics(..., percent=True)`; `plot_series(..., percent=True)` y
  `plot_combined(..., percent=True)` lo pasan. Con `percent=False`, los tres
  números en la escala de la serie, sin %.
- `plot_histogram(..., density=False)`. Con `density=True`, la densidad
  (barras de área 1, la normal con pico 0,399) y el eje «densidad».

El que llama decide: art pasa `percent=(λ = 0 y d + D ≥ 1)` y `density=True`.

## Validation

`tests/test_bug_0008_porcentaje_y_densidad.py`: por defecto, tres «%» y
100·w̄ (plot_combined y plot_series); con `percent=False`, sin % y en la escala
de la serie; el histograma por defecto, «%», área 100 y pico 100/√(2π); con
`density=True`, «densidad», área 1 y pico 1/√(2π). Suite de pyfug: 58 passed.
