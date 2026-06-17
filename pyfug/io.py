"""
Input/Output module for pyfug.

Supports multiple input formats:
- Original .inp files (FUG 1.x format)
- CSV files
- Excel files (.xlsx)
- pandas DataFrame / Series
- Raw numpy arrays
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Optional, Union
from pyfug.core import Tseries


def read_inp(filepath: Union[str, Path]) -> Tseries:
    """Read a FUG 1.x .inp file.

    The .inp format is a fixed-format ASCII file with the following structure:
    - 5 header lines (comments)
    - Frequency line label
    - Frequency value
    - Observations line label
    - nobs, begtime (if freq>1), begyear, name
      OR nobs, outyear, begyear, name (if freq==1)
    - Box-Cox line label
    - boxlam, boxm, boxgeom, nrdiff, nadiff
    - Individual factors line label
    - ifadf[0]..ifadf[freq/2] (if freq>1) or blank line
    - Data line label
    - data values (one per line)

    Parameters
    ----------
    filepath : str or Path
        Path to the .inp file (with or without .inp extension).

    Returns
    -------
    Tseries
    """
    filepath = Path(filepath)
    if filepath.suffix != ".inp":
        filepath = filepath.with_suffix(".inp")

    with open(filepath, "r") as f:
        lines = f.readlines()

    # Strip whitespace and skip empty lines
    lines = [l.strip() for l in lines]
    # Remove pure-comment lines (start with single * or are **** separators)
    # Keep section markers starting with **
    data_lines = [l for l in lines if l and not (
        (l.startswith("*") and not l.startswith("**")) or
        all(c == '*' for c in l)
    )]

    idx = 0

    # --- Frequency ---
    # Skip label line ("** Frequency of time series...")
    idx += 1  # skip label
    freq = int(data_lines[idx]); idx += 1

    # --- Observations and name ---
    idx += 1  # skip label
    parts = data_lines[idx].split(); idx += 1
    nobs = int(parts[0])

    if freq > 1:
        begtime = int(parts[1])
        begyear = int(parts[2])
        name = parts[3] if len(parts) > 3 else ""
        outyear = 0
    else:
        outyear = int(parts[1])
        begyear = int(parts[2])
        name = parts[3] if len(parts) > 3 else ""
        begtime = 1

    # --- Box-Cox and differencing parameters ---
    idx += 1  # skip label
    parts = data_lines[idx].split(); idx += 1
    # Parse up to 5 values with safe defaults
    boxlam = float(parts[0]) if len(parts) > 0 else 1.0
    boxm = float(parts[1]) if len(parts) > 1 else 0.0
    boxgeom = int(parts[2]) if len(parts) > 2 else 0
    nrdiff = int(parts[3]) if len(parts) > 3 else 0
    nadiff = int(parts[4]) if len(parts) > 4 else 0

    # --- Individual annual difference factors ---
    idx += 1  # skip label
    if freq > 1:
        parts = data_lines[idx].split(); idx += 1
        ifadf = [int(p) for p in parts]
    else:
        idx += 1  # skip blank/comment
        ifadf = []

    # --- Data values ---
    idx += 1  # skip label
    data_values = []
    for i in range(idx, len(data_lines)):
        try:
            data_values.append(float(data_lines[i]))
        except ValueError:
            pass  # skip non-numeric lines

    data = np.array(data_values, dtype=np.float64)
    # Truncate to expected nobs
    data = data[:nobs]

    ts = Tseries(
        name=name,
        nobs=nobs,
        freq=freq,
        begyear=begyear,
        begtime=begtime,
        outyear=outyear,
        data=data,
        boxlam=boxlam,
        d=nrdiff,
        ds=nadiff,
    )

    return ts


def read_csv(filepath: Union[str, Path],
             name: str = "",
             freq: int = 1,
             begyear: int = 2000,
             begtime: int = 1,
             column: Union[int, str] = 0,
             skiprows: int = 0,
             **kwargs) -> Tseries:
    """Read time series data from a CSV file.

    Parameters
    ----------
    filepath : str or Path
        Path to the CSV file.
    name : str
        Series name.
    freq : int
        Data frequency (1=annual, 4=quarterly, 12=monthly).
    begyear : int
        Beginning year.
    begtime : int
        Beginning period within year (1-based).
    column : int or str
        Column index or name containing the data.
    skiprows : int
        Number of header rows to skip.
    **kwargs
        Additional arguments passed to pandas.read_csv.

    Returns
    -------
    Tseries
    """
    import pandas as pd
    df = pd.read_csv(filepath, skiprows=skiprows, **kwargs)

    if isinstance(column, str):
        values = df[column].dropna().values
    else:
        values = df.iloc[:, column].dropna().values

    return Tseries(
        name=name,
        nobs=len(values),
        freq=freq,
        begyear=begyear,
        begtime=begtime,
        data=np.asarray(values, dtype=np.float64),
    )


def read_excel(filepath: Union[str, Path],
               name: str = "",
               freq: int = 1,
               begyear: int = 2000,
               begtime: int = 1,
               sheet_name: Union[str, int] = 0,
               column: Union[int, str] = 0,
               skiprows: int = 0,
               **kwargs) -> Tseries:
    """Read time series data from an Excel file.

    Parameters
    ----------
    filepath : str or Path
        Path to the .xlsx/.xls file.
    name : str
        Series name.
    freq : int
        Data frequency.
    begyear : int
        Beginning year.
    begtime : int
        Beginning period.
    sheet_name : str or int
        Sheet name or index.
    column : int or str
        Column index or name.
    skiprows : int
        Number of header rows.
    **kwargs
        Additional arguments passed to pandas.read_excel.

    Returns
    -------
    Tseries
    """
    import pandas as pd
    df = pd.read_excel(filepath, sheet_name=sheet_name,
                       skiprows=skiprows, **kwargs)

    if isinstance(column, str):
        values = df[column].dropna().values
    else:
        values = df.iloc[:, column].dropna().values

    return Tseries(
        name=name,
        nobs=len(values),
        freq=freq,
        begyear=begyear,
        begtime=begtime,
        data=np.asarray(values, dtype=np.float64),
    )


def read_pandas(series_or_array,
                name: str = "",
                freq: int = 1,
                begyear: int = 2000,
                begtime: int = 1) -> Tseries:
    """Create a Tseries from a pandas Series, DataFrame column, or numpy array.

    Parameters
    ----------
    series_or_array : pd.Series, pd.DataFrame, or np.ndarray
        Input data.
    name : str
        Series name.
    freq : int
        Data frequency.
    begyear : int
        Beginning year.
    begtime : int
        Beginning period.

    Returns
    -------
    Tseries
    """
    import pandas as pd

    if isinstance(series_or_array, pd.DataFrame):
        values = series_or_array.iloc[:, 0].dropna().values
    elif isinstance(series_or_array, pd.Series):
        values = series_or_array.dropna().values
        if not name and series_or_array.name:
            name = str(series_or_array.name)
        # Try to infer date info from index
        if isinstance(series_or_array.index, pd.DatetimeIndex):
            if len(series_or_array.index) > 0:
                begyear = series_or_array.index[0].year
                month = series_or_array.index[0].month
                if freq == 12:
                    begtime = month
                elif freq == 4:
                    begtime = (month - 1) // 3 + 1
    else:
        values = np.asarray(series_or_array, dtype=np.float64)

    return Tseries(
        name=name,
        nobs=len(values),
        freq=freq,
        begyear=begyear,
        begtime=begtime,
        data=np.asarray(values, dtype=np.float64),
    )
