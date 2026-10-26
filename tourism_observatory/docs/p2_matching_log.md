# P2 — Control-selection & matching log (Wayanad)

Status: **P2 in progress.** Preregistered rules (frozen `preregistration_wayanad.md`
§2/§4/§5) are the authority; this file records the runnable implementation choices and
their QA evidence. Any *change* to a frozen rule is a §7 deviation-log entry (D-11); this
file only documents the mechanics and their provenance.

**Information boundary (§5):** everything below is covariate / treatment construction.
**No outcome raster (H1–H4 dependent variable) was read, mapped, or tested at any point
in P2.** Treatment-vs-control outcome comparison is a post-freeze step.

## Step (c) — parcel grid + baseline covariates — `scripts/p2_parcel_covariates.py`

- Units: 1 km equal-area parcels (§4.1) on the frozen analysis grid (origin
  `584100, 1324500`, EPSG:32643); parcel kept when its centroid falls inside the AOI.
- Baseline-only covariates (§4.3, 2000–2005): mean slope, mean elevation, CCI-LC 2005
  dominant class + per-class shares, Hansen treecover 2000, road-distance tercile.
  WorldCover 2021 shares are deliberately **excluded** from the matching table (post-2005).
  Road distance is a **current-OSM proxy** (dev-D-4 label), not a baseline observation.
- Exclusions from both arms (§4.4): AOI ∩ ¬water ∩ ¬WDPA(all_touched) ∩ ¬scar.
- **Eligibility spec detail (logged, not a rule change):** a parcel joins both arms only
  if its eligible-pixel share ≥ **0.50**; covariates computed on eligible pixels only.
- Result: 2,020 parcels; 857 excluded (<50 % eligible share); **1,163 usable**; covariates
  complete (no NaN) on all usable parcels; road terciles balanced 388/387/388;
  `outputs/qaqc/p2_parcel_facts.json` (`scar_excluded=false` at this build — see blocker).
- Scar-absent run is **expected now**; the build must be re-run after D-6 before matching.

## Step (a)+(b) — facility universe + existence verification

- Universe = union of M5 approved homestays + D-2 classified portal → **123 facilities**
  (D-11(a)). Scripts: `p2_classified_registry.py` (parse/enrich D-2), `p2_facility_universe.py`
  (dedupe + best-coordinate), `p2_existence_quicklooks.py` (Sentinel-2 10 m quicklooks).
- Verification (§2): structure within **100 m** on imagery → **107/123 verified**
  (66 at-point, 41 within 100 m). Evidence: `outputs/qaqc/p2_existence_universe/`
  (103 quicklooks, one per distinct coordinate) + `verdicts_partial.json`;
  facility-level table `data/processed/facility_existence_universe_2026-10-23.csv`.
- No geocoding jitter; precision classes (P1…P5) retained per facility and cap claims.

## Step (d) — matching — `scripts/p2_match.py`

- Treatment (54 parcels) / control (886) per §4.2 + D-11(c).
- Greedy 1:1, no replacement, standardized Euclidean distance, **seed 20261022**,
  exact road-tercile match, calipers slope ±3° / elev ±100 m / dominant-share ±10 pp /
  Hansen ±10 pp (§4.3). Balance table: |SMD| < **0.10** gate (§4.5).
- **Hard gate:** the matcher refuses to run until the 2024 Chooralmala–Mundakkai scar
  layer exists (`data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg`) and the
  covariates are rebuilt with `scar_excluded=true`. This is enforced in code, not by habit.
- A smoke test (scratch scar outside the repo) exercised the full code path and was
  **deleted**: 50/54 matched, max|SMD| = 0.067 → PASS; 4 treated dropped on calipers.
  This was **not** an analysis result and did not satisfy §8 (which needs the real,
  scar-excluded build). It is superseded by the real run below.

## Step (c2) — scar v2 (D-12): re-digitized from NRSC VAP3

- v1 (PMC12290006 Fig. 1 centerline) was QA-found **~2 km north of the published
  crown**, 0.000 km² overlap with the published extent → discarded **before any
  matching ran on it** (D-12).
- v2 built by `scripts/p2_digitize_vap3_scar.py` from the NRSC/ISRO VAP3 impact map
  (Charter Call 1029, AOI 01, observed 31/07/2024): in-map graticule georeferencing
  (green-dot latitude error **15.2 m**), RGB extraction of the published Debris Flow
  outline, inset-box border removal, skeleton + crown→NE-tip path, 150 m buffer.
- Result: centerline **7,221 m** (~8 km published), corridor **1.781 km²**, crown
  inside. QA: `outputs/qaqc/p2_scar_digitization_qa.json` +
  `p2_scar_digitization_overlay.png` (overlay traces the flow crown→Vellarimala).
- Rebuilds with the corrected scar: covariates `scar_excluded=true`, **1,163 usable
  parcels** (unchanged); arms **54 / 886** (unchanged — corridor is uninhabited).

## Step (d2) — REAL matching run (scar-excluded build)

- Covariates `data/processed/parcel_covariates_2026-10-26.csv`; arms 54/886;
  scar gate satisfied (`scar_excluded=true`, no override).
- Result: **50 / 54 treated matched**; 4 dropped on calipers
  (`no_control_passed_calipers`). Balance: max|SMD| = **0.0667** < 0.10 → **PASS**.
  SMDs: slope 0.038, elevation 0.067, dominant-share 0.000, Hansen 0.036,
  road-tercile_1 0.000, road-tercile_2 0.000.
- Outputs: `data/processed/matched_pairs_2026-10-26.csv`,
  `outputs/qaqc/p2_match_balance_2026-10-26.json`,
  `outputs/qaqc/p2_match_facts_2026-10-26.json`.
- No outcome raster was read at any point (§5). The §4.5 gate passed on the first
  real build, so **no re-specification was needed and none was made**.

## Blockers (carried from C2)

1. ~~**D-6 scar layer**~~ — **RESOLVED** (v2 above, D-12); covariates rebuilt;
   real match run → balance table PASS.
2. **D-5 ISRO/NRSC Landslide Atlas 2023** — needed for H2, not for matching.
3. Next: §8 pre-analysis checklist → freeze (R5) → outcome work (P3) under the
   frozen design.
