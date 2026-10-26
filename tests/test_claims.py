"""Befunde der README als feste Werte und Bänder: jede Zahl, die dort steht, ist hier an den festen Plänen der App geprüft.

Die Presets sind einzelne Instanzen und deshalb exakt (Euro auf ganze Zahlen gerundet wie in der App). Die Messreihen sind Anteile und Mediane über je 300 Instanzen mit festen Zufalls-Seeds
(die Standardabweichung eines Anteils liegt bei höchstens 3 Prozentpunkten): Bänder von ±8 Prozentpunkten bei Anteilen, ±12 % (mindestens 12 €) bei Medianen, Nullen und Hundert-Prozent-Aussagen exakt.
"""

import pytest

import mie_constants as C
import mie_evaluation as ev

SHARE = 0.08


def at(preset):
    return ev.analyse(ev.Settings(**C.PRESETS[preset]))


def eur0(x):
    return ev.eur(x)


def near(x, want):
    return x == pytest.approx(want, abs=max(12.0, 0.12 * abs(want)))


# --- Presets ---------------------------------------------------------------------------------------------------------------------------------

def test_default_preset():
    a = at("Vier Mieter")
    g, mi = a.outcomes["gleich"], a.outcomes["maximin"]
    assert (eur0(g.envy), eur0(g.min_utility), g.envy_pair) == ("110 €", "76 €", (0, 1)) and a.sigma == (2, 1, 0, 3)
    assert eur0(mi.min_utility) == "186 €" and not mi.has_negative and [round(p) for p in mi.prices] == [434, 245, 135, 186]
    assert a.outcomes["mittel"].envy_pair == (1, 3) and eur0(a.outcomes["mittel"].envy) == "60 €"


def test_negative_prices_preset():
    a = at("Negative Preise")
    g, mi, ne = a.outcomes["gleich"], a.outcomes["maximin"], a.outcomes["ohne_minus"]
    assert (eur0(g.envy), eur0(g.min_utility)) == ("432 €", "−221 €") and [round(p) for p in mi.prices] == [-111, 698, 335, 78]
    assert (eur0(mi.min_utility), eur0(ne.min_utility)) == ("140 €", "29 €") and mi.has_negative and not ne.has_negative


def test_preset_where_prices_from_zero_are_impossible():
    a = at("Preise ab 0 unmöglich")
    assert a.outcomes["ohne_minus"] is None and a.outcomes["maximin"].has_negative and a.outcomes["maximin"].envy_free
    assert eur0(a.outcomes["gleich"].envy) == "602 €" and ev.verdict_state(a)[1].endswith("gibt es hier keine neidfreie Aufteilung.")


def test_premium_preset():
    a = at("Sechs Mieter, eine Premiumfläche")
    g, mi = a.outcomes["gleich"], a.outcomes["maximin"]
    assert (eur0(g.envy), eur0(g.min_utility), eur0(mi.min_utility)) == ("319 €", "−32 €", "42 €") and not mi.has_negative and a.outcomes["ohne_minus"].min_utility == pytest.approx(mi.min_utility)


def test_unequal_valuations_preset():
    a = at("Sehr ungleiche Bewertungen")
    mi, ne = a.outcomes["maximin"], a.outcomes["ohne_minus"]
    assert (eur0(mi.spread), eur0(mi.min_utility), eur0(ne.min_utility)) == ("775 €", "529 €", "206 €") and mi.has_negative and eur0(a.outcomes["gleich"].envy) == "586 €"


def test_the_presets_tell_the_stories_in_their_help_texts():
    for name, needle in (("Vier Mieter", "110 €"), ("Negative Preise", "432 €"), ("Negative Preise", "140 € gegen 29 €"), ("Sechs Mieter, eine Premiumfläche", "319 €"), ("Sehr ungleiche Bewertungen", "775 €")):
        assert needle in C.PRESET_HELP[name], (name, needle)


# --- Reihen ----------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def models():
    return ev.series_models()


