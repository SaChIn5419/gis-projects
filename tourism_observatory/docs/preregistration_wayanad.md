# Preregistration — Tourism Expansion, Ecological Risk and Community Exposure (Wayanad)

**Status: FROZEN.** This document, `tourism_observatory/docs/literature_matrix.md` and
`tourism_observatory/docs/data_audit_wayanad.md` are committed **before any outcome map is
viewed**. Their SHA-256 hashes are recorded in `docs/PROJECTSTATE.md`. Any later change to
hypotheses or rules is only permitted as an append-only **deviation log** entry (§7), never
silent edits — same discipline as `docs/limitations.md` and the Jhabua refuse-vs-guess rule.

Program scope (user, 2026-10-22): **exactly two sites — Wayanad (Kerala), then Mussoorie
(Uttarakhand). No foreign benchmark region. No third case.** Method validation relies on
Wayanad's published studies (§6 V1–V3).

---

## 1. Study area and analysis window

- **AOI:** Wayanad district, Kerala. Boundary: geoBoundaries ADM2 (same source as the
  Jhabua run; hash recorded in `data/manifest.json` at ingest).
- Baseline period (pre-treatment covariates + matching): **2000–2005** imagery
  (Landsat 5 dry-season composites).
- Outcome window: **2005 → 2025** (change detection). HEC association window follows the
  published dataset: **2011–2023**.
- Working grid: follows the Jhabua pattern — one CRS, one effective resolution
  (Landsat-native 30 m for time series; S2 10 m, Sentinel-1 20 m and DEM-derived layers
  aggregated *down to* 30 m; nothing disaggregated upward).

## 2. Treatment definition (permitted pre-freeze)

- Geocode the Kerala Tourism **approved-homestay list** (names + full addresses + approval
  order numbers + dates) and the department's accommodation registry by district; verify
  each candidate against imagery at ~10 m.
- A parcel is **treatment** if a verified tourism accommodation facility exists inside it;
  **control** otherwise. Facility *existence* may be confirmed visually pre-freeze.
- Facility **construction dating from imagery is NOT permitted pre-freeze** (it requires
  viewing change). Pre-freeze treatment-timing proxy = registry approval dates; image-based
  dating is a post-freeze sensitivity step.

## 3. Hypotheses (registered before results)

All tests two-tailed, α = 0.05; Holm correction applied *within* each hypothesis family
(not across hypotheses). A hypothesis is **falsified by its stated failure condition only.**

### H1 — Land conversion (primary)
> Vegetated/cropland→built-up conversion rate inside treatment-unit buffers **exceeds**
> matched-control buffers over 2005→2025.

- Metric: % of buffer area converted from non-built (tree/shrub/crop classes; ESA CCI +
  Landsat-derived built-up mask) to built-up. Primary radius **500 m**; sensitivity radii
  250 m and 1,000 m. Robustness: re-estimate using Hansen-built indicator and again with
  GLAD annual change — direction must agree.
- **Falsified if:** treatment ≤ control after matching (or sign flips across robustness runs).

### H2 — Hazard overlap of facility placement
> Tourism-facility footprints overlap landslide-susceptible terrain and ISRO Atlas mapped
> landslides **more than expected** under terrain-matched random placement.

- Susceptibility inputs: slope, lithology/road-cut proxies, Atlas inventory density,
  distance-to-scar (2024 Chooralmala–Mundakkai extent as published).
- Test: Monte Carlo — 1,000 placements of the same facility count, randomized within the
  district under a terrain+access feasibility constraint (fixed seed **20261022**);
  observed-vs-null exceedance p-value.
- **Falsified if:** observed overlap ≤ null expectation.

### H3 — HEC association (validation-linked; may legitimately be null)
> Human–elephant conflict incident density (2011–2023) is positively associated with
> forest-edge density and built-up growth, controlling for forest cover share, plantation/
> agriculture share, road density, elevation and seasonal rainfall. **Tourism-facility
> presence is included as a tested covariate, not presumed a driver.**

