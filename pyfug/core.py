"""
Core data structures for pyfug.

Defines the Tseries class — the central object representing a
univariate time series with metadata, transformations, and statistics.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tseries:
    """Standard single time series structure.

    Mirrors the C struct from the original FUG program.

    Attributes
    ----------
    name : str
        Time series name.
    nobs : int
        Number of observations.
    freq : int
        Frequency (observations per year): 1=annual, 4=quarterly, 12=monthly.
    begyear : int
        Beginning year.
    begtime : int
        Beginning period within year (1-based, e.g. 1=Jan/Q1).
    endyear : int
        Ending year.
    endtime : int
        Ending period within year.
    outyear : int
        Years before first observation (only for annual data).
    data : np.ndarray
        Time series data vector (1-based indexing compatible, 0-index used).
    mean : float
        Sample mean.
    var : float
        Sample variance.
    skew : float
        Skewness coefficient.
    kurt : float
        Excess kurtosis (0 = normal).
    jarquebera : float
        Jarque-Bera test statistic.
    max_idx : int
        Index of maximum value (0-based).
    min_idx : int
        Index of minimum value (0-based).
    lags : int
        Number of ACF/PACF lags computed.
    d : int
        Regular differencing order applied.
    ds : int
        Seasonal differencing order applied.
    boxlam : float
        Box-Cox lambda used.
    parent : Optional[Tseries]
        Reference to the original (untransformed) series.
    """

    name: str = ""
    nobs: int = 0
    freq: int = 1
    begyear: int = 0
    begtime: int = 1
    endyear: int = 0
    endtime: int = 0
    outyear: int = 0
    data: np.ndarray = field(default_factory=lambda: np.array([]))

    # Computed statistics
    mean: float = 0.0
    var: float = 0.0
    skew: float = 0.0
    kurt: float = 0.0
    jarquebera: float = 0.0
    max_idx: int = 0
    min_idx: int = 0

    # ACF/PACF info
    lags: int = 0

    # Differencing info
    d: int = 0
    ds: int = 0
    boxlam: float = 1.0

    # Optional parent reference (original series before transforms)
    parent: Optional["Tseries"] = None

    @property
    def n(self) -> int:
        """Number of observations (alias for nobs)."""
        return self.nobs

    @property
    def values(self) -> np.ndarray:
        """Return the data as a numpy array (shorthand)."""
        return self.data

    def __len__(self) -> int:
        return self.nobs

    def __repr__(self) -> str:
        return (
            f"Tseries(name={self.name!r}, nobs={self.nobs}, "
            f"freq={self.freq}, beg={self.begtime}/{self.begyear})"
        )

    def copy(self) -> "Tseries":
        """Return a deep copy."""
        import copy
        return copy.deepcopy(self)


def obs_to_date(beg_year: int, beg_sub: int, obs_no: int, freq: int
               ) -> tuple[int, int]:
    """Convert observation number to (year, subperiod).

    Parameters
    ----------
    beg_year : int
        Beginning year.
    beg_sub : int
        Beginning subperiod (1-based).
    obs_no : int
        Observation number (0-based or 1-based? This matches C: 1-based).
    freq : int
        Frequency (observations per year).

    Returns
    -------
    tuple[int, int]
        (year, subperiod)
    """
    if obs_no + beg_sub - 1 <= freq:
        per = beg_year
        sub = beg_sub + obs_no - 1
    else:
        cad = divmod(obs_no - (freq - beg_sub + 1), freq)
        if cad[1] > 0:
            per = beg_year + cad[0] + 1
            sub = cad[1]
        else:
            per = beg_year + cad[0]
            sub = freq
    return per, sub


def date_to_obs(beg_year: int, beg_sub: int, per: int, sub: int,
                freq: int) -> int:
    """Convert (year, subperiod) to 1-based observation number.

    Parameters
    ----------
    beg_year, beg_sub : int
        Beginning year and subperiod.
    per, sub : int
        Target year and subperiod.
    freq : int
        Frequency.

    Returns
    -------
    int
        1-based observation number.
    """
    srest = freq - beg_sub + 1
    if sub == freq:
        pcad = per - beg_year
        obs_no = srest + freq * pcad
    else:
        pcad = per - beg_year - 1
        sad = sub
        obs_no = srest + freq * pcad + sad
    return obs_no
