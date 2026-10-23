"""P1 baseline ingest — Wayanad (tourism_observatory).

Builds the BASELINE-ONLY analysis layers on one common grid, following the
Jhabua aligned-stack contract and prereg dev-D-4 (envelope-anchor grid, exact
1 km parcels come later in P2 — this script only anchors the raster grid):

  grid rule: AOI envelope snapped OUTWARD to 300 m multiples, so the 30 m
  analysis grid and the 300 m CCI grid share the same origin exactly
  (300 = 10 x 30 m). Resolution 30 m, CRS EPSG:32643 (zone confirmed by
  boundary ingest, OI-3).

Outputs (data/processed/):
  dem_copernicus30m_32643.tif        elevation, bilinear, float32
  slope_deg_32643.tif                Horn slope (3x3), float32
  worldcover_2021_32643.tif          categorical, mode 10 m -> 30 m, uint8
  hansen_treecover2000_32643.tif     tree cover %, nearest, uint8
  cci_lulc_2005_32643.tif            LCCS classes, nearest, 300 m grid, uint8
  wdpa_wayanad_32643.gpkg            clipped polygons (NOT redistributable)
  wdpa_all_touched_32643.tif         rasterized all_touched=True, uint8
  roads_wayanad_32643.gpkg           OSM highways clipped (ODbL)
  road_dist_m_32643.tif              Euclidean distance to road, float32
  aoi_mask_32643.tif                 district mask, uint8

Fail-loud rule (Jhabua): a missing or implausible source stops the run; nothing
is zero-filled. QA (scripts/p1_baseline_qaqc.py) re-opens every output.

Usage:  python scripts/p1_baseline_ingest.py
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import yaml
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.merge import merge as rio_merge
from rasterio.transform import from_origin
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
BOUNDARY = PROC / "wayanad_boundary_32643.geojson"
CONFIG = ROOT / "config" / "wayanad.yaml"

RES = 30.0
SNAP = 300.0          # must be a multiple of RES (10 x 30) for exact nesting
CRS = "EPSG:32643"


class IngestError(RuntimeError):
    pass


def load_cfg() -> dict:
    if not CONFIG.exists():
        raise IngestError(f"config missing: {CONFIG}")
    return yaml.safe_load(CONFIG.read_text())


def aoi_grid() -> tuple[gpd.GeoDataFrame, dict]:
    """Boundary + snapped grid spec, computed from the actual boundary file."""
    if not BOUNDARY.exists():
        raise IngestError(f"boundary missing: {BOUNDARY}")
    aoi = gpd.read_file(BOUNDARY)
    if str(aoi.crs) != CRS:
        raise IngestError(f"boundary CRS is {aoi.crs}, expected {CRS}")
    if len(aoi) != 1:
        raise IngestError(f"boundary has {len(aoi)} features, expected 1")

    minx, miny, maxx, maxy = aoi.total_bounds
    x0 = math.floor(minx / SNAP) * SNAP
    y0 = math.floor(miny / SNAP) * SNAP
    x1 = math.ceil(maxx / SNAP) * SNAP
    y1 = math.ceil(maxy / SNAP) * SNAP

    w30 = int(round((x1 - x0) / RES))
    h30 = int(round((y1 - y0) / RES))
    grid = {
        "bounds": (x0, y0, x1, y1),
        "transform30": from_origin(x0, y1, RES, RES),
        "shape30": (h30, w30),
        "transform300": from_origin(x0, y1, SNAP, SNAP),
        "shape300": (int(round((y1 - y0) / SNAP)), int(round((x1 - x0) / SNAP))),
    }
    return aoi, grid


def aoi_bounds_4326(aoi: gpd.GeoDataFrame, pad_deg: float = 0.02) -> tuple:
    b = aoi.to_crs("EPSG:4326").total_bounds
    return (b[0] - pad_deg, b[1] - pad_deg, b[2] + pad_deg, b[3] + pad_deg)


def warp_to_grid(
    src_arr: np.ndarray,
    src_transform,
    src_crs: str,
    grid: dict,
    resampling: Resampling,
    dst_dtype,
    src_nodata,
    dst_nodata,
    key: str = "transform30",
) -> np.ndarray:
    h, w = grid["shape30" if key == "transform30" else "shape300"]
    dst = np.full((h, w), dst_nodata, dtype=dst_dtype)
    reproject(
        source=src_arr,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=grid[key],
        dst_crs=CRS,
        dst_nodata=dst_nodata,
        resampling=resampling,
    )
    return dst


def write_raster(name: str, arr: np.ndarray, grid: dict, nodata, key: str = "transform30") -> Path:
    out = PROC / name
    transform = grid[key]
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": arr.dtype.name,
        "crs": CRS,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 2 if arr.dtype.kind == "f" else 1,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(arr, 1)
    return out


# --------------------------------------------------------------------- layers
def build_dem(aoi, grid) -> dict:
    tiles = [
        RAW / "Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif",
        RAW / "Copernicus_DSM_COG_10_N11_00_E076_00_DEM.tif",
    ]
    for t in tiles:
        if not t.exists():
            raise IngestError(f"missing DEM tile: {t.name} (run p1_download.py)")

    bbox = aoi_bounds_4326(aoi, pad_deg=0.01)
    datasets = [rasterio.open(t) for t in tiles]
    try:
        merged, mtransform = rio_merge(
            datasets, bounds=bbox, nodata=-32767.0, dtype="float32"
        )
    finally:
        for d in datasets:
            d.close()

    arr = merged[0].astype("float32")
    # Copernicus fill values are negative sentinels; no inland voids expected.
    fill = arr <= -32767.0
    if fill.any():
        arr[fill] = -9999.0
    dst_nodata = -9999.0
    dem = warp_to_grid(
        arr, mtransform, "EPSG:4326", grid, Resampling.bilinear,
        "float32", (None if not fill.any() else -9999.0), dst_nodata,
    )

    if dem[dem != dst_nodata].size == 0:
        raise IngestError("DEM warped to all-nodata")
    valid = dem[dem != dst_nodata]
    if not (0 < valid.min() < 1500 and 500 < valid.max() < 3200):
        raise IngestError(
            f"DEM range implausible for Wayanad: min={valid.min():.1f} max={valid.max():.1f}"
        )
    dem_path = write_raster("dem_copernicus30m_32643.tif", dem, grid, dst_nodata)

    # Horn slope (3x3) on the 30 m metric grid.
    z = np.where(dem == dst_nodata, np.nan, dem)
    zp = np.pad(z, 1, mode="edge")

    def blk(r0, c0):
        return zp[r0:r0 + z.shape[0], c0:c0 + z.shape[1]]

    dzdx = ((blk(0, 2) + 2 * blk(1, 2) + blk(2, 2))
            - (blk(0, 0) + 2 * blk(1, 0) + blk(2, 0))) / (8 * RES)
    dzdy = ((blk(2, 0) + 2 * blk(2, 1) + blk(2, 2))
            - (blk(0, 0) + 2 * blk(0, 1) + blk(0, 2))) / (8 * RES)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype("float32")
    slope[np.isnan(slope)] = dst_nodata

    if not (0 <= np.nanmin(slope[slope != dst_nodata]) and np.nanmax(slope[slope != dst_nodata]) <= 75):
        raise IngestError("slope out of range")
    slope_path = write_raster("slope_deg_32643.tif", slope, grid, dst_nodata)

    return {
        "dem": {"path": dem_path.name, "min": round(float(valid.min()), 2),
                "max": round(float(valid.max()), 2),
                "mean": round(float(valid.mean()), 2)},
        "slope": {"path": slope_path.name,
                  "max": round(float(slope[slope != dst_nodata].max()), 2)},
    }


def _read_window(src, bbox, layer: str):
    """Read a bbox window with a loud, explicit overlap guard (P1 tile-name
    lesson: Hansen tiles are named by north edge; a wrong tile gave a cryptic
    '2720 x 0' GDAL error instead of 'wrong tile')."""
    from rasterio.windows import from_bounds
    win = from_bounds(*bbox, transform=src.transform).round_offsets().round_lengths()
    if win.width <= 0 or win.height <= 0:
        raise IngestError(
            f"{layer}: source window has no overlap with AOI bbox {tuple(round(v,4) for v in bbox)} "
            f"— source bounds {tuple(round(v,4) for v in src.bounds)}; wrong tile/CRS?"
        )
    arr = src.read(1, window=win)
    if arr.size == 0:
        raise IngestError(f"{layer}: window read returned empty array")
    return arr, src.window_transform(win)


def build_worldcover(aoi, grid) -> dict:
    tile = RAW / "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif"
    if not tile.exists():
        raise IngestError(f"missing WorldCover tile: {tile.name} (run p1_download.py)")
    bbox = aoi_bounds_4326(aoi, pad_deg=0.005)
    with rasterio.open(tile) as src:
        arr, t = _read_window(src, bbox, "WorldCover")
        crs = src.crs
        nodata = src.nodata if src.nodata is not None else 0

    wc = warp_to_grid(arr, t, crs, grid, Resampling.mode, "uint8", nodata, 0)
    allowed = {0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}
    present = set(np.unique(wc).tolist())
    if not present <= allowed:
        raise IngestError(f"WorldCover unexpected classes: {sorted(present - allowed)}")
    if not present - {0}:
        raise IngestError("WorldCover all-nodata inside AOI")
    path = write_raster("worldcover_2021_32643.tif", wc, grid, 0)
    counts = {int(c): int(n) for c, n in zip(*np.unique(wc, return_counts=True))}
    return {"path": path.name, "classes_present": sorted(present - {0}), "counts": counts}


def build_hansen(aoi, grid) -> dict:
    # GFC tiles are named by NORTH edge: 20N_070E = 10–20N/70–80E (Wayanad).
    tile = RAW / "Hansen_GFC-2024-v1.12_treecover2000_20N_070E.tif"
    if not tile.exists():
        raise IngestError(f"missing Hansen tile: {tile.name} (run p1_download.py)")
    bbox = aoi_bounds_4326(aoi, pad_deg=0.005)
    with rasterio.open(tile) as src:
        arr, t = _read_window(src, bbox, "Hansen treecover2000")
        crs = src.crs

    hansen = warp_to_grid(arr, t, crs, grid, Resampling.nearest, "uint8", None, 255)
    valid = hansen[hansen != 255]
    if valid.size == 0 or not (0 <= valid.min() and valid.max() <= 100):
        raise IngestError(f"Hansen values implausible: {valid.min()}..{valid.max()}")
    path = write_raster("hansen_treecover2000_32643.tif", hansen, grid, 255)
    return {
        "path": path.name,
        "min": int(valid.min()), "max": int(valid.max()),
        "share_ge10pct": round(float((valid >= 10).mean()), 4),
        "note": "0 = no tree cover (valid); 255 = outside read window",
    }


def build_cci(aoi, grid) -> dict:
    tile = RAW / "ESACCI-LC-L4-LCCS-Map-300m-P1Y-2005-v2.0.7cds-N00E045-lccs_class.tif"
    if not tile.exists():
        raise IngestError(f"missing CCI tile: {tile.name} (run p1_download.py)")
    bbox = aoi_bounds_4326(aoi, pad_deg=0.01)
    with rasterio.open(tile) as src:
        arr, t = _read_window(src, bbox, "CCI-LC 2005")
        crs = src.crs
        nodata = src.nodata

    cci = warp_to_grid(
        arr, t, crs, grid, Resampling.nearest, "uint8",
        nodata, 0, key="transform300",
    )
    # Full official CCI-LC legend incl. sub-codes — source of truth:
    # http://maps.elie.ucl.ac.be/CCI/viewer/download/CCI-LC_Maps_Legend.pdf
    # (values 11/12/61/62/71/72/81/82/121/122/151/152/153/201/202 are valid;
    #  210 = Water bodies — NOT 80, which is needleleaved deciduous tree cover.)
    lccs = {0, 10, 11, 12, 20, 30, 40, 50, 60, 61, 62, 70, 71, 72,
            80, 81, 82, 90, 100, 110, 120, 121, 122, 130, 140,
            150, 151, 152, 153, 160, 170, 180, 190, 200, 201, 202, 210, 220}
    present = set(np.unique(cci).tolist())
    if not present <= lccs:
        raise IngestError(f"CCI LCCS unexpected codes: {sorted(present - lccs)}")
    if not present - {0}:
        raise IngestError("CCI all-nodata inside AOI")
    path = write_raster("cci_lulc_2005_32643.tif", cci, grid, 0, key="transform300")
    counts = {int(c): int(n) for c, n in zip(*np.unique(cci, return_counts=True))}
    return {
        "path": path.name,
        "product": "ESA CCI-LC L4 LCCS 300m annual 2005, v2.0.7cds",
        "classes_present": sorted(present - {0}),
        "counts_on_300m_grid": counts,
        "pixel_area_km2": round(SNAP * SNAP / 1e6, 4),
    }


def build_wdpa(aoi, grid) -> dict:
    zips = RAW / "WDPA_WDOECM_Oct2026_Public_IND.zip"
    if not zips.exists():
        raise IngestError(f"missing WDPA archive: {zips.name} (run p1_download.py)")

    import zipfile
    import pyogrio
    gdb_rel = "WDPA_WDOECM_Oct2026_Public_IND.gdb"
    with zipfile.ZipFile(zips) as zf:
        names = zf.namelist()
        gdb_members = [m for m in names
                       if m.startswith(gdb_rel + "/") and not m.endswith("/")]
        shp_members = [m for m in names if m.lower().endswith(".shp")]
    if shp_members:                       # shapefile build, if a future release uses one
        vsi = f"/vsizip/{zips}/{shp_members[0]}"
        layers = [(shp_members[0], "Polygon")]
    elif gdb_members:                     # Oct-2026 public release ships a .gdb
        vsi = f"/vsizip/{zips}/{gdb_rel}"
        try:
            layers = pyogrio.list_layers(vsi).tolist()
        except Exception:                 # vsizip+OpenFileGDB unsupported here
            target = RAW / gdb_rel
            if not target.exists():
                with zipfile.ZipFile(zips) as zf:
                    for m in gdb_members:
                        zf.extract(m, RAW)
            vsi = str(target)
            layers = pyogrio.list_layers(vsi).tolist()
    else:
        raise IngestError(f"WDPA zip: neither .gdb nor .shp found; members={names[:8]}")

    poly = [(n, g) for n, g in layers if "point" not in str(g).lower()]
    if not poly:
        raise IngestError(f"WDPA: no polygon layer among {layers}")
    # public WDPA releases are polygons-only; pick the main layer defensively
    layer_name = next((n for n, _ in poly if "poly" in str(n).lower()
                       or str(n).lower().startswith("wdpa")), poly[0][0])

    bbox4326 = tuple(aoi.to_crs("EPSG:4326").total_bounds)
    gdf = gpd.read_file(vsi, layer=layer_name, bbox=bbox4326)
    if gdf.empty:
        raise IngestError("WDPA: no polygons near AOI (bbox read returned empty)")
    gdf = gdf.to_crs(CRS)
    clipped = gpd.clip(gdf, aoi)
    if clipped.empty:
        raise IngestError("WDPA: zero polygons intersect the AOI — check source")

    out_gpkg = PROC / "wdpa_wayanad_32643.gpkg"
    clipped.to_file(out_gpkg, layer="wdpa", driver="GPKG")

    ras = rasterize(
        ((geom, 1) for geom in clipped.geometry if geom is not None and not geom.is_empty),
        out_shape=grid["shape30"],
        transform=grid["transform30"],
        fill=0,
        all_touched=True,          # Jhabua conservative precedent (config qa rule)
        dtype="uint8",
    )
    path = write_raster("wdpa_all_touched_32643.tif", ras, grid, 0)
    # WDPA designations overlap (e.g. Western Ghats Eco-sensitive Area contains
    # the Nilgiri PA slice); the meaningful protected extent is the UNION area.
    vec_sum_km2 = float(clipped.geometry.area.sum()) / 1e6
    vec_area_km2 = float(clipped.geometry.union_all().area) / 1e6
    ras_area_km2 = float((ras == 1).sum()) * RES * RES / 1e6
    return {
        "path": path.name,
        "vector_path": out_gpkg.name,
        "polygons": int(len(clipped)),
        "vector_area_km2": round(vec_area_km2, 3),
        "vector_area_sum_km2": round(vec_sum_km2, 3),
        "raster_area_km2": round(ras_area_km2, 3),
        "redistributable": False,
        "note": ("WDPA not redistributable; all_touched=True rasterisation "
                 "(conservative); vector_area_km2 = union (designations overlap, "
                 "sum = vector_area_sum_km2 double-counts intersections)"),
    }


def build_roads(aoi, grid) -> dict:
    pbf = RAW / "southern-zone-261020.osm.pbf"
    if not pbf.exists():
        raise IngestError(f"missing OSM extract: {pbf.name} (run p1_download.py)")
    out = PROC / "roads_wayanad_32643.gpkg"
    if out.exists():
        out.unlink()

    bbox4326 = [f"{v:.6f}" for v in aoi.to_crs("EPSG:4326").total_bounds]
    cmd = [
        "ogr2ogr", "-f", "GPKG", str(out),
        str(pbf),
        "lines",
        "-spat", *bbox4326,
        "-where", "highway IS NOT NULL",
        "-t_srs", CRS,
        "-nln", "roads",
        "-nlt", "LINESTRING",
    ]
    env = {"OGR_OSM_MAX_TMPFILE_SIZE": "2048", "OGR_OSM_COMPRESS_NODES": "YES"}
    import os
    res = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **env})
    if res.returncode != 0:
        raise IngestError(f"ogr2ogr OSM extract failed: {res.stderr[-800:]}")

    roads = gpd.read_file(out)
    if roads.empty:
        raise IngestError("OSM roads: zero highway features in AOI")
    roads = gpd.clip(roads, aoi)
    if roads.empty:
        raise IngestError("OSM roads: clip to AOI removed everything")
    roads.to_file(out, layer="roads", driver="GPKG")

    # Road-access distance covariate (CURRENT-NETWORK PROXY label, prereg dev-D-4).
    road_mask = rasterize(
        ((geom, 1) for geom in roads.geometry if geom is not None and not geom.is_empty),
        out_shape=grid["shape30"],
        transform=grid["transform30"],
        fill=0,
        all_touched=True,
        dtype="uint8",
    )
    if road_mask.sum() == 0:
        raise IngestError("road rasterisation produced zero pixels")
    from scipy.ndimage import distance_transform_edt
    dist = distance_transform_edt(road_mask == 0, sampling=RES).astype("float32")
    dist_path = write_raster("road_dist_m_32643.tif", dist, grid, None)

    by_type = {str(k): int(v) for k, v in roads["highway"].value_counts().items()}
    return {
        "path": out.name,
        "distance_raster": dist_path.name,
        "features": int(len(roads)),
        "highway_types": by_type,
        "max_distance_m": round(float(dist.max()), 1),
        "label": "CURRENT-NETWORK PROXY (not baseline-period observation)",
        "license": "ODbL — © OpenStreetMap contributors",
    }


def build_aoi_mask(aoi, grid) -> dict:
    mask = rasterize(
        ((geom, 1) for geom in aoi.geometry),
        out_shape=grid["shape30"],
        transform=grid["transform30"],
        fill=0,
        all_touched=False,
        dtype="uint8",
    )
    path = write_raster("aoi_mask_32643.tif", mask, grid, 0)
    vec_km2 = float(aoi.geometry.area.sum()) / 1e6
    ras_km2 = float(mask.sum()) * RES * RES / 1e6
    return {
        "path": path.name,
        "vector_area_km2": round(vec_km2, 3),
        "raster_area_km2": round(ras_km2, 3),
        "diff_pct": round(100 * (ras_km2 - vec_km2) / vec_km2, 3),
    }


def main() -> int:
    PROC.mkdir(parents=True, exist_ok=True)
    try:
        cfg = load_cfg()
        if cfg.get("audit_status") != "CONDITIONAL_GO":
            raise IngestError(f"unexpected audit_status: {cfg.get('audit_status')}")
        aoi, grid = aoi_grid()
        x0, y0, x1, y1 = grid["bounds"]
        print("P1 baseline ingest — Wayanad")
        print(f"  grid: origin ({x0}, {y1}) 30 m shape {grid['shape30']}  "
              f"300 m shape {grid['shape300']}  CRS {CRS}")

        facts: dict = {"grid": {
            "origin_xy": [x0, y1], "res_m": RES, "snap_m": SNAP,
            "shape30": list(grid["shape30"]), "shape300": list(grid["shape300"]),
            "crs": CRS, "snap_rule": "envelope_anchor (outward to 300 m multiples)",
        }}
        builders = [
            ("dem", build_dem),
            ("worldcover_2021", build_worldcover),
            ("hansen_treecover2000", build_hansen),
            ("cci_lulc_2005", build_cci),
            ("wdpa", build_wdpa),
            ("roads", build_roads),
            ("aoi_mask", build_aoi_mask),
        ]
        for name, fn in builders:
            print(f"[{name}] …", flush=True)
            facts[name] = fn(aoi, grid)
            print(f"    ok: {json.dumps(facts[name], default=str)[:400]}")

        facts_path = ROOT / "outputs" / "qaqc" / "ingest_facts.json"
        facts_path.parent.mkdir(parents=True, exist_ok=True)
        facts_path.write_text(json.dumps(facts, indent=1, default=str) + "\n")
        facts["facts_path"] = str(facts_path.relative_to(ROOT))
        print(f"OK — ingest facts written to {facts_path.relative_to(ROOT)}")
        return 0
    except IngestError as e:
        print(f"FAIL: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
