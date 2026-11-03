#!/usr/bin/env python3
"""P7 — D-21 descriptive 2000-vs-now land-cover accounting (prereg §7 D-21, R9).

DESCRIPTIVE ONLY. No hypothesis, no test, no p-value, no CI, no causal
language. Rule pinned and hashed before this script was run:
  D-21 → R9 = bcaa9223... (see docs/PROJECTSTATE.md)

Inputs (all already in data/manifest.json; no downloads):
  GLAD GLCLUC2020 built-up change/expansion 2000-2020 (30 m)
  Hansen GFC-2024 v1.12 treecover2000 + lossyear (30 m)
  ESA WorldCover 2021 (10 m → 30 m grid, class 10 cross-check)
  WDPA all-touched mask, district boundary, verified-facility universe

Outputs:
  outputs/qaqc/p7_2000_vs_now_accounting_2026-11-03.json   (facts of record)
  outputs/qaqc/p7_500m_display_32643.tif                   (7 display bands)

Usage: python scripts/p7_2000_vs_now.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.warp import Resampling, reproject
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import p3_h3_analysis as h3  # noqa: E402  (CellIndex / grid of record)

PROC = h3.PROC
QA = h3.QA
DISTRICT = PROC / "wayanad_boundary_32643.geojson"
BUILT = PROC / "builtup_change_2000_2020_32643.tif"
EXP = PROC / "builtup_expansion_2000_2020_32643.tif"
TC2000 = PROC / "hansen_treecover2000_32643.tif"
LOSSYEAR = PROC / "hansen_lossyear_32643.tif"
WC2021 = PROC / "worldcover_2021_32643.tif"
WDPA = PROC / "wdpa_all_touched_32643.tif"
FACS = PROC / "facility_existence_universe_2026-10-23.csv"

CANOPY_MIN = 30          # D-21(b): forest 2000 = treecover2000 >= 30 %
FAC_BUF = 500.0          # D-21(e): 500 m facility buffers (H1 radius of record)
FACT_DATE = "2026-11-03"


def load_district():
    adm = gpd.read_file(DISTRICT)
    adm = adm[adm.shapeName.str.contains("Wayanad", case=False, na=False)]
    return unary_union(adm.to_crs("EPSG:32643").geometry)


def read(path):
    with rasterio.open(path) as s:
        a = s.read(1)
        return a, s.transform, s.crs, s.nodata, s.shape


def px_area_km2(t):
    return abs(t.a * t.e) / 1e6


def mask_in(geom, transform, shape):
    """Pixel-centre-in-district mask (all_touched=False), D-21 grid rule."""
    return geometry_mask([geom], out_shape=shape, transform=transform,
                         invert=True, all_touched=False)


def shares_500m(m30, t30, ci, n):
    """Share of each 500 m cell's district area where `m30` is True.

    Denominator = all 30 m pixels whose centre falls in a retained cell, so
    the value is "fraction of cell area"; cells with no in-district pixels
    stay NaN.
    """
    h, w = m30.shape
    rows, cols = np.mgrid[0:h, 0:w]
    xs = (t30.c + (cols + 0.5) * t30.a).ravel()
    ys = (t30.f + (rows + 0.5) * t30.e).ravel()
    ii = ci(xs, ys)
    ok = (ii >= 0) & m30.ravel()
    num = np.bincount(ii[ok], minlength=n)
    den = np.bincount(ii[ii >= 0], minlength=n)
    return np.where(den > 0, num / np.maximum(den, 1), np.nan)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    district = load_district()
    area_km2 = district.area / 1e6
    print(f"district area: {area_km2:.2f} km2")

    # ---------------- built-up (GLAD, 30 m) ----------------
    built, tb, _, _, shp_b = read(BUILT)
    exp, te, _, _, shp_e = read(EXP)
    assert shp_b == shp_e and tb == te, "GLAD rasters not on one grid"
    dm_b = mask_in(district, tb, shp_b)
    ext2020 = (built > 0) & dm_b
    expa = (exp > 0) & dm_b
    ext2000 = ext2020 & ~expa
    pa_b = px_area_km2(tb)

    def km2(mask):
        return float(mask.sum() * pa_b)

    # WDPA on the GLAD grid (nearest)
    wd, tw, _, _, sw = read(WDPA)
    wdpa_b = np.zeros(shp_b, dtype="uint8")
    reproject(wd.astype("uint8"), wdpa_b, src_transform=tw,
              src_crs="EPSG:32643", dst_transform=tb, dst_crs="EPSG:32643",
              resampling=Resampling.nearest)
    wdm_b = (wdpa_b > 0) & dm_b

    # ---------------- forest (Hansen, 30 m) ----------------
    tc, th, _, nod_tc, shp_h = read(TC2000)
    ly, tl, _, nod_ly, shp_l = read(LOSSYEAR)
    assert shp_h == shp_l and th == tl, "Hansen rasters not on one grid"
    dm_h = mask_in(district, th, shp_h)
    # WDPA on the Hansen grid too (the two products sit on different grids)
    wdpa_h = np.zeros(shp_h, dtype="uint8")
    reproject(wd.astype("uint8"), wdpa_h, src_transform=tw,
              src_crs="EPSG:32643", dst_transform=th, dst_crs="EPSG:32643",
              resampling=Resampling.nearest)
    wdm_h = (wdpa_h > 0) & dm_h
    valid_h = (tc != nod_tc) & (ly != nod_ly) & dm_h
    forest2000 = (tc >= CANOPY_MIN) & valid_h
    in10 = forest2000 & (ly >= 1) & (ly <= 10)
    in20 = forest2000 & (ly >= 11) & (ly <= 20)
    in24 = forest2000 & (ly >= 21) & (ly <= 24)
    loss_any = forest2000 & (ly >= 1) & (ly <= 24)
    forest2020 = forest2000 & ~((ly >= 1) & (ly <= 20))
    forest2024 = forest2000 & ~((ly >= 1) & (ly <= 24))
    pa_h = px_area_km2(th)

    def km2h(mask):
        return float(mask.sum() * pa_h)

    annual = {int(y): km2h(forest2000 & (ly == y)) for y in range(1, 25)}

    # WorldCover 2021 tree class cross-check
    wc, twc, _, nod_wc, shp_wc = read(WC2021)
    dm_wc = mask_in(district, twc, shp_wc)
    tree_wc = (wc == 10) & dm_wc & ((wc != nod_wc) if nod_wc else True)

    # ---------------- facility 500 m buffer context (non-inferential) ------
    fac = pd.read_csv(FACS)
    fac_g = gpd.GeoDataFrame(fac, geometry=gpd.points_from_xy(fac.lon, fac.lat),
                             crs="EPSG:4326").to_crs("EPSG:32643")
    ver = fac_g[fac_g.verified.fillna(False).astype(bool) &
                fac_g.inside_district.fillna(False).astype(bool)]
    fac_union = unary_union([g.buffer(FAC_BUF) for g in ver.geometry])
    fb = rasterize([(fac_union, 1)], out_shape=shp_b, transform=tb,
                   fill=0, all_touched=True, dtype="uint8").astype(bool)
    fb = fb & dm_b
    fac_share_district = km2(fb) / area_km2
    exp_in_buf = km2(expa & fb)
    exp_share_in_buf = exp_in_buf / km2(expa)

    # ---------------- 500 m display stack ----------------
    ci = h3.CellIndex(district)
    n = ci.n
    bands = {
        "built_share_2000": shares_500m(ext2000, tb, ci, n),
        "built_share_2020": shares_500m(ext2020, tb, ci, n),
        "built_expansion_share": shares_500m(expa, tb, ci, n),
        "forest_share_2000": shares_500m(forest2000, th, ci, n),
        "forest_share_2020": shares_500m(forest2020, th, ci, n),
        "forest_share_2024": shares_500m(forest2024, th, ci, n),
    }
    # loss magnitude per cell (share of cell, from the forest-share bands)
    bands["loss_share_2001_2024"] = np.clip(
        bands["forest_share_2000"] - bands["forest_share_2024"], 0, None)
    # loss 2021-2024 = forest state 2020 minus forest state 2024
    bands["loss_share_2021_2024"] = np.clip(
        bands["forest_share_2020"] - bands["forest_share_2024"], 0, None)
    # dominant loss decade per cell (0 none, 1 2001-10, 2 2011-20, 3 2021-24)
    dec = np.zeros_like(ly, dtype="uint8")
    dec[in10] = 1
    dec[in20] = 2
    dec[in24] = 3
    h, w = ly.shape
    rows, cols = np.mgrid[0:h, 0:w]
    xs = (th.c + (cols + 0.5) * th.a).ravel()
    ys = (th.f + (rows + 0.5) * th.e).ravel()
    ii = ci(xs, ys)
    ok = (ii >= 0) & (dec.ravel() > 0)
    counts = np.zeros((n, 4))
    for k in (1, 2, 3):
        m = ok & (dec.ravel() == k)
        counts[:, k] = np.bincount(ii[m], minlength=n)
    dom = np.where(counts[:, 1:].sum(1) > 0, counts[:, 1:].argmax(1) + 1, 0)
    dom = dom.astype("uint8")
    dom2d = np.zeros((ci.ny, ci.nx), dtype="uint8")
    dom2d[ci.lut >= 0] = dom

    tr = _cell_transform(ci)

    def cellstack():
        out = np.full((len(bands) + 1, ci.ny, ci.nx), np.nan, dtype="float32")
        for i, (k, v) in enumerate(bands.items()):
            out[i][ci.lut >= 0] = v
        out[-1] = np.where(ci.lut >= 0, dom2d, np.nan)
        return out

    stack = cellstack()
    QA.mkdir(parents=True, exist_ok=True)
    disp = QA / f"p7_500m_display_32643.tif"
    with rasterio.open(disp, "w", driver="GTiff", height=ci.ny, width=ci.nx,
                       count=stack.shape[0], dtype="float32",
                       crs="EPSG:32643", transform=tr, nodata=-9999.0) as dst:
        # NaN cannot be a GTiff nodata sentinel reliably — write -9999 and
        # mask on read (a real 0.0 means "0 % of the cell", not missing).
        dst.write(np.where(np.isfinite(stack), stack, -9999.0).astype("float32"))
        for i, k in enumerate(list(bands) + ["loss_decade_dominant"], 1):
            dst.set_band_description(i, k)

    facts = {
        "task": "P7 / D-21 descriptive 2000-vs-now accounting",
        "prereg": {"pin": "D-21", "freeze": "R9",
                   "sha256": "bcaa92235ae1d92ce377b23f9da47946d6a176ccc05343715c24d99a06fe508b"},
        "inferential": False,
        "label": "descriptive accounting, no test, no p-value, no CI",
        "date": FACT_DATE,
        "district": {"area_km2": round(area_km2, 2),
                     "boundary_sha256": sha(DISTRICT)},
        "grids": {"built_30m": {"shape": list(shp_b), "px_km2": pa_b},
                  "hansen_30m": {"shape": list(shp_h), "px_km2": pa_h},
                  "display_500m": {"nx": ci.nx, "ny": ci.ny, "cells": n}},
        "builtup": {
            "product": "GLAD GLCLUC2020 built-up change 2000-2020",
            "extent_2000_km2": round(km2(ext2000), 3),
            "extent_2020_km2": round(km2(ext2020), 3),
            "expansion_2000_2020_km2": round(km2(expa), 3),
            "growth_factor_2000_to_2020": round(km2(ext2020) / km2(ext2000), 3),
            "pct_of_district_2000": round(100 * km2(ext2000) / area_km2, 3),
            "pct_of_district_2020": round(100 * km2(ext2020) / area_km2, 3),
            "inside_wdpa": {
                "extent_2000_km2": round(km2(ext2000 & wdm_b), 3),
                "extent_2020_km2": round(km2(ext2020 & wdm_b), 3),
                "expansion_km2": round(km2(expa & wdm_b), 3)},
            "outside_wdpa": {
                "extent_2000_km2": round(km2(ext2000 & ~wdm_b), 3),
                "extent_2020_km2": round(km2(ext2020 & ~wdm_b), 3),
                "expansion_km2": round(km2(expa & ~wdm_b), 3)},
            "worldcover2021_built_km2": None,
        },
        "forest": {
            "product": "Hansen GFC-2024 v1.12 treecover2000 / lossyear",
            "canopy_threshold_pct": CANOPY_MIN,
            "forest_2000_km2": round(km2h(forest2000), 3),
            "forest_2020_km2": round(km2h(forest2020), 3),
            "forest_2024_km2": round(km2h(forest2024), 3),
            "loss_2001_2010_km2": round(km2h(in10), 3),
            "loss_2011_2020_km2": round(km2h(in20), 3),
            "loss_2021_2024_km2": round(km2h(in24), 3),
            "loss_2001_2024_km2": round(km2h(loss_any), 3),
            "pct_forest2000_lost_2001_2020": round(100 * km2h(in10 | in20) / km2h(forest2000), 3),
            "pct_forest2000_lost_2001_2024": round(100 * km2h(loss_any) / km2h(forest2000), 3),
            "pct_of_district_forest2000": round(100 * km2h(forest2000) / area_km2, 3),
            "pct_of_district_forest2024": round(100 * km2h(forest2024) / area_km2, 3),
            "inside_wdpa": {
                "forest_2000_km2": round(km2h(forest2000 & wdm_h), 3),
                "loss_2001_2024_km2": round(km2h(loss_any & wdm_h), 3)},
            "outside_wdpa": {
                "forest_2000_km2": round(km2h(forest2000 & ~wdm_h), 3),
                "loss_2001_2024_km2": round(km2h(loss_any & ~wdm_h), 3)},
            "annual_loss_km2": {str(k): round(v, 3) for k, v in annual.items()},
            "worldcover2021_tree_km2_crosscheck": round(
                float(tree_wc.sum() * px_area_km2(twc)), 3),
        },
        "context_non_inferential": {
            "label": "context share only; H1 is the registered test",
            "facilities_verified": int(len(ver)),
            "buffer_m": FAC_BUF,
            "buffer_union_km2": round(km2(fb), 3),
            "buffer_share_of_district": round(fac_share_district, 4),
            "expansion_in_buffer_km2": round(exp_in_buf, 3),
            "expansion_share_in_buffer": round(exp_share_in_buf, 4),
            "share_ratio_expansion_vs_area": round(exp_share_in_buf / fac_share_district, 3),
        },
        "inputs_sha256": {p.name: sha(p) for p in
                          [BUILT, EXP, TC2000, LOSSYEAR, WC2021, WDPA]},
        "display_raster": {"path": str(disp.relative_to(ROOT)),
                           "bands": list(bands) + ["loss_decade_dominant"],
                           "sha256": sha(disp)},
        "notes": [
            "treecover_loss_2000_2020_32643.tif is `lossyear>0` (2001-2024) "
            "despite its filename; D-21 reads lossyear by code instead.",
            "Areas are pixel counts x 900 m2 on the frozen 30 m grids; "
            "district mask = pixel-centre-in-district.",
            "WorldCover 2021 tree area is a different product and is never "
            "averaged with Hansen.",
        ],
    }
    with rasterio.open(PROC / "builtup_worldcover2021_32643.tif") as s:
        wcb = s.read(1)
        dmw = mask_in(district, s.transform, wcb.shape)
        facts["builtup"]["worldcover2021_built_km2"] = round(
            float(((wcb > 0) & dmw).sum() * px_area_km2(s.transform)), 3)

    out = QA / f"p7_2000_vs_now_accounting_{FACT_DATE}.json"
    out.write_text(json.dumps(facts, indent=1))
    print(json.dumps(facts["builtup"], indent=1))
    print(json.dumps({k: v for k, v in facts["forest"].items()
                      if k != "annual_loss_km2"}, indent=1))
    print(json.dumps(facts["context_non_inferential"], indent=1))
    print(f"\nfacts -> {out.relative_to(ROOT)}  sha256 {sha(out)[:12]}")
    print(f"display -> {disp.relative_to(ROOT)}  sha256 {sha(disp)[:12]}")
    return 0


def _cell_transform(ci):
    from affine import Affine
    return Affine(500.0, 0, ci.x0, 0, -500.0, ci.y0 + ci.ny * 500.0)


if __name__ == "__main__":
    sys.exit(main())
