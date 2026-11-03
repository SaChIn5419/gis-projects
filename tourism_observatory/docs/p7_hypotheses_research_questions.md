# P7 — Hypotheses, research questions and thesis extension (Wayanad Site 1)

**Status:** task artifact for the P7 report. Companion to
`p7_literature_gap_analysis_wayanad.md` and `p7_research_report_wayanad.md`.
**Design state:** H1–H4 frozen at R6, executed under D-1…D-20; **R9**
(`bcaa9223…`) pins D-21, the descriptive 2000-vs-now accounting.
**Critical rule:** the hypotheses in §2 are **proposals**. They are *not*
registered, *not* tested, and *not* part of the Wayanad result set. Nothing
in this document may be cited as a finding of this study.

---

## §1 What was registered, and what it returned

| ID | Registered question (abridged) | Verdict | Grade |
|---|---|---|---|
| H1 | Do facility-holding protected-remnant parcels convert to built-up faster than matched comparables (2005→2025 operationalised as 2000→2020)? | Not falsified — supported; +16.32 pp @500 m, Holm p = 1.7 × 10⁻⁶ | **High** |
| H2a | Do facility footprints overlap landslide-susceptible terrain and mapped landslides more than terrain-matched random placement? | Not falsified (density: p_holm = 0.014); slope-share test null (p = 0.293) | **Moderate** |
| H2b | What sits inside the mapped hazard footprints? | Descriptive register (no test by design) | **Descriptive** |
| H3 | Do HEC incident hotspots aggregate toward pre-2011 human-influenced, non-protected covariates, with tourism as a tested covariate? | **NO VERDICT** (D-3/D-18: records are village-level, no GPS) | **No verdict** |
| H4 | Do documented disputes overlap tourism–hazard exposure hotspots more than area proportion? | Not falsified on the point-estimate rule; 1/6 vs E = 0.457, p = 0.368 | **Exploratory** |

**The honest summary:** one strong, well-identified effect (H1), one
moderate proxy-based exposure signal (H2a), one enumeration that contradicts
the expected story (H2b), one no-verdict (H3), one exploratory (H4).

---

## §2 Observations that generate new hypotheses

These are the *unregistered* regularities the executed work surfaced. Each
is stated as a testable proposition, with the data that would be needed.

### H5 — Distance–response of conversion around facilities
> Built-up conversion in remnant parcels declines monotonically with
> distance from a verified facility, and the 500 m effect (+16.32 pp) is
> the steepest segment of that gradient.

- **Why plausible:** H1 is only tested at 250/500/1000 m radii; the
  monotone ordering (+24.01 / +16.32 / +11.61 pp) is suggestive but was
  never formally modelled as a gradient.
- **Test:** continuous distance-to-facility term in the matched design, or
  a restricted cubic spline on distance with pair fixed effects; report
  the shape, not just three radii.
- **Data:** existing (parcel table + facility points + GLAD raster).
- **Falsified if:** conversion is flat or non-monotone in distance after
  matching.
- **Feasibility:** high — reuses P2/P3 artifacts; needs a new §7 pin because
  it is a new estimand.

### H6 — Timing: conversion follows facility establishment
> Parcel conversion concentrates in the years *after* the facility appears,
> not before.

- **Why plausible:** H1 measures a 20-year stock difference and cannot
  order the two events. A tourism-led conversion story predicts conversion
  after establishment; a "facilities locate where conversion is already
  happening" story predicts the opposite or simultaneity.
- **Test:** event-time / leads-and-lags design using facility opening years
  (Kerala Department of Economics & Statistics hotel survey carries
  year-of-starting cohorts; the B7 source in the literature matrix) and
  GLAD annual change epochs.
- **Data requirement:** facility establishment year for a usable subset.
  **Not currently in the manifest** — this is the binding constraint.
- **Falsified if:** pre-establishment conversion equals or exceeds
  post-establishment conversion (i.e. reverse causation dominates).
- **Feasibility:** medium — data acquisition is the risk, not the method.

### H7 — The exposure mismatch: narrow event footprints, broad inventory buffers
> Mapped-inventory exposure (H2b(b): 26/107 facilities within 1 km of 990
> inventory polygons) overstates facility exposure relative to
> event-footprint exposure (H2b(a): 0/107 inside the 2024 scar), because the
> inventory proxy is spatially diffuse.

- **Why plausible:** the two registers differ by construction (992.90 km² of
  buffers vs 1.781 km² of scar), and the paper's headline numbers invite the
  wrong reading if not separated.
- **Test:** compare exposure estimates under (i) inventory-buffer, (ii)
  event-scar, (iii) susceptibility-threshold definitions on the same
  facility set; report the spread as a measurement-sensitivity result.
- **Data:** existing.
- **Falsified if:** the three definitions converge on the same facility set.
- **Feasibility:** high — a methods paper in itself.

