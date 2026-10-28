# Mietaufteilung: neidfreie Preise – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-mietaufteilung-demo.streamlit.app/)** -->

Stück der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [unteilbare-gueter-demo](https://github.com/sebastian-hanisch/unteilbare-gueter-demo) (unteilbare Güter verteilen, ohne Preise), [gemeinsames-budget-demo](https://github.com/sebastian-hanisch/gemeinsames-budget-demo) (ein Budget auf Projekte verteilen), `hungarian-demo` und `auction-algorithm-demo` (Zuordnung) sowie `moulin-demo` und `shapley-demo` (Kosten teilen).
Die Demo fragt: **Mehrere Betriebe mieten gemeinsam eine Lagerhalle, die in ebenso viele Flächen geteilt ist wie es Mieter gibt, und zahlen eine feste Gesamtmiete – wie verteilt man Flächen und Preise, so dass niemand eine andere Fläche zu deren Preis lieber hätte?** Jeder Mieter sagt, was ihm jede Fläche wert ist (seine Angaben summieren sich auf die Gesamtmiete). Fünf Preisregeln auf denselben Angaben: **gleiche Aufteilung**, **Mittel der Bewertungen**, **neidfrei mit größtem Mindestnutzen** (die Auswahl von Spliddit), dasselbe **ohne negative Preise** und **neidfrei mit der kleinsten Preisspanne**.
Gemessen werden Neid (in Euro), Mindestnutzen, Preisspanne, **negative Preise** und die Frage, ob es ohne sie überhaupt eine neidfreie Aufteilung gibt.

Der Kern ist eigener Code (`numpy`, `scipy`): die Zuordnung per `scipy.optimize.linear_sum_assignment` (löst dasselbe wie die Ungarische Methode) und lineare Optimierungen (HiGHS) für die Preise. Ein unabhängiges Orakel in den Tests rechnet die Zuordnung durch Aufzählung aller Permutationen und die Preise **exakt mit Brüchen**, indem es alle Ecken des Preisvielecks aufzählt.

## Warum dieses Problem

Die naheliegende Regel teilt die Miete gleich. Das ist selten fair, wenn die Flächen unterschiedlich viel wert sind: bei vier Mietern ist die gleiche Aufteilung in **10 %** der Instanzen neidfrei, bei drei Mietern in 23 %, bei sieben in 1 %. Neidfreie Preise gibt es dagegen **in jeder gemessenen Instanz** (3 600 verschiedene Instanzen in den drei Reihen), aber sie sehen anders aus als erwartet: eine bestimmte Zuordnung ist nötig, die Preise liegen weit auseinander (Spanne im Median 452 € bei einer Gesamtmiete von 1 000 €), und in **35 %** der Instanzen wählt die Regel „größter Mindestnutzen“ mindestens einen **negativen Preis** (wer die Fläche nimmt, bekommt Geld dazu); wirklich unvermeidbar ist er nur dort, wo es keine neidfreien Preise ab 0 gibt (1 % unabhängig, 19 % ähnlich, 0 % Premiumfläche). Das hängt stark vom Erzeuger der Bewertungen ab: die Regel wählt ihn bei ähnlichen Geschmäckern in 51 %, bei einer Premiumfläche, die alle wollen, in 0 %.
Die Demo trennt zwei Dinge, die in einer Lehrbuchdarstellung zusammenfließen: **neidfrei** (eine Bedingung) und **welche** neidfreie Aufteilung (eine Wertung: größter Mindestnutzen oder gleichmäßigste Preise).

## Modell

**Instanz.** n Mieter und n Flächen, Gesamtmiete R = 1 000 €. Bewertungen v<sub>ij</sub> sind ganze Zahlen ≥ 0, jede Zeile summiert sich auf R (der Mieter verteilt die Miete auf die Flächen nach seiner Zahlungsbereitschaft). Drei Geschmacksmodelle: *unabhängig* (Zufallszahl hoch k je Fläche), *ähnlich* (gemeinsames Gewicht je Fläche mit 0,7 bis 1,3 Streuung je Mieter), *Premiumfläche* (flache Gewichte, eine Fläche mit dem Faktor 2 + k). k ist die **Ungleichheit** (1 bis 7).
**Aufteilung.** Eine Zuordnung σ (Mieter i bekommt Fläche σ(i)) und Preise p<sub>j</sub> mit Summe R. Nutzen von Mieter i: v<sub>iσ(i)</sub> − p<sub>σ(i)</sub>. **Neid:** was eine andere Fläche zu ihrem Preis mehr Nutzen brächte. **Neidfrei:** kein Neid.
**Zuordnung.** Neidfreie Preise gibt es nur zu einer Zuordnung mit der größten Summe der Bewertungen (Ungarische Methode), und zu jeder solchen Zuordnung gibt es dieselben (die Tests prüfen es: der Maximin-Wert ist für alle optimalen Zuordnungen gleich).
**Preisregeln.** *Gleich:* R / n je Fläche. *Mittel:* Durchschnitt der Bewertungen je Fläche. *Neidfrei (Maximin):* lineare Optimierung, größter kleinster Nutzen, danach unter dem Optimum die kleinste Preisspanne (die zweite Stufe ist **unsere Ausführung**, damit die Preise reproduzierbar sind). *Ab 0:* dasselbe mit p ≥ 0; wenn das System unlösbar ist, steht „nicht möglich“. *Kleinste Spanne:* die geringste Differenz zwischen teuerster und billigster Fläche unter allen neidfreien Preisen.
Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`mie_algorithm.py`): Zuordnung, die fünf Preisregeln, Neid (`max_envy`), Kennzahlen (`evaluate`).
- **Szenario und Auswertung** (`mie_scenario.py`, `mie_evaluation.py`): Bewertungen aus Modell, Ungleichheit und Zufalls-Seed (ganzzahlig, Zeilensumme R), Tabelle je Regel, Beispiele in Worten, drei Messreihen mit festem Programm (je Zelle 300 Instanzen, Zufalls-Seeds 100000 bis 100299), alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): fünf Schnellstart-Szenarien, Regler für Mieter, Geschmäcker, Ungleichheit und Zufalls-Seed, Ergebnis (Bewertungstabelle mit Zuordnung, Preisregeln im Vergleich, Preise je Fläche, Nutzen je Mieter), Kernfrage mit Verdikt, drei Reiter mit Messreihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Die Presets sind einzelne Instanzen und deshalb exakt. Die Messreihen sind Anteile und Mediane über je 300 Instanzen (4 Mieter, Ungleichheit 2, soweit nicht anders gesagt). **Die Zufallszahlen eines `numpy`-Generators sind nicht über Versionen stabil**: die Tests prüfen für die Reihen deshalb Bänder um diese Zahlen (±8 Prozentpunkte bei Anteilen, ±12 % bei Medianen); Nullen und „in jeder Instanz“-Aussagen sind in den festen Läufen exakt.

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Zuordnung gleich der **Aufzählung aller Permutationen** (80 Instanzen, 3 bis 6 Mieter); jede optimale Zuordnung liefert denselben Maximin-Wert (40); Neidfreiheit gleich der Definition (120 Instanzen, 3 bis 7 Mieter); Neid gleich der Definition (120); **Maximin, Maximin ab 0 und kleinste Spanne gleich einer exakten Rechnung mit Brüchen** über alle Ecken des Preisvielecks (je 36 Instanzen mit drei Mietern, dazu vier Instanzen mit vier Mietern). Handrechnungen mit Rechnung im Kommentar (zwei Mieter, drei Mieter mit negativem Preis). | `test_oracle_mietaufteilung.py`, `test_algorithm.py` |
| Wie selten ist die gleiche Aufteilung neidfrei? | Bei **4 Mietern 10 %** (unabhängig), **0 %** (ähnlich), **0 %** (Premiumfläche); mit 3, 4, 5, 6, 7 Mietern 23, 10, 3, 2, 1 %. Der größte Neid beträgt im Median **188 €** (unabhängig), **491 €** (ähnlich), 438 € (Premiumfläche); mit der Ungleichheit 1 bis 6 wächst er von **89 € auf 538 €**. | `test_claims.py::test_equal_split_and_mean_prices_are_rarely_envy_free`, `…::test_how_large_the_envy_of_the_equal_split_is` |
| Und das Mittel der Bewertungen? | Neidfrei bei 31 % (unabhängig), 5 % (ähnlich), 19 % (Premiumfläche); größter Neid im Median 43 € (unabhängig). Es ist näher an neidfrei als die gleiche Aufteilung, aber keine Lösung. | `test_claims.py::test_equal_split_and_mean_prices_are_rarely_envy_free` |
| Gibt es neidfreie Preise? | **Ja, in allen 3 600 verschiedenen Instanzen** der drei Reihen (4 200 Tabellenzeilen, drei davon sind dieselbe Zelle; Maximin und kleinste Spanne, Neid 0 €). Mit der Forderung „Preise ab 0“ **nicht immer**: nicht möglich in 1 % (unabhängig), **19 %** (ähnlich), 0 % (Premiumfläche); mit 3 bis 7 Mietern 0, 1, 4, 6, 5 %; mit der Ungleichheit 1 bis 6 0, 1, 5, 6, 9, 9 %. | `test_claims.py::test_the_envy_free_rules_are_envy_free_in_every_instance`, `…::test_prices_from_zero_are_sometimes_impossible` |
| Wie oft enthält die gewählte neidfreie Aufteilung einen negativen Preis? | Maximin: **35 %** (unabhängig), **51 %** (ähnlich), **0 %** (Premiumfläche); mit 3 bis 7 Mietern 23, 35, 45, 48, 49 %; mit der Ungleichheit 1 bis 6 **4, 35, 61, 75, 80, 84 %**. Die kleinste Spanne hat sie seltener (12 %, 37 %, 0 %; nach Ungleichheit 0 bis 61 %). Nötig sind negative Preise nur, wenn „Preise ab 0“ nicht möglich ist (1 %, 19 %, 0 %). | `test_claims.py::test_negative_prices_by_model_tenants_and_inequality` |
| Was bringt der größte Mindestnutzen gegenüber gleicher Aufteilung? | Der kleinste Nutzen steigt im Median um **187 €** (unabhängig), 250 € (ähnlich), 139 € (Premiumfläche) und in praktisch jeder Instanz (in jeder Zelle mindestens 99 %); mit 3 bis 7 Mietern 216, 187, 177, 145, 123 €; mit der Ungleichheit 1 bis 6 **99 € bis 415 €**. | `test_claims.py::test_the_maximin_prices_gain_min_utility_over_the_equal_split` |
| Was kostet „Preise ab 0“? | Mindestnutzen im Median bei der Ungleichheit 2 **170 € statt 198 €**, bei der Ungleichheit 6 **104 € statt 322 €**; die Preisspanne sinkt von 831 € auf 548 € (Ungleichheit 6). | `test_claims.py::test_the_cost_of_prices_from_zero_in_min_utility`, `…::test_price_spread_grows_with_inequality_and_shrinks_with_more_tenants` |
| Und die kleinste Preisspanne? | Spanne im Median **202 € statt 452 €** (Maximin), aber ein Mindestnutzen von nur 89 € statt 198 €; er liegt in **8 %** der Instanzen (Ungleichheit 2) sogar **unter dem der gleichen Aufteilung** und in weiteren 10 % ist er gleich (dort ist die gleiche Aufteilung schon neidfrei). Neidfrei ist nicht dasselbe wie hoher Mindestnutzen. | `test_claims.py::test_smallest_spread_prices_do_not_always_beat_the_equal_split_in_min_utility` |
| Wie breit sind die Preise? | Die Spanne der Maximin-Preise wächst mit der Ungleichheit von 235 € auf 831 € (Median) und schrumpft mit der Mieterzahl (457 € bei 3, 314 € bei 7 Mietern). | `test_claims.py::test_price_spread_grows_with_inequality_and_shrinks_with_more_tenants` |
| Schnellstart-Szenarien | Vier Mieter (Neid 110 €, neidfreie Preise ohne negative Preise, Mindestnutzen 186 €); negative Preise (Preis −111 €, „Preise ab 0“ kostet 140 € gegen 29 €); „Preise ab 0“ unmöglich; sechs Mieter mit einer Premiumfläche (Neid 319 €, Mindestnutzen −32 € auf 42 €); sehr ungleiche Bewertungen (Spanne 775 €, Mindestnutzen 529 € gegen 206 €). | `test_claims.py::test_default_preset` und die Tests der übrigen Presets |

