"""
Histogram plot — Jenkins-Treadway style.

Produces a histogram of the (standardized) series overlaid with
a normal distribution curve. Displays skewness (S), kurtosis (K),
and Jarque-Bera (JB) statistics as the xlabel.

Bin width: fixed 0.5 units (matching FUG C bandwidth = 0.5),
giving 16 bins for xmax=4, 32 bins for xmax=8.
Y-axis: percentage of observations (matching C).
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy import stats

from pyfug.statistics import descriptive_stats
from pyfug.graphics.base import (
    JT_COLOR_HIST_FILL, JT_COLOR_NORMAL, JT_COLOR_SERIES,
    JT_LINE_WIDTH_BORDER, JT_LINE_WIDTH_SERIES,
)


def plot_histogram(ser, d=0, ds=0, title="", fig=None) -> Figure:
    """Plot histogram with normal overlay — Jenkins-Treadway style.

    Parameters
    ----------
    ser : Tseries
        Time series (data will be standardized).
    d : int
        Regular differencing order.
    ds : int
        Seasonal differencing order.
    title : str
        Plot title.
    fig : Figure, optional
        Existing figure.

    Returns
    -------
    matplotlib.figure.Figure
    """
    data = np.asarray(ser.data, dtype=float)
    n = len(data)
    mean_val = float(np.mean(data)) if ser.mean == 0.0 else float(ser.mean)
    std_val  = float(np.std(data, ddof=0)) if ser.var == 0.0 else float(np.sqrt(ser.var))

    # Standardize
    z = (data - mean_val) / std_val if std_val > 1e-10 else data - mean_val

    # Compute statistics
    if ser.skew == 0.0:
        stats_dict = descriptive_stats(data)
        skew_val = stats_dict["skew"]
        kurt_val = stats_dict["kurt"]
        jb_val   = stats_dict["jb"]
    else:
        skew_val = ser.skew
        kurt_val = ser.kurt
        jb_val   = ser.jarquebera

    jb_pval = float(stats.chi2.sf(jb_val, df=2))

    # ── Determine histogram range (matching C: xmax = 4 or 8) ──────────
    abs_z = max(abs(float(np.min(z))), abs(float(np.max(z))))
    xmax = 4.0 if abs_z <= 4.0 else 8.0

    # ── Fixed bin width 0.5 (matching C bandwidth = 0.5) ────────────────
    BIN_WIDTH = 0.5
    n_bins    = int(round(2 * xmax / BIN_WIDTH))   # 16 or 32
    edges     = np.linspace(-xmax, xmax, n_bins + 1)

    counts, _ = np.histogram(z, bins=edges)
    # C: prob[i] = 100*2*freqs[i]/nobs  → density % (per unit), not frequency %
    pct = 200.0 * counts / n if n > 0 else counts.astype(float)

    # ── Plot ─────────────────────────────────────────────────────────────
    if fig is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        ax = fig.gca() if len(fig.axes) > 0 else fig.add_subplot(111)

    # Bar chart in percentages
    bar_centers = 0.5 * (edges[:-1] + edges[1:])
    ax.bar(bar_centers, pct, width=BIN_WIDTH * 0.95,
           color=JT_COLOR_HIST_FILL, edgecolor="black",
           linewidth=0.8, align='center')

    # Normal curve overlay scaled to percentage
    x_grid  = np.linspace(-xmax, xmax, 300)
    pdf     = stats.norm.pdf(x_grid, 0, 1)
    pdf_pct = pdf * 100        # density % per unit (matches C: same scale as bars)
    ax.plot(x_grid, pdf_pct, color=JT_COLOR_NORMAL,
            linewidth=JT_LINE_WIDTH_SERIES + 0.5)

    # ── Styling ──────────────────────────────────────────────────────────
    ax.set_xlim(-xmax, xmax)
    ax.set_ylim(bottom=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(JT_LINE_WIDTH_BORDER)
    ax.spines["bottom"].set_linewidth(JT_LINE_WIDTH_BORDER)

    # xlabel with mathtext S, K, JB and p-value
    ax.set_xlabel(
        f"$S$ = {skew_val:.1f}       $K$ = {kurt_val:.1f}"
        f"        $JB$ = {jb_val:.1f}  ({jb_pval:.3f})",
        fontsize=14,
    )
    ax.set_ylabel("%", fontsize=16)
    ax.set_xticks(np.arange(-xmax, xmax + 1, 2 if xmax == 4 else 4))
    ax.tick_params(axis="both", direction="out")

    ax.grid(True, axis="both", color="#DDDDDD", linewidth=0.5)
    ax.axvline(x=0, color=JT_COLOR_SERIES, linewidth=0.8)

    if title:
        ax.set_title(title, fontsize=18, fontweight="bold", pad=10)

    return fig
