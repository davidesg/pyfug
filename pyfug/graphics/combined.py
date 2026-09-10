"""
Combined plot: time series + ACF/PACF — Jenkins-Treadway style.

Layout from gnuplot_graphics.c gnuplot_File_PlotSer_CorrSer.
Panel width/height ratios derived from C gnuplot canvas sizes:
  size==2, lags≥30: series/acf width 1.32/0.63=2.095, ACF h=0.46, PACF h=0.385
  size==1, lags≥15: width 0.852/0.423=2.014, ACF h=0.41, PACF h=0.37
  size==1, lags<15:  width 0.852/0.383=2.225, ACF h=0.41, PACF h=0.37
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from pyfug.statistics import (
    acf, pacf, chi_test, acf_pacf_max, series_max, series_size
)
from pyfug.graphics.base import JT_FONT_YEAR, _tics_size


def _layout_params(size2: bool, nlags: int):
    """Return (w_ratio, h_acf, h_pacf) from C gnuplot canvas proportions."""
    if size2:
        return 2.095, 0.46, 0.385   # C: series 1.32, ACF 0.63; heights 0.46, 0.385
    elif nlags >= 15:
        return 2.014, 0.41, 0.37    # C: series 0.852, ACF 0.423
    else:
        return 2.225, 0.41, 0.37    # C: series 0.852, ACF 0.383


def _to_decimal_year(nobs, begyear, begtime, freq):
    """Decimal-year x-coordinates (same as fue._obs_to_decimal_year)."""
    xs, y, p = [], int(begyear), int(begtime)
    for _ in range(nobs):
        xs.append(y + (p - 1) / freq)
        p += 1
        if p > freq:
            p, y = 1, y + 1
    return xs


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
    if tsby is None:
        tsby = ser.begyear

    size    = series_size(tsnobs, f)
    abs_max = series_max(z)

    # ── ACF/PACF parameters ─────────────────────────────────────────────
    if nlags == 0:
        if n < 3 * (f + 1):
            nlags = max(1, n - f // 2)
        else:
            nlags = max(10, 3 * (f + 1))
    # PACF (statsmodels Levinson-Durbin) requires nlags < n/2; cap both panels
    # to the same feasible maximum so ACF and PACF stay consistent on short
    # series. The Jenkins-Treadway convention (3·(f+1)) is preserved whenever
    # the sample is long enough (n > 6·(f+1)).
    nlags = min(nlags, n - 1, max(1, n // 2 - 1))

    acf_vals  = acf(data_raw, nlags)
    pacf_vals = pacf(data_raw, nlags)

    if cbands > 0:
        cmax = cbands
    else:
        cmax = acf_pacf_max(acf_vals, pacf_vals)

    conf    = 2.0 / np.sqrt(n)
    q_stat  = chi_test(data_raw, nlags)
    q_df    = nlags - npar
    q_label = f"Q({q_df}) = {q_stat:.1f}"

    # ── Layout: GridSpec with C-derived proportions ──────────────────────────
    w_ratio, h_acf, h_pacf = _layout_params(size == 2, nlags)
    figw = 15.0 if size == 2 else 12.0
    if fig is None:
        fig = plt.figure(figsize=(figw, 5.5), layout='constrained')

    gs = gridspec.GridSpec(2, 2, figure=fig,
                           width_ratios=[w_ratio, 1.0],
                           height_ratios=[h_acf, h_pacf],
                           hspace=0.06, wspace=0.05)
    ax_s   = fig.add_subplot(gs[:, 0])
    ax_acf = fig.add_subplot(gs[0, 1])
    ax_pac = fig.add_subplot(gs[1, 1])

    # ── Font sizes (matching C) ──────────────────────────────────────────
    fs_title  = 24 if size == 2 else 22
    fs_xlabel = 16 if size == 2 else 14
    fs_acf    = 20 if nlags >= 30 else 18
    fs_q      = 17 if (f > 4 or (f == 1 and n > 200)) else 15

    if title:
        fig.suptitle(title, fontsize=fs_title, fontweight='bold')

    # ── SERIES PANEL ─────────────────────────────────────────────────────

    # Decimal-year x-axis — adjust start for observations lost to differencing
    begyear  = ser.begyear
    begtime  = getattr(ser, 'begtime', 1)
    total_p  = (int(begtime) - 1) + int(timeout)
    adj_year = int(begyear) + total_p // f
    adj_per  = total_p % f + 1
    xs = _to_decimal_year(n, adj_year, adj_per, f)

    # Spines: left + bottom only (C: border 3 lw 1.6)
    for sp in ('top', 'right'):
        ax_s.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax_s.spines[sp].set_linewidth(1.6)

    # Y-axis: every 2σ major, every 1σ minor (C: ytics nomirror 2, mytics 2)
    y_max = int(abs_max)
    ax_s.set_ylim(-y_max - 0.15, y_max + 0.15)
    ax_s.set_yticks(range(-y_max, y_max + 1, 2))
    ax_s.yaxis.set_minor_locator(plt.MultipleLocator(1))
    ax_s.tick_params(axis='y', direction='out', labelsize=11)

    # X-axis: year boundary tick lines and labels
    if f > 1:
        x0, x1 = xs[0], xs[-1]
        step = 2 if (x1 - x0) > 5 else 1
        first_yr = (int(x0) // step) * step
        x_pad = max(0.3 / f, x0 - first_yr + 0.5 / f)
        tick_pos, tick_lbl = [], []
        for yr in range(first_yr, int(x1) + 2, step):
            if yr <= x1 + 1.0 / f:
                ax_s.axvline(yr, color='k', lw=0.5, zorder=1)
                tick_pos.append(yr)
                tick_lbl.append(str(yr))
        ax_s.set_xticks(tick_pos)
        ax_s.set_xticklabels(tick_lbl, fontsize=JT_FONT_YEAR)
    else:
        # Annual series (f==1): the f>1 branch above never runs, so x_pad would be
        # undefined at set_xlim below. Define it here (see TODO.md, annual-freq bug).
        x_pad = 0.3 / f
        step = 10
        first_yr = (int(xs[0]) // step) * step
        tick_pos = [yr for yr in range(first_yr, int(xs[-1]) + step + 1, step)
                    if xs[0] <= yr <= xs[-1]]
        ax_s.set_xticks(tick_pos)
        ax_s.set_xticklabels([str(y) for y in tick_pos], fontsize=JT_FONT_YEAR)

    # Major tick at each year (longer), minor tick at each observation (shorter)
    ax_s.tick_params(axis='x', which='major', direction='out', length=5, width=0.8, pad=6)
    ax_s.xaxis.set_minor_locator(MultipleLocator(1.0 / f))
    ax_s.tick_params(axis='x', which='minor', direction='out', length=3, width=0.6)
    ax_s.set_xlim(xs[0] - x_pad, xs[-1] + 0.3 / f)

    # Plot standardized series (linespoints)
    ax_s.plot(xs, z, color='k', linewidth=1.0,
              marker='o', markersize=6.0,
              markerfacecolor='k', markeredgewidth=0,
              solid_capstyle='round', zorder=3)

    # Reference lines
    ax_s.axhline(y=0,  color='k',   lw=0.8, zorder=2)
    ax_s.axhline(y= 2, color='0.3', lw=1.0, linestyle='--', zorder=2)
    ax_s.axhline(y=-2, color='0.3', lw=1.0, linestyle='--', zorder=2)

    # Horizontal grid
    ax_s.grid(True, axis='y', color='#CCCCCC', linewidth=0.4, zorder=0)

    # xlabel: mean / SE / sigma as percentages (C: Arial 19/17)
    se       = std_v / math.sqrt(n)
    mean_pct = mean_v * 100
    se_pct   = se * 100
    std_pct  = std_v * 100
    ax_s.set_xlabel(
        f"$\\bar{{w}}\\,(\\sigma_{{\\bar{{w}}}})$ = {mean_pct:.2f}%"
        f"  ({se_pct:.2f}%)      $\\hat{{\\sigma}}_w$ = {std_pct:.2f}%",
        fontsize=fs_xlabel,
    )

    # ── ACF PANEL ────────────────────────────────────────────────────────
    _draw_acf_panel(ax_acf, acf_vals, nlags, n, f, cmax, conf,
                    q_label, "acf", fs_acf=fs_acf, fs_q=fs_q)

    # ── PACF PANEL ───────────────────────────────────────────────────────
    _draw_acf_panel(ax_pac, pacf_vals, nlags, n, f, cmax, conf,
                    "", "pacf", fs_acf=fs_acf, fs_q=fs_q)

    return fig


def _draw_acf_panel(ax, vals, nlags, n, f, cmax, conf,
                    q_label, label, fs_acf=18, fs_q=15):
    """Single ACF or PACF panel — impulse style with seasonal tick labels."""
    lag_x = np.arange(1, nlags + 1)

    # Impulse lines (vlines: more reliable than stem)
    lw_imp = 3.0 if nlags >= 30 else 4.0
    ax.vlines(lag_x, 0, vals, colors='k', linewidth=lw_imp, zorder=3)

    # ±2σ confidence bands — black dashed
    ax.axhline(y= conf, color='k', lw=0.7, linestyle='--', zorder=2)
    ax.axhline(y=-conf, color='k', lw=0.7, linestyle='--', zorder=2)
    ax.axhline(y=0,     color='k', lw=1.0, zorder=2)

    # Y-axis: ±cmax with ticks at cmax/2 intervals
    ax.set_ylim(-cmax, cmax)
    half = cmax / 2.0
    ax.set_yticks([-cmax, -half, 0.0, half, cmax])
    ax.yaxis.set_tick_params(direction='out', labelsize=9)

    # Seasonal grid lines and x-tick labels at lag multiples
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

    # Border: left only (C: border 2 lw 1.6)
    for sp in ('top', 'right', 'bottom'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_linewidth(1.6)

    if label:
        ax.text(0.5, 1.01, label, transform=ax.transAxes,
                ha='center', va='bottom', clip_on=False,
                fontsize=fs_acf, fontweight='bold')

    if q_label:
        ax.set_xlabel(q_label, fontsize=fs_q, labelpad=6)
