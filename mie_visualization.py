"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mie_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _hall(j):
    return f"Fläche {chr(ord('A') + j)}"


def build_prices(a):
    """Preis je Fläche und Regel (gruppierte Balken); die Linie zeigt die gleiche Aufteilung. Nicht mögliche Regeln fehlen."""
    n = a.values.shape[0]
    halls = [_hall(j) for j in range(n)]
    fig = go.Figure()
    for rule in C.RULES:
        o = a.outcomes[rule]
        if o is None:
            continue
        fig.add_trace(go.Bar(x=halls, y=list(o.prices), name=C.RULE_SHORT[rule], marker_color=C.RULE_COLORS[rule], hovertemplate="%{x}: %{y:.0f} €<extra>" + C.RULE_SHORT[rule] + "</extra>"))
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.6)")
    fig.add_hline(y=C.RENT / n, line_dash="dash", line_color=C.COLOR_ALERT, annotation_text=f"gleiche Aufteilung {C.RENT / n:.0f} €", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Preis in €")
    return _base(fig, height=380)


def build_utilities(a):
    """Nutzen jedes Mieters (Bewertung seiner Fläche minus Preis) je Regel; unter 0 heißt: er zahlt mehr, als die Fläche ihm wert ist."""
    n = a.values.shape[0]
    rules = [r for r in C.RULES if a.outcomes[r] is not None]
    fig = go.Figure()
    for i in range(n):
        fig.add_trace(go.Bar(x=[C.RULE_SHORT[r] for r in rules], y=[a.outcomes[r].utilities[i] for r in rules], name=f"Mieter {i + 1}", marker_color=C.COLOR_TENANTS[i],
                             hovertemplate="%{x}: %{y:.0f} €<extra>Mieter " + str(i + 1) + "</extra>"))
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.6)")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Nutzen in €")
    fig.update_xaxes(tickangle=-20)
    return _base(fig, height=380)


AXIS_TITLES = {"model": "Geschmacksmodell", "n": "Zahl der Mieter", "k": "Ungleichheit der Bewertungen"}


def build_series(rows, key, ytitle, percent=True):
    """Eine Linie je Regel; key: ef, infeasible, neg (Anteile) oder min, spread, envy, gain (Euro, Median); Regeln ohne Werte (nan) lassen Lücken."""
    fig = go.Figure()
    param = rows[0]["param"]
    for rule in C.RULES:
        pts = [r for r in rows if r["rule"] == rule]
        xs = [C.MODEL_SHORT[r["x"]] if param == "model" else r["x"] for r in pts]
        fmt = ".1%" if percent else ".0f"
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in pts], mode="lines+markers", name=C.RULE_SHORT[rule], line=dict(color=C.RULE_COLORS[rule], width=2),
                                 hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + C.RULE_SHORT[rule] + "</extra>"))
    fig.update_xaxes(title_text=AXIS_TITLES[param], type="category")
    if percent:
        fig.update_yaxes(title_text=ytitle, range=[0, 1.05], tickformat=".0%")
    else:
        fig.update_yaxes(title_text=ytitle)
    return _base(fig, height=340)
