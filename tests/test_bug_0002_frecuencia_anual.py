"""BUG-0002 — `plot_combined` se rompía en toda serie anual.

`x_pad` se asignaba sólo dentro de la rama `f > 1` del eje temporal y se
consumía después en el `set_xlim` común a las dos ramas. Con `f == 1` eso es un
`UnboundLocalError`: la figura no salía fea, no salía.

La prueba pasa las tres frecuencias por la misma puerta, y la anual va primero.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyfug.core import Tseries
from pyfug.graphics import plot_combined


def _serie(freq, nobs=40, begyear=1980):
    rng = np.random.default_rng(0)
    y = 100 * np.exp(np.cumsum(0.02 + 0.05 * rng.standard_normal(nobs)))
    return Tseries(name=f"F{freq}", nobs=nobs, freq=freq, begyear=begyear,
                   begtime=1, data=np.asarray(y, dtype=float))


@pytest.mark.parametrize("freq", [1, 4, 12])
def test_la_figura_combinada_sale_en_las_tres_frecuencias(freq):
    fig = plot_combined(_serie(freq))
    assert fig is not None
    assert fig.axes, "la figura salió sin ejes"
    matplotlib.pyplot.close(fig)


def test_el_eje_de_la_anual_tiene_limites_finitos():
    """El síntoma concreto: `set_xlim` consumía una variable sin asignar. Si
    alguien vuelve a dejarla suelta, esto lo caza aunque no lance."""
    fig = plot_combined(_serie(1, nobs=60))
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    x0, x1 = ax.get_xlim()
    assert np.isfinite(x0) and np.isfinite(x1)
    assert x1 > x0
    matplotlib.pyplot.close(fig)
