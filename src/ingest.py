#!/usr/bin/env python3
"""
src/ingest.py - build the aligned 30 m screening stack from raw sources.

This is deliberately not "reproject everything to 10 m". The screening layers
have different native resolutions and different meanings:

  * WorldCover 10 m categorical  -> aggregate to 30 m with majority (mode)
  * Hansen 30 m categorical/percent -> nearest to the 30 m grid
  * DEM 30 m continuous          -> bilinear to the grid, then Horn slope
  * Sentinel-2 10 m indices      -> average to 30 m (optional scoring layers)
  * WDPA vectors                 -> rasterise to 1/0 on the grid
  * District boundary            -> rasterise to 1/0 and define the grid

Every output is written with the same CRS, transform, width and height. The
screening module checks that contract at load time, but this module is where the
contract is created.

If a required source is missing, ingest stops and lists every missing file. It
never substitutes zeros for a missing layer: a zero-filled WorldCover or Hansen
raster would look like "eligible" land and silently inflate the result.

Usage:
    python src/ingest.py config/jhabua.yaml
    python src/ingest.py config/jhabua.yaml --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.screening import load_config, validate_config  # noqa: E402


class IngestError(RuntimeError):
    """A source, grid or output contract is broken."""


REQUIRED_SOURCE_KEYS = (
    "worldcover",
    "hansen_treecover2000",
    "hansen_lossyear",
    "hansen_gain",
    "dem",
    "protected_areas",
)
OPTIONAL_SOURCE_KEYS = ("s2_dry", "s2_monsoon")


# --------------------------------------------------------------------------- utils
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pixel_area_ha(cfg: dict) -> float:
    res = float(cfg["grid"]["resolution_m"])
    return res * res / 10_000.0


def _to_union(geoms):
    """Shapely 2 union_all with a fallback for older shapely."""
    try:
        return geoms.union_all()
    except AttributeError:  # pragma: no cover - older shapely
        return geoms.unary_union


def read_boundary(cfg: dict):
    """Return (GeoDataFrame in working CRS, union geometry)."""
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover
        raise IngestError("geopandas is required to read the boundary and WDPA") from exc

    path = Path(cfg["project"]["boundary"])
    if not path.exists():
        raise IngestError(f"boundary file missing: {path}")

    gdf = gpd.read_file(path)
    feature = str(cfg["project"].get("boundary_feature", "Jhabua"))
    if "shapeName" not in gdf.columns:
        raise IngestError(f"boundary has no shapeName column: {list(gdf.columns)}")
    match = gdf[gdf["shapeName"].astype(str).str.casefold() == feature.casefold()].copy()
    if len(match) != 1:
        raise IngestError(
            f"expected exactly one boundary feature named {feature!r}, found {len(match)}"
        )
    match = match.to_crs(cfg["grid"]["crs"])
    geom = match.geometry.iloc[0]
    if geom is None or geom.is_empty:
        raise IngestError("district boundary is empty")
    if not geom.is_valid:
        raise IngestError("district boundary geometry is invalid; repair it first")
    return match, geom


def build_grid(cfg: dict, geom) -> dict:
    """Snap the district envelope to the configured 30 m grid."""
    from rasterio.transform import from_origin

    res = float(cfg["grid"]["resolution_m"])
    if res <= 0:
        raise IngestError("grid.resolution_m must be positive")
    minx, miny, maxx, maxy = geom.bounds
    west = math.floor(minx / res) * res
    south = math.floor(miny / res) * res
    east = math.ceil(maxx / res) * res
    north = math.ceil(maxy / res) * res
    width = int(round((east - west) / res))
    height = int(round((north - south) / res))
    if width <= 0 or height <= 0:
        raise IngestError("district envelope produces an empty raster grid")
    return {
        "crs": cfg["grid"]["crs"],
        "transform": from_origin(west, north, res, res),
        "width": width,
        "height": height,
        "resolution_m": res,
        "bounds": (west, south, east, north),
    }


def rasterize_district(geom, grid: dict) -> np.ndarray:
    from rasterio.features import rasterize

    return rasterize(
        [(geom, 1)],
        out_shape=(grid["height"], grid["width"]),
        transform=grid["transform"],
        fill=0,
        dtype="uint8",
        all_touched=False,
    )


def reproject_band(
    src_path: Path,
    grid: dict,
    *,
    band: int,
    resampling,
    dtype: str,
    dst_nodata,
    src_nodata="auto",
) -> np.ndarray:
    """Reproject one band onto the common grid, preserving a nodata value."""
    import rasterio
    from rasterio.warp import reproject

    with rasterio.open(src_path) as src:
        if src.crs is None:
            raise IngestError(f"source has no CRS: {src_path}")
        if band < 1 or band > src.count:
            raise IngestError(f"{src_path} has {src.count} bands; requested band {band}")
        src_nd = src.nodata if src_nodata == "auto" else src_nodata
        dest = np.full((grid["height"], grid["width"]), dst_nodata, dtype=dtype)
        reproject(
            source=rasterio.band(src, band),
            destination=dest,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src_nd,
            dst_transform=grid["transform"],
            dst_crs=grid["crs"],
            dst_nodata=dst_nodata,
            resampling=resampling,
            init_dest_nodata=True,
        )
    return dest


def mask_outside_district(arr: np.ndarray, district: np.ndarray, nodata) -> np.ndarray:
    out = arr.copy()
    out[district == 0] = nodata
    return out


def fill_nearest(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Fill DEM holes with the nearest valid value before computing slope."""
    from scipy import ndimage

    if valid.all():
        return arr
    if not valid.any():
        raise IngestError("DEM has no valid pixels")
    inds = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return arr[tuple(inds)]


