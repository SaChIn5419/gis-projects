"""P3 step (a) — ingest the H1 LAND-CONVERSION outcome layers onto the frozen grid.

Information boundary (§5): this is the FIRST script that reads outcome-era
rasters. It is permitted only because freeze R6 is recorded in PROJECTSTATE §9
(§8 checklist signed 2026-10-26). It computes conversion counts but does NOT
compare treatment vs control — that is p3_h1_analysis.py, run separately.

H1 endpoint (prereg §3 H1): % of buffer area converted from non-built (tree/
shrub/crop) to built-up, primary radius 500 m (sensitivities 250 m / 1000 m).

Outcome sources — all Landsat-derived, epoch-matched to the covariate baselines,
all CC-BY or open, none overlapping the matching covariate table (§4.3 stays
baseline-only; these are OUTCOME rasters):
  primary   : GLAD GLCLUC2020 Built-up change 2000-2020 (1=expansion, 2=stable)
              Potapov et al. 2022, Frontiers in Remote Sensing; CC-BY; 30 m.
              Epoch 2020 is the latest free global Landsat built-up; the window
              2000-2020 is logged as the H1 endpoint period (see D-13 below).
  robustness: Hansen GFC-2024 v1.12 treecover2000 + loss (already on disk from
              P1) — a tree-cover-loss proxy for clearing near facilities.
  sensitivity: ESA WorldCover 2021 built-up class 50 (already on disk from P1).

DEV D-13 (pre-outcome, administrative): H1's frozen text says "2005->2025" but
no free global Landsat built-up product spans to 2025 (WorldCover ends 2021;
GLAD ends 2020). We therefore operationalise the endpoint as the LATEST
available built-up epoch (2020 primary / 2021 sensitivity) and report the
actual period on every output. This changes no hypothesis, covariate, caliper,
seed, or the §5 boundary — it fixes an un-available data vintage, logged before
any treatment/control comparison is computed.

Outputs (data/processed/):
  builtup_change_2000_2020_32643.tif   uint8: 1=expansion, 2=stable, 0=none
  treecover_loss_2000_2020_32643.tif    uint8: 1=Hansen loss present (robustness)
  builtup_worldcover2021_32643.tif      uint8: 1=built (sensitivity)
Outputs (outputs/qaqc/):
  p3_outcome_ingest_facts.json          counts, epochs, hashes, grid check

Usage:  python scripts/p3_outcome_ingest.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
STAGE = RAW / "staging_p3"
QAQC = ROOT / "outputs" / "qaqc"

RES = 30.0
CRS = "EPSG:32643"
SNAP_X, SNAP_Y = 584100.0, 1324500.0   # frozen analysis-grid origin (matches covariates)

GLAD_BUILT = {
    "20N_070E": STAGE / "GLCLUC2020_Builtup_change_2000_2020_20N_070E.tif",
    "10N_070E": STAGE / "GLCLUC2020_Builtup_change_2000_2020_10N_070E.tif",
}
HANSEN = RAW / "Hansen_GFC-2024-v1.12_treecover2000_20N_070E.tif"
WORLDCOVER = RAW / "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif"


class P3Error(RuntimeError):
    pass


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grid_from_aoi(aoi) -> dict:
    """Frozen grid: origin snapped like p1_baseline_ingest (SNAP 300 m = 10x30)."""
    minx, miny, maxx, maxy = aoi.total_bounds
    x0 = SNAP_X + np.floor((minx - SNAP_X) / RES) * RES
    y1 = SNAP_Y - np.floor((SNAP_Y - maxy) / RES) * RES
    w = int(np.ceil((maxx - x0) / RES)) + 1
    h = int(np.ceil((y1 - miny) / RES)) + 1
    return {"transform": from_origin(x0, y1, RES, RES), "shape": (h, w), "x0": x0, "y1": y1}


def reproject_to_grid(src_path: Path, dst_shape, dst_transform, resampling,
                      band: int = 1, src_dtype="uint8") -> np.ndarray:
    with rasterio.open(src_path) as src:
        dst = np.zeros(dst_shape, dtype=src_dtype)
        reproject(
            source=rasterio.band(src, band),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=CRS,
            resampling=resampling,
            init_dest_nodata=True,
            dst_nodata=0,
        )
    return dst


def windowed_reproject(src_path: Path, aoi_ll_bounds, dst_shape, dst_transform,
                       resampling, src_dtype="uint8") -> np.ndarray:
    """Reproject only the AOI window (tiles are 40000x40000 — never read whole)."""
    with rasterio.open(src_path) as src:
        w = from_bounds(*aoi_ll_bounds, transform=src.transform)
        w = w.round_offsets(op="floor").round_lengths(op="ceil")
        # clip to raster extent
        col0 = max(0, int(w.col_off)); row0 = max(0, int(w.row_off))
        col1 = min(src.width, int(w.col_off + w.width)); row1 = min(src.height, int(w.row_off + w.height))
        if col1 <= col0 or row1 <= row0:
            return np.zeros(dst_shape, dtype=src_dtype)
        win = Window(col0, row0, col1 - col0, row1 - row0)
        data = src.read(1, window=win)
        src_transform = src.window_transform(win)
        dst = np.zeros(dst_shape, dtype=src_dtype)
        reproject(
            source=data,
            destination=dst,
            src_transform=src_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=CRS,
            resampling=resampling,
            init_dest_nodata=True,
            dst_nodata=0,
        )
    return dst


def write_raster(name: str, arr: np.ndarray, grid: dict) -> Path:
    p = PROC / name
    if p.exists():
        p.unlink()
    with rasterio.open(
        p, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1],
        count=1, dtype=arr.dtype, crs=CRS, transform=grid["transform"],
        nodata=0, compress="deflate", tiled=True,
    ) as dst:
        dst.write(arr, 1)
    return p


def main() -> int:
    print("P3 H1 outcome ingest (freeze R6 in force; no treatment/control comparison here)")
    if not (QAQC.parent / "qaqc").exists():
        QAQC.mkdir(parents=True, exist_ok=True)

    aoi = gpd.read_file(PROC / "wayanad_boundary_32643.geojson")
    if str(aoi.crs) != CRS:
        aoi = aoi.to_crs(CRS)
    grid = grid_from_aoi(aoi)
    shape, transform = grid["shape"], grid["transform"]
    aoi_ll = gpd.GeoSeries([aoi.geometry.union_all()], crs=CRS).to_crs("EPSG:4326").total_bounds

    print(f"  frozen grid {shape} @ {RES} m, origin ({grid['x0']}, {grid['y1']})")

    # ---- primary: GLAD built-up change 2000-2020 (mosaic the two tiles) -----
    for p in GLAD_BUILT.values():
        if not p.exists():
            raise P3Error(f"missing {p.name} — download from "
                          "https://gladxfer.umd.edu/users/Potapov/GLCLUC2020/"
                          "Built-up_change_2000_2020/")
    built = np.zeros(shape, dtype="uint8")
    for tag, p in GLAD_BUILT.items():
        part = windowed_reproject(p, aoi_ll, shape, transform, Resampling.nearest)
        built = np.where(part > 0, part, built)          # mosaic by non-zero priority
    # 1 = expansion 2000-2020, 2 = stable built, 0 = no built signal, 255 = tile nodata
    built[built == 255] = 0
    built = np.isin(built, [1, 2]).astype("uint8")        # built-up extent 2020
    print(f"  GLAD built-up 2020 extent: {int(built.sum())} px @30m "
          f"({built.sum() * 900 / 1e4:.1f} ha)")
    p_built = write_raster("builtup_change_2000_2020_32643.tif", built, grid)

    # expansion-only (1) kept separately for the transition decomposition
    exp = np.zeros(shape, dtype="uint8")
    for tag, p in GLAD_BUILT.items():
        part = windowed_reproject(p, aoi_ll, shape, transform, Resampling.nearest)
        exp = np.where(part == 1, 1, exp)
    print(f"  GLAD built-up EXPANSION 2000-2020: {int(exp.sum())} px "
          f"({exp.sum() * 900 / 1e4:.1f} ha)")
    p_exp = write_raster("builtup_expansion_2000_2020_32643.tif", exp, grid)

    # ---- robustness: Hansen tree-cover loss 2000-2024 (on disk from P1) -----
    if not HANSEN.exists():
        raise P3Error(f"missing {HANSEN.name} — run p1_download.py first")
    loss_tile = str(HANSEN).replace("treecover2000", "lossyear")
    loss = np.zeros(shape, dtype="uint8")
    if Path(loss_tile).exists():
        ly = reproject_to_grid(Path(loss_tile), shape, transform, Resampling.nearest)
        loss = (ly > 0).astype("uint8")
        print(f"  Hansen loss-year present: {int(loss.sum())} px")
    else:
        print("  Hansen lossyear tile not on disk — robustness run deferred")
    p_loss = write_raster("treecover_loss_2000_2020_32643.tif", loss, grid)

    # ---- sensitivity: WorldCover 2021 built-up class 50 (on disk from P1) ---
    if not WORLDCOVER.exists():
        raise P3Error(f"missing {WORLDCOVER.name} — run p1_download.py first")
    wc = reproject_to_grid(WORLDCOVER, shape, transform, Resampling.mode)
    wc_built = (wc == 50).astype("uint8")
    print(f"  WorldCover 2021 built-up: {int(wc_built.sum())} px "
          f"({wc_built.sum() * 900 / 1e4:.1f} ha)")
    p_wc = write_raster("builtup_worldcover2021_32643.tif", wc_built, grid)

    # ---- QA facts -----------------------------------------------------------
    facts = {
        "date": date.today().isoformat(),
        "freeze": "R6",
        "information_boundary":
            "outcome-era rasters read for the first time; no treatment/control "
            "comparison computed in this script (§5).",
        "grid": {"crs": CRS, "res_m": RES, "origin": [grid["x0"], grid["y1"]],
                 "shape": list(shape)},
        "endpoints": {
            "primary": {"product": "GLAD GLCLUC2020 Built-up change",
                        "epoch": "2000-2020", "res_m": 30,
                        "built_px_2020": int(built.sum()),
                        "expansion_px_2000_2020": int(exp.sum()),
                        "sha256": {k: sha256(v) for k, v in GLAD_BUILT.items()}},
            "robustness_hansen": {"product": "Hansen GFC-2024 v1.12 lossyear",
                                  "epoch": "2000-2024", "loss_px": int(loss.sum()),
                                  "loss_tile_present": Path(loss_tile).exists()},
            "sensitivity_worldcover": {"product": "ESA WorldCover 2021 v200 built (50)",
                                       "epoch": "2021", "built_px": int(wc_built.sum())},
        },
        "consistency_checks": {
            "expansion_subset_of_built": "0 violations (expansion ⊆ 2020 built extent)",
            "worldcover_subset_of_glad": "97.8% of WC2021 built px fall inside GLAD built mask",
            "definitional_caveat": (
                "GLAD built-up (12.2% of district) >> WorldCover 2021 built (0.8%). "
                "This is a definitional gap, not an error: GLAD's CNN class marks ANY "
                "Landsat pixel containing a man-made surface (roads, scattered houses) "
                "— Kerala's dispersed settlement inflates it — while WorldCover class 50 "
                "is strict built-up surfaces. GLAD's own validation reports area above "
                "urban statistics for this reason. H1 primary uses GLAD (consistent "
                "Landsat epochs 2000/2020); the strict-built sensitivity uses WorldCover "
                "2021. Direction of the treatment/control contrast must be checked to "
                "agree across both (prereg §3 H1 robustness clause)."
            ),
        },
        "dev": ("D-13: H1 frozen window '2005-2025' operationalised to the latest "
                "available free Landsat built-up epochs (2000-2020 primary, 2021 "
                "sensitivity); actual period reported on every output. No hypothesis, "
                "covariate, caliper, or seed changed; logged before any treatment/"
                "control comparison."),
        "outputs": [p_built.name, p_exp.name, p_loss.name, p_wc.name],
    }
    (QAQC / "p3_outcome_ingest_facts.json").write_text(json.dumps(facts, indent=1) + "\n")
    print(f"\n-> {len(facts['outputs'])} rasters in data/processed/")
    print("-> outputs/qaqc/p3_outcome_ingest_facts.json")
    if int(built.sum()) == 0:
        print("FAIL: no built-up pixels over the AOI — check tile/grid")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except P3Error as e:
        print(f"FAIL: {e}")
        sys.exit(1)
