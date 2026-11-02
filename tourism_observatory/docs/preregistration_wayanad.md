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

- **D-13 (2026-10-26, P3 pre-comparison implementation spec — administrative only):**
  **H1 endpoint vintage fixed to the latest available free built-up epochs.** The
  frozen H1 window reads "2005→2025"; no free global Landsat-derived built-up product
  extends to 2025 (ESA WorldCover's final release is 2021; the GLAD GLCLUC2020 series
  ends 2020; GHSL's JRC server was unreachable from this host at acquisition time).
  Operationalisation, decided **before any treatment/control outcome comparison was
  computed** (this entry is logged first; the ingest script only counts AOI-wide
  pixels): **primary = GLAD GLCLUC2020 Built-up change 2000→2020** (Potapov et al.
  2022, *Frontiers in Remote Sensing*; 30 m Landsat ARD; CC-BY; built class = any
  Landsat pixel containing a man-made surface), **sensitivity = ESA WorldCover 2021
  strict built-up (class 50, 10 m)**, **robustness = Hansen GFC-2024 v1.12 loss-year
  2000→2024** (tree-cover loss as a clearing proxy, as §3 H1 requires a Hansen-built
  run). Every output reports the actual period (2000→2020 primary) rather than the
  nominal 2005→2025. Recorded definitional caveat (consistent with the metric text
  "ESA CCI + Landsat-derived built-up mask"): GLAD's built class covers **12.2%** of
  the district vs **0.8%** for WorldCover strict-built — a definitional gap, not an
  error (GLAD counts roads and scattered houses; Kerala's dispersed settlement
  inflates it; 97.8% of WorldCover built pixels fall inside the GLAD mask;
  expansion ⊆ 2020 built extent, 0 violations). Per §3 H1 the **direction of the
  treatment/control contrast must agree across both** runs or H1 is falsified by its
  stated failure condition. Epoch mismatch vs the 2005 baseline: the outcome window
  starts at the baseline's Landsat epoch (2000) instead of the CCI 2005 class year;
  the 2000→2005 lead is ≤5 yr and applies identically to treatment and control
  buffers (matched pairs, same county), so it cannot favour one arm. Measurement
  unit unchanged: facility-cluster union buffers at 500 m (sensitivities 250/1000 m),
  full transition matrix by CCI 2005 source class, per D-4. Changes no hypothesis,
  covariate, exclusion rule, caliper, or seed.

- **D-14 (2026-10-26, P3 H1 measurement spec — administrative only, logged before
  any treatment/control comparison):** D-4 froze the treatment-side geometry (500 m
  buffer per facility point; centres within 250 m → one cluster with union buffer,
  counted once) but left the **control-side buffer geometry, the metric denominators,
  and the test battery** un-pinned. Fixed as follows, before any arm difference was
  computed: **(i) Units.** Matching was parcel-level (50 pairs); H1 operates on
  those pairs. Per pair, the treated parcel's facilities are grouped into clusters
  by single-linkage on centre distance ≤ **250 m** (the frozen merge rule, read
  literally as radius-independent); the treatment geometry is the **pixel union of
  the per-radius buffers** (500 m primary; 250/1000 m sensitivities) around all
  facility points in the parcel, so overlapping buffers are counted once. The
  control geometry is a **buffer of the same radius around the centroid of the
  matched control parcel** (the only symmetric fixed-size footprint available on
  the control side — controls have no facility point by construction). **(ii)
  Metric.** On the frozen 30 m grid, restricted to the same eligibility mask used
  for matching (AOI ∩ ¬WorldCover-water ∩ ¬WDPA-all_touched ∩ ¬scar-v2), applied
  identically inside every buffer: numerator = expansion pixels (GLAD class 1)
  whose CCI-2005 class is vegetated/cropland (code families: cropland 10–12,
  mosaic 20–30, shrubland 40–50, forest 60–75, grass/sparse 100–180 — i.e.
  everything except urban 190 and water 210); denominator = buffer pixels that
  were non-built at baseline (GLAD 2000: classes 0/1) with the same CCI class
  restriction. Rate = numerator/denominator in %. The full transition matrix
  (CCI-2005 family × built-status 2000/2020, pixel counts) is reported per arm
  per D-4. **(iii) Tests.** Paired differences d_i = treatment − control rate,
  n = 50 pairs; both a two-sided **paired t-test** and a **Wilcoxon signed-rank
  test** are reported; Holm correction across the three radius tests within H1.
  **(iv) Robustness (§3 direction-agreement clause).** Re-estimate at 500 m with
  (a) WorldCover-2021 strict built (numerator: WC class-50 pixels that GLAD flags
  as non-built at 2000; same denominator) and (b) Hansen loss-year 2001–2024 as a
  clearing proxy (numerator: loss pixels; denominator: baseline pixels with Hansen
  2000 tree cover > 0); H1 is falsified if the sign of the mean paired difference
  disagrees with the primary run. **(v) Stratum.** D-4's "pre-existing development"
  stratum: all 51 registry order dates are 2023–2026 → **zero facilities pre-date
  the baseline by the registry-date proxy**; imagery-based construction dating (the
  optional post-freeze sensitivity) was **not run** and the stratum is reported
  empty, with this limitation labelled. Changes no hypothesis, covariate, exclusion
  rule, caliper, or seed; the control-side geometry is a measurement-choice
  (which pixels are counted), not a design change (which parcels are compared).
- **D-15 (2026-10-28, H2 inventory input substitution — logged before any H2
  statistic was computed):** H2a(ii) ("mean Atlas-inventory density in a 500 m
  KDE surface") and H2b(b) ("1 km buffers of Atlas digitized landslide points")
  require the ISRO Landslide Atlas **vector** inventory. It is not obtainable in
  any public form. Evidence trail: (a) Atlas distributed as PDF only (data-audit
  D-5, 2026-10-22); (b) Bhuvan WFS endpoint disabled (2026-10-23); (c)
  GetFeatureInfo returns empty GML (0 features) at every probe on
  `disaster:KERALA_MERGE_gcs`, *including* coordinates where GetMap visibly
  renders polygons (2026-10-28) — attribute/date harvest is impossible;
  (d) GetCapabilities carries empty `<Abstract/>` for all six candidate Kerala
  layers. Renders had first appeared byte-identical across the six layer names;
  that finding was **retracted** the same day — it was caused by using WMS 1.3.0
  with `CRS=EPSG:4326` (lat,lon axis order) while sending a lon,lat BBOX, so the
  server fell back to a default view. With the corrected protocol (WMS 1.1.1 +
  `SRS=EPSG:4326`, lon,lat BBOX) the six layers do differ:
  `disaster:kl_landslides_new` (style "Kerala Landslide") carries the most
  Wayanad content (40,034 inventory px at 55 m, vs 23,545 / 18,115 / 105 / 0 /
  0 / 0 for the others). **Substitution (user decision 2026-10-28, taken before
  any H2 statistic):** both statistics use a polygonized render proxy — 81
  overlapping 10 m GetMap tiles over 75.75–76.47 E / 11.20–11.82 N, brown-fill
  mask unioned across 50 %-overlap tiles (this removes the per-tile "bhuvan"
  watermark, which is fixed at tile centre and never brown), polygonized to
  `data/processed/inventory_wms_kl_landslides_new_32643.gpkg` (1,151 polygons,
  29.82 km²; fetch script `scripts/h2_fetch_wms_inventory.py`; QA facts
  `outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json`). **Registered test
  family unchanged: H2a Holm within {i,ii}; H2b stays descriptive (a)+(b)** —
  only the *input data* of (ii) and (b) is substituted, so the family is not
  reduced and no outcome-dependent selection is possible. **Measurement recipe
  pinned here, before computation:** H2a(ii) — rasterize the proxy polygons on
  the frozen 30 m analysis grid (cell value = inventory area fraction), Gaussian
  kernel σ = 500 m (16.667 cells) with 3σ truncation and mass normalisation,
  sample the surface at each observed facility and each of its 1,000 matched
  nulls; per-facility percentile against its own nulls; family summary = mean
  percentile + exact two-sided binomial sign test (aggregation as frozen in
  D-2). H2b(b) — buffers of **1 km around the proxy polygons** replacing
  "Atlas digitized landslide points"; register facilities, buildings and roads
  intersecting the union; every entry carries precision class
  `WMS-render polygonized (10 m px, ±1 px boundary; no attributes/vintage)`.
  **Validity caveats, carried forward:** (1) feature attributes and dates are
  unretrievable — selection criteria and vintage of the layer are
  undocumented; (2) the Jul-2024 Chooralmala–Mundakkai event is absent from
  **all six** candidate layers (≤0.5 % of the digitized VAP8 scar covered) — the
  proxy predates or excludes it; (3) georeferencing validated three ways:
  BBOX honoured (disjoint renders yield disjoint content), all 1,151 polygons
  fall inside the district boundary, 7 proxy polygons lie within 500 m of the
  VAP8 scar (2 intersecting); (4) documentation bias presumed (mapped-landslide
  density near roads/settlements), reported with H4-style caveats. Changes no
  hypothesis, covariate, exclusion rule, caliper, or seed; §3 H2 text is
  byte-unchanged — this entry records an input-data fact under the R6 rule.
  **Pinned clarifications (appended 2026-10-28, still before any H2 statistic
  was computed):** (a) *Road-distance* = Euclidean distance in metres to the
  nearest OSM highway feature of class ≥ tertiary (motorway/trunk/primary/
  secondary/tertiary and their `_link` variants), computed on the frozen 30 m
  grid from `roads_wayanad_32643.gpkg`; it is used both for eligibility (ii)
  (`≤ 2,000 m`) and the ±40 % caliper (`[0.6·d_fac, 1.4·d_fac]`) — the coherent
  reading, since ≥tertiary is D-2's only road criterion. (b) *Observed-facility
  population* = the 107 verified facility points inside the district (the same
  set H1 used). (c) *Null-draw algorithm*: eligible domain = 1 km parcel-grid
  cell centres passing (i)–(iv), evaluated on the frozen 30 m grid (AOI and
  WDPA sampled at the cell centre; CCI-2005 ≠ 190; WorldCover ∉ {80, 90} and
  CCI ≠ 210; elevation inside the [5th, 95th] percentile band of the 107
  facility elevations); one `numpy.random.default_rng(20261022)` stream
  consumed sequentially over facilities sorted by `facility_id`; candidates
  drawn uniformly from the domain with replacement, accepted only when both
  calipers pass, until 1,000 accepted per facility (literal rejection
  sampling; draws are with replacement). (d) *Percentile/sign convention*:
  `percentile_i = (#{null < obs_i} + 0.5·#{null = obs_i}) / 1000` (mid-rank,
  so the binary slope metric stays coherent); `sign_i = +1` if
  `percentile_i > 0.5`, `−1` if `< 0.5`, exact `0.5` = tie and excluded from
  the two-sided exact binomial sign test; family summary = mean percentile +
  sign test over non-tied signs; Holm adjusts the two sign-test p-values
  across {i, ii}.
- **D-16 (2026-10-28, defect found in the D-15(d) sign-test convention —
  disclosed post-computation, correction registered before it is computed):**
  The first H2a computation ran with the D-15(d) convention and produced
  (i) signs +1/−35, p_holm = 2.15e-09 and (ii) signs +36/−71, p_holm = 9.2e-04.
  Analysis of the convention's own null (an analytical derivation, valid in
  either direction and independent of the observed results) shows **both
  sign-test p-values are artifacts of point masses**, not evidence:
  under exchangeability of the observed point with its null draws, a metric
  with a point mass gives P(sign +) ≠ 0.5. For (i), metric binary with
  per-facility null probability q: among non-ties P(+) = q ≈ 0.003 — the
  observed +1 sign is exactly the null expectation (~0.35 expected), so the
  35 negative signs are what H0 predicts, not evidence against it. For (ii),
  metric zero-inflated with pool zero-fraction π₀: H0 gives
  P(+) = 1−π₀ ≈ 0.34 and P(−) = π₀ ≈ 0.66 — the observed +36/−71 split
  (0.34/0.66 of 107) is again precisely the null expectation. The midrank
  *mean* percentile is unaffected (E = 0.5 under H0 by the same algebra), so
  it stays reportable. **Timing disclosure:** this defect was discovered on
  inspecting the first computation's output incoherence (mean 0.503 vs signs
  −35/+1); the derivation shows it was baked into the convention regardless
  of any outcome, and no result direction was used to choose the correction.
  **Corrected family inference (registered here, before computation), which
  is the test form already frozen in §3 H2 itself — "Monte Carlo, 1,000
  placements, observed-vs-null exceedance p-value":** for each statistic,
  T_obs = the statistic evaluated at the 107 observed facilities
  (i: count of facilities on slope ≥ 25°; ii: mean of the 107 observed KDE
  values); T_j = the same statistic evaluated at the j-th matched null draw
  of every facility (j = 1…1,000, the same deterministic seeded draws
  already generated); one-sided exceedance
  p = (1 + #{T_j ≥ T_obs}) / 1001; Holm across {i, ii} as frozen. Both the
  registered outputs (retained verbatim in `p3_h2a_facts_2026-10-28.json`)
  and these corrected tests are reported side by side; the corrected p-values
  carry the H2a verdict, with the registered sign tests explicitly labelled
  non-interpretable in the analysis log. Changes no hypothesis, covariate,
  exclusion rule, caliper, seed, or draw; only the aggregation test that the
  point-mass defect invalidated.
- **D-17 (2026-10-28, coverage-window error found by extent audit — logged
  before the corrected inputs were fetched and before any H2b count):**
  The district reference used throughout the project (geoBoundaries ADM2
  Wayanad = AOI = `aoi_mask`/parcels/roads) spans **75.7742–76.4443 E /
  11.4515–11.9781 N**. A systematic extent audit (dataset bounds vs district
  bounds, run while preparing H2b) found two extraction windows truncated the
  district against its north edge: **(a)** the D-15 inventory fetch window
  `75.75–76.47 E / 11.20–11.82 N` omits lat 11.82–11.978 — the northern
  district strip where **16 of the 107 verified facilities** lie; **(b)** the
  P1-era OSM buildings window `75.73–76.40 E / 11.20–11.80 N` omits the same
  north strip plus the east strip 76.40–76.444 E (76,206 buildings, manifest
  entry). Roads, parcels, AOI rasters and all analysis grids were confirmed
  district-complete; only these two windows were wrong (rough bbox estimates
  instead of the district polygon). **Timing disclosure:** discovered after the
  first H2a computation and before any H2b count, by an objective bounds
  comparison — no outcome value entered the discovery, and no statistic was
  inspected to choose the correction. **Correction:** (a) re-fetch the WMS
  inventory over `75.75–76.47 E / 11.42–12.00 N` (district + ≥0.02° pad on
  every side), same layer/protocol/10 m/50 %-overlap recipe otherwise, then
  **recompute H2a under the corrected inventory** — the first H2a outputs are
  superseded (retained verbatim in git/PROJECTSTATE history and the D-16
  registration unchanged); (b) re-extract OSM buildings from the same source
  PBF (`southern-zone-261020.osm.pbf`, unchanged hash) over
  `75.73–76.47 E / 11.42–12.00 N`, clipped to the district window. Manifest
  entries updated in place (same ids, new sha256 + note), D-15's pinned
  window string superseded here. Test family, calipers, seed, KDE recipe and
  D-16 corrected-test registration all unchanged; this is an input-coverage
  fix, not a design change.
- **D-18 (2026-10-28, H3 descriptive-fallback recipe pinned before
  computation):** the R1 gate (audit-D-10, logged 2026-10-23, pre-freeze)
  established that the Morrison et al. (2025, GECCO 62:e03742) HEC records
  **never contained GPS coordinates** (village-name level; the paper
  simulated points by conditional random sampling), so the D-3 downgrade to a
  **descriptive hotspot-overlap analysis** is active (no Poisson/NB, no IRR
  table, no residual Moran's I — nothing to fit residuals to). Measurement
  recipe pinned here, before any H3 statistic: (1) records = Figshare
  `Original_records…xlsx` (2011–2014 sheets; screen: parse dates, keep
  2011–2014 window, normalize nature/species/range text, drop and count
  unparseable/out-of-window rows, report species mix; elephant-involved
  subset reported alongside the full set); (2) incident locations =
  place-name geocoding (373 unique places; Nominatim restricted to the
  district viewbox, 1 req/s, cached to `data/processed/
  h3_place_geocodes_2026-10-28.csv` with per-name precision tier
  place→section→range-centroid fallback; unmatched names excluded and
  counted); (3) incident surface = Gaussian KDE over geocoded points,
  weight = incident count, **σ = 1,000 m** (village-level positional
  precision and the paper's 1 km predictor resolution), evaluated on the
  H3 500 m grid inside the AOI (outside-WDPA sensitivity reported);
  (4) covariate surfaces, all sampled per 500 m cell and rank-percentiled
  within the district: forest-edge density and forest-cover share from
  Hansen 2000 tree cover (≥30 %), cropland share and urban share from CCI
  2005 ({10,11,12,20,30} and {190}), 2000–2010 Hansen loss share (pre-2011
  disturbance), road density from OSM (2026 snapshot, vintage-caveated),
  DEM elevation, facility count within 1 km (tourism, tested covariate);
  GLAD 2000–2020 built-up gain reported **only as a labelled-leaky
  secondary** (window ends 2020 < 2023 but is not pre-2011); seasonal
  rainfall has no raster in the data audit → documented as unavailable;
  (5) overlap statistic = mean/median covariate percentile at the incident
  surface's top-decile cells + Spearman rank rho between the two percentile
  surfaces (descriptive effect sizes, **no p-values, no CIs, no
  coefficient claims**); (6) V2 direction check against the paper's stated
  drivers (near-sanctuary/forest-edge concentration) reported as
  agreement/disagreement, never as a re-test. No hypothesis, exclusion rule
  or claim text changes; the family stays the D-3-registered descriptive
  fallback.

- **D-19 (2026-11-02, H4 measurement recipe + event table pinned before
  computation):** H4 ("documented grievance/protest event locations overlap
  tourism-hazard exposure hotspots more than expected by area proportion")
  is computed under the D-5 event-observation process; this entry pins the
  remaining operational choices **before any H4 statistic is computed**.
  §3-H4 text byte-unchanged (falsification rule stays: *falsified iff
  observed overlap ≤ area-proportion expectation*).
  (a) **Event table:** 8 disputes / 12 records compiled from open web
  sources, unit = dispute per D-5, written to
  `data/processed/h4_event_table_2026-11-02.csv` (sha256 at pin time
  `c452c653b2077a52610e822ea67c7445da6b75c98940ed2ce259b03229aa608a`;
  manifest id `h4_event_table_2026-11-02`). Set: **D-001** Muthanga AGMS
  land-rights agitation (Tvm march record tabled and excluded as out-of-AOI;
  territorial anchor Muthanga, records 2001–2026); **D-002** Wayanad
  Wildlife Sanctuary relocation dispute (Valavayal, ongoing since 2002;
  LCW); **D-003** Chooralmala–Mundakkai rehabilitation-delay protests
  (23 Feb 2025 onward); **D-004** Valathoor quarry protest (13 Sep 2024);
  **D-005** Vengappally quarry-encroachment grievance (28 Aug 2025);
  **D-006** Jenu Kuruba Nagarahole reoccupation (5 May 2025 — Kodagu
  district, Karnataka, **out of AOI: tabled per prereg naming and excluded
  from the cell-level test, reason logged**; no Wayanad-specific Jenu
  Kuruba 2025 event exists); **D-007** KSHRC quarrying directive
  (17 Jan 2025 — district precision, excluded per D-5); **D-008**
  Kanjirathinal family land-recovery struggle (Kalpetta sit-in; the 2023
  KSHRC directive record is district precision and excluded at record
  level, dispute stays cell-eligible through its sit-in record).
  **Cell-eligible disputes: 6 (< 15 ⇒ EXPLORATORY).**
  (b) **Geocoding:** same Nominatim recipe as D-18 (viewbox
  75.70,11.40,76.50,12.02, suffix ", Wayanad, Kerala, India", 1 req/s);
  cache `data/processed/h4_event_geocodes_2026-11-02.csv` (path pinned
  verbatim here; manifest entry at compute time).
  (c) **Hotspot ("tourism-hazard exposure hotspots") definition:** union of
  **500 m buffers around the 107 verified facilities** (H1 primary radius)
  **intersect** (union of **1 km buffers** around the D-15 inventory-proxy
  polygons **union** the H2b(a) 2024 scar footprint), clipped to the
  district — area where verified tourism presence co-occurs with mapped
  hazard footprints.
  (d) **Reportable area (D-5 null):** 500 m cells containing ≥ 1 OSM
  building footprint (the 2026-10-28 69,126-footprint extract); D-5's
  "cells with baseline settlement footprint" operationalized with the OSM
  layer named there.
  (e) **Precision footprints** (D-5: precision classes propagate as
  footprint buffers, never points): point → 100 m; **locality → 1,000 m**;
  subdistrict → 5,000 m; district → excluded from the cell-level test. All
  cell-eligible dispute anchors are class **locality**.
  (f) **Cell-level test:** a dispute is cell-eligible iff it has > 0 in-AOI
  records at ≥ locality precision; analysis location = centroid of those
  records' footprints (single-record disputes = the geocoded point). A
  dispute **overlaps iff its precision footprint intersects the hotspot
  footprint**. Observed statistic **T_obs** = number of cell-eligible
  disputes overlapping; **deterministic area-proportion expectation**
  E = n × A(dilate(hotspot, r_precision) ∩ reportable)/A(reportable) per
  dispute's own radius. **Permutation null:** B = **10,000**; anchored RNG
  seed **20261102** (numpy default_rng, pinned at pin time); each draw
  samples the dispute's location uniformly over the reportable-area union
  (uniform over equal-area reportable cells, uniform within cell — D-5:
  "permutation of dispute locations restricted to reportable area"),
  applies that dispute's own precision radius, and counts overlaps T_j;
  one-sided **p = (1 + #{T_j ≥ T_obs})/(B+1)**.
  (g) **Reporting:** reportable-area stats, hotspot area + share,
  per-dispute table (incl. exclusions with reasons), T_obs, E, p;
  **EXPLORATORY flag on every output; no significance language (D-5)**;
  wording restricted to "the spatial distribution of documented records";
  documentation-bias caveat mandatory (disputes documented by press/LCW —
  reporting likelihood rises with media attention and salience, e.g. near
  the 2024 landslide scene, not uniformly with exposure).

- **D-20 (2026-11-02, post-hoc rainfall sensitivity pinned before ANY
  rainfall statistic is computed):** H3's outcomes were computed and seen
  on 2026-11-02 under D-18 with "rainfall unavailable" documented in that
  pin. This entry - an explicit user decision - adds a rainfall
  sensitivity read. Because the H3 overlap table already exists and was
  examined, **every rainfall output below is labelled POST-HOC SENSITIVITY
  and is an appendix read, not part of the registered H3 family or test
  family**. §3/§4 byte-unchanged; D-18's recipe and all its printed
  results are untouched.
  (a) **Read 1 - seasonality (no new data):** month-of-incident histogram
  of the 2,704 kept 2011-2014 records (exact `screen()` code path of
  record, deterministic), reporting the Jun-Sep (SW monsoon) and Oct-Dec
  (NE monsoon) shares, all-records and elephant-subset; descriptive only,
  no tests. This read carries the seasonality check of V2 (paper:
  "season-dependent") that D-18 recorded as unavailable.
  (b) **Read 2 - spatial rainfall covariate:** CHIRPS v2.0 0.05-degree
  monthly precipitation (UCSB Climate Hazards Center,
  https://data.chc.ucsb.edu/products/CHIRPS-2.0/, Funk et al. 2015
  attribution; open data with attribution), record window 2011-2014, bbox
  75.70-76.50 E / 11.40-12.02 N. Derived layers: (i)
  `rain_annual_total_mm_2011_2014` = mean over the four years of the
  annual sum of monthly values; (ii) `rain_monsoon_jun_sep_share` = mean
  over the four years of the Jun-Sep share of annual total. Bilinear
  resample onto the H3 500 m cell grid (origin-aligned; CHIRPS native
  approx. 5.5 km -> real within-district structure). Joined with the
  **same D-18 overlap reader** (record-weighted incident-KDE percentile
  at covariate top-decile cells + Spearman rho), on the same three arms
  as the run of record (all cells / outside-WDPA / elephant subset).
  Covariate labels are deliberately **record-window (2011-2014),
  contemporaneous, not pre-2011** - a documented deviation from D-18's
  pre-2011 primary rule, justified because the construct here is the
  seasonality of the incident window itself, not pre-treatment land
  condition.
  (c) **Fallback ordering:** IMD 0.25-degree gridded daily rainfall
  (Pai et al. 2014, MAUSAM 65:1-18, imdpune.gov.in, research
  registration) only if CHIRPS is unusable. IMD is recorded here as
  **REJECTED as a spatial covariate** (0.25 deg approx. 27 km -> ~2-4
  cells over the ~60x46 km district: a near-constant field would make the
  overlap read vacuous) and acceptable only as a district-mean time
  series, which Read 1 already covers without new data.
  (d) **Script of record:** `scripts/p3_h3_rainfall_sensitivity.py`
  (imports the H3 module of record for screen/geocode/assign/CellIndex/
  aggregate; replicates the D-18 reader formulas verbatim); facts ->
  `outputs/qaqc/p3_h3_rainfall_sensitivity_{date}.json`; CHIRPS artifacts
  -> `data/raw/` + `data/processed/` with manifest entries (source,
  licence, sha256) before interpretation.
  (e) **Precommitment (binding):** regardless of outcome, H3's registered
  conclusion stands **unchanged (descriptive direction-check, no
  falsification verdict, D-3/D-18)**; no p-values, CIs or significance
  language anywhere; results may be quoted in P4-P5 only as "post-hoc
  sensitivity, non-inferential" annotations - never as H3 confirmation.

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
