"""Verdikte und Tabellen als reine Funktionen: Schwellen und jede Zahl im Text an handgesetzten Werten."""

import pytest

import mie_algorithm as A
import mie_constants as C
import mie_evaluation as ev
from conftest import vals

TRIO = vals([0, 100, 900], [0, 300, 700], [0, 0, 1000])
ZWEI = vals([700, 300], [400, 600])


@pytest.fixture
def a_trio():
    return ev.analyse_values(ev.Settings(n=3), TRIO)


def test_number_formats():
    assert ev.num(3.0) == "3,0" and ev.pct(0.333) == "33 %" and ev.pct(float("nan")) == "–" and ev.pct(None) == "–"
    assert ev.eur(1234.5) == "1.234 €" and ev.eur(-100.0) == "−100 €" and ev.eur(0.0) == "0 €" and ev.eur(333.333, 1) == "333,3 €" and ev.eur(-0.2) == "0 €"
    assert ev.tenant(0) == "Mieter 1" and ev.hall(0) == "Fläche A" and ev.hall(3) == "Fläche D"


def test_analysis_of_the_hand_instance(a_trio):
    assert a_trio.sigma == (0, 1, 2)
    assert a_trio.outcomes["maximin"].prices == pytest.approx((-100.0, 200.0, 900.0)) and a_trio.outcomes["ohne_minus"].prices == pytest.approx((0.0, 100.0, 900.0), abs=1e-6)
    assert ev.gain_over_equal(a_trio, "maximin") == pytest.approx(100.0 + 1000 / 3)                 # Mindestnutzen 100 gegen −333,3 bei gleicher Aufteilung
    assert ev.gain_over_equal(a_trio, "gleich") == 0.0


def test_rule_not_possible_is_none():
    a = ev.analyse(ev.Settings(**C.PRESETS["Preise ab 0 unmöglich"]))
    assert a.outcomes["ohne_minus"] is None and ev.gain_over_equal(a, "ohne_minus") is None


def test_value_rows_mark_the_assignment(a_trio):
    rows = ev.value_rows(a_trio)
    assert rows[0] == {"Mieter": "Mieter 1", "Fläche A": "0 ◆", "Fläche B": "100", "Fläche C": "900"}
    assert rows[2]["Fläche C"] == "1000 ◆" and rows[1]["Fläche B"] == "300 ◆" and rows[1]["Fläche A"] == "0"


def test_rule_rows_by_hand(a_trio):
    rows = {r["Regel"]: r for r in ev.rule_rows(a_trio)}
    assert list(rows) == list(C.RULES.values())
    g = rows[C.RULES["gleich"]]
    assert g["Preise"] == "333 € / 333 € / 333 €" and g["Neidfrei"] == "nein" and g["Größter Neid"] == "900 €" and g["Mindestnutzen"] == "−333 €" and g["Preisspanne"] == "0 €" and g["Negative Preise"] == "nein"
    m = rows[C.RULES["maximin"]]
    assert m["Preise"] == "−100 € / 200 € / 900 €" and m["Neidfrei"] == "ja" and m["Größter Neid"] == "–" and m["Mindestnutzen"] == "100 €" and m["Preisspanne"] == "1.000 €" and m["Negative Preise"] == "ja"
    o = rows[C.RULES["ohne_minus"]]
    assert o["Preise"] == "0 € / 100 € / 900 €" and o["Mindestnutzen"] == "0 €" and o["Negative Preise"] == "nein"


def test_rule_rows_for_a_rule_that_is_not_possible():
    a = ev.analyse(ev.Settings(**C.PRESETS["Preise ab 0 unmöglich"]))
    row = next(r for r in ev.rule_rows(a) if r["Regel"] == C.RULES["ohne_minus"])
    assert row == {"Regel": C.RULES["ohne_minus"], "Preise": "nicht möglich", "Neidfrei": "–", "Größter Neid": "–", "Mindestnutzen": "–", "Preisspanne": "–", "Negative Preise": "–"}


def test_witness_lines_by_hand(a_trio):
    lines = ev.witness_lines(a_trio)
    assert lines[0] == "**Gleich:** Mieter 1 hat Fläche A (Nutzen −333 €) und beneidet Fläche C: dort wäre sein Nutzen 567 € (Neid 900 €)."
    assert lines[1].startswith("**Mittel:** Mieter 1 hat Fläche A (Nutzen 0 €) und beneidet Fläche C: dort wäre sein Nutzen 33 € (Neid 33 €)")
    assert lines[2] == "**Neidfrei (Maximin), negative Preise:** Fläche A (−100 €); wer diese Fläche nimmt, bekommt Geld dazu; so wird der Mindestnutzen am größten (ohne negative Preise ginge es auch, dann ist der Mindestnutzen aber kleiner)."
    assert len(lines) == 3


def test_verdict_state_by_hand(a_trio):
    kind, text = ev.verdict_state(a_trio)
    assert kind == "warning"
    assert text == ("Bei gleicher Aufteilung (333,3 € je Fläche) ist der Mindestnutzen −333 € und der größte Neid 900 € (Mieter 1 beneidet Fläche C). "
                    "Hier gibt es neidfreie Preise; der größte Mindestnutzen ist 100 € (Preise von −100 € bis 900 €, Gewinn gegenüber gleich 433 €). "
                    "Bei diesem größten Mindestnutzen ist mindestens ein Preis negativ. Verlangt man Preise ab 0, sinkt der Mindestnutzen auf 0 €.")


