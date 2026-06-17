"""
Mean vs Standard-Deviation scatter plot — Jenkins-Treadway style.

Replicates fug C graph_m_dt() / meandv() from m_dt.c.

Each group of `nog` consecutive observations contributes one point.
Both group means and group std-devs are standardized before plotting so
axes are dimensionless and symmetric around zero.

Interpretation:
  σ ∝ μ  (positive slope) → log transform (λ = 0)
  σ ≈ const (flat)        → no transform  (λ = 1)
  intermediate slope      → λ ∈ (0, 1)

Public functions:
  plot_mean_deviation(ser, ...)          — single panel
  plot_mean_deviation_pair(ser, ...)     — nivel + log side by side
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure

from pyfug.graphics.base import (
    JT_COLOR_SERIES, JT_LINE_WIDTH_BORDER,
)


def meandv(y: np.ndarray, nog: int):
    """Split y into ng = n//nog groups; return (standardized_means, standardized_stdevs).

    Matches C meandv(): population std (ddof=0), standardized by mean/std of group stats.
    """
    ng = len(y) // nog
    groups = y[: ng * nog].reshape(ng, nog)
    m  = groups.mean(axis=1)
    dt = groups.std(axis=1, ddof=0)   # C Stdev = sqrt(sum/n)

    m_std  = m.std(ddof=0)
    dt_std = dt.std(ddof=0)
    ms  = (m  - m.mean())  / (m_std  if m_std  > 1e-12 else 1.0)
    dts = (dt - dt.mean()) / (dt_std if dt_std > 1e-12 else 1.0)
    return ms, dts


def _draw_panel(ax, ms, dts, title: str = "") -> None:
    """Draw a single m-dt scatter panel onto `ax`."""
    raw_max = max(float(np.abs(ms).max()), float(np.abs(dts).max()))
    abs_max = raw_max * 1.1 if raw_max > 0 else 1.0

    ax.scatter(ms, dts, s=25, color=JT_COLOR_SERIES, zorder=3)

    ax.set_xlim(-abs_max, abs_max)
    ax.set_ylim(-abs_max, abs_max)
    ax.set_aspect("equal", adjustable="box")

    tick_val = round(abs_max, 1)
    ax.set_xticks([-tick_val, 0.0, tick_val])
    ax.set_yticks([-tick_val, 0.0, tick_val])
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.tick_params(axis="both", direction="out")

    ax.axhline(0, color="k", linewidth=0.6, zorder=1)
    ax.axvline(0, color="k", linewidth=0.6, zorder=1)
    ax.grid(True, color="#DDDDDD", linewidth=0.5, zorder=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(JT_LINE_WIDTH_BORDER)
    ax.spines["bottom"].set_linewidth(JT_LINE_WIDTH_BORDER)

    ax.set_xlabel("Mean", fontsize=14)
    ax.set_ylabel("Standard-Deviation", fontsize=14)
    if title:
        ax.set_title(title, fontsize=15, fontweight="bold", pad=8)


def plot_mean_deviation(ser, nog: int = 0, title: str = "", fig=None) -> Figure:
    """Mean vs Standard-Deviation scatter chart (Jenkins-Treadway style).

    Parameters
    ----------
    ser : Tseries or TimeSeries
        Time series. Uses ``ser.data`` and ``ser.freq``.
    nog : int
        Observations per group. 0 → use ser.freq (one year per group);
        falls back to 5 when freq <= 1.
    title : str
        Plot title.
    fig : Figure, optional
        Existing figure to draw into.

    Returns
    -------
    matplotlib.figure.Figure
    """
    data    = np.asarray(ser.data, dtype=float)
    n       = len(data)
    freq = int(getattr(ser, "freq", 1)) or 1

    if nog <= 0:
        nog = freq if freq > 1 else 5

    ng = n // nog
    if ng < 2:
        raise ValueError(
            f"Not enough data for {ng} groups of {nog} obs "
            f"(need n >= {2 * nog}, got {n})"
        )

    ms, dts = meandv(data, nog)

    if fig is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        ax = fig.gca() if len(fig.axes) > 0 else fig.add_subplot(111)

    _draw_panel(ax, ms, dts, title=title)
    # Single-panel uses slightly larger fonts
    ax.set_xlabel("Mean", fontsize=16)
    ax.set_ylabel("Standard-Deviation", fontsize=16)
    if title:
        ax.set_title(title, fontsize=18, fontweight="bold", pad=10)

    return fig


def plot_mean_deviation_pair(ser, nog: int = 0,
                             name: str = "", fig=None) -> Figure:
    """Side-by-side m-dt comparison: level (left) vs log (right).

    Both panels share the same group size. Useful for deciding λ in one view.

    Parameters
    ----------
    ser : Tseries or TimeSeries
        Time series in original (level) units.
    nog : int
        Observations per group. 0 → use ser.freq.
    name : str
        Series name used in panel titles (e.g. "IPC_DE").
    fig : Figure, optional
        Existing figure.

    Returns
    -------
    matplotlib.figure.Figure
    """
    data = np.asarray(ser.data, dtype=float)
    freq = int(getattr(ser, "freq", 1)) or 1
    if nog <= 0:
        nog = freq if freq > 1 else 5

    ng = len(data) // nog
    if ng < 2:
        raise ValueError(f"Not enough data for {ng} groups of {nog} obs")

    ms_lev, dts_lev = meandv(data, nog)
    ms_log, dts_log = meandv(np.log(data), nog)

    if fig is None:
        fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    else:
        axes = fig.axes[:2]

    _draw_panel(axes[0], ms_lev, dts_lev, title=name or "Level")
    _draw_panel(axes[1], ms_log, dts_log, title=f"ln {name}" if name else "Log")

    fig.tight_layout(pad=1.5)
    return fig
