"""P1 ingest — Wayanad boundary (tourism_observatory).

Jhabua convention: open the ACTUAL file on disk (never trust manifests/screenshots),
verify the expected feature exists, reproject to the analysis CRS, compute QA facts,
and emit the processed boundary plus QA output for the manifest.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "geoBoundaries-IND-ADM2_simplified.geojson"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "wayanad_boundary_32643.geojson"

EXPECTED_ID = "IND-ADM2-76128533"          # geoBoundaries API metadata, pinned commit 9469f09


def main() -> int:
    if not RAW.exists() or RAW.stat().st_size < 1_000_000:
        print(f"FAIL: raw file missing or implausibly small: {RAW}")
        return 1

    gdf = gpd.read_file(RAW)
    n_total = len(gdf)

    if "shapeName" not in gdf.columns:
        print(f"FAIL: shapeName column absent; columns={list(gdf.columns)}")
        return 1

    # Wayanad is unique among Kerala ADM2 names; match case-insensitively but require
    # exactly one hit to avoid silently grabbing a same-named feature elsewhere.
    hits = gdf[gdf["shapeName"].str.strip().str.lower() == "wayanad"]
    if len(hits) != 1:
        print(f"FAIL: expected exactly one Wayanad feature, got {len(hits)}; "
              f"candidates={list(gdf[gdf['shapeName'].str.contains('aya', case=False)]['shapeName'].unique())[:10]}")
        return 1

    row = hits.iloc[[0]].copy()
    props = {k: row.iloc[0][k] for k in row.columns if k != "geometry"}
    crs_raw = gdf.crs

    # CRS decision (dev-D-9(c) OI-3): check the district's longitudinal extent first,
    # then confirm the UTM zone rather than assuming it.
    raw_bounds = row.total_bounds  # lon_min, lat_min, lon_max, lat_max (EPSG:4326)
    lon_min, lon_max = raw_bounds[0], raw_bounds[2]

    gdf33 = row.to_crs("EPSG:32643")
    area_km2 = float(gdf33.geometry.area.sum()) / 1e6

    zone_of_extent = 30 + int((lon_min + lon_max) / 2 // 6) + 1
    print("QA — boundary ingest")
    print(f"  source file      : {RAW.name}")
    print(f"  row top-level    : {props}")
    print(f"  raw CRS          : {crs_raw}")
    print(f"  lon extent       : {lon_min:.4f} … {lon_max:.4f} E")
    print(f"  UTM zone by centroid rule: {zone_of_extent} (expected 43)")
    print(f"  feature count (district) : {len(row)}")
    print(f"  area km2 @ EPSG:32643    : {area_km2:.3f}")

    if zone_of_extent != 43:
        print(f"FAIL: extent implies UTM zone {zone_of_extent}, not 43 — resolve before proceeding")
        return 1
    if not (1500 < area_km2 < 3000):
        # Wayanad ~2,131 km2; loose sanity band to catch wrong-feature extraction
        print(f"FAIL: area {area_km2:.1f} km2 outside sanity band for Wayanad (≈2,131 km2)")
        return 1
    if not (75.5 <= lon_min and lon_max <= 76.8):
        print(f"FAIL: longitude extent {lon_min:.2f}–{lon_max:.2f} does not match Wayanad (≈75.6–76.6 E)")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf33.to_file(OUT, driver="GeoJSON")

    qa = {
        "source_path": str(RAW.relative_to(OUT.parents[2])),
        "processed_path": str(OUT.relative_to(OUT.parents[2])),
        "boundary_id": EXPECTED_ID,
        "properties": {k: v for k, v in props.items()},
        "raw_crs": str(crs_raw),
        "utm_zone_confirmed": 43,
        "analysis_crs": "EPSG:32643",
        "area_km2": round(area_km2, 3),
        "lon_extent": [round(lon_min, 4), round(lon_max, 4)],
    }
    print(json.dumps(qa, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
