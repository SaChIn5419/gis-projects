"""P2 step (c) — 1 km equal-area parcel grid + BASELINE covariate tables (Wayanad).

Preregistered rules this implements (§4, frozen):
  1. Units: equal-area parcels over the AOI (target ~1 km grid). Implementation:
     1000 m cells anchored on the FROZEN analysis-grid origin (584100, 1324500),
     EPSG:32643. Parcels kept when their centroid falls inside the AOI mask.
  3. Matching covariates (pre-period/baseline ONLY, 2000–2005; §4.3):
       mean slope                 (caliper ±3°)
       mean elevation             (caliper ±100 m)
       baseline LULC composition  (CCI-LC 2005 class shares; caliper ±10 pp
                                   per dominant class)
       baseline Hansen tree cover (2000, caliper ±10 pp)
       road-access class          (OSM road distance tercile; current-network
                                   proxy labelled per dev-D-4)
     No post-2005 variables enter this table (WorldCover 2021 shares are
     deliberately NOT included — the matching covariate table stays baseline-only).
  4. Exclusions from BOTH arms: WDPA (all_touched raster), the 2024
     Chooralmala–Mundakkai scar zone, water bodies. Parcel-level implementation
     (logged P2 spec detail, no outcome viewed): a parcel is EXCLUDED from both
     arms when its eligible-pixel share (AOI ∩ ¬WDPA ∩ ¬water ∩ ¬scar) is
     < 50%; covariates are computed on eligible pixels only.

Information boundary (§5): covariate tables may be constructed and viewed.
No outcome rasters exist or are read here. If the scar layer
(data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg) is absent, the run
records scar_excluded=false and MUST be re-run after D-6 compilation before any
matching (enforced by p2_match.py).

Outputs (data/processed/):
  parcels_1km_32643.gpkg            — parcel polygons (parcel_id, eligibility)
  parcel_covariates_<date>.csv      — one row per parcel (baseline covariates)
Outputs (outputs/qaqc/):
  p2_parcel_facts.json              — counts, thresholds, usable-set means, seed

Usage:  python scripts/p2_parcel_covariates.py
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
QAQC = ROOT / "outputs" / "qaqc"

CELL = 1000.0                             # m, equal-area parcel size ("~1 km")
ORIGIN_X, ORIGIN_Y = 584100.0, 1324500.0  # frozen analysis-grid origin
CRS = "EPSG:32643"
MIN_ELIGIBLE_SHARE = 0.50                 # §4.4 arm-exclusion threshold (spec detail)
SEED = 20261022                           # project seed (prereg §4.5 / H2 MC)


class P2Error(RuntimeError):
    pass


def main() -> int:
    print("P2 parcel covariates — Wayanad (baseline covariates only, no outcomes)")
    aoi = gpd.read_file(PROC / "wayanad_boundary_32643.geojson")
    if aoi.crs is None or str(aoi.crs) != CRS:
        aoi = aoi.to_crs(CRS)
    aoi_geom = aoi.geometry.iloc[0]

    # ---- raster handles (all on the frozen 30 m grid) ----------------------
    def load(name: str):
        p = PROC / name
        if not p.exists():
            raise P2Error(f"missing input {name} — run p1_baseline_ingest.py first")
        return rasterio.open(p)

    dem_src = load("dem_copernicus30m_32643.tif")
    slope_src = load("slope_deg_32643.tif")
    wc_src = load("worldcover_2021_32643.tif")
    han_src = load("hansen_treecover2000_32643.tif")
    wdpa_src = load("wdpa_all_touched_32643.tif")
    mask_src = load("aoi_mask_32643.tif")
    rdist_src = load("road_dist_m_32643.tif")
    for s in (dem_src, slope_src, wc_src, han_src, wdpa_src, mask_src, rdist_src):
        assert (s.shape, s.transform) == (dem_src.shape, dem_src.transform), \
            f"grid mismatch: {s.name}"
    shape, transform = dem_src.shape, dem_src.transform

    dem = dem_src.read(1)
    slope = slope_src.read(1)
    wc = wc_src.read(1)
    han = han_src.read(1)
    wdpa = wdpa_src.read(1)
    aoi_mask = mask_src.read(1) == 1
    rdist = rdist_src.read(1)

    cci_path = PROC / "cci_lulc_2005_32643.tif"
    if not cci_path.exists():
        raise P2Error("missing cci_lulc_2005_32643.tif — baseline LULC required (§4.3)")
    cci_src = rasterio.open(cci_path)
    cci = cci_src.read(1)
    cci_transform, cci_shape = cci_src.transform, cci_src.shape

    # ---- scar zone (§4.4 exclusion; absent = re-run required before match) --
    scar_gpkg = PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg"
    scar_geoms: list = []
    if scar_gpkg.exists():
        scar = gpd.read_file(scar_gpkg)
        if scar.crs is None or str(scar.crs) != CRS:
            scar = scar.to_crs(CRS)
        scar_geoms = list(scar.geometry)
    scar_present = bool(scar_geoms)
    print(f"  scar layer: {'present' if scar_present else 'ABSENT — re-run after D-6 '
          'compilation (matching is barred until then)'}")

    # ---- eligible mask: AOI ∩ ¬water ∩ ¬WDPA ∩ ¬scar ----------------------
    water = wc == 80                       # WorldCover permanent water
    if scar_present:
        scar_mask = rasterize(((g, 1) for g in scar_geoms), out_shape=shape,
                              transform=transform, fill=0, all_touched=True,
                              dtype="uint8").astype(bool)
    else:
        scar_mask = np.zeros(shape, bool)
    eligible = aoi_mask & ~water & (wdpa != 1) & ~scar_mask

    # ---- 1 km parcel grid (anchored on the frozen origin) ------------------
    minx, miny, maxx, maxy = aoi.total_bounds
    k0 = math.floor((minx - ORIGIN_X) / CELL)
    k1 = math.ceil((maxx - ORIGIN_X) / CELL)
    j0 = math.floor((ORIGIN_Y - maxy) / CELL)
    j1 = math.ceil((ORIGIN_Y - miny) / CELL)

    cells = []                              # (parcel_id, k, j, geom) in row order
    for j in range(j0, j1):
        for k in range(k0, k1):
            x0 = ORIGIN_X + k * CELL
            y1 = ORIGIN_Y - j * CELL
            cells.append((f"p{j:03d}_{k:03d}", k, j, box(x0, y1 - CELL, x0 + CELL, y1)))
    n_cells = len(cells)
    print(f"  candidate cells in envelope: {n_cells}")

    zone = rasterize(((c[3], i + 1) for i, c in enumerate(cells)),
                     out_shape=shape, transform=transform, fill=0, dtype="int32")
    zone_cci = rasterize(((c[3], i + 1) for i, c in enumerate(cells)),
                         out_shape=cci_shape, transform=cci_transform,
                         fill=0, dtype="int32")

    cent = gpd.GeoSeries([c[3].centroid for c in cells], crs=CRS)
    cent_inside = cent.within(aoi_geom).to_numpy()
    print(f"  pixels assigned: {int((zone > 0).sum())}; "
          f"centroid-inside parcels: {int(cent_inside.sum())}")

    # ---- zonal statistics over ELIGIBLE pixels (all counts sized n_cells) --
    zi = zone[eligible]
    pid = zi - 1                            # 0-based cell index
    valid = pid >= 0
    pid = pid[valid]
    cnt = np.bincount(pid, minlength=n_cells).astype("float64")

    def zonal_mean(arr):
        v = arr[eligible][valid].astype("float64")
        s = np.bincount(pid, weights=v, minlength=n_cells)
        return np.divide(s, cnt, out=np.full(n_cells, np.nan), where=cnt > 0)

    elev_mean = zonal_mean(dem)
    slope_mean = zonal_mean(slope)
    han_mean = zonal_mean(han)
    rdist_mean = zonal_mean(rdist)

    # eligible share relative to ALL in-AOI pixels of each cell
    zi_all = zone[aoi_mask & (zone > 0)] - 1
    tot = np.bincount(zi_all, minlength=n_cells).astype("float64")
    elig_share = np.divide(cnt, tot, out=np.zeros(n_cells), where=tot > 0)

    # ---- CCI-LC 2005 class shares + dominant class (300 m nested grid) -----
    zc = zone_cci.ravel()
    sel = zc > 0
    pid_c = zc[sel] - 1
    cci_vals = cci.ravel()[sel]
    cci_tot = np.bincount(pid_c, minlength=n_cells).astype("float64")
    uniq = [int(u) for u in np.unique(cci_vals)]
    cci_share = {}
    for u in uniq:
        w = (cci_vals == u).astype("float64")
        s = np.bincount(pid_c, weights=w, minlength=n_cells)
        cci_share[u] = np.divide(s, cci_tot, out=np.zeros(n_cells),
                                 where=cci_tot > 0)
    share_mtx = np.stack([cci_share[u] for u in uniq], axis=1)
    dom_pos = share_mtx.argmax(axis=1)
    dom_class = np.array([uniq[p] for p in dom_pos], dtype="int32")
    dom_share = share_mtx[np.arange(n_cells), dom_pos]
    has_cci = cci_tot > 0

    # ---- assemble parcel table (centroid-inside rows, cell order) ----------
    rows = []
    for i, (pid_, k, j, _geom) in enumerate(cells):
        if not cent_inside[i]:
            continue
        row = {
            "parcel_id": pid_, "k": k, "j": j,
            "x0": ORIGIN_X + k * CELL, "y1": ORIGIN_Y - j * CELL,
            "pixels_total": int(tot[i]), "pixels_eligible": int(cnt[i]),
            "eligible_share": round(float(elig_share[i]), 4),
            "elev_mean_m": (round(float(elev_mean[i]), 2)
                            if not np.isnan(elev_mean[i]) else None),
            "slope_mean_deg": (round(float(slope_mean[i]), 3)
                               if not np.isnan(slope_mean[i]) else None),
            "hansen2000_mean_pct": (round(float(han_mean[i]), 2)
                                    if not np.isnan(han_mean[i]) else None),
            "road_dist_mean_m": (round(float(rdist_mean[i]), 1)
                                 if not np.isnan(rdist_mean[i]) else None),
            "cci2005_dominant": (int(dom_class[i]) if has_cci[i] else None),
            "cci2005_dominant_share": (round(float(dom_share[i]), 4)
                                       if has_cci[i] else None),
        }
        for u in uniq:
            row[f"cci2005_share_{u}"] = (round(float(cci_share[u][i]), 4)
                                         if has_cci[i] else None)
        rows.append(row)
    cov = pd.DataFrame(rows)

    cov["excluded_both_arms"] = cov["eligible_share"] < MIN_ELIGIBLE_SHARE
    usable = ~cov["excluded_both_arms"]
    cov["road_tercile"] = np.nan
    if usable.sum() >= 3:
        bins = pd.qcut(cov.loc[usable, "road_dist_mean_m"], 3, labels=[1, 2, 3],
                       duplicates="drop")
        cov.loc[usable, "road_tercile"] = bins.astype("float64")

    today = date.today().isoformat()
    out_csv = PROC / f"parcel_covariates_{today}.csv"
    cov.to_csv(out_csv, index=False)

    keep = [c for c, inc in zip(cells, cent_inside) if inc]
    assert len(keep) == len(cov) and \
        [c[0] for c in keep] == cov["parcel_id"].tolist(), "parcel order mismatch"
    gdf = gpd.GeoDataFrame(
        cov[["parcel_id", "excluded_both_arms", "eligible_share"]],
        geometry=[c[3] for c in keep], crs=CRS)
    gpkg = PROC / "parcels_1km_32643.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    gdf.to_file(gpkg, layer="parcels", driver="GPKG")

    u = cov[usable]
    facts = {
        "cell_m": CELL, "origin": [ORIGIN_X, ORIGIN_Y], "crs": CRS, "seed": SEED,
        "parcels_total": int(len(cov)),
        "parcels_excluded_both_arms": int((~usable).sum()),
        "parcels_usable": int(usable.sum()),
        "min_eligible_share_rule": MIN_ELIGIBLE_SHARE,
        "scar_excluded": scar_present,
        "coverage": {
            "parcels_with_elev": int(cov["elev_mean_m"].notna().sum()),
            "parcels_with_slope": int(cov["slope_mean_deg"].notna().sum()),
            "parcels_with_road_tercile": int(cov["road_tercile"].notna().sum()),
            "parcels_with_cci_dominant": int(cov["cci2005_dominant"].notna().sum()),
            "usable_mean_slope_deg": round(float(u["slope_mean_deg"].mean()), 3),
            "usable_mean_elev_m": round(float(u["elev_mean_m"].mean()), 1),
            "usable_mean_hansen2000_pct": round(float(u["hansen2000_mean_pct"].mean()), 2),
            "usable_dominant_cci_classes": sorted(
                u["cci2005_dominant"].dropna().astype(int).unique().tolist()),
            "usable_road_tercile_counts": {
                str(int(t)): int(n) for t, n in u["road_tercile"].value_counts()
                .sort_index().items()},
        },
        "note": ("Baseline covariates only (§4.3, 2000–2005): CCI-LC 2005 + "
                 "Hansen 2000 + Copernicus terrain; road distance = CURRENT OSM "
                 "network proxy (dev-D-4 label). The <50% eligible-share arm "
                 "exclusion is an implementation spec detail logged here; no "
                 "outcome data was viewed or exists at this stage."),
        "date": today,
    }
    QAQC.mkdir(parents=True, exist_ok=True)
    (QAQC / "p2_parcel_facts.json").write_text(json.dumps(facts, indent=1) + "\n")

    print(f"\nparcels: {facts['parcels_total']} total, "
          f"{facts['parcels_excluded_both_arms']} excluded (both arms), "
          f"{facts['parcels_usable']} usable")
    print("usable covariate summary:", json.dumps(facts["coverage"], indent=1))
    print(f"csv   : {out_csv.relative_to(ROOT)}")
    print(f"gpkg  : {gpkg.relative_to(ROOT)}")
    print("facts : outputs/qaqc/p2_parcel_facts.json")
    if facts["parcels_usable"] < 500:
        print("FAIL: too few usable parcels — inspect masks")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except P2Error as e:
        print(f"FAIL: {e}")
        sys.exit(1)
