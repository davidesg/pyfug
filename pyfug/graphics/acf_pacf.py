"""
ACF/PACF standalone plot — Jenkins-Treadway style.
Portrait layout with GridSpec + constrained_layout (same style as combined.py panels).
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator

from pyfug.statistics import acf, pacf, chi_test, acf_pacf_max


def plot_acf_pacf(ser, npar=0, nlags=0, cbands=0.0,
                  title="", fig=None) -> Figure:
    """Standalone ACF/PACF — portrait layout matching combined.py panel style."""
    n = ser.nobs
    f = ser.freq
    data_raw = ser.data

    if nlags == 0:
        if n < 3 * (f + 1):
            nlags = max(1, n - f // 2)
        else:
            nlags = max(10, 3 * (f + 1))
    nlags = min(nlags, n - 1)

    acf_vals  = acf(data_raw, nlags)
    pacf_vals = pacf(data_raw, nlags)

    cmax = cbands if cbands > 0 else acf_pacf_max(acf_vals, pacf_vals)
    conf = 2.0 / np.sqrt(n)

    q_stat  = chi_test(data_raw, nlags)
    q_df    = nlags - npar
    q_label = f"Q({q_df}) = {q_stat:.1f}"

    # Font sizes (match combined.py)
    fs_acf = 20 if nlags >= 30 else 18
    fs_q   = 17 if (f > 4 or (f == 1 and n > 200)) else 15
    fs_title = 22

    # Figure width = ACF column width from combined.py
    # combined: figw=15 w_ratio=2.095 → 15/(2.095+1)=4.85"
    #           figw=12 w_ratio=2.014 → 12/(2.014+1)=3.98"
    #           figw=12 w_ratio=2.225 → 12/(2.225+1)=3.72"
    if nlags >= 30:
        fig_w = 15.0 / (2.095 + 1.0)   # ≈ 4.85"
    elif nlags >= 15:
        fig_w = 12.0 / (2.014 + 1.0)   # ≈ 3.98"
    else:
        fig_w = 12.0 / (2.225 + 1.0)   # ≈ 3.72"
    fig_h = 9.0

    if fig is None:
        fig = plt.figure(figsize=(fig_w, fig_h), layout='constrained')

    # Height ratios from combined.py _layout_params (size==2: 0.46, 0.385)
    h_acf  = 0.46
    h_pacf = 0.385

    gs = gridspec.GridSpec(2, 1, figure=fig,
                           height_ratios=[h_acf, h_pacf],
                           hspace=0.06)
    ax_acf  = fig.add_subplot(gs[0])
    ax_pacf = fig.add_subplot(gs[1])

    _draw(ax_acf,  acf_vals,  nlags, n, f, cmax, conf, q_label, "acf",  fs_acf, fs_q)
    _draw(ax_pacf, pacf_vals, nlags, n, f, cmax, conf, "",       "pacf", fs_acf, fs_q)

    if title:
        fig.suptitle(title, fontsize=fs_title, fontweight='bold')

    return fig


def _draw(ax, corr, nlags, n, f, cmax, conf, q_label, label, fs_acf, fs_q):
    """Draw one ACF or PACF panel matching combined.py _draw_acf_panel style."""
    lag_x = np.arange(1, nlags + 1)

    lw_imp = 3.0 if nlags >= 30 else 4.0
    ax.vlines(lag_x, 0, corr, colors='k', linewidth=lw_imp, zorder=3)

    ax.axhline(y= conf, color='k', linestyle='--', linewidth=0.7, zorder=2)
    ax.axhline(y=-conf, color='k', linestyle='--', linewidth=0.7, zorder=2)
    ax.axhline(y=0,     color='k', linewidth=0.8,  zorder=2)

    ax.set_ylim(-cmax, cmax)
    half = cmax / 2.0
    ax.yaxis.set_major_locator(FixedLocator([-cmax, -half, 0.0, half, cmax]))
    ax.tick_params(axis='y', direction='out', labelsize=9)

    # Seasonal grid lines and x-tick labels
    if f > 1:
        grid_lags = [f * m for m in range(1, 4) if f * m <= nlags]
    elif nlags > 9:
        gap = round(nlags / 3)
        grid_lags = [gap * m for m in range(1, 4) if gap * m <= nlags]
    else:
        grid_lags = [x for x in (3, 6, 9) if x <= nlags]

    for xv in grid_lags:
        ax.axvline(xv, color='0.5', lw=0.8, zorder=1)

    ax.set_xlim(0.5, nlags + 0.5)
    ax.set_xticks(grid_lags)
    ax.set_xticklabels([str(x) for x in grid_lags], fontsize=9)
    ax.tick_params(axis='x', direction='out', length=3)

    for sp in ('top', 'right', 'bottom'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_linewidth(1.6)

    if label:
        ax.text(0.5, 1.01, label, transform=ax.transAxes,
                ha='center', va='bottom', clip_on=False,
                fontsize=fs_acf, fontweight='bold')

    if q_label:
        ax.set_xlabel(q_label, fontsize=fs_q, labelpad=6)
