"""P3 prep — Hansen loss-year raster for H3 covariates (tourism_observatory).

H3 (D-18 recipe) reports a pre-2011 forest-loss covariate
(`forest_loss_2000_2010_share`, mean loss-year per 500 m cell, thresholded
1..10 = 2001-2010). P1's ingest only produced the treecover-2000 layer and
P3 outcome ingest reduced lossyear to a binary mask, so this script warps the
raw lossyear tile onto the P1 grid as the full year-value raster.

Grid contract is reused verbatim from p1_baseline_ingest (envelope-anchor,
30 m, EPSG:32643, nodata 255 = outside read window); nearest-neighbour
because loss-year is categorical.

Source (already in data/manifest.json, H1 robustness layer / D-13):
  data/raw/Hansen_GFC-2024-v1.12_lossyear_20N_070E.tif
Output:
  data/processed/hansen_lossyear_32643.tif   uint8, 0 = no loss (valid),
                                             255 = outside window

Usage:  python scripts/p3_prep_lossyear.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_baseline_ingest as p1  # noqa: E402

TILE = p1.RAW / "Hansen_GFC-2024-v1.12_lossyear_20N_070E.tif"
OUT = "hansen_lossyear_32643.tif"


def main() -> int:
    if not TILE.exists():
        raise p1.IngestError(f"missing Hansen lossyear tile: {TILE.name}")
    aoi, grid = p1.aoi_grid()
    bbox = p1.aoi_bounds_4326(aoi, pad_deg=0.005)
    with rasterio.open(TILE) as src:
        arr, t = p1._read_window(src, bbox, "Hansen lossyear")
        crs = src.crs

    ly = p1.warp_to_grid(arr, t, crs, grid, Resampling.nearest, "uint8",
                         None, 255)
    valid = ly[ly != 255]
    if valid.size == 0:
        raise p1.IngestError("lossyear: no valid pixels inside AOI window")
    if not (0 <= valid.min() and valid.max() <= 24):
        raise p1.IngestError(
            f"lossyear values implausible: {valid.min()}..{valid.max()} "
            "(GFC v1.12 encodes 0..24 = no loss / 2001..2024)")
    n_loss = int((valid > 0).sum())
    if n_loss == 0:
        raise p1.IngestError("lossyear: zero loss pixels inside AOI")

    path = p1.write_raster(OUT, ly, grid, 255)
    print(f"{path.name}: {ly.shape} px, valid {valid.size}, "
          f"loss pixels {n_loss} ({n_loss * 900 / 1e4:.1f} ha), "
          f"years {int(valid[valid > 0].min())}..{int(valid.max())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