- Units: 500 m grid cells inside the AOI (outside WDPA for interpretation sensitivity).
- Model: Poisson / negative-binomial (chosen by dispersion test, decided **before**
  inspection), report IRRs with 95% CI; spatial-lag diagnostic reported, not silently
  dropped.
- **Falsified if:** edge/built-up coefficients have the opposite sign and CIs exclude
  the hypothesised direction. **Tourism coefficient null is NOT a study failure** — it is
  a genuine finding either way.

### H4 — Community-event overlap (separate category, never composited)
> Documented grievance/protest event locations overlap tourism-hazard exposure hotspots
> more than expected by area proportion.

- Inputs: structured event table (Muthanga 2001, Jenu Kuruba 2025, and others compiled
  with source URL, date, type: protest / legal proceeding / grievance — never a severity
  score).
- Test: permutation-based overlap against area-proportion expectation; **documentation-
  bias caveat stated in the brief** (more records ≠ more harm).
- **Falsified if:** overlap ≤ expectation.

## 4. Control-selection rules (frozen)

1. Units: equal-area parcels over the AOI (target ~1 km grid or nearest-equal split).
2. Treatment arm: parcel contains ≥1 verified facility. Control arm: no facility within
   **750 m** of parcel boundary.
3. Matching covariates (**pre-period / baseline only, 2000–2005**): mean slope (caliper
   ±3°), mean elevation (±100 m), baseline LULC class composition (±10 percentage points
   per dominant class), baseline Hansen tree cover (±10 pp), road-access class (OSM road
   distance tercile).
4. Exclusions from **both** arms: WDPA polygons (all_touched rule as in Jhabua), the 2024
   landslide scar zone, and water bodies.
5. 1:1 matching, no replacement, greedy on standardized distance, **fixed seed**; balance
   table with standardized mean differences required < 0.10 — if unmet, matching is
   re-specified **before any outcome is viewed**, and the re-specification is logged (§7).
6. Matching script is deterministic and reviewed; the only randomness is the seeded sort.

## 5. Information boundary — what may be opened pre-freeze vs not

| Allowed before freeze | NOT allowed before freeze |
|---|---|
| Registry download, geocoding, visual verification of facility existence | Classified change rasters (any window) |
| Baseline imagery editing (2000–2005 composites) | NDVI / vegetation-delta or built-up-delta maps |
| Terrain, lithology/road-cut, Atlas and scar layers | BACI / treatment-vs-control comparison outputs |
| HEC source documents (WII report, published paper) | HEC-overlap or exposure-register maps |
| Matching scripts + covariate tables constructed and viewed | Imagery-based construction **dating** (post-freeze step) |
| QA gate on *baseline* layers (CRS/extent/nodata) | H1–H4 test results of any kind |

Interpretation rule: "what a building is" (treatment definition) may be inspected;
"where and how much change/conflict happened" may not.

## 6. Validation plan (replaces the dropped foreign benchmark)

- **V1 — Registry consistency:** our tourism-footprint build must reproduce the district
  accommodation cohort growth in Kerala Tourism/Ecstat statistics (strong agreement =
  counts within ~10% or documented, sourced explanation for divergence).
- **V2 — HEC method:** our association analysis must reproduce the *direction* of the
  published Wayanad 1,942-incident study's stated drivers. Disagreement = method debug
  before any conclusion is written.
- **V3 — Hazard layer:** mapped 2024 landslide extents compared against published event
  inventories.
- If V2 incident-point access fails: digitize WII report hotspot maps → author contact →
  RTI; if all fail, H3 downgrades to a documented hotspot-only analysis (logged, not
  hidden).

## 7. Deviation log

Any change after freeze = new numbered entry appended at the end of this file with date,
reason, and effect on analysis; original text is never edited or removed. First log entry
number D-0 records this freeze itself.

