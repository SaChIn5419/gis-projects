#!/usr/bin/env python3
"""H2b building source: stream Google Open Buildings v3 polygons for Wayanad.

Source: Google Open Buildings v3 (inference on imagery up to May 2023),
distributed as per-S2-cell gzip CSVs (no header) from Google's public bucket:
  https://storage.googleapis.com/open-buildings-data/v3/
    polygons_s2_level_6_gzip_no_header/{cell_token}_buildings.csv.gz
Columns (documented, no header row):
  latitude, longitude, area_in_meters, confidence, geometry(WKT), full_plus_code
Licence: CC BY 4.0 (Google Open Buildings terms of use).

Wayanad district (geoBoundaries ADM2 = AOI) spans 75.7742-76.4443 E /
11.4515-11.9781 N; the four level-6 S2 cells covering it (padded by ~1.2 km so
all 1 km H2b(b) buffer spills are included) are computed at runtime with
s2sphere and fetched only if a cell file exists (200). Raw streams are NOT
stored: rows are filtered to the district+pad window on the fly, and each raw
gzip stream is sha256-hashed in flight for provenance.

Outputs:
  data/processed/buildings_google_wayanad_32643.gpkg   (EPSG:32643, layer
      buildings_google; fields: cell, lat, lon, area_m2, confidence, plus_code)
  outputs/qaqc/h2b_google_buildings_fetch_facts_{date}.json   per-cell shas
"""
import csv
import gzip
import hashlib
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from s2sphere import CellId, LatLng, LatLngRect, RegionCoverer

ROOT = Path(__file__).resolve().parents[1]
BASE = ("https://storage.googleapis.com/open-buildings-data/v3/"
        "polygons_s2_level_6_gzip_no_header")

# District + pad (>=1.2 km) window; covers every H2b(b) 1 km buffer spill.
KEEP_BBOX = (75.76, 11.44, 76.46, 11.99)  # lon_min, lat_min, lon_max, lat_max
CHUNK = 200_000

TODAY = date.today().isoformat()
OUT_GPKG = ROOT / "data/processed/buildings_google_wayanad_32643.gpkg"
OUT_FACTS = ROOT / f"outputs/qaqc/h2b_google_buildings_fetch_facts_{TODAY}.json"
COLS = ["latitude", "longitude", "area_in_meters", "confidence",
        "geometry", "full_plus_code"]

csv.field_size_limit(1 << 24)  # WKT rings can be long


def covering_cells():
    r = RegionCoverer()
    r.min_level = r.max_level = 6
    rect = LatLngRect.from_point_pair(
        LatLng.from_degrees(KEEP_BBOX[1], KEEP_BBOX[0]),
        LatLng.from_degrees(KEEP_BBOX[3], KEEP_BBOX[2]))
    return [c.to_token() for c in r.get_covering(rect)]


def stream_cell(token, tmp_path):
    """Stream one cell: hash raw gzip in-flight, filter rows to window.

    Returns (n_kept, raw_sha256, raw_bytes, n_rows_seen). Writes kept rows
    verbatim (valid CSV lines) with the cell token as an extra first column.
    Raw streams are never stored.
    """
    url = f"{BASE}/{token}_buildings.csv.gz"
    sha = hashlib.sha256()
    raw_bytes = 0
    n_rows = 0
    n_kept = 0
    lon0, lat0, lon1, lat1 = KEEP_BBOX
    req = urllib.request.Request(url, headers={"User-Agent": "tourism-observatory-research"})
    resp = urllib.request.urlopen(req, timeout=120)

    class _Tee:
        def __init__(self, fh, h):
            self.fh, self.h, self.n = fh, h, 0

        def read(self, size=-1):
            b = self.fh.read(size)
            if b:
                self.h.update(b)
                self.n += len(b)
            return b

        def readinto(self, b):
            n = self.fh.readinto(b)
            if n:
                self.h.update(memoryview(b)[:n])
                self.n += n
            return n

    tee = _Tee(resp, sha)
    with gzip.GzipFile(fileobj=tee) as zp, \
            io.TextIOWrapper(zp, encoding="utf-8") as txt, \
            open(tmp_path, "w", encoding="utf-8") as out:
        for line in txt:  # one CSV row per line; keep original quoting intact
            n_rows += 1
            f0, _, rest = line.partition(",")
            f1, _, _ = rest.partition(",")
            try:
                lat = float(f0); lon = float(f1)
            except ValueError:
                continue
            if lon0 <= lon <= lon1 and lat0 <= lat <= lat1:
                out.write(token + "," + line)
                n_kept += 1
            if n_rows % 5_000_000 == 0:
                print(f"    {token}: {n_rows/1e6:.0f}M rows, kept {n_kept:,}",
                      flush=True)
    resp.close()
    return n_kept, sha.hexdigest(), tee.n, n_rows


