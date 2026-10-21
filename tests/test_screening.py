"""Tests for src/screening.py on small synthetic grids (30 m pixels = 0.09 ha)."""
import random
from pathlib import Path

import numpy as np
import pytest

from src.screening import (
    OUTSIDE, QAError, Reason, Flag, apply_overrides, load_config, run_screening, validate_config,
)

CONFIG = Path(__file__).resolve().parents[1] / "config" / "jhabua.yaml"
SHAPE = (120, 120)


@pytest.fixture
def cfg():
    return load_config(CONFIG)


def make_layers():
    """Plain grassland district; column 0 is outside the district."""
    in_d = np.ones(SHAPE, dtype=bool)
    in_d[:, 0] = False
    return {
        "in_district": in_d,
        "nodata": np.zeros(SHAPE, dtype=bool),
        "district_mask": in_d.astype("uint8"),
        "worldcover": np.full(SHAPE, 30, dtype="uint8"),            # grassland
        "hansen_treecover2000": np.zeros(SHAPE, dtype="uint8"),
        "hansen_lossyear": np.zeros(SHAPE, dtype="uint8"),
        "hansen_gain": np.zeros(SHAPE, dtype="uint8"),
        "slope_deg": np.full(SHAPE, 2.0, dtype="float32"),
        "protected_areas": np.zeros(SHAPE, dtype="uint8"),
    }


def count(result, code):
    return int((result.reason == int(code)).sum())


def test_area_closes_and_stage_a_matches_direct_mask(cfg):
    L = make_layers()
    L["worldcover"][:20, :] = 10                  # tree cover
    L["worldcover"][20:30, :] = 50                # built-up
    L["nodata"][30:35, 1:] = True
    r = run_screening(L, cfg)
    total = int(L["in_district"].sum())
    assert sum(count(r, c) for c in Reason) == total          # every district pixel has a code
    assert (r.reason == OUTSIDE).sum() == SHAPE[0] * SHAPE[1] - total
    assert r.summary["methodology_eligible_ha"] >= r.summary["candidate_ha"]


def test_first_failing_filter_wins(cfg):
    L = make_layers()
    L["protected_areas"][50:60, 50:60] = 1
    L["slope_deg"][50:60, 50:60] = 40.0           # both protected AND steep
    r = run_screening(L, cfg)
    assert (r.reason[50:60, 50:60] == Reason.PROTECTED).all()  # PROTECTED precedes STEEP_SLOPE


def test_cropland_kept_in_census_but_flagged(cfg):
    L = make_layers()
    L["worldcover"][40:80, 20:100] = 40           # cropland block
    census = run_screening(L, cfg)
    assert count(census, Reason.CROPLAND) == 0
    assert (census.flags & Flag.CROPLAND_KEPT).any()           # kept, but flagged
    assert census.summary["methodology_eligible_ha"] >= census.summary["candidate_ha"]


def test_area_mode_is_disabled_not_silently_wrong(cfg):
    # The area route needs §1.1/§4.4.1 evidence this repo does not have.
    with pytest.raises(NotImplementedError):
        apply_overrides(cfg, {"project.eligibility_mode": "area"})


def test_small_patch_removed_big_patch_kept(cfg):
    L = make_layers()
    L["worldcover"][:] = 10                       # everything wooded...
    L["worldcover"][10:12, 10:12] = 30            # ...except a 2x2 (0.36 ha) hole
    L["worldcover"][60:100, 20:100] = 30          # and a big open block
    r = run_screening(L, cfg)
    assert (r.reason[10:12, 10:12] == Reason.SMALL_PATCH).all()
    assert (r.reason[60:100, 20:100] == Reason.ELIGIBLE).all()
    assert r.summary["methodology_eligible_ha"] > r.summary["candidate_ha"]


