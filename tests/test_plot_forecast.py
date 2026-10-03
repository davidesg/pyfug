"""pyfug.plot_forecast — fuf's forecast graph (fufplot.c `fp_forecast`)."""
import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from pyfug.graphics import plot_forecast  # noqa: E402


def _datos(L=24, freq=12):
    rng = np.random.default_rng(1)
    y = np.concatenate([rng.normal(2, 1, L), np.linspace(2, 3, L)])
    band = np.concatenate([np.zeros(L), y[L:] + 1])
    band2 = np.concatenate([np.zeros(L), y[L:] - 1])
    return dict(y=y, band=band, band2=band2, err=rng.normal(0, 0.5, L), L=L,
                sigma=0.5, freq=freq, first_year=2019, first_season=1,
                title="LRC anual (%)")


def test_el_lienzo_y_los_dos_paneles_son_los_del_C():
    fig = plot_forecast(**_datos())
    w, h = fig.get_size_inches() * 72
    assert (round(w, 1), round(h, 1)) == (324.0, 453.0)
    assert len(fig.axes) == 2
    titulos = [t.get_text() for t in fig.texts]
    assert "LRC anual (%)" in titulos and "ERR" in titulos
    matplotlib.pyplot.close(fig)


def test_el_panel_de_errores_para_en_el_origen_de_la_prevision():
    """Mismo x que el de arriba, más estrecho: (L-1)/(2L-1) de su ancho."""
    L = 24
    fig = plot_forecast(**_datos(L))
    arriba, abajo = sorted(fig.axes, key=lambda a: -a.get_position().y0)
    ratio = abajo.get_position().width / arriba.get_position().width
    assert ratio == pytest.approx((L - 1) / (2 * L - 1), rel=1e-6)
    matplotlib.pyplot.close(fig)


def test_un_rotulo_por_ano_en_mensual_y_cada_dos_en_trimestral():
    fig = plot_forecast(**_datos(24, 12))
    arriba = max(fig.axes, key=lambda a: a.get_position().y0)
    assert [t.get_text() for t in arriba.get_xticklabels()] == [
        "2019", "2020", "2021", "2022"]
    matplotlib.pyplot.close(fig)
    fig = plot_forecast(**_datos(16, 4))
    arriba = max(fig.axes, key=lambda a: a.get_position().y0)
    assert [t.get_text() for t in arriba.get_xticklabels()] == [
        "2019", "2021", "2023", "2025"]
    matplotlib.pyplot.close(fig)
