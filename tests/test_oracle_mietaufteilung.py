"""Orakel-Test mietaufteilung-demo: jede Preisregel gegen einen ANDEREN Rechenweg.

* Zuordnung: Aufzählung aller Permutationen (statt Ungarischer Methode); jede Zuordnung mit größter Summe liefert dieselben neidfreien Preise (Wert des Maximin).
* Maximin, Maximin ab 0 und kleinste Spanne: **exakte Rechnung mit Brüchen**, die alle Ecken des Preisvielecks aufzählt (statt des Simplex-Lösers HiGHS); bei drei Mietern 4 bis 5 Variablen.
* Neidfreiheit: die Definition wörtlich (kein Mieter hat eine Fläche mit höherem Nutzen zu deren Preis).
* Gleiche Preise und Mittel der Bewertungen: Summen und Einzelwerte aus der Definition.
"""

import itertools
from fractions import Fraction

import numpy as np
import pytest

import mie_algorithm as A
import mie_constants as C
import mie_scenario as S


def solve_square(matrix, rhs):
    """Gauß-Elimination mit Brüchen; None, wenn die Matrix singulär ist."""
    n = len(matrix)
    m = [list(map(Fraction, row)) + [Fraction(r)] for row, r in zip(matrix, rhs)]
    for col in range(n):
        piv = next((r for r in range(col, n) if m[r][col] != 0), None)
        if piv is None:
            return None
        m[col], m[piv] = m[piv], m[col]
        m[col] = [x / m[col][col] for x in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col]
                m[r] = [a - f * b for a, b in zip(m[r], m[col])]
    return [m[r][n] for r in range(n)]


def exact_lp(c, a_ub, b_ub, a_eq, b_eq):
    """Größter Zielwert c·x über die Ecken des Vielecks {A_ub x ≤ b_ub, A_eq x = b_eq}; None, wenn es keine Ecke gibt. Voraussetzung: der Zielwert ist beschränkt und das Vieleck hat Ecken."""
    nv = len(c)
    need = nv - len(a_eq)
    best = None
    for active in itertools.combinations(range(len(a_ub)), need):
        matrix = [list(a_eq[i]) for i in range(len(a_eq))] + [list(a_ub[i]) for i in active]
        rhs = list(b_eq) + [b_ub[i] for i in active]
        x = solve_square(matrix, rhs)
        if x is None:
            continue
        if any(sum(Fraction(a) * xi for a, xi in zip(row, x)) > b for row, b in zip(a_ub, b_ub)):
            continue
        value = sum(Fraction(ci) * xi for ci, xi in zip(c, x))
        if best is None or value > best[0]:
            best = (value, x)
    return best


def envy_rows(values, sigma, nv):
    rows, rhs = [], []
    n = len(sigma)
    for i in range(n):
        s = sigma[i]
        for j in range(n):
            if j != s:
                row = [0] * nv
                row[s], row[j] = 1, -1
                rows.append(row)
                rhs.append(int(values[i][s] - values[i][j]))
    return rows, rhs


def exact_maximin(values, sigma, nonneg=False, rent=C.RENT, second=True):
    """(t*, kleinste Spanne unter den Preisen mit Mindestnutzen t*) exakt; None, wenn es keine neidfreien Preise gibt (nur mit nonneg)."""
    n = len(sigma)
    a_ub, b_ub = envy_rows(values, sigma, n + 1)
    for i in range(n):
        row = [0] * (n + 1)
        row[sigma[i]], row[n] = 1, 1
        a_ub.append(row)
        b_ub.append(int(values[i][sigma[i]]))
    if nonneg:
        for j in range(n):
            row = [0] * (n + 1)
            row[j] = -1
            a_ub.append(row)
            b_ub.append(0)
    first = exact_lp([0] * n + [1], a_ub, b_ub, [[1] * n + [0]], [rent])
    if first is None:
        return None
    t_star = first[0]
    if not second:
        return t_star, None
    a2, b2 = envy_rows(values, sigma, n + 2)
    for i in range(n):
        row = [0] * (n + 2)
        row[sigma[i]] = 1
        a2.append(row)
        b2.append(Fraction(int(values[i][sigma[i]])) - t_star)
    for j in range(n):
        up, low = [0] * (n + 2), [0] * (n + 2)
        up[j], up[n] = 1, -1
        low[j], low[n + 1] = -1, 1
        a2 += [up, low]
        b2 += [0, 0]
    if nonneg:
        for j in range(n):
            row = [0] * (n + 2)
            row[j] = -1
            a2.append(row)
            b2.append(0)
    second = exact_lp([0] * n + [-1, 1], a2, b2, [[1] * n + [0, 0]], [rent])
    return t_star, -second[0]


