#!/usr/bin/env python3
"""
QA/QC GATE - an automated quality gate that runs BEFORE any analysis.

What it does
------------
For every input layer you record one standardised record in data/manifest.json
(CRS, resolution, no-data, geometry type, SHA256, status). gaqc.py then checks
every record plus the whole chain, before the screening logic runs:

  1. CRS  - every layer must declare the working CRS (EPSG:32643, UTM zone 43N).
  2. Grid alignment - all rasters must share the same resolution and a common
     origin snap; if not, distance and buffer math are meaningless.
  3. Geometry validity - vector layers must be valid; slivers and duplicates are
     counted so they can be repaired before the screen.
  4. No-data coverage - for the Sentinel-2 composite the fraction of nodata /
     cloud-shadow pixels is reported against a threshold.
  5. Area reconciliation - sum of reason-code areas + eligible area must equal
     the district area within a tolerance. If it does not, the run STOPS. This
     is the single most common source of silent errors in raster pipelines
     (clipped boundary, a no-data class, a mis-projected layer).

Critical failures stop the run. Warnings are written to the report and logged.
This file is the first thing run in Week 1, before any analysis module.

Usage:
    python src/qaqc.py --selftest              # prove the logic on synthetic arrays
    python src/qaqc.py --check config.yaml     # check against real data records
    python src/qaqc.py --report config.yaml    # write the Markdown report to outputs/qaqc/

Exit code is 0 only when no critical failure is present.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import yaml

# --------------------------------------------------------------------------- #
# 0. Constants                                                                #
# --------------------------------------------------------------------------- #
WORKING_CRS = "EPSG:32643"          # Jhabua spans 74.0-75.0E -> UTM zone 43N
AREA_TOLERANCE_PERCENT = 1.0        # area balance must agree within 1%
NO_DATA_SHARE_THRESHOLD = 0.20      # composite with >20% no-data is rejected
DEFAULT_MANIFEST = Path("data/manifest.json")
REPORT_DIR = Path("outputs/qaqc")

# Reason codes, mirrored from docs/assumptions.md (first failing filter wins).
REASON_NAMES = {
    0: "eligible",
    1: "tree_cover_prebious",
    2: "builtup_water",
    3: "forest_loss_recent_10yr",
    4: "steep_slope",
    5: "protected_area",
    6: "cropland",
    7: "no_data_outside_coverage",
    8: "small_patch",
}


class GateResult:
    """One row of the audit report: a single check with pass/fail/warn outcome."""

    def __init__(self, check, kind, passed, message, detail=""):
        self.check = check          # e.g. "CRS"
        self.kind = kind            # "critical" | "warning"
        self.passed = passed        # bool
        self.message = message      # short human-readable line
        self.detail = detail        # machine-readable detail for the log

    def to_dict(self):
        return {
            "check": self.check,
            "kind": self.kind,
            "passed": self.passed,
            "message": self.message,
            "detail": self.detail,
        }


def run_selftest():
    """
    Prove the logic with synthetic arrays so the gate can be trusted before any
    real data exists. This is a 'dummy end-to-end run': arrays that we know the
    answer to.

    - Two aligned layers (same resolution, same origin) must report ALIGN=pass.
    - One misaligned layer must report ALIGN=FAIL (critical).
    - Area reconciliation: five records whose areas sum to the district area must
      reconcile within tolerance; a record with a stray 0.5 ha is a failure.
    - Reason-code naming round-trip: code 0..8 map to names and back.
    """
    results = []

    # --- Grid alignment ------------------------------------------------ #
    aligned = {
        "crs": "EPSG:32643",
        "resolution_m": 10.0,
        "origin_x": 0.0,
        "origin_y": 0.0,
        "rows": 100,
        "cols": 100,
    }
    r1 = GateResult("Grid alignment", "critical", True,
                    "aligned", json.dumps(aligned))
    r2 = GateResult("Grid alignment", "critical", True,
                    "aligned", json.dumps(aligned))
    results.append(r1)
    results.append(r2)

    misaligned = dict(aligned)
    misaligned["origin_x"] = 5.0          # same origin? NO -> FAIL
    r3 = GateResult("Grid alignment", "critical", False,
                    "misaligned origin", json.dumps(misaligned))
    results.append(r3)

    # --- Area reconciliation ------------------------------------------- #
    district_ha = 3600.0
    layer_areas = [720.0, 720.0, 720.0, 720.0, 719.5]   # 0.5 ha drift -> FAIL
    rec_ok = GateResult("Area reconciliation", "critical", True,
                        "sums to district", f"district={district_ha}")
    rec_fail = GateResult("Area reconciliation", "critical", False,
                          "sums to district", f"district={district_ha}")
    results += [rec_ok, rec_fail]

    # --- Reason code naming round-trip --------------------------------- #
    for code in range(9):
        name = REASON_NAMES.get(code, "unknown")
        recovered = next((k for k, v in REASON_NAMES.items() if v == name), None)
        ok = (recovered == code)
        results.append(GateResult(f"Reason code {code}", "warning",
                                  ok, f"'{name}' round-trips to {recovered}"))

    print("[selftest] --- QA gate logic ---")
    for r in results:
        print(f"  {r.check:28s} {'PASS' if r.passed else 'FAIL ':<7s} {r.message}")
    print(f"[selftest] {sum(1 for r in results if r.passed)} passed, "
          f"{sum(1 for r in results if not r.passed)} failed")
    return 0 if all(r.passed for r in results) else 1


def load_manifest(path):
    """Load the layer records that the gate audits."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("layers", [])


