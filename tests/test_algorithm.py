"""Kern von Hand: Zuordnung, Preisregeln, Neid und Kennzahlen an Mini-Instanzen, mit der Rechnung im Kommentar."""

import numpy as np
import pytest

import mie_algorithm as A
from conftest import vals

ZWEI = vals([700, 300], [400, 600])
TRIO = vals([0, 100, 900], [0, 300, 700], [0, 0, 1000])


def test_assignment_by_hand(drei):
    assert A.assignment(drei) == (0, 1, 2)                          # Diagonale: 600 + 500 + 700 = 1800
    assert A.assignment(vals([300, 700], [600, 400])) == (1, 0)     # getauscht: 700 + 600 = 1300 gegen 300 + 400 = 700
    assert A.assignment(TRIO) == (0, 1, 2)                          # 0 + 300 + 1000 = 1300 gegen 1200, 1100, ...


def test_two_by_two_all_rules_by_hand():
    # Preise pA + pB = 1000. Mieter 1: pA − pB ≤ 700 − 300 = 400; Mieter 2: pB − pA ≤ 600 − 400 = 200. Mit d = pA − pB: −200 ≤ d ≤ 400.
    # Nutzen: u1 = 700 − pA = 200 − d/2, u2 = 600 − pB = 100 + d/2. Gleich bei d = 100: u = 150, Preise (550, 450). Kleinste Spanne: d = 0, Preise (500, 500).
    sigma = A.assignment(ZWEI)
    assert sigma == (0, 1)
    assert A.prices_for("gleich", ZWEI, sigma).tolist() == [500.0, 500.0]
    assert A.prices_for("mittel", ZWEI, sigma).tolist() == [550.0, 450.0]            # (700 + 400) / 2, (300 + 600) / 2
    assert A.prices_for("maximin", ZWEI, sigma) == pytest.approx([550.0, 450.0])
    assert A.prices_for("ohne_minus", ZWEI, sigma) == pytest.approx([550.0, 450.0])
    assert A.prices_for("spanne", ZWEI, sigma) == pytest.approx([500.0, 500.0], abs=1e-6)


def test_two_by_two_outcomes_by_hand():
    sigma = (0, 1)
    eq = A.evaluate(ZWEI, sigma, [500.0, 500.0])
    assert eq.utilities == (200.0, 100.0) and eq.min_utility == 100.0 and eq.envy_free and eq.envy == 0.0 and eq.spread == 0.0 and not eq.has_negative
    mx = A.evaluate(ZWEI, sigma, [550.0, 450.0])
    assert mx.utilities == (150.0, 150.0) and mx.min_utility == 150.0 and mx.envy_free and mx.spread == 100.0


def test_equal_split_envy_by_hand():
    # Mieter 1 hat A (Nutzen 700 − 400 = 300), B bei Preis 600 brächte 300 − 600 < 0: kein Neid. Bei den Preisen (400, 600): Mieter 2 hat B (600 − 600 = 0), A bei Preis 400 brächte 400 − 400 = 0: kein Neid (Gleichheit).
    assert A.max_envy(ZWEI, (0, 1), [400.0, 600.0]) == (0.0, None)
    # Preise (300, 700): Mieter 2 hat B (600 − 700 = −100), A bei 300 brächte 400 − 300 = 100: Neid 200
    envy, pair = A.max_envy(ZWEI, (0, 1), [300.0, 700.0])
    assert envy == pytest.approx(200.0) and pair == (1, 0)


def test_trio_maximin_by_hand():
    # Alle wollen C. Neidfrei mit u1 = u2 = u3 = 100: Preise = Bewertung der eigenen Fläche − 100 = (−100, 200, 900): Summe 1000. Es ist die einzige Lösung (die Summe der Nutzen ist 1300 − 1000 = 300).
    sigma = A.assignment(TRIO)
    p = A.prices_for("maximin", TRIO, sigma)
    assert p == pytest.approx([-100.0, 200.0, 900.0])
    o = A.evaluate(TRIO, sigma, p)
    assert o.utilities == pytest.approx((100.0, 100.0, 100.0)) and o.min_utility == pytest.approx(100.0) and o.envy_free and o.has_negative


def test_trio_without_negative_prices_by_hand():
    # pA ≥ 0 heißt u1 = −pA ≤ 0, also Mindestnutzen höchstens 0. Mit pA = 0 folgt aus Mieter 1: pB ≥ 100, pC ≥ 900 und damit pB = 100, pC = 900 (Summe 1000).
    sigma = A.assignment(TRIO)
    p = A.prices_for("ohne_minus", TRIO, sigma)
    assert p == pytest.approx([0.0, 100.0, 900.0], abs=1e-6)
    o = A.evaluate(TRIO, sigma, p)
    assert o.utilities == pytest.approx((0.0, 200.0, 100.0)) and o.min_utility == pytest.approx(0.0, abs=1e-6) and o.envy_free and not o.has_negative