def test_verdict_state_without_negative_prices_and_with_a_whole_euro_share():
    a = ev.analyse_values(ev.Settings(n=2), ZWEI)
    kind, text = ev.verdict_state(a)
    assert kind == "info" and text.startswith("Bei gleicher Aufteilung (500 € je Fläche) ist der Mindestnutzen 100 € und der größte Neid 0 €. ")
    assert "Hier gibt es neidfreie Preise; der größte Mindestnutzen ist 150 € (Preise von 450 € bis 550 €, Gewinn gegenüber gleich 50 €). Alle Preise sind positiv; die Bedingung „Preise ab 0“ kostet hier nichts." in text


def test_verdict_state_when_prices_from_zero_are_impossible():
    a = ev.analyse(ev.Settings(**C.PRESETS["Preise ab 0 unmöglich"]))
    kind, text = ev.verdict_state(a)
    assert kind == "warning" and text.endswith("Verlangt man Preise ab 0, gibt es hier keine neidfreie Aufteilung.")


def _rows(param, xs, **by_rule):
    rows = []
    for i, x in enumerate(xs):
        for rule in C.RULES:
            base = {"ef": 0.5, "infeasible": 0.0, "neg": 0.2, "min": 100.0, "spread": 300.0, "envy": 0.0, "gain": 50.0, "gain_pos": 0.9}
            base.update({k: v[i] for k, v in by_rule.get(rule, {}).items()})
            rows.append({"param": param, "x": x, "rule": rule, "runs": 300, **base})
    return rows


def test_series_rows_and_labels():
    rows = _rows("model", tuple(C.MODELS), maximin={"neg": [0.35, 0.51, 0.0]})
    table = ev.series_rows(rows, "neg")
    assert [r["Geschmacksmodell"] for r in table] == ["Unabhängig", "Ähnlich", "Premiumfläche"]
    assert table[0]["Neidfrei (Maximin)"] == "35 %" and table[1]["Neidfrei (Maximin)"] == "51 %" and table[2]["Neidfrei (Maximin)"] == "0 %" and table[0]["Gleich"] == "20 %"
    assert ev.series_rows(rows, "gain", ev.eur)[0]["Gleich"] == "50 €"
    assert list(ev.series_rows(_rows("n", (3,)), "ef")[0])[0] == "Mieter" and list(ev.series_rows(_rows("k", (1,)), "ef")[0])[0] == "Ungleichheit"
    assert ev.cell_of(rows, "aehnlich", "maximin")["neg"] == 0.51 and ev.x_label("n", 4) == "4" and ev.x_label("model", "premium") == "Premiumfläche"


def test_verdict_models_by_hand():
    rows = _rows("model", tuple(C.MODELS), gleich={"ef": [0.10, 0.0, 0.0]}, maximin={"neg": [0.35, 0.51, 0.0]}, ohne_minus={"infeasible": [0.01, 0.19, 0.0]})
    kind, text = ev.verdict_models(rows)
    assert kind == "info"
    assert text.startswith("Mittel über 300 Instanzen (4 Mieter, Ungleichheit 2). Unabhängig: gleiche Aufteilung neidfrei 10 %, negative Preise beim Maximin 35 %, „Preise ab 0“ nicht möglich 1 %;")
    assert "Ähnlich: gleiche Aufteilung neidfrei 0 %, negative Preise beim Maximin 51 %, „Preise ab 0“ nicht möglich 19 %" in text and text.endswith("nicht möglich 0 %.")


def test_verdict_tenants_by_hand():
    rows = _rows("n", (3, 7), maximin={"neg": [0.23, 0.49], "gain": [216.0, 123.0]}, gleich={"ef": [0.23, 0.01]})
    kind, text = ev.verdict_tenants(rows)
    assert kind == "info"
    assert text == ("Bei 3 bzw. 7 Mietern haben 23 % bzw. 49 % der neidfreien Maximin-Aufteilungen einen negativen Preis; "
                    "der Mindestnutzen steigt gegenüber der gleichen Aufteilung im Median um 216 € bzw. 123 €. Neidfrei ist die gleiche Aufteilung in 23 % bzw. 1 % der Instanzen.")


def test_verdict_inequality_by_hand():
    rows = _rows("k", (1, 6), maximin={"neg": [0.04, 0.84], "spread": [235.0, 831.0]}, ohne_minus={"infeasible": [0.0, 0.09]})
    kind, text = ev.verdict_inequality(rows)
    assert kind == "info"
    assert text == ("Bei Ungleichheit 1 bzw. 6 (4 Mieter, 300 Instanzen): negative Preise beim Maximin 4 % bzw. 84 %; „Preise ab 0“ nicht möglich 0 % bzw. 9 %; Preisspanne (Median) 235 € bzw. 831 €.")


def test_cells_are_reproducible_and_bounded():
    a = ev._cell(4, "unabhaengig", 2, runs=6, seed=7)
    assert a == ev._cell(4, "unabhaengig", 2, runs=6, seed=7) and set(a) == set(C.RULES)
    assert a["maximin"]["ef"] == 1.0 and a["gleich"]["gain"] == 0.0 and a["maximin"]["infeasible"] == 0.0 and a["maximin"]["envy"] == 0.0
    assert all(0.0 <= d[k] <= 1.0 for d in a.values() for k in ("ef", "infeasible", "neg"))


def test_gain_of_the_envy_free_rule_is_positive():
    a = ev._cell(5, "premium", 2, runs=8, seed=3)
    assert a["maximin"]["gain"] > 0 and a["maximin"]["gain_pos"] == 1.0 and A.TOL > 0
