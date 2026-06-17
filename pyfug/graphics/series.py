"""
Time series plot — Jenkins-Treadway style.

Produces a standardized (z-score) line plot with decimal-year x-axis,
year boundary dividers, ±2σ dashed reference lines, and xlabel with
mean / SE / sigma statistics. Matches the series panel of combined.py.
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from pyfug.statistics import series_max, series_size
from pyfug.graphics.base import JT_FONT_YEAR, JT_COLOR_SERIES, _tics_size
from pyfug.graphics.combined import _to_decimal_year


def plot_series(ser, tsnobs=None, timeout=None, tsby=None,
                d=0, ds=0, title="",
                fig=None, ax=None) -> Figure:
    """Plot the standardized time series with Jenkins-Treadway design.

    Parameters
    ----------
    ser : Tseries
        Time series with data, freq, begyear, begtime.
    tsnobs : int, optional
        Total observations in original series (before differencing).
    timeout : int, optional
        Observations lost to differencing.
    tsby : int, optional
        Starting year for x-axis labels (ignored — derived from ser).
    title : str
        Plot title (mathtext-formatted).
    fig, ax : optional
        Existing figure/axes to draw on.
    """
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=(12, 4))

    n = ser.nobs
    f = ser.freq
    data = np.asarray(ser.data, dtype=float)

    if tsnobs is None:
        tsnobs = n
    if timeout is None:
        timeout = 0

    # ── Standardize ────────────────────────────────────────────────────
    mean_v = float(np.mean(data))
    std_v  = float(np.std(data, ddof=0))
    z = (data - mean_v) / std_v if std_v > 1e-10 else data - mean_v

    size    = series_size(tsnobs, f)
    abs_max = series_max(z)

    # ── Decimal-year x-axis (same as combined panel) ────────────────────
    begyear = ser.begyear
    begtime = getattr(ser, 'begtime', 1)
    total_p = (int(begtime) - 1) + int(timeout)
    adj_year = int(begyear) + total_p // f
    adj_per  = total_p % f + 1
    xs = _to_decimal_year(n, adj_year, adj_per, f)

    # ── Y-axis ─────────────────────────────────────────────────────────
    y_max = int(abs_max)
    ax.set_ylim(-y_max - 0.15, y_max + 0.15)
    ax.set_yticks(range(-y_max, y_max + 1, 2))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.tick_params(axis='y', direction='out', labelsize=11)

    # ── X-axis: year dividers + tick labels ────────────────────────────
    if f > 1:
        x0, x1 = xs[0], xs[-1]
        step = 2 if (x1 - x0) > 5 else 1
        # Floor to nearest step-aligned year (matches C: even years regardless of start)
        first_yr = (int(x0) // step) * step
        x_pad = max(0.3 / f, x0 - first_yr + 0.5 / f)  # ensure first_yr fits in xlim
        tick_pos, tick_lbl = [], []
        for yr in range(first_yr, int(x1) + 2, step):
            if yr <= x1 + 1.0 / f:
                ax.axvline(yr, color='k', lw=0.5, zorder=1)
                tick_pos.append(yr)
                tick_lbl.append(str(yr))
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_lbl, fontsize=JT_FONT_YEAR)
    else:
        step = 10
        first_yr = (int(xs[0]) // step) * step
        tick_pos = [yr for yr in range(first_yr, int(xs[-1]) + step + 1, step)
                    if xs[0] <= yr <= xs[-1]]
        ax.set_xticks(tick_pos)
        ax.set_xticklabels([str(y) for y in tick_pos], fontsize=JT_FONT_YEAR)

    # Major tick at each year (longer), minor tick at each observation (shorter)
    ax.tick_params(axis='x', which='major', direction='out', length=5, width=0.8, pad=6)
    ax.xaxis.set_minor_locator(MultipleLocator(1.0 / f))
    ax.tick_params(axis='x', which='minor', direction='out', length=3, width=0.6)
    if f == 1:
        x_pad = 0.3
    ax.set_xlim(xs[0] - x_pad, xs[-1] + 0.3 / f)

    # ── Plot series (linespoints) ───────────────────────────────────────
    ax.plot(xs, z, color=JT_COLOR_SERIES, linewidth=1.0,
            marker='o', markersize=6.0,
            markerfacecolor=JT_COLOR_SERIES, markeredgewidth=0,
            solid_capstyle='round', zorder=3)

    # ── Reference lines ────────────────────────────────────────────────
    ax.axhline(y=0,  color='k',   lw=0.8, zorder=2)
    ax.axhline(y= 2, color='0.3', lw=1.0, linestyle='--', zorder=2)
    ax.axhline(y=-2, color='0.3', lw=1.0, linestyle='--', zorder=2)

    # ── Grid and border ────────────────────────────────────────────────
    ax.grid(True, axis='y', color='#CCCCCC', linewidth=0.5, zorder=0)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax.spines[sp].set_linewidth(1.6)

    # ── xlabel: mean / SE / sigma as percentages ───────────────────────
    se       = std_v / math.sqrt(n)
    fs_xlabel = 19 if size == 2 else 17
    ax.set_xlabel(
        f"$\\bar{{w}}\\,(\\sigma_{{\\bar{{w}}}})$ = {mean_v*100:.2f}%"
        f"  ({se*100:.2f}%)      $\\hat{{\\sigma}}_w$ = {std_v*100:.2f}%",
        fontsize=fs_xlabel,
    )

    # ── Title ──────────────────────────────────────────────────────────
    if title:
        fs_title = 24 if size == 2 else 22
        ax.set_title(title, fontsize=fs_title, fontweight='bold', pad=10)

    return fig


def plot_series_simple(ser, figsize=(12, 4), title=""):
    """Simplified wrapper for quick plotting."""
    return plot_series(ser, tsnobs=ser.nobs, timeout=0,
                       d=ser.d, ds=ser.ds, title=title)
