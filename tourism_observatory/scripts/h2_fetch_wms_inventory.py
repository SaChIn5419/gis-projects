#!/usr/bin/env python3
"""H2 inventory proxy: fetch + polygonize Bhuvan WMS landslide layer.

Deviations: the ISRO Landslide Atlas vector inventory does not exist in
any public form (PDF only; Bhuvan WFS disabled; GetFeatureInfo returns empty).
Preregistered H2a(ii)/H2b(b) therefore use a documented substitution: polygons
polygonized from high-resolution tiled GetMap renders of the Bhuvan WMS layer
`disaster:kl_landslides_new` (see prereg section 7, D-15). D-17 refetches the
same layer/protocol over the corrected (district-complete) window.

Technical notes (learned the hard way):
  * WMS 1.3.0 + CRS=EPSG:4326 uses lat,lon axis order; we use WMS 1.1.1 +
    SRS=EPSG:4326 with lon,lat BBOX.
  * Every render carries a fixed-pixel-size "bhuvan" watermark at the tile
    centre (near-black + white pixels). Tiles are fetched with 50% overlap and
    the brown-mask is UNIONED across tiles so the watermark (never brown) is
    replaced by neighbouring tiles' content.

Outputs (all paths relative to project root):
  data/raw/staging_h2/kl_landslides_new_wayanad_mosaic_10m.tif   georeferenced RGBA mosaic (EPSG:4326)
  data/processed/inventory_wms_kl_landslides_new_32643.gpkg      polygonized inventory (EPSG:32643)
  outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json            QA facts incl. VAP8 scar overlap check
"""
import hashlib
import io
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
import rasterio
from rasterio.features import shapes as rio_shapes
from rasterio.transform import from_bounds
from shapely.geometry import shape as shp_shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
LAYER = "disaster:kl_landslides_new"
WMS = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"

# Study window: district extent 75.7742-76.4443 E / 11.4515-11.9781 N
# (geoBoundaries ADM2 = AOI), padded >=0.02 deg on every side. D-17: the
# original 11.20-11.82 N window truncated the district's north strip (16 of
# 107 facilities); refetched over the corrected window.
BBOX = (75.75, 11.42, 76.47, 12.00)  # lon_min, lat_min, lon_max, lat_max
RES_M = 10.0                          # target ground resolution, metres/px
TILE_W, TILE_H = 2048, 1920           # px per tile
STEP_X, STEP_Y = 1024, 960            # 50% overlap -> watermark removal by union
ALPHA_MIN = 16                        # accept pixels with alpha >= 16/255
SLEEP_S = 0.4
RETRIES = 3

TODAY = date.today().isoformat()
OUT_MOSAIC = ROOT / "data/raw/staging_h2/kl_landslides_new_wayanad_mosaic_10m.tif"
OUT_GPKG = ROOT / "data/processed/inventory_wms_kl_landslides_new_32643.gpkg"
OUT_FACTS = ROOT / f"outputs/qaqc/h2_wms_inventory_facts_{TODAY}.json"
SCAR_GPKG = ROOT / "data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg"
BOUNDARY = ROOT / "data/raw/geoBoundaries-IND-ADM2_simplified.geojson"


def pixel_size_deg():
    """Degrees per pixel for the target resolution (10 m) in this window."""
    lat_mid = (BBOX[1] + BBOX[3]) / 2
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat_mid))
    return RES_M / m_per_deg_lon, RES_M / m_per_deg_lat


def grid():
    dlon, dlat = pixel_size_deg()
    total_w = int(round((BBOX[2] - BBOX[0]) / dlon))
    total_h = int(round((BBOX[3] - BBOX[1]) / dlat))
    starts_x = sorted({x for x in range(0, total_w, STEP_X)} |
                      {max(0, total_w - TILE_W)})
    starts_y = sorted({y for y in range(0, total_h, STEP_Y)} |
                      {max(0, total_h - TILE_H)})
    tiles = []
    for sy in starts_y:
        for sx in starts_x:
            w = min(TILE_W, total_w - sx)
            h = min(TILE_H, total_h - sy)
            tiles.append((sx, sy, w, h))
    return total_w, total_h, tiles


