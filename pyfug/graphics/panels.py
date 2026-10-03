"""
Axes-level pieces of the Jenkins-Treadway style, for an engine's OWN figures.

The fug figures (`plot_combined`, `plot_series`, `plot_acf_pacf`,
`plot_forecast`) are built whole by pyfug. Some engines draw figures of their
own that have no fug counterpart — art's theoretical-vs-empirical acf, its
seasonal pattern — and need the same pieces on an axes they laid out
themselves. These used to be private helpers of `fue.plots`, imported from
outside; they live here now, public, so that pyfug is the one graphics engine.
"""

from __future__ import annotations

import numpy as np


def tj_spines(ax, sides=("left", "bottom")):
    """Only the given spines: the Treadway-Jenkins minimal border."""
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(sp in sides)


def seasonal_lags(freq: int, nlags: int) -> list[int]:
    """Where the seasonal grid of an acf goes: freq, 2·freq, 3·freq, or for
    annual data 3/6/9 (a third of the lags when there are more than 9)."""
    if freq > 1:
        return [freq * m for m in range(1, 4) if freq * m <= nlags]
    if nlags > 9:
        gap = int(round(nlags / 3))
        return [gap * m for m in range(1, 4) if gap * m <= nlags]
    return [x for x in (3, 6, 9) if x <= nlags]


def corr_on_axes(ax, vals, band, cmax, freq, label="", lw=None):
    """One acf or pacf on an existing axes: impulses, ±band dashed, the zero
    line, the seasonal grid, and five y ticks at cmax/2."""
    vals = np.asarray(vals, dtype=float)
    nlags = len(vals)
    lag_x = np.arange(1, nlags + 1)
    tj_spines(ax, sides=("left",))
    lw_imp = lw if lw is not None else (2.2 if nlags >= 30 else 3.0)
    ax.vlines(lag_x, 0, vals, colors="k", linewidth=lw_imp, zorder=3)
    ax.axhline(band, color="k", lw=1.0, linestyle="--", zorder=2)
    ax.axhline(-band, color="k", lw=1.0, linestyle="--", zorder=2)
    ax.axhline(0, color="k", lw=1.5, zorder=2)
    grid = seasonal_lags(freq, nlags)
    for xv in grid:
        ax.axvline(xv, color="0.5", lw=0.8, zorder=1)
    half = cmax / 2.0
    ax.set_ylim(-cmax, cmax)
    ax.set_yticks([-cmax, -half, 0.0, half, cmax])
    ax.yaxis.set_tick_params(direction="out", labelsize=9)
    ax.set_xticks(grid)
    ax.set_xticklabels([str(x) for x in grid], fontsize=9)
    ax.tick_params(axis="x", direction="out", length=3)
    ax.set_xlim(0.5, nlags + 0.5)
    if label:
        ax.set_title(label, loc="left", fontsize=11, pad=2)