def horn_slope(dem: np.ndarray, transform, nodata: float) -> np.ndarray:
    """Horn (1981) slope in degrees from a DEM on a square grid."""
    dem = dem.astype(np.float64)
    valid = dem != nodata
    if not valid.any():
        raise IngestError("DEM has no valid pixels to derive slope")
    dem_filled = fill_nearest(dem, valid)

    dx = abs(float(transform.a))
    dy = abs(float(transform.e))
    if dx <= 0 or dy <= 0:
        raise IngestError("DEM transform has a non-positive pixel size")

    p = np.pad(dem_filled, 1, mode="edge")
    a = p[:-2, :-2]
    b = p[:-2, 1:-1]
    c = p[:-2, 2:]
    d = p[1:-1, :-2]
    f = p[1:-1, 1:-1]
    i = p[1:-1, 2:]
    g = p[2:, :-2]
    h = p[2:, 1:-1]
    k = p[2:, 2:]
    dzdx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * dx)
    dzdy = ((g + 2.0 * h + k) - (a + 2.0 * b + c)) / (8.0 * dy)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    slope = np.clip(slope, 0.0, 90.0)
    slope[~valid] = nodata
    return slope.astype("float32")


def rasterize_protected(cfg: dict, grid: dict, district: np.ndarray) -> np.ndarray:
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover
        raise IngestError("geopandas is required for WDPA") from exc
    from rasterio.features import rasterize

    path = Path(cfg["paths"]["sources"]["protected_areas"])
    gdf = gpd.read_file(path)
    if len(gdf) == 0:
        out = np.zeros((grid["height"], grid["width"]), dtype="uint8")
        out[district == 0] = 255
        return out
    gdf = gdf.to_crs(grid["crs"])
    geom = _to_union(gdf.geometry)
    protected = rasterize(
        [(geom, 1)],
        out_shape=(grid["height"], grid["width"]),
        transform=grid["transform"],
        fill=0,
        dtype="uint8",
        all_touched=True,
    )
    protected[district == 0] = 255
    return protected


