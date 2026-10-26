"""Randfälle: Extremwerte der Regler, Invarianten jeder Aufteilung, entartete Bewertungen."""

import numpy as np
import pytest

import mie_algorithm as A
import mie_constants as C
import mie_evaluation as ev
import mie_scenario as S
from conftest import vals

EXTREMES = [(n, model, k) for n in (C.N_MIN, 5, C.N_MAX) for model in C.MODELS for k in (C.K_MIN, C.K_MAX)]


@pytest.mark.parametrize("n,model,k", EXTREMES)
def test_invariants_at_the_extremes(n, model, k):
    a = ev.analyse(ev.Settings(n=n, model=model, k=k, seed=2))
    assert a.values.shape == (n, n) and (a.values.sum(axis=1) == C.RENT).all() and (a.values >= 0).all() and sorted(a.sigma) == list(range(n))
    for rule, o in a.outcomes.items():
        if o is None:
            assert rule == "ohne_minus"
            continue
        assert sum(o.prices) == pytest.approx(C.RENT, abs=1e-5), rule
        assert o.min_utility == pytest.approx(min(o.utilities)) and o.spread == pytest.approx(max(o.prices) - min(o.prices))
        assert o.envy >= 0.0 and (o.envy_pair is None) == (o.envy == 0.0) and o.envy_free == (o.envy_pair is None)
        assert sum(o.utilities) == pytest.approx(sum(int(a.values[i, a.sigma[i]]) for i in range(n)) - C.RENT, abs=1e-5)         # die Summe der Nutzen ist fest
    for rule in ("maximin", "spanne"):
        assert a.outcomes[rule].envy_free
    assert a.outcomes["ohne_minus"] is None or (a.outcomes["ohne_minus"].envy_free and not a.outcomes["ohne_minus"].has_negative)
    assert a.outcomes["maximin"].min_utility >= a.outcomes["spanne"].min_utility - 1e-6
    if a.outcomes["ohne_minus"] is not None:
        assert a.outcomes["maximin"].min_utility >= a.outcomes["ohne_minus"].min_utility - 1e-6
    kind, text = ev.verdict_state(a)
    assert kind in ("warning", "info") and text
    assert len(ev.rule_rows(a)) == len(C.RULES) and len(ev.value_rows(a)) == n
    ev.witness_lines(a)


def test_round_to_total_is_exact_and_deterministic():
    assert S.round_to_total(np.array([1.0, 1.0, 1.0]), 1000).tolist() == [334, 333, 333]            # der Rest geht an den kleinsten Index
    assert S.round_to_total(np.array([3.0, 1.0]), 100).tolist() == [75, 25]
    assert S.round_to_total(np.array([1e-9, 1.0]), 10).tolist() == [0, 10]
    for seed in range(20):
        w = np.random.default_rng(seed).random(7) + 0.01
        assert S.round_to_total(w, 1000).sum() == 1000


def test_models_are_functions_of_their_seed_and_differ():
    for model in C.MODELS:
        a, b = S.make_values(5, model, 3, 11), S.make_values(5, model, 3, 11)
        assert (a == b).all() and not (a == S.make_values(5, model, 3, 12)).all()
    with pytest.raises(ValueError):
        S.make_values(4, "x", 2, 1)


def test_models_have_their_signature():
    ahnlich = np.mean([S.make_values(6, "aehnlich", 2, s).std(axis=0).mean() for s in range(30)])
    unabh = np.mean([S.make_values(6, "unabhaengig", 2, s).std(axis=0).mean() for s in range(30)])
    assert ahnlich < unabh                                                                           # ähnliche Geschmäcker: die Mieter bewerten dieselbe Fläche ähnlich
    prem = S.make_values(6, "premium", 2, 4)
    top = int(np.argmax(prem.mean(axis=0)))
    assert (prem.argmax(axis=1) == top).all()                                                        # alle Mieter bewerten dieselbe Fläche am höchsten
    flat = np.mean([S.make_values(6, "unabhaengig", 1, s).max(axis=1).mean() for s in range(30)])
    skew = np.mean([S.make_values(6, "unabhaengig", 7, s).max(axis=1).mean() for s in range(30)])
    assert skew > flat                                                                               # größere Ungleichheit: der höchste Wert je Mieter wächst


def test_ties_in_the_assignment_do_not_change_the_maximin_value():
    v = vals([500, 500, 0], [500, 500, 0], [0, 0, 1000])                                              # zwei gleichwertige Zuordnungen für die ersten beiden Mieter
    s = A.assignment(v)
    t = (1, 0, 2) if s[:2] == (0, 1) else (0, 1, 2)
    a, b = A.evaluate(v, s, A.lp_maximin(v, s)), A.evaluate(v, t, A.lp_maximin(v, t))
    assert a.min_utility == pytest.approx(b.min_utility) and a.envy_free and b.envy_free


def test_two_tenants_have_a_range_of_envy_free_prices():
    v = vals([700, 300], [400, 600])
    for rule in ("maximin", "spanne", "ohne_minus"):
        o = A.evaluate(v, (0, 1), A.prices_for(rule, v, (0, 1)))
        assert o.envy_free and sum(o.prices) == pytest.approx(1000.0)


def test_a_tenant_who_values_everything_equally_is_never_envious():
    v = vals([250, 250, 250, 250], [700, 100, 100, 100], [100, 700, 100, 100], [100, 100, 700, 100])
    sigma = A.assignment(v)
    o = A.evaluate(v, sigma, A.prices_for("maximin", v, sigma))
    assert o.envy_free and o.min_utility >= 0.0