## Ehrliche Grenzen

- **Ehrliche Bewertungen.** Wer weiß, wie gerechnet wird, kann seine Bewertungen verschieben und so einen niedrigeren Preis erreichen; die Demo geht von wahren Angaben aus.
- **Die Auswahl unter den neidfreien Preisen ist eine Wertung.** Der größte Mindestnutzen ist die Auswahl von Spliddit (nach den Abstracts; die Quellen sind nicht im Original gelesen); die zweite Stufe (kleinste Preisspanne unter dem Optimum) und die Regel „kleinste Spanne“ sind **eigene Festlegungen**. Die Preise der Regel „kleinste Spanne“ sind nicht immer eindeutig (die Messreihen und Tests prüfen den **Wert**, nicht den Preisvektor).
- **Die Zahlen hängen vom Erzeuger der Bewertungen ab.** Der Anteil, in dem das Maximin einen negativen Preis wählt, reicht von 0 % (Premiumfläche) bis 51 % (ähnlich) bei sonst gleichen Einstellungen, und die Vormessung nannte bereits „generatorabhängig“. Echte Betriebe sind nicht gemessen; der Anteil hängt vom Erzeuger und von der Ungleichheit ab (4 bis 84 %).
- **Jeder Mieter nimmt genau eine Fläche; Flächen sind nicht teilbar** und es gibt ebenso viele Flächen wie Mieter. Bewertungen in Euro, **jede Zeile summiert sich auf die Gesamtmiete**; mit anderer Eichung wären Preise und Nutzen andere.
- **Fließkomma und Löser.** Die Preise kommen aus dem Simplex-Löser HiGHS; Neid unter 1e-7 zählt als 0. Die Tests vergleichen die Werte mit der exakten Rechnung mit Brüchen (bis auf 1e-5).
- **„Immer“ heißt: in allen gemessenen Instanzen.** Dass neidfreie Preise (mit erlaubten negativen Preisen) immer existieren, ist ein bekannter Satz der Zuordnungsspiele; die Eichung der Bewertungen ist dafür nicht nötig (aus dem Gedächtnis); hier bestätigt, nicht bewiesen. Eine Stichprobe von 300 Instanzen je Zelle; kleine Unterschiede sind kein Befund.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9194 (9170 bis 9193 sind vergeben).
- **Fünf Regeln statt „Maximin gegen gleiche Aufteilung“.** Der Plan nannte nur den größten Mindestnutzen und die gleiche Aufteilung. Neu: das Mittel der Bewertungen (eine naheliegende Regel, die nicht neidfrei ist), „Preise ab 0“ (die Forderung, die Vormessung und Spliddit-Vergleich nahelegen) und die kleinste Preisspanne (die zeigt, dass Neidfreiheit allein den Mindestnutzen nicht sichert).
- **Orakel:** der Plan nannte „LP-Optimum gegen Aufzählung der Preisgitter bei 3 Zimmern“ und „Dualpreise der Zuordnung“. Das Orakel zählt stattdessen **alle Ecken des Preisvielecks mit Brüchen** auf (exakt, kein Gitter) und die Zuordnung durch alle Permutationen; die Neidfreiheit als Invariante bleibt.
- **Vormessung und App im Vergleich** (Vormessung: Bewertungen als Quadrat von Zufallszahlen, 1 000 Instanzen, andere Zufalls-Seeds; App: 300 Instanzen, Ungleichheit 2, unabhängig): LP lösbar in 1 000 von 1 000 gegen 300 von 300 (und in allen 3 600 verschiedenen Instanzen der Reihen); negative Preise 34,5 % gegen 35 %; Mindestnutzen gegenüber gleicher Aufteilung +186,6 gegen +187 € im Median. Übereinstimmung im Rahmen der Stichprobe.
- **Der Plan nannte die Bewertungserzeuger als Ampelpunkt (grün-gelb); die App wählt mehrere** (drei Modelle und die Ungleichheit) und zeigt, wie stark die Befunde davon abhängen.
- **Reglerspanne:** Mieter 3 bis 8, Ungleichheit 1 bis 7, drei Modelle.

