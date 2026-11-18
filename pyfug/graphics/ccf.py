"""The two-sided CCF, in the format Treadway approved — the suite's one drawing.

Two approved prototypes agree on it, GraphMaker (``ccfgrafico.cpp``) and drvus
(``ccf2_1.eps`` with its ``ccf.c``), and atsw-gui's C draws it with
``lib/ccfplot``: a wide, low panel; lags -K .. K, symmetric; bars; the bands at
+-2/sqrt(N); a dashed vertical at lag 0 dividing the two sides; the series that
leads at k > 0 first in the title ("input - output"); Hosking's portmanteau
below, labelled P — GraphMaker's choice, "so as not to confuse it with
Ljung-Box's Q".

The two sides say different things, and that is the point of the figure: at
k > 0 the influence of the input on the output (the transfer); at k < 0 the
influence of the output on the input — if there is anything there that is not
noise, the input is not exogenous.

This module was drvarma's (``drvarma.plots._draw_ccf_panel``), which drtran
and sima borrowed; it lives here now, with the rest of the suite's figures.
pyfug draws; the statistic P is the engines' (it discounts the ARMA
parameters of the model behind the residuals, drvarma BUG-0015), and comes in
as a label.
"""

from __future__ import annotations

import os

import numpy as np

#: The formats a figure is written in by `save_ccf`: the raster for a screen
#: or a chat, and the vectors — high definition, as the C's EPS — for a report
#: (SVG) and for print or LaTeX (PDF).
FORMATS = ("png", "svg", "pdf")


def ccf_default_lags(freq: int) -> int:
    """GraphMaker's lags for the CCF: 7 for annual data, 15 for quarterly; for
    monthly it let the analyst choose 8 to 39, and 12 is the default atsw-gui's
    ``lib/ccfplot`` takes (``ccf_lags_por_defecto``)."""
    f = int(freq)
    return {1: 7, 4: 15, 12: 12}.get(f, 3 * f if f > 1 else 7)


def ccf_scale(value: float) -> float:
    """GraphMaker's vertical scale: +-0.4 with marks every 0.2, enlarged to 0.6,
    0.8 or 1.0 when a bar or the band does not fit (``lib/ccfplot``'s
    ``escala``)."""
    for e in (0.4, 0.6, 0.8, 1.0):
        if value <= e * 0.98:
            return e
    return 1.0


def p_label(stat: float, df: int) -> str:
    """GraphMaker's label for Hosking's portmanteau: ``P ( df ) = value``; with
    no degrees of freedom left (K <= p + q), the value and why."""
    return "P ( %d ) = %.1f" % (df, stat) if df > 0 else "P = %.1f  (K ≤ p + q)" % stat


def draw_ccf_panel(ax, rho, lags: int, n: int, freq: int, title: str,
                   p_text: str = "", band=None, cmax: float | None = None) -> None:
    """One two-sided CCF panel on the axes ``ax``.

    ``rho``: the 2*lags + 1 correlations, lags -K .. K (``pyfug.statistics.ccf``).
    ``n``: the observations behind them (the band is 2/sqrt(n)). ``title``: the
    series that leads at k > 0 first, "A - B". ``p_text``: the statistic, centred
    below (`p_label`). ``band``: the half-width of the band, a scalar or one value
    per lag (a series that is not white needs its own — Bartlett's for two
    unrelated autocorrelated series, Jenkins and Alavi 1981, (3.13) — and the
    band then follows the lag). ``cmax`` fixes the scale, so that stacked panels
    share it.
    """
    rho = np.asarray(rho, float)
    if band is None:
        band = 2.0 / np.sqrt(n)
    band = np.broadcast_to(np.asarray(band, float), (2 * lags + 1,))
    if cmax is None:
        cmax = ccf_scale(max(float(np.max(np.abs(rho))), float(band.max())))
    x = np.arange(-lags, lags + 1)
    ax.axhline(0.0, color="k", lw=1.0, zorder=2)                  # the zero
    if np.all(band == band[0]):
        ax.axhline(band[0], color="k", ls=":", lw=1.2, zorder=2)
        ax.axhline(-band[0], color="k", ls=":", lw=1.2, zorder=2)
    else:                                                         # by lag
        ax.plot(x, band, color="k", ls=":", lw=1.2, zorder=2, drawstyle="steps-mid")
        ax.plot(x, -band, color="k", ls=":", lw=1.2, zorder=2, drawstyle="steps-mid")
    ax.axvline(0.0, color="k", ls="--", lw=0.8, zorder=1)         # the two sides
    ax.bar(x, np.clip(rho, -cmax, cmax), width=0.21, color="k", lw=0, zorder=3)
    ax.set_ylim(-cmax, cmax)
    ax.set_yticks([-cmax, -cmax / 2.0, 0.0, cmax / 2.0, cmax])
    ax.set_xlim(-lags - 0.5, lags + 0.5)
    if freq > 1 and lags > 8:                   # GraphMaker: 12 a month, 4 a quarter
        step = freq
    else:                                       # 2 a year (or with 8 monthly lags)
        step = 2 if lags <= 12 else 4
    ticks = list(range(0, lags + 1, step))
    ax.set_xticks([-t for t in reversed(ticks[1:])] + ticks)
    ax.tick_params(axis="both", direction="out", length=3, labelsize=9)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title(title, fontsize=11)                              # centred above
    if p_text:
        ax.set_xlabel(p_text, fontsize=10, labelpad=4)            # centred below


def plot_ccf(rho, lags: int, n: int, freq: int, title: str, p_text: str = "",
             band=None, cmax: float | None = None, ax=None):
    """The figure of one CCF panel (`draw_ccf_panel`), wide and low as the
    approved prototype (360 x 126 points). Returns the figure."""
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(9.0, 3.2))
    else:
        fig = ax.get_figure()
    draw_ccf_panel(ax, rho, lags, n, freq, title, p_text, band=band, cmax=cmax)
    fig.tight_layout()
    return fig


def save_ccf(fig, path: str, formats=FORMATS, dpi: int = 130) -> list:
    """Write ``fig`` in each of ``formats`` next to ``path`` (its extension is
    replaced): the PNG for a screen or a chat, SVG and PDF in vectors. Returns
    the paths written, in the order of ``formats``."""
    base, _ext = os.path.splitext(path)
    out = []
    for fmt in formats:
        p = f"{base}.{fmt}"
        fig.savefig(p, format=fmt, dpi=dpi if fmt == "png" else None,
                    bbox_inches="tight")
        out.append(p)
    return out
