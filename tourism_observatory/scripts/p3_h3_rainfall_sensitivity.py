#!/usr/bin/env python3
"""P3 D-20 — post-hoc rainfall sensitivity (Wayanad H3 appendix read).

Implements prereg SS7 D-20 (freeze R8) EXACTLY as pinned, with the binding
precommitment: H-3's registered conclusion (descriptive direction-check,
no falsification verdict) is unchanged regardless of outcome; every output
is labelled POST-HOC SENSITIVITY; no p-values, CIs or significance
language anywhere.

  Read 1 (no new data): month-of-incident histogram of the 2,704 kept
       2011-2014 records via the exact screen() code path of record;
       Jun-Sep (SW monsoon) + Oct-Dec (NE monsoon) shares; all + elephant.
  Read 2 (CHIRPS v2.0 0.05-deg monthly 2011-2014, record-window covariates
       rain_annual_total_mm_2011_2014 / rain_monsoon_jun_sep_share, bilinear
       to the origin-aligned 500 m grid by p3_fetch_chirps.py): joined with
       the SAME D-18 overlap reader (percentile at incident-KDE top-decile
       cells + Spearman rho) on the same three arms as the run of record.

Grid/geocode/KDE reproduce the run of record deterministically (module
imports of p3_h3_analysis; geocode cache complete -> no network).

Outputs:
  outputs/qaqc/p3_h3_rainfall_sensitivity_{date}.json   (POST-HOC label)

Usage:  python scripts/p3_h3_rainfall_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "outputs/qaqc"
TODAY = date.today().isoformat()
sys.path.insert(0, str(ROOT / "scripts"))
import p3_h3_analysis as h3  # noqa: E402  (module of record: screen/geocode/assign/CellIndex/aggregate)

PROC, RAW = h3.PROC, h3.RAW
RAIN_ANNUAL = PROC / "chirps_rain_annual_2011_2014_32643.tif"
RAIN_MONSOON = PROC / "chirps_rain_monsoon_share_2011_2014_32643.tif"
FACTS = QA / f"p3_h3_rainfall_sensitivity_{TODAY}.json"

NODATA = np.float32(-9999.0)


def main() -> int:
    adm = gpd.read_file(h3.DISTRICT)
    adm = adm[adm.shapeName.str.contains("Wayanad", case=False, na=False)]
    district = unary_union(adm.to_crs("EPSG:32643").geometry)

    # ---- reproduce the run of record, deterministically ------------------
    rec, sfacts = h3.screen()
    assert sfacts["kept_rows"] == 2704, f"screen mismatch: {sfacts['kept_rows']}"
    assert sfacts["elephant_rows"] == 2018, f"elephant mismatch: {sfacts['elephant_rows']}"
    geo = h3.geocode(rec)
    assert len(geo) == 425, f"cache size mismatch: {len(geo)}"
    pts = h3.assign_points(rec, geo)
    placed = pts[pts.tier != "none"].copy()
    assert len(placed) == 2704 and (pts.tier == "none").sum() == 0
    tiers = placed.tier.value_counts().to_dict()
    assert tiers == {"place": 1089, "range": 1043, "section": 572}, tiers
    print("run-of-record reproduction: 2704 records placed, tiers OK",
          flush=True)

    ci = h3.CellIndex(district)
    n = ci.n
    cx = ci.centres.x.to_numpy()
    cy = ci.centres.y.to_numpy()
    wdpa = h3.aggregate(PROC / "wdpa_all_touched_32643.tif", ci, n, "max")
    outside_wdpa = ~(np.nan_to_num(wdpa, nan=0) == 1)
    assert n == 8112 and outside_wdpa.sum() == 4423, (n, outside_wdpa.sum())
    print(f"grid: {n} cells ({int(outside_wdpa.sum())} outside WDPA) OK",
          flush=True)

    def kde_surface(mask):
        # identical to p3_h3_analysis.main (sigma=1000 m, weighted, ranked)
        sub = placed[mask]
        agg = sub.groupby(["lat", "lon"]).size().reset_index(name="w")
        px = gpd.GeoSeries(gpd.points_from_xy(agg.lon, agg.lat), crs="EPSG:4326"
                           ).to_crs("EPSG:32643")
        d2 = ((cx[:, None] - px.x.to_numpy()[None, :]) ** 2 +
              (cy[:, None] - px.y.to_numpy()[None, :]) ** 2)
        k = (agg.w.to_numpy()[None, :] * np.exp(-d2 / (2 * h3.SIGMA_M ** 2))).sum(1)
        return pd.Series(k).rank(pct=True).to_numpy(), len(sub)

    kde_all, n_all = kde_surface(np.ones(len(placed), dtype=bool))
    kde_elp, n_elp = kde_surface(placed.elephant.to_numpy())

    # ---- Read 1: seasonality (record dates only; no new data) ------------
    months_all = rec["date"].dt.month.value_counts().reindex(
        range(1, 13), fill_value=0).astype(int)
    months_elp = rec.loc[rec.elephant, "date"].dt.month.value_counts() \
        .reindex(range(1, 13), fill_value=0).astype(int)

    def share(months, a, b):
        return round(float(months.loc[list(range(a, b + 1))].sum() / months.sum()), 4)

    read1 = {
        "label": "POST-HOC SENSITIVITY (D-20a; non-inferential)",
        "month_histogram_all": months_all.to_dict(),
        "month_histogram_elephant": months_elp.to_dict(),
        "sw_monsoon_jun_sep_share_all": share(months_all, 6, 9),
        "ne_monsoon_oct_dec_share_all": share(months_all, 10, 12),
        "sw_monsoon_jun_sep_share_elephant": share(months_elp, 6, 9),
        "ne_monsoon_oct_dec_share_elephant": share(months_elp, 10, 12),
        "reading": "descriptive only, no test; carries the V2 seasonality "
                   "check D-18 recorded as unavailable",
    }
    print("Read 1 (seasonality): Jun-Sep share all = "
          f"{read1['sw_monsoon_jun_sep_share_all']}, "
          f"elephant = {read1['sw_monsoon_jun_sep_share_elephant']}",
          flush=True)

    # ---- Read 2: spatial rainfall covariates via the D-18 reader ---------
    rain = h3.aggregate(RAIN_ANNUAL, ci, n, "mean")
    mshare = h3.aggregate(RAIN_MONSOON, ci, n, "mean")
    surfaces = {
        "rain_annual_total_mm_2011_2014": rain,
        "rain_monsoon_jun_sep_share": mshare,
    }

    def overlap(kde, mask):
        # formulas copied VERBATIM from p3_h3_analysis.main
        out = {}
        k = kde[mask]
        top = k >= np.nanquantile(k, 0.9)
        for name, arr in surfaces.items():
            v = arr[mask]
            ok = ~np.isnan(v) & (v != NODATA)
            pct = pd.Series(v[ok]).rank(pct=True).to_numpy()
            kk = pd.Series(k[ok]).rank(pct=True).to_numpy()
            rho = float(np.corrcoef(pct, kk)[0, 1])
            vv = pct[top[ok]]
            out[name] = {
                "mean_pct_at_top_decile": round(float(np.mean(vv)), 4),
                "median_pct_at_top_decile": round(float(np.median(vv)), 4),
                "share_above_district_median": round(float((vv > 0.5).mean()), 4),
                "spearman_rho_vs_incident_kde": round(rho, 4),
                "n_cells_finite": int(ok.sum()),
            }
        return out

    read2 = {
        "label": "POST-HOC SENSITIVITY (D-20b; record-window covariates; "
                 "non-inferential; cannot alter the H-3 verdict)",
        "covariate_files": [RAIN_ANNUAL.name, RAIN_MONSOON.name],
        "covariate_note": "CHIRPS v2.0 0.05deg monthly 2011-2014, bbox "
                          "subset, bilinear to the origin-aligned 500 m "
                          "grid (scripts/p3_fetch_chirps.py); labels are "
                          "record-window (contemporaneous), NOT pre-2011 "
                          "per D-20(b) deviation note",
        "district_native_px_ranges": _native_ranges(),
        "overlap_all_cells_primary": overlap(kde_all, np.ones(n, dtype=bool)),
        "overlap_outside_wdpa_sensitivity": overlap(kde_all, outside_wdpa),
        "overlap_elephant_subset_sensitivity": overlap(kde_elp,
                                                       np.ones(n, dtype=bool)),
        "reading": "same reader as the run of record; joined as appendix "
                   "rows ONLY",
    }
    for tag in ("overlap_all_cells_primary", "overlap_outside_wdpa_sensitivity",
                "overlap_elephant_subset_sensitivity"):
        print(f"[{tag}]")
        for k, v in read2[tag].items():
            print(f"  {k:34s} top%ile {v['mean_pct_at_top_decile']:.3f}  "
                  f"rho {v['spearman_rho_vs_incident_kde']:+.3f}", flush=True)

    facts = {
        "date": TODAY,
        "pin": "prereg SS7 D-20 (freeze R8) - pinned BEFORE any rainfall "
               "statistic was computed",
        "deviation_status": "POST-HOC SENSITIVITY - H-3 outcomes were "
                            "already computed and seen (2026-11-02) under "
                            "D-18; this appendix read cannot change the "
                            "registered H-3 conclusion (D-20e binding "
                            "precommitment)",
        "reproduction_checks": {
            "kept_rows": int(len(rec)), "elephant_rows": int(rec.elephant.sum()),
            "placed_records": int(len(placed)), "tier_counts": tiers,
            "grid_cells": n, "outside_wdpa_cells": int(outside_wdpa.sum()),
            "records_in_surface_all": int(n_all),
            "records_in_surface_elephant": int(n_elp),
        },
        "read1_seasonality": read1,
        "read2_spatial_rainfall": read2,
        "fallback_unused": "IMD 0.25deg rejected as spatial covariate per "
                           "D-20(c); CHIRPS usable -> fallback not triggered",
        "governance": {
            "h3_verdict_standing": "unchanged: descriptive direction-check, "
                                   "no falsification verdict (D-3/D-18)",
            "significance_language": "none; no p-values or CIs computed",
            "quotable_in_p4_p5_as": "post-hoc sensitivity, non-inferential",
        },
        "caveats": [
            "Record-window (2011-2014) covariates are contemporaneous, not "
            "pre-2011 (documented D-20(b) deviation; construct = the "
            "incident window's own seasonality).",
            "CHIRPS native approx 5.5 km -> bilinear-smoothed at 500 m; "
            "within-cell variance is interpolated, not observed.",
            "Incident surface remains village-massed (place-name hotspot "
            "surface; audit-D-10).",
            "Rain-gauge under-representation in the Western Ghats is a "
            "known CHIRPS caveat (published literature).",
        ],
    }
    QA.mkdir(parents=True, exist_ok=True)
    FACTS.write_text(json.dumps(facts, indent=1, default=str))
    print(f"\nfacts -> {FACTS.relative_to(ROOT)}  (POST-HOC SENSITIVITY)",
          flush=True)
    return 0


def _native_ranges():
    with rasterio.open(PROC / "chirps_rain_annual_2011_2014_32643.tif") as s:
        a = s.read(1)
        v = a[a != NODATA]
        r1 = {"min": float(v.min()), "max": float(v.max()),
              "mean": round(float(v.mean()), 1), "n_valid_px": int(v.size)}
    with rasterio.open(PROC / "chirps_rain_monsoon_share_2011_2014_32643.tif") as s:
        a = s.read(1)
        v = a[a != NODATA]
        r2 = {"min": round(float(v.min()), 4), "max": round(float(v.max()), 4),
              "mean": round(float(v.mean()), 4), "n_valid_px": int(v.size)}
    return {"rain_annual_total_mm_2011_2014": r1,
            "rain_monsoon_jun_sep_share": r2}


if __name__ == "__main__":
    sys.exit(main())
