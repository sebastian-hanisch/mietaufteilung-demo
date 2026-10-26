"""Mietaufteilung: neidfreie Preise - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Abstimmen und Fair Teilen“: n Mieter teilen sich n Lagerflächen und eine feste Gesamtmiete. Jeder Mieter sagt, was ihm jede Fläche wert ist. Fünf Preisregeln (gleich, Mittel der
Bewertungen, neidfrei mit größtem Mindestnutzen, ohne negative Preise, kleinste Preisspanne) werden auf Neid, Mindestnutzen und Preisspanne geprüft. Der Kern liegt in mie_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import mie_constants as C
import mie_evaluation as ev
from mie_evaluation import Settings, analyse, num, rule_rows, series_rows, value_rows, verdict_inequality, verdict_models, verdict_state, verdict_tenants, witness_lines
from mie_layout import dunkles_design, kopf_css
from mie_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from mie_visualization import build_prices, build_series, build_utilities

st.set_page_config(page_title="Mietaufteilung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_models():
    return ev.series_models()


@st.cache_data(show_spinner=False)
def _series_tenants():
    return ev.series_tenants()


@st.cache_data(show_spinner=False)
def _series_inequality():
    return ev.series_inequality()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mie_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🏭 Lagerflächen und Miete: wer zahlt was?")
st.markdown(
    f"""
Mehrere Betriebe mieten gemeinsam eine Lagerhalle, die in **gleich viele Flächen** wie Mieter geteilt ist, und zahlen zusammen eine **feste Gesamtmiete** ({C.RENT:,} €). Die Flächen sind nicht gleich viel wert: eine liegt am Tor, eine hat keine Rampe. Jeder Mieter sagt, **was ihm jede Fläche wert ist** (seine Bewertungen summieren sich auf die Gesamtmiete).
Gesucht sind eine **Zuordnung** (wer bekommt welche Fläche) und **Preise** (die sich auf die Gesamtmiete summieren), so dass **niemand eine andere Fläche zu deren Preis lieber hätte**: Neidfreiheit. Die naheliegende **gleiche Aufteilung** (Miete durch Flächenzahl) erfüllt das fast nie.
Die Demo vergleicht **fünf Preisregeln** auf denselben Bewertungen und zeigt, was neidfreie Preise brauchen: eine bestimmte Zuordnung, manchmal **negative Preise** und eine Entscheidung, wer wie viel bekommt (hier: der größte Mindestnutzen).
Verwandt: `hungarian-demo` und `auction-algorithm-demo` (Zuordnung), `moulin-demo` und `shapley-demo` (Kosten teilen), `unteilbare-gueter-demo` (Güter ohne Preise verteilen).

