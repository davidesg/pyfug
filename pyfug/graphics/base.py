"""
Base layout engine and Jenkins-Treadway theme constants.

Provides:
- JTFigure: A matplotlib Figure subclass with preset proportions
- plot_title(): Generate the LaTeX-style title with differencing notation
- file_plot_name(): Generate filenames matching original FUG convention
- Layout constants for precise positioning
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure

# ── Jenkins-Treadway layout constants ──────────────────────────────

# Standard figure dimensions (inches) — matches original A4/letter proportions
STANDARD_WIDTH = 8.5   # Full figure width
STANDARD_HEIGHT = 11.0  # Full figure height

# Font configuration for publication quality
JT_FONT_FAMILY = "sans-serif"
JT_FONT = "DejaVu Sans"
JT_FONT_SIZE_TITLE = 18
JT_FONT_SIZE_AXIS = 14
JT_FONT_SIZE_TICKS = 12
JT_FONT_SIZE_LABEL = 17
JT_FONT_YEAR = 17.2       # year labels below x-axis (Arial 17.2 in FUG C)

# Line weights
JT_LINE_WIDTH_SERIES = 1.5
JT_LINE_WIDTH_BORDER = 1.6
JT_LINE_WIDTH_GRID = 0.5
JT_LINE_WIDTH_CONFIDENCE = 1.2
JT_LINE_WIDTH_IMPULSE = 2.5

# Colors (publication-safe grayscale + accent)
JT_COLOR_SERIES = "#000000"         # black
JT_COLOR_ACF = "#000000"            # black
JT_COLOR_CONFIDENCE = "#D62728"     # red (for ±2/√n bands)
JT_COLOR_GRID = "#BBBBBB"           # light gray
JT_COLOR_HIST_FILL = "#CFCFCF"      # medium gray
JT_COLOR_NORMAL = "#000000"         # black

# Default DPI for raster output
JT_DPI = 150


def _setup_matplotlib_rc():
    """Configure matplotlib rcParams for Jenkins-Treadway style."""
    matplotlib.rcParams.update({
        "font.family": JT_FONT_FAMILY,
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
        "font.size": JT_FONT_SIZE_AXIS,
        "axes.titlesize": JT_FONT_SIZE_TITLE,
        "axes.labelsize": JT_FONT_SIZE_LABEL,
        "xtick.labelsize": JT_FONT_SIZE_TICKS,
        "ytick.labelsize": JT_FONT_SIZE_TICKS,
        "lines.linewidth": JT_LINE_WIDTH_SERIES,
        "axes.linewidth": JT_LINE_WIDTH_BORDER,
        "grid.linewidth": JT_LINE_WIDTH_GRID,
        "axes.grid": False,
        "figure.dpi": JT_DPI,
        "savefig.dpi": JT_DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
        "text.usetex": False,
    })


_setup_matplotlib_rc()


class JTFigure:
    """Factory for Jenkins-Treadway styled matplotlib Figures.

    Provides convenience methods for creating figures with
    the correct proportions and styling for each plot type.
    """

    def __init__(self, figsize=None, dpi=None):
        if figsize is None:
            figsize = (STANDARD_WIDTH, STANDARD_HEIGHT)
        if dpi is None:
            dpi = JT_DPI
        self.fig = Figure(figsize=figsize, dpi=dpi)

    @property
    def figure(self) -> Figure:
        return self.fig

    def save(self, filepath, **kwargs):
        kwargs.setdefault("dpi", JT_DPI)
        kwargs.setdefault("bbox_inches", "tight")
        kwargs.setdefault("pad_inches", 0.1)
        self.fig.savefig(filepath, **kwargs)


def plot_title(d: int, ds: int, boxlam: float, freq: int, name: str) -> str:
    """Generate the graph title with differencing and Box-Cox notation.

    Uses LaTeX math notation for the nabla (∇) and superscripts.
    Matches the original plot_title() from FUG.

    Examples:
        d=0, ds=0, lam=0   → "ln PU"
        d=1, ds=0, lam=1   → "∇ PU"
        d=2, ds=0, lam=1   → "∇² PU"
        d=0, ds=1, lam=0   → "∇₁₂ ln PU"
        d=1, ds=1, lam=0.5 → "∇ ∇₁₂ PU(0.50)"

    Parameters
    ----------
    d : int
        Regular differencing order.
    ds : int
        Seasonal differencing order.
    boxlam : float
        Box-Cox lambda.
    freq : int
        Data frequency.
    name : str
        Series name.

    Returns
    -------
    str
        LaTeX-formatted title string.
    """
    parts = []

    # Regular differencing — mathtext nabla (renders in all backends)
    if d == 2:
        parts.append("$\\nabla^2$")
    elif d > 0:
        parts.append("$\\nabla$")

    # Seasonal differencing — mathtext subscript
    if ds > 0:
        parts.append(f"$\\nabla_{{{freq}}}$")

    # Box-Cox (log)
    if boxlam == 0.0:
        parts.append("ln")

    # Series name
    parts.append(name)

    # Box-Cox parameter (if not 0 or 1)
    if boxlam not in (0.0, 1.0):
        parts[-1] = f"{name}({boxlam:.2f})"

    return " ".join(parts)


def file_plot_name(d: int, ds: int, boxlam: float, freq: int,
                   outname: str) -> str:
    """Generate the output filename matching original FUG convention.

    Examples:
        d=0, ds=0, lam=1   → "d0PU"
        d=1, ds=0, lam=0   → "d1lnPU"
        d=1, ds=0, lam=0.5 → "d1l0.5PU"
        d=1, ds=1, lam=1   → "d1D1PU"
        d=1, ds=1, lam=0   → "d1D1lnPU"

    Parameters
    ----------
    d : int
        Regular differencing order.
    ds : int
        Seasonal differencing order.
    boxlam : float
        Box-Cox lambda.
    freq : int
        Data frequency (unused, kept for API compatibility).
    outname : str
        Base output name.

    Returns
    -------
    str
        Filename (without extension).
    """
    if ds == 0:
        if boxlam == 1.0:
            return f"d{d}{outname}"
        elif boxlam == 0.0:
            return f"d{d}ln{outname}"
        else:
            return f"d{d}l{boxlam:.1f}{outname}"
    else:
        if boxlam == 1.0:
            return f"d{d}D{ds}{outname}"
        elif boxlam == 0.0:
            return f"d{d}D{ds}ln{outname}"
        else:
            return f"d{d}D{ds}l{boxlam:.1f}{outname}"


def subscript_num(n: int) -> str:
    """Convert integer to Unicode subscript digits."""
    subscripts = str.maketrans("0123456789", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089")
    return str(n).translate(subscripts)


def _tics_size(size: int, abs_max: float) -> float:
    """Compute Y-axis label offset for series plots.

    Replicates the tics_size calculation from original FUG.
    """
    if size == 2 and abs_max > 4:
        return abs_max + 0.75
    elif size == 2 and abs_max < 4:
        return abs_max + 0.65
    elif abs_max > 4:
        return abs_max + 0.72
    else:
        return abs_max + 0.62
