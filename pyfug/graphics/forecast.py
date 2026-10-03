"""
The forecast graph of fuf — atsw-gui engines/fuf/src/fufplot.c `fp_forecast`.

Two panels on a 324×453 pt canvas, as the EPS of FUF 1.08 had them:

- top: the last L observations and the L forecasts of the series (an annual
  change, or the level), one solid line with a point at each observation
  (larger where observed), and the forecast bands dashed;
- bottom: «ERR», the last L residuals as impulses, under the observations
  they belong to (the panel keeps the scale of the one above and stops at the
  forecast origin), with the zero line and a dashed band of two standard
  deviations.

The figure takes plain arrays, so any engine can draw it. Which series, which
bands and in which units are the engine's decision (fuf: usfo.c
`forecast_graphic`, `forecast_graphic_BC`; fue: `forecast_graph_data`).
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure

from pyfug.graphics import fugplot as fp
from pyfug.graphics.base import jt_style

# fufplot.c. Las medidas están en puntos.
W, H = 324.0, 453.0
MARGIN_L, MARGIN_R = 38.0, 6.0
SZ_TITLE, SZ_TICK = 16.0, 12.0
LW_AXIS, LW_GRID, LW_LINE, LW_BAND, LW_IMPULSE = 0.80, 0.50, 0.80, 0.75, 1.40
TIC = 3.0
DOT_OBS, DOT_FOR = 2.35, 2.00


def _nice_step(rng: float, n: int) -> float:
    """1, 2, 2.5 o 5 por una potencia de diez, para unas n divisiones."""
    if not rng > 0.0 or n < 1:
        return 1.0
    raw = rng / n
    power = 10.0 ** math.floor(math.log10(raw))
    step = raw / power
    for s in (1.0, 2.0, 2.5, 5.0):
        if step <= s:
            return s * power
    return 10.0 * power


def _tick_label(v: float, step: float) -> str:
    """Los decimales que pide el paso, sin ceros que no dicen nada."""
    decimals, s = 0, step
    while decimals < 6 and abs(s - math.floor(s + 0.5)) > 1e-9:
        s *= 10.0
        decimals += 1
    text = f"{v + 0.0:.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _year_step(x0, x1, n, freq, every):
    """Un año cada cuántos, para que los rótulos no se monten."""
    w = fp.helv_width("0000", SZ_TICK) * 1.15
    if n < 2 or freq < 1:
        return every
    while every < 100 and (x1 - x0) * every * freq / (n - 1) < w:
        every += 1
    return every


def _panel(fig, x0, x1, y0, y1, n, v0, v1):
    ax = fig.add_axes([x0 / W, y0 / H, (x1 - x0) / W, (y1 - y0) / H])
    ax.set_xlim(0, n - 1)
    ax.set_ylim(v0, v1)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_linewidth(LW_AXIS)
    return ax


def _year_axis(ax, n, freq, first_year, first_season, every):
    """Una línea y un rótulo en cada primera estación de un año (cada `every`)."""
    pos, lbl = [], []
    year, season = int(first_year), int(first_season)
    for i in range(n):
        if season == 1 and (year - first_year) % every == 0:
            ax.axvline(i, color="k", lw=LW_GRID, zorder=1)
            pos.append(i)
            lbl.append(str(year))
        season += 1
        if season > freq:
            season, year = 1, year + 1
    ax.set_xticks(pos)
    ax.set_xticklabels(lbl, fontsize=SZ_TICK, fontfamily=fp.FAMILY)
    # fd_text en y0 - SZ_TICK - 3: la parte alta de los dígitos queda a
    # unos 3 + 0.28·SZ_TICK puntos del eje.
    ax.tick_params(axis="x", length=0, pad=3.0 + 0.282 * SZ_TICK)


def _yaxis(ax, v0, v1, step):
    start = math.ceil(v0 / step - 1e-9) * step
    ticks, v = [], start
    while v <= v1 + 1e-9 * abs(v1):
        ticks.append(v)
        v += step
    ax.set_yticks(ticks)
    ax.set_yticklabels([_tick_label(t, step) for t in ticks], fontsize=SZ_TICK,
                       fontfamily=fp.FAMILY)
    ax.tick_params(axis="y", direction="out", length=TIC, width=LW_AXIS, pad=2.0)


@jt_style
def plot_forecast(y, band, band2, err, L, sigma, freq, first_year,
                  first_season, title, fig=None) -> Figure:
    """The forecast graph of fuf (fp_forecast).

    Parameters
    ----------
    y : array of 2L
        The last L observations, then the L forecasts.
    band, band2 : arrays of 2L
        Upper and lower forecast bands; only entries L..2L-1 are used.
    err : array of L
        The last L residuals.
    L : int
        Number of observations shown, equal to the number of forecasts.
    sigma : float
        Residual standard deviation, in the units of `err`.
    freq, first_year, first_season : int
        Frequency and the date of y[0].
    title : str
        Title of the top panel («LRC anual (%)», «Annual change», «LEVEL»).
    """
    y = np.asarray(y, dtype=float)
    band = np.asarray(band, dtype=float)
    band2 = np.asarray(band2, dtype=float)
    err = np.asarray(err, dtype=float)
    n = 2 * L
    fig = fp.new_canvas(W, H, fig)
    x0, x1 = MARGIN_L, W - MARGIN_R
    every = 1 if freq == 12 else (2 if freq == 4 else 10)   # as in FUF 1.08

    # ── [1] the panel of the forecasts ─────────────────────────────────────
    y0, y1 = H - 200.0, H - 30.0
    v0 = min(float(y.min()), float(band2[L:n].min()))
    v1 = max(float(y.max()), float(band[L:n].max()))
    step = _nice_step(v1 - v0, 5)
    v0 = math.floor(v0 / step) * step
    v1 = math.ceil(v1 / step) * step

    fig.text((x0 - 20.0) / W, (y1 + 14.0) / H, title, ha="left", va="baseline",
             fontsize=SZ_TITLE, fontweight="bold", fontfamily=fp.FAMILY)
    ax = _panel(fig, x0, x1, y0, y1, n, v0, v1)
    _year_axis(ax, n, freq, first_year, first_season,
               _year_step(x0, x1, n, freq, every))
    _yaxis(ax, v0, v1, step)

    xf = np.arange(L, n)
    for b in (band, band2):
        ax.plot(xf, b[L:n], color="k", lw=LW_BAND,
                dashes=(1.6 / LW_BAND, 2.2 / LW_BAND), zorder=2, clip_on=False)
    ax.plot(np.arange(n), y, color="k", lw=LW_LINE, zorder=3, clip_on=False)
    ax.plot(np.arange(L), y[:L], "o", color="k", markersize=2 * DOT_OBS,
            markeredgewidth=0, zorder=4, clip_on=False)
    ax.plot(xf, y[L:n], "o", color="k", markersize=2 * DOT_FOR,
            markeredgewidth=0, zorder=4, clip_on=False)

    # ── [2] the panel of the errors, under the observations it belongs to ──
    y0, y1 = 40.0, 195.0
    x1 = x0 + (x1 - x0) * (L - 1) / float(n - 1)

    cmax = 4.0 * sigma
    if len(err):
        cmax = max(cmax, float(np.abs(err[:L]).max()))
    if 4.0 * sigma < cmax <= 6.0 * sigma:
        cmax = 6.0 * sigma
    elif 6.0 * sigma < cmax <= 7.0 * sigma:
        cmax = 7.0 * sigma
    elif cmax > 7.0 * sigma:
        cmax = 10.0 * sigma
    if not cmax > 0.0:
        cmax = 1.0
    cmax += 0.10 * sigma
    # gnuplot recibía el rango con un decimal ("%1.1f").
    if math.floor(cmax * 10.0 + 0.5) > 0.0:
        cmax = math.floor(cmax * 10.0 + 0.5) / 10.0

    fig.text((x0 - 20.0) / W, (y1 + 14.0) / H, "ERR", ha="left", va="baseline",
             fontsize=SZ_TITLE, fontweight="bold", fontfamily=fp.FAMILY)
    ax2 = _panel(fig, x0, x1, y0, y1, L, -cmax, cmax)
    _year_axis(ax2, L, freq, first_year, first_season,
               _year_step(x0, x1, L, freq, every))
    step = math.floor(2.0 * sigma * 10.0 + 0.5) / 10.0
    if not step > 0.0:
        step = _nice_step(2.0 * cmax, 4)
    _yaxis(ax2, -cmax, cmax, step)

    ax2.axhline(0.0, color="k", lw=LW_AXIS, zorder=2)
    if sigma > 0.0:
        band_v = math.floor(2.0 * sigma * 10.0 + 0.5) / 10.0
        if not band_v > 0.0:
            band_v = 2.0 * sigma
        for v in (band_v, -band_v):
            ax2.axhline(v, color="k", lw=LW_BAND,
                        dashes=(3.0 / LW_BAND, 3.0 / LW_BAND), zorder=2)
    ax2.vlines(np.arange(L), 0.0, err[:L], colors="k", linewidth=LW_IMPULSE,
               capstyle="butt", zorder=3)
    return fig
