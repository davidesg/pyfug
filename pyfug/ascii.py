"""
ASCII text output module — EXACT replica of FUG 1.x diagnose.c output.

Produces byte-identical .out files with:
- Statistics header
- Standardized time series ASCII plot (55-char grid with outlier markers)
- Outlier table
- Histogram ASCII (64-char with dot patterns)
- ACF/PACF table with cumulative Q-stat
- Mean-Deviation ASCII plot (40-char grid + values table)
"""

from __future__ import annotations

import numpy as np
from pyfug.core import Tseries, obs_to_date
from pyfug.statistics import descriptive_stats, acf, pacf, chi_test
from pyfug.graphics.mean_deviation import meandv as _meandv


# ── Helper: replicate C's iround ─────────────────────────────

def _iround(x: float) -> int:
    """Round to nearest integer (C-style, away from zero for .5)."""
    return int(np.floor(x + 0.5))


# ═══════════════════════════════════════════════════════════════
# SECTION: HEADER + STATISTICS
# ═══════════════════════════════════════════════════════════════

def _write_header(f, ser: Tseries, boxlam: float, nrdiff: int, nadiff: int,
                  infile: str, outfile: str):
    """Lines 1-12: FUG header + separator + series info."""
    f.write("\n")
    f.write("FUG 1.07: CopyLEFT (C) 2010  Arthur B. Treadway & David Guerrero\n")
    f.write(f"Input file             : {infile}\n")
    f.write(f"Output file            : {outfile}\n")
    f.write("Option                 : Series Plots\t\n")
    f.write("\n")
    f.write("________________________________________________________________________________ \n")
    f.write(f"Series Name                : {ser.name:>2s}\n")
    f.write(f"Seasonal period            : {ser.freq:>2d}\n")
    f.write(f"Regular differences        : {nrdiff:>2d}\n")
    f.write(f"Annual differences         : {nadiff:>2d}\n")
    f.write(f"Box-Cox Transformation     : {boxlam:>2.1f}\n")
    f.write("________________________________________________________________________________ \n")
    f.write("\n")


