"""P3 step (b) — H1 land-conversion analysis: treatment vs matched control.

Information boundary (§5): outcome rasters are read here for the FIRST time in a
treatment/control comparison. Permitted because freeze R6 is recorded in
PROJECTSTATE §9 (§8 checklist signed 2026-10-26) and the measurement spec was
pinned in D-14 BEFORE any arm difference was computed.

Implements dev-D-14 exactly (no rule, covariate, caliper or seed is changed):

  Units      : the 50 matched pairs (data/processed/matched_pairs_2026-10-26.csv).
  Treatment  : pixel union of per-radius buffers (500 m primary; 250/1000 m
               sensitivities) around all verified facility points inside the
               treated parcel (overlapping buffers counted once).
  Control    : buffer of the same radius around the centroid of the matched
               control parcel.
  Metric     : on the frozen 30 m grid (P3 outcome grid, congruent with the
               covariate grid — pixel edges coincide), restricted to the
               matching eligibility mask (AOI ∩ ¬WorldCover-water ∩
               ¬WDPA-all_touched ∩ ¬scar-v2) applied identically in every buffer:
                 numerator   = GLAD expansion pixels (class 1) whose CCI-2005
                               class is vegetated/cropland (families 10-12,
                               20-30, 40-50, 60-75, 100-180; i.e. all except
                               urban 190 and water 210)
                 denominator = buffer pixels non-built at 2000 (GLAD classes
                               0/1) with the same CCI restriction
                 rate        = numerator / denominator in %
  Tests      : paired t-test AND Wilcoxon signed-rank on d_i = treatment −
               control, n = 50 pairs; Holm correction across the three radius
               tests within H1 (per test family).
  Robustness : at 500 m, (a) WorldCover-2021 strict built (numerator: WC class
               50 pixels that GLAD flags as non-built at 2000; same
               denominator) and (b) Hansen loss 2001-2024 as clearing proxy
               (numerator: loss pixels; denominator: baseline pixels with
               Hansen 2000 tree cover > 0). H1 is falsified per §3 if the sign
               of the mean paired difference disagrees with the primary run.
  Stratum    : D-4's pre-existing-development stratum is reported EMPTY (all 51
               registry order dates 2023-2026; no imagery-based construction
               dating was run — labelled limitation, D-14(v)).

Implementation notes (measurement details, logged, not rule changes):
  - CCI 2005 ships at 300 m on the covariate grid; it is nearest-upscaled 10x
    to 30 m (exact — same origin, 300 = 10 x 30) so the D-14 CCI family
    restriction applies per 30 m pixel.
  - Rasterisation of every buffer uses the pixel-centre rule (all_touched=False)
    identically on both arms.
  - The D-14(iv)(a) robustness numerator additionally carries the CCI
    vegetated/cropland restriction so that numerator ⊆ denominator by
    construction (the frozen text pins "same denominator"; keeping the same
    land-cover support in both terms is the consistent reading).
  - Buffer geometries are rasterised on the P3 outcome grid; the eligibility
    mask is rebuilt from the covariate-grid layers and cropped to the outcome
    window (grid congruence asserted in code).

Outputs:
  data/processed/h1_pair_rates_<date>.csv        per-pair rates at all radii
  outputs/qaqc/p3_h1_facts_<date>.json           tests, Holm, robustness,
                                                 transition matrices, QA checks

Usage:  python scripts/p3_h1_analysis.py
"""
from __future__ import annotations

import json

from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy import stats
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
QAQC = ROOT / "outputs" / "qaqc"

CRS = "EPSG:32643"
RES = 30.0
RADII = (250.0, 500.0, 1000.0)          # D-14(i): 500 m primary
PRIMARY_R = 500.0
PAIRS_CSV = PROC / "matched_pairs_2026-10-26.csv"

# CCI-2005 families per D-14(ii): vegetated/cropland support of the metric
CCI_FAMILIES = {                      # name: (lo, hi) inclusive code ranges
    "cropland_10_12": (10, 12),
    "mosaic_20_30": (20, 30),
    "shrub_40_50": (40, 50),
    "forest_60_75": (60, 75),
    "grass_sparse_100_180": (100, 180),
    "urban_190": (190, 190),
    "water_210": (210, 210),
}
VEG_CODES = ("cropland_10_12", "mosaic_20_30", "shrub_40_50",
             "forest_60_75", "grass_sparse_100_180")


