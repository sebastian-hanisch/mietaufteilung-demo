"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

RENT = 1000                                   # Gesamtmiete in Euro; jeder Mieter verteilt genau diese Summe auf die Flächen (Bewertungen summieren sich je Mieter auf RENT)

RULES = {
    "gleich": "Gleiche Aufteilung",
    "mittel": "Mittel der Bewertungen",
    "maximin": "Neidfrei, größter Mindestnutzen",
    "ohne_minus": "Neidfrei, größter Mindestnutzen, Preise ab 0",
    "spanne": "Neidfrei, kleinste Preisspanne",
}
RULE_SHORT = {"gleich": "Gleich", "mittel": "Mittel", "maximin": "Neidfrei (Maximin)", "ohne_minus": "Neidfrei ab 0", "spanne": "Kleinste Spanne"}
RULE_TEXT = {
    "gleich": "Jede Fläche kostet Miete geteilt durch Zahl der Flächen, unabhängig von ihrem Wert.",
    "mittel": "Der Preis einer Fläche ist der Durchschnitt der Bewertungen aller Mieter für diese Fläche.",
    "maximin": "Unter allen neidfreien Preisen der größte kleinste Nutzen; unter den dann noch möglichen die kleinste Preisspanne (die Auswahl von Spliddit, das Verfahren im Detail ist hier eigene Ausführung).",
    "ohne_minus": "Wie zuvor, aber kein Preis darf negativ sein; gibt es dann keine neidfreie Aufteilung, steht „nicht möglich“.",
    "spanne": "Unter allen neidfreien Preisen die mit dem kleinsten Abstand zwischen teuerster und billigster Fläche.",
}
DEFAULT_RULE = "maximin"

MODELS = {
    "unabhaengig": "Unabhängige Geschmäcker",
    "aehnlich": "Ähnliche Geschmäcker (alle schätzen dieselben Flächen)",
    "premium": "Eine Premiumfläche (alle wollen dieselbe)",
}
MODEL_SHORT = {"unabhaengig": "Unabhängig", "aehnlich": "Ähnlich", "premium": "Premiumfläche"}
DEFAULT_MODEL = "unabhaengig"

N_MIN, N_MAX, DEFAULT_N = 3, 8, 4             # Mieter (und Flächen)
K_MIN, K_MAX, DEFAULT_K = 1, 7, 2             # Ungleichheit der Bewertungen (Exponent der Zufallsgewichte)
SEED_MAX, DEFAULT_SEED = 9999, 7

# Feste Messreihen (unabhängig von den Reglern): nie ein einzelner Zufalls-Seed als Befund
SERIES_SEED = 100000
SERIES_RUNS = 300
SERIES_N, SERIES_K = 4, 2
SERIES_NS = (3, 4, 5, 6, 7)                   # Reihe 2: Mieterzahl bei Ungleichheit 2
SERIES_KS = (1, 2, 3, 4, 5, 6)                # Reihe 3: Ungleichheit bei 4 Mietern

COLOR_TENANTS = ["#4c78a8", "#e8a838", "#2F6B65", "#b04a3a", "#7b6fa8", "#8c8c8c", "#a8825c", "#5f9ea0"]
COLOR_ALERT = "#c0392b"
RULE_COLORS = {"gleich": "#9aa5b1", "mittel": "#4c78a8", "maximin": "#2F6B65", "ohne_minus": "#7fb8a6", "spanne": "#b04a3a"}

PRESETS = {
    "Vier Mieter": {"n": 4, "model": "unabhaengig", "k": 2, "seed": 7},
    "Negative Preise": {"n": 4, "model": "unabhaengig", "k": 3, "seed": 19},
    "Preise ab 0 unmöglich": {"n": 4, "model": "aehnlich", "k": 2, "seed": 3},
    "Sechs Mieter, eine Premiumfläche": {"n": 6, "model": "premium", "k": 2, "seed": 1},
    "Sehr ungleiche Bewertungen": {"n": 4, "model": "unabhaengig", "k": 6, "seed": 8},
}
PRESET_HELP = {
    "Vier Mieter": "Voreinstellung: vier Mieter, vier Flächen, unabhängige Geschmäcker. Die gleiche Aufteilung lässt einen Mieter 110 € Neid empfinden; neidfreie Preise gibt es ohne negative Preise.",
    "Negative Preise": "Hier ist die gleiche Aufteilung weit von neidfrei (größter Neid 432 €, kleinster Nutzen −221 €). Die neidfreien Preise mit dem größten Mindestnutzen haben einen negativen Preis (−111 €); „Preise ab 0“ gibt es hier auch, kosten aber Mindestnutzen (140 € gegen 29 €).",
    "Preise ab 0 unmöglich": "Bei ähnlichen Geschmäckern (alle schätzen dieselben Flächen) gibt es hier keine neidfreie Aufteilung ohne negative Preise: die unbeliebten Flächen müssen mit Geld ausgeglichen werden (negativer Preis).",
    "Sechs Mieter, eine Premiumfläche": "Eine Fläche, die alle wollen: die gleiche Aufteilung lässt 319 € Neid zu, neidfreie Preise heben den kleinsten Nutzen von −32 € auf 42 €, ganz ohne negative Preise.",
    "Sehr ungleiche Bewertungen": "Jeder Mieter will ein oder zwei Flächen sehr und die anderen kaum: die neidfreien Preise liegen weit auseinander (Spanne 775 €), der größte Mindestnutzen ist 529 €, mit „Preise ab 0“ nur 206 €.",
}
