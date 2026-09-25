---
id: BUG-0004
title: Importar pyfug cambia TODAS las figuras del proceso — `graphics/base.py` reescribe los `rcParams` globales de matplotlib al cargarse
status: open
severity: medium
component: graphics
found_in: 2.0.0
fixed_in:
reported: 2026-09-25
reporter: David — revisión de las figuras de la suite (art BUG-0165)
tags:
  - graphics
  - matplotlib
  - efecto-global
references:
  - fue/TODO.md, «Reemplazar plots.py con pyfug» (condición previa)
  - art-python/TODO.md, «PARA 0.3 — un solo dibujo para la figura de un modelo»
---

## Summary

`graphics/base.py:74` ejecuta `_setup_matplotlib_rc()` al importarse el módulo.
Reescribe `matplotlib.rcParams` del proceso entero. Medido, `import pyfug` cambia:

    figure.dpi    100.0  -> 150.0
    savefig.dpi   figure -> 150.0
    savefig.bbox  None   -> tight
    font.size     10.0   -> 14.0

(y fuentes, grosores de línea y de ejes).

## Impact

Medio. Cualquier figura que el programa dibuje DESPUÉS de importar pyfug —de
fue, de art o del usuario— sale con el estilo de pyfug, y distinta según el
orden de las importaciones. Es la condición previa para que fue pueda usar
pyfug como motor opcional (0.3 de la suite): fue no puede cambiar el aspecto de
sus propias figuras de previsión por el hecho de haber dibujado una de
residuos.

## Root cause

El estilo se aplica como configuración global en vez de por figura.

## Fix

Aplicar el estilo sólo a las figuras de pyfug: `matplotlib.rc_context(...)`
alrededor de cada constructor, o un `style` propio que se pasa al crear la
figura. Ninguna escritura en `rcParams` al importar.

## Validation

Que `import pyfug` deje `rcParams` intacto y que las figuras de pyfug sigan
saliendo con su estilo.
