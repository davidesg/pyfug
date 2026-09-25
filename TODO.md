# pyfug — TODO

## Pendiente

### ~~Gráfico media-desviación típica (`-e`)~~  ✅ implementado (jun-2026)

Implementar `pyfug/graphics/mean_deviation.py` — replica el gráfico `-e` de fug C.

**Qué es**: para cada segmento de la serie (por ejemplo, años o períodos estacionales),
calcula la media y la desviación típica y los representa en un diagrama de dispersión
media (eje X) vs desviación típica (eje Y). Sirve para seleccionar la transformación
Box-Cox λ:
- Si σ ∝ media → ln (λ=0)
- Si σ ≈ constante → sin transformación (λ=1)
- Si relación intermedia → λ∈(0,1)

**Referencia**: `gnuplot_graphics.c` función `gnuplot_File_PlotMeanDev` en fug-1.12.01.

**API prevista** (según README):
```python
from pyfug.graphics.mean_deviation import plot_mean_deviation
fig = plot_mean_deviation(ser, title="IPC_DE")
```

**Integración en el motor**:
- `engine.py` `diffgraph`: activar con flag `-e` / `case_e=True`
- `cli.py`: opción `-e`

**Notas de diseño**:
- Mismas constantes de estilo Jenkins-Treadway que el resto de gráficos (base.py)
- Figura cuadrada, misma proporción que el histograma
- Etiqueta de cada punto: identificador del segmento (año, trimestre, etc.)
- Ejes: media en X, desviación típica en Y; título "Mean vs Std Dev"

---

## Contexto de uso (jun-2026)

pyfug es usado directamente por Claude como analista Box-Jenkins, sin necesidad
de una capa ART compleja. El flujo típico:

```python
from pyfug.core import Tseries
from pyfug.graphics.combined import plot_combined
from pyfug.graphics.acf_pacf import plot_acf_pacf
from pyfug.graphics.histogram import plot_histogram
from pyfug.graphics.mean_deviation import plot_mean_deviation  # pendiente

# serie desde fue.inp.load o desde pandas
fig = plot_combined(ser, d=1, title="∇ ln WTI")
fig = plot_histogram(ser, d=1, title="∇ ln WTI")
fig = plot_mean_deviation(ser, title="WTI nivel")
```

Gráficos actuales implementados y estables:
- `combined.py` — serie + ACF + PACF en layout GridSpec + constrained_layout
- `series.py` — serie standalone
- `acf_pacf.py` — ACF + PACF standalone (ancho = columna ACF del combinado)
- `histogram.py` — histograma con curva normal, S/K/JB + p-valor

---

## Gráficos ya implementados — estado

| Módulo | Estado | Notas |
|--------|--------|-------|
| `combined.py` | ✅ estable | GridSpec, nlags=max(10,3(f+1)), lw_imp=3/4, band lw=0.7 |
| `series.py` | ✅ estable | mismo estilo que combined |
| `acf_pacf.py` | ✅ estable | ancho = columna ACF del combinado |
| `histogram.py` | ✅ estable | JB p-valor incluido |
| `mean_deviation.py` | ✅ estable | scatter std. mean vs std. std-dev, nog=freq por defecto |

## Empaquetado — la versión, escrita una sola vez (2026-09-25)

- [ ] `__version__` está escrita a mano en `pyfug/__init__.py` además de en
      `pyproject.toml`. Derivarla de la metadata, como hizo fue en su BUG-0016
      (allí se quedó tres versiones atrás sin que nada lo delatara).
