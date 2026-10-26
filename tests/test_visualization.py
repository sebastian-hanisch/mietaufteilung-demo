"""Abbildungen: Aufbau, gesperrte Achsen, Werte an der Hand-Instanz."""

import pytest

import mie_constants as C
import mie_evaluation as ev
import mie_visualization as V
from conftest import vals

TRIO = vals([0, 100, 900], [0, 300, 700], [0, 0, 1000])


@pytest.fixture
def a_trio():
    return ev.analyse_values(ev.Settings(n=3), TRIO)


def locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def test_prices_figure_by_hand(a_trio):
    fig = V.build_prices(a_trio)
    bars = [t for t in fig.data if t.type == "bar"]
    assert [b.name for b in bars] == [C.RULE_SHORT[r] for r in C.RULES] and list(bars[0].x) == ["Fläche A", "Fläche B", "Fläche C"]
    assert [round(float(v)) for v in bars[2].y] == [-100, 200, 900] and [round(float(v)) for v in bars[3].y] == [0, 100, 900]
    assert [round(float(v), 1) for v in bars[0].y] == [333.3] * 3
    lines = [s for s in fig.layout.shapes if s.type == "line"]
    assert sorted(round(s.y0, 1) for s in lines) == [0.0, 333.3] and locked(fig)


def test_prices_figure_skips_a_rule_that_is_not_possible():
    a = ev.analyse(ev.Settings(**C.PRESETS["Preise ab 0 unmöglich"]))
    names = [t.name for t in V.build_prices(a).data if t.type == "bar"]
    assert C.RULE_SHORT["ohne_minus"] not in names and len(names) == len(C.RULES) - 1


def test_utilities_figure_by_hand(a_trio):
    fig = V.build_utilities(a_trio)
    bars = [t for t in fig.data if t.type == "bar"]
    assert [b.name for b in bars] == ["Mieter 1", "Mieter 2", "Mieter 3"]
    assert [round(float(v)) for v in bars[0].y][:4] == [-333, 0, 100, 0]                  # Mieter 1: gleich, Mittel, Maximin, ab 0 (die Preise der kleinsten Spanne sind nicht eindeutig)
    assert [round(float(v)) for v in bars[1].y][:4] == [-33, 167, 100, 200] and [round(float(v)) for v in bars[2].y][:4] == [667, 133, 100, 100] and locked(fig)
    assert len(bars[0].x) == len(C.RULES)


def test_utilities_figure_skips_a_rule_that_is_not_possible():
    a = ev.analyse(ev.Settings(**C.PRESETS["Preise ab 0 unmöglich"]))
    assert len(V.build_utilities(a).data[0].x) == len(C.RULES) - 1


def test_figures_have_a_color_for_every_possible_tenant():
    a = ev.analyse(ev.Settings(n=C.N_MAX, seed=3))
    assert len([t for t in V.build_utilities(a).data if t.type == "bar"]) == C.N_MAX


def rows(param, xs):
    return [{"param": param, "x": x, "rule": rule, "runs": 10, "neg": 0.3, "gain": 120.0, "spread": 400.0} for x in xs for rule in C.RULES]


def test_series_figure_has_one_line_per_rule_and_percent_or_euro_axes():
    fig = V.build_series(rows("n", (3, 4)), "neg", "Anteil")
    assert [t.name for t in fig.data] == [C.RULE_SHORT[r] for r in C.RULES] and list(fig.data[0].x) == [3, 4] and tuple(fig.layout.yaxis.range) == (0, 1.05) and locked(fig)
    euro = V.build_series(rows("k", (1, 2)), "gain", "Gewinn", percent=False)
    assert euro.layout.yaxis.range is None and euro.layout.xaxis.title.text == V.AXIS_TITLES["k"]
    models = V.build_series(rows("model", tuple(C.MODELS)), "neg", "Anteil")
    assert list(models.data[0].x) == ["Unabhängig", "Ähnlich", "Premiumfläche"]