def fetch_tile(sx, sy, w, h, total_w, total_h):
    dlon, dlat = pixel_size_deg()
    lon0 = BBOX[0] + sx * dlon
    lon1 = BBOX[0] + (sx + w) * dlon
    lat1 = BBOX[3] - sy * dlat
    lat0 = BBOX[3] - (sy + h) * dlat
    params = {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap",
        "LAYERS": LAYER, "SRS": "EPSG:4326",
        "BBOX": f"{lon0:.7f},{lat0:.7f},{lon1:.7f},{lat1:.7f}",
        "WIDTH": w, "HEIGHT": h,
        "FORMAT": "image/png", "TRANSPARENT": "true",
    }
    url = WMS + "?" + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(RETRIES):
        try:
            data = urllib.request.urlopen(url, timeout=120).read()
            if len(data) < 200:
                raise RuntimeError(f"suspiciously small response ({len(data)}B)")
            return data
        except Exception as exc:  # noqa: BLE001 - network retries
            last_err = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"tile ({sx},{sy}) failed after {RETRIES} tries: {last_err}")


def brown_mask(rgba):
    """Inventory-fill mask: brown family, excluding watermark (black/white)."""
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3]
    return (a >= ALPHA_MIN) & (r - g >= 40) & (g - b >= 15) & (r >= 90) & (r <= 235)


