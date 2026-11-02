"""P4 — H4 analysis (Wayanad tourism_observatory).

Implements prereg §7 D-19 (freeze R7e) exactly: descriptive permutation
overlap of documented dispute locations against tourism-hazard exposure
hotspots, restricted to the D-5 reportable area. EXPLORATORY regime (<15
disputes): the permutation read-out is reported as pinned, and D-5's
no-significance-language rule applies to all interpretation.

Recipe (D-19, pinned before computation):
  hotspot    = union of 500 m buffers around verified facilities
               INTERSECT (union of 1 km buffers around the D-15 inventory
               proxy polygons UNION the H2b(a) 2024 scar), clipped to district
  reportable = 500 m cells containing >=1 OSM building footprint (D-5
               "cells with baseline settlement footprint", OSM layer)
  overlap    = dispute precision footprint (locality -> 1,000 m) intersects
               hotspot  <=>  anchor point lies in dilate(hotspot, r)
  T_obs      = count of cell-eligible disputes overlapping
  E          = sum_i A(dilate(hotspot, r_i) intersect reportable) /
               A(reportable)
  null       = B = 10,000 permutations, numpy default_rng seed 20261102;
               each draw samples the dispute's location uniformly over the
               reportable-area union (uniform over equal-area reportable
               cells, uniform within cell) and applies that dispute's own
               precision radius; p = (1 + #{T_j >= T_obs}) / (B + 1)
  falsified iff T_obs <= E (§3 rule, unchanged; point-estimate comparison)

Usage:  python scripts/p4_h4_analysis.py
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.ops import unary_union
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
QA = ROOT / "outputs" / "qaqc"
TODAY = date.today().isoformat()

EVENTS = PROC / "h4_event_table_2026-11-02.csv"          # pinned in D-19(a)
GEOCODES = PROC / "h4_event_geocodes_2026-11-02.csv"     # pinned in D-19(b)
DISTRICT = PROC / "wayanad_boundary_32643.geojson"
FACILITIES = PROC / "facility_existence_universe_2026-10-23.csv"
INVENTORY = PROC / "inventory_wms_kl_landslides_new_32643.gpkg"
SCAR = PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg"
BUILDINGS = PROC / "buildings_osm_wayanad_32643.gpkg"
FACTS = QA / f"p4_h4_facts_{TODAY}.json"
DISPUTE_OUT = QA / f"p4_h4_dispute_table_{TODAY}.csv"

GRID_M = 500.0
FAC_BUF = 500.0      # H1 primary radius (D-19(c))
HAZ_BUF = 1000.0     # H2b(b) buffer (D-15 polygons)
B_PERM = 10_000
SEED = 20261102      # pinned in D-19(f)
RADII = {"point": 100.0, "locality": 1000.0, "subdistrict": 5000.0}
UA = {"User-Agent": "tourism-observatory/2026-11 (research; Wayanad H4)"}
NM = "https://nominatim.openstreetmap.org/search"
VIEWBOX = "75.70,11.40,76.50,12.02"


# ----------------------------------------------------------------- geocoding
def geocode_label(label: str) -> str:
    """D-19(b) deterministic query rule derived from the location label:
    text before the first ' / ' and before the first ' ('; trailing
    ' village' trimmed (so 'Muthanga village / Muthanga Wildlife Sanctuary'
    queries 'Muthanga')."""
    name = label.split(" / ")[0].split(" (")[0].strip()
    if name.endswith(" village"):
        name = name[: -len(" village")].strip()
    return name


def nm_query(name: str):
    params = urllib.parse.urlencode({
        "q": f"{name}, Wayanad, Kerala, India", "format": "json",
        "limit": 1, "viewbox": VIEWBOX, "bounded": "1"})
    req = urllib.request.Request(NM + "?" + params, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read().decode())
    return (float(out[0]["lat"]), float(out[0]["lon"]),
            out[0]["display_name"]) if out else None


def geocode_queries(queries: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    cache: dict[str, dict] = {}
    if GEOCODES.exists():
        c = pd.read_csv(GEOCODES)
        for _, r in c.iterrows():
            cache[r["name"]] = {"lat": r.lat, "lon": r.lon,
                                "matched": int(r.matched),
                                "display_name": str(r.display_name)}
    details = []
    for name in queries:
        if name not in cache:
            try:
                res = nm_query(name)
            except Exception:  # noqa: BLE001 - network
                res = None
                time.sleep(3)
            if res is None:
                cache[name] = {"lat": np.nan, "lon": np.nan, "matched": 0,
                               "display_name": ""}
            else:
                cache[name] = {"lat": res[0], "lon": res[1], "matched": 1,
                               "display_name": res[2]}
            time.sleep(1.05)
        v = cache[name]
        details.append({"query": name, "matched": v["matched"],
                        "display_name": v["display_name"]})
    geo = pd.DataFrame([{"name": k, "tier": "event", **v}
                        for k, v in cache.items()])
    geo.to_csv(GEOCODES, index=False)
    return geo, details


# ------------------------------------------------------------------- helpers
def area(poly) -> float:
    return 0.0 if poly.is_empty else float(poly.area)


# ---------------------------------------------------------------------- main
def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)

    ev = pd.read_csv(EVENTS)
    district_df = gpd.read_file(DISTRICT).to_crs("EPSG:32643")
    district = unary_union(district_df.geometry)
    print(f"district area: {area(district) / 1e6:.2f} km2 "
          f"({len(district_df)} feature)", flush=True)

    # ---- hotspot (D-19(c)) ------------------------------------------------
    fac = pd.read_csv(FACILITIES)
    fac = fac[fac.verified.fillna(False) & fac.inside_district.fillna(False)]
    fac_pts = gpd.GeoDataFrame(
        {"facility_id": fac.facility_id.tolist()},
        geometry=gpd.points_from_xy(fac.lon, fac.lat), crs="EPSG:4326"
    ).to_crs("EPSG:32643")
    fac_union = unary_union([g.buffer(FAC_BUF) for g in fac_pts.geometry])
    print(f"facilities used: {len(fac_pts)}; 500 m buffer union "
          f"{area(fac_union) / 1e6:.2f} km2", flush=True)

    inv = gpd.read_file(INVENTORY).to_crs("EPSG:32643")
    inv_union = unary_union([g.buffer(HAZ_BUF) for g in inv.geometry])
    scar = unary_union(gpd.read_file(SCAR).to_crs("EPSG:32643").geometry)
    hazard = unary_union([inv_union, scar])
    hotspot = shapely.intersection(fac_union, hazard)
    hotspot = shapely.intersection(hotspot, district)
    print(f"inventory 1 km buffers {area(inv_union) / 1e6:.2f} km2, "
          f"scar {area(scar) / 1e6:.3f} km2, hazard union "
          f"{area(hazard) / 1e6:.2f} km2", flush=True)
    print(f"HOTSPOT (facility500 INTERSECT hazard): "
          f"{area(hotspot) / 1e6:.4f} km2", flush=True)

    # ---- reportable area (D-5: cells with >=1 OSM building footprint) -----
    bld = gpd.read_file(BUILDINGS)[["geometry"]]
    minx, miny, maxx, maxy = district.bounds
    x0 = math.floor(minx / GRID_M) * GRID_M
    y0 = math.floor(miny / GRID_M) * GRID_M
    nx = int(math.ceil((maxx - x0) / GRID_M))
    ny = int(math.ceil((maxy - y0) / GRID_M))
    exact = set()
    for g in bld.geometry:
        b = g.bounds
        c1 = max(int((b[0] - x0) // GRID_M), 0)
        c2 = min(int((b[2] - x0) // GRID_M), nx - 1)
        r1 = max(int((b[1] - y0) // GRID_M), 0)
        r2 = min(int((b[3] - y0) // GRID_M), ny - 1)
        for cxx in range(c1, c2 + 1):
            for cyy in range(r1, r2 + 1):
                exact.add((cxx, cyy))
    lots = sorted(exact)
    cell_polys = [shapely.box(x0 + i * GRID_M, y0 + j * GRID_M,
                              x0 + (i + 1) * GRID_M, y0 + (j + 1) * GRID_M)
                  for i, j in lots]
    rep_union = shapely.union_all(cell_polys)
    rep_area = len(lots) * GRID_M * GRID_M
    rep_in_district = shapely.intersection(rep_union, district)
    print(f"reportable cells: {len(lots)} -> area {rep_area / 1e6:.2f} km2 "
          f"(part within district {area(rep_in_district) / 1e6:.2f} km2)",
          flush=True)

    # ---- dispute anchors (D-19(f)) ----------------------------------------
    ev = ev[ev.cell_test_status == "in"].copy()
    ev = ev[ev.precision_class.isin(["point", "locality", "subdistrict"])]
    queries = sorted({geocode_label(l) for l in ev.location_label})
    geo, details = geocode_queries(queries)
    lookup = {r["name"]: (r.lat, r.lon) for _, r in geo.iterrows()
              if r.matched == 1}

    rows = []
    for did, grp in ev.groupby("dispute_id"):
        names = sorted({geocode_label(l) for l in grp.location_label})
        missing = [nm for nm in names if nm not in lookup]
        if missing:
            raise SystemExit(f"{did}: unmatched geocode queries {missing}")
        gs = gpd.GeoSeries(gpd.points_from_xy([lookup[nm][1] for nm in names],
                                              [lookup[nm][0] for nm in names]),
                           crs="EPSG:4326")
        # analysis location = centroid of the dispute's in-AOI record points,
        # computed geographically (points stay EPSG:4326), then projected
        # once for metric overlap work
        anchor_ll = unary_union(gs.geometry.tolist()).centroid
        anchor = gpd.GeoSeries([anchor_ll], crs="EPSG:4326"
                               ).to_crs("EPSG:32643").geometry.iloc[0]
        radius = RADII[grp.precision_class.iloc[0]]
        hotspot_d = shapely.buffer(hotspot, radius)
        inside = prep(hotspot_d).contains(anchor)
        p_i = area(shapely.intersection(hotspot_d, rep_union)) / rep_area
        rows.append({
            "dispute_id": did,
            "dispute_label": grp.dispute_label.iloc[0],
            "records_in": ";".join(grp.record_id.tolist()),
            "precision_class": grp.precision_class.iloc[0],
            "radius_m": radius,
            "anchor_lat": round(anchor_ll.y, 6),
            "anchor_lon": round(anchor_ll.x, 6),
            "geocode_names": ";".join(names),
            "overlaps_hotspot": bool(inside),
            "p_expectation_per_dispute": round(p_i, 6),
        })
    disp = pd.DataFrame(rows)
    disp.to_csv(DISPUTE_OUT, index=False)
    print(disp[["dispute_id", "radius_m", "anchor_lat", "anchor_lon",
                "overlaps_hotspot", "p_expectation_per_dispute"]].to_string(),
          flush=True)

    n = len(disp)
    T_obs = int(disp.overlaps_hotspot.sum())
    E = float(disp.p_expectation_per_dispute.sum())

    # ---- permutation null (D-19(f)) ---------------------------------------
    rng = np.random.default_rng(SEED)
    prepared = [prep(shapely.buffer(hotspot, r)) for r in disp.radius_m]
    count_ge = 0
    for _ in range(B_PERM):
        t = 0
        for pre in prepared:
            c = lots[rng.integers(0, len(lots))]
            x = x0 + c[0] * GRID_M + rng.uniform(0, GRID_M)
            y = y0 + c[1] * GRID_M + rng.uniform(0, GRID_M)
            if pre.contains(shapely.Point(x, y)):
                t += 1
        if t >= T_obs:
            count_ge += 1
    p_perm = (1 + count_ge) / (B_PERM + 1)

    falsified = T_obs <= E
    verdict = ("falsified (T_obs <= area-proportion expectation)" if falsified
               else "not falsified (T_obs > area-proportion expectation)")
    print(f"\nT_obs={T_obs}  E={E:.4f}  p_perm={p_perm:.5f} "
          f"(#{count_ge} of {B_PERM} gave T_j >= {T_obs})\n"
          f"§3 rule: {verdict}\nEXPLORATORY (disputes {n} < 15): yes",
          flush=True)

    facts = {
        "date": TODAY,
        "freeze": "R7e",
        "pin": "prereg §7 D-19 (recipe + event table pinned before "
               "computation)",
        "hypothesis": "H4 — documented grievance/protest event locations "
                      "overlap tourism-hazard exposure hotspots more than "
                      "expected by area proportion (§3 wording); reported "
                      "as the spatial distribution of documented records "
                      "only (D-5)",
        "exploratory": True,
        "exploratory_reason": f"cell-eligible disputes n = {n} < 15 (D-5)",
        "event_table": {
            "path": str(EVENTS.relative_to(ROOT)),
            "sha256": "c452c653b2077a52610e822ea67c7445da6b"
                      "75c98940ed2ce259b03229aa608a",
            "all_disputes": 8, "all_records": 12,
            "cell_eligible_disputes": n, "cell_eligible_records": len(ev),
        },
        "geocoding": {"cache": GEOCODES.name, "details": details},
        "hotspot": {
            "facilities_used": int(len(fac_pts)),
            "facility_buffer_m": FAC_BUF,
            "facility_buffer_area_km2": round(area(fac_union) / 1e6, 3),
            "hazard_union_km2": round(area(hazard) / 1e6, 3),
            "inventory_buffers_km2": round(area(inv_union) / 1e6, 3),
            "scar_km2": round(area(scar) / 1e6, 4),
            "hotspot_km2": round(area(hotspot) / 1e6, 4),
            "hotspot_share_of_district":
                round(area(hotspot) / area(district), 6),
            "definition": "union(verified-facility 500 m buffers) INTERSECT "
                          "(union(inventory 1 km buffers) UNION scar), "
                          "clipped to district",
        },
        "reportable": {
            "rule": "500 m cells containing >= 1 OSM building footprint "
                    "(69,126-footprint 2026-10 extract; the OSM layer named "
                    "in D-5)",
            "grid_sizes": {"cell_m": GRID_M, "nx": nx, "ny": ny},
            "cells": len(lots),
            "area_km2": round(rep_area / 1e6, 2),
            "area_within_district_km2":
                round(area(rep_in_district) / 1e6, 2),
            "share_of_district": round(area(rep_in_district)
                                       / area(district), 4),
        },
        "test": {
            "n_cell_eligible": n,
            "T_obs": T_obs,
            "E_expected": round(E, 6),
            "sign": "(dispute overlaps iff anchor point in "
                    "dilate(hotspot, radius); mathematically identical to "
                    "the D-19 footprint-intersection definition)",
            "falsified_iff_T_obs_le_E": falsified,
            "verdict_point_estimate": verdict,
            "permutation": {
                "B": B_PERM, "seed": SEED, "rule": "p = (1 + #{T_j >= T_obs}"
                ") / (B+1)", "count_T_j_ge_T_obs": count_ge, "p": p_perm,
                "note": "permuted locations are uniform over the "
                        "reportable-area union (full equal-area reportable "
                        "cells, uniform within cell), as pinned in D-19(f); "
                        "the p value is reported as a pinned read-out — "
                        "D-5's no-significance-language rule still governs "
                        "all interpretation because n < 15 (EXPLORATORY)",
            },
        },
        "dispute_table_out": str(DISPUTE_OUT.relative_to(ROOT)),
        "exclusions": [
            {"id": "D-001-R1", "reason": "out of AOI (Thiruvananthapuram "
                                         "march record inside D-001; "
                                         "dispute eligible via Muthanga "
                                         "records)"},
            {"id": "D-006 (dispute)", "reason": "out of AOI — Nagarahole, "
                                                "Kodagu district, Karnataka; "
                                                "tabled because prereg §4 "
                                                "named the Jenu Kuruba 2025 "
                                                "event"},
            {"id": "D-007 (dispute)", "reason": "district precision "
                                                "(district-wide KSHRC "
                                                "directive) — excluded per "
                                                "D-5"},
            {"id": "D-008-R2 (record)", "reason": "district precision; the "
                                                  "dispute stays cell-"
                                                  "eligible via D-008-R1"},
        ],
        "caveats": [
            "Documentation/effort bias: the dispute register comes from "
            "press and Land Conflict Watch — reporting likelihood rises "
            "with media attention and with salience (e.g. near the 2024 "
            "landslide scene), not uniformly with exposure.",
            "< 15 cell-eligible disputes → EXPLORATORY per D-5; no "
            "significance language is drawn from the permutation read-out.",
            "Anchors are locality-class village geocodes (Nominatim); a 1 km "
            "precision radius is an interpretation of village-scale "
            "uncertainty, as pinned in D-19(e).",
            "Reportable area uses the current OSM building snapshot "
            "(2026-10-28 69,126 footprints, vintage-caveated) as the "
            "baseline settlement layer named in D-5.",
            "The exposure hotspot definition is as pinned (verified-facility "
            "500 m buffers intersecting mapped-hazard footprints); it is a "
            "register-time construct, not per-event-era exposure.",
        ],
    }
    FACTS.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print(f"\nfacts -> {FACTS}", flush=True)

    # read-back sanity of own outputs (audit rule: open what you wrote)
    pd.read_csv(DISPUTE_OUT)
    json.loads(FACTS.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