def exact_min_spread(values, sigma, rent=C.RENT):
    n = len(sigma)
    a_ub, b_ub = envy_rows(values, sigma, n + 2)
    for j in range(n):
        up, low = [0] * (n + 2), [0] * (n + 2)
        up[j], up[n] = 1, -1
        low[j], low[n + 1] = -1, 1
        a_ub += [up, low]
        b_ub += [0, 0]
    best = exact_lp([0] * n + [-1, 1], a_ub, b_ub, [[1] * n + [0, 0]], [rent])
    return -best[0]


def instance(seed, n=3):
    rng = np.random.default_rng(seed)
    model = list(C.MODELS)[seed % 3]
    return S.make_values(n, model, int(rng.integers(1, 7)), seed)


# --- Zuordnung -------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(80))
def test_assignment_maximizes_the_sum_over_all_permutations(seed):
    n = 3 + seed % 4
    v = instance(seed, n)
    sigma = A.assignment(v)
    best = max(sum(int(v[i][p[i]]) for i in range(n)) for p in itertools.permutations(range(n)))
    assert sum(int(v[i][sigma[i]]) for i in range(n)) == best and sorted(sigma) == list(range(n))


@pytest.mark.parametrize("seed", range(40))
def test_every_optimal_assignment_gives_the_same_maximin_value(seed):
    n = 3 + seed % 2
    v = instance(seed, n)
    best = max(sum(int(v[i][p[i]]) for i in range(n)) for p in itertools.permutations(range(n)))
    values = []
    for p in itertools.permutations(range(n)):
        if sum(int(v[i][p[i]]) for i in range(n)) == best:
            prices = A.lp_maximin(v, p)
            values.append(A.evaluate(v, p, prices).min_utility)
    assert max(values) - min(values) < 1e-6


# --- Neidfreiheit nach der Definition --------------------------------------------------------------------------------------------------------

def naive_envy_free(values, sigma, prices, tol=1e-6):
    n = len(sigma)
    for i in range(n):
        mine = values[i][sigma[i]] - prices[sigma[i]]
        if any(values[i][j] - prices[j] > mine + tol for j in range(n)):
            return False
    return True


@pytest.mark.parametrize("seed", range(120))
def test_envy_free_rules_are_envy_free_and_sum_to_the_rent(seed):
    n = 3 + seed % 5
    v = instance(seed, n)
    sigma = A.assignment(v)
    for rule in ("maximin", "ohne_minus", "spanne"):
        p = A.prices_for(rule, v, sigma)
        if p is None:
            assert rule == "ohne_minus"
            continue
        assert naive_envy_free(v, sigma, p), (seed, rule)
        assert p.sum() == pytest.approx(C.RENT, abs=1e-6)
        if rule == "ohne_minus":
            assert p.min() >= -1e-7
    assert A.evaluate(v, sigma, A.prices_for("maximin", v, sigma)).envy_free


@pytest.mark.parametrize("seed", range(120))
def test_max_envy_matches_the_definition(seed):
    n = 3 + seed % 4
    v = instance(seed, n)
    sigma = A.assignment(v)
    rng = np.random.default_rng(700 + seed)
    for _ in range(4):
        raw = rng.random(n) + 0.1
        p = C.RENT * raw / raw.sum()
        envy, pair = A.max_envy(v, sigma, p)
        want = max(max(v[i][j] - p[j] - (v[i][sigma[i]] - p[sigma[i]]) for j in range(n) if j != sigma[i]) for i in range(n))
        assert envy == pytest.approx(max(want, 0.0), abs=1e-9)
        assert (pair is None) == (want <= A.TOL)
        if pair is not None:
            i, j = pair
            assert v[i][j] - p[j] - (v[i][sigma[i]] - p[sigma[i]]) == pytest.approx(envy)