def main():
    from PIL import Image

    total_w, total_h, tiles = grid()
    print(f"grid: {total_w}x{total_h} px, {len(tiles)} tiles")
    mosaic = np.zeros((total_h, total_w), dtype=bool)
    colors = {}
    failures = []

    for i, (sx, sy, w, h) in enumerate(tiles, 1):
        try:
            data = fetch_tile(sx, sy, w, h, total_w, total_h)
        except RuntimeError as exc:
            failures.append(str(exc))
            print(f"  [{i}/{len(tiles)}] FAILED {exc}")
            continue
        arr = np.array(Image.open(io.BytesIO(data)).convert("RGBA"))
        if arr.shape[:2] != (h, w):
            failures.append(f"tile ({sx},{sy}) size {arr.shape[:2]} != {(h, w)}")
            print(f"  [{i}/{len(tiles)}] SIZE MISMATCH {arr.shape[:2]}")
            continue
        m = brown_mask(arr)
        mosaic[sy:sy + h, sx:sx + w] |= m
        # colour histogram of opaque pixels (sampling for speed)
        op = arr[:, :, 3] >= ALPHA_MIN
        if i % 7 == 1 or i == len(tiles):
            cols, cnts = np.unique(arr[op][:, :3], axis=0, return_counts=True)
            for c, n in zip(cols, cnts):
                key = tuple(int(v) for v in c)
                colors[key] = colors.get(key, 0) + int(n)
        print(f"  [{i}/{len(tiles)}] tile ({sx},{sy}) brown={int(m.sum())}")
        time.sleep(SLEEP_S)

    if failures:
        print(f"WARN: {len(failures)} tile failures", file=sys.stderr)
    print(f"mosaic brown px: {int(mosaic.sum())} / {mosaic.size}")
    top_colors = sorted(colors.items(), key=lambda kv: -kv[1])[:8]

    # --- write georeferenced mosaic GeoTIFF (RGBA, EPSG:4326) ---
    dlon, dlat = pixel_size_deg()
    transform = from_bounds(BBOX[0], BBOX[1], BBOX[2], BBOX[3],
                            total_w, total_h)
    rgba = np.zeros((4, total_h, total_w), dtype=np.uint8)
    rgba[0][mosaic] = 160
    rgba[1][mosaic] = 82
    rgba[2][mosaic] = 44
    rgba[3][mosaic] = 255
    OUT_MOSAIC.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT_MOSAIC, "w", driver="GTiff", height=total_h,
                       width=total_w, count=4, dtype="uint8",
                       crs="EPSG:4326", transform=transform,
                       compress="deflate", tiled=True) as dst:
        dst.write(rgba)
    mosaic_sha = hashlib.sha256(OUT_MOSAIC.read_bytes()).hexdigest()
    print(f"mosaic -> {OUT_MOSAIC.name} sha {mosaic_sha[:16]}")

    # --- polygonize ---
    geoms = []
    for geom_json, val in rio_shapes(mosaic.astype(np.uint8), mask=mosaic,
                                     transform=transform):
        if val == 1:
            geoms.append(shp_shape(geom_json))
    print(f"polygonized: {len(geoms)} parts")
    gdf = gpd.GeoDataFrame({"src": ["wms_kl_landslides_new"] * len(geoms)},
                           geometry=geoms, crs="EPSG:4326").to_crs("EPSG:32643")
    gdf["area_m2"] = gdf.geometry.area
    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    gdf.to_file(OUT_GPKG, layer="inventory_wms", driver="GPKG")
    gpkg_sha = hashlib.sha256(OUT_GPKG.read_bytes()).hexdigest()
    print(f"gpkg -> {OUT_GPKG.name}: {len(gdf)} polys, "
          f"{gdf.area_m2.sum()/1e6:.2f} km2, sha {gpkg_sha[:16]}")

    # --- QA facts ---
    facts = {
        "date": TODAY,
        "purpose": "H2a(ii)/H2b(b) inventory substitution (prereg s7 D-15): "
                   "polygonized Bhuvan WMS render proxy for the non-public "
                   "ISRO Landslide Atlas vector inventory",
        "wms_endpoint": WMS,
        "layer": LAYER,
        "protocol": "WMS 1.1.1 SRS=EPSG:4326 lon,lat BBOX, tiled GetMap, "
                    "50% overlap, brown-mask union (removes per-tile bhuvan "
                    "watermark at tile centre)",
        "bbox_lonlat": list(BBOX),
        "resolution_m": RES_M,
        "mosaic_size_px": [total_w, total_h],
        "tiles_requested": len(tiles),
        "tile_failures": failures,
        "brown_px": int(mosaic.sum()),
        "dominant_sample_colors": [{"rgb": list(k), "count": v}
                                   for k, v in top_colors],
        "mosaic_path": str(OUT_MOSAIC.relative_to(ROOT.parent)),
        "mosaic_sha256": mosaic_sha,
        "gpkg_path": str(OUT_GPKG.relative_to(ROOT.parent)),
        "gpkg_sha256": gpkg_sha,
        "polygon_count": int(len(gdf)),
        "total_area_km2": round(float(gdf.area_m2.sum() / 1e6), 3),
    }

    # ground-truth check: overlap with digitized VAP8 2024 scar
    if SCAR_GPKG.exists():
        scar = gpd.read_file(SCAR_GPKG).to_crs("EPSG:32643")
        scar_u = unary_union(scar.geometry)
        inter = gdf.geometry.intersects(scar_u)
        inter_area = gdf.loc[inter].geometry.intersection(scar_u).area.sum()
        near = gdf.geometry.distance(scar_u) <= 500.0
        touching = gdf.geometry.touches(scar_u)
        facts["vap8_scar_check"] = {
            "scar_path": str(SCAR_GPKG.relative_to(ROOT.parent)),
            "scar_area_km2": round(float(scar_u.area / 1e6), 3),
            "inventory_polys_intersecting_scar": int(inter.sum()),
            "inventory_area_inside_scar_km2": round(float(inter_area / 1e6), 3),
            "scar_fraction_covered_by_inventory": round(
                float(inter_area / scar_u.area), 4),
            "inventory_polys_within_500m": int(near.sum()),
            "inventory_polys_touching_scar": int(touching.sum()),
            "note": "interpretation: only a small fraction of the scar is "
                    "covered - the layer does NOT map the Jul-2024 "
                    "Chooralmala-Mundakkai event (absent from all six "
                    "candidate layers; prereg s7 D-15 caveat 2). "
                    "Georeferencing is validated instead by: inventory polys "
                    "within 500 m of the scar, BBOX-honoured renders, and "
                    "polys inside the district.",
        }

    # inside-district coverage
    if BOUNDARY.exists():
        adm = gpd.read_file(BOUNDARY).to_crs("EPSG:32643")
        dist = unary_union(adm.geometry)
        inside = gdf.geometry.within(dist) | gdf.geometry.intersects(dist)
        facts["district_check"] = {
            "boundary_path": str(BOUNDARY.relative_to(ROOT.parent)),
            "polys_intersecting_district": int(inside.sum()),
            "area_in_district_km2": round(
                float(gdf.loc[inside].geometry.intersection(dist).area.sum()/1e6), 3),
        }

    OUT_FACTS.parent.mkdir(parents=True, exist_ok=True)
    OUT_FACTS.write_text(json.dumps(facts, indent=1))
    print(f"facts -> {OUT_FACTS.relative_to(ROOT)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
