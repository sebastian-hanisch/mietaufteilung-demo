"""Auswertung: Einstellungen, Analyse einer Instanz, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Messreihen."""

import math
from dataclasses import dataclass

import numpy as np

import mie_algorithm as A
import mie_constants as C
from mie_scenario import make_values


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def eur(x: float, digits: int = 0) -> str:
    """Betrag in Euro mit Dezimalkomma und Tausenderpunkt; negative Beträge mit echtem Minuszeichen."""
    s = f"{abs(x):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if round(x, digits) < 0 else "") + s + " €"


def pct(x: float, digits: int = 0) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",")


def short_rule(rule: str) -> str:
    return C.RULE_SHORT[rule]


def tenant(i: int) -> str:
    return f"Mieter {i + 1}"


def hall(j: int) -> str:
    return f"Fläche {chr(ord('A') + j)}"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    model: str = C.DEFAULT_MODEL
    k: int = C.DEFAULT_K
    seed: int = C.DEFAULT_SEED


@dataclass
class Analysis:
    settings: Settings
    values: np.ndarray
    sigma: tuple
    outcomes: dict        # Regel -> Outcome oder None („nicht möglich“)


def analyse(settings: Settings) -> Analysis:
    return analyse_values(settings, make_values(settings.n, settings.model, settings.k, settings.seed))


def analyse_values(settings: Settings, values: np.ndarray) -> Analysis:
    """Alle Regeln auf gegebenen Bewertungen (die Tests reichen handgebaute Werte herein)."""
    sigma = A.assignment(values)
    outcomes = {}
    for rule in C.RULES:
        prices = A.prices_for(rule, values, sigma)
        outcomes[rule] = None if prices is None else A.evaluate(values, sigma, prices)
    return Analysis(settings=settings, values=values, sigma=sigma, outcomes=outcomes)


def gain_over_equal(a: Analysis, rule: str):
    """Mindestnutzen der Regel minus Mindestnutzen der gleichen Aufteilung (bei derselben Zuordnung); None, wenn die Regel nicht möglich ist."""
    o = a.outcomes[rule]
    return None if o is None else o.min_utility - a.outcomes["gleich"].min_utility


def value_rows(a: Analysis) -> list[dict]:
    """Bewertungen als Tabelle: je Mieter eine Zeile, je Fläche eine Spalte; die zugeordnete Fläche ist mit ◆ markiert."""
    n = a.values.shape[0]
    rows = []
    for i in range(n):
        row = {"Mieter": tenant(i)}
        for j in range(n):
            row[hall(j)] = f"{int(a.values[i, j])} ◆" if a.sigma[i] == j else str(int(a.values[i, j]))
        rows.append(row)
    return rows


def rule_rows(a: Analysis) -> list[dict]:
    """Zeilen für st.table: je Regel eine Zeile."""
    rows = []
    for rule in C.RULES:
        o = a.outcomes[rule]
        if o is None:
            rows.append({"Regel": C.RULES[rule], "Preise": "nicht möglich", "Neidfrei": "–", "Größter Neid": "–", "Mindestnutzen": "–", "Preisspanne": "–", "Negative Preise": "–"})
            continue
        rows.append({
            "Regel": C.RULES[rule], "Preise": " / ".join(eur(p) for p in o.prices), "Neidfrei": "ja" if o.envy_free else "nein",
            "Größter Neid": "–" if o.envy_free else eur(o.envy), "Mindestnutzen": eur(o.min_utility), "Preisspanne": eur(o.spread), "Negative Preise": "ja" if o.has_negative else "nein",
        })
    return rows


def witness_lines(a: Analysis) -> list[str]:
    """Je Regel ohne Neidfreiheit ein Beispiel in Worten; dazu die Flächen mit negativem Preis bei den neidfreien Regeln."""
    lines = []
    v = a.values
    for rule in C.RULES:
        o = a.outcomes[rule]
        if o is None:
            continue
        if not o.envy_free:
            i, j = o.envy_pair
            mine = v[i, a.sigma[i]] - o.prices[a.sigma[i]]
            there = v[i, j] - o.prices[j]
            lines.append(f"**{short_rule(rule)}:** {tenant(i)} hat {hall(a.sigma[i])} (Nutzen {eur(mine)}) und beneidet {hall(j)}: dort wäre sein Nutzen {eur(there)} (Neid {eur(o.envy)}).")
        elif o.has_negative and rule == "maximin":
            neg = [j for j, p in enumerate(o.prices) if p < -A.TOL]
            names = ", ".join(f"{hall(j)} ({eur(o.prices[j])})" for j in neg)
            lines.append(f"**{short_rule(rule)}, negative Preise:** {names}; wer diese Fläche nimmt, bekommt Geld dazu; nur so zieht niemand eine andere Fläche vor.")
    return lines


