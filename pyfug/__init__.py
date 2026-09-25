"""
pyfug — Jenkins-Treadway High-Definition Time Series Graphics
==============================================================

A Python library for producing publication-quality time series
analysis graphics with the precise proportions and layout of the
Jenkins-Treadway design methodology.

Originally based on FUG 1.12 (C/gnuplot) by Arthur B. Treadway
and David E. Guerrero. Reimplemented in Python with matplotlib.

Usage as a library
------------------
>>> from pyfug import Tseries, read_inp, diffgraph
>>> ts = read_inp("PU.inp")
>>> fig = diffgraph(ts)  # matplotlib Figure
>>> fig.savefig("output.pdf")

Usage as CLI
------------
$ pyfug PU one -c        # combined series + ACF/PACF plot
$ pyfug PU set 2 1 -c    # identification plots set
"""

__version__ = "2.0.1"   # también en pyproject.toml: ver TODO (escrita dos veces)
__author__ = "David E. Guerrero & Arthur B. Treadway"

from pyfug.core import Tseries
from pyfug.io import read_inp, read_csv, read_excel, read_pandas
from pyfug.transform import boxcox, regular_diff, seasonal_diff, apply_diffops
from pyfug.statistics import (
    acf, pacf, ljung_box,
    descriptive_stats, chi_test,
)
from pyfug.graphics import (
    plot_series,
    plot_acf_pacf,
    plot_combined,
    plot_histogram,
    plot_mean_deviation,
    diffgraph,
)
from pyfug.ascii import generate_ascii_output

__all__ = [
    "Tseries",
    "read_inp", "read_csv", "read_excel", "read_pandas",
    "boxcox", "regular_diff", "seasonal_diff", "apply_diffops",
    "acf", "pacf", "ljung_box", "descriptive_stats", "chi_test",
    "plot_series", "plot_acf_pacf", "plot_combined",
    "plot_histogram", "plot_mean_deviation",
    "diffgraph", "generate_ascii_output",
]