## Verifikation

- **Kern:** jede Einheit an Mini-Instanzen von Hand (zwei Mieter: alle fünf Regeln mit Rechnung; drei Mieter mit negativem Preis, der Mindestnutzen 100 € für alle; Preise ab 0 mit eindeutiger Lösung; gleiche Aufteilung und Mittel mit Neid; alle Bewertungen gleich; alle wollen dieselbe Fläche).
- **Orakel:** Aufzählung aller Permutationen, Neidfreiheit und Neid nach der Definition, exakte Eckenaufzählung mit Brüchen (Maximin mit zweiter Stufe, ab 0, kleinste Spanne) auf zufälligen Instanzen aller drei Modelle, Invarianz gegen die Wahl der optimalen Zuordnung, Prüfung, dass die Tests nicht leer laufen (es gibt negative Preise, unmögliche „Preise ab 0“ und nicht neidfreie gleiche Aufteilungen).
- **Verdikte:** reine Funktionen, jeder Zweig (negative Preise, „Preise ab 0“ nicht möglich, gleiche Aufteilung neidfrei) und jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`), Randfälle an den Reglergrenzen (`tests/test_edge_cases.py`).
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, keines auf einem Reglerrand, kein Preset entsteht durch Änderung eines einzigen Reglers, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 73 Stellen im Kern `mie_algorithm.py`, **72 gefangen** (5 davon über wortgleiche Zeilen in Nachbar-Demos), **1 als äquivalent festgehalten**, keine Zeitüberschreitung. Der erste Lauf ließ 2 überleben: eine **echte Lücke** (bei gleichem Neid zweier Mieter meldet `max_envy` das erste Paar; `test_max_envy_reports_the_first_pair_on_a_tie` fängt den Wechsel auf das letzte) und eine äquivalente (das Vorzeichen des Spielraums von 1e-9 in der zweiten Stufe von `lp_maximin` liegt innerhalb der Toleranz des Lösers).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `mie_algorithm.py` | Kern: Zuordnung, Preisregeln, Neid, Kennzahlen |
| `mie_constants.py` | Regler-Grenzen, feste Pläne, Farben, Presets |
| `mie_evaluation.py` | Analyse einer Instanz, Tabellen, Beispiele in Worten, Messreihen, Verdikte |
| `mie_layout.py` | Fester Kopf (Stylesheet) |
| `mie_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `mie_scenario.py` | Bewertungen nach drei Geschmacksmodellen, ganzzahlig mit Zeilensumme R |
| `mie_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen, Kern, Orakel mit exakter Rechnung, Verdikte, Randfälle, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe, Claims |

## Bewusst nicht umgesetzt

- **Mehr Flächen als Mieter, mehrere Flächen je Mieter, Teilbarkeit:** ein anderes Zuteilungsproblem.
- **Mindestpreise und Höchstpreise je Fläche** (etwa eine Untergrenze, damit der Vermieter nichts zuzahlt): „Preise ab 0“ ist der einfachste Fall davon.
- **Strategisches Verhalten:** die Bewertungen sind ehrlich; wie viel ein Mieter durch falsche Angaben gewinnen könnte, ist hier nicht gemessen.
- **Auktionsverfahren und Preisanpassung in Runden** (nur die Gleichgewichtspreise werden gerechnet, nicht der Weg dorthin).
- **Weitere Auswahlregeln** unter den neidfreien Preisen (etwa Leximin, größte Summe der kleinsten k Nutzen).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
