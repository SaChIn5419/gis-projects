# PROJECT STATE — Agroforestry land screening, Jhabua (MP)

**Status tracked here so a later session can pick up the same state.** Update after
every session: DONE → IN PROGRESS → NEXT.

## 1. Headline

Config-driven GIS screening of candidate degraded land (public data only) for an
agroforestry project under VM0047 ARR v1.1. **The real Jhabua run is complete**:
independent, unaffiliated, and a strict pre-feasibility screen — not an eligibility
determination and not a credit estimate.

**Run results (2026-10-21, all inputs valid, EPSG:32643 @ 30 m):**

| Where | ha | Share of district |
|---|---:|---:|
| District | 343,380.6 | 100% |
| Stage A — methodology-eligible | 324,094.0 | 94.4% |
| Stage B — candidate | 251,292.8 | 73.2% |
| Candidate carrying confidence flags | 197,590.4 | 57.6% |

Exclusions in order: woody 19,286.6 · built/water/wetland 4,300.2 · protected
(WDPA) 68,149.1 · steep (144.2) · small patches 207.7 · recent removal 0 ·
cropland 0 (the last two are **measured zeros**, not gaps).

## 2. Phase status

| Phase | What | Status |
|---|---|---|
| W1 Foundations | config, verified assumptions, QA gate, synthetic end-to-end | **DONE** |
| W2 Screening | ingest contract, 30 m aligned stack, reason codes, waterfall | **DONE (run 2026-10-21; QA 19 checks, 0 blocking)** |
| W3 Scoring | weighted overlay, Dirichlet sensitivity, stability map | not started (optional) |
| W4 Maps | 4 portfolio maps from real rasters (`scripts/make_maps.py`) | **DONE** |
| W5 Docs | README, limitations, data sources, learning manual, case study | **DONE** |
| W6 Portfolio packaging | case study, notebook lab, commit | **DONE (this session)** |

## 3. Key decisions (why)

1. **Census mode only.** VM0047 §4.3(8)(a)/§6.2 use <10% pre-existing woody biomass.
   The 10-year rule in §4.4.2(1) is a separate census **exclusion**, not the v1.0
   "non-forest for ten years" test.
2. **Area mode disabled.** §1.1/§4.4.1 need managed-forest, timber-harvest and
   native-ecosystem evidence that this repo does not have. Refuse rather than mislabel.
3. **Two-stage waterfall.** Stage A = methodology/data validity; Stage B = design
   screens. `methodology_eligible_ha` and `candidate_ha` are reported separately.
4. **30 m effective resolution.** WorldCover/S2 aggregate down; Hansen/DEM stay native.
5. **One reason-code contract.** 0 eligible, 1 woody, 2 built/water/wetland, 3 cropland,
   4 recent removal, 5 steep, 6 protected, 7 nodata, 8 small patch, 255 outside.
   Stage-B raw masks are supersets of waterfall rows: each pixel is attributed to the
   FIRST failing rule (verified by the notebook's byte-for-byte reproduction).
6. **QA gate measures rasters.** It opens every GeoTIFF; it does not trust a manifest.
7. **No credit forecast.** Pre-feasibility only.
8. **WDPA all-polygons, deliberately conservative.** Reserve/Protected Forest designations
   are kept in the exclusion; an IUCN I–IV sensitivity remains an optional follow-up.
9. **73.2% candidate is by design, not a bug.** Census mode keeps cropland (60.6% of the
   district). The candidate is a targeting pool, never a grant of eligibility.

## 4. Artifact hashes

- Verra VM0047 v1.1 PDF: `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`
- Raw boundary: `4fd352176b425954d6188d4c1a590dee70b226171608032e31d5879d849da8e5`
- Jhabua boundary extract: `f35e2f5b04bc6ccbcd99dd0a4d616f8f624df2ca7cbcf67868792e147e159c06`
- S2 dry raw: `e40040b746bdac3a1a241892bebb942a36236b3b3e551bb0e2b29db66021dc35`
- S2 monsoon raw: `8735395ef1c8901e1a013563d6853e4b31d6ed5be68dc658ce812ef50f95663e`
- All six raw-source hashes: `data/manifest.json` (canonical record)
- Jhabua area in EPSG:32643: **3,433.775 km²** → config reference **3,433.78 km²**

## 5. Artifacts on disk

- `data/processed/aligned/` — 11 aligned 30 m layers (git-ignored).
- `outputs/jhabua_agroforestry_screening/` — `reason_codes.tif`, `confidence_flags.tif`,
  `waterfall.csv`, `run_summary.json`.
- `outputs/maps/` — `01_study_area.png`, `02_reason_codes.png`, `03_waterfall.png`,
  `04_candidate_closeup.png`.
- `outputs/qaqc/qaqc_report.md` — QA gate report.
- `outputs/learning_lab/` — notebook scratch maps (`*_by_hand.png`, `*_bug.png`).
- `notebooks/learn_by_hand.ipynb` — hands-on companion; executed clean; all 8 capstone
  asserts PASS; the hand classifier reproduces `reason_codes.tif` byte-for-byte.
- `learning.md` — the 12-module GIS training manual (coursebook).
- `docs/case_study.md` — portfolio narrative + CV bullets.

## 6. Verification

- `python -m pytest -q` → **17 passed**.
- `python src/qaqc.py --check config/jhabua.yaml` → **19 checks, 0 blocking**; the
  "no screening output" warning is cleared now that outputs exist.
- `python scripts/make_maps.py config/jhabua.yaml` → 4 maps rendered.
- Notebook `learn_by_hand.ipynb` → **all 15 code cells runnable, 8/8 capstone asserts PASS**,
  reason_codes and confidence_flags reproduced exactly, 207.72 ha small-patch removal exact.

## 7. Blockers

None for the core screen. Optional, non-blocking follow-ups:
1. WDPA IUCN I–IV **sensitivity variant** (a one-config change; large narrative impact).
2. Woody-threshold sensitivity (10% vs 15%+).
3. QGIS `.qgz` project file for the 4 maps.
4. Public vs private repo decision (default: private portfolio copy).

## 8. Next action

If continuing: pick one optional follow-up from §7 and give it a config + docs entry.
Each is ≤1 day. Otherwise the project is complete as a portfolio artifact.
