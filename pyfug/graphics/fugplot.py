"""
The pieces of fug C's figures — atsw-gui lib/fugplot/fugplot.c, in Python.

`plot_combined` (-c), `plot_series` (-a) and `plot_acf_pacf` (-b) are built from
the same panels the C uses, so the three figures share one geometry: the
canvas measured in points, each panel where the C puts it, and the C's fonts,
line widths and tick lengths (BUG-0007). Coordinates passed here are in POINTS
from the bottom-left corner of the canvas, as in fugplot.c.
"""

from __future__ import annotations

import math

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, MultipleLocator

from pyfug.graphics.base import _rotulo_estacional

# Geometría de fug C (fugplot.c). Las medidas están en puntos.
LAYOUT_BIG   = dict(W=720.0, H=252.0, tick=8.0, year=8.6, title=12.0, q=8.5,
                    stat=9.5, point=1.75)
LAYOUT_SMALL = dict(W=468.0, H=219.0, tick=7.5, year=8.6, title=11.0, q=7.5,
                    stat=8.5, point=1.55)
LW_AXIS, LW_THIN, LW_BAND, LW_ZERO, LW_CBAND = 0.40, 0.25, 0.375, 0.70, 0.30
TIC_MAJOR, TIC_MINOR, TIC_X = 3.5, 1.75, 2.0
# Helvetica, la del C; Nimbus Sans y Liberation Sans tienen sus métricas.
FAMILY = ["Nimbus Sans", "Liberation Sans", "DejaVu Sans"]


def layout(size: int) -> dict:
    return LAYOUT_BIG if size == 2 else LAYOUT_SMALL


def helv_width(text: str, size: float) -> float:
    """Ancho en puntos de un número en Helvetica (dígitos 0.556 em, '-' 0.333)."""
    return size * sum(0.333 if c == "-" else 0.556 for c in text)


def series_x0(L: dict, abs_max: float) -> float:
    """Borde izquierdo del panel de la serie: cabe el rótulo «-AbsMax»."""
    return 4.0 + helv_width("%d" % -int(abs_max), L["tick"]) + 1.5 + TIC_MAJOR


def new_canvas(W: float, H: float, fig=None):
    """Lienzo de W×H puntos, sin motor de maquetación: posiciones fijas."""
    if fig is None:
        fig = plt.figure(figsize=(W / 72.0, H / 72.0))
    fig.set_layout_engine("none")
    return fig


def _axes(fig, W, H, x0, x1, y0, y1):
    return fig.add_axes([x0 / W, y0 / H, (x1 - x0) / W, (y1 - y0) / H])


def _to_decimal_year(nobs, begyear, begtime, freq):
    """Decimal-year x-coordinates (same as fue._obs_to_decimal_year)."""
    xs, y, p = [], int(begyear), int(begtime)
    for _ in range(nobs):
        xs.append(y + (p - 1) / freq)
        p += 1
        if p > freq:
            p, y = 1, y + 1
    return xs