- **D-0 (2026-10-22):** Freeze event. Hypotheses §3, control rules §4, information
  boundary §5 and validation plan §6 recorded; scope resolved to exactly two sites
  (Wayanad → Mussoorie); hashes recorded in `docs/PROJECTSTATE.md` §9.
- **D-1 (2026-10-22, administrative):** File relocation — all three frozen artifacts moved
  from `docs/` to `tourism_observatory/docs/` at user request; only internal path
  references were updated, no hypothesis/rule text changed. Hashes re-recorded.
- **D-2 (2026-10-22, C1 review):** **H2 split into H2a and H2b; original §3-H2 superseded
  (text retained above, unused).** Resolution of the scar-exclusion contradiction:
  §4 exclusions (incl. 2024 scar) apply **only to the H1 land-conversion sample frame**;
  the 2024 scar and Atlas-mapped landslides are the *outcome footprints* of H2b, a
  distinct population, never both exclusion and test target.
  **H2a — siting preference vs susceptibility.** Eligible placement domain defined
  **without any hazard inputs**: 1 km-grid points inside AOI that are (i) outside WDPA
  (all_touched) and water bodies (WorldCover 80/90 + CCI water), (ii) within 2 km of an
  OSM road class ≥ tertiary, (iii) non-built-up at baseline (CCI 2005 ≠ urban),
  (iv) elevation within the [5th,95th] percentile band of observed facility elevations.
  Null: 1,000 matched draws per facility (seed **20261022**, rejection sampling), each
  further constrained by **availability/access calipers only** — elevation ±150 m,
  road-distance ±40%. Slope, lithology/road-cut, inventory density and scar distance are
  **test metrics only, never eligibility criteria**; otherwise the null is contaminated
  by the very preference being tested. Statistics (registered, Holm within {i,ii}):
  (i) share placed on slope ≥ 25°; (ii) mean Atlas-inventory density in a 500 m KDE
  surface. Pair-level aggregation: each observed facility's percentile against its own
  1,000 matched nulls; family summary = mean percentile + exact two-sided binomial sign
  test. Interpretation guard: H2a detects *siting preference*; *exposure/risk* claims
  require H2b. No susceptibility score is ever substituted for an occurrence probability.
  **H2b — event exposure (descriptive, not a significance test):** exposure register of
  facilities, buildings (Google Open Buildings + OSM) and OSM roads within (a) published
  2024 Chooralmala–Mundakkai scar footprints and (b) 1 km buffers of Atlas digitized
  landslide points; each entry carries a footprint-source precision class; spatial
  uncertainty reported alongside counts.
- **D-3 (2026-10-22, C1 review):** **H3 hard data gate + temporal-leakage fix.**
  Ordered gate before any estimation: (1) obtain the C1 Wayanad paper full text;
  (2) read its data-availability statement; (3) if incident points are obtainable, screen
  them (date fields, coordinate precision, event definitions — attack vs property vs crop,
  missingness, division-level reporting coverage) and document the screen in the data
  audit appendix **before** choosing a model. If only hotspot maps are available: H3
  downgrades to a **descriptive hotspot-overlap analysis** (KDE percentile comparison
  between incident surfaces and covariate surfaces); **no Poisson/NB fit on rasterized
  hotspot categories; no IRR table;** this downgrade is itself a deviation-log fact, not
  a silent fallback. Temporal fix (leakage): primary model uses **pre-2011 baseline
  (2000–2010) covariates only**; incident window 2011–2023 unchanged; if year-resolved
  records are obtained, a lag-1 yearly-covariate sensitivity is permitted; **no covariate
  window may end after 2023** (the earlier 2005→2025 built-up predictor is withdrawn).
  Spatial dependence: report Moran's I on residuals + division-level cluster-robust SEs
  when incident data allow. Claims limited to what the outcome's temporal resolution
  permits.
