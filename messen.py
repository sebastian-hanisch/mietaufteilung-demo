"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout."""

import sys
import time

sys.path.insert(0, ".")
import mie_constants as C
import mie_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, "| Zuordnung", a.sigma)
    for r in ev.rule_rows(a):
        print("   ", r)
    for line in ev.witness_lines(a):
        print("   -", line)
    print("   ", ev.verdict_state(a)[1])

for title, fn, key_list in (("REIHE 1 (Geschmäcker)", ev.series_models, ("ef", "infeasible", "neg", "min", "spread", "envy", "gain", "gain_pos")),
                            ("REIHE 2 (Mieter)", ev.series_tenants, ("ef", "infeasible", "neg", "min", "spread", "envy", "gain", "gain_pos")),
                            ("REIHE 3 (Ungleichheit)", ev.series_inequality, ("ef", "infeasible", "neg", "min", "spread", "envy", "gain", "gain_pos"))):
    rows = fn()
    print(title, rows[0]["runs"], "Instanzen je Zelle")
    for key in key_list:
        print(" ", key)
        fmt = ev.pct if key in ("ef", "infeasible", "neg", "gain_pos") else ev.eur
        for r in ev.series_rows(rows, key, fmt):
            print("    ", r)
print("sec", round(time.time() - t0, 1))
