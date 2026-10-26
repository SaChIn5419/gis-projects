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

---

## 9. NEW PROGRAM (2026-10-22): Tourism, Ecological Risk and Community Exposure Observatory

User decision: personal research program, **exactly two sites** — **Wayanad (Kerala) →
Mussoorie (Uttarakhand)**. No foreign benchmark, no third case. Each site is a full
investigation counted as Decision artifact. Plan: `/home/sachindb/.opencode/plan/tourism-ecological-risk-research-plan.md`.

### Phase P0 — delivered (2026-10-22): pre-analysis freeze

Three frozen artifacts, committed **before any outcome map is viewed**, now relocated (D-1)
into the dedicated program folder as the user requested:

- `tourism_observatory/docs/preregistration_wayanad.md` — hypotheses H1–H4 with falsification conditions,
  frozen control-selection rules (baseline-only covariates, calipers, seed 20261022,
  balance SMD < 0.10), information-boundary table (what may/may not be opened pre-freeze),
  validation plan V1–V3, append-only deviation log (D-0 freeze, D-1 relocation).
- `tourism_observatory/docs/literature_matrix.md` — ~25 entries in 4 groups (A: tourism→LUCC benchmarks;
  B: hill-station hazards + institutional; C: HWC spatial evidence; D: methods/risk),
  each with indicators + limitations + explicit verification flags; known gaps stated
  (hill-station resort-footprint literature thin = the study's own target gap).
- `tourism_observatory/docs/data_audit_wayanad.md` — source-by-source audit (21 sources), §6 checklist
  **PASS 6/6**, tracked risks R1 (HEC points, H), R2 (community-event compilation bias, M),
  R3 (imagery dating, L→M), with fallback chains.
- `tourism_observatory/README.md` — program structure, phase status, non-negotiable rules.
- Scope decision recorded (user, 2026-10-22): **exactly two sites — Wayanad → Mussoorie.**
  No foreign benchmark, no third case. Validation relies on Wayanad's published studies.

**Freeze hashes (SHA-256), re-recorded after D-1 relocation to `tourism_observatory/docs/`:**
- `tourism_observatory/docs/preregistration_wayanad.md` → `aa2ce6b89d2a71aaf331e15f84f783c86a1779abd2d38c224490cc1df622ac3d`
- `tourism_observatory/docs/literature_matrix.md` → `91e452b0bc02d35d08d8e577927dfabc8bf2668586c89ca3266edd6b5cafe784`
- `tourism_observatory/docs/data_audit_wayanad.md` → `5aa3efcdb523bd202b8fd1c0d49ff277d582e0ed8a68e6846f7bd310935d2eae`
- plan (external, reference only) → `fc14c24d8e4a4bc7abc63ce1767e23582d76da8a18ef5dd2da735cd8a462c5ec`

### C1 review outcome (2026-10-22): REVISE → revisions delivered via deviation entries D-2…D-8

External C1 design review of all three artifacts returned: principles/boundary **PASS**;
H1 REVISE · H2 BLOCK · H3 REVISE (hard data gate) · H4 REVISE (observational process) ·
audit verdict too strong · literature verification pending. All items were resolved
**append-only** in the preregistration deviation log (no frozen hypothesis text edited):
D-2 (H2a/H2b split, hazard-blind eligibility domain, scar populations separated) ·
D-3 (HEC gate + pre-2011 covariate window, leakage removed) · D-4 (H1 association
estimand, exact parcel grid, cluster rule, transition matrix) · D-5 (dispute unit, dedup,
precision classes, reportable-area null, EXPLORATORY flag) · D-6 (audit verdict →
CONDITIONAL GO, verification = file on disk + manifest hash) · D-7 (V1/V2/V3 criteria
tightened; alignment/comparability preconditions) · D-8 (source-type ledger +
verification queue, queued as P1 documentation).

**Authorization state (per reviewer): C1 sign-off remains PENDING**; **P1 baseline-only
work is authorized** with the information boundary unchanged: downloads + provenance
reports, baseline terrain/access covariates, facility-existence verification,
geocoding/alignment tests — **no H1–H4 outcome maps, no treatment-vs-control tests.**

**Freeze hashes R2 (post-D-1 relocation + D-2…D-8 revisions; supersedes hash table above for audit purposes — original R1 hashes retained for history):**
- `tourism_observatory/docs/preregistration_wayanad.md` → `d3e4cde2b87d7ce8a87aaa73337540f03f5ef5b2bd5232fd610fdb917b862ac2`
- `tourism_observatory/docs/literature_matrix.md` → `697dc1f593786432b996151846a80e0d22d9d9f66f3c2a7999c2b766a71e7110`
- `tourism_observatory/docs/data_audit_wayanad.md` → `327263b42f7225ce599a76625ae1b28a31186462a8dde9a4f4a5816af923a8bb`

**Freeze hashes R3 (post dev-D-9 administrative consistency pass; supersedes R2 for
verification — R2 values retained above for history):**
- `tourism_observatory/docs/preregistration_wayanad.md` → `2985fb4edba36a7b29853d05e065392dfe5d65755426baffbab89dd297dc195c`
- `tourism_observatory/docs/literature_matrix.md` → `578a995ad0e7334f03dd19f7898112d85bfc74c83872beab870d44fb7f20065b`
- `tourism_observatory/docs/data_audit_wayanad.md` → `aab7ef4df2947ba104c35e9bd32cca063257e5c9a79204d3bf95451644d89b2e`

**Freeze hashes R4 (post P1 acquisition-log append to the audit, §11; supersedes R3 for
verification — R2/R3 retained above for history; prereg and matrix unchanged since R3):**
- `tourism_observatory/docs/data_audit_wayanad.md` → `b27f58360f551979fcc7fa31ed584df4a4b3ef823983a638159cbcd7872ee56c`
- `tourism_observatory/docs/preregistration_wayanad.md` → `2985fb4edba36a7b29853d05e065392dfe5d65755426baffbab89dd297dc195c` (unchanged from R3)
- `tourism_observatory/docs/literature_matrix.md` → `578a995ad0e7334f03dd19f7898112d85bfc74c83872beab870d44fb7f20065b` (unchanged from R3)

**P1 first acquisitions (2026-10-22, hashes in `tourism_observatory/data/manifest.json`):**
geoBoundaries IND ADM2 pinned snapshot (`d68db39c…`) + Wayanad boundary @EPSG:32643
(`1d4f92cd…`); Kerala approved-homestay registry snapshot 2026-10-22 (`1c7d664c…`) with
51 Wayanad facilities parsed (`fda3aefd…`). OI-1/OI-3 closed; OI-4 partially closed
(currently-valid snapshot semantics confirmed — order date = latest renewal).

Consistency audit of record: `tourism_observatory/docs/c1_consistency_audit.md`
(findings, superseded-text trail, open items, remaining blockers).

Next action: user's final C1 sign-off on the revised artifacts; then P1 baseline-only
acquisition (`config/wayanad.yaml`, registry downloads with manifest hashes, baseline
composites, QA gate on baseline layers only, data-completeness + provenance report
→ feeds C2 go/no-go).

### C1 final sign-off (2026-10-23): SIGNED — recorded at prereg dev-D-10

Reviewer completed the final cross-check and granted final sign-off ("c1 sign off
yes"). Both §6 conditions of the consistency audit are met and logged: reviewer
cross-check performed; P1 empirical verifications logged — 17 sources with SHA-256 in
`tourism_observatory/data/manifest.json`, baseline QA gate **PASS (0 critical, 0
warnings, 62 checks, files opened directly)**, audit-D-10 R1 gate executed (aggregate
READY via open Figshare dataset; points do not exist at source — registered H3
fallback stands; the row's "*Frontiers* / 2011–2023" description corrected append-only
to *GECCO* 62:e03742 / events 2011–2014), audit-D-1 coverage start year verified
(2024-01-27; OI-4 closed: scheme GO 299/06 = 2006, GO 324/15 = 2015). Sign-off does
not change any §3/§4/§5 element; it releases the C1 condition and lets **C2** decide on
P1 data-completeness.

**P1 delivered (2026-10-23):** baseline stack on the frozen grid (DEM+slope, WorldCover,
Hansen 2000 tree cover, CCI-LC 2005 @300 m, WDPA union 855.8 km², OSM roads + distance,
AOI mask) — QA PASS; geocoding round 2 (51/51 in-district, P2–P5 precision classes,
round 1 archived); registry sources D-2/D-3/D-4 + OI-4 order acquired and hashed;
`tourism_observatory/docs/p1_provenance_report.md` is the C2 input
(`8a3140cf4fc68c19…`). Consistency audit addendum §8 records the sign-off conditions.

**Freeze hashes R5 (post dev-D-10 sign-off entry + §11 research/registry log + matrix
verification results; supersedes R4 for verification — R2/R3/R4 retained above):**
- `tourism_observatory/docs/preregistration_wayanad.md` → `420d252cc979ca91048a3007acea890d1c7396603c64d1a452a6d8b33645fe1a`
- `tourism_observatory/docs/literature_matrix.md` → `7a7933666f2a4b3503afa89cdb4726e77ab77c425d6333602bf67b9ce1ba8aa1`
- `tourism_observatory/docs/data_audit_wayanad.md` → `7e4e9da2ebfb602711fbdbe5a9e52047c901462e441bec2be155ff4e3b7ad2ed`
- (audit-of-record, not part of the freeze trio but tracked here: `c1_consistency_audit.md` → `710739bf413f62808b21d5dd6c18564264696d6e4591e29712e34f4ade7b15d6`)

Next action: **C2 — P1 data-completeness go/no-go** on
`tourism_observatory/docs/p1_provenance_report.md` (QA PASS + 17-source manifest +
registry/D-10 verifications; residual non-blocking items listed in report §7–§8). On
C2 go → P2 (control matching) under the unchanged prereg §4/§5 boundary.

### C2 decision (2026-10-23): GO

User decision on `tourism_observatory/docs/p1_provenance_report.md` §7–§8: **GO** —
P1 data-completeness accepted; residuals (A4-numbers/B4-primary verify flags,
fresh-vs-renewal inference, hazard downloads D-5…D-8, facility-exact existence
verification) explicitly accepted as non-blocking and carried into P2. **P2 is open:**
matching/covariate/verification work proceeds under frozen prereg §2/§4/§5 (treatment
verification, parcel grid, baseline covariate tables, exclusions, 1:1 match + balance
table); no H1–H4 outcome computation before the freeze gate. Next concrete P2 steps:
(a) treatment-arm existence verification at ~10 m (Sentinel-2, as preregistered);
(b) D-5…D-8 hazard acquisitions (Atlas, 2024 scar extent, terrain/rainfall) — required
for §4.4 exclusions and H2; (c) 1 km parcel grid + baseline covariate tables; (d)
deterministic 1:1 matching (seed 20261022) with SMD balance gate < 0.10.

### P2 milestone (2026-10-26): matching complete, balance gate PASS

Executed under frozen prereg §4/§5, no outcome rasters read (§5 boundary intact).

- **Facility universe (D-11a/b):** M5 homestays + D-2 portal → **123 facilities**
  (81 portal JSON-LD pin > 31 M5 geocode > 11 fresh PIN ladder; no jitter).
  Existence check on Sentinel-2 10 m quicklooks → **107/123 verified** (structure
  within 100 m). Evidence: `outputs/qaqc/p2_existence_universe/` + facility CSVs.
- **Scar (D-6 → D-12 correction):** v1 (PMC Fig.1 centerline) was QA-found ~2 km
  north of the published crown (0.000 km² overlap) and discarded **before any
  matching ran on it**. v2 re-digitized from the NRSC VAP3 impact map
  (`scripts/p2_digitize_vap3_scar.py`, in-map georeferencing, green-dot latitude
  error 15.2 m): centerline **7,221 m** (≈8 km published), corridor **1.781 km²**,
  crown inside. QA: `outputs/qaqc/p2_scar_digitization_qa.json` + `_overlay.png`.
- **Parcels + covariates (§4.1/§4.3):** 1 km grid, `scar_excluded=true` build →
  2,020 parcels, 857 excluded (<50 % eligible), **1,163 usable**; road terciles
  388/387/388. Facts: `outputs/qaqc/p2_parcel_facts.json`.
- **Arms + match (§4.2/§4.5):** **54 treatment / 886 control**; greedy 1:1 no
  replacement, seed 20261022, exact road-tercile + calipers. **50/54 matched**,
  max|SMD| = **0.0667 < 0.10 → PASS**. 4 unmatched on calipers.
- **Outputs:** `matched_pairs_2026-10-26.csv`,
  `outputs/qaqc/p2_match_balance_2026-10-26.json`, `p2_match_facts_2026-10-26.json`.

Deviation log through **D-12** (`docs/preregistration_wayanad.md` §7) — all
pre-outcome implementation details, none changes a hypothesis, covariate, exclusion
rule, caliper, or seed. Next action: **§8 pre-analysis checklist → freeze (R6) → P3
(outcome work) under the frozen design.** Residual non-matching item carried: D-5
ISRO Landslide Atlas 2023 (needed for H2, not for matching).

### Freeze R6 (2026-10-26) — §8 checklist signed, design frozen for outcome work

§8 pre-analysis checklist completed and signed (dated verification block in
`preregistration_wayanad.md` §8). Mechanical confirmations: hypotheses §3 and
controls §4 byte-identical to the R5-frozen text (prereg diff `893ad83`→verification
commit is 55 additions / **0 deletions**, all inside §7); match executed with balance
table reported (max|SMD| 0.0667 → PASS); deviation log justified (D-1…D-12, all
pre-outcome); scope resolved to exactly two sites (Wayanad, Mussoorie). **P3 outcome
work (H1–H4) is now authorized under §5.**

**Freeze hashes R6 (supersede R5 for verification; R2–R5 retained above):**
- `tourism_observatory/docs/preregistration_wayanad.md` → `d51857fc86c445edeb53a608a523643e14654a76197dd94c32b8910be3f7af7d`
- `tourism_observatory/docs/literature_matrix.md` → `7a7933666f2a4b3503afa89cdb4726e77ab77c425d6333602bf67b9ce1ba8aa1`
- `tourism_observatory/docs/data_audit_wayanad.md` → `7e4e9da2ebfb602711fbdbe5a9e52047c901462e441bec2be155ff4e3b7ad2ed`

Analysis input of record at R6: scar v2 (`data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg`,
D-12), covariates `parcel_covariates_2026-10-26.csv`, pairs `matched_pairs_2026-10-26.csv`
(50 pairs, seed 20261022). Any post-R6 change to the frozen trio requires a §7 entry
+ R7 re-hash before outcomes are examined under the changed rule.
