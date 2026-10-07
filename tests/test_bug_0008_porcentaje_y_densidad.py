"""BUG-0008 — el % de la línea de estadísticos y el eje del histograma.

fug C escribe w̄, σ̂_w̄ y σ̂_w ×100 con «%» y rotula «%» un histograma que es
100·densidad. Es su convenio y sigue siendo el de defecto; `percent=False` y
`density=True` lo apagan para quien dibuja un nivel o quiere la densidad.
"""
import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from pyfug.core import Tseries  # noqa: E402
from pyfug.graphics import plot_combined, plot_histogram  # noqa: E402
from pyfug.graphics.series import plot_series  # noqa: E402


def _ser(nobs=216):
    rng = np.random.default_rng(0)
    y = np.log(100 * np.exp(np.cumsum(0.003 + 0.004 * rng.standard_normal(nobs))))
    return Tseries(name="S", nobs=nobs, freq=12, begyear=2002, begtime=1,
                   data=np.asarray(y, dtype=float))


def _linea_w(fig):
    t = [x.get_text() for x in fig.texts if "bar{w}" in x.get_text()]
    assert len(t) == 1
    return t[0]


@pytest.mark.parametrize("plot", [plot_combined, plot_series])
def test_por_defecto_el_convenio_de_fug_c(plot):
    ser = _ser()
    txt = _linea_w(plot(ser))
    assert txt.count("%") == 3
    assert f"{100 * np.mean(ser.data):.2f}%" in txt
    matplotlib.pyplot.close("all")


@pytest.mark.parametrize("plot", [plot_combined, plot_series])
def test_percent_false_en_la_escala_de_la_serie(plot):
    ser = _ser()
    txt = _linea_w(plot(ser, percent=False))
    assert "%" not in txt
    assert f"{np.mean(ser.data):.4g}" in txt
    assert f"{np.std(ser.data):.4g}" in txt
    matplotlib.pyplot.close("all")


def _barras(fig):
    ax = fig.axes[0]
    alturas = np.array([p.get_height() for p in ax.patches])
    pico = max(ln.get_ydata().max() for ln in ax.get_lines()
               if len(ln.get_ydata()) > 100)
    return ax, alturas, pico


def test_histograma_por_defecto_100_por_densidad():
    rng = np.random.default_rng(1)
    ser = Tseries(name="a", nobs=400, freq=12, begyear=2000, begtime=1,
                  data=rng.standard_normal(400))
    ax, h, pico = _barras(plot_histogram(ser))
    assert ax.get_ylabel() == "%"
    assert pico == pytest.approx(100 / np.sqrt(2 * np.pi), rel=1e-3)
    assert h.sum() * 0.5 == pytest.approx(100.0)
    matplotlib.pyplot.close("all")


def test_histograma_density_true():
    rng = np.random.default_rng(1)
    ser = Tseries(name="a", nobs=400, freq=12, begyear=2000, begtime=1,
                  data=rng.standard_normal(400))
    ax, h, pico = _barras(plot_histogram(ser, density=True))
    assert ax.get_ylabel() == "densidad"
    assert pico == pytest.approx(1 / np.sqrt(2 * np.pi), rel=1e-3)
    assert h.sum() * 0.5 == pytest.approx(1.0)   # área 1
    matplotlib.pyplot.close("all")