# --- exakte Rechnung mit Brüchen -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(36))
def test_maximin_matches_the_exact_vertex_enumeration(seed):
    v = instance(seed, 3)
    sigma = A.assignment(v)
    t_star, spread = exact_maximin(v, sigma)
    o = A.evaluate(v, sigma, A.lp_maximin(v, sigma))
    assert o.min_utility == pytest.approx(float(t_star), abs=1e-6)
    assert o.spread == pytest.approx(float(spread), abs=1e-5)


@pytest.mark.parametrize("seed", range(36))
def test_maximin_without_negative_prices_matches_the_exact_enumeration(seed):
    v = instance(seed, 3)
    sigma = A.assignment(v)
    exact = exact_maximin(v, sigma, nonneg=True)
    got = A.lp_maximin(v, sigma, nonneg=True)
    assert (exact is None) == (got is None)
    if exact is not None:
        o = A.evaluate(v, sigma, got)
        assert o.min_utility == pytest.approx(float(exact[0]), abs=1e-6) and o.spread == pytest.approx(float(exact[1]), abs=1e-5)


@pytest.mark.parametrize("seed", range(36))
def test_smallest_spread_matches_the_exact_enumeration(seed):
    v = instance(seed, 3)
    sigma = A.assignment(v)
    assert A.evaluate(v, sigma, A.lp_spread(v, sigma)).spread == pytest.approx(float(exact_min_spread(v, sigma)), abs=1e-5)


@pytest.mark.parametrize("seed", range(4))
def test_four_tenants_match_the_exact_enumeration_too(seed):
    """Vier Mieter: die erste Stufe (Mindestnutzen) für vier Instanzen; die Spanne nur für die ersten beiden (die Aufzählung wächst rasch)."""
    v = instance(seed, 4)
    sigma = A.assignment(v)
    t_star, _ = exact_maximin(v, sigma, second=False)
    assert A.evaluate(v, sigma, A.lp_maximin(v, sigma)).min_utility == pytest.approx(float(t_star), abs=1e-6)
    if seed < 2:
        assert A.evaluate(v, sigma, A.lp_spread(v, sigma)).spread == pytest.approx(float(exact_min_spread(v, sigma)), abs=1e-5)


def test_the_exact_oracle_solves_a_known_polytope():
    # Maximiere x + y über x ≤ 2, y ≤ 3, x + y = 4 (eine Gleichung): nur der Wert 4 ist möglich
    best = exact_lp([1, 1], [[1, 0], [0, 1]], [2, 3], [[1, 1]], [4])
    assert best[0] == 4
    assert exact_lp([1, 0], [[1, 0], [-1, 0]], [3, -5], [[0, 1]], [1]) is None                     # x ≤ 3 und x ≥ 5: leer
    assert solve_square([[2, 0], [0, 4]], [6, 8]) == [3, 2] and solve_square([[1, 1], [2, 2]], [1, 2]) is None


# --- Gleiche Preise und Mittel ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(60))
def test_equal_and_mean_prices_by_definition(seed):
    n = 3 + seed % 5
    v = instance(seed, n)
    assert A.equal_prices(n).tolist() == [C.RENT / n] * n
    mean = A.mean_prices(v)
    assert mean.sum() == pytest.approx(C.RENT) and all(mean[j] == pytest.approx(sum(int(v[i][j]) for i in range(n)) / n) for j in range(n))


def test_the_property_tests_are_not_vacuous():
    """Es gibt Instanzen mit negativem Maximin-Preis, mit unmöglichem „ab 0“ und mit nicht neidfreier gleicher Aufteilung; sonst prüften die Tests oben nichts Unterscheidendes."""
    neg = infeasible = unequal = 0
    for seed in range(120):
        n = 3 + seed % 5
        v = instance(seed, n)
        sigma = A.assignment(v)
        neg += A.lp_maximin(v, sigma).min() < -1e-6
        infeasible += A.lp_maximin(v, sigma, nonneg=True) is None
        unequal += not A.evaluate(v, sigma, A.equal_prices(n)).envy_free
    assert neg >= 15 and infeasible >= 3 and unequal >= 100, (neg, infeasible, unequal)