def series_panel(fig, L, W, H, x0, x1, y0, y1, ser, z, abs_max, timeout, tsby,
                 ax=None):
    """El panel de la serie tipificada (series_panel de fugplot.c)."""
    n, f = len(z), ser.freq
    if ax is None:
        ax = _axes(fig, W, H, x0, x1, y0, y1)

    # Decimal-year x-axis — adjust start for observations lost to differencing
    begyear = ser.begyear
    begtime = getattr(ser, 'begtime', 1)
    total_p = (int(begtime) - 1) + int(timeout)
    xs = _to_decimal_year(n, int(begyear) + total_p // f, total_p % f + 1, f)

    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax.spines[sp].set_linewidth(LW_AXIS)

    # Eje y: ±AbsMax; rótulo en los pares, marca menor en los impares.
    y_max = int(abs_max)
    ax.set_ylim(-abs_max, abs_max)
    ax.set_yticks(range(-y_max, y_max + 1, 2))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.tick_params(axis='y', which='major', direction='out', length=TIC_MAJOR,
                   width=LW_AXIS, pad=1.5, labelsize=L["tick"])
    ax.tick_params(axis='y', which='minor', direction='out', length=TIC_MINOR,
                   width=LW_AXIS)

    if f > 1:
        # La alineación de fug C, que corrigió Treadway (BUG-0006): el eje
        # arranca en el primer período del AÑO DE COMIENZO de la serie
        # original —rellenando lo que se pierde al diferenciar y lo que falta
        # hasta ese período— y hay una línea y un rótulo cada 2 años desde
        # ese año (fug.c: timeout = ornsop + begtime - 1; fugplot.c: líneas en
        # -tmornsop + 2·f·i, rótulo tsby + 2i).
        first_yr = int(begyear)
        x_left = first_yr
        tick_pos, tick_lbl = [], []
        for yr in range(first_yr, int(xs[-1]) + 2, 2):
            if yr <= xs[-1] + 1e-9:          # C: X > xmax ends the loop
                if yr > first_yr:            # C: the first line is the axis
                    ax.axvline(yr, color='k', lw=LW_THIN, zorder=1)
                tick_pos.append(yr)
                tick_lbl.append(_rotulo_estacional(yr, f))
    else:
        # ── ANUAL (f == 1) — el convenio de fug C, no un parche ────────────
        #
        #   fug.c:332     ornsop  = nrdiff + freq*nadiff
        #   fug.c:382     timeout = ornsop + ser->outyear        ← sólo anuales
        #   fug.c:404     ... , ser->begyear - ser->outyear , ...
        #   gnuplot_graphics.c:493-517  líneas y rótulos cada 20 años con
        #                 f=1; el rótulo i-ésimo es tsby + 2*i*10
        #
        # `outyear` («year before graph», fug.h:58) es un margen izquierdo en
        # años, propiedad de la serie y sólo de las anuales (BUG-0002). El eje
        # arranca en el primer rótulo, `begyear - outyear`.
        first_yr = int(tsby)
        x_left = min(first_yr, xs[0])
        tick_pos, tick_lbl = [], []
        k = 0
        while first_yr + 20 * k <= xs[-1]:
            yr = first_yr + 20 * k
            if k > 0:                        # C: the first label has no line
                ax.axvline(yr, color='k', lw=LW_THIN, zorder=1)
            tick_pos.append(yr)
            tick_lbl.append(str(yr))
            k += 1

    # Rótulos de año bajo el eje (fd_text en y0 - TIC_X - 2.5 - 0.718·year):
    # como marcas de largo 0 con el texto a TIC_X + 2.5 pt.
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_lbl, fontsize=L["year"], fontfamily=FAMILY)
    ax.tick_params(axis='x', which='major', length=0, pad=TIC_X + 2.5)
    # Una marca por observación, de TIC_X, desde el borde del eje.
    ax.xaxis.set_minor_locator(FixedLocator(
        np.arange(x_left, xs[-1] + 1e-9, 1.0 / f)))
    ax.tick_params(axis='x', which='minor', direction='out', length=TIC_X,
                   width=LW_AXIS)
    ax.set_xlim(x_left, xs[-1])
    for t in ax.get_yticklabels():
        t.set_fontfamily(FAMILY)

    # La serie: línea fina y discos de radio L["point"].
    ax.plot(xs, z, color='k', linewidth=LW_THIN, marker='o',
            markersize=2.0 * L["point"], markerfacecolor='k',
            markeredgewidth=0, zorder=3, clip_on=False)

    # Cero sólido fino y bandas ±2 discontinuas (2.5/2.5).
    ax.axhline(y=0, color='k', lw=LW_THIN, zorder=2)
    for v in (-2, 2):
        ax.axhline(y=v, color='k', lw=LW_BAND,
                   dashes=(2.5 / LW_BAND, 2.5 / LW_BAND), zorder=2)
    return ax