- **D-4 (2026-10-22, C1 review):** **H1 identification + control-unit determinations.**
  Estimand restated: **association** between verified accommodation presence (timing-
  cohorted) and subsequent conversion — **the words "effect of tourism development" /
  causal language are barred from all outputs** unless a timing design supports it (none
  is currently available). Timing cohorts: facility timestamp = earliest of registry
  order date vs verifiable pre-facility baseline imagery evidence; units showing facility
  presence already in the 2005 baseline are removed from the treatment-vs-control
  comparison and reported as a **"pre-existing development" stratum** (listed, counted,
  not discarded silently). Units and geometry: matching unit = **1 km parcel** on a
  city-block grid derived from the AOI envelope anchor (same snapping convention as the
  Jhabua 30 m grid; 1 km cell = 100×100 @30 m; no approximate "nearest-equal split");
  outcome computed on the **500 m buffer around each facility point**; facilities whose
  buffers overlap *(within 250 m of centres)* form one **facility cluster = single
  treatment unit** with a union buffer, counted once. Control eligibility: the 750 m
  exclusion is measured **from the nearest facility point** (not the parcel boundary);
  edge parcels: clipped by the AOI and retained only if ≥ 50% of nominal area, with all
  drops listed in the balance report. Matching feasibility: unmatched treated units are
  **reported with their characteristics**; calipers/ratios are never altered after
  outcomes are seen. Transition reporting: H1's outcome is decomposed by source class
  (e.g., tree→built, shrub→built, crop→built) with the full transition matrix reported;
  the net vegetated/cropland→built share remains the primary endpoint. Road access
  covariate: explicitly labelled **current-OSM network proxy, not a baseline
  observation**, unless a pre-2015 OSM historical extract is obtained (then both variants
  run and their agreement documented).
- **D-5 (2026-10-22, C1 review):** **H4 event observation process.** Analysis unit =
  **dispute**, operationally the named campaign / legal case / protest series. Each
  underlying record stores: dispute ID · record type ∈ {protest, legal proceeding,
  grievance, official report} · date(s) · location label + **precision class ∈ {point,
  locality, subdistrict, district}** · source URL · corroboration status.
  **Deduplication rule:** records matching on named parties/theme are clustered to one
  dispute ID; a long-running dispute is one unit regardless of record count.
  Analysis location = centroid of records with ≥ point/locality precision; disputes
  known only at district precision are analysed at district level and **excluded from
  the cell-level spatial test** (their exclusion reasons logged). Protests and legal
  proceedings are reported **separately**; never composited with each other or with HEC
  data. **Spatial null:** permutation of dispute locations restricted to *reportable
  area* = cells with baseline settlement footprint (OSM/Settlement layer), acknowledging
  reporting feasibility; precision classes propagate as footprint buffers, not points.
  If the dispute table has < 15 units, H4 is flagged **EXPLORATORY** and no significance
  language appears in outputs. Wording fixed in all deliverables: "spatial distribution
  of documented records" — never "community suffering" or causal proof.
- **D-6 (2026-10-22, C1 review):** **Data-audit verdict downgraded from PASS to
  CONDITIONAL GO (P1 baseline-only).** Public availability ≠ downloaded file: every
  source keeps its `to-download/digitize/obtain` status until **the file is on disk with
  a SHA-256 hash recorded in `data/manifest.json`**; only then does the status flip to
  verified. The original v1 "PASS 6/6" line in the audit is superseded by this entry
  (v2 label shown in the audit). P1 authorized scope: downloads + documentation, baseline
  terrain/accessibility covariates, facility-existence verification, geocoding and
  raster-alignment tests, data-completeness and source-provenance reports — **no H1–H4
  outcome maps, no treatment-vs-control tests.**