def verdict_state(a: Analysis) -> tuple[str, str]:
    """Verdikt: Neid der gleichen Aufteilung, was die neidfreien Preise leisten, ob negative Preise nötig sind."""
    g, mi, ne = a.outcomes["gleich"], a.outcomes["maximin"], a.outcomes["ohne_minus"]
    n = a.settings.n
    share = C.RENT / n
    text = (f"Bei gleicher Aufteilung ({eur(share, 0 if abs(share - round(share)) < 1e-9 else 1)} je Fläche) ist der Mindestnutzen {eur(g.min_utility)} und der größte Neid {eur(g.envy)}"
            f"{'' if g.envy_free else ' (' + tenant(g.envy_pair[0]) + ' beneidet ' + hall(g.envy_pair[1]) + ')'}. "
            f"Hier gibt es neidfreie Preise; der größte Mindestnutzen ist {eur(mi.min_utility)} (Preise von {eur(min(mi.prices))} bis {eur(max(mi.prices))}, Gewinn gegenüber gleich {eur(mi.min_utility - g.min_utility)}). ")
    if mi.has_negative:
        text += "Dafür ist mindestens ein Preis negativ. "
        text += (f"Verlangt man Preise ab 0, sinkt der Mindestnutzen auf {eur(ne.min_utility)}." if ne is not None else "Verlangt man Preise ab 0, gibt es hier keine neidfreie Aufteilung.")
    else:
        text += "Alle Preise sind positiv; die Bedingung „Preise ab 0“ kostet hier nichts."
    return ("warning" if not g.envy_free else "info"), text


# --- feste Messreihen -------------------------------------------------------------------------------------------------------------------------

def _cell(n: int, model: str, k: int, runs: int, seed: int) -> dict:
    """Je Regel: Anteil neidfreier Instanzen, Anteil „nicht möglich“, Anteil mit negativen Preisen, Mediane von Mindestnutzen, Preisspanne, Neid und Gewinn gegenüber gleich."""
    acc = {rule: {"ef": 0, "infeasible": 0, "neg": 0, "min": [], "spread": [], "envy": [], "gain": []} for rule in C.RULES}
    for s in range(runs):
        a = analyse_values(Settings(n=n, model=model, k=k, seed=seed + s), make_values(n, model, k, seed + s))
        for rule in C.RULES:
            o = a.outcomes[rule]
            d = acc[rule]
            if o is None:
                d["infeasible"] += 1
                continue
            d["ef"] += o.envy_free
            d["neg"] += o.has_negative
            d["min"].append(o.min_utility)
            d["spread"].append(o.spread)
            d["envy"].append(o.envy)
            d["gain"].append(o.min_utility - a.outcomes["gleich"].min_utility)
    out = {}
    for rule, d in acc.items():
        med = lambda xs: float(np.median(xs)) if xs else float("nan")
        out[rule] = {"ef": d["ef"] / runs, "infeasible": d["infeasible"] / runs, "neg": d["neg"] / runs, "min": med(d["min"]), "spread": med(d["spread"]),
                     "envy": med(d["envy"]), "gain": med(d["gain"]), "gain_pos": float(np.mean(np.array(d["gain"]) > 1e-9)) if d["gain"] else float("nan")}
    return out


def _sweep(param: str, values, runs: int, seed: int) -> list[dict]:
    rows = []
    for x in values:
        args = {"n": C.SERIES_N, "model": C.DEFAULT_MODEL, "k": C.SERIES_K}
        args[param] = x
        cell = _cell(args["n"], args["model"], args["k"], runs, seed)
        for rule in C.RULES:
            rows.append({"param": param, "x": x, "rule": rule, "runs": runs, **cell[rule]})
    return rows