def _numero(v: float) -> str:
    """Como `number` del C: "0.30" -> "0.3", "0.00" -> "0", "-0" -> "0"."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def corr_panel(fig, L, W, H, x0, x1, y0, y1, vals, nlags, f, n, cmax, label):
    """Un panel de acf o pacf (corr_panel de fugplot.c)."""
    ax = _axes(fig, W, H, x0, x1, y0, y1)
    ax.set_xlim(0, nlags)
    ax.set_ylim(-cmax, cmax)

    # Retardos estacionales: líneas finas de todo el alto y su rótulo.
    if f > 1:
        marks = [f * m for m in range(1, 4) if f * m <= nlags]
    elif nlags > 9:
        gap = int(round(nlags / 3))
        marks = [gap * m for m in range(1, 4)]
    else:
        marks = [3, 6] + ([9] if nlags == 9 else [])
    for xv in marks:
        ax.axvline(xv, color='k', lw=LW_THIN, zorder=1)
    ax.set_xticks(marks)
    ax.set_xticklabels([str(x) for x in marks], fontsize=L["tick"],
                       fontfamily=FAMILY)
    ax.tick_params(axis='x', length=0, pad=3.0)

    # Bandas ±2/√n (sólo si caben) y la línea del cero.
    conf = 2.0 / math.sqrt(n)
    if conf < cmax:
        for v in (-conf, conf):
            ax.axhline(y=v, color='k', lw=LW_CBAND,
                       dashes=(2.0 / LW_CBAND, 2.0 / LW_CBAND), zorder=2)
    ax.axhline(y=0, color='k', lw=LW_ZERO, zorder=2)

    # Barras de extremos rectos: 1.75 o 2.25 pt, como mucho 0.6 del hueco.
    bw = 1.75 if nlags >= 30 else 2.25
    bw = min(bw, 0.6 * (x1 - x0) / nlags)
    v = np.clip(np.asarray(vals, dtype=float), -cmax, cmax)
    ax.vlines(np.arange(1, nlags + 1), 0, v, colors='k', linewidth=bw,
              capstyle='butt', zorder=3)

    # Eje izquierdo con 5 marcas en cmax/2.
    ticks = [k * cmax / 2.0 for k in range(-2, 3)]
    ax.set_yticks(ticks)
    ax.set_yticklabels([_numero(t) for t in ticks], fontsize=L["tick"],
                       fontfamily=FAMILY)
    ax.tick_params(axis='y', direction='out', length=TIC_MAJOR,
                   width=LW_AXIS, pad=1.5)
    for sp in ('top', 'right', 'bottom'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_linewidth(LW_AXIS)

    # Título del panel, centrado 5 pt por encima, sin negrita.
    ax.annotate(label, xy=(0.5, 1.0), xycoords="axes fraction",
                xytext=(0, 5.0), textcoords="offset points",
                ha="center", va="baseline", annotation_clip=False,
                fontsize=10.0 if nlags >= 30 else 9.0, fontfamily=FAMILY)
    return ax


def q_label(fig, W, H, xc, y, size, q_df, q_stat):
    """«Q(k) = x», centrada en xc, con la línea base en y (puntos)."""
    fig.text(xc / W, y / H, f"Q({q_df}) = {q_stat:.1f}", ha="center",
             va="baseline", fontsize=size, fontfamily=FAMILY)


def title(fig, W, H, text, size, x, y, align="right", xmax=0.0):
    """El título en negrita. Con `xmax` y alineado a la izquierda, se corre a
    la izquierda lo justo para terminar, como mucho, en `xmax` (fugplot.c)."""
    t = fig.text(x / W, y / H, text, ha=align, va="baseline", fontsize=size,
                 fontweight="bold", fontfamily=FAMILY)
    if xmax > 0.0 and align == "left":
        ancho = t.get_window_extent(fig.canvas.get_renderer()).width
        ancho_pt = ancho * 72.0 / fig.dpi
        if x + ancho_pt > xmax:
            t.set_x((xmax - ancho_pt) / W)
    return t


def statistics(fig, L, W, H, xc, y, mean, sd, n):
    """w̄ ( σ̂_w̄ ) = m% (se%)      σ̂_w = sd%, centrada en xc (puntos)."""
    se = sd / math.sqrt(n)
    fig.text(xc / W, y / H,
             r"$\bar{w}$ ( $\hat{\sigma}_{\bar{w}}$ ) = "
             f"{100 * mean:.2f}% ({100 * se:.2f}%)"
             r"        $\hat{\sigma}_w$ = " f"{100 * sd:.2f}%",
             ha="center", va="baseline", fontsize=L["stat"], fontfamily=FAMILY)


def default_lags(nobs: int, freq: int) -> int:
    """Retardos por defecto de la acf/pacf: `default_lags` de plotsupport.c.

    La misma regla para el .out, los gráficos y la GUI. Aquí se le añade el
    tope de la PACF de pyfug (Durbin-Levinson sobre n/2), que el C no tiene.
    """
    if nobs < 3 * (freq + 1):
        lags = nobs - freq // 2
    elif freq == 1 and nobs > 200:
        lags = 45
    elif freq == 1:
        lags = 9
    else:
        lags = 3 * (freq + 1)
    lags = min(lags, nobs - 2, max(1, nobs // 2 - 1))
    return max(1, lags)
