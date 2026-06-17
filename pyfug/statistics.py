"""
Statistics module for pyfug.

Computes descriptive statistics, ACF, PACF, and diagnostic tests
for time series analysis.

Uses statsmodels for robust ACF/PACF computation with standard
confidence intervals, and scipy for distribution tests.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Tuple
from statsmodels.tsa.stattools import acf as sm_acf, pacf as sm_pacf
from scipy import stats as sp_stats


def descriptive_stats(data: np.ndarray) -> dict:
    """Compute descriptive statistics for a data vector.

    Parameters
    ----------
    data : np.ndarray
        Input data (1-D array).

    Returns
    -------
    dict
        Dictionary with keys: mean, var, std, skew, kurt, jb, min_idx, max_idx.
        Kurtosis is excess kurtosis (normal = 0).
    """
    n = len(data)
    if n == 0:
        return {"mean": 0, "var": 0, "std": 0, "skew": 0, "kurt": 0,
                "jb": 0, "min_idx": 0, "max_idx": 0}

    mean = np.mean(data)
    var = np.var(data)
    std = np.sqrt(var) if var > 0 else 0.0

    if std < 1e-20:
        skew = 0.0
        kurt = 0.0
        jb = 0.0
    else:
        centered = data - mean
        m2 = np.mean(centered ** 2)
        m3 = np.mean(centered ** 3)
        m4 = np.mean(centered ** 4)

        skew = m3 / (m2 ** 1.5) if m2 > 1e-20 else 0.0
        kurt = m4 / (m2 ** 2) - 3.0 if m2 > 1e-20 else 0.0
        jb = n / 6.0 * (skew ** 2 + kurt ** 2 / 4.0)

    min_idx = int(np.argmin(data))
    max_idx = int(np.argmax(data))

    return {
        "mean": float(mean),
        "var": float(var),
        "std": float(std),
        "skew": float(skew),
        "kurt": float(kurt),
        "jb": float(jb),
        "min_idx": min_idx,
        "max_idx": max_idx,
    }


def acf(data: np.ndarray, nlags: int, unbiased: bool = False) -> np.ndarray:
    """Compute the autocorrelation function.

    Parameters
    ----------
    data : np.ndarray
        Input time series.
    nlags : int
        Number of lags.
    unbiased : bool
        If True, use unbiased estimator (divides by n-k).

    Returns
    -------
    np.ndarray
        ACF values for lags 1..nlags.
    """
    if nlags >= len(data):
        nlags = len(data) - 1
    if nlags < 1:
        return np.array([])

    # Use statsmodels
    result = sm_acf(data, nlags=nlags, fft=False, adjusted=unbiased)
    # Return lags 1..nlags (skip lag 0 which is always 1.0)
    return result[1:]


def pacf(data: np.ndarray, nlags: int) -> np.ndarray:
    """Compute the partial autocorrelation function using Levinson-Durbin.

    Parameters
    ----------
    data : np.ndarray
        Input time series.
    nlags : int
        Number of lags.

    Returns
    -------
    np.ndarray
        PACF values for lags 1..nlags.
    """
    # statsmodels pacf can only estimate partial autocorrelations for lags up
    # to 50% of the sample size; cap defensively so any caller is safe.
    max_nlags = len(data) // 2 - 1
    if nlags > max_nlags:
        nlags = max_nlags
    if nlags < 1:
        return np.array([])

    result = sm_pacf(data, nlags=nlags, method="ywm")
    # Return lags 1..nlags (skip lag 0 which is always 1.0)
    return result[1:]


def ljung_box(data: np.ndarray, nlags: int) -> Tuple[float, float]:
    """Compute Ljung-Box Q statistic.

    Parameters
    ----------
    data : np.ndarray
        Input time series.
    nlags : int
        Number of lags to test.

    Returns
    -------
    tuple
        (Q statistic, p-value)
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox
    if nlags < 1:
        return 0.0, 1.0
    result = acorr_ljungbox(data, lags=[nlags], return_df=False)
    q = float(result.lb_stat.iloc[0])
    pval = float(result.lb_pvalue.iloc[0])
    return q, pval


