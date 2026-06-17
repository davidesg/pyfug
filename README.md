# pyfug — Jenkins-Treadway High-Definition Time Series Graphics

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-GPL%20v2-green)

**pyfug** es la migración a Python del programa FUG 1.12 (C/gnuplot),
diseñado por Arthur B. Treadway y David E. Guerrero. Produce gráficos
de series temporales de alta definición con las proporciones precisas
del diseño Jenkins-Treadway, ahora usando **matplotlib** como motor
gráfico.

## ¿Qué aporta sobre el FUG original?

| Original (C + gnuplot) | pyfug (Python + matplotlib) |
|------------------------|----------------------------|
| Solo entrada `.inp` | `.inp`, CSV, Excel, pandas, numpy |
| Solo salida EPS | PDF vectorial, SVG, PNG, interactivo (Jupyter) |
| Solo CLI | CLI + API Python + Jupyter notebooks |
| Gnuplot externo | matplotlib integrado (sin dependencias externas) |
| Compilación C | `pip install` |
| Sin integración | Conectable con statsmodels, scipy, pandas |

## Instalación

```bash
cd pyfug
pip install -e .

# Opcional: soporte Jupyter
pip install -e ".[jupyter]"
```

## Uso rápido

### Desde línea de comandos

```bash
# Gráfico combinado (serie + ACF/PACF) — igual que FUG original
pyfug PU.inp one -c

# Set de identificación con hasta 2 diferencias regulares y 1 estacional
pyfug PU.inp set 2 1 -c

# Solo ACF/PACF con 24 lags
pyfug PU.inp one -b -l 24

# Histograma + mean-deviation chart
pyfug PU.inp one -d -e
```

### Desde Python

```python
from pyfug import read_inp, diffgraph

# Leer datos
ser = read_inp("PU.inp")

# Gráfico combinado con log y 1 diferencia regular
result = diffgraph(ser,
    boxlam=0.0,    # log
    nrdiff=1,      # 1 diferencia regular
    case_c=True,   # combinado
    return_figs=True)

fig = result['figures'][0]
fig.savefig("output.pdf")
```

### Desde pandas/CSV

```python
import pandas as pd
from pyfug import read_pandas, diffgraph

# Desde DataFrame
df = pd.read_csv("mis_datos.csv")
ser = read_pandas(df["precios"], name="IPC", freq=12, begyear=2020)

# Generar gráficos
result = diffgraph(ser, boxlam=0.0, nrdiff=1, case_c=True)
```

### En Jupyter

```python
from pyfug import read_inp
from pyfug.jupyter import display_diffgraph

ser = read_inp("PU.inp")

# Muestra todos los gráficos inline
transformed = display_diffgraph(ser,
    boxlam=0.0, nrdiff=1, nadiff=0,
    case_c=True, case_d=True, case_e=True)
```

### Con modelos de estimación (statsmodels)

```python
from statsmodels.tsa.arima.model import ARIMA
from pyfug.jupyter import from_statsmodels_result, diagnostic_plots

# Ajustar modelo
model = ARIMA(ser.data, order=(1, 1, 1))
result = model.fit()

# Extraer residuos como Tseries
resid_ser = from_statsmodels_result(result, name="Residuos ARIMA(1,1,1)")

# Gráficos de diagnóstico completos
diagnostic_plots(resid_ser, model_name="ARIMA111")
```

## Tipos de gráficos

| Flag | Gráfico | Descripción |
|------|---------|-------------|
| `-a` | Serie temporal | Línea con etiquetas de año precisas |
| `-b` | ACF/PACF | Correlograma con bandas ±2/√n y Q de Ljung-Box |
| `-c` | Combinado | Serie + ACF/PACF en layout multi-panel |
| `-d` | Histograma | Histograma estandarizado + curva normal |
| `-e` | Mean-Deviation | Medias vs desviaciones típicas estandarizadas |

## Estructura del proyecto

```
pyfug/
├── pyfug/
│   ├── __init__.py          # API pública
│   ├── core.py               # Tseries dataclass
│   ├── io.py                 # Lectura .inp, CSV, Excel, pandas
│   ├── transform.py          # Box-Cox, diferencias
│   ├── statistics.py         # ACF, PACF, Ljung-Box, estadísticos
│   ├── graphics/
│   │   ├── __init__.py
│   │   ├── base.py           # Constantes y tema Jenkins-Treadway
│   │   ├── series.py         # Gráfico de serie
│   │   ├── acf_pacf.py       # Correlograma ACF/PACF
│   │   ├── combined.py       # Serie + ACF/PACF combinado
│   │   ├── histogram.py      # Histograma + normal
│   │   ├── mean_deviation.py # Mean-Deviation chart
│   │   └── engine.py         # Motor principal (diffgraph)
│   ├── latex.py              # Salida LaTeX
│   ├── cli.py                # Interfaz línea de comandos
│   └── jupyter.py            # Integración Jupyter
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

## Diseño Jenkins-Treadway

El valor distintivo de FUG/pyfug está en las **proporciones precisas**
de los gráficos:

- **ACF/PACF**: Sin ticks en el eje X — usa líneas verticales y etiquetas
  manuales en los lags; bandas de confianza ±2/√n en rojo; estadístico
  Ljung-Box como etiqueta del eje X.
- **Serie temporal**: Etiquetas de año en lugar de ticks; borde solo en
  izquierda e inferior; grid horizontal; grosor de línea calibrado.
- **Layout combinado**: Serie grande a la izquierda, ACF y PACF a la
  derecha en dos paneles con proporciones exactas según número de lags
  y frecuencia de los datos.
- **Histograma**: Estructura cuadrada con curva normal superpuesta;
  asimetría, curtosis y Jarque-Bera como etiqueta del eje X.

## Licencia

GNU General Public License v2.0 — mismo régimen que el FUG original.

## Autores

- **Arthur B. Treadway** — diseño original Jenkins-Treadway, FUG 1.x (C)
- **David E. Guerrero** — FUG 1.x (C), migración a Python 2.0
