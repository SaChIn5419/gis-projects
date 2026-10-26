"""P2 step (a) — Sentinel-2 10 m existence-verification quicklooks (§2, Wayanad).

Preregistered rule (§2): "verify each candidate against imagery at ~10 m" —
facility EXISTENCE may be confirmed visually pre-freeze; imagery-based construction
DATING is NOT done here (post-freeze step, §5).

For every DISTINCT geocoded coordinate pair in registry_geocoded_<date>.csv (facilities
sharing a point share one imagery check), fetch the least-cloudy Sentinel-2 L2A scene
(cloud < 25 %, 2024-01-01 → present; widen on failure), read B04/B03/B02 at 10 m native
over a ±300 m window centred on the point (S2 native CRS = EPSG:32643, same as the
geocoded points), apply a per-scene 2–98 % stretch, overlay a red cross at the exact
point + 100 m reference circle, and save a labelled PNG.

Outputs (outputs/qaqc/p2_existence/):
  <locID>_<lat>_<lon>.png      — quicklook for visual inspection
  p2_existence_index.csv       — locID, coords, facility count + sl ids, precision
                                 mix, scene id / datetime / cloud
No verdicts are written here: verdicts are recorded AFTER visual inspection into
data/processed/facility_existence_verdicts_<date>.csv (separate manual step).

Usage:  python scripts/p2_existence_quicklooks.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import rasterio
from PIL import Image, ImageDraw
from pyproj import Transformer
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs" / "qaqc" / "p2_existence"

WINDOW_M = 300            # ± metres around each distinct point
RES = 10                  # Sentinel-2 native m
SCALE = 6                 # nearest-neighbour magnification for inspection
CLOUD_MAX = 25            # eo:cloud_cover filter
DATE_WIDE = "2023-01-01/2026-12-31"
DATE_PREFER = "2024-01-01/2026-12-31"
POINT_CRS = "EPSG:32643"


def stretch_rgb(b4: np.ndarray, b3: np.ndarray, b2: np.ndarray) -> np.ndarray:
    """Per-scene 2–98 % percentile stretch → uint8 RGB."""
    stack = np.stack([b4, b3, b2]).astype("float64")
    valid = stack[np.isfinite(stack) & (stack > 0)]
    if valid.size == 0:
        return np.zeros((b4.shape[0], b4.shape[1], 3), "uint8")
    lo, hi = np.percentile(valid, [2, 98])
    if hi <= lo:
        hi = lo + 1
    out = np.clip((stack - lo) / (hi - lo), 0, 1)
    return (out * 255).astype("uint8").transpose(1, 2, 0)


def find_scene(cat, x_pt: float, y_pt: float, lon: float, lat: float,
               w_lon: float, w_lat: float):
    """Least-cloudy S2 L2A scene whose raster FULLY covers the ±300 m window.

    x_pt/y_pt = point in EPSG:32643 (native); scenes failing CRS or coverage
    (MGRS tile edge / partial datatake) are skipped so a covering scene is found.
    """
    bbox = [lon - w_lon, lat - w_lat, lon + w_lon, lat + w_lat]
    for dt in (DATE_PREFER, DATE_WIDE):
        try:
            search = cat.search(
                collections=["sentinel-2-l2a"], bbox=bbox, datetime=dt,
                query={"eo:cloud_cover": {"lt": CLOUD_MAX}},
            )
            items = sorted(search.items(),
                           key=lambda i: (i.properties.get("eo:cloud_cover", 100),
                                          -i.datetime.timestamp()))  # latest among ties
        except Exception:
            continue
        for it in items:
            try:
                href = planetary_computer.sign(it.assets["B04"].href)
                with rasterio.open(href) as src:
                    if src.crs is None or src.crs.to_epsg() != 32643:
                        continue
                    b = src.bounds
                    if not (b.left <= x_pt - WINDOW_M and x_pt + WINDOW_M <= b.right
                            and b.bottom <= y_pt - WINDOW_M
                            and y_pt + WINDOW_M <= b.top):
                        continue
            except Exception:
                continue
            return it
    return None


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", help="CSV with lat/lon/facility_id/precision_class/"
                                     "name columns (universe mode)")
    ap.add_argument("--outdir", help="output subfolder name under outputs/qaqc/")
    args = ap.parse_args()
    global OUT
    if args.outdir:
        OUT = ROOT / "outputs" / "qaqc" / args.outdir

    if args.points:
        src_csv = Path(args.points)
        df = pd.read_csv(src_csv)
        assert {"lat", "lon", "facility_id", "precision_class", "name"} <= set(df.columns), \
            "points CSV must carry lat/lon/facility_id/precision_class/name"
        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        locs = (df.groupby(["lat", "lon"], sort=True)
                .agg(sl_ids=("facility_id", lambda s: ";".join(map(str, s))),
                     n=("facility_id", "size"),
                     precision=("precision_class",
                                 lambda s: "/".join(sorted(set(s)))),
                     names=("name", lambda s: " | ".join(
                         x.replace(",", ";") for x in s.head(3))))
                .reset_index())
        print(f"{src_csv}: {len(df)} facilities → {len(locs)} distinct locations")
    else:
        csvs = sorted(PROC.glob("registry_geocoded_*.csv"))
        csvs = [p for p in csvs if "_r1" not in p.stem]
        if not csvs:
            print("FAIL: no registry_geocoded_*.csv — run p1_registry_geocode.py")
            return 1
        src_csv = csvs[-1]
        df = pd.read_csv(src_csv)
        # distinct coordinate pairs, sorted deterministically (lat, lon)
        locs = (df.groupby(["lat", "lon"], sort=True)
                .agg(sl_ids=("sl", lambda s: ";".join(map(str, sorted(s)))),
                     n=("sl", "size"),
                     precision=("precision_class",
                                 lambda s: "/".join(sorted(set(s)))),
                     names=("name_address",
                            lambda s: " | ".join(x.replace(",", ";") for x in s.head(3))))
                .reset_index())
        print(f"{src_csv.name}: {len(df)} facilities → {len(locs)} distinct locations")
    OUT.mkdir(parents=True, exist_ok=True)

    cat = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace)

    rows, failures = [], []
    for i, r in locs.iterrows():
        loc_id = f"loc{i:02d}"
        lon, lat = float(r.lon), float(r.lat)
        w = WINDOW_M / (111_320 * np.cos(np.radians(lat)))   # deg ≈ m window
        tf = Transformer.from_crs("EPSG:4326", POINT_CRS, always_xy=True)
        x_pt, y_pt = tf.transform(lon, lat)
        it = find_scene(cat, x_pt, y_pt, lon, lat, w, w)
        if it is None:
            failures.append((loc_id, lat, lon, "no scene found"))
            print(f"  {loc_id}: NO SCENE")
            continue
        try:
            half_px = WINDOW_M // RES
            imgs = []
            for band in ("B04", "B03", "B02"):
                href = planetary_computer.sign(it.assets[band].href)
                with rasterio.open(href) as src:
                    # rasterio's index() returns (row, col)
                    row, col = src.index(x_pt, y_pt, op=round)
                    win = Window(col - half_px, row - half_px,
                                 2 * half_px, 2 * half_px)
                    arr = src.read(1, window=win, boundless=True, fill_value=0)
                    if arr.shape != (2 * half_px, 2 * half_px):
                        raise ValueError(f"bad shape {arr.shape}")
                    if band == "B04":
                        crs_ok = src.crs.to_epsg() == 32643
                imgs.append(arr.astype("float64"))
            if not crs_ok:
                raise ValueError("native crs != 32643")
        except Exception as e:  # tile edge / partial coverage → try next scene
            failures.append((loc_id, lat, lon, f"read failed: {e}"))
            print(f"  {loc_id}: read failed ({e})")
            continue

        rgb = stretch_rgb(*imgs)
        # non-blackness guard: fraction of non-zero (in-scene) pixels in window
        valid_frac = float((imgs[0] > 0).mean())
        if valid_frac < 0.5:
            failures.append((loc_id, lat, lon,
                             f"window coverage {valid_frac:.0%} — partial/edge"))
            print(f"  {loc_id}: window coverage {valid_frac:.0%} → skipped")
            continue
        im = Image.fromarray(rgb).resize(
            (rgb.shape[1] * SCALE, rgb.shape[0] * SCALE), Image.NEAREST)
        d = ImageDraw.Draw(im)
        cx = cy = im.size[0] // 2
        d.line([(cx - 18, cy), (cx + 18, cy)], fill=(255, 0, 0), width=3)
        d.line([(cx, cy - 18), (cx, cy + 18)], fill=(255, 0, 0), width=3)
        r_px = int((100 / RES) * SCALE)                      # 100 m circle
        d.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px],
                  outline=(255, 255, 0), width=2)
        label = (f"{loc_id} {r.n:.4f},{r.lon:.4f} n={r.n} {r.precision} "
                 f"| S2 {it.datetime.date()} cld={it.properties.get('eo:cloud_cover'):.0f}% "
                 f"| cross=point, yellow=100m")
        d.rectangle([0, 0, im.size[0], 18], fill=(0, 0, 0))
        d.text((3, 3), label, fill=(255, 255, 255))
        png = OUT / f"{loc_id}_{lat:.4f}_{lon:.4f}.png"
        im.save(png)

        rows.append({
            "loc_id": loc_id, "lat": lat, "lon": lon, "n_facilities": int(r.n),
            "sl_ids": r.sl_ids, "precision_mix": r.precision,
            "names_head": r.names,
            "scene_id": it.id, "scene_date": it.datetime.date().isoformat(),
            "scene_cloud_pct": round(float(it.properties.get("eo:cloud_cover")), 1),
            "valid_px_frac": round(valid_frac, 3),
            "window_m": WINDOW_M, "png": str(png.relative_to(ROOT)),
        })
        print(f"  {loc_id}: n={r.n} {r.precision} → {png.name} "
              f"(cld {rows[-1]['scene_cloud_pct']}%)")

    idx = pd.DataFrame(rows)
    idx.to_csv(OUT / "p2_existence_index.csv", index=False)
    print(f"\nquicklooks: {len(idx)}/{len(locs)} → {OUT.relative_to(ROOT)}/")
    if failures:
        print("failures:", failures)
    return 0 if len(idx) == len(locs) else 1


if __name__ == "__main__":
    sys.exit(main())
