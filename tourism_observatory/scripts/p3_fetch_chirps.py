#!/usr/bin/env python3
"""P3 D-20 — CHIRPS v2.0 0.05-degree monthly fetch + rainfall covariate prep.

Implements prereg SS7 D-20 (freeze R8, pinned BEFORE any rainfall statistic):

  source    CHIRPS v2.0 global monthly 0.05-degree GeoTIFFs (UCSB Climate
            Hazards Center, public domain; Funk et al. 2015 attribution).
            Monthly per-year files under
            products/CHIRPS/v2.0/global_monthly/tifs/chirps-v2.0.{Y}.{M}.tif.gz
  window    record window 2011-2014, bbox 75.70-76.50 E / 11.40-12.02 N
            (district + margin, per D-20(b))
  artifacts data/raw/chirps_v2_monthly_2011_2014_wayanad_bbox_4326.tif
              (48-band stack, native CHIRPS grid, bboxsubset)
            data/processed/chirps_rain_annual_2011_2014_32643.tif
              (500 m grid cell pixels, origin-aligned to the H3 CellIndex)
            data/processed/chirps_rain_monsoon_share_2011_2014_32643.tif
  derivation rain_annual_total_mm_2011_2014 = mean over years of annual sum
             rain_monsoon_jun_sep_share = mean over years of Jun-Sep share
             bilinear warp to the 500 m grid (D-20(b))
  fallback  IMD 0.25-degree (Pai et al. 2014) only if CHIRPS unusable
            (D-20(c)) - not triggered here.

Downloads go to /tmp/opencode (transient); only the subset stack and the
derived covariate rasters enter data/ (manifest entries follow the run).

Usage:  python scripts/p3_fetch_chirps.py
"""
from __future__ import annotations

import gzip
import io
import sys
import time
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from rasterio.io import MemoryFile
from rasterio.warp import reproject, Resampling
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = ROOT / "data/raw", ROOT / "data/processed"
DISTRICT_PATH = ROOT / "data/raw/geoBoundaries-IND-ADM2_simplified.geojson"

BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/tifs"
YEARS = (2011, 2012, 2013, 2014)
BBOX = (75.70, 11.40, 76.50, 12.02)          # D-20(b)
GRID_M = 500.0
NODATA = np.float32(-9999.0)
UA = {"User-Agent": "tourism-observatory-research (academic reproducibility)"}
TMP = Path("/tmp/opencode/chirps_gz")

STACK_OUT = RAW / "chirps_v2_monthly_2011_2014_wayanad_bbox_4326.tif"
ANNUAL_OUT = PROC / "chirps_rain_annual_2011_2014_32643.tif"
MONSOON_OUT = PROC / "chirps_rain_monsoon_share_2011_2014_32643.tif"


def district_geom() -> tuple:
    adm = gpd.read_file(DISTRICT_PATH)
    adm = adm[adm.shapeName.str.contains("Wayanad", case=False, na=False)]
    district = unary_union(adm.to_crs("EPSG:32643").geometry)
    return district.bounds


def fetch_one(y: int, m: int) -> np.ndarray:
    """Download (cached in /tmp) and window-read one CHIRPS month."""
    name = f"chirps-v2.0.{y}.{m:02d}.tif.gz"
    TMP.mkdir(parents=True, exist_ok=True)
    gz_path = TMP / name
    if not gz_path.exists():
        for attempt in range(3):
            try:
                req = urllib.request.Request(f"{BASE}/{name}", headers=UA)
                buf = bytearray()
                with urllib.request.urlopen(req, timeout=120) as r:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        buf.extend(chunk)
                gz_path.write_bytes(bytes(buf))
                break
            except Exception:  # noqa: BLE001 - network, retry
                if attempt == 2:
                    raise
                time.sleep(5)
    raw = gzip.decompress(gz_path.read_bytes())
    with MemoryFile(raw) as mf:
        with mf.open() as src:
            res = src.res  # (lon, lat) degrees
            ox, oy = src.transform.c, src.transform.f  # top-left origin (lon, lat)
            x0, y0, x1, y1 = BBOX
            c0 = max(int(np.floor((x0 - ox) / res[0])) - 1, 0)
            c1 = min(int(np.ceil((x1 - ox) / res[0])) + 1, src.width)
            r0 = max(int(np.floor((oy - y1) / abs(res[1]))) - 1, 0)
            r1 = min(int(np.ceil((oy - y0) / abs(res[1]))) + 1, src.height)
            win = rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0)
            a = src.read(1, window=win).astype(np.float32)
            wtr = src.window_transform(win)
    a[a < 0] = NODATA  # CHIRPS missing values are negative
    return a, wtr


