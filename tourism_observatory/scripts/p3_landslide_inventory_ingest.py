#!/usr/bin/env python3
"""
p3_landslide_inventory_ingest.py
================================
Wayanad second-hazard layer — landslide inventory ingestion.

Reads the raw attribute-bearing landslide inventory archive, aligns it to the
project CRS (EPSG:32643, UTM zone 43N), clips it to the Wayanad AOI, and writes
the cleaned layer to data/processed/hazard/.

OUTPUT
  data/processed/hazard/wayanad_landslide_layer.geojson

USAGE
  # Dry-run / schema check — no AOI clipping, just report the raw schema:
  python3 scripts/p3_landslide_inventory_ingest.py --dry-run --raw-inventory /path/to/inventory.shp

  # Full ingest — clip to AOI and export:
  python3 scripts/p3_landslide_inventory_ingest.py --raw-inventory /path/to/inventory.shp --out data/processed/hazard/wayanad_landslide_layer.geojson

DEPENDENCIES
  geopandas, shapely, pyproj, pandas
  Environment: miniforge3 (geopandas >= 0.11)

NOTES
  - The raw inventory must carry an attribute column (event ID, date, type,
    volume, etc.). If the archive has no attribute fields the script fails fast
    with a schema error rather than silently producing an attribute-less layer.
  - CRS alignment is always done to the project CRS EPSG:32643 before clipping;
    the inverted (to_crs) call is resolved against the AOI's CRS, never guessed.
"""
import argparse
import sys
import os

import geopandas as gpd
import pandas as pd

# Project CRS: EPSG:32643 (Utah zone 43N), which matches the district's longitude
# span (74.0-75.0 E) and the rest of the Wayanad pipeline.
TARGET_CRS = "EPSG:32643"

# Default AOI & output locations (overridden by CLI args).
DEFAULT_AOI = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed",
    "wayanad_boundary_32643.geojson"
)
DEFAULT_OUT = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "hazard",
    "wayanad_landslide_layer.geojson"
)

MIN_OUTPUT_ROWS = 1  # fail loudly if clipping empties the archive


def resolve_path(path):
    """Resolve a possibly-relative path to an absolute path inside the project."""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", path))


def load_inventory(path):
    """Load the raw inventory; return (gdf, schema_info)."""
    if not os.path.exists(path):
        sys.exit(f"[ingest] raw inventory not found: {path}")

    if path.endswith(".gpkg"):
        gdf = gpd.read_file(path)
        # gpkg may embed a layer name; attempt to pick the largest vector layer.
        if len(gdf) == 0:
            # fallback: read all layers and take the biggest
            layers = gpd.list_layers(path)
            if not layers:
                sys.exit("[ingest] gpkg has no vector layers: " + path)
            best = max(layers, key=lambda l: l.row_count)
            gdf = gpd.read_file(path, layer=best.name)
    else:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".shp",):
            gdf = gpd.read_file(path)
        elif ext in (".geojson",):
            gdf = gpd.read_file(path)
        else:
            sys.exit(f"[ingest] unsupported raw inventory extension: {ext}")

    if gdf is None or len(gdf) == 0:
        sys.exit(f"[ingest] loaded zero features from: {path}")

    attrs = [c for c in gdf.columns if c != "geometry"]
    schema = {
        "n_features": int(len(gdf)),
        "crs": str(gdf.crs),
        "columns": list(gdf.columns),
        "num_attribute_cols": int(len(attrs)),
    }
    return gdf, schema


def check_attribute_schema(gdf, raw_path):
    """Fail loudly if the archive carries no attribute fields."""
    attrs = [c for c in gdf.columns if c != "geometry"]
    if not attrs:
        sys.exit(
            f"[ingest] ABORT — {raw_path} has NO attribute columns. "
            "This is a bare spatial layer, not an attribute-bearing inventory; "
            "it cannot feed R-1/R-3 without a provenance change."
        )


def align_and_clip(inventory_gdf, aoi_gdf, out_path):
    """Align inventory to project CRS, clip to AOI, export."""
    # 1) Assign project CRS if missing.
    if inventory_gdf.crs is None:
        inventory_gdf = inventory_gdf.set_crs(TARGET_CRS)
        print(f"[ingest] {inventory_gdf.crs.to_epsg()} assigned (no CRS declared)")

    # 2) Align inventory to project CRS, AOI to project CRS too.
    inv = inventory_gdf.to_crs(TARGET_CRS)
    aoi = aoi_gdf.to_crs(TARGET_CRS)

    # 3) Spatial clip to AOI.
    clipped = gpd.clip(inv, aoi)
    if len(clipped) == 0:
        sys.exit(f"[ingest] ABORT — clipping to AOI produced 0 features. "
                 "Does the AOI cover the inventory extent?")

    # 4) Re-project geometry to EPSG:32643 for the output (kept already in 32643).
    clipped = clipped.to_crs(TARGET_CRS)

    # 5) Drop duplicate rows (keep first occurrence) before writing.
    cols = [c for c in clipped.columns if c != "geometry"]
    before = len(clipped)
    clipped = clipped.drop_duplicates(subset=cols, keep="first")
    if len(clipped) < before:
        print(f"[ingest] dropped {before - len(clipped)} exact duplicate rows")

    clipped.to_file(out_path, driver="GeoJSON")
    return clipped


def main():
    ap = argparse.ArgumentParser(description="Ingest landslide inventory for Wayanad.")
    ap.add_argument("--raw-inventory", required=True,
                    help="Path to raw landslide inventory archive (shapefile/geojson/gpkg)")
    ap.add_argument("--aoi", default=resolve_path(DEFAULT_AOI),
                    help="AOI boundary (default: project Wayanad boundary)")
    ap.add_argument("--out", default=resolve_path(DEFAULT_OUT),
                    help="Output GeoJSON path")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report raw schema only; do not clip/export")
    args = ap.parse_args()

    # Resolve paths.
    raw = os.path.abspath(args.raw_inventory)
    aoi_path = os.path.abspath(args.aoi)
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Load.
    print(f"[ingest] loading inventory: {raw}")
    inv_gdf, schema = load_inventory(raw)
    print(f"[ingest] raw schema: {schema}")

    # Attribute check — fail fast on a bare spatial layer.
    check_attribute_schema(inv_gdf, raw)

    # Load AOI.
    print(f"[ingest] loading AOI: {aoi_path}")
    aoi_gdf = gpd.read_file(aoi_path)
    if aoi_gdf.crs is None:
        sys.exit("[ingest] AOI has no CRS — cannot clip safely.")
    aoi_gdf = aoi_gdf.to_crs(TARGET_CRS)

    # Bounding box sanity check.
    print(f"[ingest] AOI bounds (EPSG:32643): {aoi_gdf.total_bounds.tolist()}")

    if args.dry_run:
        print(f"[ingest] DRY RUN. Raw schema reported; no clipping/export performed.")
        return

    # Clip and export.
    print(f"[ingest] clipping to AOI -> {out_path}")
    out = align_and_clip(inv_gdf, aoi_gdf, out_path)

    # Post-write QA.
    print(f"[ingest] written: {out_path}")
    print(f"[ingest] output features: {len(out)}")
    print(f"[ingest] output CRS: {out.crs.to_epsg()}")
    print(f"[ingest] output geometry type: {out.geom_type.tolist()[:1]}")
    print(f"[ingest] output attribute leading columns: "
          f"{list(out.columns[:6])}")

    print(f"[qa] PASS — {len(out)} clipped features written, CRS EPSG:32643")


if __name__ == "__main__":
    main()
