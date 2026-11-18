"""The suite's one CCF (pyfug.statistics.ccf, pyfug.graphics.ccf).

Homologated with atsw-gui's C (lib/ccfplot) — the format of the two approved
prototypes, GraphMaker and drvus — and with drvarma's copy of the computation,
which its engines use: the two are pinned to the last bit.
"""
import os

import numpy as np
import pytest

import matplotlib
matplotlib.use("Agg")

from pyfug.statistics import ccf
from pyfug.graphics.ccf import (ccf_default_lags, ccf_scale, draw_ccf_panel, p_label,
                                plot_ccf, save_ccf)


def _par(n=120, seed=3):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    y = np.r_[0.0, 0.0, 0.7 * x[:-2]] + 0.5 * rng.standard_normal(n)   # x leads y by 2
    return y, x


def test_the_lag_convention():
    """At k > 0 the second series leads: y_t with x_{t-k}."""
    y, x = _par()
    r = ccf(y, x, 6)
    assert len(r) == 13 and int(np.argmax(r)) - 6 == 2


def test_the_same_numbers_as_drvarma():
    dv = pytest.importorskip("drvarma.diagnostics")
    y, x = _par()
    assert np.array_equal(ccf(y, x, 9), dv.ccf(y, x, 9))


@pytest.mark.parametrize("freq, lags", [(1, 7), (4, 15), (12, 12), (2, 6), (6, 18)])
def test_the_default_lags_are_lib_ccfplots(freq, lags):
    # ccf_lags_por_defecto: 7 annual, 15 quarterly, 12 monthly, 3*freq otherwise
    assert ccf_default_lags(freq) == lags


@pytest.mark.parametrize("value, scale", [(0.1, 0.4), (0.39, 0.4), (0.393, 0.6),
                                          (0.7, 0.8), (0.79, 1.0), (1.5, 1.0)])
def test_the_scale_is_lib_ccfplots(value, scale):
    # escala: +-0.4, enlarged to 0.6, 0.8, 1.0 when a bar or the band does not fit
    assert ccf_scale(value) == scale


def test_the_statistic_is_called_P():
    assert p_label(944.3, 60) == "P ( 60 ) = 944.3"
    assert p_label(3.0, 0).startswith("P = 3.0")


def test_the_panel():
    import matplotlib.pyplot as plt
    y, x = _par()
    r = ccf(y, x, 12)
    fig, ax = plt.subplots()
    draw_ccf_panel(ax, r, 12, len(y), 12, "X - Y", p_label(20.0, 40))
    assert ax.get_title() == "X - Y" and ax.get_xlabel() == "P ( 40 ) = 20.0"
    c = ccf_scale(max(np.max(np.abs(r)), 2 / np.sqrt(len(y))))
    assert c > 0.4 and ax.get_ylim() == (-c, c)          # the lead does not fit 0.4
    assert ax.get_xlim() == (-12.5, 12.5)
    plt.close(fig)


def test_vectors_and_raster(tmp_path):
    y, x = _par()
    fig = plot_ccf(ccf(y, x, 7), 7, len(y), 1, "X - Y", p_label(12.0, 20))
    paths = save_ccf(fig, str(tmp_path / "ccf.png"))
    assert [os.path.splitext(p)[1] for p in paths] == [".png", ".svg", ".pdf"]
    assert all(os.path.getsize(p) > 1000 for p in paths)
    assert open(paths[1]).read().lstrip().startswith(("<?xml", "<svg"))
