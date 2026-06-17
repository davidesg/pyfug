"""
Jupyter notebook integration for pyfug.

Provides convenience functions for inline display of
Jenkins-Treadway plots in Jupyter notebooks, plus
integration hooks for estimation engines (statsmodels, etc.).
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional

from pyfug.core import Tseries
from pyfug.io import read_inp, read_pandas
from pyfug.transform import boxcox
from pyfug.graphics.engine import diffgraph
from pyfug.statistics import compute_all


def display_diffgraph(ser: Tseries, **kwargs):
    """Display diffgraph output inline in a Jupyter notebook.

    Parameters
    ----------
    ser : Tseries
        Time series.
    **kwargs
        Passed to diffgraph. Common options: boxlam, nrdiff, nadiff,
        lags, case_a, case_b, case_c, case_d, case_e.

    Returns
    -------
    Tseries
        The transformed series (for further analysis).
    """
    result = diffgraph(ser, save=False, return_figs=True, **kwargs)

    for fig in result["figures"]:
        display(fig)  # noqa: F821 — available in Jupyter
        plt.close(fig)

    return result["transformed"]


def from_statsmodels_result(result, name: str = "") -> Tseries:
    """Create a Tseries from a statsmodels ARIMA/SARIMAX result.

    Extracts the residuals and optionally the fitted values
    for diagnostic plotting.

    Parameters
    ----------
    result : statsmodels result object
        A fitted ARIMA, SARIMAX, or similar model result.
    name : str
        Name for the series.

    Returns
    -------
    Tseries
        Residuals as a Tseries.
    """
    resid = result.resid
    # Drop NaN values
    resid = resid.dropna() if hasattr(resid, "dropna") else resid
    values = np.asarray(resid, dtype=np.float64)

    return Tseries(
        name=name or "Residuals",
        nobs=len(values),
        freq=1,
        begyear=0,
        data=values,
    )


def diagnostic_plots(ser: Tseries,
                     model_name: str = "",
                     output_dir: str = ".",
                     **kwargs) -> dict:
    """Generate a complete diagnostic plot set for model residuals.

    Produces: series plot, ACF/PACF, histogram, and mean-deviation chart.
    Designed for integration with estimation engines.

    Parameters
    ----------
    ser : Tseries
        Time series (typically model residuals).
    model_name : str
        Name prefix for output files.
    output_dir : str
        Output directory.

    Returns
    -------
    dict
        With keys 'transformed' (Tseries) and 'files' (list of paths).
    """
    from pyfug.graphics.engine import diffgraph as _diffgraph

    outname = model_name or ser.name or "diagnostics"

    return _diffgraph(
        ser,
        outname=outname,
        output_dir=output_dir,
        case_a=True,
        case_c=True,
        case_d=True,
        case_e=True,
        **kwargs,
    )


def compare_series(*series: Tseries,
                   labels: Optional[list] = None,
                   title: str = "Series Comparison",
                   figsize: tuple = (12, 6)):
    """Plot multiple series on the same axes for comparison.

    Parameters
    ----------
    *series : Tseries
        One or more time series to compare.
    labels : list of str, optional
        Labels for the legend.
    title : str
        Plot title.
    figsize : tuple
        Figure size.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    if labels is None:
        labels = [s.name or f"Series {i+1}" for i, s in enumerate(series)]

    for ser, label in zip(series, labels):
        ax.plot(ser.data, label=label, linewidth=1.5)

    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Observation")
    ax.set_ylabel("Value")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig
