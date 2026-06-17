"""Integration tests for pyfug using the original FUG PU example data."""

import sys
import os
import tempfile

# Ensure we can import pyfug
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from pyfug import Tseries
from pyfug.io import read_inp
from pyfug.transform import boxcox, delop, regular_diff, seasonal_diff
from pyfug.statistics import (
    descriptive_stats, acf, pacf, ljung_box, chi_test,
    acf_pacf_max, series_max, compute_all
)
from pyfug.graphics.base import plot_title, file_plot_name

# ── PU example data (from original FUG examples/PU.inp) ──────

PU_DATA = [
    168.800, 169.800, 171.200, 171.300, 171.500, 172.400,
    172.800, 172.800, 173.700, 174.000, 174.100, 174.000,
    175.100, 175.800, 176.200, 176.900, 177.700, 178.000,
    177.500, 177.500, 178.300, 177.700, 177.400, 176.700,
    177.100, 177.800, 178.800, 179.800, 179.800, 179.900,
    180.100, 180.700, 181.000, 181.300, 181.300, 180.900,
    181.700, 183.100, 184.200, 183.800, 183.500, 183.700,
    183.900, 184.600, 185.200, 185.000, 184.500, 184.300,
    185.200, 186.200, 187.400, 188.000, 189.100, 189.700,
    189.400, 189.500, 189.900, 190.900, 191.000, 190.300,
    190.700, 191.800, 193.300, 194.600, 194.400, 194.500,
    195.400, 196.400, 198.800, 199.200, 197.600, 196.800,
    198.300, 198.700, 199.800, 201.500, 202.500, 202.900,
    203.500, 203.900, 202.900, 201.800, 201.500, 201.800,
    202.416, 203.499, 205.352, 206.686, 207.949, 208.352,
    208.299, 207.917, 208.490, 208.936, 210.177, 210.036,
    211.080, 211.693, 213.528, 214.823, 216.632, 218.815,
    219.964, 219.086, 218.783, 216.573, 212.425, 210.228,
]


def create_pu_series():
    """Create the standard PU Tseries matching original FUG example."""
    return Tseries(
        name="PU",
        nobs=108,
        freq=12,
        begyear=2000,
        begtime=1,
        data=np.array(PU_DATA, dtype=np.float64),
    )


# ── Tests ────────────────────────────────────────────────────

def test_tseries_creation():
    """Tseries dataclass basic operations."""
    ser = create_pu_series()
    assert ser.name == "PU"
    assert ser.nobs == 108
    assert ser.freq == 12
    assert ser.begyear == 2000
    assert ser.begtime == 1
    assert len(ser) == 108
    assert ser.n == 108
    assert len(ser.data) == 108
    print("✓ Tseries creation")


def test_io_read_inp():
    """Read the original PU.inp file."""
    import tempfile
    import os

    # Write a temporary .inp file
    inp_content = """********************************************************
* Example of input file for program FUG                *
* Copyright (C) 2009 A.B. Treadway & D.E. Guerrero     *
********************************************************

** Frequency of time series: either 1(A), 4(Q) or 12(M):
   12
** Number of observations, starting date and name of time series:
   108 1 2000 PU
** Box-Cox lambda, regular differences and complete annual differences:
   0.0 0 0 0 0
** Individual factors of the annual difference (starting at freq 0.0):
   0 0 0 0 0 0 0
** Time series (stochastic and non-standard deterministic variables):
""" + "\n".join(str(v) for v in PU_DATA)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".inp",
                                      delete=False) as f:
        f.write(inp_content)
        tmp_path = f.name

    try:
        ser = read_inp(tmp_path)
        assert ser.name == "PU"
        assert ser.nobs == 108
        assert ser.freq == 12
        assert ser.begyear == 2000
        assert ser.begtime == 1
        assert ser.boxlam == 0.0
        assert ser.d == 0
        assert ser.ds == 0
        assert len(ser.data) == 108
        assert abs(ser.data[0] - 168.800) < 1e-6
        assert abs(ser.data[-1] - 210.228) < 1e-6
        print("✓ read_inp")
    finally:
        os.unlink(tmp_path)


def test_boxcox():
    """Box-Cox transformation: log, identity, and lambda."""
    data = np.array([1.0, 2.0, 4.0, 8.0])

    # Identity (lambda = 1)
    result = boxcox(data, lam=1.0)
    np.testing.assert_allclose(result, data)
    assert np.allclose(result, data)

    # Log (lambda = 0, m=0)
    result = boxcox(data, lam=0.0, m=0.0)
    expected = np.log(data)
    np.testing.assert_allclose(result, expected)

    # Lambda = 0.5 (sqrt-like)
    result = boxcox(data, lam=0.5, m=0.0)
    expected = 2.0 * (np.sqrt(data) - 1.0)
    np.testing.assert_allclose(result, expected)

    print("✓ boxcox")


def test_regular_diff():
    """Regular differencing."""
    data = np.array([1.0, 3.0, 6.0, 10.0, 15.0])

    # d = 1
    result = regular_diff(data, d=1)
    expected = np.array([2.0, 3.0, 4.0, 5.0])
    np.testing.assert_allclose(result, expected)

    # d = 2
    result = regular_diff(data, d=2)
    expected = np.array([1.0, 1.0, 1.0])
    np.testing.assert_allclose(result, expected)

    # d = 0
    result = regular_diff(data, d=0)
    np.testing.assert_allclose(result, data)

    print("✓ regular_diff")


def test_seasonal_diff():
    """Seasonal differencing."""
    # Simulated quarterly data with trend
    data = np.array([
        1.0, 2.0, 3.0, 4.0,
        5.0, 6.0, 7.0, 8.0,
        9.0, 10.0, 11.0, 12.0,
    ])

    # ds=1, period=4
    result = seasonal_diff(data, period=4, ds=1)
    expected = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0])
    np.testing.assert_allclose(result, expected)

    print("✓ seasonal_diff")


def test_delop():
    """Difference operator construction."""
    # (1 - B) operator with sp=12, d=1, ds=0
    op = delop(12, 1, 0, [0, 0, 0, 0, 0, 0, 0])
    # Should give: [-1, 1, 0, 0, ...]
    assert op[0] == -1.0
    assert op[1] == 1.0

    # (1 - B)(1 - B^12) with sp=12, d=1, ds=1
    op = delop(12, 1, 1, [0, 0, 0, 0, 0, 0, 0])
    assert op[0] == -1.0
    # op[1] = 1 (from 1-B), op[12] = 1 (from 1-B^12), op[13] = -1 (cross)
    assert op[1] == 1.0
    assert op[12] == 1.0
    assert op[13] == -1.0

    print("✓ delop")


