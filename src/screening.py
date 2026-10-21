"""
screening.py - staged exclusion waterfall with per-pixel reason codes.

Two stages, reported separately on purpose:

  STAGE A  methodology + data validity   -> "methodology-eligible" area
  STAGE B  project design screens        -> "candidate" area (after small-patch removal)

Stage-B codes (builtup/water, cropland, protected, slope, small patch) are design,
safeguard or transaction-cost choices. They do NOT cite a methodology clause, and
the waterfall says so in its `basis` column.

Core functions are pure (arrays + config dict in, arrays out) so the sensitivity
module can call run_screening() hundreds of times with overridden settings.

All input layers must already share one grid (same CRS, shape, transform).
That is ingest.py / qaqc.py's job; load_layers() only guards against mismatch.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage


# --------------------------------------------------------------------------- codes
class Reason(IntEnum):
    ELIGIBLE = 0
    WOODY_COVER = 1
    BUILTUP_WATER_WETLAND = 2
    CROPLAND = 3
    RECENT_WOODY_REMOVAL = 4
    STEEP_SLOPE = 5
    PROTECTED = 6
    NODATA = 7
    SMALL_PATCH = 8


OUTSIDE = 255  # pixel outside the district: never counted in any area


class Flag(IntFlag):
    """Data-confidence flags on candidate pixels. Flags are NOT exclusions."""
    SHRUBLAND = 1             # woody biomass may exceed the threshold unseen
    LOSS_10_20_YRS = 2        # tree loss 10-20 yrs ago; regrowth state uncertain
    CROPLAND_KEPT = 4         # cropland passed; cropland mask is unvalidated


# Membership is fixed in code (it is a statement about what each rule IS).
# Config only controls the order inside each stage.
STAGE_A = ("NODATA", "WOODY_COVER", "RECENT_WOODY_REMOVAL")
STAGE_B = ("BUILTUP_WATER_WETLAND", "CROPLAND", "PROTECTED", "STEEP_SLOPE")

REQUIRED_LAYERS = (
    "district_mask", "worldcover", "hansen_treecover2000",
    "hansen_lossyear", "hansen_gain", "slope_deg", "protected_areas",
)
NODATA_LAYERS = (
    "worldcover", "hansen_treecover2000", "hansen_lossyear", "hansen_gain",
    "slope_deg", "protected_areas",
)


class QAError(RuntimeError):
    """Raised when an integrity check fails. Do not 'fix' by loosening checks."""


# --------------------------------------------------------------------------- config
def load_config(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    mode = cfg["project"]["eligibility_mode"]
    if mode not in ("census", "area"):
        raise ValueError(f"eligibility_mode must be 'census' or 'area', got {mode!r}")
    if mode == "area":
        # The area-based route is not a variation of the census screen. Under
        # VM0047 §1.1/§4.4.1 it needs evidence that existing forest was not
        # managed for wood products in the past 10 years, that clearing did not
        # involve timber harvesting/native-ecosystem degradation, and that
        # planting density is not silently using the census route. None of those
        # datasets exist in this repository. Refusing is safer than reporting a
        # number produced by the wrong rule.
        raise NotImplementedError(
            "area-based eligibility is not implemented: it needs managed-forest, "
            "timber-harvest and native-ecosystem evidence that this project does "
            "not have. Run with eligibility_mode: census, or implement §1.1/§4.4.1 "
            "before reporting area-mode hectares."
        )

    s = cfg["screening"]
    a, b = list(s["stage_a_order"]), list(s["stage_b_order"])
    if sorted(a) != sorted(STAGE_A):
        raise ValueError(f"stage_a_order must list exactly {STAGE_A}; got {a}")
    if sorted(b) != sorted(STAGE_B):
        raise ValueError(f"stage_b_order must list exactly {STAGE_B}; got {b}")
    if a[0] != "NODATA":
        raise ValueError("NODATA must be first in stage_a_order so the area balance closes")

    w = s["woody"]
    if w["source"] not in ("worldcover", "hansen", "either"):
        raise ValueError("woody.source must be worldcover | hansen | either")
    if w["shrubland"] not in ("flag", "exclude"):
        raise ValueError("woody.shrubland must be flag | exclude")
    if not 0 < float(w["threshold_pct"]) <= 100:
        raise ValueError("woody.threshold_pct must be in (0, 100]")

    d = s["design_screens"]
    if d["patch_connectivity"] not in (4, 8):
        raise ValueError("patch_connectivity must be 4 or 8")
    if set(d["exclude_cropland"]) != {"census", "area"}:
        raise ValueError("design_screens.exclude_cropland needs both 'census' and 'area'")
    lo, hi = s["flag_loss_window_years"]
    if lo >= hi:
        raise ValueError("flag_loss_window_years must be [low, high] with low < high")


def apply_overrides(cfg: dict, overrides: dict) -> dict:
    """Deep-copy cfg and set dotted-path overrides, e.g.
    {"screening.woody.threshold_pct": 30, "project.eligibility_mode": "area"}.
    Used by the sensitivity module for structural variants."""
    out = copy.deepcopy(cfg)
    for dotted, value in overrides.items():
        node = out
        *parents, leaf = dotted.split(".")
        for key in parents:
            node = node[key]
        if leaf not in node:
            raise KeyError(f"override path not in config: {dotted}")
        node[leaf] = value
    validate_config(out)
    return out


def pixel_area_ha(cfg: dict, layers: dict | None = None) -> float:
    """Area of one pixel in hectares.

    When load_layers() has measured the real transform it stores
    ``_pixel_area_ha`` on the layer dict. Pure-array callers (tests, sensitivity)
    fall back to the configured resolution. This prevents a 10 m stack being
    priced as if it were 30 m.
    """
    if layers is not None and "_pixel_area_ha" in layers:
        return float(layers["_pixel_area_ha"])
    res = float(cfg["grid"]["resolution_m"])
    return res * res / 10_000.0


# --------------------------------------------------------------------------- rejecters
# Each returns a boolean array: True where the filter REJECTS the pixel.
def _loss_calendar_year(lossyear: np.ndarray) -> np.ndarray:
    return np.where(lossyear > 0, 2000 + lossyear.astype(np.int32), 0)


def woody_mask(layers: dict, cfg: dict) -> np.ndarray:
    """True where pre-existing woody cover is judged >= threshold at project start.
    PROXY: canopy cover (Hansen) and/or WorldCover tree class; see config limitation."""
    s = cfg["screening"]
    w = s["woody"]
    start = cfg["project"]["start_year"]
    loss_year = _loss_calendar_year(layers["hansen_lossyear"])
    lost_by_start = (loss_year > 0) & (loss_year <= start)

    classes = list(w["worldcover_classes"])
    if w["shrubland"] == "exclude":
        classes.append(w["shrubland_worldcover_class"])
    wc_woody = np.isin(layers["worldcover"], classes)

    canopy_now = np.where(lost_by_start, 0, layers["hansen_treecover2000"])
    hansen_woody = canopy_now >= float(w["threshold_pct"])
    if w["treat_hansen_gain_as_woody"]:
        hansen_woody |= layers["hansen_gain"].astype(bool)

    src = w["source"]
    if src == "worldcover":
        return wc_woody
    if src == "hansen":
        return hansen_woody
    return wc_woody | hansen_woody


def recent_removal_mask(layers: dict, cfg: dict) -> np.ndarray:
    """Hansen loss inside the look-back window, on pixels that carried canopy."""
    s = cfg["screening"]
    start = cfg["project"]["start_year"]
    loss_year = _loss_calendar_year(layers["hansen_lossyear"])
    had_canopy = layers["hansen_treecover2000"] >= float(s["woody"]["threshold_pct"])
    age = start - loss_year
    return (loss_year > 0) & (loss_year <= start) & (age <= s["recent_removal_years"]) & had_canopy


def _cropland_excluded(cfg: dict) -> bool:
    return bool(cfg["screening"]["design_screens"]["exclude_cropland"][cfg["project"]["eligibility_mode"]])


def build_rejecters(layers: dict, cfg: dict) -> dict:
    d = cfg["screening"]["design_screens"]
    wc = layers["worldcover"]
    zeros = np.zeros(wc.shape, dtype=bool)
    return {
        "NODATA": layers["nodata"],
        "WOODY_COVER": woody_mask(layers, cfg),
        "RECENT_WOODY_REMOVAL": recent_removal_mask(layers, cfg),
        "BUILTUP_WATER_WETLAND": np.isin(wc, d["builtup_water_wetland_classes"]),
        "CROPLAND": (wc == d["cropland_worldcover_class"]) if _cropland_excluded(cfg) else zeros,
        "PROTECTED": layers["protected_areas"].astype(bool),
        "STEEP_SLOPE": layers["slope_deg"] > float(d["max_slope_deg"]),
    }


# --------------------------------------------------------------------------- core
def apply_filters(rejecters: dict, order: list, in_district: np.ndarray) -> np.ndarray:
    """First failing filter wins. Returns uint8 reason raster (OUTSIDE=255)."""
    reason = np.full(in_district.shape, OUTSIDE, dtype=np.uint8)
    reason[in_district] = Reason.ELIGIBLE
    for name in order:
        newly = rejecters[name] & (reason == Reason.ELIGIBLE)
        reason[newly] = Reason[name]
    return reason


def _structure(connectivity: int):
    return np.ones((3, 3), dtype=int) if connectivity == 8 else None


def patch_stats(mask: np.ndarray, px_ha: float, connectivity: int) -> dict:
    lab, n = ndimage.label(mask, structure=_structure(connectivity))
    if n == 0:
        return {"n_patches": 0, "total_ha": 0.0, "mean_ha": 0.0, "median_ha": 0.0, "max_ha": 0.0}
    sizes = np.bincount(lab.ravel())[1:] * px_ha
    return {
        "n_patches": int(n),
        "total_ha": float(sizes.sum()),
        "mean_ha": float(sizes.mean()),
        "median_ha": float(np.median(sizes)),
        "max_ha": float(sizes.max()),
    }


def remove_small_patches(reason: np.ndarray, cfg: dict) -> np.ndarray:
    d = cfg["screening"]["design_screens"]
    min_px = math.ceil(float(d["min_patch_ha"]) / pixel_area_ha(cfg))
    lab, n = ndimage.label(reason == Reason.ELIGIBLE, structure=_structure(d["patch_connectivity"]))
    if n == 0:
        return reason
    small = np.bincount(lab.ravel()) < min_px
    small[0] = False  # label 0 = background
    out = reason.copy()
    out[small[lab]] = Reason.SMALL_PATCH
    return out


def compute_flags(layers: dict, cfg: dict, candidate: np.ndarray) -> np.ndarray:
    s = cfg["screening"]
    start = cfg["project"]["start_year"]
    lo, hi = s["flag_loss_window_years"]
    loss_year = _loss_calendar_year(layers["hansen_lossyear"])
    age = start - loss_year

    flags = np.zeros(candidate.shape, dtype=np.uint8)
    flags[layers["worldcover"] == s["woody"]["shrubland_worldcover_class"]] |= np.uint8(Flag.SHRUBLAND)
    flags[(loss_year > 0) & (age > lo) & (age <= hi)] |= np.uint8(Flag.LOSS_10_20_YRS)
    if not _cropland_excluded(cfg):
        flags[layers["worldcover"] == s["design_screens"]["cropland_worldcover_class"]] |= np.uint8(Flag.CROPLAND_KEPT)
    flags[~candidate] = 0  # flags describe candidate land only
    return flags


def check_layers(layers: dict, cfg: dict) -> None:
    """Cheap sanity checks that run before screening."""
    shapes = {k: layers[k].shape for k in REQUIRED_LAYERS}
    if len(set(shapes.values())) != 1:
        raise QAError(f"layer shapes differ: {shapes}")
    last = cfg["screening"]["hansen_last_loss_year"]
    ly = layers["hansen_lossyear"]
    if ly.size and int(ly.max()) + 2000 > last:
        raise QAError(
            f"Hansen loss year {int(ly.max()) + 2000} exceeds configured "
            f"hansen_last_loss_year={last}; update the config to the release you downloaded."
        )
    if not layers["in_district"].any():
        raise QAError("district mask is empty")


def check_area_balance(reason: np.ndarray, cfg: dict, reference_area_ha=None,
                       px_ha: float | None = None) -> dict:
    known = {int(r) for r in Reason} | {OUTSIDE}
    unknown = set(np.unique(reason).tolist()) - known
    if unknown:
        raise QAError(f"unknown reason codes in raster: {sorted(unknown)}")
    in_d = int((reason != OUTSIDE).sum())
    parts = sum(int((reason == int(r)).sum()) for r in Reason)
    if parts != in_d:
        raise QAError(f"area does not close: parts={parts} district={in_d}")

    px = float(px_ha) if px_ha is not None else pixel_area_ha(cfg)
    out = {"district_pixels": in_d, "district_ha": in_d * px, "balance": "ok"}
    if reference_area_ha:
        gap = 100.0 * (out["district_ha"] - reference_area_ha) / reference_area_ha
        out["reference_gap_pct"] = gap
        tol = float(cfg["qa"]["area_tolerance_pct"])
        if abs(gap) > tol:
            raise QAError(
                f"raster district area differs from reference by {gap:+.2f}% (tolerance {tol}%). "
                "Check CRS, the district mask, and which boundary the reference came from."
            )
    return out


def build_waterfall(reason: np.ndarray, cfg: dict, notes: dict,
                    px_ha: float | None = None) -> list:
    px = float(px_ha) if px_ha is not None else pixel_area_ha(cfg)
    s = cfg["screening"]
    total = int((reason != OUTSIDE).sum())
    refs = s.get("clause_refs", {}) or {}

    rows, remaining = [], total

    def add(step, stage, code, basis, n):
        nonlocal remaining
        remaining -= n
        note = notes.get(step, "")
        if n == 0 and step not in ("ELIGIBLE",) and not note:
            note = "checked; zero area removed"
        rows.append({
            "step": step, "stage": stage, "code": code, "basis": basis,
            "removed_ha": round(n * px, 3),
            "pct_of_district": round(100.0 * n / total, 3),
            "remaining_ha": round(remaining * px, 3),
            "note": note,
        })

    for name in s["stage_a_order"]:
        basis = refs.get(name) or "NO CLAUSE RECORDED - fill clause_refs after verifying"
        add(name, "A_methodology", int(Reason[name]), basis, int((reason == Reason[name]).sum()))
    rows.append({"step": "METHODOLOGY_ELIGIBLE", "stage": "summary", "code": "", "basis": "",
                 "removed_ha": 0.0, "pct_of_district": round(100.0 * remaining / total, 3),
                 "remaining_ha": round(remaining * px, 3), "note": ""})
    for name in s["stage_b_order"]:
        add(name, "B_design", int(Reason[name]), "project design screen (no methodology clause)",
            int((reason == Reason[name]).sum()))
    add("SMALL_PATCH", "B_design", int(Reason.SMALL_PATCH), "transaction-cost screen (no methodology clause)",
        int((reason == Reason.SMALL_PATCH).sum()))
    rows.append({"step": "CANDIDATE", "stage": "summary", "code": int(Reason.ELIGIBLE), "basis": "",
                 "removed_ha": 0.0, "pct_of_district": round(100.0 * remaining / total, 3),
                 "remaining_ha": round(remaining * px, 3), "note": ""})
    return rows


@dataclass
class ScreeningResult:
    reason: np.ndarray
    flags: np.ndarray
    methodology_eligible: np.ndarray
    candidate: np.ndarray
    waterfall: list
    fragmentation: dict
    qa: dict
    summary: dict = field(default_factory=dict)


def run_screening(layers: dict, cfg: dict, reference_area_ha=None) -> ScreeningResult:
    validate_config(cfg)
    check_layers(layers, cfg)
    s = cfg["screening"]
    px = pixel_area_ha(cfg, layers)
    in_d = layers["in_district"]

    rej = {k: v & in_d for k, v in build_rejecters(layers, cfg).items()}

    # Order-invariant by construction: plain AND of stage-A passes.
    methodology = in_d.copy()
    for name in STAGE_A:
        methodology &= ~rej[name]

    reason = apply_filters(rej, list(s["stage_a_order"]) + list(s["stage_b_order"]), in_d)

    conn = s["design_screens"]["patch_connectivity"]
    frag_before = patch_stats(reason == Reason.ELIGIBLE, px, conn)
    reason = remove_small_patches(reason, cfg)
    candidate = reason == Reason.ELIGIBLE
    frag_after = patch_stats(candidate, px, conn)

    # Attribution must agree with the direct methodology mask.
    stage_a_codes = [int(Reason[n]) for n in STAGE_A]
    rejected_a = int(np.isin(reason, stage_a_codes).sum())
    if rejected_a != int(in_d.sum() - methodology.sum()):
        raise QAError("stage-A attribution disagrees with the methodology-eligible mask")

    qa = check_area_balance(reason, cfg, reference_area_ha, px_ha=px)

    notes = {}
    if not layers["protected_areas"][in_d].any():
        notes["PROTECTED"] = "no protected-area pixels inside district (checked, zero area)"

    flags = compute_flags(layers, cfg, candidate)
    waterfall = build_waterfall(reason, cfg, notes, px_ha=px)

    summary = {
        "mode": cfg["project"]["eligibility_mode"],
        "start_year": cfg["project"]["start_year"],
        "district_ha": qa["district_ha"],
        "methodology_eligible_ha": float(methodology.sum() * px),
        "candidate_ha": float(candidate.sum() * px),
        "candidate_flagged_ha": float((flags > 0).sum() * px),
    }
    return ScreeningResult(
        reason=reason, flags=flags, methodology_eligible=methodology, candidate=candidate,
        waterfall=waterfall,
        fragmentation={"before_patch_removal": frag_before, "after_patch_removal": frag_after},
        qa=qa, summary=summary,
    )


# --------------------------------------------------------------------------- I/O
def load_layers(cfg: dict, base=".") -> tuple[dict, dict]:
    """Read aligned GeoTIFFs. Returns (layers, raster_profile).

    The actual transform is measured here, not trusted from the config. If a
    stack was written at 10 m while the config says 30 m, every hectare would be
    nine times too large; that is a silent failure, so it is a hard QA error.
    """
    import rasterio  # imported here so the pure functions work without it

    folder = Path(base) / cfg["paths"]["aligned_dir"]
    layers, masks, ref, profile = {}, {}, None, None
    for key in REQUIRED_LAYERS:
        path = folder / cfg["paths"]["layers"][key]
        if not path.exists():
            raise QAError(
                f"required aligned layer missing: {path}. Run "
                "`python src/ingest.py config/jhabua.yaml` after placing the raw "
                "sources in data/raw/."
            )
        with rasterio.open(path) as src:
            if src.count < 1:
                raise QAError(f"layer '{key}' has no raster bands: {path}")
            here = (src.crs, src.transform, src.shape)
            if ref is None:
                ref, profile = here, src.profile
            elif here != ref:
                raise QAError(
                    f"layer '{key}' is not on the same grid as the first layer: "
                    f"{here} vs {ref}"
                )
            arr = src.read(1, masked=True)
            masks[key] = np.ma.getmaskarray(arr)
            layers[key] = arr.filled(0)

    expected = rasterio.crs.CRS.from_string(cfg["grid"]["crs"])
    if ref[0] != expected:
        raise QAError(f"raster CRS {ref[0]} != configured {cfg['grid']['crs']}")

    transform = ref[1]
    if not math.isclose(abs(transform.b), 0.0, abs_tol=1e-9) or not math.isclose(
        abs(transform.d), 0.0, abs_tol=1e-9
    ):
        raise QAError(f"rotated/sheared transform is not supported: {transform}")
    configured_res = float(cfg["grid"]["resolution_m"])
    measured_res_x, measured_res_y = abs(transform.a), abs(transform.e)
    for axis, measured in (("x", measured_res_x), ("y", measured_res_y)):
        if not math.isclose(measured, configured_res, rel_tol=1e-6, abs_tol=1e-6):
            raise QAError(
                f"measured {axis} resolution {measured:.6f} m != configured "
                f"{configured_res:.6f} m. Re-run ingest at the configured grid; "
                "do not let a 10 m stack be priced with 30 m pixel areas."
            )

    layers["_transform"] = transform
    layers["_crs"] = ref[0]
    layers["_pixel_area_ha"] = measured_res_x * measured_res_y / 10_000.0
    layers["in_district"] = layers["district_mask"] > 0

    nodata = np.zeros(layers["in_district"].shape, dtype=bool)
    for key in NODATA_LAYERS:
        nodata |= masks[key]
    layers["nodata"] = nodata & layers["in_district"]
    return layers, profile


def write_outputs(result: ScreeningResult, cfg: dict, profile: dict, base=".") -> Path:
    import rasterio

    out = Path(base) / cfg["paths"]["output_dir"] / cfg["project"]["name"]
    out.mkdir(parents=True, exist_ok=True)

    prof = dict(profile)
    prof.update(dtype="uint8", count=1, nodata=OUTSIDE, compress="lzw")
    flags = result.flags.copy()
    flags[result.reason == OUTSIDE] = OUTSIDE
    for name, arr in (("reason_codes.tif", result.reason), ("confidence_flags.tif", flags)):
        with rasterio.open(out / name, "w", **prof) as dst:
            dst.write(arr, 1)

    with open(out / "waterfall.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(result.waterfall[0].keys()))
        writer.writeheader()
        writer.writerows(result.waterfall)

    cfg_text = yaml.safe_dump(cfg, sort_keys=True)
    record = {
        "summary": result.summary,
        "fragmentation": result.fragmentation,
        "qa": result.qa,
        "config_sha256": hashlib.sha256(cfg_text.encode()).hexdigest(),
        "config": cfg,
    }
    with open(out / "run_summary.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, default=str)
    return out


def main(argv=None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Run the staged screening waterfall.")
    ap.add_argument("config")
    ap.add_argument("--base", default=".", help="project root (default: .)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    layers, profile = load_layers(cfg, args.base)
    ref_km2 = cfg["qa"].get("reference_area_km2")
    result = run_screening(layers, cfg, reference_area_ha=ref_km2 * 100 if ref_km2 else None)
    out = write_outputs(result, cfg, profile, args.base)

    s = result.summary
    print(f"mode={s['mode']}  district={s['district_ha']:,.0f} ha")
    print(f"methodology-eligible: {s['methodology_eligible_ha']:,.0f} ha")
    print(f"candidate (after design screens): {s['candidate_ha']:,.0f} ha")
    print(f"outputs written to {out}")


if __name__ == "__main__":
    main()
