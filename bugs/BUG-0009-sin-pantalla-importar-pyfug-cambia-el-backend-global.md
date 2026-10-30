---
id: BUG-0009
title: Sin pantalla, importar pyfug.graphics cambia el backend GLOBAL de matplotlib — `graphics/engine.py` llama a `matplotlib.use("Agg")` al cargarse
status: open
severity: low
component: graphics
found_in: 2.0.2
fixed_in:
reported: 2026-10-30
reporter: David / Claude — prueba de instalación limpia de atsw 2.1.0 en diez distribuciones
tags:
  - graphics
  - matplotlib
  - efecto-global
references:
  - pyfug/graphics/engine.py (el `matplotlib.use("Agg")` condicionado a DISPLAY)
  - bugs/BUG-0004-importar-pyfug-cambia-todas-las-figuras-del-proceso.md
  - tests/test_bug_0004_rcparams_por_figura.py::test_importar_pyfug_no_cambia_ningun_rcparam
---

## Summary

`pyfug/graphics/engine.py` hace, al importarse,

    if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
        matplotlib.use("Agg")

y `matplotlib.use` escribe `rcParams["backend"]` y `rcParams["backend_fallback"]`.
Es el resto de BUG-0004: el estilo pasó a `jt_style`, el backend no. En
cualquier máquina sin pantalla —un servidor, un CI, un contenedor— importar
pyfug fija el backend del proceso entero. La prueba de BUG-0004 lo dice: en la
prueba de instalación limpia de atsw 2.1.0 (2026-10-30, diez distribuciones en
podman) falló en las diez, y aquí sólo pasa porque hay DISPLAY.

## Impact

Bajo. Sin pantalla matplotlib ya elige Agg por su cuenta (`backend_fallback`),
así que lo normal es que no cambie nada visible. Lo que cambia es que pyfug
decide por el proceso: quien importe pyfug y luego quiera otro backend no
interactivo, o confíe en el `backend_fallback`, se lo encuentra fijado. Y la
prueba que protege BUG-0004 queda roja en todo CI.

## Reproduction

`bugs/BUG-0009-repro/repro.py` importa `pyfug.graphics` en un proceso hijo sin
DISPLAY, sin WAYLAND_DISPLAY y sin MPLBACKEND, y lista los rcParams que cambian.
Sale con 1 mientras cambie alguno.

    python3 bugs/BUG-0009-repro/repro.py

## Root cause

La llamada a `matplotlib.use` al importar el módulo, de antes de BUG-0004.

## Fix

Propuesto: quitar la llamada. Sin pantalla, matplotlib ya resuelve Agg con su
`backend_fallback`; quien necesite fijarlo lo hace con MPLBACKEND, que es suyo
y no de una biblioteca.

## Validation

El repro, y `tests/test_bug_0004_rcparams_por_figura.py` en un entorno sin
pantalla.