def main():
    tokens = covering_cells()
    print(f"level-6 cells covering district+pad: {tokens}")
    tmp_dir = ROOT / "data/raw/staging_h2b"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cell_facts = []
    frames = []
    for tok in tokens:
        tmp = tmp_dir / f"gob_{tok}_filtered.csv"
        print(f"  streaming {tok} ...", flush=True)
        try:
            n_kept, raw_sha, raw_n, n_rows = stream_cell(tok, tmp)
        except Exception as exc:  # noqa: BLE001 - 404 = cell without file
            if "404" in str(exc):
                print(f"    {tok}: no file (404) - cell has no buildings")
                cell_facts.append({"cell": tok, "status": "404-absent"})
                continue
            raise
        print(f"    {tok}: rows {n_rows:,}, kept {n_kept:,}, "
              f"raw {raw_n/1e6:.1f} MB, sha {raw_sha[:16]}")
        cell_facts.append({"cell": tok, "status": "ok", "rows_seen": n_rows,
                           "rows_kept": n_kept, "raw_gzip_bytes": raw_n,
                           "raw_gzip_sha256": raw_sha,
                           "source_url": f"{BASE}/{tok}_buildings.csv.gz"})
        if n_kept:
            df = pd.read_csv(tmp, header=None,
                             names=["cell"] + COLS, dtype={"cell": str},
                             quoting=csv.QUOTE_MINIMAL)
            frames.append(df)
        tmp.unlink()  # filtered temp no longer needed once parsed

    if not frames:
        print("no rows kept - aborting", file=sys.stderr)
        return 1
    big = pd.concat(frames, ignore_index=True)
    del frames
    print(f"total kept rows: {len(big):,}")
    gdf = gpd.GeoDataFrame(
        big.rename(columns={"area_in_meters": "area_m2",
                            "full_plus_code": "plus_code"})
           [["cell", "latitude", "longitude", "area_m2", "confidence",
             "plus_code"]],
        geometry=shapely.from_wkt(big["geometry"].to_numpy()),
        crs="EPSG:4326").to_crs("EPSG:32643")
    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    gdf.to_file(OUT_GPKG, layer="buildings_google", driver="GPKG")
    gpkg_sha = hashlib.sha256(OUT_GPKG.read_bytes()).hexdigest()
    print(f"gpkg -> {OUT_GPKG.name}: {len(gdf)} buildings, sha {gpkg_sha[:16]}")

    facts = {
        "date": TODAY,
        "purpose": "H2b building register (prereg H2b: buildings from Google "
                   "Open Buildings + OSM)",
        "dataset": "Google Open Buildings v3 polygons (S2 level-6 cells)",
        "licence": "CC BY 4.0",
        "inference_vintage": "imagery up to May 2023 (v3 release)",
        "bucket": "gs://open-buildings-data/v3/polygons_s2_level_6_gzip_no_header",
        "keep_window_lonlat": list(KEEP_BBOX),
        "keep_window_note": "district + >=1.2 km pad (covers all 1 km H2b(b) "
                            "buffer spills); exact district/footprint "
                            "selection happens in the H2b analysis",
        "cells": cell_facts,
        "gpkg_path": str(OUT_GPKG.relative_to(ROOT.parent)),
        "gpkg_sha256": gpkg_sha,
        "feature_count": int(len(gdf)),
        "confidence_min": round(float(gdf.confidence.min()), 4),
        "confidence_max": round(float(gdf.confidence.max()), 4),
        "confidence_ge_0.5": int((gdf.confidence >= 0.5).sum()),
        "confidence_ge_0.7": int((gdf.confidence >= 0.7).sum()),
        "total_area_km2": round(float(gdf.area_m2.sum() / 1e6), 3),
        "columns_note": "fields per Google v3 CSV: latitude, longitude, "
                        "area_in_meters, confidence, geometry(WKT), "
                        "full_plus_code; raw streams hashed in flight, not "
                        "stored",
    }
    OUT_FACTS.parent.mkdir(parents=True, exist_ok=True)
    OUT_FACTS.write_text(json.dumps(facts, indent=1))
    print(f"facts -> {OUT_FACTS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
