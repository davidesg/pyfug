"""BUG-0003 — `diffgraph` dated the differenced series twice.

It built the series with the start already moved past the lost observations,
and passed `plot_combined` a `timeout` that added them again. Now the plotted
series keeps the ORIGINAL start and `timeout` holds the lost observations, as
in fug C.
"""
import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from pyfug.core import Tseries  # noqa: E402
from pyfug.graphics.engine import diffgraph  # noqa: E402


def _serie():
    y = np.exp(4 + np.cumsum(np.random.default_rng(0).normal(0.01, 0.02, 120)))
    return Tseries(name="S", nobs=120, freq=12, begyear=2000, begtime=1, data=y)


@pytest.mark.parametrize("d, D, primero", [
    (0, 0, 2000.0),
    (1, 0, 2000 + 1 / 12),        # febrero de 2000
    (1, 1, 2001 + 1 / 12),        # febrero de 2001
])
@pytest.mark.parametrize("caso", ["case_a", "case_c"])
def test_el_primer_punto_cae_en_su_fecha(d, D, primero, caso):
    kw = dict(case_a=False, case_c=False)
    kw[caso] = True
    out = diffgraph(_serie(), boxlam=0.0, nrdiff=d, nadiff=D, case_ascii=False,
                    save=False, return_figs=True, **kw)
    fig = out["figures"][0]
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    serie = max(ax.lines, key=lambda ln: len(ln.get_xdata()))
    assert serie.get_xdata()[0] == pytest.approx(primero)
    assert ax.get_xlim()[0] == pytest.approx(2000.0), "el eje arranca en el año de comienzo"
    matplotlib.pyplot.close(fig)


def test_la_serie_de_los_estadisticos_sigue_fechada_en_su_primer_dato():
    out = diffgraph(_serie(), boxlam=0.0, nrdiff=1, nadiff=1, case_ascii=False,
                    save=False, return_figs=True)
    t = out["transformed"]
    assert (t.begyear, t.begtime) == (2001, 2)
