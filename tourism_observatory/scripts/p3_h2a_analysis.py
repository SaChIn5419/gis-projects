#!/usr/bin/env python3
"""P3 H2a — facility siting preference vs susceptibility (prereg §3 D-2, pins in §7 D-15).

Statistics (registered, Holm within {i, ii}):
  (i)   share placed on slope >= 25 deg
  (ii)  mean inventory density in a 500 m KDE surface  [input substituted per D-15:
        polygons polygonized from Bhuvan WMS renders of disaster:kl_landslides_new]

Per facility: mid-rank percentile of the observed metric against its own 1,000
matched null draws; family summary = mean percentile + exact two-sided binomial
sign test (ties excluded); Holm across the two sign-test p-values.
**D-16 correction:** those sign tests are analytically invalid for
point-massed metrics (their null is not 50/50); family inference therefore also
carries the registered corrected Monte Carlo exceedance tests — T_obs at the
observed facilities vs T_j at the j-th null draws, p=(1+#{T_j>=T_obs})/1001,
Holm across {i,ii} — in facts key `corrected_tests_D16`. Registered outputs
are retained verbatim.

Eligible placement domain (D-2, hazard-free): 1 km parcel-grid cell centres
inside AOI, outside WDPA (all_touched), outside water (WorldCover 80/90 or
CCI-2005 210), non-built at baseline (CCI-2005 != 190), within 2 km of an OSM
road class >= tertiary, elevation within the [5th,95th] percentile band of the
observed facility elevations. Null calipers: elevation +/-150 m and
road-distance +/-40% (nearest >=tertiary road) — rejection sampling, one
default_rng(20261022) stream over facilities sorted by facility_id.

Outputs:
  data/processed/h2a_facility_percentiles_<date>.csv
  outputs/qaqc/p3_h2a_facts_<date>.json
  outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif   (QA gate opens the actual GTiff)
"""
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
from scipy.ndimage import gaussian_filter
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"
OUT = ROOT / "outputs/qaqc"
TODAY = date.today().isoformat()
RES = 30.0
SEED = 20261022
N_NULL = 1000
SLOPE_THR = 25.0
KDE_SIGMA_M = 500.0
ELEV_CAL_M = 150.0
ROAD_CAL_FRAC = 0.40
ROAD_MAX_M = 2000.0
TERTIARY = {"motorway", "trunk", "primary", "secondary", "tertiary",
            "motorway_link", "trunk_link", "primary_link", "secondary_link",
            "tertiary_link"}
WC_WATER = {80, 90}
CCI_WATER = {210}
CCI_URBAN = 190


class H2Error(RuntimeError):
    pass


def load(name):
    with rasterio.open(PROC / name) as src:
        arr = src.read(1)
        return arr, src.transform, src.shape, src.nodata


def sample(arr, tr, nodata, pts_xy, idx=("col", "row")):
    """Nearest-cell sample of arr at (x, y) in arr CRS."""
    inv = ~tr
    cols, rows = inv * (pts_xy[:, 0], pts_xy[:, 1])
    cols = np.clip(np.round(cols - 0.5).astype(int), 0, arr.shape[1] - 1)
    rows = np.clip(np.round(rows - 0.5).astype(int), 0, arr.shape[0] - 1)
    vals = arr[rows, cols]
    if nodata is not None and not np.isnan(nodata):
        vals = np.where(vals == nodata, np.nan, vals)
    return vals.astype(float)


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    out, running = {}, 0.0
    m = len(items)
    for rank, (k, p) in enumerate(items):
        adj = min(1.0, (m - rank) * p)
        running = max(running, adj)
        out[k] = running
    return out


