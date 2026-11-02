#!/usr/bin/env python3
"""P3 H2b — event-exposure registers (descriptive, not a significance test).

Frozen recipe (prereg D-2 H2b + D-15 pins, "H2b stays descriptive (a)+(b)"):
exposure register of facilities, buildings (Google Open Buildings + OSM) and
OSM roads within
  (a) the published 2024 Chooralmala-Mundakkai scar footprint
      (digitized NRSC VAP3 impact-map outline), and
  (b) 1 km buffers around the proxy inventory polygons
      (D-15 substitution for "Atlas digitized landslide points").
Every entry carries the footprint-source precision class, and spatial
uncertainty is reported alongside counts as the count range under a footprint
boundary perturbation of +/- the class's positional uncertainty
(a: +/-15 m georeferencing; b: +/-10 m = 1 px WMS boundary).

No p-values, no null models: H2b is a descriptive register by design.
Interpretation guard (D-2): counts are *exposure* of the mapped stock inside
mapped footprints, not risk; the (b) proxy excludes the Jul-2024 event and
presumes documentation bias; building vintages (GOB imagery <= May 2023; OSM
snapshot 2026-10-26) mix pre/post event stock.

Outputs:
  outputs/qaqc/p3_h2b_facts_{date}.json
  outputs/qaqc/h2b_facility_exposure_register_{date}.csv
"""
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"
QA = ROOT / "outputs/qaqc"
TODAY = date.today().isoformat()

PRECISION_A = ("digitized NRSC impact-map outline (VAP3 31-Jul-2024, ~1.6 m/px, "
               "graticule georeferencing +/-15 m; 150 m corridor buffer)")
PRECISION_B = ("WMS-render polygonized (10 m px, +/-1 px boundary; "
               "no attributes/vintage)")
JITTER_A_M = 15.0
JITTER_B_M = 10.0