def main() -> int:
    b = district_geom()
    x0 = float(np.floor(b[0] / GRID_M) * GRID_M)
    y0 = float(np.floor(b[1] / GRID_M) * GRID_M)
    nx = int(np.ceil((b[2] - x0) / GRID_M))
    ny = int(np.ceil((b[3] - y0) / GRID_M))
    print(f"district bounds -> 500 m grid origin ({x0:.0f},{y0:.0f}) "
          f"{nx}x{ny} cells", flush=True)

    months, stack, wtr_ref = [], [], None
    for y in YEARS:
        for m in range(1, 13):
            a, wtr = fetch_one(y, m)
            if wtr_ref is None:
                wtr_ref, ref_shape = wtr, a.shape
            else:
                assert a.shape == ref_shape and not np.allclose(wtr, wtr_ref) is False
            stack.append(a)
            months.append((y, m))
            print(f"  {y}-{m:02d}: min {a.min():.1f} max {a.max():.1f} "
                  f"mean {a.mean():.1f} mm", flush=True)

    arr = np.stack(stack)                      # (48, h, w)
    valid = arr != NODATA
    print(f"bbox subset: {arr.shape[1]}x{arr.shape[2]} px @0.05deg, "
          f"48 months, nodata px {int((~valid).sum())} "
          f"(of {arr.size})", flush=True)

    # ---- native-grid stack -> data/raw ------------------------------------
    prof = {"driver": "GTiff", "width": arr.shape[2], "height": arr.shape[1],
            "count": 48, "dtype": "float32", "transform": wtr_ref,
            "crs": "EPSG:4326", "nodata": float(NODATA)}
    with rasterio.open(STACK_OUT, "w", **prof) as dst:
        dst.write(arr)
        dst.descriptions = tuple(f"chirps_{y}_{m:02d}" for y, m in months)

    # ---- derive annual total + Jun-Sep share (native grid) -----------------
    annual_tot = np.full(arr.shape[1:], NODATA, dtype=np.float32)
    mshare = np.full(arr.shape[1:], NODATA, dtype=np.float32)
    ani = np.arange(4) * 12
    with np.errstate(invalid="ignore"):
        for k in range(4):                     # per year
            yr = arr[ani[k]:ani[k] + 12]
            tot = np.where(valid[ani[k]:ani[k] + 12], yr, 0).sum(0)
            mon = yr[6:10].sum(0)              # Jun, Jul, Aug, Sep bands
            complete = valid[ani[k]:ani[k] + 12].all(0) & (tot > 0)
            if k == 0:
                annual_sum = np.where(complete, tot, 0)
                share_sum = np.where(complete, np.where(tot > 0, mon / tot, 0), 0)
                nyears = complete.astype(np.float32)
            else:
                annual_sum += np.where(complete, tot, 0)
                share_sum += np.where(complete, np.where(tot > 0, mon / tot, 0), 0)
                nyears += complete
        ok = nyears > 0
        annual_tot[ok] = (annual_sum[ok] / nyears[ok]).astype("float32")
        mshare[ok] = (share_sum[ok] / nyears[ok]).astype("float32")
    print(f"native-grid annual total: min {annual_tot[annual_tot != NODATA].min():.0f} "
          f"max {annual_tot[annual_tot != NODATA].max():.0f} mm; "
          f"monsoon share min {mshare[mshare != NODATA].min():.3f} "
          f"max {mshare[mshare != NODATA].max():.3f}", flush=True)

    # ---- bilinear warp to the origin-aligned 500 m grid (D-20(b)) ----------
    # target transform: pixel k spans [x0 + k*500, x0+(k+1)*500); its CENTRE
    # is x0 + (k+0.5)*500 = exact cell centre -> 1:1 with h3.CellIndex.
    tgt_tr = Affine(GRID_M, 0, x0, 0, -GRID_M, y0 + ny * GRID_M)
    for out_path, srcv in ((ANNUAL_OUT, annual_tot), (MONSOON_OUT, mshare)):
        dstv = np.full((ny, nx), NODATA, dtype=np.float32)
        reproject(srcv, dstv, src_transform=wtr_ref, src_crs="EPSG:4326",
                  dst_transform=tgt_tr, dst_crs="EPSG:32643",
                  src_nodata=float(NODATA), dst_nodata=float(NODATA),
                  resampling=Resampling.bilinear)
        prof2 = {"driver": "GTiff", "width": nx, "height": ny, "count": 1,
                 "dtype": "float32", "transform": tgt_tr,
                 "crs": "EPSG:32643", "nodata": float(NODATA),
                 "compress": "deflate"}
        with rasterio.open(out_path, "w", **prof2) as dst:
            dst.write(dstv, 1)
        v = dstv[dstv != NODATA]
        print(f"{out_path.name}: {int(v.size)} valid cell px, "
              f"min {v.min():.1f} max {v.max():.1f} "
              f"mean {v.mean():.1f}", flush=True)

    print("\nstack ->", STACK_OUT.relative_to(ROOT))
    print("annual ->", ANNUAL_OUT.relative_to(ROOT))
    print("monsoon ->", MONSOON_OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
