"""
ACF/PACF standalone plot — fug C's graph -b.

Built from the panels of `pyfug.graphics.fugplot` with the geometry of
atsw-gui lib/fugplot/fugplot.c `fp_CorrSer` (BUG-0007): a 252 pt high canvas
whose width grows with the number of lags (101.9, 152.3 or 234 pt), the acf at
0.595–0.833 H, the pacf at 0.125–0.365 H, and the Q between them.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from pyfug.statistics import acf, pacf, chi_test, acf_pacf_max
from pyfug.graphics import fugplot as fp
from pyfug.graphics.base import jt_style


@jt_style
def plot_acf_pacf(ser, npar=0, nlags=0, cbands=0.0,
                  title="", fig=None) -> Figure:
    """The acf and the pacf of a series, as fug -b draws them.

    `title` is accepted for compatibility; like the C, the figure has none.
    """
    n = ser.nobs
    f = ser.freq
    data_raw = np.asarray(ser.data, dtype=float)

    if nlags == 0:
        nlags = fp.default_lags(n, f)
    nlags = min(nlags, n - 1, max(1, n // 2 - 1))

    acf_vals = acf(data_raw, nlags)
    pacf_vals = pacf(data_raw, nlags)
    cmax = cbands if cbands > 0 else acf_pacf_max(acf_vals, pacf_vals)

    # El lienzo crece con los retardos (fp_CorrSer).
    H = 252.0
    W = 234.0 if nlags >= 30 else (152.3 if nlags >= 15 else 101.9)
    L = dict(fp.LAYOUT_BIG)
    L["tick"] = 8.0 if nlags >= 30 else 7.5
    L["q"] = 8.5 if (f > 4 or (f == 1 and n > 200)) else 7.5
    x0, x1 = 34.0, W - 6.0

    fig = fp.new_canvas(W, H, fig)
    fp.corr_panel(fig, L, W, H, x0, x1, 0.595 * H, 0.833 * H,
                  acf_vals, nlags, f, n, cmax, "acf")
    fp.q_label(fig, W, H, (x0 + x1) / 2.0, 0.595 * H - 21.0, L["q"],
               nlags - npar, chi_test(data_raw, nlags))
    fp.corr_panel(fig, L, W, H, x0, x1, 0.125 * H, 0.365 * H,
                  pacf_vals, nlags, f, n, cmax, "pacf")
    return fig
