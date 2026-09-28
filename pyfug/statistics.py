"""
Statistics module for pyfug.

Computes descriptive statistics, ACF, PACF, and diagnostic tests
for time series analysis.

ACF, PACF and Ljung-Box are computed here with numpy and scipy, with the same
formulas as fue's (`fue.acf`, `fue.pacf`, `fue.ljung_box`); the tests pin
the agreement to rounding. statsmodels is no longer a dependency (2026-09-28): the suite
computes these itself, and a third-party convention (the MA sign of
statsmodels' ArmaProcess, art BUG-0192) already cost a defect once.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Tuple
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

    d = np.asarray(data, dtype=float)
    d = d - d.mean()
    n = len(d)
    c0 = float(d @ d) / n
    if c0 <= 0.0:
        return np.zeros(nlags)
    ck = np.array([float(d[k:] @ d[:n - k]) for k in range(1, nlags + 1)])
    ck /= (n - np.arange(1, nlags + 1)) if unbiased else n
    return ck / c0


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
    # Partial autocorrelations are estimable only up to 50 % of the sample
    # size; cap defensively so any caller is safe.
    max_nlags = len(data) // 2 - 1
    if nlags > max_nlags:
        nlags = max_nlags
    if nlags < 1:
        return np.array([])

    # Yule-Walker on the (biased) sample ACF, by Durbin-Levinson.
    r = np.r_[1.0, acf(data, nlags)]
    out = np.zeros(nlags)
    prev = np.zeros(0)
    for k in range(1, nlags + 1):
        den = 1.0 - float(prev @ r[1:k])
        a = (r[k] - float(prev @ r[k - 1:0:-1])) / den if den != 0.0 else 0.0
        prev = np.r_[prev - a * prev[::-1], a]
        out[k - 1] = a
    return out


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
    if nlags < 1:
        return 0.0, 1.0
    n = len(data)
    r = acf(data, nlags)
    q = float(n * (n + 2) * np.sum(r ** 2 / (n - np.arange(1, nlags + 1))))
    return q, float(sp_stats.chi2.sf(q, nlags))


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
