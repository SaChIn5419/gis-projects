"""P2 step (d) — deterministic 1:1 treatment-control matching + balance gate (§4).

Frozen rules implemented (preregistration_wayanad.md §4):

  §4.1 equal-area ~1 km parcels                     → p2_parcel_covariates.py
  §4.2 treatment = parcel with ≥1 VERIFIED facility → p2_facility_universe.py
       control   = no facility within 750 m of parcel boundary   + imagery
                                                        verification (≤100 m rule)
  §4.3 baseline (2000–2005) matching covariates with hard calipers:
       mean slope          ±3°
       mean elevation      ±100 m
       LULC dominant share ±10 pp (share of the TREATED parcel's dominant class)
       Hansen tree cover   ±10 pp
       road-access class   OSM road-distance tercile (exact class match)
  §4.4 exclusions from BOTH arms: WDPA (all_touched), 2024 Chooralmala–Mundakkai
       scar zone, water bodies → parcel eligibility from p2_parcel_covariates.py
  §4.5 1:1 greedy matching, no replacement, standardized Euclidean distance,
       FIXED SEED 20261022; balance table of standardized mean differences
       (SMD) must be |SMD| < 0.10 on every covariate, else matching is
       re-specified BEFORE any outcome is viewed and logged in prereg §7.
  §4.6 the only randomness is the seeded shuffle of treated units.

HARD SAFETY BAR: the script REFUSES to match unless the covariate build was
made WITH the 2024 scar exclusion (facts scar_excluded=true), because §4.4
excludes the scar zone from BOTH arms. A --scar-override flag exists ONLY for
smoke-testing the code path with a scratch file outside data/processed; such
runs print a warning, stamp scar_override=true in the facts, and must be
deleted — never used for analysis. Outcome rasters are neither read nor
referenced anywhere below (information boundary §5).

Outputs (data/processed/):
  matched_pairs_<date>.csv      — treated ↔ control parcel ids + std distance
Outputs (outputs/qaqc/):
  p2_match_balance_<date>.json  — SMD table, gate verdict, seed, calipers
  p2_match_facts_<date>.json    — arm counts, unmatched detail, scar status

Usage:
  python scripts/p2_match.py
  python scripts/p2_match.py --scar-override /tmp/smoke_scar.gpkg   # smoke only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
QAQC = ROOT / "outputs" / "qaqc"

SEED = 20261022                       # prereg §4.5 fixed seed (= H2 MC seed)
CALIPERS = {
    "slope_mean_deg": 3.0,            # ±°   (§4.3)
    "elev_mean_m": 100.0,             # ± m  (§4.3)
    "cci_dom_share": 0.10,            # ±10 pp expressed as fraction (§4.3)
    "hansen2000_mean_pct": 10.0,      # ± pp (§4.3)
}
ROAD_EXACT = True                     # §4.3 road-access class: exact tercile match
SMD_GATE = 0.10                       # §4.5
CONTROL_BUFFER_M = 750.0              # §4.2
TERCILES = (1, 2, 3)

COVS_CONT = ["slope_mean_deg", "elev_mean_m", "cci_dom_share",
             "hansen2000_mean_pct"]


class MatchError(RuntimeError):
    pass


def smd(a, b) -> float:
    """Standardized mean difference (pooled SD)."""
    a = pd.Series(a).dropna().astype(float)
    b = pd.Series(b).dropna().astype(float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    if pooled == 0:
        return 0.0 if a.mean() == b.mean() else float("inf")
    return float((a.mean() - b.mean()) / pooled)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scar-override",
                    help="SMOKE TEST ONLY: scratch scar file (never analysis)")
    args = ap.parse_args()

    # ---- §4.4 scar gate (hard) --------------------------------------------
    scar_path = PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg"
    scar_override = bool(args.scar_override)
    if scar_override:
        scar_path = Path(args.scar_override)
        if not scar_path.exists():
            raise MatchError(f"override scar missing: {scar_path}")
        print(f"!! SMOKE TEST: scratch scar {scar_path} — results are NOT an "
              "analysis run and must be deleted")
    elif not scar_path.exists():
        raise MatchError(
            "2024 Chooralmala–Mundakkai scar layer missing "
            f"({scar_path.relative_to(ROOT)}). §4.4 excludes the scar zone from "
            "BOTH arms — matching is BARRED until D-6 is compiled and "
            "p2_parcel_covariates.py re-run with scar_excluded=true.")

    # ---- covariates + parcels + facility arms ------------------------------
    covs = sorted(PROC.glob("parcel_covariates_*.csv"))
    if not covs:
        raise MatchError("no parcel_covariates_*.csv — run p2_parcel_covariates.py")
    cov_csv = covs[-1]
    facts_p = json.loads((QAQC / "p2_parcel_facts.json").read_text())
    if not facts_p.get("scar_excluded") and not scar_override:
        raise MatchError("covariate run was built WITHOUT the scar exclusion "
                         "(scar_excluded=false): re-run p2_parcel_covariates.py "
                         "after D-6 compilation, then re-run this matcher.")
    if scar_override:
        print("WARN: covariates lack the scar exclusion — smoke test only; "
              "delete all outputs of this run.")

    cov = pd.read_csv(cov_csv).set_index("parcel_id")
    parcels = gpd.read_file(PROC / "parcels_1km_32643.gpkg")
    facs = pd.read_csv(PROC / "facility_existence_universe_2026-10-23.csv")

    fpts = gpd.GeoDataFrame(facs.copy(),
                            geometry=gpd.points_from_xy(facs.lon, facs.lat),
                            crs="EPSG:4326").to_crs(parcels.crs)
    fj = gpd.sjoin(fpts, parcels[["parcel_id", "geometry"]],
                   predicate="within", how="left")

    # §4.2 treatment: ≥1 verified facility inside; eligible parcel (arm exclusion)
    treat_ids = sorted({
        p for p in fj.loc[fj.verified.fillna(False) & fj.parcel_id.notna(),
                          "parcel_id"].unique()
        if p in cov.index and not cov.loc[p, "excluded_both_arms"]})

    # §4.2 control: eligible, not treatment, >750 m from ANY candidate point
    fp_union = unary_union(fj.geometry.tolist())
    elig = parcels[~parcels.excluded_both_arms].copy()
    elig["d_fac_m"] = elig.geometry.boundary.distance(fp_union)
    controls = sorted(p for p in
                      elig.loc[elig.d_fac_m > CONTROL_BUFFER_M, "parcel_id"]
                      if p not in set(treat_ids) and p in cov.index)
    print(f"treatment parcels: {len(treat_ids)} | control pool: {len(controls)} "
          f"| covariates: {cov_csv.name}")

    # ---- §4.3 covariate frame ---------------------------------------------
    d = cov.copy()
    share_cols = {c: c for c in d.columns if c.startswith("cci2005_share_")}
    assert share_cols, "no cci2005_share_* columns in covariate table"
    d["cci_dom_share"] = [
        (d.loc[p, f"cci2005_share_{int(d.loc[p, 'cci2005_dominant'])}"]
         if pd.notna(d.loc[p, "cci2005_dominant"]) else np.nan)
        for p in d.index]

    need = treat_ids + controls
    if d.loc[need, COVS_CONT + ["road_tercile"]].isna().any().any():
        bad = d.loc[need][d.loc[need, COVS_CONT + ["road_tercile"]].isna()
                       ].index.tolist()
        raise MatchError(f"missing covariates for {len(bad)} arm parcels: {bad[:5]}...")

    # standardize on the POOLED arms (pre-match), as §4.5 distance prescribes
    T = d.loc[treat_ids]
    C = d.loc[controls]
    scale = {}
    for v in COVS_CONT:
        s = np.sqrt((T[v].var(ddof=1) + C[v].var(ddof=1)) / 2)
        scale[v] = float(s) if np.isfinite(s) and s > 0 else 1.0

    def feature_matrix(ids: list[str]) -> np.ndarray:
        sub = d.loc[ids]
        M = np.column_stack([
            (sub[v].to_numpy(float) - T[v].mean()) / scale[v]
            for v in COVS_CONT] +
            [(sub["road_tercile"].to_numpy(float) == float(t)).astype(float)
             for t in TERCILES])
        return M

    F_T = {p: feature_matrix([p])[0] for p in treat_ids}
    F_C = feature_matrix(controls)
    c_index = {p: i for i, p in enumerate(controls)}
    road_C = d.loc[controls, "road_tercile"].to_numpy(float)
    road_T = d.loc[treat_ids, "road_tercile"].to_numpy(float)

    # caliper masks (vectorized over controls) --------------------------------
    slope_C = d.loc[controls, "slope_mean_deg"].to_numpy(float)
    elev_C = d.loc[controls, "elev_mean_m"].to_numpy(float)
    share_C = d.loc[controls, "cci_dom_share"].to_numpy(float)
    han_C = d.loc[controls, "hansen2000_mean_pct"].to_numpy(float)

    # ---- §4.5 greedy 1:1, no replacement, seeded shuffle -------------------
    rng = np.random.default_rng(SEED)
    order = list(treat_ids)
    rng.shuffle(order)                       # §4.6: the ONLY randomness

    used = np.zeros(len(controls), bool)
    pairs, unmatched = [], []

    for tp in order:
        r = d.loc[tp]
        ft = F_T[tp]
        cand = np.where(~used & (road_C == float(r["road_tercile"])) &
                        (np.abs(slope_C - r["slope_mean_deg"])
                         <= CALIPERS["slope_mean_deg"]) &
                        (np.abs(elev_C - r["elev_mean_m"])
                         <= CALIPERS["elev_mean_m"]) &
                        (np.abs(share_C - r["cci_dom_share"])
                         <= CALIPERS["cci_dom_share"]) &
                        (np.abs(han_C - r["hansen2000_mean_pct"])
                         <= CALIPERS["hansen2000_mean_pct"]))[0]
        if cand.size == 0:
            unmatched.append([tp, "no_control_passed_calipers"])
            continue
        dists = np.linalg.norm(F_C[cand] - ft, axis=1)
        pick = cand[int(np.argmin(dists))]       # deterministic tie → first index
        used[pick] = True
        pairs.append({"treated": tp, "control": controls[pick],
                      "std_distance": round(float(dists.min()), 6)})

    pairs_df = pd.DataFrame(pairs, columns=["treated", "control", "std_distance"])

    # ---- §4.5 balance table -------------------------------------------------
    smds = {}
    if len(pairs_df):
        for v in COVS_CONT:
            smds[v] = smd(pairs_df["treated"].map(d[v]),
                          pairs_df["control"].map(d[v]))
        for t in (1, 2):
            smds[f"road_tercile_{t}"] = smd(
                pairs_df["treated"].map(lambda p: float(int(d.loc[p, "road_tercile"]) == t)),
                pairs_df["control"].map(lambda p: float(int(d.loc[p, "road_tercile"]) == t)))
    gate = (len(pairs_df) > 0 and len(smds) == len(COVS_CONT) + 2 and
            all(np.isfinite(v) and abs(v) < SMD_GATE for v in smds.values()))

    today = date.today().isoformat()
    out_csv = PROC / f"matched_pairs_{today}.csv"
    pairs_df.to_csv(out_csv, index=False)
    bal = {"date": today, "seed": SEED, "calipers": CALIPERS,
           "road_exact_match": ROAD_EXACT, "smd_gate": SMD_GATE,
           "smd": {k: round(v, 4) for k, v in smds.items()},
           "max_abs_smd": round(max(abs(v) for v in smds.values()), 4) if smds else None,
           "gate_pass": bool(gate), "n_pairs": int(len(pairs_df)),
           "n_treated": len(treat_ids), "n_control_pool": len(controls),
           "scar_override": scar_override,
           "note": ("Pre-outcome matching output (§5 allows matching scripts + "
                    "covariate tables). If gate_pass is false: re-specify "
                    "BEFORE viewing any outcome and log in prereg §7 (§4.5).")}
    (QAQC / f"p2_match_balance_{today}.json").write_text(json.dumps(bal, indent=1) + "\n")
    facts = {"date": today, "scar_override": scar_override,
             "scar_layer": str(scar_path),
             "treatment_parcels": len(treat_ids), "control_pool": len(controls),
             "pairs": int(len(pairs_df)), "unmatched_treated": len(unmatched),
             "unmatched_detail": unmatched}
    (QAQC / f"p2_match_facts_{today}.json").write_text(json.dumps(facts, indent=1) + "\n")

    print(f"\npairs: {len(pairs_df)} / {len(treat_ids)} treated matched")
    print("SMD:", json.dumps(bal["smd"], indent=1))
    print(f"max|SMD| = {bal['max_abs_smd']} → gate {'PASS' if gate else 'FAIL'}")
    print(f"pairs  : {out_csv.relative_to(ROOT)}")
    if unmatched:
        reasons = pd.Series([r for _, r in unmatched]).value_counts().to_dict()
        print("unmatched:", reasons)
    if not gate:
        print("\nGATE FAIL — re-specify matching BEFORE viewing any outcome and "
              "log the change in prereg §7 (§4.5).")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MatchError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