Weiter unten: der Abschnitt **🔬 Messreihen**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
""".replace(f"{C.RENT:,}", f"{C.RENT:,}".replace(",", "."))
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
1. **Bewertungen:** ganze Euro-Beträge je Mieter und Fläche, jede Zeile summiert sich auf die Gesamtmiete; drei Modelle (unabhängig, ähnlich, eine Premiumfläche) und die Ungleichheit (je größer, desto ungleicher bewertet ein Mieter die Flächen).
2. **Zuordnung:** die mit der größten Summe der Bewertungen (Ungarische Methode). Nur zu einer solchen Zuordnung gibt es neidfreie Preise, und zu jeder gibt es dieselben.
3. **Preise:** *Gleich:* Miete durch Flächenzahl. *Mittel:* Durchschnitt der Bewertungen je Fläche. *Neidfrei (Maximin):* unter allen neidfreien Preisen der größte kleinste Nutzen, dann die kleinste Preisspanne (lineare Optimierung). *Ab 0:* dasselbe, aber kein Preis unter 0. *Kleinste Spanne:* der geringste Abstand zwischen teuerster und billigster Fläche unter allen neidfreien Preisen.
4. **Nutzen** eines Mieters: Bewertung seiner Fläche minus ihr Preis. **Neid:** was eine andere Fläche mehr Nutzen brächte.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    n = st.slider("Mieter (und Flächen)", *bounds("n_slider"), key="n_slider", help="Zahl der Mieter; die Halle hat ebenso viele Flächen.")
    model = st.selectbox("Geschmäcker", list(C.MODELS), format_func=C.MODELS.get, key="model_select", help="Wie die Bewertungen entstehen.")
    k = st.slider("Ungleichheit der Bewertungen", *bounds("k_slider"), key="k_slider", help="Exponent der Zufallsgewichte: bei 1 bewertet ein Mieter die Flächen ähnlich, bei hohen Werten will er eine oder zwei sehr und die anderen kaum.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Bewertungen ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "model_select": model, "k_slider": int(k), "seed_input": int(seed)})

settings = Settings(n=int(n), model=model, k=int(k), seed=int(seed))
with st.spinner("Rechne die Preise …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
g, mi = a.outcomes["gleich"], a.outcomes["maximin"]
m1.metric("Gesamtmiete", f"{C.RENT:,} €".replace(",", "."), delta=f"{settings.n} Flächen, {settings.n} Mieter", delta_color="off")
m2.metric("Größter Neid bei gleicher Aufteilung", ev.eur(g.envy), delta="neidfrei" if g.envy_free else "Mieter beneiden eine andere Fläche", delta_color="off")
m3.metric("Größter Mindestnutzen (neidfrei)", ev.eur(mi.min_utility), delta=f"gleich aufgeteilt: {ev.eur(g.min_utility)}", delta_color="off")
st.markdown("**Bewertungen** (was jede Fläche dem Mieter wert ist; ◆ = ihm zugeordnet)")
st.table(value_rows(a))
st.markdown("**Preisregeln im Vergleich**")
st.table(rule_rows(a))
st.markdown("**Preise je Fläche**")
st.plotly_chart(build_prices(a), width="stretch", key="prices_chart")
st.markdown("**Nutzen der Mieter** (Bewertung der Fläche minus Preis; unter 0 zahlt ein Mieter mehr, als die Fläche ihm wert ist)")
st.plotly_chart(build_utilities(a), width="stretch", key="utilities_chart")
lines = witness_lines(a)
if lines:
    st.markdown("**Beispiele**")
    for line in lines:
        st.markdown("- " + line)

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was macht eine Aufteilung neidfrei, und was kostet das?")
kind, text = verdict_state(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Messreihen")
st.caption(f"Feste Programme, unabhängig von den Reglern. Jede Reihe rechnet auf Klick in einigen Sekunden; je Zelle {C.SERIES_RUNS} Instanzen mit den Zufalls-Seeds {C.SERIES_SEED} bis {C.SERIES_SEED + C.SERIES_RUNS - 1}.")
tab1, tab2, tab3 = st.tabs(["Welche Geschmäcker?", "Wie viele Mieter?", "Wie ungleich?"])
with tab1:
    st.markdown(f"**Wie oft sind negative Preise nötig?** Anteil der Instanzen für die drei Geschmacksmodelle ({C.SERIES_N} Mieter, Ungleichheit {C.SERIES_K}).")
    if st.button("Reihe rechnen", key="models_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_models()
        st.session_state["models_done"] = time.perf_counter() - t0
    if "models_done" in st.session_state:
        rows = _series_models()
        st.plotly_chart(build_series(rows, "neg", "Anteil mit negativem Preis"), width="stretch", key="models_neg_chart")
        st.plotly_chart(build_series(rows, "infeasible", "Anteil „nicht möglich“"), width="stretch", key="models_inf_chart")
        st.table(series_rows(rows, "neg"))
        kind, text = verdict_models(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['models_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown(f"**Wie hängt es von der Mieterzahl ab?** Unabhängige Geschmäcker, Ungleichheit {C.SERIES_K}.")
    if st.button("Reihe rechnen", key="tenants_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_tenants()
        st.session_state["tenants_done"] = time.perf_counter() - t0
    if "tenants_done" in st.session_state:
        rows = _series_tenants()
        st.plotly_chart(build_series(rows, "ef", "Anteil neidfreier Aufteilungen"), width="stretch", key="tenants_ef_chart")
        st.plotly_chart(build_series(rows, "gain", "Gewinn des Mindestnutzens gegenüber gleich (Median, €)", percent=False), width="stretch", key="tenants_gain_chart")
        st.table(series_rows(rows, "ef"))
        kind, text = verdict_tenants(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['tenants_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown(f"**Wie hängt es von der Ungleichheit der Bewertungen ab?** {C.SERIES_N} Mieter, unabhängige Geschmäcker.")
    if st.button("Reihe rechnen", key="inequality_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_inequality()
        st.session_state["inequality_done"] = time.perf_counter() - t0
    if "inequality_done" in st.session_state:
        rows = _series_inequality()
        st.plotly_chart(build_series(rows, "neg", "Anteil mit negativem Preis"), width="stretch", key="inequality_neg_chart")
        st.plotly_chart(build_series(rows, "spread", "Preisspanne (Median, €)", percent=False), width="stretch", key="inequality_spread_chart")
        st.table(series_rows(rows, "infeasible"))
        kind, text = verdict_inequality(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['inequality_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ehrliche Bewertungen** | Wer weiß, wie gerechnet wird, kann seine Bewertungen verschieben und so einen niedrigeren Preis erreichen; die Demo geht von wahren Angaben aus. | – |
| **Jeder Mieter nimmt genau eine Fläche, Flächen nicht teilbar** | Gehören Flächen zusammen oder will ein Mieter zwei, passt das Modell nicht. | diese Demo |
| **Bewertungen in Euro, jede Zeile summiert sich auf die Gesamtmiete** | Diese Eichung macht die Angaben verschiedener Mieter vergleichbar (aus dem Gedächtnis fragt auch Spliddit so). Die Ergebnisse gelten für sie; mit anderer Eichung wären Preise und Nutzen andere. | diese Demo |
| **Die Auswahl unter den neidfreien Preisen ist eine Wertung** | Der größte Mindestnutzen ist eine von vielen Möglichkeiten; die Messreihen zeigen, was er gegenüber der kleinsten Spanne kostet. | diese Demo (Tabelle) |
| **Negative Preise sind erlaubt** | „Preise ab 0“ kostet Mindestnutzen und ist manchmal unmöglich (Reihe 1 und 3). | diese Demo |
| **Eine Stichprobe von 300 Instanzen je Zelle** | Die Anteile hängen vom Erzeuger der Bewertungen ab (drei Modelle); echte Betriebe liegen dazwischen. | diese Demo (Messreihen) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Instanz.** $n$ Mieter, $n$ Flächen, Gesamtmiete $R$, Bewertungen $v_{ij} \ge 0$ mit $\sum_j v_{ij} = R$ für jeden Mieter $i$. Eine Aufteilung ist eine Zuordnung $\sigma$ (Mieter $i$ bekommt Fläche $\sigma(i)$) und Preise $p_j$ mit $\sum_j p_j = R$. Der Nutzen von Mieter $i$ ist $u_i = v_{i\sigma(i)} - p_{\sigma(i)}$.

**Neidfreiheit.** $v_{i\sigma(i)} - p_{\sigma(i)} \ge v_{ij} - p_j$ für alle $i, j$, also $p_{\sigma(i)} - p_j \le v_{i\sigma(i)} - v_{ij}$. Das ist ein lineares System; es hat eine Lösung genau dann, wenn $\sigma$ die Summe $\sum_i v_{i\sigma(i)}$ maximiert, und dann gilt dasselbe für jede maximierende Zuordnung (Dualität der Zuordnungsaufgabe).

**Neidfreie Preise für die Gesamtmiete $R$** gab es in allen gemessenen Instanzen (nach der Literatur immer, wenn jede Zeile auf $R$ summiert; aus dem Gedächtnis); nur der Ausschluss negativer Preise machte sie manchmal unmöglich.

**Maximin.** $\max t$ unter $t \le v_{i\sigma(i)} - p_{\sigma(i)}$, Neidfreiheit und $\sum p_j = R$; danach unter dem Optimum $t^*$ die kleinste Spanne $\min \bigl(\max_j p_j - \min_j p_j\bigr)$. Kleinste Spanne: dasselbe ohne die Bedingung an $t$.

**Literatur** (aus Abstracts, nicht im Original geprüft): Goldman, Procaccia, *Spliddit*, ACM SIGecom Exchanges 2014; Gal, Mash, Procaccia, Zick, *Which Is the Fairest (Rent Division) of Them All?*, Journal of the ACM 2017: unter allen neidfreien Aufteilungen ist Maximin in der Nutzerstudie die fairste; Su, *Rental Harmony*, 1999.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