### H8 — Inventory recency bias against tourism corridors
> The mapped inventory under-represents recent (post-2020) failures,
> especially near tourism corridors, so exposure estimates conditional on it
> are biased downward exactly where tourism is densest.

- **Why plausible:** the 2024 scar is absent from the inventory proxy; the
  inventory carries no vintage attributes (D-15).
- **Test:** compare inventory spatial coverage by distance-to-facility band
  and by year of the 2024 event; check whether facility-dense areas have
  lower inventory density than terrain-matched controls.
- **Data:** existing inventory + facility points (+ any post-2024 official
  event layer, which would need a manifest entry).
- **Falsified if:** inventory density is unrelated to facility proximity
  after terrain matching.
- **Feasibility:** high, but interpretively delicate (absence of mapping ≠
  absence of events).

### H9 — The low-rainfall, human-modified belt
> Incident hotspots sit in the lower-rainfall, human-modified farming belt
> rather than in the wettest forest, and this is a property of where people
> and elephants meet — not of where landslides occur.

- **Why plausible:** D-20 post-hoc ρ(rain annual, incident KDE) = −0.572
  (primary), −0.234 (outside WDPA), −0.583 (elephant); wettest decile at the
  13th incident percentile; no monsoon lock-in (0.4183).
- **Test:** requires incident-level coordinates (not village centroids).
  With GPS data, a point-process model with rainfall, forest edge and
  settlement covariates would separate the mechanisms.
- **Falsified if:** with GPS data the rainfall association disappears or
  reverses.
- **Feasibility:** low **for now** — data do not exist at the required
  resolution. This is a data-acquisition hypothesis, not an analysis one.

### H10 — Protection effect on forest loss
> Forest loss inside WDPA boundaries is materially slower than outside,
> conditional on elevation, slope and distance to settlement.

- **Why plausible:** D-21 descriptive accounting: 1.39 % of inside-WDPA
  forest lost 2001–2024 vs 3.90 % outside (2.8× difference).
- **Test:** matched or regression-adjusted comparison of loss probability
  with terrain and access covariates; the descriptive numbers alone are not
  a protection estimate (WDPA siting is not random).
- **Data:** existing (Hansen, WDPA, DEM, roads, settlements).
- **Falsified if:** the difference vanishes after terrain/access adjustment.
- **Feasibility:** high — but it is a **new analysis** and needs its own pin.

### H11 — Cross-site replication (Mussoorie)
> The facility-proximate conversion effect (H1) and the exposure-overlap
> signal (H2a) replicate in a Himalayan hill station with a different
> hazard regime (rainfall-triggered vs rainfall + road-cut).

- **Why plausible:** the design was built to be transferable; Site 2's
  preplan already pins rainfall pre-freeze.
- **Test:** identical recipe, same grades, pre-registered before Site 2
  outcomes are opened.
- **Falsified if:** the effect is absent or sign-reversed in Mussoorie.
- **Feasibility:** medium — depends on the Mussoorie facility universe and
  parcel grid being constructible at the same quality.

---

## §3 Research questions (thesis scale)

Each RQ states what would be publishable, what data it needs, and what the
main threat is. RQ1–RQ3 are answerable with the present design; RQ4–RQ6
need new data or a new site; RQ7–RQ8 are programme-level.

### RQ1 — Attribution
**What is the effect of tourism-facility presence on land conversion in
protected-remnant parcels, and how much of the district-level built-up
expansion can be attributed to it?**

- Design: the H1 matched-pair estimand, extended with (i) dose–response in
  distance (H5), (ii) event-time ordering (H6), (iii) an attribution
  decomposition comparing matched-pair Δ to district Δ.
- Publishable as: "Facility-proximate land conversion in a Western Ghats
  tourism district: a matched-pair design."
- Threat: unobserved parcel quality; treatment is facility *presence*, not
  facility *opening*.

### RQ2 — Exposure and its measurement
**Do tourism facilities sit in hazardous terrain more than chance, and how
much does the answer depend on which hazard definition is used
(inventory buffer, event scar, susceptibility threshold)?**

- Design: H2a's Monte Carlo under three hazard definitions (H7), plus the
  inventory-recency test (H8).
- Publishable as: "How you define hazard changes who is exposed: a
  measurement-sensitivity study of tourism exposure."
- Threat: the inventory has no vintage; absence of mapping is not absence
  of hazard.

### RQ3 — Distribution and governance
**Who bears the risk of hazard-adjacent tourism development, and does
documented contestation cluster where exposure and land-use friction
coincide?**

- Design: H4 extended beyond n = 6 with a systematically compiled dispute
  register (source-documented, type-coded, no severity score), plus
  tenure/land-class overlays.
- Publishable as: "Contestation at the hazard frontier: disputes and
  exposure in a tourism landscape."
