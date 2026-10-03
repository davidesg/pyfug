"""
Time series plot — fug C's graph -a.

The standardized series alone, built from the panels of
`pyfug.graphics.fugplot` with the geometry of atsw-gui lib/fugplot/fugplot.c
`fp_PlotSer` (BUG-0007): the C canvas in points, the series panel from `sx0` to
`W − 12` and from 53 pt to `H − 34`, the title right-aligned on its edge, and
the statistics centred under it.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from pyfug.statistics import series_max, series_size
from pyfug.graphics.base import _compacta_si_se_montan
from pyfug.graphics import fugplot as fp


def plot_series(ser, tsnobs=None, timeout=None, tsby=None,
                d=0, ds=0, title="",
                fig=None, ax=None) -> Figure:
    """Plot the standardized time series with the fug C design.

    Parameters
    ----------
    ser : Tseries
        Time series with data, freq, begyear, begtime.
    tsnobs : int, optional
        Total observations in original series (before differencing).
    timeout : int, optional
        Observations lost to differencing.
    tsby : int, optional
        First year label of an annual axis (default `begyear - outyear`).
    title : str
        Plot title.
    fig, ax : optional
        Existing figure/axes to draw on. With an `ax`, only the series panel
        is drawn into it, at its own position.
    """
    n = ser.nobs
    f = ser.freq
    data = np.asarray(ser.data, dtype=float)
    if timeout is None:
        timeout = 0
    if tsnobs is None:
        tsnobs = n + timeout
    if tsby is None:
        outyear = int(getattr(ser, 'outyear', 0) or 0)
        tsby = ser.begyear - outyear if f == 1 else ser.begyear

    mean_v = float(np.mean(data))
    std_v = float(np.std(data, ddof=0))
    z = (data - mean_v) / std_v if std_v > 1e-10 else data - mean_v

    size = series_size(tsnobs, f)
    abs_max = series_max(z)
    L = fp.layout(size)
    W, H = L["W"], L["H"]

    if ax is not None:
        fig = ax.figure
        fp.series_panel(fig, L, W, H, 0, 0, 0, 0, ser, z, abs_max, timeout,
                        tsby, ax=ax)
        if title:
            ax.set_title(title, fontsize=L["title"], fontweight="bold",
                         fontfamily=fp.FAMILY, loc="right")
        return fig

    fig = fp.new_canvas(W, H, fig)
    sx0 = fp.series_x0(L, abs_max)
    sx1 = W - 12.0
    ax = fp.series_panel(fig, L, W, H, sx0, sx1, 53.0, H - 34.0, ser, z,
                         abs_max, timeout, tsby)
    fp.title(fig, W, H, title or getattr(ser, "name", "") or "", L["title"],
             sx1, H - 16.0, align="right")
    fp.statistics(fig, L, W, H, (sx0 + sx1) / 2.0, 12.0, mean_v, std_v, n)
    if f > 1:
        _compacta_si_se_montan(fig, ax, f)
    return fig


def plot_series_simple(ser, figsize=(12, 4), title=""):
    """Simplified wrapper for quick plotting."""
    return plot_series(ser, tsnobs=ser.nobs, timeout=0,
                       d=ser.d, ds=ser.ds, title=title)
