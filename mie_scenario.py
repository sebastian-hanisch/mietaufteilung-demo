"""Szenario: n Mieter und n Flächen; jeder Mieter verteilt die Gesamtmiete als ganze Euro-Beträge auf die Flächen (seine Zahlungsbereitschaft je Fläche)."""

import numpy as np

import mie_constants as C


def round_to_total(weights: np.ndarray, total: int) -> np.ndarray:
    """Ganze Zahlen mit der Summe `total`, proportional zu den Gewichten (größter Rest; bei Gleichstand der kleinere Index)."""
    shares = total * weights / weights.sum()
    base = np.floor(shares).astype(int)
    missing = total - int(base.sum())
    order = sorted(range(len(weights)), key=lambda j: (-(shares[j] - base[j]), j))
    for j in order[:missing]:
        base[j] += 1
    return base


def make_values(n: int, model: str, k: int, seed: int) -> np.ndarray:
    """Matrix (n, n) ganzer Zahlen: values[i, j] ist, was Mieter i für Fläche j zu zahlen bereit wäre; jede Zeile summiert sich auf C.RENT.

    unabhaengig: Gewichte Zufallszahl hoch k (je größer k, desto ungleicher die Flächen für einen Mieter).
    aehnlich: ein gemeinsames Gewicht je Fläche (Zufallszahl hoch k), je Mieter mit Streuung von 0,7 bis 1,3 multipliziert.
    premium: flache Gewichte (0,5 bis 1,5), eine zufällige Fläche mit dem Faktor 2 + k für alle."""
    if model not in C.MODELS:
        raise ValueError(model)
    rng = np.random.default_rng(seed)
    if model == "unabhaengig":
        w = rng.random((n, n)) ** k
    elif model == "aehnlich":
        base = rng.random(n) ** k
        w = base[None, :] * (0.7 + 0.6 * rng.random((n, n)))
    else:
        w = 0.5 + rng.random((n, n))
        w[:, int(rng.integers(0, n))] *= 2 + k
    w = w + 1e-9                                             # nie eine Zeile aus lauter Nullen
    return np.stack([round_to_total(w[i], C.RENT) for i in range(n)])