- **D-7 (2026-10-22, C1 review):** **Validation criteria tightened.** V1 (registry
  consistency) requires, *before* computing agreement: a **category-alignment table**
  (approved-homestay list vs classified hotels vs total units vs survey cohorts — years
  and geographic units stated); agreement is assessed only on comparable cohort-year rows
  after alignment; target = direction match + |share difference| ≤ 10 pp at district-year
  level; failing alignment, V1 is reclassified a "consistency check", not validation, and
  the divergence source is documented. V2 (HEC) requires comparable outcome definition,
  spatial unit and time window to act as a replication benchmark; without them the
  published study is a **methodological reference only**, and success = directional
  agreement on named drivers with comparability limits stated. V3 (landslide) validates
  **scar mapping only**; it does not validate any district-wide susceptibility model,
  and output wording will not claim otherwise.
- **D-8 (2026-10-22, C1 review — NORMAL):** **Literature verification ledger.** The
  literature matrix gains an appended **source-type ledger** (peer-reviewed / official
  inventory / institutional report / news / NGO / grey) and an independence flag (no
  treating two sources as independent confirmation if they derive from the same
  underlying report). Verification tasks: open the C1 Wayanad paper and check its data
  statement; verify the exact methods/validation numbers of the Mussoorie susceptibility
  study (B1) before reuse in Investigation 2; verify remaining `verify`-flagged DOIs.
  These tasks are part of P1 documentation, not outcome analysis.
- **D-9 (2026-10-22, cross-file consistency audit — administrative only).** The
  pre-sign-off consistency pass found three colliding ID spaces and several v1 remnants.
  Nothing in this entry touches hypotheses, matching/analysis rules, or verdicts.
  (a) **Binding ID convention for all future files:** literature-matrix row IDs are
  written `lit-Cx` / `lit-Mx`; data-audit source rows `audit-D-1…D-21`; deviation entries
  in this log `dev-D-x`; the sign-off checkpoint always `checkpoint-C1`. The HEC
  benchmark paper is `lit-C1` and is unrelated to checkpoint-C1.
  (b) Authorized administrative edits, applied under this entry with original wording
  preserved in `tourism_observatory/docs/c1_consistency_audit.md`: matrix §D row IDs
  renamed `D1–D4` → `M1–M4` (and the §E table row updated) to end the collision with
  audit source IDs; author-string typo in M1 ("Topuz & Với" → "M. Topuz et al.",
  citation stays in the verify queue); audit §8 closing line annotated **superseded** by
  verdict v2 (text retained); audit §9 header typo ("supersêdes" → "supersedes");
  audit §10 ledger corrected (dev-D-19 was double-assigned; audit-D-9 reclassified
  institutional, not "peer-reviewed+official"; previously untyped rows assigned; taxonomy
  gains `open satellite/raster`); README structure-tree verdict line updated from stale
  "checklist PASS 6/6" to verdict v2 CONDITIONAL GO.
  (c) `config/wayanad.yaml` open items recorded — not blockers, P1 ingest tasks: pin the
  geoBoundaries snapshot version; replace the CCI 2005 placeholder layer ID with the
  exact vintage at ingest; confirm UTM zone 43N vs 44N from the district extent.
- **D-10 (2026-10-23, checkpoint-C1 final sign-off — record entry; administrative only).**
  The reviewer completed the final cross-check of the corrected artifacts and granted
  **final sign-off for checkpoint-C1** (explicit confirmation: "c1 sign off yes").
  Both conditions listed in `c1_consistency_audit.md` §6 are now met and logged, never
  silent: (1) reviewer cross-check — performed, sign-off given 2026-10-23; (2) P1
  empirical verifications — files + SHA-256 for **17 sources** in `data/manifest.json`;
  baseline QA gate **PASS (0 critical, 0 warnings, 62 checks, files opened directly)**
  in `outputs/qaqc/baseline_qaqc_report.md`; audit-D-10 R1 data-availability gate
  executed (READY village/aggregate level via open Figshare dataset; points do not exist
  at source — registered fallback stands); audit-D-1 coverage start year verified
  (orders 2024-01-27 → 2026-07-03, snapshot semantics) — all rows in data-audit §11 and
  `docs/p1_provenance_report.md`. This entry changes nothing in §3 hypotheses, §4
  controls, §6 validation, or the §5 information boundary; it records that the C1
  condition on P2 is released and that C2 (P1 data-completeness go/no-go) may now decide.
  Acquisition-path and QA-rule incidents observed during P1 (GEE → direct tile downloads;
  CCI legend sub-codes; WDPA geodatabase format + overlapping-designation union rule;
  Hansen north-edge tile naming; boundary-fringe DEM diagnosis; geocoding rounds 1→2) are
  logged in data-audit §11 — none alters a registered design element.