def chi_test(data: np.ndarray, nlags: int) -> float:
    """Compute the Ljung-Box Q statistic (same as ljung_box, returns Q only).

    This matches the ChiTest function from original FUG.

    Parameters
    ----------
    data : np.ndarray
        Input time series.
    nlags : int
        Number of lags.

    Returns
    -------
    float
        Q statistic.
    """
    q, _ = ljung_box(data, nlags)
    return q


def acf_pacf_max(acf_vals: np.ndarray, pacf_vals: np.ndarray) -> float:
    """Determine optimal y-axis range for ACF/PACF plots.

    Replicates Acf_Pacf_Max from original FUG:
    - Finds maximum absolute coefficient value
    - Rounds up to nearest "nice" value: 0.40, 0.60, 0.80, 1.0

    Parameters
    ----------
    acf_vals : np.ndarray
        ACF values.
    pacf_vals : np.ndarray
        PACF values.

    Returns
    -------
    float
        Recommended y-axis limit (cmax).
    """
    combined = np.concatenate([acf_vals, pacf_vals])
    cmax = 0.40
    for v in combined:
        if abs(v) > cmax:
            cmax = abs(v)

    if 0.40 < cmax <= 0.60:
        cmax = 0.60
    elif 0.60 < cmax <= 0.80:
        cmax = 0.80
    elif 0.80 < cmax <= 1.0:
        cmax = 1.0

    return cmax


def series_max(data: np.ndarray) -> float:
    """Determine optimal y-axis range for series plots.

    Replicates SeriesMax from original FUG:
    - Finds maximum absolute value
    - Rounds up to nearest "nice" value: 4, 6, 8, 10, 12

    Parameters
    ----------
    data : np.ndarray
        Series data.

    Returns
    -------
    float
        Recommended y-axis limit.
    """
    abs_max = 4.0
    for v in data:
        if abs(v) >= abs_max:
            abs_max = abs(v)

    if 4.0 < abs_max <= 6.0:
        abs_max = 6.0
    elif 6.0 < abs_max <= 8.0:
        abs_max = 8.0
    elif 8.0 < abs_max <= 10.0:
        abs_max = 10.0
    elif abs_max > 10.0:
        abs_max = 12.0

    return abs_max


def series_size(nobs: int, freq: int) -> int:
    """Determine if the series needs a "large" layout size.

    Returns 2 if freq > 4 or nobs > 200, otherwise 1.

    Parameters
    ----------
    nobs : int
        Number of observations.
    freq : int
        Frequency.

    Returns
    -------
    int
        1 or 2.
    """
    if freq > 4 or nobs > 200:
        return 2
    return 1


def compute_all(ser: Tseries, nlags: int = 0) -> Tseries:
    """Compute all statistics and attach them to a Tseries.

    Parameters
    ----------
    ser : Tseries
        Time series.
    nlags : int
        Number of lags for ACF/PACF. If 0, auto-detected.

    Returns
    -------
    Tseries
        The same object with computed statistics.
    """
    from pyfug.core import Tseries

    stats = descriptive_stats(ser.data)
    ser.mean = stats["mean"]
    ser.var = stats["var"]
    ser.skew = stats["skew"]
    ser.kurt = stats["kurt"]
    ser.jarquebera = stats["jb"]
    ser.max_idx = stats["max_idx"]
    ser.min_idx = stats["min_idx"]

    # Auto-detect lags if not specified
    if nlags == 0:
        if ser.nobs < 3 * (ser.freq + 1):
            nlags = max(1, ser.nobs - ser.freq // 2)
        elif ser.freq == 1:
            nlags = 9
        else:
            nlags = 3 * (ser.freq + 1)

    ser.lags = min(nlags, ser.nobs - 1)

    return ser