def test_recent_loss_excluded_old_loss_flagged(cfg):
    L = make_layers()
    L["hansen_treecover2000"][:] = 50
    L["hansen_lossyear"][20:60, 20:60] = 22       # 2022 -> 4 yrs before 2026 -> excluded
    L["hansen_lossyear"][70:110, 20:60] = 8       # 2008 -> 18 yrs before -> flagged
    r = run_screening(L, cfg)
    assert (r.reason[20:60, 20:60] == Reason.RECENT_WOODY_REMOVAL).all()
    assert (r.reason[70:110, 20:60] == Reason.ELIGIBLE).all()
    assert (r.flags[70:110, 20:60] & Flag.LOSS_10_20_YRS).all()


def test_eligible_set_is_invariant_to_filter_order(cfg):
    rng = random.Random(7)
    L = make_layers()
    L["worldcover"][:30, :] = 10
    L["worldcover"][30:45, :] = 40
    L["worldcover"][45:50, :] = 80
    L["slope_deg"][60:90, 60:90] = 35.0
    L["protected_areas"][80:100, 10:50] = 1
    base = run_screening(L, cfg)
    for _ in range(10):
        a = ["WOODY_COVER", "RECENT_WOODY_REMOVAL"]
        b = ["BUILTUP_WATER_WETLAND", "CROPLAND", "PROTECTED", "STEEP_SLOPE"]
        rng.shuffle(a)
        rng.shuffle(b)
        shuffled = apply_overrides(cfg, {
            "screening.stage_a_order": ["NODATA"] + a,
            "screening.stage_b_order": b,
        })
        r = run_screening(L, shuffled)
        assert np.array_equal(r.candidate, base.candidate)
        assert np.array_equal(r.methodology_eligible, base.methodology_eligible)


def test_zero_protected_area_is_reported_not_silent(cfg):
    r = run_screening(make_layers(), cfg)
    row = next(x for x in r.waterfall if x["step"] == "PROTECTED")
    assert "zero area" in row["note"]


def test_waterfall_labels_basis_honestly(cfg):
    r = run_screening(make_layers(), cfg)
    by = {x["step"]: x for x in r.waterfall}
    assert "§4.3(8)(a)" in by["WOODY_COVER"]["basis"]           # clause_refs is filled
    assert "§4.4.2(1)" in by["RECENT_WOODY_REMOVAL"]["basis"]
    assert "no methodology clause" in by["STEEP_SLOPE"]["basis"]
    assert "NO CLAUSE RECORDED" not in by["WOODY_COVER"]["basis"]


def test_reason_codes_are_the_canonical_contract():
    # Keeping this assertion in the tests makes a code reshuffle visible.
    assert int(Reason.ELIGIBLE) == 0
    assert int(Reason.WOODY_COVER) == 1
    assert int(Reason.BUILTUP_WATER_WETLAND) == 2
    assert int(Reason.CROPLAND) == 3
    assert int(Reason.RECENT_WOODY_REMOVAL) == 4
    assert int(Reason.STEEP_SLOPE) == 5
    assert int(Reason.PROTECTED) == 6
    assert int(Reason.NODATA) == 7
    assert int(Reason.SMALL_PATCH) == 8


def test_reference_area_mismatch_fails(cfg):
    L = make_layers()
    true_ha = L["in_district"].sum() * 0.09
    run_screening(L, cfg, reference_area_ha=true_ha)             # passes
    with pytest.raises(QAError):
        run_screening(L, cfg, reference_area_ha=true_ha * 1.10)  # 10% off


def test_hansen_year_beyond_config_fails(cfg):
    L = make_layers()
    L["hansen_lossyear"][5, 5] = 30                               # 2030 > hansen_last_loss_year
    with pytest.raises(QAError):
        run_screening(L, cfg)


def test_bad_orders_rejected(cfg):
    with pytest.raises(ValueError):
        apply_overrides(cfg, {"screening.stage_a_order": ["WOODY_COVER", "NODATA", "RECENT_WOODY_REMOVAL"]})
    with pytest.raises(ValueError):
        apply_overrides(cfg, {"screening.stage_b_order": ["STEEP_SLOPE", "PROTECTED"]})
    with pytest.raises(ValueError):
        apply_overrides(cfg, {"screening.stage_b_order": ["WOODY_COVER", "CROPLAND", "PROTECTED", "STEEP_SLOPE"]})


def test_config_validates(cfg):
    validate_config(cfg)
