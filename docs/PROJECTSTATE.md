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
- Verification commit: **`74f42f76d6386fa20550d3c096e3ab194665a04a`** (this freeze
  entry; the match build itself is commit `c41edca`).
- `tourism_observatory/docs/preregistration_wayanad.md` → `d51857fc86c445edeb53a608a523643e14654a76197dd94c32b8910be3f7af7d`
- `tourism_observatory/docs/literature_matrix.md` → `7a7933666f2a4b3503afa89cdb4726e77ab77c425d6333602bf67b9ce1ba8aa1`
- `tourism_observatory/docs/data_audit_wayanad.md` → `7e4e9da2ebfb602711fbdbe5a9e52047c901462e441bec2be155ff4e3b7ad2ed`

Analysis input of record at R6: scar v2 (`data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg`,
D-12), covariates `parcel_covariates_2026-10-26.csv`, pairs `matched_pairs_2026-10-26.csv`
(50 pairs, seed 20261022). Any post-R6 change to the frozen trio requires a §7 entry
+ R7 re-hash before outcomes are examined under the changed rule.

### P3 H1 computed (2026-10-28) — first treatment/control outcome comparison under R6

H1 land-conversion analysis executed per the D-14 measurement spec (pinned
2026-10-26 before any arm difference). Script `tourism_observatory/scripts/p3_h1_analysis.py`;
narrative `tourism_observatory/docs/p3_h1_analysis_log.md`. 50 matched pairs,
pixel-union treatment buffers vs matched-control-centroid buffers, eligibility
mask identical to matching (AOI ∩ ¬water ∩ ¬WDPA ∩ ¬scar-v2), paired t-test +
Wilcoxon with Holm across radii, robustness at 500 m (WorldCover-strict built;
Hansen loss proxy).

**Result:** treatment conversion exceeds control at every radius —
250 m +24.01 pp, **500 m (primary) +16.32 pp** (t-test Holm p=1.68e-06;
Wilcoxon Holm p=6.51e-07), 1,000 m +11.61 pp; robustness signs agree
(WC-strict +5.24 pp; Hansen +1.96 pp). By the frozen §3 rule **H1 is NOT
falsified; direction supported.** Claim language deferred to the P5 brief.
Pre-existing-development stratum empty by registry-date proxy (D-14(v)),
labelled. QA gate: rasterisation fidelity ≤2.20 %, zero zero-denominators,
numerator⊆denominator everywhere, no treatment/control geometry overlap.
No frozen rule, covariate, caliper or seed was changed; no new deviation entry
was needed for this step.

**Hashes (P3 H1 artifacts):**
- `tourism_observatory/outputs/qaqc/p3_h1_facts_2026-10-28.json` → `85d1597c1bc5936322c9c99321b487feed22bfbbcdd3fe3d9262a204bf114734`
- `tourism_observatory/data/processed/h1_pair_rates_2026-10-28.csv` → `dbec3c6f6043287555c74b59377b61adfa6da2f87d75be7fd06abad8b5bb4ed6`
- `tourism_observatory/docs/p3_h1_analysis_log.md` → `5ba6fae33aa79a02a7f82817f1e8029690c0d55ca416cecee0103f0e7c33bb0a`
- `tourism_observatory/scripts/p3_h1_analysis.py` → `ab992944c6adc7a99ee60641b7b0ea01bc44efb0db3d0fcd0045d3366fbe2516`

Next: H3 hard data gate (HEC incident-table availability, D-3 downgrade path
frozen), then H2 (D-5 Atlas inventory decision) and H4 (event-table compile).

### D-15 logged + Freeze R7 (2026-10-28) — H2 inventory input substituted, before any H2 statistic