@pytest.fixture(scope="module")
def tenants():
    return ev.series_tenants()


@pytest.fixture(scope="module")
def inequality():
    return ev.series_inequality()


def cell(rows, x, rule, key):
    return ev.cell_of(rows, x, rule)[key]


def test_the_envy_free_rules_are_envy_free_in_every_instance(models, tenants, inequality):
    for rows in (models, tenants, inequality):
        for r in rows:
            if r["rule"] in ("maximin", "spanne"):
                assert r["ef"] == 1.0 and r["infeasible"] == 0.0 and r["envy"] == 0.0, (r["param"], r["x"], r["rule"])
            if r["rule"] == "ohne_minus":
                assert r["ef"] == pytest.approx(1.0 - r["infeasible"]), (r["param"], r["x"])


def test_equal_split_and_mean_prices_are_rarely_envy_free(models, tenants):
    assert cell(models, "unabhaengig", "gleich", "ef") == pytest.approx(0.10, abs=SHARE) and cell(models, "aehnlich", "gleich", "ef") == 0.0 and cell(models, "premium", "gleich", "ef") == 0.0
    assert cell(models, "unabhaengig", "mittel", "ef") == pytest.approx(0.31, abs=SHARE) and cell(models, "aehnlich", "mittel", "ef") == pytest.approx(0.05, abs=SHARE)
    assert [cell(tenants, n, "gleich", "ef") for n in C.SERIES_NS] == pytest.approx([0.23, 0.10, 0.03, 0.02, 0.01], abs=SHARE)
    assert [cell(tenants, n, "mittel", "ef") for n in C.SERIES_NS] == pytest.approx([0.59, 0.31, 0.17, 0.06, 0.03], abs=SHARE)


def test_how_large_the_envy_of_the_equal_split_is(models, inequality):
    assert near(cell(models, "unabhaengig", "gleich", "envy"), 188) and near(cell(models, "aehnlich", "gleich", "envy"), 491) and near(cell(models, "premium", "gleich", "envy"), 438)
    assert [round(cell(inequality, k, "gleich", "envy") / 10) for k in C.SERIES_KS] == pytest.approx([9, 19, 30, 38, 48, 54], abs=4)
    assert near(cell(models, "unabhaengig", "mittel", "envy"), 43)
    assert cell(models, "premium", "mittel", "ef") == pytest.approx(0.19, abs=SHARE)


def test_negative_prices_by_model_tenants_and_inequality(models, tenants, inequality):
    assert cell(models, "unabhaengig", "maximin", "neg") == pytest.approx(0.35, abs=SHARE) and cell(models, "aehnlich", "maximin", "neg") == pytest.approx(0.51, abs=SHARE)
    assert cell(models, "premium", "maximin", "neg") == 0.0 and cell(models, "premium", "spanne", "neg") == 0.0
    assert cell(models, "unabhaengig", "spanne", "neg") == pytest.approx(0.12, abs=SHARE) and cell(models, "aehnlich", "spanne", "neg") == pytest.approx(0.37, abs=SHARE)
    assert [cell(tenants, n, "maximin", "neg") for n in C.SERIES_NS] == pytest.approx([0.23, 0.35, 0.45, 0.48, 0.49], abs=SHARE)
    assert [cell(inequality, k, "maximin", "neg") for k in C.SERIES_KS] == pytest.approx([0.04, 0.35, 0.61, 0.75, 0.80, 0.84], abs=SHARE)
    assert [cell(inequality, k, "spanne", "neg") for k in C.SERIES_KS] == pytest.approx([0.0, 0.12, 0.30, 0.47, 0.56, 0.61], abs=SHARE)


