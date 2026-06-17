"""
Transformation module for pyfug.

Implements:
- Box-Cox transformation (with and without geometric mean normalization)
- Regular differencing operator: ∇ᵈ = (1 - B)ᵈ
- Seasonal/complete annual differencing: ∇ₛ = (1 - Bˢ)
- Individual frequency components of annual differencing
- Combined differencing operator construction
"""

from __future__ import annotations

import numpy as np
from typing import Optional, List
from pyfug.core import Tseries, obs_to_date


def boxcox(data: np.ndarray,
           lam: float = 1.0,
           m: float = 0.0,
           geometric: bool = False,
           refactor: float = 1.0) -> np.ndarray:
    """Apply Box-Cox transformation to data.

    Box-Cox: y(λ) = ( (y + m)^λ - 1 ) / λ   if λ ≠ 0
             y(λ) = log(y + m)               if λ = 0
             y(λ) = y                        if λ = 1

    With geometric normalization (boxgeom=1):
        Jacob = (∏(y + m))^(1/n)
        y(λ) = Jacob · log(y + m)                        if λ = 0
        y(λ) = ((y + m)^λ - 1) / (λ · Jacob^(λ-1))      if λ ≠ 0,1

    Parameters
    ----------
    data : np.ndarray
        Input data vector.
    lam : float
        Box-Cox lambda parameter.
    m : float
        Additive shift (ensures y+m > 0 for log).
    geometric : bool
        If True, apply geometric mean normalization (boxgeom).
    refactor : float
        Scale factor applied to output.

    Returns
    -------
    np.ndarray
        Transformed data.
    """
    shifted = data + m

    if not geometric:
        if lam == 0.0:
            if np.any(shifted <= 0):
                raise ValueError("Box-Cox λ=0 requires data+m > 0")
            return refactor * np.log(shifted)
        elif lam != 1.0:
            return refactor * (np.power(shifted, lam) - 1.0) / lam
        else:
            return refactor * data
    else:
        product = np.prod(shifted)
        jacob = np.power(product, 1.0 / len(data))

        if lam == 0.0:
            return refactor * jacob * np.log(shifted)
        elif lam != 1.0:
            return refactor * (np.power(shifted, lam) - 1.0) / (
                lam * np.power(jacob, lam - 1.0))
        else:
            return refactor * data


def regular_diff(data: np.ndarray, d: int) -> np.ndarray:
    """Apply regular differencing d times: ∇ᵈ = (1 - B)ᵈ.

    Uses binomial coefficient recursion for numerical stability.

    Parameters
    ----------
    data : np.ndarray
        Input data.
    d : int
        Order of differencing.

    Returns
    -------
    np.ndarray
        Differenced data, length = n - d.
    """
    if d == 0:
        return data.copy()

    n = len(data)
    result = data.copy()
    for _ in range(d):
        result = np.diff(result)
    return result


def seasonal_diff(data: np.ndarray, period: int, ds: int) -> np.ndarray:
    """Apply seasonal differencing ds times: ∇ₛ = (1 - Bˢ).

    Parameters
    ----------
    data : np.ndarray
        Input data.
    period : int
        Seasonal period (e.g., 12 for monthly, 4 for quarterly).
    ds : int
        Number of seasonal differences.

    Returns
    -------
    np.ndarray
        Seasonally differenced data, length = n - ds*period.
    """
    if ds == 0:
        return data.copy()

    result = data.copy()
    for _ in range(ds):
        result = result[period:] - result[:-period]
    return result