The D-5 Atlas blocker was resolved by user decision on 2026-10-28: **attempt
WMS-render polygonization first.** Retrieval attempts and their outcomes:
Bhuvan WFS disabled (2026-10-23); GetFeatureInfo returns empty GML at every
probe *including* coordinates where GetMap visibly renders polygons; capability
Abstracts empty for all six candidate Kerala layers. An earlier
"byte-identical across 6 layers" finding was **retracted** the same day — it
came from WMS 1.3.0 + `CRS=EPSG:4326` with a lon,lat BBOX (lat,lon axis order
→ server default view). Corrected protocol (WMS 1.1.1 + `SRS=EPSG:4326`)
shows the layers differ; `disaster:kl_landslides_new` (style "Kerala
Landslide") carries the most Wayanad content.

**Substitution:** H2a(ii) and H2b(b) input data = polygons polygonized from
81 overlapping 10 m GetMap tiles (75.75–76.47 E / 11.20–11.82 N, brown-mask
union across 50 % overlap → per-tile "bhuvan" watermark removed),
`data/processed/inventory_wms_kl_landslides_new_32643.gpkg` — 1,151 polygons,
29.82 km², all inside the district. **Test family unchanged** (H2a Holm within
{i,ii}; H2b descriptive (a)+(b)); §3 text byte-unchanged — only input data
substituted. Validity caveats (no attributes/vintage; Jul-2024
Chooralmala–Mundakkai event absent from all six layers, ≤0.5 % VAP8 scar
coverage; ±10 m boundary precision; documentation bias presumed) are recorded
in full in prereg §7 D-15. Measurement recipe for both statistics was pinned in
the D-15 text **before computation**. Deviation entry + this R7 record were
written before any H2 statistic was computed, per the R6 consequence rule.

**Freeze hashes R7 (supersede R6 for verification; R2–R6 retained above):**
- `tourism_observatory/docs/preregistration_wayanad.md` → `943e9f9ce0c8367d6181f4d5a76a172c27836554dc0e5b833d216fd64e171174`
  (R7d: re-hashed after the D-18 entry (H3 descriptive-fallback recipe pinned
  before computation), 2026-10-28. History: R7 draft `541bd46e…` (D-15 body)
  → R7a `5637e6ac…` (D-15 pinned clarifications) → R7b `d4e258cd…` (D-16
  defect + corrected-test registration, pre-computation) → R7c `176da474…`
  (D-17 extent-audit fix, pre-refetch) → R7d `943e9f9c…` (D-18 H3 recipe
  pin, pre-H3-computation). All five retained for audit.)
- `tourism_observatory/docs/literature_matrix.md` → `7a7933666f2a4b3503afa89cdb4726e77ab77c425d6333602bf67b9ce1ba8aa1` (unchanged since R6)
- `tourism_observatory/docs/data_audit_wayanad.md` → `7e4e9da2ebfb602711fbdbe5a9e52047c901462e441bec2be155ff4e3b7ad2ed` (unchanged since R6)

**Hashes (H2 inventory proxy inputs of record):**
- `tourism_observatory/data/raw/staging_h2/kl_landslides_new_wayanad_mosaic_10m.tif` → `da8b3af673420b078c36a0406362193c921c777823d0a008fb4c4d1b6cb007e9`
- `tourism_observatory/data/processed/inventory_wms_kl_landslides_new_32643.gpkg` → `4411b9bb7a238dcfdb8022e32159df59e9311112d592aea01e7bba5b51771207`
- `tourism_observatory/outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json` → `1e95024dd8fb8d97bd58559e8ae697a2dc2dfc90f5619e40438cc64317f62868`
- `tourism_observatory/scripts/h2_fetch_wms_inventory.py` (fetch/polygonize script)

Next: compute H2a(i)+(ii) and H2b(a)+(b) under the D-15-pinned recipes, then
H3 (Figshare HEC descriptive KDE-percentile path) and H4 event table.

### D-16 logged + Freeze R7b (2026-10-28) — sign-test defect found at first H2a computation

First H2a computation (`scripts/p3_h2a_analysis.py`) ran clean: domain
2,020 grid points → **876 eligible**; 107/107 verified facilities evaluable;
elevation band [736, 917] m; caliper pool min/median 15/71 (no pool-size
correlation with percentiles, |r| = 0.006). Registered outputs
(`outputs/qaqc/p3_h2a_facts_2026-10-28.json`, CSV
`data/processed/h2a_facility_percentiles_2026-10-28.csv`, KDE GTiff
`outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif`):

- (i) slope ≥ 25°: observed share 0.009 (1 facility, F027, null share 0.0)
  vs null share 0.003; mean percentile 0.503; signs +1/−35 (71 ties);
  **p_holm 2.15e-09**
- (ii) KDE density: mean percentile 0.561 (median 0.402); 71/107 facilities
  with obs_kde = 0; signs +36/−71 (0 ties); **p_holm 9.23e-04**

**Defect:** inspecting the incoherence (mean 0.503 vs signs −35/+1) showed the
D-15(d) sign test's own null is not 50/50 for point-massed metrics. Under
exchangeability, P(sign +) = q ≈ 0.003 for binary (i) — observed +1 is exactly
the null expectation — and P(sign +) = 1−π₀ ≈ 0.34 for zero-inflated (ii) —
observed +36/−71 is exactly the null expectation. **Both registered sign-test
p-values are artifacts of the convention**; the midrank mean percentile stays
valid (E = 0.5 under H0). Derivation is direction-free: it does not depend on
which way any result pointed.

**Correction (D-16, registered before computing):** family inference = the
§3-H2-frozen Monte Carlo observed-vs-null exceedance form — T_obs at the 107
observed facilities vs T_j at j-th null draws (same deterministic seeded
draws), p = (1 + #{T_j ≥ T_obs})/1001, Holm across {i,ii}. Registered outputs
retained verbatim and labelled non-interpretable for the sign tests; corrected
p-values carry the H2a verdict. R7b re-hash above was written before the
corrected tests ran.

Next: corrected D-16 tests → H2a verdict → H2b registers → H3 → H4.

### H2a COMPLETE (2026-10-28) — corrected D-16 tests computed; H2a NOT falsified

Corrected Monte Carlo exceedance tests ran exactly as registered in D-16
(same deterministic draws; registered outputs reproduced byte-identical):

- **(i)** count on slope ≥25°: T_obs = 1 vs null mean 0.355 (max 3) →
  p_raw = p_holm = **0.293** (directionally above null, not significant).
- **(ii)** mean observed KDE inventory density: T_obs = 0.0012524 vs null mean
  0.0004923, p95 0.0009179 → p_raw 0.01199, **p_holm = 0.024** — observed
  overlap **exceeds** the null expectation (T_obs above 98.8 % of null worlds).

**H2a verdict (frozen §3 rule, "falsified if observed overlap ≤ null
expectation"): NOT falsified** — the Atlas-inventory-density statistic (ii)
shows significant exceedance (p_holm 0.024); the slope-share statistic (i) is
a non-significant directional excess. Interpretation is *siting preference
only* (D-2 guard): exposure/risk claims require H2b. Registered sign tests
reported verbatim but labelled non-interpretable per D-16.

**Hashes (P3 H2a artifacts — run 1, superseded by D-17; retained for audit):**
- `tourism_observatory/outputs/qaqc/p3_h2a_facts_2026-10-28.json` → `25968f6e6e621b51b2d590ed6683b7aca41e144286d33cc6b1aa7df02f52f56e`
- `tourism_observatory/data/processed/h2a_facility_percentiles_2026-10-28.csv` → `25ef81f4479d65f368233be9a6ecee5e8d203da4908d973790f3fe5e4c99b9bf`
- `tourism_observatory/outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif` → `7bb4c5318023e3a19626fa3ecef03d371d4ac78e6b553b6684c8ee9dca89ed31`
- `tourism_observatory/scripts/p3_h2a_analysis.py` → `e2bab79c8df4fc820467738d470d6669b4a8a0151f410ad083a6d3717ee4cd1e`
- `tourism_observatory/docs/p3_h2_analysis_log.md` (narrative of record, incl. defect proof + verdict)

Next: H2b(a) scar-footprint + H2b(b) 1 km inventory-buffer exposure registers
(descriptive; precision classes + spatial uncertainty), Google Open Buildings
acquisition (data-audit D-17) first, then H3 and H4.

### D-17 logged + Freeze R7c (2026-10-28) — extent-audit coverage-window error; H2a rerun ordered before H2b

A systematic extent audit (dataset bounds vs the district reference, run while
preparing H2b) found two extraction windows truncated the district against its
north edge. District reference (geoBoundaries ADM2 Wayanad = AOI =
`aoi_mask`/parcels/roads) spans **75.7742–76.4443 E / 11.4515–11.9781 N**:

- **D-15 inventory fetch window** `75.75–76.47 E / 11.20–11.82 N` omits lat
  11.82–11.978 — the northern district strip where **16 of the 107 verified
  facilities** lie. Mosaic/inventory bounds confirm: max lat 11.8176.
- **P1-era OSM buildings window** `75.73–76.40 E / 11.20–11.80 N` omits the
  same north strip plus the east strip 76.40–76.444 E (76,206 buildings).
- Roads, parcels, AOI rasters and analysis grids confirmed district-complete.

**Timing disclosure:** discovered *after* the first H2a computation and before
any H2b count, by an objective bounds comparison — no outcome value entered
the discovery; no statistic was inspected to choose the correction. The first
H2a outputs (above) are **superseded** — retained verbatim in git/PROJECTSTATE
history; D-16's corrected-test registration is unchanged and reruns on the
corrected inventory.

**Correction (full entry in prereg §7 D-17):**
(a) re-fetch WMS inventory over `75.75–76.47 E / 11.42–12.00 N` (district +
≥0.02° pad), same layer/protocol/10 m/50 %-overlap recipe, then recompute H2a;
(b) re-extract OSM buildings from the same source PBF (unchanged hash) over
`75.73–76.47 E / 11.42–12.00 N`, clipped to the district window. Manifest
entries updated in place (same ids, new sha256 + D-17 note). Test family,
calipers, seed, KDE recipe, D-16 registration unchanged — input-coverage fix,
not a design change.

**R7c** = prereg re-hash after the D-17 entry (written before the corrected
inputs were fetched): `176da4740804c03c4d4ddf3bb6e4b9491207eb5d3954ac50bab3661e33c7b626`.
History chain R7 `541bd46e` → R7a `5637e6ac` → R7b `d4e258cd` → R7c `176da474`
all retained.

Next: refetch inventory (D-17a) → re-extract OSM buildings (D-17b) → rerun H2a
→ update hashes/manifest → H2b → H3 → H4.

### D-17a/b executed + H2a RERUN COMPLETE (2026-10-28) — district-complete inputs; H2a verdict unchanged (NOT falsified), stronger on (ii)

All three D-17 corrections executed, in the registered order:

- **D-17a inventory refetch** (`75.75–76.47 E / 11.42–12.00 N`, 72 tiles,
  script byte-unchanged except BBOX + de-hardcoded QA note): **990 polys,
  24.061 km², all inside district; 229 polys (3.568 km²) north of 11.82 N** —
  the strip the first window missed (confirming the audit). VAP8 QA
  reproduced: 2 intersecting, 7 within 500 m, 0 touching, 1.48 % scar
  coverage (Jul-2024 event still absent, as in run 1).
- **D-17b OSM buildings re-extraction** (`75.73–76.47 E / 11.42–12.00 N`,
  same PBF + same GDAL OSM recipe): **69,126 buildings** (extent now covers
  the north and east strips; net −7,080 vs the truncated window because the
  old window also covered 11.20–11.42 N outside the district).
- **H2a rerun** (`p3_h2a_analysis.py` unchanged, seed/calipers/D-16 tests as
  registered): registered outputs reproduced as artifacts of the fresh data;
  corrected D-16 exceedance tests:
  - **(i)** T_obs = 1 vs null mean 0.355 (max 3) → p_holm **0.293**
    (unchanged, slope layer untouched).
  - **(ii)** T_obs = 0.0029206 vs null mean 0.0011454, p95 0.0021635 →
    p_raw 0.006993, **p_holm = 0.01399** (run 1: 0.024 — exceedance
    strengthened on the district-complete inventory).

**H2a verdict: NOT falsified — unchanged**, resting on (ii); interpretation
guard (siting preference only) carries over. Run-1 artifacts superseded and
overwritten in place; data artifacts are gitignored, so the audit trail is
the hashes below + the run-1 stats retained in this file and
`docs/p3_h2_analysis_log.md` §7 (run 2 in §8).

**Hashes (files of record after D-17):**
- `tourism_observatory/outputs/qaqc/p3_h2a_facts_2026-10-28.json` → `f34327954bdd76c9acd081396699866039ce64a66a68644397504b393e040919`
- `tourism_observatory/data/processed/h2a_facility_percentiles_2026-10-28.csv` → `3214370aa6b1e6fd963852782f61349da295d46fc2ef92a790cc862331871575`
- `tourism_observatory/outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif` → `c9a1c6af717363882f59d53c8c44f99fd6f6c872a4db4f5dacbe4583d1733759`
- `tourism_observatory/data/processed/inventory_wms_kl_landslides_new_32643.gpkg` → `c12ee632fe7da200759370c530ea63b4db61cbf503e76315765049bf48656e78`
- `tourism_observatory/data/raw/staging_h2/kl_landslides_new_wayanad_mosaic_10m.tif` → `17938cee277734df38043e725a9400770f57db7d9f3b86d3c98ac7c6ee2da835`
- `tourism_observatory/outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json` → `4eb2712f6307cf9b8b7374fa50b3a36644e12a24511d6104397b27b8a3ff92e1`
- `tourism_observatory/data/processed/buildings_osm_wayanad_32643.gpkg` → `c189c9e3162214bda50378bf11e2bd7ba403b8ee747be68f848808bf1d12f7db`
- `tourism_observatory/scripts/p3_h2a_analysis.py` → `e2bab79c8df4fc820467738d470d6669b4a8a0151f410ad083a6d3717ee4cd1e` (unchanged)
- `tourism_observatory/data/manifest.json` (25 entries; 3 updated in place for D-17)

Next: Google Open Buildings v3 stream-fetch (H2b building source, level-6 S2
cells 3ba5/3ba7/3ba9/3baf, raw streams hashed in flight) → `p3_h2b_analysis.py`
registers (a) scar footprint + (b) 1 km inventory-proxy buffers → H3 → H4.

### H2b COMPLETE (2026-10-28) — descriptive exposure registers as frozen; H2 phase closed

GOB v3 acquired by streaming Google's own bucket (level-6 S2 cells
3ba5/3ba7/3ba9/3baf; raw gzip sha256 hashed in flight, not stored; Source
Cooperative unreachable from this machine): **636,445 footprints** in the
district+1.2 km-pad window, confidence 0.650–0.966, CC BY 4.0, imagery ≤ May
2023 → `data/processed/buildings_google_wayanad_32643.gpkg`. Manifest now
**27 entries** (+GOB, +scar vector which had been missing from the manifest).

`p3_h2b_analysis.py` ran the frozen D-2/D-15 register recipe (descriptive;
(a) digitized 2024 scar footprint; (b) 1 km buffers of the D-17a proxy
inventory; every entry carries its footprint-source precision class;
uncertainty = count range under ± the class's positional-uncertainty
jitter):

- **(a) 2024 scar (1.781 km²):** 0 facilities, 0 buildings (GOB and OSM),
  1 construction-class road segment, 0.758 km [0.720, 0.835]. The mapped
  debris-flow corridor contains no mapped built stock.
- **(b) inventory buffers (992.9 km² = 46.6 % of district):** 26/107
  facilities; GOB 73,027 (57,291 at confidence ≥0.7) [71,980, 74,050];
  OSM 10,389 [10,242, 10,521]; OSM roads 3,184 segments / 1,370.055 km
  [1,355.112, 1,384.882]. Reading guard recorded: the union covers 46.6 %
  of the district — raw counts are register counts, not area-adjusted
  excesses; documentation bias + proxy-excludes-Jul-2024 caveats attached;
  (a) and (b) cover different event populations, never merged.

**Hashes (H2b artifacts):**
- `tourism_observatory/outputs/qaqc/p3_h2b_facts_2026-10-28.json` → `e50ae8bd1701360f6f4b00cbfa060e4b051b3e59a7dd132f05b4c411e830f0f1`
- `tourism_observatory/outputs/qaqc/h2b_facility_exposure_register_2026-10-28.csv` → `550d63506551b0e1ed5d15ee6e987d3f195915d6b7f4a27903bf0e300350250a`
- `tourism_observatory/outputs/qaqc/h2b_google_buildings_fetch_facts_2026-10-28.json` → `8d4c3ddc3ea5867a312df58887378bc147e8e2674eb25ff227f3d05873efa62d`
- `tourism_observatory/data/processed/buildings_google_wayanad_32643.gpkg` → `d8ea52b199289347ef7d4a707cc293b47631569e9519c7181fb2cb4e1948e780`
- `tourism_observatory/scripts/p3_h2b_analysis.py` → `6686efe77b3cba9ab0b060d8e1c20d1ee2989f437a6c7aa11831e1d0f289b8f7`
- `tourism_observatory/scripts/h2b_fetch_google_buildings.py` → `56001bcf4d84387c7460aae3c0bf28ce582fbf0e3b4b035b1799c75ff265b345`
- `tourism_observatory/docs/p3_h2_analysis_log.md` (§1–§9 narrative of record)
- `tourism_observatory/data/manifest.json` → 27 sources (GOB + scar vector added)

**H2 phase (H2a + H2b) closed.** Next: H3 (HEC records in
`data/raw/staging_h3/` — D-3 screen before any model choice) → H4.

### D-18 logged + Freeze R7d (2026-10-28) — H3 descriptive-fallback recipe pinned before computation

The R1 gate (audit-D-10, logged 2026-10-23, **pre-freeze**) established the
Morrison et al. (2025, GECCO 62:e03742) HEC records **never contained GPS
coordinates** (village-name level; the paper simulated points by conditional
random sampling), so the D-3-registered downgrade to a **descriptive
hotspot-overlap analysis** is active: no Poisson/NB, no IRR table, no
residual Moran's I. Screen of the Figshare workbook (pre-model, per D-3):
4 year-sheets 2011–2014, parsed row counts 446/721/890/688 = 2,745; no
coordinate columns in any sheet; date typos/out-of-window values present
(2101, 0013, 2027, epoch 1970) to be dropped and counted; nature categories
case-normalized (crop damage dominant); species mix elephant-dominated
(ELP 1,581 + ELEPHANT 248 + mixed) — construct validity holds; 373 unique
place names + 59 sections; 2014 sheet has no Place column.

**D-18 pins (prereg §7, written before any H3 statistic):** place-name
geocoding (Nominatim, district viewbox, cached, precision tier
place→section→range-centroid), incident KDE σ = 1,000 m on the 500 m grid,
pre-2011 covariates only (Hansen 2000 edge/cover, CCI 2005 cropland/urban,
Hansen 2000–2010 loss; GLAD 2000–2020 gain as labelled-leaky secondary;
rainfall unavailable), overlap = percentile comparison + Spearman rho as
descriptive effect sizes (no p-values/CIs), V2 direction check against the
paper's stated drivers. **R7d** = `943e9f9ce0c8367d6181f4d5a76a172c27836554dc0e5b833d216fd64e171174`
(history: R7 `541bd46e` → R7a `5637e6ac` → R7b `d4e258cd` → R7c `176da474`
→ R7d `943e9f9c`).

Next: H3 screen appendix entry → geocode cache → `p3_h3_analysis.py` →
H4.

### H3 COMPLETE (2026-11-02) — D-18 registered descriptive direction-check; no falsification verdict by recipe

**Run interrupted by a host restart on 2026-10-28 (150/425 geocode names
cached) and resumed 2026-11-02 from the D-18-pinned cache file
(`h3_place_geocodes_2026-10-28.csv`, sha `180bff99…`, manifest id
`h3_place_geocodes_2026-10-28`; ODbL, Nominatim viewbox-bounded
75.70,11.40,76.50,12.02). Frozen §7 §3 semantics unchanged.**

**Screen (run of record, post-filter — supersedes the preliminary 10-28
counts, which were pre-date-filter parse stats):** 2,745 parsed → 26
unparsable dates + 15 out-of-window dropped → **2,704 kept**
(2011-01-01…2014-12-24); nature crop 2,377 / cattle 267 / attack 30 /
property 19 / nil 11; species top ELP 1,557 · ELEPHANT 244 · WBR 167 ·
TGR 162; elephant-flag rows **2,018**; 367 unique places + 58 sections, 4
ranges (2014 sheet has no Place column — range tier fills it).

**Geocoding:** 425 names cached (367 place + 58 section), 99
Nominatim-matched; record-level placement **2,704/2,704** (place 1,089 ·
range 1,043 · section 572). ~1,600 records mass at 4 range centroids —
treat-with-care caveat (village-massed surface, not points).

**Surfaces:** 500 m grid, 8,112 district cells (4,423 outside WDPA);
incident KDE σ = 1,000 m; overlap = record-weighted percentile reads +
Spearman ρ (no p-values/CIs — D-18).

**Overlap (primary, all cells):** signed-positive but near-null for every
pre-2011 human-modification covariate — edge ρ +0.038 (top-decile mean
percentile 0.457), cropland +0.064 (0.509), road +0.064 (0.407), forest loss
2001–10 +0.039 (0.468), urban 2005 +0.023 (0.501); **forest cover share
−0.178 (0.405)** — the only stable directional feature across all three arms
(−0.178 primary / −0.051 outside-WDPA / −0.218 elephant subset): incident
mass sits in non-forest, human-modified land. Facilities ≤1 km null in every
arm (−0.015 / −0.058 / +0.013) — the incidental 2011–2014 register gives no
support to a tourism-attraction proximity signal. Leaky built-up gain
+0.104 (secondary, not interpreted causally).

**V2 check (paper's stated drivers):** edge concentration signed-positive
but fragile (ρ +0.038, top-decile percentile ≈ district median) — no
operationally meaningful concentration detectable from village-massed
records; consistent with the D-3 finding that the paper's edge signal rests
on simulated points we cannot reproduce.

**Outcome:** H3 is reported as a descriptive direction check under D-18 and
**carries no falsification verdict** — the registered recipe prohibits
p-values/CIs/hotspot-quartile Monte Carlo. Direction: contradicts-nothing /
near-null in magnitude; not a point hypothesis.

**Pre-outcome fixes (all before any overlap output existed; both launch
attempts crashed at the KDE stage, no facts JSON existed at the time):**
elephant mask NA (`str.contains` → `na=False`), 40-row concat index
misalignment, missing covariate realization built
(`p3_prep_lossyear.py` sha `936be90b…` → manifest `hansen_lossyear_32643`
sha `b2c788dc…`, 93,050 px / 8,374.5 ha), built-up input name corrected to
the run-of-record outcome raster. D-18 recipe parameters untouched
(σ, grid, tiers, percentile/ρ readers, pre-2011 covariate list all as
pinned).

**Hashes (H3 artifacts):** script
`7d2c4b684cef198ee78f009c2c23bb9074358e2e8174c13d876fab170fadadc7`; facts
`dd73bddb6e457f0b766dd98a20fd5567fe187e1629bc379ea64a45bacb1bcb40`
(outputs/qaqc/p3_h3_facts_2026-11-02.json); geocode cache `180bff99…`;
lossyear raster `b2c788dc…`. Manifest now **31 entries**. Log of record:
`tourism_observatory/docs/p3_h3_analysis_log.md`.

Next: H4 event table (final dispute set, sources verified) → D-19 recipe
pin + R7e re-hash **before** computing → `p4_h4_analysis.py` → log → commit
all accumulated P3 work.

### H4 pre-computation pin: D-19 logged + Freeze R7e (2026-11-02) — recipe + event table pinned BEFORE computing

**D-19 written to prereg §7 (before any H4 statistic exists), append-only; §3/§4
untouched. R7e = full-file re-hash after the D-19 append:**
`c4ac960629b01169685dd2149f0f04f323e3ab839ee266a30489208acde01f93`
(history: R7 `541bd46e` → R7a `5637e6ac` → R7b `d4e258cd` → R7c `176da474` →
R7d `943e9f9c…` → R7e `c4ac9606…`).

**D-19 pins:** event table 8 disputes / 12 records →
`data/processed/h4_event_table_2026-11-02.csv` (sha at pin
`c452c653b2077a52610e822ea67c7445da6b75c98940ed2ce259b03229aa608a`,
manifest id `h4_event_table_2026-11-02`: D-001 Muthanga AGMS agitation,
D-002 WWS relocation, D-003 Chooralmala–Mundakkai rehab protests,
D-004 Valathoor quarry, D-005 Vengappally quarry-encroachment grievance,
D-006 Jenu Kuruba Nagarahole reoccupation (**out of AOI → tabled, excluded**,
logged), D-007 KSHRC district directive (**district precision → excluded per
D-5**), D-008 Kanjirathinal sit-in; cell-eligible = **6 (< 15 ⇒
EXPLORATORY)**). Geocode cache path pinned:
`data/processed/h4_event_geocodes_2026-11-02.csv` (Nominatim D-18 recipe).
**Hotspot** = union of 500 m buffers around the 107 verified facilities ∩
(1 km hazard buffers around D-15 proxy inventory ∪ H2b(a) 2024 scar).
**Reportable area** = 500 m cells with ≥ 1 OSM building footprint (D-5).
**Precision footprints:** locality → 1,000 m (all eligible anchors are
locality); point → 100 m; subdistrict → 5,000 m; district → excluded.
**Test:** overlap = precision footprint ∩ hotspot ≠ ∅; T_obs vs
deterministic expectation E = n × A(dilate(hotspot, r) ∩ reportable) /
A(reportable); permutation B = 10,000, seed 20261102, locations uniform over
reportable-area union; p = (1 + #{T_j ≥ T_obs})/(B+1). **Falsified iff
T_obs ≤ E (§3 rule unchanged). EXPLORATORY flag + no significance language +
documentation-bias caveat (D-5).**

Next: `scripts/p4_h4_analysis.py` (implement exactly the D-19 pin) → facts +
dispute table → H4 log → PROJECTSTATE → **commit all accumulated P3 work**.

### H4 COMPLETE (2026-11-02) — EXPLORATORY (n = 6 < 15): NOT falsified on the §3 point-estimate rule; no significance language per D-5

**R7e verified byte-stable after the run** (`c4ac9606…` unchanged — no
post-pin text edit). Script implements the pin exactly: hotspot =
107-facility 500 m buffer union (63.24 km²) ∩ (D-15 inventory 1 km buffers
992.90 km² ∪ 2024 scar 1.781 km²) → **exposure hotspot 15.0578 km² = 0.74%
of district**; reportable area = 3,761 cells holding ≥1 of the 69,126 OSM
building footprints = 940.25 km² as pinned cell-union (668.49 km² within
district); anchors = Nominatim village points (all 6 matched; cache manifest
`h4_event_geocodes_2026-11-02`, ODbL, sha `4b68abc4…`); overlap = anchor ∈
dilate(hotspot, 1,000 m) ≡ pinned footprint-intersection definition (all
eligible disputes single-geocode, so no centroid ambiguity).

**Result:** **T_obs = 1/6 disputes overlap** (D-004 Valathoor quarry protest,
anchor 24 m from the hotspot boundary — solid). Deterministic expectation
E = 0.4572 (6 × 0.0762). **§3 rule: observed > expected ⇒ NOT falsified**
(point estimate). **Permutation (pinned): B = 10,000, seed 20261102 →
p = 0.3685** — a pinned read-out only: **n = 6 < 15 ⇒ EXPLORATORY, D-5's
no-significance-language rule governs all interpretation**. Margin
disclosures: D-003 Chooralmala (rehab-delay protest) misses overlap by
94 m beyond its precision radius and D-008 Kalpetta by 143 m — both
fragile to the pinned radius, reported rather than smoothed.

**Compute-record disclosure (three executions):** Run A (anchor lat/lon
*columns* written in projected metres) crashed pre-facts — superseded; Run B
introduced a coordinate-corruption bug (re-projecting projected metres as if
geographic → invalid anchors, all-False intermediate facts) — superseded and
disclosed, no decision taken on it; **Run C = run of record** (geographic
centroid, one projection), which reproduced Run A's overlap pattern
(T_obs = 1). The D-19 recipe text never changed across A/B/C; every
eligible dispute anchors at a single geocode so no convention ambiguity
exists; hence no additional re-hash was required.

**Hashes (H4 artifacts):** script
`53a7b57cf18a710f7d863cccbe3dd62dd5a246a1b16728e69e9dc7e37ec2ee2e`; facts
`d945c4a6339843ba251e515373ea1bd117573c9533fe0ad7ca3baab30cca7a37`
(outputs/qaqc/p4_h4_facts_2026-11-02.json); dispute table
`7a1996cd529e0665997adf8bbf255306f449cd59d9e0ba5d719d756178bd66f5`;
event table (pinned in D-19) `c452c653…`; geocode cache `4b68abc4…`.
Manifest now **33 entries**. Log of record:
`tourism_observatory/docs/p4_h4_analysis_log.md`. P3 hypothesis block
(H1–H4) now fully computed: H1 NOT falsified, H2a NOT falsified (stronger
after D-17 rerun), H2b registers descriptive, H3 descriptive direction
check under D-18 (no verdict by recipe), H4 NOT falsified (EXPLORATORY).

Next: **git commit all accumulated P3 work** (scripts, manifest 33, prereg
D-19/R7e, PROJECTSTATE entries, H1–H4 logs, README) → then P4–P5 (risk
register → evidence brief) → Mussoorie preplan.

### D-20 pre-computation pin: post-hoc rainfall sensitivity logged + Freeze R8 (2026-11-02) — BEFORE any rainfall statistic

**User decision (approved):** add the post-hoc rainfall sensitivity read to
H3 ("Option B" from the caveat review) plus fold rainfall into the
Mussoorie preplan pre-freeze. **D-20 written to prereg §7 (append-only,
§3/§4 untouched), full-file re-hash recorded BEFORE computing:**

**R8 = `da2baee87b9dad57cd1c9d0077242e0cbbf36233d98d842e90d291beba9d98e8`**
(history: R7 `541bd46e` → R7a `5637e6ac` → R7b `d4e258cd` → R7c `176da474` →
R7d `943e9f9c…` → R7e `c4ac9606…` → R8 `da2baee8…`).

**D-20 pins:** (a) **Read 1 — seasonality**, no new data: month-of-incident
histogram of the 2,704 kept records via the exact `screen()` code path of
record; Jun–Sep (SW monsoon) + Oct–Dec (NE monsoon) shares; all-records +
elephant subset; descriptive only. (b) **Read 2 — CHIRPS v2.0 0.05° monthly
2011–2014** (UCSB CHC, Funk et al. 2015 attribution, open-with-attribution),
bbox 75.70–76.50 E / 11.40–12.02 N; derived `rain_annual_total_mm_2011_2014`
+ `rain_monsoon_jun_sep_share`, bilinear to the H3 500 m origin-aligned
grid, joined via the **same D-18 overlap reader** on the same three arms;
covariate labels deliberately **record-window (2011–2014), contemporaneous,
NOT pre-2011** — deviation from D-18's pre-2011 primary rule documented with
reason (construct = seasonality of the incident window). (c) **Fallback:**
IMD 0.25° daily (Pai et al. 2014, imdpune.gov.in, registration) only if
CHIRPS unusable; **REJECTED as a spatial covariate** (≈27 km ⇒ ~2–4 cells,
near-flat field) — usable only as a district-mean series, which Read 1
covers without new data. (d) Script of record:
`scripts/p3_h3_rainfall_sensitivity.py` (imports the H3 module of record;
replicates the D-18 reader verbatim); facts
`outputs/qaqc/p3_h3_rainfall_sensitivity_{date}.json`. (e) **Binding
precommitment:** H3's registered conclusion (no falsification verdict,
D-3/D-18) stands unchanged regardless of outcome; no p-values/CIs/
significance language; P4–P5 may quote results only as "post-hoc
sensitivity, non-inferential" — never as H3 confirmation.

Next: fetch CHIRPS (vsicurl windowed read; fallback ordering per pin) →
manifest entries → `p3_h3_rainfall_sensitivity.py` → facts + log →
PROJECTSTATE → commit → **P4 risk register** → **P5 evidence brief**.

### D-20 COMPLETE (2026-11-02): post-hoc rainfall sensitivity executed under R8; precommitment honored; P4–P5 synthesis opened

**Execution order verified:** D-20 appended → R8 hashed → R8 recorded here
BEFORE any download/statistic → CHIRPS fetched → manifest entries (36
total) → sensitivity run → prereg re-verified byte-stable at R8 after the
run. Manifest now **36 entries** (+3 CHIRPS artifacts, sha-filled).

**Artifacts (sha256):** `data/raw/chirps_v2_monthly_2011_2014_wayanad_bbox_4326.tif`
`58fdd6a5…` (15×19 px native grid, 48 bands, 48 nodata edge-px = one
coverage-edge pixel identical across months);
`data/processed/chirps_rain_annual_2011_2014_32643.tif` `5200897d…`
(valid px range 1,126–3,609 mm, mean 2,396 on the 500 m bounding grid,
17,199 px; only 8,112 centre-in-district cells aggregate);
`data/processed/chirps_rain_monsoon_share_2011_2014_32643.tif`
`5bfacd9f…` (0.54–0.64). IMD fallback NOT triggered.

**Exact reproduction asserted:** screen 2,704 kept / 2,018 elephant;
geocode cache 425 (no network); tiers 1,089/1,043/572, 0 unplaced; grid
8,112 cells / 4,423 outside WDPA — all matching
`p3_h3_facts_2026-11-02.json`.

**Results (facts `p3_h3_rainfall_sensitivity_2026-11-02.json`, sha
`e1ab4cbe…`):** Read 1 — SW-monsoon (Jun–Sep) share **0.4183** all /
**0.4351** elephant; NE (Oct–Dec) **0.2670**/0.2488; peaks Jul **363**,
Nov **295**; no monsoon lock-in (dry quarter ≈ 0.234). Read 2 —
`rain_annual_total_mm_2011_2014` ρ = **−0.572** primary / **−0.234**
outside-WDPA / **−0.583** elephant; wettest-decile cells sit at the
**13th** incident percentile (mean pct 0.133);
`rain_monsoon_jun_sep_share` near-null/sign-fragile (−0.151 primary,
+0.078 outside-WDPA). **Reading:** incident hotspots lie in the
lower-rainfall human-modified farming belt — direction-consistent with
H3's stable negative forest-cover feature; NOT quotable as H3
confirmation (D-20(e) precommitment honored; no p-values computed).

**Log of record:** `tourism_observatory/docs/p3_d20_rainfall_sensitivity_log.md`.

### P4–P5 COMPLETE (2026-11-02): Wayanad risk register + evidence brief — Site 1 synthesis closed

**Deliverables:**
- `tourism_observatory/docs/p4_risk_register_wayanad.md` — exposure-
  evidence synthesis (NOT a probabilistic risk assessment): **R-1**
  landslide-exposure co-location (Moderate-High; H2a(ii) p_holm=0.014,
  T_obs 2.55× null mean; H2b(b) 26/107 facilities, 73,027 GOB buildings,
  1,370.1 km roads in 992.90 km² buffers); **R-2** conversion pressure in
  the remnant class (High; H1 +16.32 pp @500 m, Holm 1.7e-06, robustness
  signs agree); **R-3** 2024 scar status register (1.781 km², 0 facilities
  /0 buildings, 0.758 km `construction` road; event-population separation
  guard); **R-4** HEC adjacency (no-verdict; D-20 rainfall appendix
  labelled non-inferential); **R-5** dispute adjacency (EXPLORATORY;
  T_obs=1 vs E=0.457; margins 24/94/143 m). §2 caveat blast-radius table
  (D-15 bounded by D-17a re-render agreement; deeper probe would need a
  new §7 pin), §3 unknowns, §4 explicit trigger list. **Register
  introduces no new statistics** (only D-20 facts cited, labelled).
- `tourism_observatory/docs/p5_evidence_brief_wayanad.md` — verdict block
  (H1 High / H2a Moderate / H2b descriptive / H3 No-verdict / H4
  Exploratory), consensus statement ("hazard-adjacent development
  pressure, not tourism-causes-conflict"), H2b enumeration table, methods,
  limitations, **§6 hash-ledger provenance** (facts sha256 re-verified by
  QA pass; manifest 36), Site-2 pointer.

**QA pass:** all facts JSONs re-opened; every number in both documents
traced to the hashed facts of record; prereg still at R8.

**Site 1 (Wayanad) pipeline closed. Next: Mussoorie (Site 2) preplan —
rainfall pinned PRE-freeze per D-20 plan; mountain-road-lifeline context;
same facility/matching/grading recipe.**
