"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, keiner auf einem Reglerrand und keiner, der durch eine einzelne Regleränderung vom Standard entsteht."""

import mie_constants as C
import mie_evaluation as ev
import mie_presets as P

FIRST = "Vier Mieter"
BOUNDS = {"n": (C.N_MIN, C.N_MAX), "k": (C.K_MIN, C.K_MAX), "seed": (0, C.SEED_MAX)}


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, p in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert lo <= p[key] <= hi, (name, key)
        assert p["model"] in C.MODELS, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[FIRST]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_preset_sits_on_a_slider_bound():
    for name, preset in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert preset[key] not in (lo, hi), (name, key)


def test_no_single_change_of_the_default_produces_another_preset():
    default = C.PRESETS[FIRST]
    for name, p in C.PRESETS.items():
        if name != FIRST:
            assert sum(1 for k in p if p[k] != default[k]) >= 2, name


def test_presets_are_pairwise_different_and_cover_every_model():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values) and {p["model"] for p in C.PRESETS.values()} == set(C.MODELS)


def test_colors_cover_the_largest_tenant_count():
    assert len(C.COLOR_TENANTS) >= C.N_MAX