# --------------------------------------------------------------------------- writing
def write_raster(path: Path, arr: np.ndarray, grid: dict, dtype: str, nodata, description: str) -> None:
    import rasterio

    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": grid["height"],
        "width": grid["width"],
        "count": 1,
        "dtype": dtype,
        "crs": grid["crs"],
        "transform": grid["transform"],
        "nodata": nodata,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        data = np.asarray(arr)
        if np.issubdtype(data.dtype, np.floating):
            # GeoTIFFs with NaN pixels are hard to mask consistently; write
            # them as the declared nodata value instead.
            data = np.where(np.isfinite(data), data, nodata)
        dst.write(data.astype(dtype), 1)
        dst.set_band_description(1, description)


def _layer_stats(arr: np.ndarray, district: np.ndarray, nodata) -> dict:
    valid = district.astype(bool) & (arr != nodata) & np.isfinite(arr)
    vals = arr[valid]
    return {
        "valid_pixels_inside_district": int(valid.sum()),
        "nodata_share_inside_district": round(float(1.0 - valid.sum() / max(int(district.sum()), 1)), 6),
        "min": float(vals.min()) if vals.size else None,
        "max": float(vals.max()) if vals.size else None,
    }


def write_manifest(cfg: dict, records: list, grid: dict, district: np.ndarray) -> Path:
    """Write provenance for both the raw sources and the aligned outputs."""
    out = Path(cfg["paths"]["aligned_dir"]) / "manifest.json"
    payload = {
        "project": cfg["project"]["name"],
        "district": cfg["project"]["district"],
        "generated_from_config": str(Path(cfg.get("_config_path", "config/jhabua.yaml"))),
        "grid": {
            "crs": grid["crs"],
            "resolution_m": grid["resolution_m"],
            "width": grid["width"],
            "height": grid["height"],
            "transform": list(grid["transform"])[:6],
            "district_pixels": int(district.sum()),
            "district_ha": round(float(district.sum()) * pixel_area_ha(cfg), 3),
        },
        "layers": records,
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the aligned 30 m Jhabua stack.")
    parser.add_argument("config", nargs="?", default="config/jhabua.yaml")
    parser.add_argument("--base", default=".", help="project root (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="check sources and grid, write nothing")
    args = parser.parse_args(argv)

    root = Path(args.base).resolve()
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = root / cfg_path
    cfg = load_config(cfg_path)
    cfg["_config_path"] = str(cfg_path.relative_to(root))
    validate_config(cfg)

    sources = cfg["paths"]["sources"]
    missing = [k for k in REQUIRED_SOURCE_KEYS if not (root / sources[k]).exists()]
    if missing:
        print("[ingest] STOP - required raw sources are missing:")
        for key in missing:
            print(f"  - {key}: {root / sources[key]}")
        print("[ingest] no outputs were written; a zero-filled layer would silently inflate eligible area.")
        return 2

    boundary_gdf, geom = read_boundary({**cfg, "project": {**cfg["project"], "boundary": str(root / cfg["project"]["boundary"])}})
    grid = build_grid(cfg, geom)
    district = rasterize_district(geom, grid)
    if district.sum() == 0:
        raise IngestError("district mask is empty after rasterisation")

    print(
        f"[ingest] grid {grid['width']} x {grid['height']} @ {grid['resolution_m']} m "
        f"({grid['crs']}), district {district.sum() * pixel_area_ha(cfg):,.1f} ha"
    )
    if args.dry_run:
        print("[ingest] dry run: sources present, grid built, no files written")
        return 0

    aligned = root / cfg["paths"]["aligned_dir"]
    aligned.mkdir(parents=True, exist_ok=True)
    records = []

    def finish(key: str, arr: np.ndarray, dtype: str, nodata, description: str,
               source_key: str | None = None) -> None:
        filename = cfg["paths"]["layers"][key]
        path = aligned / filename
        write_raster(path, arr, grid, dtype, nodata, description)
        stats = _layer_stats(arr, district, nodata)
        rec = {
            "id": key,
            "path": str(path.relative_to(root)),
            "source": "district boundary" if source_key is None
            else str((root / sources[source_key]).relative_to(root)),
            "source_sha256": None if source_key is None else sha256_of(root / sources[source_key]),
            "output_sha256": sha256_of(path),
            "dtype": dtype,
            "nodata": nodata,
            **stats,
        }
        records.append(rec)
        print(f"  [{key}] -> {path.relative_to(root)} ({stats['min']}..{stats['max']}, "
              f"nodata {stats['nodata_share_inside_district']:.2%})")

    # 1. District mask
    finish("district_mask", district, "uint8", 0, "1 = inside Jhabua district")

    # 2. WorldCover: majority class at 30 m
    from rasterio.warp import Resampling

    wc = reproject_band(
        root / sources["worldcover"], grid, band=1, resampling=Resampling.mode,
        dtype="uint8", dst_nodata=0,
    )
    wc = mask_outside_district(wc, district, 0)
    finish("worldcover", wc, "uint8", 0, "ESA WorldCover 2021 v200, majority at 30 m",
           source_key="worldcover")

    # 3. Hansen layers: preserve native values, nearest to the common grid
    tree = reproject_band(
        root / sources["hansen_treecover2000"], grid, band=1, resampling=Resampling.nearest,
        dtype="uint8", dst_nodata=255,
    )
    tree = mask_outside_district(tree, district, 255)
    finish("hansen_treecover2000", tree, "uint8", 255, "Hansen treecover2000, percent",
           source_key="hansen_treecover2000")

    loss = reproject_band(
        root / sources["hansen_lossyear"], grid, band=1, resampling=Resampling.nearest,
        dtype="uint8", dst_nodata=255,
    )
    loss = mask_outside_district(loss, district, 255)
    finish("hansen_lossyear", loss, "uint8", 255, "Hansen lossyear, 0 = none, 1..N = 2000+N",
           source_key="hansen_lossyear")

    gain = reproject_band(
        root / sources["hansen_gain"], grid, band=1, resampling=Resampling.nearest,
        dtype="uint8", dst_nodata=255,
    )
    gain = mask_outside_district(gain, district, 255)
    finish("hansen_gain", gain, "uint8", 255, "Hansen gain 2000-2012, 0/1",
           source_key="hansen_gain")

    # 4. DEM -> slope
    dem = reproject_band(
        root / sources["dem"], grid, band=1, resampling=Resampling.bilinear,
        dtype="float32", dst_nodata=-9999.0,
    )
    slope = horn_slope(dem, grid["transform"], -9999.0)
    slope = mask_outside_district(slope, district, -9999.0)
    finish("slope_deg", slope, "float32", -9999.0, "Slope in degrees, Horn method",
           source_key="dem")

    # 5. WDPA -> binary protected
    protected = rasterize_protected(
        {**cfg, "paths": {**cfg["paths"], "sources": {**sources,
            "protected_areas": str(root / sources["protected_areas"])}}},
        grid, district,
    )
    finish("protected_areas", protected, "uint8", 255, "1 = WDPA protected area",
           source_key="protected_areas")

    # 6. Optional Sentinel-2 scoring indices (average aggregation to 30 m)
    for key in OPTIONAL_SOURCE_KEYS:
        if not (root / sources[key]).exists():
            print(f"  [{key}] optional source missing; skipping")
            continue
        for band, idx_key, desc in (
            (7, f"ndvi_{'dry' if key.endswith('dry') else 'monsoon'}", "Sentinel-2 NDVI, 30 m mean"),
            (8, f"bsi_{'dry' if key.endswith('dry') else 'monsoon'}", "Sentinel-2 BSI, 30 m mean"),
        ):
            arr = reproject_band(
                root / sources[key], grid, band=band, resampling=Resampling.average,
                dtype="float32", dst_nodata=-9999.0, src_nodata=np.nan,
            )
            arr = mask_outside_district(arr, district, -9999.0)
            finish(idx_key, arr, "float32", -9999.0, desc, source_key=key)

    manifest_path = write_manifest(cfg, records, grid, district)
    print(f"[ingest] wrote {len(records)} aligned layers and {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
