"""BUG-0005 — los rótulos de año de las series estacionales.

- Trimestral: DOS dígitos siempre, el legado de Treadway en GraphMaker
  (`singletrim.cpp`: `FormatFloat("00", …)`). Con el año entero se montaban en
  una trimestral de unos 25 años o más.
- Mensual: el año entero, como lo aprobó Treadway; dos dígitos sólo si se monta.
- Anual: año entero cada 20 años (fug C), lo fija test_bug_0002.
"""
import matplotlib
import pytest

matplotlib.use("Agg")

from pyfug.core import Tseries  # noqa: E402
from pyfug.graphics import plot_combined  # noqa: E402
from pyfug.graphics.base import _rotulo_estacional  # noqa: E402
import numpy as np  # noqa: E402


def _rotulos(freq, begyear, nobs, begper=1):
    rng = np.random.default_rng(0)
    y = 100 * np.exp(np.cumsum(0.02 + 0.05 * rng.standard_normal(nobs)))
    ser = Tseries(name="S", nobs=nobs, freq=freq, begyear=begyear,
                  begtime=begper, data=np.asarray(y, dtype=float))
    fig = plot_combined(ser)
    fig.canvas.draw()
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    et = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    boxes = [t.get_window_extent() for t in ax.get_xticklabels() if t.get_text()]
    matplotlib.pyplot.close(fig)
    return et, boxes


@pytest.mark.parametrize("yr, txt", [(1996, "96"), (2000, "00"), (2008, "08"),
                                     (1900, "00")])
def test_trimestral_el_ano_con_dos_digitos(yr, txt):
    assert _rotulo_estacional(yr, 4) == txt


def test_mensual_el_ano_entero():
    assert _rotulo_estacional(1996, 12) == "1996"


def test_trimestral_cada_dos_anos_y_cruzando_el_siglo():
    et, _ = _rotulos(4, 1994, 48)
    assert et[:6] == ["94", "96", "98", "00", "02", "04"], et


def test_una_mensual_que_cabe_conserva_el_ano_entero():
    """El WTI del pass-through: 2002-2019, 215 meses."""
    et, boxes = _rotulos(12, 2002, 215, begper=2)
    assert all(len(t) == 4 for t in et), et
    for a, b in zip(boxes, boxes[1:]):
        assert a.x1 < b.x0


def test_una_mensual_larga_pasa_a_dos_digitos_y_no_se_monta():
    et, boxes = _rotulos(12, 1975, 12 * 50)
    assert all(len(t) == 2 for t in et), et
    for a, b in zip(boxes, boxes[1:]):
        assert a.x1 < b.x0


def test_una_trimestral_de_31_anos_no_monta_los_rotulos():
    """El caso que lo destapó: 1995-2025, 120 trimestres."""
    _, boxes = _rotulos(4, 1995, 124)
    for a, b in zip(boxes, boxes[1:]):
        assert a.x1 < b.x0, "dos rótulos de año se solapan"


# ── BUG-0006: la alineación de fug C, que corrigió Treadway ──────────────

def test_el_primer_rotulo_es_el_ano_de_comienzo_aunque_sea_impar():
    """C: el eje arranca en el primer período del año de comienzo y rotula
    cada 2 años desde ahí. Antes se redondeaba al año PAR anterior: una serie
    de 1995 salía con «94, 96, …»."""
    et, _ = _rotulos(4, 1995, 124, begper=2)
    assert et[:4] == ["95", "97", "99", "01"], et


def test_el_eje_empieza_en_el_ano_de_comienzo():
    rng = np.random.default_rng(0)
    y = 100 * np.exp(np.cumsum(0.02 + 0.05 * rng.standard_normal(60)))
    fig = plot_combined(Tseries(name="S", nobs=60, freq=4, begyear=1995,
                                begtime=3, data=np.asarray(y, dtype=float)))
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    assert ax.get_xlim()[0] == pytest.approx(1995.0)
    matplotlib.pyplot.close(fig)


def test_una_serie_corta_tambien_va_cada_dos_anos():
    """C no cambia de paso con series cortas; aquí se usaba 1 por debajo de 5."""
    et, _ = _rotulos(12, 2015, 48)
    assert et == ["2015", "2017"], et