- **D-11 (2026-10-23, P2 pre-outcome implementation spec — administrative only).**
  Operationalizes frozen §2/§4 into executable code **before any outcome is viewed**;
  changes no hypothesis, covariate list, exclusion, caliper, seed, or the §5 boundary.
  (a) **Facility universe = both §2 lists.** The treatment source is the union of the
  M5 approved-homestay list (51) and the D-2 classified portal (97 unique properties
  after de-duplicating the portal's internal repeats; 5 excluded as non-accommodation
  Tour-Operator/Restaurant/Ayurveda), with 20 cross-list name matches → **123 facilities**,
  all in-district. Coordinate preference (highest available): portal JSON-LD GeoCoordinates
  pin (81) → M5 round-2 geocode (31) → fresh PIN-first ladder (11); **no jitter applied**.
  (b) **Existence verification (§2).** "Verified" = a visible built structure within
  **100 m** of the mapped point on a Sentinel-2 10 m quicklook; 107/123 verified
  (66 at-point ≤50 m, 41 within 100 m). Precision classes cap claims and are retained
  per facility (P1…P5); P5 points that resolve to a settlement within 100 m stay verified
  but flagged coarse, and imagery construction-dating remains a post-freeze step (§5).
  (c) **Arms (§4.2).** Treatment = parcel containing ≥1 verified facility on an eligible
  parcel (54 parcels). Control = eligible parcel >750 m from **any** candidate facility
  point (886 parcels), the conservative literal reading of §4.2. (d) **Eligibility (§4.4).**
  A parcel joins both arms only if ≥50 % of its pixels are eligible (AOI∖water∖WDPA∖scar);
  covariates computed on eligible pixels. (e) **Matching (§4.5).** Greedy 1:1, no
  replacement, standardized Euclidean distance, fixed seed 20261022, exact road-tercile
  match + §4.3 calipers; **SMD < 0.10** gate. The matcher **refuses to run** until the
  2024 scar layer exists and covariates are rebuilt with `scar_excluded=true`. No outcome
  raster was read to produce any of the above (§5); a smoke test with a scratch scar was
  run-and-deleted (not an analysis). If the SMD gate fails on the real build, the
  re-specification is logged here **before** any outcome is viewed (§4.5).

