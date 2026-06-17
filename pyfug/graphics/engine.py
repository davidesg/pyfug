"""
Main graphics engine for pyfug.

The `diffgraph` function is the central entry point — it replicates the
DiffGraph() function from FUG's fug.c, producing the complete set of
Jenkins-Treadway plots for a time series.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Optional, List

import matplotlib
# Only force Agg if no display available (headless servers)
import os as _os
if "DISPLAY" not in _os.environ and "WAYLAND_DISPLAY" not in _os.environ:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pyfug.core import Tseries, obs_to_date
from pyfug.transform import boxcox, delop, apply_diffops
from pyfug.statistics import compute_all
from pyfug.graphics.base import plot_title, file_plot_name
from pyfug.graphics.series import plot_series
from pyfug.graphics.acf_pacf import plot_acf_pacf
from pyfug.graphics.combined import plot_combined
from pyfug.graphics.histogram import plot_histogram
from pyfug.graphics.mean_deviation import plot_mean_deviation
from pyfug.ascii import generate_ascii_output


def diffgraph(ser: Tseries,
              nparma: int = 0,
              boxlam: float = 1.0,
              boxm: float = 0.0,
              boxgeom: int = 0,
              nrdiff: int = 0,
              nadiff: int = 0,
              ifadf: Optional[List[int]] = None,
              lags: int = 0,
              cbands: float = 0.0,
              m_dt_nog: int = 0,
              outname: str = "output",
              *,
              case_a: bool = False,
              case_b: bool = False,
              case_c: bool = False,
              case_d: bool = False,
              case_e: bool = False,
              case_h: bool = False,
              case_ascii: bool = True,
              output_dir: str = ".",
              save: bool = True,
              return_figs: bool = False) -> dict:
    """Produce Jenkins-Treadway graphics for a time series.

    This is the main entry point, replicating FUG's DiffGraph function.
    It applies Box-Cox and differencing transformations, computes
    statistics, and produces the requested graph types.

    Parameters
    ----------
    ser : Tseries
        Original time series.
    nparma : int
        Number of ARMA parameters (for Ljung-Box df adjustment).
    boxlam : float
        Box-Cox lambda.
    boxm : float
        Box-Cox shift parameter.
    boxgeom : int
        Use geometric mean normalization (0 or 1).
    nrdiff : int
        Regular differencing order.
    nadiff : int
        Seasonal differencing order.
    ifadf : list of int, optional
        Individual annual difference factor flags.
    lags : int
        Number of ACF/PACF lags. 0 = auto.
    cbands : float
        Confidence band override. 0 = auto.
    m_dt_nog : int
        Number of obs per group for mean-deviation. 0 = auto.
    outname : str
        Base name for output files.
    case_a : bool
        Produce series plot.
    case_b : bool
        Produce ACF/PACF plot.
    case_c : bool
        Produce combined series + ACF/PACF plot.
    case_d : bool
        Produce histogram.
    case_e : bool
        Produce mean-deviation chart.
    case_h : bool
        Include mean-deviation in identification set.
    output_dir : str
        Directory for saved figures.
    save : bool
        If True, save figures to files.
    return_figs : bool
        If True, return matplotlib Figures in the result dict.

    Returns
    -------
    dict
        Keys: 'transformed' (Tseries), 'figures' (list of Figure, if return_figs),
        'files' (list of saved filenames).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Box-Cox transform ──────────────────────────
    transformed = boxcox(ser.data, lam=boxlam, m=boxm,
                        geometric=bool(boxgeom))

    # ── Step 2: Differencing ───────────────────────────────
    ornsop = nrdiff + ser.freq * nadiff

    if ornsop > 0:
        op = delop(ser.freq, nrdiff, nadiff, ifadf)
        eff_ord = nrdiff + ser.freq * nadiff
        if ifadf and ser.freq > 1:
            for k, flag in enumerate(ifadf[:ser.freq // 2 + 1]):
                if flag:
                    eff_ord += (2 if (ser.freq == 12 and k in (1, 2, 3, 4, 5))
                                or (ser.freq == 4 and k in (1, 3)) else 1)

        n = len(transformed)
        result = np.zeros(n - eff_ord)
        for t in range(len(result)):
            val = transformed[t + eff_ord]
            for i in range(1, min(eff_ord + 1, len(op))):
                if i <= t + eff_ord:
                    val -= op[i] * transformed[t + eff_ord - i]
            result[t] = val

        new_byear, new_btime = obs_to_date(
            ser.begyear, ser.begtime, eff_ord + 1, ser.freq
        )
        res_ser = Tseries(
            name=ser.name,
            nobs=len(result),
            freq=ser.freq,
            begyear=new_byear,
            begtime=new_btime,
            data=result,
            d=nrdiff,
            ds=nadiff,
            boxlam=boxlam,
            parent=ser,
        )
    else:
        res_ser = Tseries(
            name=ser.name,
            nobs=len(transformed),
            freq=ser.freq,
            begyear=ser.begyear,
            begtime=ser.begtime,
            outyear=ser.outyear,
            data=transformed,
            boxlam=boxlam,
            parent=ser,
        )

    # ── Step 3: Compute statistics ─────────────────────────
    compute_all(res_ser, lags)

    # ── Step 4: Title and filename ─────────────────────────
    title = plot_title(nrdiff, nadiff, boxlam, ser.freq, ser.name)
    fname = file_plot_name(nrdiff, nadiff, boxlam, ser.freq, outname)

    # ── Step 5: Compute time offsets for axis labeling ─────
    if ser.begtime == 1 and ser.freq > 1:
        timeout = ornsop
    elif ser.freq > 1:
        timeout = ornsop + (ser.begtime - 1)
    else:
        timeout = ornsop + ser.outyear

    tsnobs = ser.nobs
    tsby = ser.begyear
    if ser.freq == 1:
        tsby = ser.begyear - ser.outyear

    # ── Step 6: Generate plots ─────────────────────────────
    figures = []
    files = []

    # Case A: Series only
    if case_a:
        fig = plot_series(res_ser, tsnobs=tsnobs, timeout=timeout,
                         tsby=tsby, d=nrdiff, ds=nadiff, title=title)
        if save:
            path = output_dir / f"{fname}_series.pdf"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            files.append(str(path))
        figures.append(fig)

    # Case B: ACF/PACF only
    if case_b:
        fig = plot_acf_pacf(res_ser, npar=nparma, nlags=lags,
                           cbands=cbands, title=title)
        if save:
            path = output_dir / f"acf_{fname}.pdf"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            files.append(str(path))
        figures.append(fig)

    # Case C: Combined
    if case_c:
        fig = plot_combined(res_ser, npar=nparma, tsnobs=tsnobs,
                           timeout=timeout, tsby=tsby,
                           d=nrdiff, ds=nadiff, nlags=lags,
                           cbands=cbands, title=title)
        if save:
            path = output_dir / f"{fname}.pdf"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            files.append(str(path))
        figures.append(fig)

    # Case D: Histogram
    if case_d:
        fig = plot_histogram(res_ser, d=nrdiff, ds=nadiff, title=title)
        if save:
            path = output_dir / f"hist_{fname}.pdf"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            files.append(str(path))
        figures.append(fig)

    # Case E/H: Mean-deviation
    if case_e or (case_h and nrdiff == 0 and nadiff == 0):
        nog = m_dt_nog
        if nog == 0:
            nog = 12 if ser.freq == 12 else 8
        fig = plot_mean_deviation(res_ser, nog=nog, title=title)
        if save:
            path = output_dir / f"m_dt_{fname}.pdf"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            files.append(str(path))
        figures.append(fig)

    # ── Step 7: ASCII output ────────────────────────────────
    if case_ascii:
        ascii_path = output_dir / f"{fname}.out"
        _ascii_content = generate_ascii_output(
            res_ser,
            boxlam=boxlam,
            nrdiff=nrdiff,
            nadiff=nadiff,
            nlags=lags,
            m_dt_nog=m_dt_nog,
            infile=f"{fname}.inp",
            outfile=f"{fname}.out",
            output_path=str(ascii_path),
        )
        files.append(str(ascii_path))

    result = {
        "transformed": res_ser,
        "files": files,
    }
    if return_figs:
        result["figures"] = figures

    return result


def diffgraph_set(ser: Tseries,
                  boxlam: float = 1.0,
                  boxm: float = 0.0,
                  boxgeom: int = 0,
                  max_nrdiff: int = 2,
                  max_nadiff: int = 1,
                  ifadf: Optional[List[int]] = None,
                  lags: int = 0,
                  cbands: float = 0.0,
                  m_dt_nog: int = 0,
                  outname: str = "output",
                  *,
                  case_a: bool = False,
                  case_b: bool = False,
                  case_c: bool = False,
                  case_d: bool = False,
                  case_e: bool = False,
                  case_h: bool = False,
                  output_dir: str = ".",
                  **kwargs) -> list[dict]:
    """Produce a set of identification plots across differencing orders.

    Replicates FUG's "set" mode: generates plots for all combinations
    of regular differencing (0..max_nrdiff) and seasonal differencing
    (0..max_nadiff).

    Parameters
    ----------
    ser : Tseries
        Original time series.
    boxlam : float
        Box-Cox lambda.
    boxm : float
        Box-Cox shift.
    boxgeom : int
        Geometric mean normalization flag.
    max_nrdiff : int
        Maximum regular differencing order.
    max_nadiff : int
        Maximum seasonal differencing order.
    ifadf : list of int, optional
        Individual annual difference factors.
    lags : int
        Number of ACF/PACF lags.
    cbands : float
        Confidence band override.
    m_dt_nog : int
        Mean-deviation group size.
    outname : str
        Output base name.
    case_a, case_b, case_c, case_d, case_e, case_h : bool
        Plot type flags.
    output_dir : str
        Output directory.

    Returns
    -------
    list[dict]
        Results for each (d, ds) combination.
    """
    results = []

    for ds in range(max_nadiff + 1):
        for d in range(max_nrdiff + 1):
            # Skip cases where nothing is produced
            # (original + log fix from FUG)
            result = diffgraph(
                ser,
                nparma=0,
                boxlam=boxlam,
                boxm=boxm,
                boxgeom=boxgeom,
                nrdiff=d,
                nadiff=ds,
                ifadf=ifadf,
                lags=lags,
                cbands=cbands,
                m_dt_nog=m_dt_nog,
                outname=outname,
                case_a=case_a,
                case_b=case_b,
                case_c=case_c,
                case_d=case_d,
                case_e=case_e and d == 0 and ds == 0,
                case_h=case_h and d == 0 and ds == 0,
                output_dir=output_dir,
                **kwargs,
            )
            results.append(result)

    # Extra: if boxlam != 1 and case_h, produce original-level plots too
    if boxlam != 1.0 and case_h:
        result = diffgraph(
            ser, nparma=0, boxlam=1.0, boxm=1.0, boxgeom=0,
            nrdiff=0, nadiff=0, ifadf=ifadf,
            lags=lags, cbands=cbands, m_dt_nog=m_dt_nog,
            outname=outname,
            case_h=True, output_dir=output_dir, **kwargs,
        )
        results.append(result)

    return results
