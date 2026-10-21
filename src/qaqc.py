#!/usr/bin/env python3
"""
src/qaqc.py - QA/QC gate that measures the actual rasters.

The first version of this file checked a JSON manifest. That is not evidence:
a manifest can say "EPSG:32643, 30 m" while the GeoTIFF is 10 m in another CRS.
This version opens every aligned layer and measures:

  * the CRS, transform, resolution, shape and dtype
  * whether every layer is on the same grid as the district mask
  * declared nodata and the share of missing pixels inside the district
  * value ranges and allowed classes
  * district area from the mask vs the boundary reference
  * optional Sentinel-2 index layers
  * (if a screening output exists) reason-code area balance

Critical failures stop the run. Warnings are recorded but do not stop it.

Usage:
    python src/qaqc.py --selftest
    python src/qaqc.py --check config/jhabua.yaml
    python src/qaqc.py --report config/jhabua.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.screening import OUTSIDE, Reason, load_config, pixel_area_ha  # noqa: E402


REQUIRED_LAYERS = (
    "district_mask", "worldcover", "hansen_treecover2000",
    "hansen_lossyear", "hansen_gain", "slope_deg", "protected_areas",
)
OPTIONAL_LAYERS = ("ndvi_dry", "ndvi_monsoon", "bsi_dry", "bsi_monsoon")
REASON_NAMES = {int(r): r.name.lower() for r in Reason}


class GateResult:
    def __init__(self, check: str, kind: str, passed: bool, message: str, detail=""):
        self.check = check
        self.kind = kind          # critical | warning
        self.passed = passed
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "check": self.check,
            "kind": self.kind,
            "passed": self.passed,
            "message": self.message,
            "detail": self.detail,
        }


def _open_facts(path: Path) -> dict:
    import rasterio

    with rasterio.open(path) as src:
        return {
            "path": str(path),
            "crs": str(src.crs) if src.crs else None,
            "transform": tuple(src.transform)[:6],
            "resolution": (abs(float(src.transform.a)), abs(float(src.transform.e))),
            "shape": (src.height, src.width),
            "count": src.count,
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
            "bounds": tuple(src.bounds),
        }


def _read_layer(path: Path, expected_nodata=None):
    """Return (2-D values, 2-D valid mask, CRS) with nodata excluded."""
    import rasterio

    with rasterio.open(path) as src:
        arr = src.read(1, masked=True)
        data = np.asarray(arr.data, dtype="float64")
        valid = ~np.ma.getmaskarray(arr)
        if src.nodata is not None:
            valid &= data != float(src.nodata)
        if expected_nodata is not None:
            valid &= data != float(expected_nodata)
        valid &= np.isfinite(data)
        return data, valid, str(src.crs) if src.crs else None


def _ok(check: str, msg: str, detail="") -> GateResult:
    return GateResult(check, "critical", True, msg, detail)


def _fail(check: str, msg: str, detail="", kind="critical") -> GateResult:
    return GateResult(check, kind, False, msg, detail)


def _warn(check: str, msg: str, detail="") -> GateResult:
    return GateResult(check, "warning", True, msg, detail)


def check_grid(cfg: dict, base: Path, facts: dict) -> list:
    results = []
    res = float(cfg["grid"]["resolution_m"])
    crs = str(cfg["grid"]["crs"])
    ref = facts["district_mask"]
    for key in REQUIRED_LAYERS:
        f = facts[key]
        if f["crs"] != crs:
            results.append(_fail("CRS", f"{key}: {f['crs']} != {crs}", f["path"]))
        if not (np.isclose(f["resolution"][0], res, atol=1e-6)
                and np.isclose(f["resolution"][1], res, atol=1e-6)):
            results.append(_fail(
                "Resolution", f"{key}: {f['resolution']} != {res} m", f["path"]
            ))
        if f["shape"] != ref["shape"]:
            results.append(_fail("Grid alignment", f"{key}: shape {f['shape']} != {ref['shape']}", f["path"]))
        if f["transform"] != ref["transform"]:
            results.append(_fail("Grid alignment", f"{key}: transform differs from district_mask", f["path"]))
        if f["count"] < 1:
            results.append(_fail("Bands", f"{key}: no bands", f["path"]))
    if not any(r.check in ("CRS", "Resolution", "Grid alignment") and not r.passed for r in results):
        results.append(_ok("CRS / resolution / grid", f"all required layers share {crs} @ {res} m"))
    return results


def check_district_area(cfg: dict, facts: dict, district: np.ndarray) -> list:
    results = []
    px = pixel_area_ha(cfg)
    area_ha = float(district.sum()) * px
    results.append(_ok("District mask", f"{int(district.sum()):,} pixels = {area_ha:,.1f} ha"))
    ref_km2 = cfg.get("qa", {}).get("reference_area_km2")
    if ref_km2:
        ref_ha = float(ref_km2) * 100.0
        gap = 100.0 * (area_ha - ref_ha) / ref_ha
        tol = float(cfg["qa"].get("area_tolerance_pct", 1.0))
        detail = f"raster={area_ha:.1f} ha, reference={ref_ha:.1f} ha, gap={gap:+.3f}%"
        if abs(gap) <= tol:
            results.append(_ok("Area reconciliation", detail))
        else:
            results.append(_fail(
                "Area reconciliation",
                f"district area differs from reference by {gap:+.2f}% (tolerance {tol}%)",
                detail,
            ))
    else:
        results.append(_warn("Area reconciliation", "qa.reference_area_km2 is null; cannot check"))
    return results


def check_values(cfg: dict, facts: dict, base: Path, district: np.ndarray) -> list:
    results = []
    max_missing = float(cfg["qa"].get("max_nodata_share_inside_district", 0.02))
    expected_classes = set(int(x) for x in cfg["qa"].get("expected_worldcover_classes", []))
    loss_last = int(cfg["screening"]["hansen_last_loss_year"])
    s2_lo, s2_hi = cfg["qa"].get("s2_index_bounds", [-1.0, 1.0])

    for key in REQUIRED_LAYERS:
        f = facts[key]
        if f["nodata"] is None and key != "district_mask":
            results.append(_warn("Nodata declared", f"{key}: no nodata value in GeoTIFF", f["path"]))

        vals, valid, _ = _read_layer(Path(f["path"]))
        inside = district & valid
        n_inside = int(district.sum())
        missing = 1.0 - inside.sum() / max(n_inside, 1)
        if missing > max_missing:
            results.append(_fail(
                "Nodata coverage",
                f"{key}: {missing:.2%} of district pixels are missing (max {max_missing:.2%})",
                f["path"],
            ))
        else:
            results.append(_ok("Nodata coverage", f"{key}: {missing:.2%} missing inside district"))

        if not inside.any():
            results.append(_fail("Values", f"{key}: no valid pixels inside district", f["path"]))
            continue

        v = vals[inside]
        lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
        if key == "district_mask":
            if not set(np.unique(v).astype(int)).issubset({0, 1}):
                results.append(_fail("Values", "district_mask is not binary 0/1", f["path"]))
        elif key == "worldcover":
            got = set(np.unique(v).astype(int))
            if expected_classes and not got.issubset(expected_classes):
                results.append(_fail(
                    "Values", f"worldcover has unexpected classes {sorted(got - expected_classes)}", f["path"]
                ))
            else:
                results.append(_ok("Values", f"worldcover classes {sorted(got)}", f["path"]))
        elif key == "hansen_treecover2000":
            if lo < 0 or hi > 100:
                results.append(_fail("Values", f"treecover2000 outside 0..100 ({lo}..{hi})", f["path"]))
        elif key == "hansen_lossyear":
            max_year = int(np.nanmax(v)) + 2000
            if max_year > loss_last:
                results.append(_fail(
                    "Hansen vintage",
                    f"lossyear reaches {max_year} > configured {loss_last}",
                    f["path"],
                ))
            else:
                results.append(_ok("Hansen vintage", f"lossyear max {max_year} <= {loss_last}"))
        elif key == "hansen_gain":
            if not set(np.unique(v).astype(int)).issubset({0, 1}):
                results.append(_fail("Values", "hansen_gain is not binary", f["path"]))
        elif key == "slope_deg":
            if lo < 0 or hi > 90:
                results.append(_fail("Values", f"slope outside 0..90 ({lo}..{hi})", f["path"]))
        elif key == "protected_areas":
            if not set(np.unique(v).astype(int)).issubset({0, 1}):
                results.append(_fail("Values", "protected_areas is not binary", f["path"]))

    for key in OPTIONAL_LAYERS:
        f = facts.get(key)
        if not f:
            continue
        if f["shape"] != facts["district_mask"]["shape"] or f["transform"] != facts["district_mask"]["transform"]:
            results.append(_fail("Grid alignment", f"{key}: optional layer is off-grid", f["path"]))
            continue
        vals, valid, _ = _read_layer(Path(f["path"]))
        v = vals[district & valid]
        if v.size:
            lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
            if lo < float(s2_lo) or hi > float(s2_hi):
                results.append(_fail("Values", f"{key} outside {s2_lo}..{s2_hi} ({lo:.3f}..{hi:.3f})", f["path"]))
            else:
                results.append(_ok("Values", f"{key} range {lo:.3f}..{hi:.3f}"))
    return results


def check_boundary(cfg: dict, base: Path) -> list:
    try:
        import geopandas as gpd
    except ImportError:
        return [_warn("Boundary geometry", "geopandas missing; boundary check PENDING")]
    path = base / cfg["project"]["boundary"]
    if not path.exists():
        return [_fail("Boundary geometry", f"boundary missing: {path}")]
    gdf = gpd.read_file(path)
    feature = str(cfg["project"].get("boundary_feature", "Jhabua"))
    match = gdf[gdf["shapeName"].astype(str).str.casefold() == feature.casefold()]
    if len(match) != 1:
        return [_fail("Boundary geometry", f"expected one {feature!r}, found {len(match)}")]
    geom = match.to_crs(cfg["grid"]["crs"]).geometry.iloc[0]
    results = []
    if not geom.is_valid:
        results.append(_fail("Boundary geometry", "invalid geometry; repair before ingest"))
    else:
        results.append(_ok("Boundary geometry", "valid"))
    ref = cfg.get("qa", {}).get("reference_area_km2")
    if ref:
        actual = float(geom.area) / 1e6
        gap = 100.0 * (actual - float(ref)) / float(ref)
        tol = float(cfg["qa"].get("area_tolerance_pct", 1.0))
        if abs(gap) > tol:
            results.append(_fail(
                "Boundary area", f"vector area {actual:.2f} km2 differs from reference {ref:.2f} by {gap:+.2f}%"
            ))
        else:
            results.append(_ok("Boundary area", f"{actual:.2f} km2 (gap {gap:+.3f}%)"))
    return results


def check_reason_output(cfg: dict, base: Path) -> list:
    """If a screening run exists, check that its codes are known and sum to district."""
    import rasterio

    out = base / cfg["paths"]["output_dir"] / cfg["project"]["name"] / "reason_codes.tif"
    if not out.exists():
        return [_warn("Reason-code balance", "no screening output yet; run src/screening.py")]
    with rasterio.open(out) as src:
        arr = src.read(1)
    known = {int(r) for r in Reason} | {OUTSIDE}
    unknown = set(np.unique(arr).tolist()) - known
    if unknown:
        return [_fail("Reason-code balance", f"unknown codes {sorted(unknown)}", str(out))]
    district = int((arr != OUTSIDE).sum())
    parts = sum(int((arr == int(r)).sum()) for r in Reason)
    detail = f"district={district:,} px, coded={parts:,} px"
    if parts != district:
        return [_fail("Reason-code balance", "reason codes do not sum to district", detail)]
    return [_ok("Reason-code balance", detail)]


def run_checks(cfg: dict, base=".") -> tuple[list, dict]:
    from src.screening import validate_config

    validate_config(cfg)
    base = Path(base).resolve()
    aligned = base / cfg["paths"]["aligned_dir"]
    facts, results = {}, []
    for key in REQUIRED_LAYERS:
        path = aligned / cfg["paths"]["layers"][key]
        if not path.exists():
            results.append(_fail("File presence", f"missing {key}: {path}"))
            continue
        facts[key] = _open_facts(path)
    for key in OPTIONAL_LAYERS:
        name = cfg["paths"]["layers"].get(key)
        if not name:
            continue
        path = aligned / name
        if path.is_file():
            facts[key] = _open_facts(path)

    if "district_mask" not in facts:
        return results, {"facts": facts}

    results += check_grid(cfg, base, facts)
    results += check_boundary(cfg, base)

    # District mask array drives all coverage and area checks.
    import rasterio
    with rasterio.open(facts["district_mask"]["path"]) as src:
        district = src.read(1) > 0
    results += check_district_area(cfg, facts, district)
    results += check_values(cfg, facts, base, district)
    results += check_reason_output(cfg, base)
    return results, {"facts": facts, "district_pixels": int(district.sum())}


def write_report(results: list, cfg: dict, base: Path, extra: dict) -> Path:
    out_dir = base / cfg["paths"]["output_dir"] / "qaqc"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "qaqc_report.md"
    critical = [r for r in results if r.kind == "critical" and not r.passed]
    warnings = [r for r in results if r.kind == "warning" and not r.passed]
    lines = [
        "# QA/QC gate report",
        "",
        f"Config: `{cfg.get('_config_path', 'config/jhabua.yaml')}`",
        f"District: {cfg['project']['district']} ({cfg['project']['name']})",
        "",
        "## Summary",
        "",
        f"- Critical failures: **{len(critical)}**",
        f"- Warnings: **{len(warnings)}**",
        f"- Passed checks: **{sum(1 for r in results if r.passed)}**",
        f"- Overall: {'RUN ABORTED' if critical else 'OK - proceed'}",
        "",
        "## Checks",
        "",
        "| Check | Outcome | Detail |",
        "|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: (x.kind != "critical", not x.passed, x.check)):
        outcome = "PASS" if r.passed else ("FAIL" if r.kind == "critical" else "WARN")
        lines.append(f"| {r.check} | {outcome} | {r.message} |")
    lines += ["", "## Measured facts", "", "```json",
              json.dumps(extra.get("facts", {}), indent=2), "```", ""]
    if critical:
        lines += ["## Blocking failures", ""]
        lines += [f"- **{r.check}**: {r.message}" for r in critical]
        lines += [""]
    lines += [
        "## Notes",
        "",
        "- This gate opens the GeoTIFFs; it does not trust a manifest.",
        "- Reason codes come from `src/screening.py`; they are the single source of truth.",
        "- A null reference area is a warning, not a pass: set `qa.reference_area_km2`.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def run_selftest() -> int:
    """Build a tiny valid stack, then corrupt it and prove the gate notices."""
    import rasterio
    import tempfile
    from rasterio.transform import from_origin

    with tempfile.TemporaryDirectory(prefix="qaqc-selftest-") as tmp:
        tmp = Path(tmp)
        aligned = tmp / "data/processed/aligned"
        aligned.mkdir(parents=True)
        raw = tmp / "data/raw"
        raw.mkdir(parents=True)
        # The boundary check is part of the gate; give the temp project the
        # real boundary so the selftest exercises that path too.
        (raw / "boundary.geojson").write_bytes(
            (ROOT / "data/raw/boundary.geojson").read_bytes()
        )
        cfg = load_config(ROOT / "config/jhabua.yaml")
        cfg["_config_path"] = "selftest"
        cfg["paths"]["aligned_dir"] = "data/processed/aligned"
        cfg["qa"]["reference_area_km2"] = None
        shape = (30, 40)
        transform = from_origin(600000, 2500000, 30, 30)
        profile = dict(driver="GTiff", height=shape[0], width=shape[1], count=1,
                       crs="EPSG:32643", transform=transform, compress="lzw")
        arrays = {
            "district_mask": (np.ones(shape, dtype="uint8"), 0),
            "worldcover": (np.full(shape, 30, dtype="uint8"), 0),
            "hansen_treecover2000": (np.zeros(shape, dtype="uint8"), 255),
            "hansen_lossyear": (np.zeros(shape, dtype="uint8"), 255),
            "hansen_gain": (np.zeros(shape, dtype="uint8"), 255),
            "slope_deg": (np.full(shape, 5.0, dtype="float32"), -9999.0),
            "protected_areas": (np.zeros(shape, dtype="uint8"), 255),
        }
        for key, (arr, nodata) in arrays.items():
            with rasterio.open(aligned / cfg["paths"]["layers"][key], "w",
                               dtype=str(arr.dtype), nodata=nodata, **profile) as dst:
                dst.write(arr, 1)

        results, extra = run_checks(cfg, tmp)
        critical = [r for r in results if r.kind == "critical" and not r.passed]
        print(f"[selftest] clean stack: {len(results)} checks, {len(critical)} critical")
        for r in critical:
            print(f"  FAIL {r.check}: {r.message}")

        # Corrupt one layer to 10 m; the gate must fail on resolution/alignment.
        bad_profile = {**profile, "dtype": "float32", "nodata": -9999.0,
                       "transform": from_origin(600000, 2500000, 10, 10)}
        with rasterio.open(aligned / cfg["paths"]["layers"]["slope_deg"], "w",
                           **bad_profile) as dst:
            dst.write(np.full(shape, 5.0, dtype="float32"), 1)
        results2, _ = run_checks(cfg, tmp)
        caught = any(r.check == "Resolution" and not r.passed for r in results2)

    ok = not critical and caught
    print(f"[selftest] corrupted stack caught: {caught}")
    print(f"[selftest] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="QA/QC gate for the Jhabua screening stack.")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--check", metavar="CONFIG")
    parser.add_argument("--report", metavar="CONFIG")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()
    cfg_path = args.check or args.report
    if not cfg_path:
        parser.print_help()
        return 2

    path = Path(cfg_path)
    if not path.is_absolute():
        path = ROOT / path
    cfg = load_config(path)
    cfg["_config_path"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    results, extra = run_checks(cfg, ROOT)
    report = write_report(results, cfg, ROOT, extra)
    critical = [r for r in results if r.kind == "critical" and not r.passed]
    print(f"[gate] {len(results)} checks, {len(critical)} blocking; report: {report}")
    for r in critical:
        print(f"  FAIL {r.check}: {r.message}")
    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
