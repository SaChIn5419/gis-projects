#!/usr/bin/env python3
"""
src/ingest.py — load, clip and reproject every layer into the working CRS.

Purpose
-------
Every layer in data/raw/ is acquired in its own native CRS (geoBoundaries is
EPSG:4326, WorldCover is EPSG:4326, SRTM is EPSG:4326, OSM is EPSG:4326).
The screening math (distances, areas, buffers, reason codes) only makes sense
in one CRS, so ingest.py reprojects everything to EPSG:32643 (UTM zone 43N)
and clips it to the Jhabua district boundary. It writes one file per layer to
data/processed/ and records the SHA256 + CRS + resolution in data/manifest.json
so the QA gate can check the result.

Inputs
------
  - config/<district>.yaml  (working_crs, boundary, district_area_ha)
  - data/manifest.json      (the source list: layer id, path, type, crs, ...)

Outputs
-------
  - data/processed/<layer>.tif   for rasters (clipped, reprojected, 10/30 m)
  - data/processed/<layer>.geojson for vectors (clipped, reprojected)
  - data/manifest.json updated: sha256 (output), crs, resolution, area_ha, status=processed

Usage
-----
    python src/ingest.py config/jhabua.yaml
    python src/ingest.py config.yaml

Notes for the learner
---------------------
- Reprojection changes pixel counts: a 10 m raster reprojected to 30 m loses
  resolution; a 30 m raster reprojected to 10 m gains resolution but no new
  information. The manifest records the OUTPUT resolution so the QA gate can
  flag a mismatch.
- The boundary is the Jhabua feature extracted from geoBoundaries ADM2; ingest
  reads the full file and filters to shapeName == "Jhabua".
- Geopandas is optional: if it is missing, vector layers are recorded as
  PENDING and skipped (the QA gate will flag them).
- rasterio is required for rasters: if it is missing, the gate cannot run.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

# ---- helpers ----------------------------------------------------------------

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_manifest(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(path, manifest):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)


def district_boundary_path(cfg):
    """Return the path to the boundary file (full India ADM2 GeoJSON)."""
    return Path(cfg["project"]["boundary"])


def extract_jhabua_boundary(path):
    """Read the full ADM2 file and return the Jhabua feature (geopandas)."""
    try:
        import geopandas as gpd
    except ImportError:
        print("  [ingest] geopandas missing - boundary extraction PENDING")
        return None
    gdf = gpd.read_file(path)
    jhabua = gdf[gdf["shapeName"].str.lower() == "jhabua"].copy()
    if jhabua.empty:
        print("  [ingest] no Jhabua feature found in boundary file")
        return None
    return jhabua


def reproject_vector(gdf, target_crs):
    """Reproject a GeoDataFrame to the target CRS."""
    if gdf is None:
        return None
    return gdf.to_crs(target_crs)


def clip_raster_to_boundary(raster_path, boundary_gdf, target_crs):
    """
    Open a raster, clip to the district boundary, reproject to target_crs.
    Returns (array, transform, crs, nodata_pct). Returns None on failure.
    """
    try:
        import rasterio
        from rasterio.mask import mask as raster_mask
        from rasterio.warp import calculate_default_transform, reproject, Resampling
        from rasterio.enums import Resampling as RS
    except ImportError:
        print("  [ingest] rasterio missing - raster clip PENDING")
        return None

    with rasterio.open(raster_path) as src:
        # reproject the source to target_crs first (so the clip uses the right grid)
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "nodata": src.nodata if src.nodata is not None else 0,
        })
        # read + reproject into a memory buffer
        data = np.zeros((src.count, height, width), dtype=src.dtypes[0])
        reproject(
            source=rasterio.band(src, list(range(1, src.count + 1))),
            destination=data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=target_crs,
            resampling=RS.nearest,
        )
        # clip to the boundary
        boundary = boundary_gdf.geometry.unary_union
        # build a mask raster in the same grid
        from rasterio.features import rasterize
        mask_arr = rasterize(
            [(boundary, 1)],
            out_shape=(height, width),
            transform=transform,
            fill=0,
            dtype="uint8",
        )
        data = np.where(mask_arr[None, :, :] == 1, data, kwargs["nodata"])
        # no-data share
        nodata_ratio = float((data == kwargs["nodata"]).sum()) / float(data.size)
        # area (ha): pixels * res * res / 10000
        res_x = abs(transform.a)
        res_y = abs(transform.e)
        area_ha = float((mask_arr == 1).sum() * res_x * res_y / 10000.0)
        return {
            "array": data,
            "transform": transform,
            "crs": target_crs,
            "width": width,
            "height": height,
            "meta": kwargs,
            "nodata_value": kwargs["nodata"],
            "nodata_ratio": nodata_ratio,
            "area_ha": area_ha,
        }


def write_raster(path, payload):
    """Write a clipped/reprojected raster to disk."""
    try:
        import rasterio
    except ImportError:
        print("  [ingest] rasterio missing - cannot write raster")
        return None
    meta = payload["meta"].copy()
    meta["driver"] = "GTiff"
    meta["count"] = payload["array"].shape[0]
    with rasterio.open(path, "w", **meta) as dst:
        dst.write(payload["array"])
    return path


def write_vector(path, gdf):
    """Write a clipped/reprojected vector layer to disk."""
    if gdf is None:
        return None
    try:
        gdf.to_file(path, driver="GeoJSON")
        return path
    except Exception as exc:  # noqa: BLE001
        print(f"  [ingest] could not write vector {path}: {exc}")
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingest: load + clip + reproject to EPSG:32643")
    parser.add_argument("config", nargs="?", default="config.yaml",
                        help="path to config file (default: config.yaml)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    target_crs = cfg["project"]["working_crs"]
    district_area_ha = cfg["project"].get("district_area_ha", 3600.0)
    boundary_path = district_boundary_path(cfg)

    print(f"[ingest] working CRS = {target_crs}")
    print(f"[ingest] boundary = {boundary_path}")

    # boundary (vector) — extract Jhabua from the full ADM2 file
    jhabua = extract_jhabua_boundary(boundary_path)
    if jhabua is not None:
        jhabua = reproject_vector(jhabua, target_crs)
        out_path = Path("data/processed/boundary_jhabua.geojson")
        write_vector(out_path, jhabua)
        print(f"  boundary -> {out_path} (SHA256 {sha256_of(out_path)})")

    # load manifest
    manifest_path = Path("data/manifest.json")
    manifest = load_manifest(manifest_path)

    # process each layer
    for rec in manifest.get("layers", []):
        layer_id = rec["id"]
        src_path = Path(rec["path"])
        if not src_path.exists():
            print(f"  [{layer_id}] source missing ({src_path}) - skipping, status stays {rec['status']}")
            continue

        print(f"  [{layer_id}] processing {src_path} ...")
        if rec["type"] == "raster":
            payload = clip_raster_to_boundary(src_path, jhabua, target_crs)
            if payload is None:
                print(f"  [{layer_id}] PENDING - rasterio missing or clip failed")
                continue
            out_path = Path("data/processed") / (src_path.stem + ".tif")
            write_raster(out_path, payload)
            rec["output_path"] = str(out_path)
            rec["output_sha256"] = sha256_of(out_path)
            rec["crs"] = target_crs
            rec["resolution_m"] = payload["transform"].a
            rec["nodata_ratio"] = round(payload["nodata_ratio"], 4)
            rec["area_ha"] = round(payload["area_ha"], 2)
            rec["status"] = "processed"
            print(f"  [{layer_id}] -> {out_path} "
                  f"(res={payload['transform'].a}m, nodata={payload['nodata_ratio']:.2%}, "
                  f"area={payload['area_ha']:.1f} ha)")
        elif rec["type"] == "vector":
            if jhabua is None:
                print(f"  [{layer_id}] PENDING - geopandas missing")
                continue
            try:
                import geopandas as gpd
                gdf = gpd.read_file(src_path)
                gdf = gdf.to_crs(target_crs)
                # clip to Jhabua
                gdf = gdf[gdf.geometry.intersects(jhabua.geometry.unary_union)]
                out_path = Path("data/processed") / (src_path.stem + ".geojson")
                write_vector(out_path, gdf)
                rec["output_path"] = str(out_path)
                rec["output_sha256"] = sha256_of(out_path)
                rec["crs"] = target_crs
                rec["feature_count"] = len(gdf)
                rec["status"] = "processed"
                print(f"  [{layer_id}] -> {out_path} ({len(gdf)} features)")
            except Exception as exc:  # noqa: BLE001
                print(f"  [{layer_id}] FAILED: {exc}")
                rec["status"] = "error"
                rec["error"] = str(exc)

    save_manifest(manifest_path, manifest)
    print(f"[ingest] manifest updated: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
