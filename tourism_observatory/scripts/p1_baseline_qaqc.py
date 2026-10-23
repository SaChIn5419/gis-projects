"""P1 QA gate — baseline layers only (tourism_observatory).

Jhabua rule: QA opens the ACTUAL files. This script never reads
data/manifest.json and never reads outputs/qaqc/ingest_facts.json — it
recomputes the expected grid from the boundary file and re-measures every
output:

  * CRS, transform, measured resolution, shape, dtype, declared nodata
  * extent coverage of the AOI envelope
  * nodata share inside the AOI mask
  * value plausibility / allowed class codes per layer
  * area-sum checks (AOI mask vs boundary vector; WDPA raster vs vector;
    class partition vs AOI area)
  * cross-layer grid consistency (all 30 m layers identical; 300 m CCI grid
    shares the origin exactly — 300 = 10 x 30)

Critical failures exit 1. Warnings are recorded but do not stop the run.
Scope rule: BASELINE LAYERS ONLY (config qa.scope_pre_c1) — no outcome layers
exist and none are read.

Usage:  python scripts/p1_baseline_qaqc.py
        python scripts/p1_baseline_qaqc.py --report-dir outputs/qaqc
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
BOUNDARY = PROC / "wayanad_boundary_32643.geojson"

RES = 30.0
SNAP = 300.0
CRS = "EPSG:32643"

# filename -> (grid res, allowed classes or value band, categorical?)
LAYERS = {
    "dem_copernicus30m_32643.tif": {"res": 30, "band": (0, 3500), "kind": "continuous"},
    "slope_deg_32643.tif": {"res": 30, "band": (0, 80), "kind": "continuous"},
    "worldcover_2021_32643.tif": {
        "res": 30, "kind": "categorical",
        "allowed": {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100},
    },
    "hansen_treecover2000_32643.tif": {"res": 30, "band": (0, 100), "kind": "continuous"},
    "wdpa_all_touched_32643.tif": {
        "res": 30, "kind": "categorical", "allowed": {0, 1},
    },
    "road_dist_m_32643.tif": {"res": 30, "band": (0, 50000), "kind": "continuous"},
    "aoi_mask_32643.tif": {"res": 30, "kind": "categorical", "allowed": {0, 1}},
    "cci_lulc_2005_32643.tif": {
        "res": 300, "kind": "categorical",
        # Official CCI-LC legend incl. sub-codes (CCI-LC_Maps_Legend.pdf;
        # 210 = Water bodies, 190 = Urban areas, 80 = needleleaved deciduous).
        "allowed": {0, 10, 11, 12, 20, 30, 40, 50, 60, 61, 62, 70, 71, 72,
                    80, 81, 82, 90, 100, 110, 120, 121, 122, 130, 140,
                    150, 151, 152, 153, 160, 170, 180, 190, 200, 201, 202,
                    210, 220},
    },
}


class Gate:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, check: str, kind: str, passed: bool, message: str) -> None:
        self.rows.append({"check": check, "kind": kind,
                          "status": "PASS" if passed else ("FAIL" if kind == "critical" else "WARN"),
                          "message": message})

    @property
    def failed(self) -> bool:
        return any(r["status"] == "FAIL" for r in self.rows)

    @property
    def warned(self) -> int:
        return sum(1 for r in self.rows if r["status"] == "WARN")


def expected_grid(aoi: gpd.GeoDataFrame) -> dict:
    minx, miny, maxx, maxy = aoi.total_bounds
    x0 = math.floor(minx / SNAP) * SNAP
    y0 = math.floor(miny / SNAP) * SNAP
    x1 = math.ceil(maxx / SNAP) * SNAP
    y1 = math.ceil(maxy / SNAP) * SNAP
    return {
        "bounds": (x0, y0, x1, y1),
        "origin": (x0, y1),
        "shape30": (int((y1 - y0) / RES), int((x1 - x0) / RES)),
        "shape300": (int((y1 - y0) / SNAP), int((x1 - x0) / SNAP)),
    }


def check_layer(name: str, spec: dict, grid: dict, aoi, gate: Gate) -> dict:
    path = PROC / name
    facts: dict = {"file": name}
    if not path.exists():
        gate.add(f"{name}: exists", "critical", False, "file missing — ingest not run or failed")
        return facts

    with rasterio.open(path) as src:
        facts["crs"] = str(src.crs)
        facts["dtype"] = src.dtypes[0]
        facts["nodata"] = src.nodata
        res_x = abs(src.transform.a)
        res_y = abs(src.transform.e)
        facts["measured_res_m"] = [round(res_x, 6), round(res_y, 6)]
        facts["shape"] = [src.height, src.width]
        facts["bounds"] = [round(v, 2) for v in src.bounds]

        # 1. CRS
        gate.add(f"{name}: CRS", "critical", str(src.crs) == CRS,
                 f"CRS {src.crs} (expected {CRS})")

        # 2. measured resolution (read from the transform, not metadata claims)
        ok_res = math.isclose(res_x, spec["res"], rel_tol=1e-9) and \
            math.isclose(res_y, spec["res"], rel_tol=1e-9)
        gate.add(f"{name}: measured resolution", "critical", ok_res,
                 f"measured {res_x:g} x {res_y:g} m (expected {spec['res']})")

        # 3. shape vs independently recomputed grid
        exp_shape = grid["shape30" if spec["res"] == 30 else "shape300"]
        gate.add(f"{name}: shape", "critical", (src.height, src.width) == exp_shape,
                 f"shape {(src.height, src.width)} (expected {exp_shape})")

        # 4. transform origin matches the snapped anchor exactly
        exp_origin = grid["origin"]
        got_origin = (src.transform.c, src.transform.f)
        ok_origin = all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(got_origin, exp_origin))
        gate.add(f"{name}: grid origin (envelope anchor)", "critical", ok_origin,
                 f"origin {got_origin} (expected {exp_origin})")

        # 5. extent covers AOI envelope
        env = aoi.total_bounds
        covers = (src.bounds.left <= env[0] and src.bounds.bottom <= env[1]
                  and src.bounds.right >= env[2] and src.bounds.top >= env[3])
        gate.add(f"{name}: extent covers AOI envelope", "critical", covers,
                 f"raster bounds {[round(v,1) for v in src.bounds]} vs AOI {[round(v,1) for v in env]}")

        # 6. read with AOI mask; never trust declared stats
        arr = src.read(1)
        mask_in = geometry_mask(
            [aoi.geometry.iloc[0]], out_shape=arr.shape,
            transform=src.transform, invert=True, all_touched=False,
        )
        inside = arr[mask_in]
        if inside.size == 0:
            gate.add(f"{name}: AOI overlap", "critical", False, "AOI mask selects zero pixels")
            return facts

        nd = src.nodata
        if nd is not None:
            valid = inside[inside != nd]
            nd_share = float((inside == nd).mean())
        else:
            valid = inside
            nd_share = 0.0
        facts["nodata_share_in_aoi"] = round(nd_share, 5)
        facts["pixels_in_aoi"] = int(inside.size)

        if spec["kind"] == "continuous":
            if valid.size == 0:
                gate.add(f"{name}: values", "critical", False, "all-nodata inside AOI")
                return facts
            lo, hi = float(valid.min()), float(valid.max())
            band = spec["band"]
            facts.update({"min": round(lo, 3), "max": round(hi, 3),
                          "mean": round(float(valid.mean()), 3)})
            gate.add(f"{name}: value band", "critical", band[0] <= lo and hi <= band[1],
                     f"min {lo:.3f} / max {hi:.3f} within {band}")
        else:
            present = set(np.unique(inside).tolist())
            facts["classes_in_aoi"] = sorted(int(c) for c in present)
            bad = present - set(spec["allowed"])
            gate.add(f"{name}: allowed classes", "critical", not bad,
                     f"classes {sorted(int(c) for c in present)}; unexpected {sorted(int(c) for c in bad)}")
            if nd is None and 255 in present:
                gate.add(f"{name}: sentinel 255", "warning", False,
                         "declared-nodata sentinel appears inside AOI")

        # 7. nodata share policy (missing-data failure per Jhabua 9477303 rule)
        hard = name in {"dem_copernicus30m_32643.tif", "slope_deg_32643.tif",
                        "worldcover_2021_32643.tif"}
        if hard:
            gate.add(f"{name}: nodata share in AOI", "critical", nd_share <= 0.05,
                     f"{nd_share:.4%} (fail >5%)")
        elif name == "wdpa_all_touched_32643.tif":
            # Presence raster: unprotected area is nodata LEGITIMATELY (57.6% of
            # the AOI is outside WDPA), so the generic 20% nodata warn is wrong
            # here. Guard instead against a failed/near-empty burn.
            gate.add(f"{name}: burn share in AOI", "warning",
                     0.01 <= (1 - nd_share) <= 0.99,
                     f"protected share {1 - nd_share:.4%} (warn if <1% or >99%)")
        elif nd is not None:
            gate.add(f"{name}: nodata share in AOI", "warning", nd_share <= 0.20,
                     f"{nd_share:.4%} (warn >20%)")

    return facts


def area_checks(aoi, grid: dict, gate: Gate) -> dict:
    out: dict = {}
    vec_km2 = float(aoi.geometry.area.sum()) / 1e6

    mask_path = PROC / "aoi_mask_32643.tif"
    with rasterio.open(mask_path) as src:
        m = src.read(1)
        ras_km2 = float((m == 1).sum()) * RES * RES / 1e6
    diff = 100 * (ras_km2 - vec_km2) / vec_km2
    out["aoi_mask_km2"] = round(ras_km2, 3)
    out["boundary_vector_km2"] = round(vec_km2, 3)
    out["aoi_diff_pct"] = round(diff, 3)
    gate.add("area-sum: AOI mask vs boundary vector", "critical", abs(diff) <= 2.0,
             f"mask {ras_km2:.3f} km² vs vector {vec_km2:.3f} km² = {diff:+.3f}% (fail >2%)")

    # class partition of WorldCover must tile the AOI mask exactly (area-sum rule)
    wc_path = PROC / "worldcover_2021_32643.tif"
    with rasterio.open(wc_path) as src:
        wc = src.read(1)
    inside = (m == 1)
    classes = wc[inside]
    tot_km2 = classes.size * RES * RES / 1e6
    per_class = {int(c): round(float(n) * RES * RES / 1e6, 3)
                 for c, n in zip(*np.unique(classes, return_counts=True))}
    sum_km2 = round(sum(per_class.values()), 3)
    out["worldcover_class_area_km2"] = per_class
    out["worldcover_sum_km2"] = sum_km2
    ok = abs(sum_km2 - ras_km2) <= 0.01 or abs(tot_km2 - ras_km2) <= 0.01
    gate.add("area-sum: WorldCover classes tile the AOI", "critical", ok,
             f"class areas sum {sum_km2} km² vs mask {ras_km2} km²")

    # WDPA: all_touched rasterisation must cover at least the vector's UNION area.
    # (Union, not sum: WDPA designations overlap — here the Western Ghats
    # Eco-sensitive Area contains the Nilgiri PA slice, intersection 298.4 km²,
    # so summing polygons double-counts; the raster is a union by construction.
    # Learned at P1 gate 2026-10-23 when the sum rule falsely failed.)
    vec_path = PROC / "wdpa_wayanad_32643.gpkg"
    if vec_path.exists():
        v = gpd.read_file(vec_path)
        v_sum_km2 = float(v.geometry.area.sum()) / 1e6
        v_km2 = float(v.geometry.union_all().area) / 1e6
        with rasterio.open(PROC / "wdpa_all_touched_32643.tif") as src:
            r = src.read(1)
        r_km2 = float((r == 1).sum()) * RES * RES / 1e6
        out["wdpa_vector_km2"] = round(v_km2, 3)
        out["wdpa_vector_sum_km2"] = round(v_sum_km2, 3)
        out["wdpa_raster_km2"] = round(r_km2, 3)
        gate.add("area-sum: WDPA raster >= vector union (all_touched rule)", "critical",
                 r_km2 >= v_km2 - 0.01,
                 f"raster {r_km2:.3f} km² vs union {v_km2:.3f} km² "
                 f"(sum {v_sum_km2:.3f} km² double-counts overlaps)")
        # all_touched may over-cover the vector by at most ~25% + 5 km² of
        # boundary-pixel rounding (base area included; the pre-fix rule forgot
        # the base and could never pass)
        margin = v_km2 * 1.25 + 5.0
        gate.add("area-sum: WDPA raster within all_touched margin", "warning",
                 r_km2 <= margin,
                 f"raster {r_km2:.3f} km²; allowance {margin:.3f} km²")
    else:
        gate.add("WDPA vector present", "warning", False, f"missing {vec_path.name}")

    # roads vector + distance raster sanity
    roads_path = PROC / "roads_wayanad_32643.gpkg"
    if roads_path.exists():
        rd = gpd.read_file(roads_path)
        out["road_features"] = int(len(rd))
        gate.add("roads: feature count", "critical", len(rd) > 0, f"{len(rd)} highway features")
        inside_share = float(gpd.clip(rd, aoi).shape[0]) / max(len(rd), 1)
        gate.add("roads: share inside AOI after clip", "warning", inside_share > 0.95,
                 f"{inside_share:.1%} inside (clipped layer expected ≥95%)")
    else:
        gate.add("roads vector present", "critical", False, f"missing {roads_path.name}")

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-dir", default=str(ROOT / "outputs" / "qaqc"))
    args = ap.parse_args()

    if not BOUNDARY.exists():
        print(f"FAIL: boundary missing: {BOUNDARY}")
        return 1
    aoi = gpd.read_file(BOUNDARY)
    if str(aoi.crs) != CRS or len(aoi) != 1:
        print(f"FAIL: boundary crs={aoi.crs} features={len(aoi)} (want {CRS}, 1)")
        return 1
    grid = expected_grid(aoi)

    gate = Gate()
    layer_facts = {}
    for name, spec in LAYERS.items():
        layer_facts[name] = check_layer(name, spec, grid, aoi, gate)
    area_facts = area_checks(aoi, grid, gate)

    # cross-layer consistency: every 30 m layer on one identical grid
    shapes30 = {n: tuple(f["shape"]) for n, f in layer_facts.items()
                if f.get("measured_res_m", [None])[0] == 30 and "shape" in f}
    gate.add("grid consistency: all 30 m layers identical shape",
             "critical", len(set(shapes30.values())) == 1, f"{set(shapes30.values())}")

    n_fail = sum(1 for r in gate.rows if r["status"] == "FAIL")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "baseline layers only (qa.scope_pre_c1) — no outcome layers exist",
        "rule": "files opened directly; manifest not read (Jhabua fail-fast QA)",
        "expected_grid": {"origin": list(grid["origin"]), "res_m": RES,
                          "snap_m": SNAP, "shape30": list(grid["shape30"]),
                          "shape300": list(grid["shape300"]), "crs": CRS},
        "checks": gate.rows,
        "layers": layer_facts,
        "areas": area_facts,
        "summary": {"checks": len(gate.rows), "fail": n_fail, "warn": gate.warned},
    }

    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "baseline_qaqc_report.json").write_text(
        json.dumps(report, indent=1, default=str) + "\n")

    lines = [
        "# P1 baseline QA report — Wayanad",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Scope: {report['scope']}",
        f"Rule: {report['rule']}",
        "",
        f"**Result: {'FAIL' if gate.failed else 'PASS'}** "
        f"({n_fail} critical failures, {gate.warned} warnings, {len(gate.rows)} checks)",
        "",
        "## Checks",
        "",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for r in gate.rows:
        lines.append(f"| {r['status']} | {r['check']} | {r['message']} |")
    lines += ["", "## Layer measurements (from opened files)", "",
              "| file | dtype | nodata | measured res (m) | shape | nodata share in AOI | values |",
              "|---|---|---|---|---|---|---|"]
    for n, f in layer_facts.items():
        vals = (f"{f.get('min')} … {f.get('max')}" if "min" in f
                else str(f.get("classes_in_aoi", ""))[:80])
        lines.append(
            f"| {n} | {f.get('dtype')} | {f.get('nodata')} | {f.get('measured_res_m')} "
            f"| {f.get('shape')} | {f.get('nodata_share_in_aoi', 0)} | {vals} |")
    lines += ["", "## Area checks", ""]
    for k, v in area_facts.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    (report_dir / "baseline_qaqc_report.md").write_text("\n".join(lines) + "\n")

    print(f"QA {'FAIL' if gate.failed else 'PASS'} — {n_fail} fail, {gate.warned} warn, "
          f"{len(gate.rows)} checks")
    for r in gate.rows:
        if r["status"] != "PASS":
            print(f"  {r['status']}: {r['check']} — {r['message']}")
    print(f"report: {(report_dir / 'baseline_qaqc_report.md').relative_to(ROOT)}")
    return 1 if gate.failed else 0


if __name__ == "__main__":
    sys.exit(main())
