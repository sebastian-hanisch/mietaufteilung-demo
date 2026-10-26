"""Kern: Mietaufteilung (n Mieter, n Flächen, Gesamtmiete fest) mit neidfreien Preisen.

Bewertungen: Matrix `values` (n, n) ganzer Zahlen, values[i, j] = Zahlungsbereitschaft von Mieter i für Fläche j; jede Zeile summiert sich auf die Gesamtmiete. Eine Aufteilung ist eine
Zuordnung `sigma` (Mieter i bekommt Fläche sigma[i]) und Preise `p` (Fläche j kostet p[j], die Preise summieren sich auf die Gesamtmiete; negative Preise sind erlaubt, wenn nicht anders
gesagt). Der Nutzen von Mieter i ist values[i, sigma[i]] − p[sigma[i]]. **Neidfrei**: kein Mieter hätte lieber eine andere Fläche zu deren Preis.

Neidfreie Preise gibt es nur zu einer Zuordnung mit der größten Gesamtbewertung (Ungarische Methode); zu jeder solchen Zuordnung gibt es dieselben neidfreien Preise.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment, linprog

import mie_constants as C

TOL = 1e-7          # Neid unterhalb dieser Grenze zählt als 0 (Rundung des LP-Lösers)
SLACK = 1e-9        # Spielraum in der zweiten Stufe, damit der Mindestnutzen der ersten Stufe numerisch erreichbar bleibt


def assignment(values) -> tuple:
    """Zuordnung mit der größten Summe der Bewertungen (Ungarische Methode); sigma[i] = Fläche von Mieter i."""
    rows, cols = linear_sum_assignment(-np.asarray(values))
    sigma = [0] * len(rows)
    for i, j in zip(rows, cols):
        sigma[int(i)] = int(j)
    return tuple(sigma)


def utilities(values, sigma, prices) -> np.ndarray:
    return np.array([values[i, sigma[i]] - prices[sigma[i]] for i in range(len(sigma))], dtype=float)


def max_envy(values, sigma, prices):
    """Größter Neid in Euro und das Paar (Mieter, beneidete Fläche); (0.0, None), wenn niemand neidet (bis TOL)."""
    n = len(sigma)
    u = utilities(values, sigma, prices)
    best, who = 0.0, None
    for i in range(n):
        for j in range(n):
            if j == sigma[i]:
                continue
            envy = float(values[i, j] - prices[j] - u[i])
            if envy > best + 1e-12 and envy > TOL:
                best, who = envy, (i, j)
    return best, who


def _envy_rows(values, sigma, n_cols):
    """Zeilen A p ≤ b für Neidfreiheit: p[s] − p[j] ≤ values[i, s] − values[i, j] für jeden Mieter i und jede andere Fläche j (s = sigma[i])."""
    n = len(sigma)
    rows, rhs = [], []
    for i in range(n):
        s = sigma[i]
        for j in range(n):
            if j != s:
                row = np.zeros(n_cols)
                row[s], row[j] = 1.0, -1.0
                rows.append(row)
                rhs.append(float(values[i, s] - values[i, j]))
    return rows, rhs


def lp_maximin(values, sigma, nonneg=False, rent=C.RENT):
    """Neidfreie Preise mit dem größten Mindestnutzen; unter allen Preisen mit diesem Mindestnutzen die mit der kleinsten Preisspanne. None, wenn es keine gibt (nur mit nonneg möglich)."""
    n = len(sigma)
    rows, rhs = _envy_rows(values, sigma, n + 1)
    for i in range(n):                                          # t ≤ Nutzen von i
        row = np.zeros(n + 1)
        row[sigma[i]], row[n] = 1.0, 1.0
        rows.append(row)
        rhs.append(float(values[i, sigma[i]]))
    eq = np.append(np.ones(n), 0.0)[None, :]
    bounds = [(0, None) if nonneg else (None, None)] * n + [(None, None)]
    c = np.zeros(n + 1)
    c[n] = -1.0
    first = linprog(c, A_ub=np.array(rows), b_ub=rhs, A_eq=eq, b_eq=[rent], bounds=bounds, method="highs")
    if first.status != 0:
        return None
    t_star = float(first.x[n])
    # zweite Stufe: Variablen p (n), hi, lo; Nutzen von i ≥ t_star; kleinste Spanne hi − lo
    rows2, rhs2 = _envy_rows(values, sigma, n + 2)
    for i in range(n):
        row = np.zeros(n + 2)
        row[sigma[i]] = 1.0
        rows2.append(row)
        rhs2.append(float(values[i, sigma[i]]) - t_star + SLACK)
    for j in range(n):
        up, low = np.zeros(n + 2), np.zeros(n + 2)
        up[j], up[n] = 1.0, -1.0                                # p[j] − hi ≤ 0
        low[j], low[n + 1] = -1.0, 1.0                          # lo − p[j] ≤ 0
        rows2 += [up, low]
        rhs2 += [0.0, 0.0]
    eq2 = np.concatenate([np.ones(n), [0.0, 0.0]])[None, :]
    c2 = np.zeros(n + 2)
    c2[n], c2[n + 1] = 1.0, -1.0
    bounds2 = [(0, None) if nonneg else (None, None)] * n + [(None, None), (None, None)]
    second = linprog(c2, A_ub=np.array(rows2), b_ub=rhs2, A_eq=eq2, b_eq=[rent], bounds=bounds2, method="highs")
    chosen = second.x[:n] if second.status == 0 else first.x[:n]
    return np.array(chosen, dtype=float)


def lp_spread(values, sigma, rent=C.RENT):
    """Neidfreie Preise mit der kleinsten Spanne zwischen teuerster und billigster Fläche."""
    n = len(sigma)
    rows, rhs = _envy_rows(values, sigma, n + 2)
    for j in range(n):
        up, low = np.zeros(n + 2), np.zeros(n + 2)
        up[j], up[n] = 1.0, -1.0
        low[j], low[n + 1] = -1.0, 1.0
        rows += [up, low]
        rhs += [0.0, 0.0]
    eq = np.concatenate([np.ones(n), [0.0, 0.0]])[None, :]
    c = np.zeros(n + 2)
    c[n], c[n + 1] = 1.0, -1.0
    res = linprog(c, A_ub=np.array(rows), b_ub=rhs, A_eq=eq, b_eq=[rent], bounds=[(None, None)] * (n + 2), method="highs")
    return np.array(res.x[:n], dtype=float) if res.status == 0 else None


def equal_prices(n, rent=C.RENT) -> np.ndarray:
    return np.full(n, rent / n)


def mean_prices(values) -> np.ndarray:
    """Durchschnitt der Bewertungen je Fläche; weil jede Zeile auf die Gesamtmiete summiert, summieren sich auch die Preise darauf."""
    return np.asarray(values, dtype=float).mean(axis=0)


RULE_NAMES = ("gleich", "mittel", "maximin", "ohne_minus", "spanne")


def prices_for(rule, values, sigma):
    if rule == "gleich":
        return equal_prices(len(sigma))
    if rule == "mittel":
        return mean_prices(values)
    if rule == "maximin":
        return lp_maximin(values, sigma)
    if rule == "ohne_minus":
        return lp_maximin(values, sigma, nonneg=True)
    if rule == "spanne":
        return lp_spread(values, sigma)
    raise ValueError(rule)


@dataclass(frozen=True)
class Outcome:
    prices: tuple
    utilities: tuple
    min_utility: float
    envy: float                  # größter Neid in Euro
    envy_pair: object            # (Mieter, beneidete Fläche) oder None
    spread: float                # teuerste minus billigste Fläche
    has_negative: bool           # mindestens ein Preis unter 0

    @property
    def envy_free(self) -> bool:
        return self.envy_pair is None


def evaluate(values, sigma, prices) -> Outcome:
    p = np.asarray(prices, dtype=float)
    u = utilities(values, sigma, p)
    envy, pair = max_envy(values, sigma, p)
    return Outcome(prices=tuple(float(x) for x in p), utilities=tuple(float(x) for x in u), min_utility=float(u.min()), envy=envy, envy_pair=pair,
                   spread=float(p.max() - p.min()), has_negative=bool((p < -TOL).any()))
