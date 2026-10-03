"""
Combined plot: standardized series + ACF/PACF — fug C's graph -c.

Built from the panels of `pyfug.graphics.fugplot`, with the geometry of
atsw-gui lib/fugplot/fugplot.c `plotser_corrser` (BUG-0007).
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from pyfug.statistics import acf, pacf, chi_test, acf_pacf_max, series_max, series_size
from pyfug.graphics.base import jt_style, _compacta_si_se_montan
from pyfug.graphics import fugplot as fp


@jt_style
def plot_combined(ser, npar=0, tsnobs=None, timeout=None, tsby=None,
                  d=0, ds=0, nlags=0, cbands=0.0,
                  title="", fig=None) -> Figure:
    """Replica of FUG gnuplot_File_PlotSer_CorrSer with C-exact axes positions."""
    n = ser.nobs
    f = ser.freq
    data_raw = np.asarray(ser.data, dtype=float)

    # Standardize (matching C: a[i] = (data[i] − mean) / sigma)
    mean_v = float(np.mean(data_raw))
    std_v  = float(np.std(data_raw, ddof=0))
    z = (data_raw - mean_v) / std_v if std_v > 1e-10 else data_raw - mean_v

    if tsnobs is None:
        tsnobs = n + (timeout or 0)
    if timeout is None:
        timeout = 0
    outyear = int(getattr(ser, 'outyear', 0) or 0)
    if tsby is None:
        # CONVENIO DE FUG C (fug.c:399-404). Para anuales el origen de los
        # rótulos NO es `begyear` sino `begyear - outyear`:
        #     if (freq > 1) ... ser->begyear ...
        #     else          ... ser->begyear - ser->outyear ...
        tsby = ser.begyear - outyear if f == 1 else ser.begyear

    size    = series_size(tsnobs, f)
    abs_max = series_max(z)

    # ── ACF/PACF parameters ─────────────────────────────────────────────
    if nlags == 0:
        nlags = fp.default_lags(n, f)
    # PACF (Durbin-Levinson) requires nlags < n/2: same cap for both panels.
    nlags = min(nlags, n - 1, max(1, n // 2 - 1))

    acf_vals  = acf(data_raw, nlags)
    pacf_vals = pacf(data_raw, nlags)
    cmax = cbands if cbands > 0 else acf_pacf_max(acf_vals, pacf_vals)
    q_stat = chi_test(data_raw, nlags)

    # ── LAYOUT: plotser_corrser de fugplot.c ──────────────────────────────
    L = fp.layout(size)
    W, H = L["W"], L["H"]
    fig = fp.new_canvas(W, H, fig)
    sx0 = fp.series_x0(L, abs_max)
    sx1 = 0.632 * W
    cx0 = 0.738 * W
    cx1 = W - 12.0

    ax_s = fp.series_panel(fig, L, W, H, sx0, sx1, 0.26 * H, 0.77 * H,
                           ser, z, abs_max, timeout, tsby)
    # El título, como lo coloca GraphMaker (y fugplot.c): alineado a la
    # izquierda desde el 80 % del ancho de la serie, sin entrar en la columna
    # de la acf/pacf.
    fp.title(fig, W, H, title or getattr(ser, "name", "") or "", L["title"],
             sx0 + 0.80 * (sx1 - sx0), H - 16.0, align="left", xmax=cx0 - 6.0)
    fp.statistics(fig, L, W, H, (sx0 + sx1) / 2.0, 16.0 if size == 2 else 14.0,
                  mean_v, std_v, n)
    fp.corr_panel(fig, L, W, H, cx0, cx1, 0.595 * H, 0.833 * H,
                  acf_vals, nlags, f, n, cmax, "acf")
    fp.q_label(fig, W, H, (cx0 + cx1) / 2.0, 0.595 * H - 21.0, L["q"],
               nlags - npar, q_stat)
    fp.corr_panel(fig, L, W, H, cx0, cx1, 0.125 * H, 0.365 * H,
                  pacf_vals, nlags, f, n, cmax, "pacf")

    if f > 1:
        _compacta_si_se_montan(fig, ax_s, f)
    return fig