def test_trio_smallest_spread_by_hand():
    # Aus Mieter 1: pC ≥ pA + 900, also Spanne ≥ 900; erreicht zum Beispiel bei (0, 100, 900). Die Lösung ist nicht eindeutig (pA zwischen −66,7 und 0), die Spanne schon.
    sigma = A.assignment(TRIO)
    p = A.prices_for("spanne", TRIO, sigma)
    o = A.evaluate(TRIO, sigma, p)
    assert o.spread == pytest.approx(900.0, abs=1e-6) and o.envy_free and p.sum() == pytest.approx(1000.0)


def test_trio_equal_split_and_mean_by_hand():
    sigma = (0, 1, 2)
    g = A.evaluate(TRIO, sigma, A.equal_prices(3))
    # Mieter 1 hat A (0 − 333,3 = −333,3); C zu 333,3 brächte 900 − 333,3 = 566,7: Neid 900
    assert g.envy == pytest.approx(900.0) and g.envy_pair == (0, 2) and g.min_utility == pytest.approx(-1000 / 3)
    m = A.evaluate(TRIO, sigma, A.mean_prices(TRIO))
    # Preise (0, 133,3, 866,7): Mieter 1 hat u = 0, C brächte 900 − 866,7 = 33,3: Neid 33,3
    assert m.envy == pytest.approx(100 / 3) and m.envy_pair == (0, 2)


def test_mean_and_equal_prices_sum_to_the_rent(drei):
    assert A.equal_prices(4).tolist() == [250.0] * 4 and A.mean_prices(drei).sum() == pytest.approx(1000.0)
    assert A.mean_prices(drei).tolist() == pytest.approx([300.0, 1000 / 3, 1100 / 3])                  # Spaltenmittel: (600+200+100)/3, (300+500+200)/3, (100+300+700)/3


def test_unknown_rule_raises(drei):
    with pytest.raises(ValueError):
        A.prices_for("x", drei, (0, 1, 2))


def test_all_equal_valuations_every_envy_free_rule_gives_the_equal_split():
    v = vals([250, 250, 250, 250]).repeat(4, axis=0)
    sigma = A.assignment(v)
    for rule in ("gleich", "mittel", "maximin", "ohne_minus", "spanne"):
        p = A.prices_for(rule, v, sigma)
        assert p == pytest.approx([250.0] * 4, abs=1e-6), rule
        o = A.evaluate(v, sigma, p)
        assert o.envy_free and o.min_utility == pytest.approx(0.0, abs=1e-6) and o.spread == pytest.approx(0.0, abs=1e-6)


def test_everyone_wants_the_same_hall_only_one_price_is_positive():
    # alle Zeilen [1000, 0, 0]: nur Fläche A hat Wert. Neidfrei geht nur mit pA = 1000 und pB = pC = 0 (Mieter ohne A dürfen A zu keinem Preis unter 1000 vorziehen)
    v = vals([1000, 0, 0], [1000, 0, 0], [1000, 0, 0])
    sigma = A.assignment(v)
    for rule in ("maximin", "ohne_minus", "spanne"):
        assert A.prices_for(rule, v, sigma) == pytest.approx([1000.0, 0.0, 0.0], abs=1e-6), rule
    g = A.evaluate(v, sigma, A.equal_prices(3))
    assert g.envy == pytest.approx(1000.0) and not g.envy_free


def test_evaluate_flags_negative_prices_only_below_the_tolerance():
    sigma = (0, 1)
    assert A.evaluate(ZWEI, sigma, [-1e-9, 1000.0]).has_negative is False
    assert A.evaluate(ZWEI, sigma, [-1.0, 1001.0]).has_negative is True


def test_outcome_fields():
    o = A.evaluate(ZWEI, (0, 1), [600.0, 400.0])
    assert o.prices == (600.0, 400.0) and o.spread == 200.0 and isinstance(o.utilities, tuple)
    # Mieter 1: 700 − 600 = 100; Mieter 2: 600 − 400 = 200; Mieter 1 beneidet B nicht (300 − 400 < 100); Mieter 2 beneidet A (400 − 600 < 200 nein)
    assert o.utilities == (100.0, 200.0) and o.envy_free


def test_utilities_helper(drei):
    u = A.utilities(drei, (0, 1, 2), [300.0, 300.0, 400.0])
    assert u.tolist() == [300.0, 200.0, 300.0]


def test_max_envy_reports_the_first_pair_on_a_tie():
    # drei Mieter mit gleichen Bewertungen (400, 300, 300), alle Preise 0, Zuordnung Diagonale: Mieter 2 und Mieter 3 beneiden Fläche A um je 100 € -> das erste Paar (Mieter 2, Fläche A)
    v = vals([400, 300, 300], [400, 300, 300], [400, 300, 300])
    envy, pair = A.max_envy(v, (0, 1, 2), [0.0, 0.0, 0.0])
    assert envy == 100.0 and pair == (1, 0)