class H1Error(RuntimeError):
    pass


def load_arr(name: str) -> tuple[np.ndarray, rasterio.Affine, tuple]:
    p = PROC / name
    if not p.exists():
        raise H1Error(f"missing input {name}")
    with rasterio.open(p) as src:
        return src.read(1), src.transform, src.shape


def main() -> int:
    print("P3 H1 analysis — Wayanad (treatment vs matched control, D-14 spec)")

    # ---- outcome-grid layers (P3 grid) --------------------------------------
    glad, gtr, gshape = load_arr("builtup_change_2000_2020_32643.tif")   # 1=exp 2=stable
    wcbuilt, wtr, _ = load_arr("builtup_worldcover2021_32643.tif")       # 1=built
    hloss, ltr, _ = load_arr("treecover_loss_2000_2020_32643.tif")       # 1=loss
    for t in (wtr, ltr):
        assert t == gtr, "outcome rasters are not on one grid"

    # ---- covariate-grid layers, cropped to the outcome window ---------------
    # Grid congruence: both grids are 30 m EPSG:32643 with origins offset by
    # exact pixel multiples — pixel EDGES coincide; only the window differs.
    aoi_m, aotr, _ = load_arr("aoi_mask_32643.tif")
    wc, wctr, _ = load_arr("worldcover_2021_32643.tif")
    wdpa, _, _ = load_arr("wdpa_all_touched_32643.tif")
    htree, _, _ = load_arr("hansen_treecover2000_32643.tif")
    cci300, _, _ = load_arr("cci_lulc_2005_32643.tif")

    col_off = round((gtr.c - aotr.c) / RES)
    row_off = round((aotr.f - gtr.f) / RES)
    assert abs((gtr.c - aotr.c) / RES - col_off) < 1e-6 and \
        abs((aotr.f - gtr.f) / RES - row_off) < 1e-6, "grids not congruent"
    sl = np.s_[row_off:row_off + gshape[0], col_off:col_off + gshape[1]]
    aoi_mc = aoi_m[sl] == 1
    wcc = wc[sl]
    wdpac = wdpa[sl]
    htreec = htree[sl]
    assert aoi_mc.shape == gshape, "crop/shape mismatch"

    # CCI 2005: nearest upscale 300 m -> 30 m (same origin; 10x repeat is exact)
    cci30 = np.repeat(np.repeat(cci300, 10, axis=0), 10, axis=1)[sl]

    # ---- eligibility mask (identical to p2_parcel_covariates) ---------------
    scar_gpkg = PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg"
    if not scar_gpkg.exists():
        raise H1Error("scar v2 layer missing — P2 input of record required")
    scar = gpd.read_file(scar_gpkg)
    if scar.crs is None or str(scar.crs) != CRS:
        scar = scar.to_crs(CRS)
    scar_mask = rasterize(((g, 1) for g in scar.geometry), out_shape=gshape,
                          transform=gtr, fill=0, all_touched=True,
                          dtype="uint8").astype(bool)
    water = wcc == 80                          # WorldCover permanent water
    elig = aoi_mc & ~water & (wdpac != 1) & ~scar_mask

    # ---- CCI family mask (D-14 land-cover support) -------------------------
    veg = np.zeros(gshape, bool)
    fam_rows: dict[str, np.ndarray] = {}
    for fam, (lo, hi) in CCI_FAMILIES.items():
        m = (cci30 >= lo) & (cci30 <= hi)
        fam_rows[fam] = m
        if fam in VEG_CODES:
            veg |= m

    # ---- arms ---------------------------------------------------------------
    pairs = pd.read_csv(PAIRS_CSV)
    if len(pairs) != 50:
        raise H1Error(f"expected 50 matched pairs, found {len(pairs)}")
    parcels = gpd.read_file(PROC / "parcels_1km_32643.gpkg")
    facs = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")
    fpts = gpd.GeoDataFrame(facs.copy(),
                            geometry=gpd.points_from_xy(facs.lon, facs.lat),
                            crs="EPSG:4326").to_crs(parcels.crs)
    fj = gpd.sjoin(fpts, parcels[["parcel_id", "geometry"]],
                   predicate="within", how="left")
    ver = fj[fj.verified.fillna(False) & fj.parcel_id.notna()]

    pid2geom = dict(zip(parcels.parcel_id, parcels.geometry))
    fac_by_parcel: dict[str, list] = (
        ver.groupby("parcel_id").geometry.apply(list).to_dict())

    def rasterise(geom) -> np.ndarray:
        return rasterize([(geom, 1)], out_shape=gshape, transform=gtr,
                         fill=0, all_touched=False, dtype="uint8").astype(bool)

    # Raster bounds polygon: buffer geometries near the district edge extend
    # past the grid; fidelity checks must compare against the CLIPPED area.
    from shapely.geometry import box
    raster_bounds_poly = box(gtr.c, gtr.f - gshape[0] * RES,
                             gtr.c + gshape[1] * RES, gtr.f)

    def metric(geom, radius: float) -> dict:
        """D-14 metric for one buffer geometry."""
        inbuf = rasterise(geom)
        n_buf = int(inbuf.sum())
        # Fidelity expectation = geometry area clipped to the raster grid,
        # in pixels. (Treatment geometry is a UNION of k facility buffers —
        # comparing against a single πr² circle would misflag k>1 parcels.)
        clipped_area_m2 = geom.intersection(raster_bounds_poly).area
        area_expect = clipped_area_m2 / (RES * RES)
        elig_in = inbuf & elig
        base = elig_in & veg & np.isin(glad, (0, 1))     # non-built 2000 + veg
        num = base & (glad == 1)
        den = base
        n_num, n_den = int(num.sum()), int(den.sum())
        rate = 100.0 * n_num / n_den if n_den > 0 else float("nan")
        return {"buf_px": n_buf, "area_expect_px": round(area_expect, 1),
                "elig_px": int(elig_in.sum()), "num_px": n_num,
                "den_px": n_den, "rate_pct": rate}

    def robust_a(geom) -> dict:
        """(a) WorldCover-2021 strict built; same denominator as primary."""
        inbuf = rasterise(geom) & elig
        base = inbuf & veg & np.isin(glad, (0, 1))
        num = base & (wcbuilt == 1)
        n_num, n_den = int(num.sum()), int(base.sum())
        return {"num_px": n_num, "den_px": n_den,
                "rate_pct": 100.0 * n_num / n_den if n_den else float("nan")}

    def robust_b(geom) -> dict:
        """(b) Hansen loss 2001-2024 clearing proxy; its own denominator."""
        inbuf = rasterise(geom) & elig
        den = inbuf & (htreec != 255) & (htreec > 0)
        num = den & (hloss == 1)
        n_num, n_den = int(num.sum()), int(den.sum())
        return {"num_px": n_num, "den_px": n_den,
                "rate_pct": 100.0 * n_num / n_den if n_den else float("nan")}

    # ---- per-pair computation ----------------------------------------------
    recs = []
    overlap_px = 0
    qa = {"den_zero": 0, "num_gt_den": 0, "area_dev_max_pct": 0.0,
          "no_facilities": []}
    trans = {arm: {f: {0: 0, 1: 0, 2: 0} for f in CCI_FAMILIES}
             for arm in ("treatment", "control")}

    for _, row in pairs.iterrows():
        t_pid, c_pid = row.treated, row.control
        c_geom = pid2geom[c_pid]
        c_cent = c_geom.centroid
        pts = fac_by_parcel.get(t_pid, [])
        if not pts:
            qa["no_facilities"].append(t_pid)
            continue
        for r in RADII:
            t_geom = unary_union([p.buffer(r) for p in pts])
            c_buf = c_cent.buffer(r)
            t = metric(t_geom, r)
            c = metric(c_buf, r)
            for m in (t, c):
                dev = abs(m["buf_px"] - m["area_expect_px"]) \
                    / m["area_expect_px"] * 100
                qa["area_dev_max_pct"] = max(qa["area_dev_max_pct"], dev)
            if t["den_px"] == 0 or c["den_px"] == 0:
                qa["den_zero"] += 1
            if t["num_px"] > t["den_px"] or c["num_px"] > c["den_px"]:
                qa["num_gt_den"] += 1
            if r == PRIMARY_R:
                tg, cg = rasterise(t_geom), rasterise(c_buf)
                overlap_px += int((tg & cg).sum())
            recs.append({"pair": f"{t_pid}|{c_pid}", "treated": t_pid,
                         "control": c_pid, "radius_m": r,
                         "treat": t, "control_m": c,
                         "diff_pp": t["rate_pct"] - c["rate_pct"]})
            if r == PRIMARY_R:     # transition matrix (pooled, 500 m)
                for arm, gm in (("treatment", t_geom), ("control", c_buf)):
                    inb = rasterise(gm) & elig
                    for fam, m in fam_rows.items():
                        cnt = np.bincount(glad[inb & m], minlength=3)
                        for cls in (0, 1, 2):
                            trans[arm][fam][cls] += int(cnt[cls])

    df = pd.DataFrame([{
        "pair": r["pair"], "treated": r["treated"], "control": r["control"],
        "radius_m": r["radius_m"],
        "treat_num_px": r["treat"]["num_px"], "treat_den_px": r["treat"]["den_px"],
        "treat_rate_pct": round(r["treat"]["rate_pct"], 4),
        "ctrl_num_px": r["control_m"]["num_px"], "ctrl_den_px": r["control_m"]["den_px"],
        "ctrl_rate_pct": round(r["control_m"]["rate_pct"], 4),
        "diff_pp": round(r["diff_pp"], 4)} for r in recs])

    # ---- tests (D-14(iii)) --------------------------------------------------
    def holm(pvals: dict[float, float]) -> dict[float, float]:
        items = sorted(pvals.items(), key=lambda kv: kv[1])
        m, out, running = len(items), {}, 0.0
        for k, (r_, p_) in enumerate(items):
            running = max(running, (m - k) * p_)
            out[r_] = min(1.0, running)
        return out

    tests: dict[str, dict] = {}
    raw_t, raw_w = {}, {}
    for r_ in RADII:
        sub = df[df.radius_m == r_].dropna(subset=["diff_pp"])
        t_ = sub.treat_rate_pct.to_numpy()
        c_ = sub.ctrl_rate_pct.to_numpy()
        d_ = t_ - c_
        n_used = len(d_)
        if n_used < 2 or np.allclose(d_, 0):
            tt = {"stat": None, "p": 1.0}
            ww = {"stat": None, "p": 1.0}
        else:
            tt_ = stats.ttest_rel(t_, c_)
            ww_ = stats.wilcoxon(d_)
            tt = {"stat": float(tt_.statistic), "p": float(tt_.pvalue)}
            ww = {"stat": float(ww_.statistic), "p": float(ww_.pvalue)}
        raw_t[r_] = tt["p"]
        raw_w[r_] = ww["p"]
        tests[str(int(r_))] = {
            "n_pairs_used": n_used,
            "mean_treat_pct": round(float(np.mean(t_)), 4),
            "mean_ctrl_pct": round(float(np.mean(c_)), 4),
            "mean_diff_pp": round(float(np.mean(d_)), 4),
            "sd_diff_pp": round(float(np.std(d_, ddof=1)), 4) if n_used > 1 else None,
            "paired_t": tt, "wilcoxon": ww}
    holm_t, holm_w = holm(raw_t), holm(raw_w)
    for r_ in RADII:
        k = str(int(r_))
        tests[k]["paired_t"]["p_holm"] = float(f"{holm_t[r_]:.6g}")
        tests[k]["wilcoxon"]["p_holm"] = float(f"{holm_w[r_]:.6g}")
        tests[k]["paired_t"]["p_raw"] = float(f"{raw_t[r_]:.6g}")
        tests[k]["wilcoxon"]["p_raw"] = float(f"{raw_w[r_]:.6g}")

    # ---- robustness (D-14(iv)) at 500 m -------------------------------------
    rob = {"worldcover_strict": [], "hansen_loss": []}
    for _, row in pairs.iterrows():
        pts = fac_by_parcel.get(row.treated, [])
        if not pts:
            continue
        t_geom = unary_union([p.buffer(PRIMARY_R) for p in pts])
        c_buf = pid2geom[row.control].centroid.buffer(PRIMARY_R)
        a_t, a_c = robust_a(t_geom), robust_a(c_buf)
        b_t, b_c = robust_b(t_geom), robust_b(c_buf)
        rob["worldcover_strict"].append(
            {"t": a_t["rate_pct"], "c": a_c["rate_pct"],
             "diff": a_t["rate_pct"] - a_c["rate_pct"]})
        rob["hansen_loss"].append(
            {"t": b_t["rate_pct"], "c": b_c["rate_pct"],
             "diff": b_t["rate_pct"] - b_c["rate_pct"]})

    def rob_summary(items: list) -> dict:
        d = np.array([x["diff"] for x in items], float)
        d = d[~np.isnan(d)]
        return {"n_pairs": int(len(d)), "mean_diff_pp": round(float(d.mean()), 4),
                "sign_matches_primary": bool(
                    np.sign(d.mean()) == np.sign(
                        tests[str(int(PRIMARY_R))]["mean_diff_pp"]))}

    primary_mean = tests[str(int(PRIMARY_R))]["mean_diff_pp"]
    robustness = {
        "worldcover_strict": rob_summary(rob["worldcover_strict"]),
        "hansen_loss": rob_summary(rob["hansen_loss"])}

    falsified = (primary_mean <= 0) or (not all(
        v["sign_matches_primary"] for v in robustness.values()))

    # ---- facts --------------------------------------------------------------
    facts = {
        "date": date.today().isoformat(),
        "freeze": "R6",
        "spec": "dev-D-14 (measurement spec pinned before this comparison)",
        "pairs_total": int(len(pairs)),
        "radii_m": [int(r_) for r_ in RADII],
        "primary_radius_m": int(PRIMARY_R),
        "grid": {"crs": CRS, "res_m": RES,
                 "origin": [gtr.c, gtr.f], "shape": list(gshape),
                 "cci_upscaled_300m_to_30m_nearest": True},
        "eligibility_mask": "AOI ∩ ¬WorldCover-water(80) ∩ ¬WDPA-all_touched "
                            "∩ ¬scar-v2 (identical to matching mask)",
        "tests": tests,
        "robustness_500m": robustness,
        "h1_falsified_by_frozen_rule": bool(falsified),
        "primary_mean_diff_pp": primary_mean,
        "stratum_preexisting_development": {
            "count": 0,
            "note": "All 51 registry order dates 2023-2026 → zero facilities "
                    "pre-date the 2000-2005 baseline by the registry-date "
                    "proxy; imagery-based construction dating not run "
                    "(D-14(v), labelled limitation)."},
        "transition_matrix_500m_pooled": {
            arm: {fam: {str(c): n for c, n in cls.items()}
                  for fam, cls in d.items()}
            for arm, d in trans.items()},
        "qa": {
            "buffer_area_deviation_max_pct": round(qa["area_dev_max_pct"], 2),
            "geometries_with_zero_denominator": qa["den_zero"],
            "numerator_gt_denominator_violations": qa["num_gt_den"],
            "treatment_control_geometry_overlap_px_500m": overlap_px,
            "pairs_missing_facilities": qa["no_facilities"],
            "note": "Pixel-centre rasterisation (all_touched=False) on both "
                    "arms; area deviation = |rasterised px − geometry area "
                    "clipped to grid / 900| / expected. Treatment geometry is "
                    "the union of k facility buffers, so the check uses the "
                    "true union area, not a single circle."}}

    out_csv = PROC / f"h1_pair_rates_{facts['date']}.csv"
    out_json = QAQC / f"p3_h1_facts_{facts['date']}.json"
    df.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(facts, indent=1, ensure_ascii=False))

    # ---- console summary ----------------------------------------------------
    print(f"pairs: {facts['pairs_total']}  grid: {gshape} @ {gtr.c},{gtr.f}")
    for r_ in RADII:
        t = tests[str(int(r_))]
        print(f"  r={int(r_):>5} m  treat={t['mean_treat_pct']:.3f}%  "
              f"ctrl={t['mean_ctrl_pct']:.3f}%  d={t['mean_diff_pp']:+.3f} pp  "
              f"t-p(Holm)={t['paired_t']['p_holm']:.4g}  "
              f"wilc-p(Holm)={t['wilcoxon']['p_holm']:.4g}")
    for k, v in robustness.items():
        print(f"  robustness {k}: d={v['mean_diff_pp']:+.4f} pp  "
              f"sign_agrees={v['sign_matches_primary']}")
    print(f"  H1 falsified by frozen rule: {falsified}")
    print(f"QA: area_dev_max={qa['area_dev_max_pct']:.2f}%  den0={qa['den_zero']}  "
          f"num>den={qa['num_gt_den']}  overlap_px={overlap_px}")
    print(f"wrote {out_csv.relative_to(ROOT)}")
    print(f"wrote {out_json.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