- Threat: documentation bias — more records ≠ more harm. Must be stated,
  not modelled away.

### RQ4 — Pressure measurement
**Can tourism pressure be measured by visitation rather than by facility
existence, and does the conversion effect scale with pressure?**

- Design: replace the binary facility covariate with arrivals/bed-nights
  (Kerala Tourism Statistics; district-level at best) or with
  facility capacity (rooms/beds) where available.
- Publishable as: an upgrade of RQ1 if the data can be assembled.
- Threat: district-level visitation cannot be matched to parcels; the
  design would need a different unit.

### RQ5 — Cross-site generality
**Is facility-proximate conversion a Wayanad-specific pattern or a general
property of Indian hill-station tourism?**

- Design: Site 2 (Mussoorie) under the identical recipe (H11); then a
  two-site comparison of effect sizes, not a pooled estimate.
- Publishable as: the programme paper.
- Threat: Site 2's facility universe and parcel grid may not reach the same
  verification standard.

### RQ6 — Policy counterfactual
**Would regulation of facility siting (slope/forest-setback rules) have
changed the observed exposure distribution?**

- Design: re-run the H2a null under a siting constraint (e.g. no new
  facility on slopes > 25° or within X m of forest edge) and compare the
  observed configuration to the constrained feasible set.
- Publishable as: a policy-relevant simulation — but only as a
  **counterfactual of placements**, never as an evaluation of a real policy.
- Threat: it is a simulation; label it as such.

### RQ7 — Measurement infrastructure
**What would a tourism–hazard observatory need to measure to make these
questions answerable in real time?**

- Design: a data-provenance and cadence specification: facility registry
  refresh, event inventory with vintages, parcel-level conversion epochs,
  visitation series, dispute register protocol.
- Publishable as: a data/methods paper or a policy brief.
- Threat: none scientific; risk of being seen as advocacy.

### RQ8 — Claim discipline
**How much do published tourism–hazard associations change when
pre-registration, pinned deviations and no-verdict reporting are applied?**

- Design: a reproducibility audit of a sample of the 13-query literature
  (how many pre-register? how many report nulls? how many distinguish
  inventory from event exposure?).
- Publishable as: a meta-research note — small but distinctive.
- Threat: sample selection; must be a census of a defined query set, not a
  convenience sample.

---

## §4 Thesis skeleton (if this becomes a doctoral programme)

| Chapter | Content | Status |
|---|---|---|
| 1 | Introduction: tourism as land-use and hazard driver; the attribution gap | draftable now |
| 2 | Literature: five strands, seven gaps (§3 of the gap analysis) | **done** (this P7 set) |
| 3 | Study design: two sites, facility universe, parcel matching, pinned deviations | partially done (Site 1) |
| 4 | RQ1 / H1 + H5 + H6: conversion and timing | H1 done; H5 needs pin; H6 needs data |
| 5 | RQ2 / H2a + H2b + H7 + H8: exposure and its measurement | H2a/H2b done; H7 doable now; H8 doable now |
| 6 | RQ3 / H3 + H4: conflict and contestation | H3 no-verdict; H4 exploratory — chapter must be framed as measurement limits |
| 7 | RQ5 / H11: Mussoorie and cross-site comparison | not started |
| 8 | Synthesis: what a tourism–hazard observatory should measure | draftable now |

**Publication plan (realistic):**

1. **Paper A (methods/measurement):** H2a + H2b + H7 + H8 — "Hazard
   definition changes who is exposed." Strongest standalone contribution
   because it does not depend on the causal claim.
2. **Paper B (attribution):** H1 + H5 (+H6 if data arrive) — the matched-pair
   conversion paper.
3. **Paper C (programme):** two-site comparison + observatory specification.

Paper A is the safest first submission; Paper B carries the most
intellectual risk but the highest payoff.

---

## §5 What would falsify the programme

Be explicit, because a programme without falsifiers is advocacy:

1. **H1 fails to replicate at Site 2** with the same recipe and comparable
   data quality → facility-proximate conversion is site-specific, and the
   general claim dies.
2. **H5/H6 show reverse or simultaneous timing** → facilities follow
   conversion rather than lead it; the causal reading of H1 collapses to
   selection, and the paper must be rewritten as descriptive co-location.
3. **H7 shows hazard definitions converge** → the measurement-sensitivity
   contribution (Paper A) evaporates; H2b becomes a footnote.
4. **H8 finds no inventory-recency bias** → the completeness critique is
   wrong and the exposure estimates stand as originally read.
5. **GPS-level incident data reverse the D-20 rainfall direction** → the
   "human-modified low-rainfall belt" observation is an artefact of village
   centroid aggregation.

Each of these is a legitimate outcome. The design exists to make them
detectable rather than to make the preferred story survive.