def test_descriptive_stats():
    """Descriptive statistics computation."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    stats = descriptive_stats(data)
    assert abs(stats["mean"] - 3.0) < 1e-10
    assert abs(stats["std"] - np.sqrt(2.0)) < 1e-10
    assert abs(stats["skew"]) < 1e-10   # symmetric
    assert stats["kurt"] < 0            # platykurtic for uniform-like
    print("✓ descriptive_stats")


def test_acf_pacf():
    """ACF and PACF computation."""
    ser = create_pu_series()

    # Transform: log
    transformed = boxcox(ser.data, lam=0.0, m=0.0)

    # ACF
    acf_vals = acf(transformed, nlags=12)
    assert len(acf_vals) == 12
    # ACF at lag 1 should be positive and high for trending series
    assert acf_vals[0] > 0.8

    # PACF
    pacf_vals = pacf(transformed, nlags=12)
    assert len(pacf_vals) == 12
    # PACF at lag 1 should be high
    assert abs(pacf_vals[0]) > 0.5

    print("✓ acf/pacf")


def test_ljung_box():
    """Ljung-Box Q statistic."""
    ser = create_pu_series()
    transformed = boxcox(ser.data, lam=0.0, m=0.0)

    q, pval = ljung_box(transformed, nlags=12)
    # Q should be significant for trending series
    assert q > 10.0
    assert pval < 0.05

    # chi_test (convenience wrapper)
    q2 = chi_test(transformed, nlags=12)
    assert abs(q - q2) < 1e-6

    print("✓ ljung_box")


def test_acf_pacf_max():
    """Auto y-axis scaling for correlograms."""
    acf_vals = np.array([0.1, 0.3, 0.5, 0.2])
    pacf_vals = np.array([0.6, 0.1, 0.1, 0.1])

    cmax = acf_pacf_max(acf_vals, pacf_vals)
    # max is 0.6, should round to 0.60 (no change since >0.40 and ≤0.60)
    assert cmax == 0.60

    # Now with 0.7
    acf_vals2 = np.array([0.7, 0.3, 0.1])
    pacf_vals2 = np.array([0.1, 0.1, 0.1])
    cmax = acf_pacf_max(acf_vals2, pacf_vals2)
    assert cmax == 0.80

    print("✓ acf_pacf_max")


def test_series_max():
    """Auto y-axis scaling for series plots."""
    data = np.array([1.0, -3.0, 5.5, 2.0])
    abs_max = series_max(data)
    assert abs_max == 6.0  # 5.5 rounds up to 6.0

    data2 = np.array([1.0, 2.0, 3.0])
    abs_max = series_max(data2)
    assert abs_max == 4.0  # default minimum

    print("✓ series_max")


def test_compute_all():
    """Attach all statistics to a Tseries."""
    ser = create_pu_series()
    compute_all(ser)
    assert ser.lags > 0
    assert ser.lags <= ser.nobs - 1
    assert ser.mean != 0.0
    assert ser.var > 0.0
    print("✓ compute_all")


def test_plot_title():
    """Title generation with differencing notation."""
    # Log, no differences
    title = plot_title(0, 0, 0.0, 12, "PU")
    assert "ln" in title
    assert "PU" in title

    # 1 regular diff, log
    title = plot_title(1, 0, 0.0, 12, "PU")
    assert "\u2207" in title or "nabla" in title.lower()  # Unicode nabla

    # Seasonal diff
    title = plot_title(0, 1, 1.0, 12, "PU")
    assert "\u2081\u2082" in title or "12" in title  # Unicode subscript 12

    print("✓ plot_title")


def test_file_plot_name():
    """Filename generation convention."""
    # d0, no lambda change
    name = file_plot_name(0, 0, 1.0, 12, "PU")
    assert name == "d0PU"

    # d1, log
    name = file_plot_name(1, 0, 0.0, 12, "PU")
    assert name == "d1lnPU"

    # d1, D1, log
    name = file_plot_name(1, 1, 0.0, 12, "PU")
    assert name == "d1D1lnPU"

    # d1, lambda=0.5
    name = file_plot_name(1, 0, 0.5, 12, "PU")
    assert name == "d1l0.5PU"

    print("✓ file_plot_name")


def test_meandv():
    """Mean-Deviation calculations."""
    from pyfug.graphics.mean_deviation import meandv

    # Simple data: 8 groups of 3
    data = np.arange(24, dtype=np.float64)
    z_means, z_stdevs = meandv(data, nog=3)

    assert len(z_means) == 8
    assert len(z_stdevs) == 8

    # All groups have same stdev (uniform distribution over 3 points)
    # so standardized stdevs should be near 0
    assert np.std(z_stdevs) < 0.1

    print("✓ meandv")


def test_graphics_generation():
    """Test that graphics can be generated without errors."""
    import matplotlib
    matplotlib.use("Agg")

    from pyfug.graphics.engine import diffgraph as dg

    ser = create_pu_series()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test combined plot
        result = dg(ser, boxlam=0.0, boxm=0.0, nrdiff=0, nadiff=0,
                    case_c=True, case_ascii=True, output_dir=tmpdir, save=True)
        assert len(result["files"]) == 2  # PDF + .out
        assert os.path.exists(result["files"][0])
        assert "transformed" in result
        assert result["transformed"].nobs == 108  # no diffs

        # Test all plot types
        result = dg(ser, boxlam=0.0, boxm=0.0, nrdiff=0, nadiff=0,
                    case_a=True, case_b=True, case_c=True,
                    case_d=True, case_e=True, case_ascii=True,
                    output_dir=tmpdir, save=True,
                    return_figs=True)
        assert len(result["files"]) == 6  # 5 PDFs + 1 .out
        assert len(result["figures"]) == 5

        # With differencing
        result = dg(ser, boxlam=0.0, boxm=0.0, nrdiff=1, nadiff=0,
                    case_c=True, output_dir=tmpdir, save=True)
        assert result["transformed"].nobs == 107  # lost 1 to diff

        print("✓ graphics generation")


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("pyfug — Integration Tests")
    print("=" * 50)

    test_tseries_creation()
    test_io_read_inp()
    test_boxcox()
    test_regular_diff()
    test_seasonal_diff()
    test_delop()
    test_descriptive_stats()
    test_acf_pacf()
    test_ljung_box()
    test_acf_pacf_max()
    test_series_max()
    test_compute_all()
    test_plot_title()
    test_file_plot_name()
    test_meandv()
    test_graphics_generation()

    print("\n" + "=" * 50)
    print("All tests passed.")
