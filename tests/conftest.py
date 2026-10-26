"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def vals(*rows) -> np.ndarray:
    """Bewertungen aus Zeilen (ein Mieter je Zeile)."""
    return np.array(rows, dtype=int)


@pytest.fixture
def drei():
    """3 Mieter, 3 Flächen, Gesamtmiete 1000 (jede Zeile summiert sich darauf).

    Mieter 1: 600 / 300 / 100, Mieter 2: 200 / 500 / 300, Mieter 3: 100 / 200 / 700. Die Zuordnung mit der größten Summe ist die Diagonale (600 + 500 + 700 = 1800).
    Handrechnung folgt in den Tests."""
    return vals([600, 300, 100], [200, 500, 300], [100, 200, 700])