def delop(sp: int, d: int, ds: int,
          ifds: Optional[List[int]] = None) -> np.ndarray:
    """Construct the combined differencing operator polynomial.

    This replicates the DelOp function from FUG's delop.c.

    The operator is defined as:
        (1 - B)ᵈ · (1 - Bˢᵖ)ᵈˢ · ∏ individual factors

    Returns the polynomial coefficients op[0..ord] where ord = d + ds*sp + extra
    for individual factors. The operator is stored such that applying it means:
        y_new[t] = data[t] + Σᵢ₌₁ᵒʳᵈ op[i] · data[t-i]

    Parameters
    ----------
    sp : int
        Seasonal period (frequency).
    d : int
        Regular differencing order.
    ds : int
        Seasonal differencing order.
    ifds : list of int, optional
        Flags for individual annual difference factors (length sp/2 + 1).

    Returns
    -------
    np.ndarray
        Operator polynomial coefficients op[0..ord], where op[0] = -1.
    """
    # ---- [1] Multiply regular by complete annual differences ----
    pp1 = d + ds * sp
    pol1 = np.zeros(pp1 + 1)
    pol1[0] = -1.0
    pp = 0

    if ds > 0:
        for _ in range(ds):
            pol2 = np.zeros(pp1 + 1)
            for j in range(pp + sp + 1):
                if 0 <= j < sp:
                    pol2[j] = pol1[j]
                elif sp <= j <= pp:
                    pol2[j] = pol1[j] - pol1[j - sp]
                elif pp < j <= pp + sp:
                    pol2[j] = -pol1[j - sp]
            pp += sp
            pol1[:] = pol2

    if d > 0:
        for _ in range(d):
            pol2 = np.zeros(pp1 + 1)
            for j in range(pp + 2):
                if 0 <= j < 1:
                    pol2[j] = pol1[j]
                elif 1 <= j <= pp:
                    pol2[j] = pol1[j] - pol1[j - 1]
                elif pp < j <= pp + 1:
                    pol2[j] = -pol1[j - 1]
            pp += 1
            pol1[:] = pol2

    # ---- [2] Multiply individual factors of the annual difference ----
    if ifds is None or sp <= 1 or not any(ifds):
        return pol1[:pp + 1].copy()

    pp2 = 0
    # Count how many individual factors are active
    max_components = sp // 2 + 1
    if len(ifds) < max_components:
        ifds = ifds + [0] * (max_components - len(ifds))

    # Compute extra polynomial order from active components
    extra_order = 0
    for k in range(max_components):
        if ifds[k]:
            if (sp == 12 and k == 1) or (sp == 12 and k == 2) or \
               (sp == 12 and k == 4) or (sp == 12 and k == 5) or \
               ((sp == 12 or sp == 4) and k == 3):
                extra_order += 2
            else:
                extra_order += 1

    total_ord = pp + extra_order
    pol2 = np.zeros(total_ord + 1)
    pol3 = np.zeros(total_ord + 1)
    pol3[0] = -1.0
    pp2 = 0

    # Factor 0: (1 - B) if ifds[0]=1 for sp=12 or sp=4
    if (sp == 12 or sp == 4) and ifds[0] == 1:
        pol4 = np.array([-1.0, 1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(2):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 1
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 1: 1 - √3 B + B² (frequency π/6 for monthly)
    if sp == 12 and ifds[1] == 1:
        pol4 = np.array([-1.0, np.sqrt(3.0), -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(3):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 2
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 2: 1 - B + B² (frequency π/3 for monthly)
    if sp == 12 and ifds[2] == 1:
        pol4 = np.array([-1.0, 1.0, -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(3):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 2
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 3: 1 + B² (frequency π/2 for monthly, π for quarterly)
    if (sp == 12 and ifds[3] == 1) or (sp == 4 and ifds[1] == 1):
        pol4 = np.array([-1.0, 0.0, -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(3):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 2
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 4: 1 + B + B² (frequency 2π/3 for monthly)
    if sp == 12 and ifds[4] == 1:
        pol4 = np.array([-1.0, -1.0, -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(3):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 2
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 5: 1 + √3 B + B² (frequency 5π/6 for monthly)
    if sp == 12 and ifds[5] == 1:
        pol4 = np.array([-1.0, -np.sqrt(3.0), -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(3):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 2
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # Factor 6: 1 + B (frequency π for monthly, 2π for quarterly)
    if (sp == 12 and ifds[6] == 1) or (sp == 4 and ifds[2] == 1):
        pol4 = np.array([-1.0, -1.0])
        pol2.fill(0.0)
        pol2[0] = -1.0
        for i in range(pp2 + 1):
            for j in range(2):
                pol2[j + i] -= pol4[j] * pol3[i]
        pp2 += 1
        pol3[:pp2 + 1] = pol2[:pp2 + 1]

    # ---- [3] Convolve pol1 and pol3 ----
    op = np.zeros(pp + pp2 + 2)
    op[0] = -1.0
    for i in range(pp + 1):
        for j in range(pp2 + 1):
            if pol1[i] != 0 and pol3[j] != 0:
                if i + j >= 1:  # op[0] stays -1
                    op[i + j] += pol1[i] * pol3[j]

    # Negate the coefficients (operator is -polynomial for application)
    return op


def apply_diffops(ser: Tseries,
                  d: int,
                  ds: int,
                  ifadf: Optional[List[int]] = None) -> Tseries:
    """Apply combined differencing operators to a Tseries.

    Parameters
    ----------
    ser : Tseries
        Input (already Box-Cox transformed) series.
    d : int
        Regular differencing order.
    ds : int
        Seasonal differencing order.
    ifadf : list of int, optional
        Individual annual difference factors.

    Returns
    -------
    Tseries
        Differenced series with updated metadata.
    """
    if ifadf is None and ser.freq > 1:
        ifadf = [0] * (ser.freq // 2 + 1)

    ord_total = d + ser.freq * ds
    if ifadf:
        ord_total += sum(ifadf)

    if ord_total == 0:
        return ser.copy()

    # Get the differencing operator
    op = delop(ser.freq, d, ds, ifadf)
    # Effective order (last non-zero for np.convolve)
    eff_ord = d + ser.freq * ds
    if ifadf:
        for k, flag in enumerate(ifadf):
            if flag:
                if k == 0:
                    eff_ord += 1
                else:
                    eff_ord += 2 if k <= 5 else 1

    # Apply operator: y[t] = Σ op[i] * data[t-i]
    n = len(ser.data)
    result_len = n - eff_ord
    result = np.zeros(result_len)

    for t in range(result_len):
        val = ser.data[t + eff_ord]
        for i in range(1, min(eff_ord + 1, len(op))):
            if i <= t + eff_ord:
                val -= op[i] * ser.data[t + eff_ord - i]
        result[t] = val

    # Update begin date
    obs_offset = eff_ord + 1  # 1-based offset
    new_byear, new_btime = obs_to_date(
        ser.begyear, ser.begtime, obs_offset, ser.freq
    )

    return Tseries(
        name=ser.name,
        nobs=result_len,
        freq=ser.freq,
        begyear=new_byear,
        begtime=new_btime,
        outyear=ser.outyear,
        data=result,
        d=d,
        ds=ds,
        boxlam=ser.boxlam,
        parent=ser,
    )