def _write_statistics(f, ser: Tseries):
    """Lines 13-26: descriptive statistics in FUG format."""
    n = ser.nobs
    stats = descriptive_stats(ser.data) if ser.mean == 0.0 else {
        "mean": ser.mean, "var": ser.var, "std": np.sqrt(ser.var),
        "skew": ser.skew, "kurt": ser.kurt, "jb": ser.jarquebera,
        "min_idx": ser.min_idx, "max_idx": ser.max_idx,
    }

    mean_val = stats["mean"]
    std_val = stats["std"]
    std_err = std_val / np.sqrt(n)
    
    # FUG integer-division JB bug
    jb_fug = (n // 6) * (stats["skew"]**2 + stats["kurt"]**2 / 4.0)

    f.write("\n")
    f.write(f"Transformed Time Series Data (seasonal period: {ser.freq})\n")
    f.write(f"{n} observations: from {ser.begtime}/{ser.begyear}")
    end_year, end_sub = obs_to_date(ser.begyear, ser.begtime, n, ser.freq)
    f.write(f" to {end_sub}/{end_year}\n")
    f.write("\n")
    f.write(f"                  Mean: {mean_val:18.6f}\n")
    f.write(f"Standard error of mean: {std_err:18.6f}\n")
    f.write(f"              Variance: {stats['var']:18.6f}\n")
    f.write(f"    Standard deviation: {std_val:18.6f}\n")
    f.write(f"              Skewness: {stats['skew']:18.6f}\n")
    f.write(f"              Kurtosis: {stats['kurt']:18.6f}\n")
    f.write(f"           Jarque-Bera: {jb_fug:18.6f}\n")

    min_idx = stats["min_idx"] + 1
    min_year, min_sub = obs_to_date(ser.begyear, ser.begtime, min_idx, ser.freq)
    f.write(f"               Minimum: {ser.data[stats['min_idx']]:18.6f} at "
            f"{min_sub:>2d}/{min_year} (observation {min_idx:>3d})\n")

    max_idx = stats["max_idx"] + 1
    max_year, max_sub = obs_to_date(ser.begyear, ser.begtime, max_idx, ser.freq)
    f.write(f"               Maximum: {ser.data[stats['max_idx']]:18.6f} at "
            f"{max_sub:>2d}/{max_year} (observation {max_idx:>3d})\n")


# ═══════════════════════════════════════════════════════════════
# SECTION: ASCII TIME SERIES PLOT (File_PlotSer)
# ═══════════════════════════════════════════════════════════════

def _write_ascii_plot(f, ser: Tseries):
    """Exact replica of FUG File_PlotSer — 55-char standardized plot."""
    n = ser.nobs
    mean_val = np.mean(ser.data)
    std_val = np.std(ser.data)
    z = (ser.data - mean_val) / std_val if std_val > 1e-10 else np.zeros(n)

    # AbsMax: max |z|, clamped to ≥3.0
    abs_max = max(abs(np.min(z)), abs(np.max(z)))
    if abs_max <= 2.0:
        abs_max = 3.0

    if abs_max > 8.0:
        f.write("Warning: at least one observation above 8 sigmas\n")
        return

    # Horizontal increment: 25 chars per sigma (center at position 27)
    hor_inc = 25.0 / abs_max
    band_pos_1 = hor_inc       # ±1σ position
    band_pos_2 = 2.0 * hor_inc  # ±2σ position

    # Build Guions (80-char template) and Marcas (76-char, center '0' at pos 39)
    guions = list("-------------+-------------------------+-------------------------+--------------")
    marcas = list("                                       0                          ")
    
    for i in range(1, 9):
        if abs_max >= i:
            pos_neg = 39 - _iround(i * hor_inc)
            pos_pos = 39 + _iround(i * hor_inc)
            label = str(i)
            if 0 <= pos_neg < 80:
                guions[pos_neg] = '+'
            if 0 <= pos_pos < 80:
                guions[pos_pos] = '+'
            if 0 <= pos_neg < 76:
                marcas[pos_neg] = label[0]
                if pos_neg - 1 >= 0:
                    marcas[pos_neg - 1] = '-'
            if 0 <= pos_pos < 76:
                marcas[pos_pos] = label[0]
                if pos_pos - 1 >= 0:
                    marcas[pos_pos - 1] = '+'

    guions_str = "".join(guions)
    marcas_str = "".join(marcas)

    f.write("\n")
    f.write("Standardized time series plot ")
    f.write("(original values on right-side column):\n")
    f.write("\n")
    f.write(f"{marcas_str}\n")
    f.write(f"{guions_str}\n")

    # Each observation line
    for i in range(n):
        obs_no = i + 1
        year, sub = obs_to_date(ser.begyear, ser.begtime, obs_no, ser.freq)

        # Build 55-char line
        line = [" "] * 55
        
        # Position 1: | or + (if last subperiod of year)
        if ser.freq != 1 and sub == ser.freq:
            line[1] = '+'
        else:
            line[1] = '|'

        # Position 53: | or +
        if ser.freq != 1 and sub == ser.freq:
            line[53] = '+'
        else:
            line[53] = '|'

        # Position 0 and 54: outlier markers (|z| >= 2.0)
        if abs(z[i]) >= 2.0:
            line[0] = '\u00af'   # ¯ macron
            line[54] = '\u00ae'  # ® registered

        # Position 27: center marker (| or *)
        pos = 27 + _iround(z[i] * hor_inc)
        if 0 <= pos < 55:
            line[pos] = '*'
        if line[27] == ' ':
            line[27] = '|'

        # Band markers at ±1σ, ±2σ
        for bp in [band_pos_1, band_pos_2]:
            for sign in [-1, 1]:
                bpos = 27 + _iround(sign * bp)
                if 0 <= bpos < 55 and line[bpos] == ' ':
                    line[bpos] = ':'

        line_str = "".join(line)

        # Observation label
        if ser.freq == 1:
            f.write(f"{obs_no:>4d}{year:>7d} {line_str}{ser.data[i]:13.10f}\n")
        else:
            f.write(f"{obs_no:>4d}{sub:>3d}/{year:<4d}{line_str}{ser.data[i]:13.10f}\n")

    f.write(f"{guions_str}\n")
    f.write(f"{marcas_str}\n")
    f.write("\n")

    # Outlier table
    f.write("                 +------------------------------------------+\n")
    f.write("                 |       Table of standardized values       |\n")
    f.write("                 |       greater than or equal to 2.0       |\n")
    f.write("                 +------------------------------------------+\n")
    f.write("                 |                                          |\n")
    f.write("                 | Observation    Date   Standardized value |\n")
    f.write("                 |                                          |\n")

    for i in range(n):
        if abs(z[i]) >= 2.0:
            obs_no = i + 1
            year, sub = obs_to_date(ser.begyear, ser.begtime, obs_no, ser.freq)
            f.write("                 |")
            f.write(f"{obs_no:>7d}")
            if ser.freq == 1:
                f.write(f"{year:>13d} ")
            else:
                f.write(f"{sub:>9d}/{year:<4d}")
            f.write(f"{z[i]:13.2f}")
            f.write("        |\n")

    f.write("                 +------------------------------------------+\n")
    f.write("\n")


# ═══════════════════════════════════════════════════════════════
# SECTION: ASCII HISTOGRAM (File_HistSer)
# ═══════════════════════════════════════════════════════════════

def _write_ascii_histogram(f, ser: Tseries):
    """Exact replica of FUG File_HistSer — 64-char dot histogram."""
    n = ser.nobs
    mean_val = np.mean(ser.data)
    std_val = np.std(ser.data)
    z = (ser.data - mean_val) / std_val if std_val > 1e-10 else np.zeros(n)

    num_fil = 17
    num_col = 64

    # Determine xmax
    xmax_val = max(abs(np.min(z)), abs(np.max(z)))
    if xmax_val > 8.0:
        f.write("Warning: at least one observation above 8 sigmas\n")
        return
    xmax_val = 4.0 if xmax_val <= 4.0 else 8.0

    if xmax_val == 4.0:
        nphor = 4
        no_str = "    "
        yes_str = "...."
        base1 = "        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+"
        base2 = "       -4      -3      -2      -1       0      +1      +2      +3      +4"
    else:
        nphor = 2
        no_str = "  "
        yes_str = ".."
        base1 = "        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
        base2 = "       -8  -7  -6  -5  -4  -3  -2  -1   0  +1  +2  +3  +4  +5  +6  +7  +8"

    # Breakpoints: every 0.5 from -xmax+0.5
    breakpoints = []
    bp = -xmax_val + 0.5
    while bp < xmax_val:
        breakpoints.append(bp)
        bp += 0.5
    num_cat = len(breakpoints)

    # Frequencies
    freqs = [0] * num_cat
    atip1 = 0  # |z| >= 1
    atip2 = 0  # |z| >= 2
    for zi in z:
        if abs(zi) >= 2.0:
            atip2 += 1
        if abs(zi) >= 1.0:
            atip1 += 1
        placed = False
        for j in range(num_cat - 1):
            if breakpoints[j] < zi <= breakpoints[j + 1]:
                freqs[j + 1] += 1
                placed = True
                break
        if not placed:
            if zi <= breakpoints[0]:
                freqs[0] += 1
            else:
                freqs[-1] += 1

    fmax = max(freqs) if freqs else 1
    obs_per_fil = fmax / 16.0

    # Build rows
    shist = [""] * num_fil
    aux = [""] * num_fil
    chk = [0] * num_cat

    for j in range(2, num_fil + 1):  # rows 2..17 (1-indexed)
        for i in range(num_cat):
            if freqs[i] > obs_per_fil * (num_fil - j):
                shist[j - 1] += yes_str
            else:
                shist[j - 1] += no_str
        shist[j - 1] = shist[j - 1][:-len(no_str)] if shist[j - 1].endswith(no_str) else shist[j - 1]
        shist[j - 1] += "|"

    # Frequency labels
    for j in range(2, num_fil + 1):
        for i in range(num_cat):
            if freqs[i] > obs_per_fil * (num_fil - j) and chk[i] == 0:
                s1 = str(freqs[i])
                if nphor == 2:
                    if len(s1) == 1:
                        s1 += " "
                else:  # nphor == 4
                    if len(s1) == 2:
                        s1 = " " + s1 + " "
                    elif len(s1) == 1:
                        s1 = "   " + s1 + " "
                    elif len(s1) == 3:
                        s1 += " "
                aux[j - 2] += s1
                chk[i] = 1
            else:
                aux[j - 2] += no_str

    # row 1: copy aux[0]
    shist[0] = aux[0] + "|"

    # Merge aux into shist for rows 2..16
    for j in range(2, num_fil):
        s = list(shist[j - 1])
        a = aux[j - 1]
        for i in range(min(len(a), len(s))):
            if a[i] != ' ':
                s[i] = a[i]
        shist[j - 1] = "".join(s)

    # Write
    f.write("\n")
    f.write("Standardized time series histogram:\n")
    f.write("\n")
    f.write(f"{base2}\n")
    f.write(f"{base1}\n")
    for i in range(num_fil):
        f.write(f"        |{shist[i]}\n")
    f.write(f"{base1}\n")
    f.write(f"{base2}\n")
    f.write("\n")

    f.write(f"{atip1:>16d} values outside (-1,+1): "
            f"{atip1 * 100.0 / n:5.2f} % (31.74 %% expected)\n")
    f.write(f"{atip2:>16d} values outside (-2,+2): "
            f"{atip2 * 100.0 / n:5.2f} % ( 4.56 %% expected)\n")
    f.write("\n")

    # S, K, JB labels
    stats = descriptive_stats(ser.data)
    f.write(f"          S = {stats['skew']:.1f}   K = {stats['kurt']:.1f}   "
            f"JB = {stats['jb']:.1f}\n")
    f.write("\n")


# ═══════════════════════════════════════════════════════════════
# SECTION: ACF/PACF TABLE (File_CorrSer)
# ═══════════════════════════════════════════════════════════════

def _write_acf_ascii_bars(f, ser: Tseries, nlags: int = 0):
    """Exact replica of FUG File_CorrSer — horizontal bar chart for ACF and PACF."""
    n = ser.nobs
    fq = ser.freq

    if nlags == 0:
        if n < 3 * (fq + 1):
            nlags = max(1, n - fq // 2)
        elif fq == 1:
            nlags = 9
        else:
            nlags = 3 * (fq + 1)
    nlags = min(nlags, n - 1)

    acf_vals = acf(ser.data, nlags)
    pacf_vals = pacf(ser.data, nlags)
    conf = 2.0 / np.sqrt(n)  # ±2σ band displayed in title
    sigma_2 = 2.0 / np.sqrt(n)  # ±2σ position for ':' markers

    # Scale: 25 chars per unit of correlation (center at pos 39)
    scale = 25.0
    center = 39
    band_pos = _iround(sigma_2 * scale)  # position offset for ':' markers at ±2σ

    # Guions separator (80 chars)
    guions = "-------------+-------------------------+-------------------------+--------------"

    # ── Cumulative Q-stat ────────────────────────────────────
    q_cum = np.zeros(nlags + 1)
    for k in range(1, nlags + 1):
        r = acf_vals[k - 1]
        q_cum[k] = q_cum[k - 1] + n * (n + 2) * r * r / (n - k)

    def _draw_corr(f, title, values, show_q=True, is_pacf=False):
        band_label = "pacf bands" if is_pacf else "acf bands"
        f.write(f"\n{title} ({band_label} = \xb1 {conf:.3f}):\n")
        f.write("\n")
        # Header
        if show_q:
            f.write("            -1                         0                         1  L-B Q  DF\n")
        else:
            f.write("            -1                         0                         1\n")
        f.write(f"{guions}\n")

        for k in range(1, nlags + 1):
            val = values[k - 1]
            is_seasonal = (fq > 1 and k % fq == 0)

            # Build bar: 53 chars (positions 13 to 65, center at 39)
            bar = [" "] * 53
            local_center = center - 13  # = 26
            
            # Edge markers at positions 0 and 52
            edge_char = '+' if is_seasonal else '|'
            bar[0] = edge_char
            bar[52] = edge_char
            
            # Center marker (same as edge for seasonal lags)
            bar[local_center] = edge_char

            # Bar: fill with '*' (or '+' for seasonal lags)
            fill_char = '+' if is_seasonal else '*'
            bar_len = _iround(abs(val) * scale)
            if val > 0:
                for i in range(1, min(bar_len, 52 - local_center) + 1):
                    if bar[local_center + i] == ' ':
                        bar[local_center + i] = fill_char
            elif val < 0:
                for i in range(1, min(bar_len, local_center) + 1):
                    if bar[local_center - i] == ' ':
                        bar[local_center - i] = fill_char

            # Band markers at ±1σ (fixed offset from center)
            bp_left = local_center - band_pos
            bp_right = local_center + band_pos
            if 0 <= bp_left < 53 and bar[bp_left] == ' ':
                bar[bp_left] = ':'
            if 0 <= bp_right < 53 and bar[bp_right] == ' ':
                bar[bp_right] = ':'

            bar_str = "".join(bar)

            # Right-side info (Q-stat for seasonal lags and last lag)
            right = " "
            if show_q and (is_seasonal or k == nlags):
                right = f" {q_cum[k]:8.2f} {k:>3d}"

            f.write(f"{k:>4d} {val:>7.3f} {bar_str}{right}\n")

        # Footer
        f.write(f"{guions}\n")
        if show_q:
            f.write("            -1                         0                         1  L-B Q  DF\n")
        else:
            f.write("            -1                         0                         1\n")
        f.write("\n")

    _draw_corr(f, "Autocorrelation function", acf_vals, show_q=True)
    _draw_corr(f, "Partial autocorrelation function", pacf_vals, show_q=False, is_pacf=True)


# ═══════════════════════════════════════════════════════════════
# SECTION: MEAN-DEVIATION ASCII (DesvMed)
# ═══════════════════════════════════════════════════════════════

def _write_meandev(f, ser: Tseries, nog: int = 0):
    """Exact replica of FUG DesvMed — 40-char mean-deviation chart."""
    num_fil = 17
    num_col = 40

    if nog <= 0:
        nog = 12 if ser.freq == 12 else 8

    z_means, z_stdevs = _meandv(ser.data, nog)
    ng = len(z_means)

    abs_max = max(
        max(abs(z_means)) if ng > 0 else 1.0,
        max(abs(z_stdevs)) if ng > 0 else 1.0,
    )
    abs_max *= 1.1
    if abs_max < 0.1:
        abs_max = 1.0

    max_range = 2.0 * abs_max / num_fil
    max_mean = 2.0 * abs_max / num_col

    pos_x = np.zeros(ng, dtype=int)
    pos_y = np.zeros(ng, dtype=int)

    for i in range(ng):
        pos_x[i] = _iround((z_means[i] + abs_max) / max_mean)
        pos_y[i] = _iround((abs_max - z_stdevs[i]) / max_range)
        pos_x[i] = max(0, min(pos_x[i], num_col - 1))
        pos_y[i] = max(0, min(pos_y[i], num_fil - 1))

    # Build rows
    rows = [[" "] * num_col for _ in range(num_fil)]
    for grp in range(ng):
        py = pos_y[grp]
        px = pos_x[grp]
        if 0 <= py < num_fil and 0 <= px < num_col:
            rows[py][px] = '*'

    for i in range(num_fil):
        rows[i][num_col - 1] = '+' if i == 8 else '|'

    f.write("\n\n")
    f.write(f"Mean-Standard Deviation Plot Standardized, "
            f"Observations Number for Each Group: {nog}\n\n")
    f.write(f"                      {abs_max:.1f} +-------------------+"
            f"-------------------+\n")

    for i in range(num_fil):
        if i == 8:
            f.write(" Standard Deviation   0.0 +")
        else:
            f.write("                          |")
        row_str = "".join(rows[i])
        f.write(f"{row_str}\n")

    f.write(f"                     -{abs_max:.1f} +-------------------+"
            f"-------------------+\n")
    f.write(f"                        -{abs_max:.1f}                 0.0"
            f"                 {abs_max:.1f}\n")
    f.write("                                             Mean                    '\n")
    f.write("\n\n")

    # Table of standardized values
    if ser.freq == 1:
        f.write("                 +--------------------------------------------------------+\n")
        f.write("                 |              Table of standardized values              |\n")
        f.write("                 |   for each Mean and correspondent Standard Deviation   |\n")
        f.write("                 +--------------------------------------------------------+\n")
        f.write("                 |                                                        |\n")
        f.write("                 |   Group        Dates       Mean      Standard          |\n")
        f.write("                 |                                      Deviation         |\n")
        f.write("                 +--------------------------------------------------------+\n")
    else:
        f.write("                 +--------------------------------------------------------+\n")
        f.write("                 |              Table of standardized values              |\n")
        f.write("                 |   for each Mean and correspondent Standard Deviation   |\n")
        f.write("                 +--------------------------------------------------------+\n")
        f.write("                 |                                                        |\n")
        f.write("                 |   Group          Dates            Mean      Standard   |\n")
        f.write("                 |                                             Deviation  |\n")
        f.write("                 +--------------------------------------------------------+\n")

    for i in range(ng):
        f.write("                 |")
        f.write(f"{i + 1:>7d}")
        start_obs = i * nog + 1
        end_obs = (i + 1) * nog
        sy, ss = obs_to_date(ser.begyear, ser.begtime, start_obs, ser.freq)
        ey, es = obs_to_date(ser.begyear, ser.begtime, end_obs, ser.freq)
        if ser.freq == 1:
            f.write(f"{sy:>9d} - {ey:>3d}")
        else:
            f.write(f"{ss:>7d}/{sy:<4d} - {es:>2d}/{ey:<4d}")
        f.write(f"      {z_means[i]:>4.1f}        {z_stdevs[i]:>4.1f}")
        if ser.freq == 1:
            f.write("           |\n")
        else:
            f.write("    |\n")
    f.write("                 +--------------------------------------------------------+\n")
    f.write("\n\n")


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def generate_ascii_output(ser: Tseries,
                          boxlam: float = 1.0,
                          nrdiff: int = 0,
                          nadiff: int = 0,
                          nlags: int = 0,
                          m_dt_nog: int = 0,
                          infile: str = "",
                          outfile: str = "",
                          output_path: str = "") -> str:
    """Generate complete FUG-identical ASCII output.

    Parameters
    ----------
    ser : Tseries
        Transformed time series.
    boxlam : float
        Box-Cox lambda.
    nrdiff, nadiff : int
        Differencing orders.
    nlags : int
        Number of ACF lags (0=auto).
    m_dt_nog : int
        Obs per group for mean-deviation (0=auto).
    infile, outfile : str
        Input/output filenames for header.
    output_path : str
        If given, write to this file.

    Returns
    -------
    str
        Generated content.
    """
    import io

    if not infile:
        infile = "test.inp"
    if not outfile:
        outfile = "test.out"

    f = io.StringIO() if not output_path else open(output_path, "w", encoding="latin-1")

    _write_header(f, ser, boxlam, nrdiff, nadiff, infile, outfile)
    _write_statistics(f, ser)
    _write_ascii_plot(f, ser)
    _write_ascii_histogram(f, ser)
    _write_acf_ascii_bars(f, ser, nlags)

    if m_dt_nog <= 0:
        m_dt_nog = 12 if ser.freq == 12 else 8
    _write_meandev(f, ser, m_dt_nog)

    if output_path:
        f.close()
        with open(output_path, "r", encoding="latin-1") as f2:
            return f2.read()
    else:
        result = f.getvalue()
        f.close()
        return result
