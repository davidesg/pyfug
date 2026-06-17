"""
Graphics package for pyfug.

Implements the Jenkins-Treadway high-definition plots:
- Time series plot
- ACF/PACF correlogram
- Combined series + ACF/PACF plot
- Histogram with normal distribution overlay
- Mean-Deviation (m-dt) chart

All plots use matplotlib with precise layout proportions
matching the original FUG designs for publication quality.
"""

from pyfug.graphics.base import (
    JTFigure, plot_title, file_plot_name, STANDARD_WIDTH
)
from pyfug.graphics.series import plot_series
from pyfug.graphics.acf_pacf import plot_acf_pacf
from pyfug.graphics.combined import plot_combined
from pyfug.graphics.histogram import plot_histogram
from pyfug.graphics.mean_deviation import plot_mean_deviation, plot_mean_deviation_pair
from pyfug.graphics.engine import diffgraph

__all__ = [
    "JTFigure", "plot_title", "file_plot_name", "STANDARD_WIDTH",
    "plot_series", "plot_acf_pacf", "plot_combined",
    "plot_histogram", "plot_mean_deviation", "plot_mean_deviation_pair",
    "diffgraph",
]
