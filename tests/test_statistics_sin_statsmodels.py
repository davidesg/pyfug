"""pyfug.statistics computes ACF, PACF and Ljung-Box itself, as fue does."""
import numpy as np
import pytest

from pyfug import statistics as S


def _series():
    rng = np.random.default_rng(1)
    for i in range(60):
        n = int(rng.integers(15, 400))
        yield np.cumsum(rng.standard_normal(n)) * (i % 3 == 0) + rng.standard_normal(n)


def test_the_same_numbers_as_fue():
    fue = pytest.importorskip("fue")
    for x in _series():
        L = min(40, len(x) // 2 - 2)
        np.testing.assert_allclose(S.acf(x, L), fue.acf(x, lags=L), atol=1e-14)
        np.testing.assert_allclose(S.pacf(x, L), fue.pacf(x, lags=L), atol=1e-12)
        q = fue.ljung_box(x, lags=L)["statistic"][0]
        assert S.ljung_box(x, L)[0] == pytest.approx(q, rel=1e-12)


def test_the_same_numbers_as_statsmodels():
    sm = pytest.importorskip("statsmodels.tsa.stattools")
    from statsmodels.stats.diagnostic import acorr_ljungbox
    for x in _series():
        L = min(40, len(x) // 2 - 2)
        np.testing.assert_allclose(S.acf(x, L, unbiased=True),
                                   sm.acf(x, nlags=L, adjusted=True, fft=False)[1:], atol=1e-14)
        np.testing.assert_allclose(S.pacf(x, L), sm.pacf(x, nlags=L, method="ywm")[1:], atol=1e-12)
        r = acorr_ljungbox(x, lags=[L], return_df=False)
        assert S.ljung_box(x, L)[1] == pytest.approx(float(r.lb_pvalue.iloc[0]), rel=1e-9, abs=1e-15)


def test_pyfug_does_not_import_statsmodels():
    import subprocess
    import sys
    code = ("import sys, pyfug, pyfug.statistics, pyfug.graphics.combined; "
            "print('statsmodels' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.stdout.strip() == "False", out.stderr