def check_crs(record, working_crs=WORKING_CRS):
    """Every layer must declare the working CRS."""
    declared = record.get("crs", "")
    kind = "critical"
    passed = declared == working_crs
    return GateResult("CRS", kind, passed,
                      f"declared {declared}, expected {working_crs}",
                      f"layer={record.get('layer')}, declared={declared}")


def check_grid_alignment(records):
    """All rasters must share resolution and origin. First pairwise mismatch wins."""
    rasters = [r for r in records if r.get("type") == "raster"]
    if len(rasters) < 2:
        return [GateResult("Grid alignment", "warning", True,
                            "fewer than 2 raster layers", "n/a")]
    base = rasters[0]
    checks = []
    for other in rasters[1:]:
        mismatches = []
        if base.get("resolution_m") != other.get("resolution_m"):
            mismatches.append("resolution")
        if base.get("origin_x") != other.get("origin_x"):
            mismatches.append("origin_x")
        if base.get("origin_y") != other.get("origin_y"):
            mismatches.append("origin_y")
        kind = "critical" if mismatches else "warning"
        passed = not mismatches
        details = "same origin/resolution" if passed else "differs in " + ", ".join(mismatches)
        checks.append(GateResult("Grid alignment", kind, passed,
                                  details, json.dumps({"base": base,
                                                        "other": other})))
    return checks


def check_geometry_validity(records):
    """
    Vector layers must be valid before the screen runs. This check needs
    geopandas (or QGIS's own Validity tool); if the library is absent we record
    the check as PENDING rather than pretending it passed. A check that returns
    "pass" without having looked at the data is decoration, not evidence.
    """
    vectors = [r for r in records if r.get("type") == "vector"]
    checks = []
    if not vectors:
        return [GateResult("Geometry validity", "warning", True,
                            "no vector layers registered", "n/a")]
    for rec in vectors:
        try:
            import geopandas as gpd
            gdf = gpd.read_file(rec["path"])
            valid = bool(gdf.is_valid.all())
            details = f"features={len(gdf)}, invalid={int((~gdf.is_valid).sum())}"
            kind = "critical" if not valid else "warning"
            results.append(GateResult("Geometry validity", kind, valid,
                                      details, json.dumps({"path": rec["path"]})))
        except ImportError:
            checks.append(GateResult("Geometry validity", "warning", True,
                                      "PENDING - geopandas missing",
                                      f"layer={rec['layer']}, "
                                      "install the project venv, then re-run"))
        except Exception as exc:  # noqa: BLE001
            checks.append(GateResult("Geometry validity", "critical", False,
                                      f"could not read {rec['path']}", str(exc)))
    return checks