- **D-12 (2026-10-26, pre-outcome implementation correction — administrative only):**
  **Scar geometry v1 superseded by v2.** v1 (centerline digitized by eye from
  PMC12290006 Fig. 1, compiled by `p2_compile_scar_d6.py`) was QA-checked against the
  NRSC/ISRO **VAP3** landslide impact map (Charter Call 1029, AOI 01, observed
  31/07/2024; UTM 43N, 1:12,500) and found displaced: v1 sat ~2 km NORTH of the
  published crown and its overlap with the published debris-flow extent was
  **0.000 km²**. v1 was discarded **before any matching was run on it** (the §4.4
  matcher gate had barred the real run; the smoke test used a scratch scar, not v1).
  v2 source and method: the VAP3 legend gives the crown exactly —
  **76°8′10.58″E, 11°28′0.347″N** — and `scripts/p2_digitize_vap3_scar.py`
  (i) renders the sheet at 200 dpi, (ii) georeferences the main panel from the
  in-map graticule (1′ latitude ticks + green-dot longitude anchor; fit residual
  <1 px, green-dot latitude error **15.2 m** vs the legend), (iii) extracts the
  published yellow Debris Flow outline by RGB threshold, (iv) removes inset-box
  borders (deletion of long axis-aligned runs; flow rails are diagonal), (v) bridges
  gaps, skeletonizes, and takes the **crown→NE-tip** path (a graph-diameter path was
  tried and rejected: it terminated on inset-box border spurs and missed the crown),
  (vi) buffers the centerline by **150 m** (unchanged §4.4 half-width). Result:
  centerline **7,221 m** (NRSC publishes "approximately 8 km"), corridor
  **1.781 km²**, crown inside the corridor. A minor overshoot NE of Chooralmala is
  in the conservative direction for an exclusion (over-excludes, never leaves scar
  pixels inside a parcel). QA: `outputs/qaqc/p2_scar_digitization_qa.json` +
  `p2_scar_digitization_overlay.png`. Downstream re-run under the same frozen rules:
  covariates rebuilt (`scar_excluded=true`, 1,163 usable parcels — unchanged), arm
  counts unchanged (54 treatment / 886 control: the corridor runs through
  uninhabited terrain), and the **real** match executed → 50/54 pairs,
  max|SMD| = 0.067 → §4.5 gate PASS. Changes no hypothesis, covariate, exclusion
  rule, caliper, or seed; no outcome was viewed (§5).

## 8. Pre-analysis inspection checklist (gate before P2)

Before outcome work starts, confirm: ☐ hypotheses §3 unchanged ☐ controls §4 unchanged ☐
match executed, balance table reported ☐ deviation log empty or justified ☐ scope items
resolved (2 sites only) ☐ commit hash recorded in PROJECTSTATE.

### §8 verification (2026-10-26) — completed; freeze R6 recorded

- ☑ **Hypotheses §3 unchanged.** Verified mechanically: the prereg diff from the R5
  state (commit `893ad83`) to the verification commit contains **55 added lines, 0
  deletions**, all inside §7 (entries D-11, D-12). §3 is therefore byte-identical
  to its R5-frozen text.
- ☑ **Controls §4 unchanged.** Same mechanical verification (0 deletions repo-wide on
  this file; §4 untouched since R5). Covariate list, calipers, exclusion rule, 750 m
  control buffer, seed 20261022, and the SMD < 0.10 gate are as frozen.
- ☑ **Match executed, balance table reported.** Real scar-excluded build (no
  override): 54 treatment / 886 control, **50/54 pairs**, max|SMD| = **0.0667** →
  gate **PASS**; 4 treated unmatched on calipers. Balance table:
  `outputs/qaqc/p2_match_balance_2026-10-26.json`; pairs:
  `data/processed/matched_pairs_2026-10-26.csv`; narrative: `docs/p2_matching_log.md`.
- ☑ **Deviation log justified.** §7 carries D-1…D-12; the P2 entries (D-11
  implementation spec, D-12 scar v1→v2 correction) are pre-outcome implementation
  details — none changes a hypothesis, covariate, exclusion, caliper, or seed, and
  no outcome raster was read to produce any P2 output (§5 boundary held; the D-12
  correction was made and validated against a *source map*, not an outcome layer).
- ☑ **Scope items resolved (2 sites only).** Program scope remains exactly Wayanad
  then Mussoorie (§1, resolved 2026-10-22). All P2 artifacts are Wayanad-only;
  no third site was introduced.
- ☑ **Commit hash recorded in PROJECTSTATE.** Verification commit + R6 freeze hashes
  recorded in `docs/PROJECTSTATE.md` §9.

Consequence: the design is frozen at **R6**. P3 outcome work (H1–H4 computation)
may begin under §5 rules; any post-R6 change to the frozen trio requires a new §7
entry and an R7 re-hash before outcomes are examined under the changed rule.
