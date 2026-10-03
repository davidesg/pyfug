"""BUG-0004 — importing pyfug used to rewrite matplotlib's global rcParams.

The Jenkins-Treadway style now applies per figure (`jt_style`), so neither the
import nor drawing a pyfug figure changes how the rest of the process draws.
"""
import subprocess
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")


def test_importar_pyfug_no_cambia_ningun_rcparam():
    codigo = (
        "import matplotlib; before = dict(matplotlib.rcParams)\n"
        "import pyfug, pyfug.graphics\n"
        "print([k for k, v in matplotlib.rcParams.items() if before.get(k) != v])\n")
    out = subprocess.run([sys.executable, "-c", codigo], capture_output=True,
                         text=True, check=True).stdout.strip().splitlines()[-1]
    assert out == "[]", out


def test_dibujar_una_figura_de_pyfug_tampoco():
    from pyfug.core import Tseries
    from pyfug.graphics import plot_combined
    before = dict(matplotlib.rcParams)
    y = np.exp(4 + np.cumsum(np.random.default_rng(0).normal(0.01, 0.02, 60)))
    fig = plot_combined(Tseries(name="S", nobs=60, freq=4, begyear=2000,
                                begtime=1, data=y))
    matplotlib.pyplot.close(fig)
    assert {k for k, v in matplotlib.rcParams.items() if before.get(k) != v} == set()


def test_quien_quiera_el_estilo_global_lo_pide():
    from pyfug.graphics.base import use_jt_style, JT_DPI
    with matplotlib.rc_context():
        use_jt_style()
        assert matplotlib.rcParams["figure.dpi"] == JT_DPI