def series_models(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 1: die drei Geschmacksmodelle (4 Mieter, Ungleichheit 2)."""
    return _sweep("model", tuple(C.MODELS), runs, seed)


def series_tenants(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 2: Zahl der Mieter (unabhängige Geschmäcker, Ungleichheit 2)."""
    return _sweep("n", C.SERIES_NS, runs, seed)


def series_inequality(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 3: Ungleichheit der Bewertungen (4 Mieter, unabhängige Geschmäcker)."""
    return _sweep("k", C.SERIES_KS, runs, seed)


def cell_of(rows: list[dict], x, rule: str) -> dict:
    return next(r for r in rows if r["x"] == x and r["rule"] == rule)


AXIS_LABELS = {"model": "Geschmacksmodell", "n": "Mieter", "k": "Ungleichheit"}


def x_label(param: str, x) -> str:
    return C.MODEL_SHORT[x] if param == "model" else str(x)


def series_rows(rows: list[dict], key: str, formatter=pct) -> list[dict]:
    """Zeilen für st.table: je Wert des Reglers eine Zeile, je Regel eine Spalte."""
    out = []
    for x in dict.fromkeys(r["x"] for r in rows):
        row = {AXIS_LABELS[rows[0]["param"]]: x_label(rows[0]["param"], x)}
        for rule in C.RULES:
            row[short_rule(rule)] = formatter(cell_of(rows, x, rule)[key])
        out.append(row)
    return out


def verdict_models(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 1: je Modell Anteil neidfreier gleicher Aufteilungen, negative Preise beim Maximin, „Preise ab 0“ nicht möglich."""
    parts = []
    for x in dict.fromkeys(r["x"] for r in rows):
        parts.append(f"{C.MODEL_SHORT[x]}: gleiche Aufteilung neidfrei {pct(cell_of(rows, x, 'gleich')['ef'])}, negative Preise beim Maximin {pct(cell_of(rows, x, 'maximin')['neg'])}, „Preise ab 0“ nicht möglich {pct(cell_of(rows, x, 'ohne_minus')['infeasible'])}")
    return "info", f"Mittel über {rows[0]['runs']} Instanzen (4 Mieter, Ungleichheit 2). " + "; ".join(parts) + "."


def verdict_tenants(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 2: bei kleinster und größter Mieterzahl negative Preise und Gewinn des Maximin gegenüber gleich."""
    lo, hi = min(r["x"] for r in rows), max(r["x"] for r in rows)
    f = lambda x, rule, key: cell_of(rows, x, rule)[key]
    return "info", (f"Bei {lo} bzw. {hi} Mietern haben {pct(f(lo, 'maximin', 'neg'))} bzw. {pct(f(hi, 'maximin', 'neg'))} der neidfreien Maximin-Aufteilungen einen negativen Preis; "
                    f"der Mindestnutzen steigt gegenüber der gleichen Aufteilung im Median um {eur(f(lo, 'maximin', 'gain'))} bzw. {eur(f(hi, 'maximin', 'gain'))}. "
                    f"Neidfrei ist die gleiche Aufteilung in {pct(f(lo, 'gleich', 'ef'))} bzw. {pct(f(hi, 'gleich', 'ef'))} der Instanzen.")


def verdict_inequality(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 3: bei der kleinsten und größten Ungleichheit negative Preise, nicht mögliche Aufteilungen ab 0 und Preisspanne."""
    lo, hi = min(r["x"] for r in rows), max(r["x"] for r in rows)
    f = lambda x, rule, key: cell_of(rows, x, rule)[key]
    return "info", (f"Bei Ungleichheit {lo} bzw. {hi} (4 Mieter, {rows[0]['runs']} Instanzen): negative Preise beim Maximin {pct(f(lo, 'maximin', 'neg'))} bzw. {pct(f(hi, 'maximin', 'neg'))}; "
                    f"„Preise ab 0“ nicht möglich {pct(f(lo, 'ohne_minus', 'infeasible'))} bzw. {pct(f(hi, 'ohne_minus', 'infeasible'))}; "
                    f"Preisspanne (Median) {eur(f(lo, 'maximin', 'spread'))} bzw. {eur(f(hi, 'maximin', 'spread'))}.")