def midrank_percentile(obs: float, nulls: np.ndarray) -> float:
    return float((np.sum(nulls < obs) + 0.5 * np.sum(nulls == obs)) / len(nulls))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- frozen grid + congruent inputs (QA: open the actual GTiffs) -------
    aoi, aotr, gshape, _ = load("aoi_mask_32643.tif")
    slope, str_, sshape, snod = load("slope_deg_32643.tif")
    dem, dtr, dshape, dnod = load("dem_copernicus30m_32643.tif")
    wc, wtr, wshape, wnod = load("worldcover_2021_32643.tif")
    wdpa, ptr, pshape, pnod = load("wdpa_all_touched_32643.tif")
    for nm, (tr, shp) in {"slope": (str_, sshape), "dem": (dtr, dshape),
                          "worldcover": (wtr, wshape), "wdpa": (ptr, pshape)}.items():
        if tr != aotr or shp != gshape:
            raise H2Error(f"{nm} not on the frozen AOI grid")
    slope = slope.astype(np.float32)
    dem = dem.astype(np.float32)
    slope_valid = np.isfinite(slope) & (slope >= 0) & (slope <= 90)
    dem_valid = np.isfinite(dem) & (dem > -1000)
    qa_range = {
        "slope_deg_minmax": [float(slope[slope_valid].min()), float(slope[slope_valid].max())],
        "dem_m_minmax": [float(dem[dem_valid].min()), float(dem[dem_valid].max())],
        "aoi_cells": int((aoi == 1).sum()),
    }

    # CCI-2005 (300 m grid) sampled by coordinates
    cci, ctr, _, ccinod = load("cci_lulc_2005_32643.tif")

    # ---- >=tertiary road distance on the frozen grid ----------------------
    roads = gpd.read_file(PROC / "roads_wayanad_32643.gpkg")
    tert = roads[roads["highway"].isin(TERTIARY)]
    if len(tert) == 0:
        raise H2Error("no >=tertiary roads")
    tert_mask = rasterize(((g, 1) for g in tert.geometry), out_shape=gshape,
                          transform=aotr, all_touched=True, dtype="uint8").astype(bool)
    from scipy.ndimage import distance_transform_edt
    road_t_dist = distance_transform_edt(~tert_mask) * RES  # metres
    qa_range["tertiary_road_features"] = int(len(tert))
    qa_range["tertiary_road_cells"] = int(tert_mask.sum())

    # ---- inventory KDE surface (D-15 recipe) ------------------------------
    inv = gpd.read_file(PROC / "inventory_wms_kl_landslides_new_32643.gpkg").to_crs("EPSG:32643")
    # fractional coverage: rasterize at 10 m (3x subgrid of the 30 m grid)
    sub = RES / 3.0
    inv_sub = rasterize(((g, 1) for g in inv.geometry),
                        out_shape=(gshape[0] * 3, gshape[1] * 3),
                        transform=aotr * rasterio.Affine.scale(1 / 3.0, 1 / 3.0),
                        all_touched=False, dtype="uint8").astype(np.float32)
    frac = inv_sub.reshape(gshape[0], 3, gshape[1], 3).mean(axis=(1, 3))
    sigma_cells = KDE_SIGMA_M / RES
    kde = gaussian_filter(frac, sigma=sigma_cells, truncate=3.0, mode="constant",
                          cval=0.0)
    kde_path = OUT / f"p3_h2a_kde_inventory_500m_32643.tif"
    with rasterio.open(kde_path, "w", driver="GTiff", height=gshape[0],
                       width=gshape[1], count=1, dtype="float32", crs="EPSG:32643",
                       transform=aotr, nodata=float("nan"), compress="deflate") as dst:
        dst.write(kde.astype(np.float32), 1)
    # QA gate: reopen the actual GTiff, do not trust the in-memory array
    with rasterio.open(kde_path) as chk:
        kde_disk = chk.read(1)
    if kde_disk.shape != gshape or not np.isfinite(kde_disk).any():
        raise H2Error("KDE GTiff QA failed")
    qa_range["kde_nonzero_cells"] = int((kde_disk > 0).sum())
    qa_range["kde_max"] = float(np.nanmax(kde_disk))

    # ---- observed facilities ---------------------------------------------
    fac = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")
    fac = fac[fac.verified.fillna(False) & fac.inside_district.fillna(False)].copy()
    fpts = gpd.GeoDataFrame(fac, geometry=gpd.points_from_xy(fac.lon, fac.lat),
                            crs="EPSG:4326").to_crs("EPSG:32643")
    parcels = gpd.read_file(PROC / "parcels_1km_32643.gpkg")
    fj = gpd.sjoin(fpts, parcels[["parcel_id", "geometry"]], predicate="within",
                   how="left")
    fj = fj[fj.parcel_id.notna()].sort_values("facility_id").reset_index(drop=True)
    fxy = np.column_stack([fj.geometry.x.values, fj.geometry.y.values])
    elev_fac = sample(dem, dtr, dnod, fxy)
    col_f = np.round((fxy[:, 0] - aotr.c) / RES - 0.5).astype(int)
    row_f = np.round((aotr.f - fxy[:, 1]) / RES - 0.5).astype(int)
    in_grid_f = (row_f >= 0) & (row_f < gshape[0]) & (col_f >= 0) & (col_f < gshape[1])
    road_fac = np.where(in_grid_f,
                        road_t_dist[np.clip(row_f, 0, gshape[0] - 1),
                                    np.clip(col_f, 0, gshape[1] - 1)],
                        np.nan)
    slope_fac = sample(slope, str_, snod, fxy)
    valid_f = np.isfinite(elev_fac) & np.isfinite(slope_fac) & np.isfinite(road_fac)
    if not valid_f.all():
        fj = fj[valid_f].reset_index(drop=True)
        fxy, elev_fac, road_fac, slope_fac = fxy[valid_f], elev_fac[valid_f], \
            road_fac[valid_f], slope_fac[valid_f]
        col_f, row_f = col_f[valid_f], row_f[valid_f]
    n_fac = len(fj)
    if n_fac == 0:
        raise H2Error("no usable facility points")
    elev_lo, elev_hi = np.percentile(elev_fac, [5, 95])

    # ---- eligible domain: 1 km parcel-grid cell centres -------------------
    cen = parcels.copy()
    cen["geometry"] = cen.geometry.centroid
    cxy = np.column_stack([cen.geometry.x.values, cen.geometry.y.values])
    in_aoi = np.array([aoi[int(round((aotr.f - y) / RES - 0.5)),
                           int(round((x - aotr.c) / RES - 0.5))] == 1
                       for x, y in cxy])
    c_dem = sample(dem, dtr, dnod, cxy)
    c_slope = sample(slope, str_, snod, cxy)
    # NB: wdpa_all_touched declares nodata=0, but 0 semantically means
    # "outside WDPA" (values are {0,1}; H1 used `wdpac != 1`) -> sample raw.
    c_wdpa = sample(wdpa, ptr, None, cxy)
    c_wc = sample(wc, wtr, wnod, cxy)
    c_cci = sample(cci, ctr, ccinod, cxy)
    c_road = np.array([road_t_dist[int(round((aotr.f - y) / RES - 0.5)),
                                   int(round((x - aotr.c) / RES - 0.5))]
                       for x, y in cxy])
    col0 = np.round((cxy[:, 0] - aotr.c) / RES - 0.5).astype(int)
    row0 = np.round((aotr.f - cxy[:, 1]) / RES - 0.5).astype(int)
    in_grid = (row0 >= 0) & (row0 < gshape[0]) & (col0 >= 0) & (col0 < gshape[1])
    c_kde = np.where(in_grid, kde_disk[np.clip(row0, 0, gshape[0] - 1),
                                       np.clip(col0, 0, gshape[1] - 1)], np.nan)

    crit = {
        "grid_points_total": int(len(cen)),
        "c0_in_aoi": in_aoi.astype(int),
        "c1_outside_wdpa": (np.nan_to_num(c_wdpa, nan=1) == 0).astype(int),
        "c2_not_water": (~np.isin(np.nan_to_num(c_wc, nan=-1), list(WC_WATER)) &
                         ~np.isin(np.nan_to_num(c_cci, nan=-1), list(CCI_WATER)) &
                         (c_cci != 0)).astype(int),
        "c3_non_built_2005": (np.nan_to_num(c_cci, nan=0) != CCI_URBAN).astype(int),
        "c4_near_tertiary": (np.nan_to_num(c_road, nan=1e9) <= ROAD_MAX_M).astype(int),
        "c5_elev_band": ((c_dem >= elev_lo) & (c_dem <= elev_hi)).astype(int),
        "c6_valid_dem_slope_road": (np.isfinite(c_dem) & np.isfinite(c_slope) &
                                    np.isfinite(c_road)).astype(int),
    }
    domain_mask = np.ones(len(cen), bool)
    attrition = {"grid_points_total": int(len(cen))}
    for k, v in crit.items():
        if k == "grid_points_total":
            continue
        domain_mask &= v.astype(bool)
        attrition[k] = int(domain_mask.sum())
    d_idx = np.nonzero(domain_mask)[0]
    d_slope = c_slope[d_idx]
    d_elev = c_dem[d_idx]
    d_road = c_road[d_idx]
    d_kde = c_kde[d_idx]
    if len(d_idx) < 100:
        raise H2Error(f"eligible domain too small: {len(d_idx)}")

    # ---- null draws: pinned rejection sampler ----------------------------
    rng = np.random.default_rng(SEED)
    rows, pool_sizes = [], []
    # per-draw null metrics retained for the D-16 corrected Monte Carlo
    null_i_rows, null_ii_rows = [], []
    # KDE at facility points (nearest cell, NaN outside grid)
    kfac = np.where(in_grid_f,
                    kde_disk[np.clip(row_f, 0, gshape[0] - 1),
                             np.clip(col_f, 0, gshape[1] - 1)],
                    np.nan)
    ok_fac = np.isfinite(kfac)
    if not ok_fac.all():
        fj = fj[ok_fac].reset_index(drop=True)
        fxy, elev_fac, road_fac, slope_fac = fxy[ok_fac], elev_fac[ok_fac], \
            road_fac[ok_fac], slope_fac[ok_fac]
        kfac = kfac[ok_fac]
        n_fac = len(fj)
        if n_fac == 0:
            raise H2Error("no facility with a finite KDE value")

    for i in range(n_fac):
        e_f, r_f = float(elev_fac[i]), float(road_fac[i])
        e_lo_f, e_hi_f = e_f - ELEV_CAL_M, e_f + ELEV_CAL_M
        r_lo_f, r_hi_f = (1 - ROAD_CAL_FRAC) * r_f, (1 + ROAD_CAL_FRAC) * r_f
        # eligible pool for this facility (calipers define acceptance)
        ok = ((d_elev >= e_lo_f) & (d_elev <= e_hi_f) &
              (d_road >= r_lo_f) & (d_road <= r_hi_f) &
              np.isfinite(d_kde))
        pool = np.nonzero(ok)[0]
        pool_sizes.append(int(len(pool)))
        if len(pool) == 0:
            rows.append({"facility_id": fj.facility_id.iloc[i],
                         "evaluable": False, "reason": "empty caliper pool"})
            continue
        # literal rejection sampling from the DOMAIN (uniform over all
        # eligible points), accepting only caliper-passing draws
        picks = []
        while len(picks) < N_NULL:
            cand = rng.integers(0, len(d_idx), size=4096)
            acc = cand[(d_elev[cand] >= e_lo_f) & (d_elev[cand] <= e_hi_f) &
                       (d_road[cand] >= r_lo_f) & (d_road[cand] <= r_hi_f) &
                       np.isfinite(d_kde[cand])]
            picks.extend(acc[:N_NULL - len(picks)].tolist())
        picks = np.asarray(picks[:N_NULL])

        obs_i = int(slope_fac[i] >= SLOPE_THR)
        null_i = (d_slope[picks] >= SLOPE_THR).astype(int)
        p_i = midrank_percentile(obs_i, null_i)
        obs_ii = float(kfac[i])
        null_ii = d_kde[picks]
        p_ii = midrank_percentile(obs_ii, null_ii)
        null_i_rows.append(null_i)
        null_ii_rows.append(null_ii)
        rows.append({
            "facility_id": fj.facility_id.iloc[i],
            "lon": float(fj.lon.iloc[i]), "lat": float(fj.lat.iloc[i]),
            "elev_m": round(e_f, 1), "road_dist_tert_m": round(r_f, 1),
            "slope_deg": round(float(slope_fac[i]), 2),
            "obs_slope_ge25": obs_i,
            "null_share_slope_ge25": round(float(null_i.mean()), 4),
            "pct_i": round(p_i, 4),
            "obs_kde_density": obs_ii,
            "null_mean_kde_density": round(float(null_ii.mean()), 10),
            "pct_ii": round(p_ii, 4),
            "evaluable": True,
            "caliper_pool_size": int(len(pool)),
        })

    res = pd.DataFrame(rows)
    ev = res[res.evaluable.fillna(False)].copy()
    if len(ev) < 30:
        raise H2Error(f"too few evaluable facilities: {len(ev)}")
    ev["sign_i"] = np.sign(ev.pct_i - 0.5)
    ev["sign_ii"] = np.sign(ev.pct_ii - 0.5)

    tests = {}
    for key, col in (("i", "sign_i"), ("ii", "sign_ii")):
        s = ev[col]
        pos, neg, tie = int((s > 0).sum()), int((s < 0).sum()), int((s == 0).sum())
        n_eff = pos + neg
        p = float(binomtest(pos, n_eff, 0.5, alternative="two-sided").pvalue) \
            if n_eff else float("nan")
        tests[key] = {
            "mean_percentile": round(float(ev[f"pct_{key}"].mean()), 4),
            "sign_pos": pos, "sign_neg": neg, "ties_excluded": tie,
            "n_effective": n_eff,
            "p_sign_raw": float(f"{p:.6g}"),
        }
    h = holm({k: v["p_sign_raw"] for k, v in tests.items()})
    for k in tests:
        tests[k]["p_holm"] = float(f"{h[k]:.6g}")

    # ---- D-16 corrected family inference (registered before computation) --
    # Monte Carlo observed-vs-null exceedance, the s3-H2 frozen test form:
    # T_obs at the observed facilities vs T_j at the j-th null draw of every
    # facility (same deterministic seeded draws); p=(1+#{T_j>=T_obs})/1001.
    null_i_mat = np.vstack(null_i_rows)      # n_eval x 1000, draw index = column
    null_ii_mat = np.vstack(null_ii_rows)
    if null_i_mat.shape != (len(ev), N_NULL):
        raise H2Error("null-draw matrix misaligned with evaluable facilities")
    t_obs_i = int(ev.obs_slope_ge25.sum())
    t_j_i = null_i_mat.sum(axis=0).astype(int)
    p_corr_i = (1 + int(np.sum(t_j_i >= t_obs_i))) / (N_NULL + 1)
    t_obs_ii = float(ev.obs_kde_density.mean())
    t_j_ii = null_ii_mat.mean(axis=0)
    p_corr_ii = (1 + int(np.sum(t_j_ii >= t_obs_ii))) / (N_NULL + 1)
    hc = holm({"i": p_corr_i, "ii": p_corr_ii})
    corrected = {
        "registration": "prereg s7 D-16 (registered before this computation)",
        "test_form": "Monte Carlo observed-vs-null exceedance (s3 H2 frozen "
                     "form): p=(1+#{T_j>=T_obs})/1001, Holm across {i,ii}",
        "i": {
            "statistic": "count of facilities with slope >= 25 deg",
            "T_obs": t_obs_i,
            "T_j_mean": round(float(t_j_i.mean()), 4),
            "T_j_max": int(t_j_i.max()),
            "p_raw": float(f"{p_corr_i:.6g}"),
            "p_holm": float(f"{hc['i']:.6g}"),
        },
        "ii": {
            "statistic": "mean observed KDE inventory density across facilities",
            "T_obs": t_obs_ii,
            "T_j_mean": float(f"{t_j_ii.mean():.6g}"),
            "T_j_p95": float(f"{np.quantile(t_j_ii, 0.95):.6g}"),
            "p_raw": float(f"{p_corr_ii:.6g}"),
            "p_holm": float(f"{hc['ii']:.6g}"),
        },
        "registered_sign_tests_status": "non-interpretable for point-massed "
            "metrics (defect proof in prereg s7 D-16); retained verbatim in "
            "'tests' for the record",
    }

    # descriptive shares (registered metric (i))
    share_obs = float(ev.obs_slope_ge25.mean())
    share_null = float(ev.null_share_slope_ge25.mean())

    facts = {
        "date": TODAY,
        "hypothesis": "H2a — facility siting preference vs susceptibility (prereg s3 D-2)",
        "deviations": "s7 D-15 (inventory input substitution + pinned "
                      "clarifications); s7 D-16 (sign-test defect -> corrected "
                      "Monte Carlo exceedance tests)",
        "seed": SEED, "n_null_per_facility": N_NULL,
        "facilities_verified_inside": int(len(fac)),
        "facilities_evaluable": int(len(ev)),
        "elev_band_p5_p95_m": [round(float(elev_lo), 1), round(float(elev_hi), 1)],
        "domain_attrition": attrition,
        "eligible_domain_points": int(len(d_idx)),
        "caliper_pool_size_min_median": [int(np.min(pool_sizes)),
                                         int(np.median(pool_sizes))],
        "qa_ranges": qa_range,
        "metric_i_slope_ge25_share": {"observed": round(share_obs, 4),
                                      "null_expected": round(share_null, 4)},
        "tests": tests,
        "corrected_tests_D16": corrected,
        "kde_surface_gtiff": str(kde_path.relative_to(ROOT.parent)),
        "inputs": {
            "inventory_gpkg": "data/processed/inventory_wms_kl_landslides_new_32643.gpkg",
            "roads": "data/processed/roads_wayanad_32643.gpkg (>=tertiary classes)",
            "facilities": "data/processed/facility_existence_universe_2026-10-23.csv",
        },
    }

    res.to_csv(PROC / f"h2a_facility_percentiles_{TODAY}.csv", index=False)
    facts_path = OUT / f"p3_h2a_facts_{TODAY}.json"
    facts_path.write_text(json.dumps(facts, indent=1))

    print(f"domain: {attrition['grid_points_total']} grid pts -> "
          f"{len(d_idx)} eligible; facilities {n_fac} -> evaluable {len(ev)}")
    print(f"elev band [{elev_lo:.0f}, {elev_hi:.0f}] m; "
          f"pool min/median {facts['caliper_pool_size_min_median']}")
    print(f"(i) slope>=25 share obs {share_obs:.3f} vs null {share_null:.3f} | "
          f"mean pct {tests['i']['mean_percentile']:.3f} "
          f"signs +{tests['i']['sign_pos']}/-{tests['i']['sign_neg']} "
          f"p_holm={tests['i']['p_holm']:.4g}")
    print(f"(ii) KDE mean pct {tests['ii']['mean_percentile']:.3f} "
          f"signs +{tests['ii']['sign_pos']}/-{tests['ii']['sign_neg']} "
          f"p_holm={tests['ii']['p_holm']:.4g}")
    print(f"[D-16 corrected MC] (i) T_obs={corrected['i']['T_obs']} "
          f"p_holm={corrected['i']['p_holm']:.4g} | "
          f"(ii) T_obs={corrected['ii']['T_obs']:.6g} "
          f"p_holm={corrected['ii']['p_holm']:.4g}")
    print(f"facts -> {facts_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except H2Error as exc:
        print(f"H2Error: {exc}", file=sys.stderr)
        sys.exit(1)