def load_footprints():
    scar = gpd.read_file(PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg")
    scar_u = unary_union(scar.geometry.to_crs("EPSG:32643").values)
    inv = gpd.read_file(PROC / "inventory_wms_kl_landslides_new_32643.gpkg")
    inv_u = unary_union(inv.geometry.to_crs("EPSG:32643").values)
    buf_u = inv_u.buffer(1000.0)  # 1 km around the proxy polygons (D-15)
    return scar_u, buf_u, len(inv)


def register_facilities(fp, tag, fac_gdf):
    hit = fac_gdf[fac_gdf.geometry.intersects(fp)].copy()
    hit["dist_m"] = hit.geometry.distance(fp)
    return hit


def register_buildings(fp, tag, gob, osm):
    jitter = JITTER_A_M if tag == "a_scar_2024" else JITTER_B_M
    out = {}
    for name, gdf in (("google", gob), ("osm", osm)):
        inter = gdf.geometry.intersects(fp)
        sub = gdf[inter]
        area_in = sub.geometry.intersection(fp).area.sum()
        d = {
            "count": int(inter.sum()),
            "area_inside_km2": round(float(area_in / 1e6), 4),
        }
        if name == "google":
            d["count_confidence_ge_0.7"] = int((sub.confidence >= 0.7).sum())
        # spatial uncertainty: count range under +/- boundary jitter
        lo = int(gdf.geometry.intersects(fp.buffer(-jitter)).sum())
        hi = int(gdf.geometry.intersects(fp.buffer(jitter)).sum())
        d["count_jitter_pm_m"] = jitter
        d["count_jitter_range"] = [lo, hi]
        out[name] = d
    return out


def register_roads(fp, tag, roads):
    jitter = JITTER_A_M if tag == "a_scar_2024" else JITTER_B_M
    inter = roads.geometry.intersects(fp)
    sub = roads[inter]
    length_in = sub.geometry.intersection(fp).length.sum()
    by_class = sub.groupby("highway").geometry.apply(
        lambda s: round(float(s.intersection(fp).length.sum() / 1000), 3)
    ).sort_values(ascending=False)
    lo = float(roads[roads.geometry.intersects(fp.buffer(-jitter))]
               .geometry.intersection(fp.buffer(-jitter)).length.sum() / 1000)
    hi = float(roads[roads.geometry.intersects(fp.buffer(jitter))]
               .geometry.intersection(fp.buffer(jitter)).length.sum() / 1000)
    return {
        "segments_intersecting": int(inter.sum()),
        "length_inside_km": round(float(length_in / 1000), 3),
        "length_inside_by_highway_km": {k: v for k, v in by_class.items()},
        "length_jitter_pm_m": jitter,
        "length_jitter_range_km": [round(lo, 3), round(hi, 3)],
    }


def main():
    scar_u, buf_u, n_inv_polys = load_footprints()
    footprints = {
        "a_scar_2024": {
            "union": scar_u,
            "precision_class": PRECISION_A,
            "source": "digitized NRSC VAP3 (Charter Call 1029, 31/07/2024) "
                      "debris-flow outline; scar_chooralmala_mundakkai_2024_32643.gpkg",
            "event": "2024 Chooralmala-Mundakkai",
        },
        "b_inventory_buffers_1km": {
            "union": buf_u,
            "precision_class": PRECISION_B,
            "source": f"1 km buffer around {n_inv_polys} proxy polygons; "
                      "inventory_wms_kl_landslides_new_32643.gpkg (D-15/D-17a)",
            "event": "pre-Jul-2024 mapped inventory (Jul-2024 event EXCLUDED)",
        },
    }

    fac = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")
    fac = fac[fac.verified.fillna(False) & fac.inside_district.fillna(False)].copy()
    fac_gdf = gpd.GeoDataFrame(
        fac, geometry=gpd.points_from_xy(fac.lon, fac.lat), crs="EPSG:4326"
    ).to_crs("EPSG:32643")

    gob = gpd.read_file(PROC / "buildings_google_wayanad_32643.gpkg")
    osm = gpd.read_file(PROC / "buildings_osm_wayanad_32643.gpkg")
    roads = gpd.read_file(PROC / "roads_wayanad_32643.gpkg")

    facts = {
        "date": TODAY,
        "hypothesis": "H2b — event exposure (descriptive register; no "
                      "significance test by design, prereg D-2 + D-15)",
        "footprints": {},
        "caveats": [
            "(b) proxy excludes the Jul-2024 event (see H2a log / D-15): the "
            "two footprints cover different event populations and must not be "
            "merged into one exposure number.",
            "Documentation bias presumed for (b) (mapped-landslide density "
            "near roads/settlements); counts are exposure of the MAPPED "
            "stock, never risk.",
            "Building vintages: Google Open Buildings v3 = imagery up to "
            "May 2023 (pre-event stock); OSM snapshot 2026-10-26 (mixed, "
            "partly post-event rebuild).",
            "Facility set = 107/123 registry entries verified inside the "
            "district (existence-verified universe, same as H1/H2a).",
        ],
    }
    reg_rows = []
    for tag, fp in footprints.items():
        u = fp["union"]
        fac_hit = register_facilities(u, tag, fac_gdf)
        for _, r in fac_hit.iterrows():
            reg_rows.append({
                "footprint": tag, "facility_id": r.facility_id, "name": r["name"],
                "d2_category": r.get("d2_category"), "lat": r.lat, "lon": r.lon,
                "dist_m": round(float(r.dist_m), 2),
                "precision_class": fp["precision_class"],
            })
        facts["footprints"][tag] = {
            "precision_class": fp["precision_class"],
            "source": fp["source"],
            "event_population": fp["event"],
            "union_area_km2": round(float(u.area / 1e6), 4),
            "facilities": {
                "count": int(len(fac_hit)),
                "facility_ids": sorted(fac_hit.facility_id.tolist()),
                "note": "points intersect the footprint union; dist_m is the "
                        "exact planar distance (0 inside)",
            },
            "buildings": register_buildings(u, tag, gob, osm),
            "roads_osm": register_roads(u, tag, roads),
        }
        fb = facts["footprints"][tag]
        print(f"{tag}: area {u.area/1e6:.3f} km2 | facilities {len(fac_hit)} | "
              f"GOB {fb['buildings']['google']['count']} | "
              f"OSM bldg {fb['buildings']['osm']['count']} | "
              f"road km {fb['roads_osm']['length_inside_km']}")

    QA.mkdir(parents=True, exist_ok=True)
    reg = pd.DataFrame(reg_rows)
    reg_path = QA / f"h2b_facility_exposure_register_{TODAY}.csv"
    reg.to_csv(reg_path, index=False)
    facts_path = QA / f"p3_h2b_facts_{TODAY}.json"
    facts_path.write_text(json.dumps(facts, indent=1))
    print(f"register -> {reg_path.relative_to(ROOT)} ({len(reg)} rows)")
    print(f"facts -> {facts_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