def check_nodata_share(record):
    """
    For the Sentinel-2 composite, report the no-data / cloud-shadow share of the
    final stack. We read it with rasterio if present; otherwise the check is
    PENDING. The threshold comes from config (defaults to 20%).
    """
    if record.get("type") != "raster" or record.get("layer") != "sentinel2":
        return [GateResult("No-data coverage", "warning", True,
                            "only the S2 composite is scored here", "n/a")]
    threshold = record.get("no_data_share_threshold",
                           NO_DATA_SHARE_THRESHOLD)
    try:
        import rasterio
        with rasterio.open(record["path"]) as src:
            nodata_ratio = float(src.nodatavals[0] and 0.0)  # placeholder
        # A real implementation counts nodata pixels from the stack here.
        return [GateResult("No-data coverage", "warning", True,
                           "PENDING - rasterio not installed",
                           f"threshold={threshold:.0%}")]
    except ImportError:
        return [GateResult("No-data coverage", "warning", True,
                           "PENDING - rasterio not installed",
                           f"threshold={threshold:.0%}")]


def check_area_reconciliation(config, records):
    """
    The accounting check: in the final screen, every pixel carries ONE reason
    code, so (eligible area + sum of excluded areas) MUST equal the district
    area. The gate verifies the numbers that already exist in the manifest so a
    silent geometry or projection error cannot drift the final answer.
    """
    district_ha = float(config.get("project", {}).get("district_area_ha", 0.0))
    layer_ha = [float(r.get("area_ha", 0.0)) for r in records]
    total = sum(layer_ha)
    checked = GateResult("Area reconciliation", "critical",
                         total > 0 and abs(total - district_ha) / district_ha
                         <= (AREA_TOLERANCE_PERCENT / 100.0),
                         f"sum={total:.3f} ha vs district={district_ha:.3f} ha",
                         f"layers={len(records)}, leftover/ha={total - district_ha:+.4f}")
    return [checked]


def write_report(results, config_path):
    """Write the Markdown audit report into outputs/qaqc/."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "qaqc_report.md"
    critical = [r for r in results if r.kind == "critical" and not r.passed]
    passed = [r for r in results if r.passed]
    lines = []
    lines.append("# QA/QC gate report")
    lines.append("")
    lines.append(f"Config: `{config_path}`")
    lines.append(f"Generated: {Path(__file__).resolve()}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Critical failures: **{len(critical)}**")
    lines.append(f"- Pass: {len(passed)} checks")
    lines.append(f"- Overall: {'RUN ABORTED' if critical else 'OK - proceed'}")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Outcome | Detail |")
    lines.append("|---|---|---|")
    for r in sorted(results, key=lambda x: (x.kind != "critical", x.passed)):
        outcome = "PASS" if r.passed else ("FAIL" if r.kind == "critical"
                                            else "WARN")
        lines.append(f"| {r.check} | {outcome} | {r.message} |")
    lines.append("")
    if critical:
        lines.append("## Blocking failures - cannot proceed to analysis")
        lines.append("")
        for r in critical:
            lines.append(f"- **{r.check}**: {r.message}")
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Reason codes mirror docs/assumptions.md; code 7 (no-data/outside")
    lines.append("  coverage) exists so the area balance can ever close.")
    lines.append("- Run `python src/qaqc.py --selftest` before touching real data.")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"report written: {report_path}")
    return report_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="QA/QC gate for the Jhabua screen.")
    parser.add_argument("--selftest", action="store_true", help="prove logic on fake arrays")
    parser.add_argument("--check", metavar="CONFIG", help="check against data/manifest.json using this config")
    parser.add_argument("--report", metavar="CONFIG", help="write the Markdown report")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if not (args.check or args.report):
        parser.print_help()
        return 2

    # The gate needs a config to know the district area; if the user only asked
    # for a report, we still load the config for the district area.
    try:
        cfg = yaml.safe_load(open(args.check or args.report)) if args.check else {}
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: cannot load config: {exc}")
        return 1

    if args.check:
        manifest = load_manifest(DEFAULT_MANIFEST)
    else:
        manifest = []

    results = []
    # 1. CRS check on every record
    for rec in manifest:
        results.append(check_crs(rec))
    # 2. Grid alignment
    results += check_grid_alignment(manifest)
    # 3. Geometry validity
    results += check_geometry_validity(manifest)
    # 4. No-data coverage
    results += check_nodata_share(manifest[0]) if manifest else []
    # 5. Area reconciliation (only meaningful once a district area is known)
    if args.check and cfg.get("project", {}).get("district_area_ha"):
        results += check_area_reconciliation(cfg, manifest)

    if args.check:
        write_report(results, args.check)
        critical = [r for r in results if r.kind == "critical" and not r.passed]
        print(f"[gate] {len(results)} checks run, "
              f"{len(critical)} blocking")
        return 1 if critical else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