def test_prices_from_zero_are_sometimes_impossible(models, tenants, inequality):
    assert cell(models, "aehnlich", "ohne_minus", "infeasible") == pytest.approx(0.19, abs=SHARE) and cell(models, "unabhaengig", "ohne_minus", "infeasible") <= 0.05 and cell(models, "premium", "ohne_minus", "infeasible") == 0.0
    assert [cell(tenants, n, "ohne_minus", "infeasible") for n in C.SERIES_NS] == pytest.approx([0.0, 0.01, 0.04, 0.06, 0.05], abs=0.05)
    assert [cell(inequality, k, "ohne_minus", "infeasible") for k in C.SERIES_KS] == pytest.approx([0.0, 0.01, 0.05, 0.06, 0.09, 0.09], abs=0.05)


def test_the_maximin_prices_gain_min_utility_over_the_equal_split(models, tenants, inequality):
    assert near(cell(models, "unabhaengig", "maximin", "gain"), 187) and near(cell(models, "aehnlich", "maximin", "gain"), 250) and near(cell(models, "premium", "maximin", "gain"), 139)
    assert all(cell(inequality, k, "maximin", "gain_pos") >= 0.98 for k in C.SERIES_KS) and all(cell(tenants, n, "maximin", "gain_pos") >= 0.98 for n in C.SERIES_NS)
    assert cell(models, "unabhaengig", "maximin", "gain_pos") >= 0.99 and cell(models, "aehnlich", "maximin", "gain_pos") >= 0.99 and cell(models, "premium", "maximin", "gain_pos") == 1.0
    assert [round(cell(tenants, n, "maximin", "gain")) for n in C.SERIES_NS] == pytest.approx([216, 187, 177, 145, 123], abs=25)
    assert [round(cell(inequality, k, "maximin", "gain")) for k in C.SERIES_KS] == pytest.approx([99, 187, 271, 327, 378, 415], abs=45)


def test_smallest_spread_prices_do_not_always_beat_the_equal_split_in_min_utility(models, inequality):
    assert cell(models, "unabhaengig", "spanne", "gain_pos") == pytest.approx(0.82, abs=SHARE) and cell(models, "aehnlich", "spanne", "gain_pos") >= 0.99
    assert cell(inequality, 1, "spanne", "gain_pos") == pytest.approx(0.77, abs=SHARE)


def test_price_spread_grows_with_inequality_and_shrinks_with_more_tenants(tenants, inequality):
    assert [round(cell(inequality, k, "maximin", "spread") / 10) for k in C.SERIES_KS] == pytest.approx([24, 45, 60, 70, 77, 83], abs=8)
    assert [round(cell(tenants, n, "maximin", "spread") / 10) for n in C.SERIES_NS] == pytest.approx([46, 45, 42, 37, 31], abs=6)
    assert near(cell(inequality, 2, "spanne", "spread"), 202) and near(cell(inequality, 6, "spanne", "spread"), 541) and near(cell(inequality, 6, "ohne_minus", "spread"), 548) and near(cell(inequality, 6, "maximin", "spread"), 831)
    assert near(cell(inequality, 2, "spanne", "min"), 89) and near(cell(inequality, 2, "maximin", "min"), 198) and near(cell(inequality, 2, "ohne_minus", "min"), 170) and near(cell(inequality, 6, "ohne_minus", "min"), 104)
    assert near(cell(inequality, 6, "maximin", "min"), 322)


def test_the_cost_of_prices_from_zero_in_min_utility(inequality):
    assert [round(cell(inequality, k, "ohne_minus", "min") / 10) for k in C.SERIES_KS] == pytest.approx([11, 17, 19, 17, 14, 10], abs=4)
    assert [round(cell(inequality, k, "maximin", "min") / 10) for k in C.SERIES_KS] == pytest.approx([12, 20, 25, 29, 31, 32], abs=4)


def test_the_series_use_the_documented_seeds():
    assert C.SERIES_SEED == 100000 and C.SERIES_RUNS == 300 and (C.SERIES_N, C.SERIES_K) == (4, 2) and C.SERIES_NS == (3, 4, 5, 6, 7) and C.SERIES_KS == (1, 2, 3, 4, 5, 6)
