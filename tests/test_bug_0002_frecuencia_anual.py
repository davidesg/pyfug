"""BUG-0002 — `plot_combined` se rompía en toda serie anual.

`x_pad` se asignaba sólo dentro de la rama `f > 1` del eje temporal y se
consumía después en el `set_xlim` común a las dos ramas. Con `f == 1` eso es un
`UnboundLocalError`: la figura no salía fea, no salía.

La prueba pasa las tres frecuencias por la misma puerta, y la anual va primero.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyfug.core import Tseries
from pyfug.graphics import plot_combined


def _serie(freq, nobs=40, begyear=1980):
    rng = np.random.default_rng(0)
    y = 100 * np.exp(np.cumsum(0.02 + 0.05 * rng.standard_normal(nobs)))
    return Tseries(name=f"F{freq}", nobs=nobs, freq=freq, begyear=begyear,
                   begtime=1, data=np.asarray(y, dtype=float))


@pytest.mark.parametrize("freq", [1, 4, 12])
def test_la_figura_combinada_sale_en_las_tres_frecuencias(freq):
    fig = plot_combined(_serie(freq))
    assert fig is not None
    assert fig.axes, "la figura salió sin ejes"
    matplotlib.pyplot.close(fig)


def test_el_eje_de_la_anual_tiene_limites_finitos():
    """El síntoma concreto: `set_xlim` consumía una variable sin asignar. Si
    alguien vuelve a dejarla suelta, esto lo caza aunque no lance."""
    fig = plot_combined(_serie(1, nobs=60))
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    x0, x1 = ax.get_xlim()
    assert np.isfinite(x0) and np.isfinite(x1)
    assert x1 > x0
    matplotlib.pyplot.close(fig)


# ────────── el convenio de fug C, no un parche ──────────
#
#   fug.c:332          ornsop  = nrdiff + freq*nadiff
#   fug.c:382          timeout = ornsop + ser->outyear        (sólo f == 1)
#   fug.c:404          ... , ser->begyear - ser->outyear , ...
#   gnuplot_i.c:1275   plot [-timeout : n-1][-AbsMax : AbsMax]
#   gnuplot_graphics.c:493-517   líneas y rótulos en -tmornsop + 2*f*i*10,
#                                o sea CADA 20 AÑOS con f == 1

def _eje(ser):
    fig = plot_combined(ser)
    fig.canvas.draw()
    ax = max(fig.axes, key=lambda a: a.get_position().width)
    et = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    lim = ax.get_xlim()
    matplotlib.pyplot.close(fig)
    return et, lim


def test_los_rotulos_anuales_van_cada_VEINTE_anos():
    """C: `2*f*i*10` con f=1. El primer arreglo puso 10, que no es el convenio."""
    et, _ = _eje(_serie(1, nobs=120, begyear=1900))
    assert et == ['1900', '1920', '1940', '1960', '1980', '2000'], et


def test_el_primer_rotulo_es_begyear_y_no_un_multiplo_redondeado():
    """C rotula desde `tsby` (i = 0), no desde el múltiplo del paso que quede
    por debajo. Redondear hacia abajo es lo que pone un año ANTERIOR al primer
    dato en el eje."""
    et, lim = _eje(_serie(1, nobs=40, begyear=1987))
    assert et[0] == '1987', et
    assert lim[0] == pytest.approx(1987.0), lim


def test_outyear_es_el_margen_izquierdo_y_corre_los_rotulos():
    """`outyear` —«year before graph (only yearly data)», fug.h:58— es una
    propiedad DECLARADA de la serie, no un pad cosmético. `pyfug` la llevaba en
    el `Tseries` y `plot_combined` la ignoraba.

    C la usa dos veces: alarga el eje por la izquierda (`timeout = ornsop +
    outyear`) y corre el origen de los rótulos (`begyear - outyear`).
    """
    s = _serie(1, nobs=40, begyear=1980)
    s.outyear = 5
    et, lim = _eje(s)
    assert et[0] == '1975', et
    assert lim[0] == pytest.approx(1975.0), lim
    # y sin `outyear` el eje arranca en el primer dato
    et0, lim0 = _eje(_serie(1, nobs=40, begyear=1980))
    assert et0[0] == '1980'
    assert lim0[0] == pytest.approx(1980.0)


def test_las_mensuales_y_trimestrales_no_se_tocan():
    """El convenio anual es OTRO. Las de f>1 siguen con su paso de 2 años, que
    es lo que BUG-0001 discute — y este arreglo no entra ahí."""
    for freq in (4, 12):
        et, _ = _eje(_serie(freq, nobs=80, begyear=2000))
        años = [int(x) for x in et]
        pasos = {b - a for a, b in zip(años, años[1:])}
        assert pasos <= {2}, (freq, et)
