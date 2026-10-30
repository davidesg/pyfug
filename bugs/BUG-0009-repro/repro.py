"""BUG-0009: without a display, importing pyfug.graphics changes matplotlib's
GLOBAL backend. pyfug/graphics/engine.py does, at import,

    if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
        matplotlib.use("Agg")

and matplotlib.use writes rcParams["backend"] (and "backend_fallback"). It is
the remnant of BUG-0004 ("importing pyfug changes every figure of the
process"): the style moved to jt_style, the backend did not. It shows on every
headless machine -- servers, CI, containers: the clean-install test of atsw
2.1.0 (2026-10-30, ten distributions in podman) failed
tests/test_bug_0004_rcparams_por_figura.py in all ten, and it passes here only
when DISPLAY is set.

The repro imports pyfug.graphics in a child with no display and no MPLBACKEND,
and lists the rcParams that changed. Expected: none.

    python3 bugs/BUG-0009-repro/repro.py   # exits 1 while open
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
env = {k: v for k, v in os.environ.items()
       if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MPLBACKEND")}
env["PYTHONPATH"] = os.path.join(HERE, "..", "..")
code = ("import matplotlib; before = dict(matplotlib.rcParams)\n"
        "import pyfug, pyfug.graphics\n"
        "print(pyfug.__file__)\n"
        "print([k for k, v in matplotlib.rcParams.items() if before.get(k) != v])\n")
out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                     text=True, check=True).stdout.strip().splitlines()
print("pyfug from", out[-2])
print("rcParams changed by the import:", out[-1])
sys.exit(1 if out[-1] != "[]" else 0)
