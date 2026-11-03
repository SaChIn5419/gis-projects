# Tourism development, land conversion and hazard exposure in a Western Ghats district: a pre-registered, facility-level audit of Wayanad, Kerala

**Report type:** research paper (Site 1 of a two-site observatory).
**Status:** complete for Site 1; Site 2 (Mussoorie) preplanned, not executed.
**Design of record:** `docs/preregistration_wayanad.md`, frozen at R6,
executed under append-only deviations D-1…D-20, and pinned at
**R9 `bcaa9223…`** for the descriptive 2000-vs-now accounting (D-21).
**Companion documents:** `p7_literature_gap_analysis_wayanad.md`,
`p7_hypotheses_research_questions.md`, `p5_evidence_brief_wayanad.md`,
`p4_risk_register_wayanad.md`.
**Authors:** _to be completed._
**Keywords:** tourism development; land-use change; landslide exposure;
matched-pair design; pre-registration; Western Ghats; Wayanad.

---

## Abstract

**Context.** Tourism is expanding into steep, forested landscapes across the
Western Ghats, and the district of Wayanad (Kerala, India) combines a dense
tourism facility economy, extensive protected forest, and a well-documented
history of rainfall-triggered landslides, including the July 2024
Mundakkai–Chooralmala disaster. District-level land-cover change and
landslide susceptibility have both been mapped repeatedly. What has not
been established is whether tourism presence is associated with land
conversion *at the decision unit* (the parcel), and whether facilities are
exposed to mapped hazard more than comparable terrain would be by chance.

**Objective.** To test facility-level land conversion and hazard exposure in
Wayanad under a pre-registered design, and to report the results — including
the null and unidentifiable ones — without post-hoc upgrading.

**Data and methods.** We verified 107 of 123 tourism registry entries inside
the district, built a 1,163-parcel protected-remnant universe, and matched
50 treatment parcels to 50 controls under frozen calipers (max |SMD| =
0.0667). Four hypotheses were registered before outcomes were opened:
H1 land conversion (GLAD 2000–2020 built-up change); H2a hazard overlap
against a terrain-matched Monte Carlo null (B = 1,001, seeded); H2b
enumeration of assets inside mapped hazard footprints; H3 human–elephant
conflict covariates (downgraded pre-outcome to a descriptive fallback); H4
documented disputes versus an exposure hotspot (exploratory). A descriptive
2000-vs-now land-cover accounting (D-21, pinned at R9) provides context and
is explicitly non-inferential.

**Results.** Facility-holding remnant parcels converted to built-up **16.32
percentage points faster** than matched controls at 500 m (Holm p = 1.7 ×
10⁻⁶), with consistent signs at 250 m (+24.01 pp), 1,000 m (+11.61 pp) and
under two independent robustness indicators. Facility placement overlapped
mapped landslide-inventory density **~2.55× more than chance** (T = 0.002921
vs null mean 0.001145, p_holm = 0.014), but the companion slope-share test
was null (p = 0.293). The 2024 scar (1.781 km²) contained **no verified
facility and no building** from either building source, while 1 km buffers
around 990 mapped inventory polygons contained 26 of 107 facilities and
73,027 buildings. Human–elephant conflict returned **no verdict** (records
are village-level, not GPS). Documented disputes overlapped the exposure
hotspot at 1/6 versus an area-proportion expectation of 0.457 (p = 0.368,
n = 6; exploratory). Descriptively, built-up extent rose from 145.1 to
246.9 km² (1.70×) between 2000 and 2020, and 2.73 % of year-2000 forest was
lost by 2024, with **42 % of that loss concentrated in 2021–2024**.

**Conclusions.** Tourism presence in Wayanad is associated with faster
parcel-scale conversion and with higher mapped-hazard density than matched
terrain, but not with the event that actually occurred: the 2024 scar fell
outside the mapped inventory used for the exposure test and contained no
tourism assets. The most defensible reading is **hazard-adjacent
development pressure with a measurement gap**, not "tourism causes
landslides". Exposure estimates in this literature depend substantially on
which hazard definition is used, and the absolute built-up extent is
strongly product-dependent (GLAD 246.9 km² vs ESA WorldCover 16.2 km²),
though the sign of change is robust. We position the study's contribution
as identification and measurement, not as a new district-level trend.

---

## 1. Introduction

### 1.1 The problem

Mountain tourism development is one of the least measured drivers of land
change in South Asia. The literature has established, for over a decade,
that tourism facilities cluster around protected areas (Karanth & DeFries,
2010: 85 % within 5 km of a boundary, 72 % built after 2000), that
settlements expand around protected areas in biodiversity hotspots (Bailey
et al., 2015), and that conversion is often parcel-level and locally driven
rather than corporate (Pandya et al., 2022). In Wayanad specifically, forest
has been converted to agriculture and plantation since at least the 1950s
(Saha et al., 2022), land-cover change over 23 years has been classified
into nine classes (Bijosh & Abraham, 2024), and future trajectories have
been modelled with CA-ANN (Manawat & Yadav, 2025).

At the same time, Wayanad is one of India's most landslide-exposed
districts. Susceptibility has been mapped with MCDM methods (Guria et al.,
2025), with temporal GEE stacks (Katkar et al., 2024), and — in a 2026
preprint — with machine learning across four Western Ghats hotspots in
which **tourism-driven urbanisation is named as an under-quantified
predisposing factor** (Kellengere Shankarnarayan, 2026). The July 2024
Mundakkai–Chooralmala landslide killed more than 400 people and has since
been studied for its formation mechanisms, progression and impact (Achu et
al., 2025; Ramesh et al., 2025).

**The gap is therefore not "does tourism change land in Wayanad" or "is
Wayanad landslide-prone".** Both are answered. The gap is:

1. whether tourism presence is associated with conversion **at the parcel**,
   against a counterfactual, rather than at district scale or by scenario;
2. whether facilities are exposed to mapped hazard **more than comparable
   terrain would be by chance** — an exposure test, not another
   susceptibility surface;
3. **what actually sits inside** a hazard footprint in a tourism landscape;
4. how much the answer depends on the **hazard definition** and on
   **inventory completeness**;
5. and whether any of this can be reported with explicit claim discipline in
   a literature that habitually over-reads correlational maps.

### 1.2 Contributions

- **A parcel-level counterfactual** for facility presence in a protected
  remnant class (H1), with pre-registered radii, matching calipers, and two
  independent robustness indicators.
- **A facility-level exposure test** against a terrain-matched sampling null
  (H2a), including a companion test that failed (slope share) and is
  reported as a failure.
- **An asset enumeration** inside two hazard footprints of different
  construction (H2b), which produces the study's most uncomfortable result:
  zero facilities and zero buildings inside the 2024 scar.
- **A measurement-bias demonstration**: the exposure signal is estimated
  from a mapped inventory that does not contain the 2024 event, and the
  absolute built-up extent varies 15-fold between two standard products.
- **Claim discipline as method**: frozen hypotheses, append-only deviations,
  a hash chain from R6 to R9, and explicit no-verdict/exploratory labels.

### 1.3 What this paper does not claim

It does not claim that tourism causes landslides. It does not claim that the
district-level land-cover trend is novel. It does not claim that human–
elephant conflict is driven by tourism — the data cannot support that
question, and the hypothesis returns no verdict. D-21's 2000-vs-now numbers
are descriptive accounting, not estimates of effect.

---

## 2. Study area and context

Wayanad district, Kerala, covers **2,026.39 km²** of the Western Ghats
between roughly 11.4–12.0° N and 75.7–76.5° E, with elevation from about
3 m to 2,232 m. It contains substantial protected forest (WDPA complexes),
a plantation economy (coffee, tea, cardamom, rubber), a dense rural
settlement pattern, and a tourism sector built around hill scenery,
waterfalls and wildlife. The district is a recognised human–elephant
conflict landscape (Anoop & Ganesh, 2020; Morrison et al., 2025) and one of
India's highest-exposure landslide districts (ISRO/NRSC Atlas; Katkar et
al., 2024).

Two features of the context matter for interpretation:

1. **The 2024 event is recent relative to every dataset used here.** The
   facility universe is a current-existence registry; building footprints
   are pre-event Google (≤ May 2023) and 2026 OSM; the hazard inventory is
   a WMS proxy with no vintage attributes (D-15). Any exposure statement is
   therefore conditional on measurement vintage.
2. **Tourism here is not resort-enclave tourism.** It is distributed:
   homestays and small facilities along roads and settlements. That matters
   because parcel-scale conversion, not large-footprint construction, is the
   dominant land-change channel.

---

## 3. Data

| Dataset | Product / source | Resolution | Role | Caveat |
|---|---|---|---|---|
| Tourism registry | Kerala registry entries, existence-verified by satellite imagery (2026) | point | Facility universe: 123 entries → **107 verified inside district** | Current existence only; no opening dates |
| Parcel universe | Protected-remnant parcels (1,163) built on the frozen grid | polygon | Matching frame | Remnant class only; excludes non-remnant land |
| Built-up change | GLAD GLCLUC2020 built-up change 2000–2020 (Potapov et al., 2022) | 30 m | H1 primary endpoint; D-21 accounting | Class semantics: 1 = expansion, 2 = stable built |
| Built-up (sensitivity) | ESA WorldCover 2021 v200, class 50 | 10 m → 30 m | H1 robustness; D-21 cross-check | Urban-class definition much stricter |
| Forest | Hansen GFC-2024 v1.12 treecover2000, lossyear | 30 m | H1 robustness; D-21 accounting; H3 covariates | `lossyear > 0` spans 2001–2024 |
| Landslide inventory | Kerala WMS proxy inventory, 990 polygons | vector | H2a KDE; H2b buffers | No attributes, no vintage (D-15) |
| Event scar | NRSC VAP3 digitised 2024 Chooralmala–Mundakkai scar | vector | H2b register (a) | Single event; digitisation error |
| Buildings | Google Open Buildings (≤ May 2023); OSM (2026-10) | polygon | H2b enumeration | Two vintages, different completeness |
| Roads | OSM 2026-10 | line | H2b enumeration; H3 road density | Snapshot |
| HEC records | Morrison et al. (2025) Figshare records, 2011–2014 | village-level | H3 (descriptive fallback) | **No coordinates at source** |
| Disputes | Structured event table (8 disputes / 12 records), source-URL coded | point/area | H4 | Documentation bias; n = 6 geolocatable |
| Rainfall | CHIRPS v2.0 monthly, 2011–2014, bilinear to 500 m | 0.05° → 500 m | D-20 post-hoc sensitivity only | Contemporaneous, not pre-treatment |
| Terrain / access | Copernicus GLO-30 DEM; OSM road distance | 30 m | Matching covariates; null constraints | — |

All files entering `data/` carry a manifest entry with source, licence and
sha256 (36 entries at Site-1 close). No new file was added for D-21: every
input was already manifested.

---

## 4. Methods

### 4.1 Design and registration

The design was frozen at R6 after a pre-analysis checklist. Hypotheses H1–H4
were registered before outcomes were opened; §3 (hypotheses) and §4
(controls) are byte-unchanged since. Every departure is recorded in an
append-only deviation log (D-1…D-21) and each new analysis requires a full-
file re-hash of the pre-registration recorded **before** computation. The
chain runs R6 → R7 → … → R8 `da2baee8…` (D-20) → **R9 `bcaa9223…`** (D-21).

### 4.2 Facility universe and matching

Registry entries (123) were existence-verified against satellite imagery;
107 were verified inside the district and used. From a 1,163-parcel
protected-remnant universe, a deterministic 1:1 no-replacement match
selected controls on frozen covariates and calipers (seed 20261022, 750 m
control buffer). Result: **54 eligible treated parcels → 50 matched pairs**
(886 control candidates), balance gate **max |SMD| = 0.0667 < 0.10** → pass.
Four treated parcels remained unmatched on calipers and are reported, not
silently dropped.

### 4.3 Outcomes

- **H1.** Built-up conversion share within 250/500/1,000 m buffers around
  each parcel, GLAD 2000–2020; paired t-test with Holm correction within the
  hypothesis family; robustness with WorldCover-2021 built-up and Hansen
  loss indicators (sign agreement required).
- **H2a.** Observed facility-vs-inventory overlap statistic T (mean KDE
  value at facility locations) against 1,001 terrain- and access-constrained
  random placements of the same facility count (fixed seed), exceedance
  p-value (1 + #{T_j ≥ T_obs}) / 1001; companion slope-share test.
- **H2b.** Two registers that are never merged: (a) the 2024 scar and
  (b) 1 km buffers around the 990 inventory polygons with the scar overlap
  excluded. Enumerations of facilities, buildings and roads; building counts
  reported with confidence bands and jitter ranges.
- **H3.** Pre-outcome downgraded (D-3/D-18) because the source records are
  village-level. Descriptive KDE overlap: Spearman ρ between incident-surface
  percentiles and covariate percentiles, three arms, **no p-values**.
- **H4.** Overlap of geolocatable disputes with the D-19(c) exposure hotspot
  versus area-proportion expectation; pinned permutation (B = 10,000, seed
  20261102), reported as **non-inferential** (n = 6 < 15).
- **D-21.** Descriptive accounting: built-up extent 2000/2020, forest 2000 /
  2020 / 2024, loss by decade band, WDPA splits, annual loss series, and a
  non-inferential context share for facility buffers.

### 4.4 Claim rules applied throughout

No p-value, CI or causal language for H3, H4 or D-21. H3's registered
conclusion cannot be altered by the post-hoc rainfall sensitivity (binding
precommitment D-20e). D-21 numbers may not be promoted into the H1–H4
family. Where a product disagreement exists (GLAD vs WorldCover), both
numbers are reported and neither is averaged.

### 4.5 Reproducibility

Scripts of record: `p3_h1_analysis.py`, `p3_h2_analysis.py`,
`p3_h3_analysis.py`, `p3_h3_rainfall_sensitivity.py`, `p4_h4_analysis.py`,
`p7_2000_vs_now.py`, `p6_render_maps.py`, `p7_render_maps.py`. Facts files
and their sha256 are listed in Appendix A. Figures F1–F9 are rendered from
the files of record; the render pipeline asserts its outputs against the
facts (e.g. rainfall ρ re-render −0.571 vs facts −0.572).

---

## 5. Results

All numbers below are quoted from hash-pinned facts files (Appendix A).
Percentages computed from those numbers are marked *(derived)*.

### 5.1 The 2000-vs-now context (D-21, descriptive — no test)

**Built-up.** The district's GLAD built-up extent rose from **145.114 km² in
2000** to **246.921 km² in 2020** — an expansion of **101.807 km²**, a
**1.702×** increase, from 7.161 % to 12.185 % of district area. Inside WDPA
boundaries the extent rose 24.166 → 42.471 km² (+18.305 km², **18.0 % of all
expansion** *(derived)*); outside, 120.948 → 204.450 km² (+83.502 km²).

**Forest.** Forest defined as Hansen tree cover ≥ 30 % covered
**1,601.214 km² (79.018 % of the district) in 2000**, **1,575.776 km² in
2020** and **1,557.524 km² in 2024**. Cumulative loss 2001–2024 was
**43.691 km², or 2.729 % of year-2000 forest**, distributed as:

| period | loss (km²) | per-year rate (km² yr⁻¹) *(derived)* |
|---|---|---|
| 2001–2010 | 8.752 | 0.875 |
| 2011–2020 | 16.686 | 1.669 |
| 2021–2024 | **18.252** | **4.563** |

The most recent four years account for **41.8 %** *(derived)* of all
24-year loss at a per-year rate **2.7× the 2011–2020 rate** *(derived)*.
Loss was **1.39 % of inside-WDPA forest** (10.326 of 745.428 km²) versus
**3.90 % outside** (33.365 of 855.787 km²) *(derived)* — a 2.8× difference
in rate, unadjusted for terrain or access.

**Product disagreement (reported, not reconciled).** ESA WorldCover 2021
places only **16.214 km²** in its built-up class, against GLAD's 246.921 km²
for 2020 — a **15.2×** difference *(derived)*. WorldCover's tree class
(1,816.199 km²) exceeds Hansen's ≥ 30 % forest (1,601.214 km²) by a similar
order in the other direction *(derived)*. Absolute class areas are therefore
**not comparable across products**; the change signal and the within-pair
design are the defensible units.

**Context share (non-inferential).** The union of 500 m buffers around the
107 verified facilities covers **67.485 km² (3.33 % of the district)** but
contains **6.310 km² of the 101.807 km² expansion (6.20 %)** — a
**1.86×** concentration *(derived)*. This is context only; **H1 is the
registered test** and the two must not be conflated.

**Figures F8 and F9** show these quantities as three (built-up) and four
(forest) panels on the 500 m grid. The visual result is unambiguous: the
expansion belt runs through the settled centre and south-west, and the
recent loss panel is spatially co-located with the longer-run loss panel,
not displaced from it.

### 5.2 H1 — Facility-holding parcels convert faster (High confidence)

Matched-pair Δ built-up change 2000–2020:

| radius | treatment − control | sign | p |
|---|---|---|---|
| 250 m | **+24.01 pp** | agrees | per-radius p in facts |
| **500 m (primary)** | **+16.32 pp** | — | **Holm p = 1.7 × 10⁻⁶** (t = 5.64) |
| 1,000 m | +11.61 pp | agrees | per-radius p in facts |

Holm correction is applied within the registered radius family; the primary
(500 m) result is the one quoted, and the other radii are reported as sign
agreement rather than as separate claims.

Robustness: WorldCover-2021 built-up **+5.24 pp**; Hansen loss **+1.96 pp**;
both signs agree with the primary. Four treated parcels were unmatched on
calipers; the effect is not driven by them (they are excluded from the
paired estimate by construction and reported in the matching log).

The monotone decline across radii is suggestive of a distance gradient but
is **not** a gradient estimate — H5 in the companion hypotheses document
proposes the test that would be.

### 5.3 H2a — Facilities sit in higher mapped-hazard density than chance (Moderate confidence)

- Observed statistic **T_obs = 0.002921**.
- Null (1,001 seeded placements, terrain- and access-constrained): mean
  **0.001145**, 95th percentile **0.002164**.
- Ratio **~2.55×**; exceedance **p_holm = 0.014**.
- Independent re-render and rerun (D-17a) reproduced the result.
- **Companion test failed:** the slope-share test returned
  **p_holm = 0.293** — facilities do not occupy steep-slope cells more than
  chance.

The honest reading: facilities are where the *mapped inventory* is dense,
not where slopes are steep. That distinction turns out to be the paper's
central measurement issue (see 5.4).

### 5.4 H2b — What is actually inside the footprints (Descriptive)

| footprint | area | facilities | buildings | roads |
|---|---|---|---|---|
| (a) 2024 scar, Chooralmala–Mundakkai | **1.781 km²** | **0** | **0** (Google pre-event and OSM 2026 both) | 1 segment, **0.758 km**, class `construction` |
| (b) 1 km buffers around 990 inventory polygons (scar overlap excluded) | **992.90 km² (46.6 % of district)** | **26 / 107** | **73,027** (Google; 57,291 at confidence ≥ 0.7; 71,980–74,050 under ±10 m jitter) · 10,389 OSM | **1,370.1 km** (3,184 segments) |

This is the study's most consequential pair of numbers. The event that
actually occurred — the deadliest landslide in the district's recorded
history — contained **no tourism facility and no building** in either
building dataset, while the *mapped inventory* buffers imply that a quarter
of the facility universe sits within 1 km of a mapped landslide. The two
statements are not contradictory; they describe **different event
populations**, and the paper keeps them separate by design.

**Consequence for H2a.** The exposure signal is estimated from the
inventory proxy, which does not contain the 2024 event. H2a therefore
describes **susceptibility terrain**, not realised event exposure. This is a
boundary of the result, not a footnote.

### 5.5 H3 — Human–elephant conflict: no verdict

The registered model was downgraded before outcomes were opened (D-3/D-18)
because the source records (2,704 kept records, 2011–2014) carry **village
names, not coordinates**. The descriptive fallback gives:

- forest-cover ρ = **−0.178** (primary), **−0.051** (outside WDPA),
  **−0.218** (elephant subset);
- all human-modification covariates **|ρ| ≤ 0.07**;
- facility covariate **null in every arm**.

There is no p-value because there is no test. The one stable feature —
incidents locating **off dense forest** — is directionally consistent with
the published conflict literature (Morrison et al., 2025) and is the only
claim we make.

**D-20 post-hoc rainfall sensitivity (non-inferential).** Incident hotspots
lie in the **lower-rainfall, human-modified farming belt**:
ρ(annual rainfall, incident KDE) = **−0.572** (primary), **−0.234**
(outside WDPA), **−0.583** (elephant); the wettest decile sits at the 13th
incident percentile; the Jun–Sep monsoon share of annual rainfall is
**0.4183**, i.e. **no monsoon lock-in**. This is labelled post-hoc
sensitivity and **cannot** alter H3's no-verdict.

### 5.6 H4 — Disputes versus the exposure hotspot: exploratory

Six geolocatable disputes (from a register of 8 disputes / 12 records) were
tested against the D-19(c) exposure hotspot (facility 500 m buffers ∩
inventory 1 km buffers ∪ 2024 scar; 15.06 km²):

- observed overlap **T = 1/6**;
- deterministic area-proportion expectation **E = 0.457**;
- pinned permutation **p = 0.368** (B = 10,000, seed 20261102);
- distances to the hotspot for D-003 / D-004 / D-008: **94 / 24 / 143 m**.

With n = 6 the design cannot separate a real clustering tendency from
documentation bias. The result is reported as exploratory and is not used
to support any claim about tourism and social conflict.

### 5.7 Summary of verdicts

| hypothesis | verdict | grade |
|---|---|---|
| H1 land conversion | not falsified — supported | **High** |
| H2a hazard overlap (density) | not falsified | **Moderate** |
| H2a slope-share companion | null | — |
| H2b footprint enumeration | descriptive register | **Descriptive** |
| H3 HEC covariates | **no verdict** | **No verdict** |
| H4 dispute overlap | exploratory | **Exploratory** |
| D-21 2000-vs-now accounting | descriptive, non-inferential | **Descriptive** |

---

## 6. Discussion

### 6.1 What the results establish

Three findings survive the design:

1. **Facility presence marks faster parcel-scale conversion.** The effect is
   large (+16.32 pp at 500 m on a built-up share base), precisely estimated
   within the matched design, and sign-stable across radii and two
   independent indicators. It is the strongest result in the study.
2. **Facility placement is not random with respect to mapped hazard** — but
   only under the inventory-density definition, not under slope share. That
   asymmetry is informative rather than embarrassing: it says facilities
   are located where *mapped landslides are dense*, which may reflect
   terrain, roads, or the mapping process itself.
3. **The event that mattered is outside the exposure measurement.** The
   2024 scar contains zero tourism facilities and zero buildings, and lies
   outside the inventory proxy used for H2a. Exposure estimates in this
   landscape are therefore conditional on a hazard map that did not contain
   the disaster.

The fourth and fifth results are absences: H3 cannot be answered with the
available records, and H4 cannot be answered with n = 6.

### 6.2 Relation to the literature

**Where the study extends the literature.**

- *Tourism → land change.* Karanth & DeFries (2010) established facility
  clustering near protected areas; Pandya et al. (2022) showed parcel-level
  conversion qualitatively at Corbett. This study supplies the missing
  **quantitative counterfactual at the parcel**, in a district where the
  district-level trend was already known (Saha et al., 2022; Bijosh &
  Abraham, 2024; Manawat & Yadav, 2025).
- *Hazard exposure.* Susceptibility mapping for Wayanad is well developed
  (Guria et al., 2025; Katkar et al., 2024), and a 2026 preprint already
  names tourism-driven urbanisation as a predisposing factor (Kellengere
  Shankarnarayan, 2026). This study does not compete on susceptibility; it
  asks the complementary question — **are facilities where hazard is, more
  than chance?** — and then shows the answer depends on the hazard
  definition.
- *Measurement.* Tanyaş & Lombardo (2019) and Santangelo et al. (2015)
  formalised inventory completeness and mapping error. This study is an
  empirical demonstration of why that matters for exposure: the inventory
  and the event disagree, and the disagreement is large enough to change the
  headline.

**Where the study is anticipated.** The framing "tourism urbanisation on
steep forested slopes is an under-quantified predisposing factor" is no
longer novel — the 2026 preprint says it for Wayanad among four hotspots.
Our introduction therefore concedes the framing and claims only the
identification strategy, the exposure test, the enumeration, and the
measurement result.

**Where the study agrees with the literature.** The lower-rainfall,
human-modified location of conflict hotspots (D-20) is consistent with
Morrison et al. (2025); the forest-edge/settlement pattern is the standard
conflict-geography finding (Sengupta et al., 2020; Anoop & Ganesh, 2020).
We do not claim novelty there.

### 6.3 What is new, precisely

| Claim | Status |
|---|---|
| Parcel-level counterfactual for facility-proximate conversion in India | **New** (to our knowledge) |
| Facility-level exposure tested against a terrain-matched null | **New** for this landscape |
| Asset enumeration inside a tourism-landscape hazard footprint | **New**; the zero-facility scar is the headline |
| Hazard-definition sensitivity of exposure | **Partly new** — method known, application new |
| Inventory-completeness demonstration for tourism exposure | **Partly new** |
| Pre-registered claim discipline in tourism–hazard work | **New as practice**, not as theory |
| District land-cover trend in Wayanad | **Not new** — cite, don't claim |
| Wayanad landslide susceptibility | **Not new** — cite, don't claim |
| Tourism facilities cluster near protected areas | **Not new** (Karanth & DeFries, 2010) |

### 6.4 Limitations

1. **Inventory proxy (D-15).** No attributes, no vintage, WMS-sourced. H2a
   is bounded by it; the D-17a re-render reduces but does not remove the
   concern.
2. **Vintages.** Facility existence is current; buildings are 2023/2026;
   roads are 2026; the H3 records are 2011–2014. No entry may be read as a
   historical baseline.
3. **No visitation data.** Tourism pressure is proxied by facility
   existence. A facility may be dormant; a busy area may be under-registered.
4. **Single site.** Site 2 is preplanned, not executed. Cross-site
   generality is a promise, not a result.
5. **Unobserved parcel quality.** Matching cannot eliminate selection on
   unmeasured parcel attributes (tenure, access, land value). H6's
   event-time design is the natural next test.
6. **Product disagreement.** GLAD and WorldCover differ by 15× on absolute
   built-up extent. The change estimate and the paired design are robust in
   sign, but absolute areas should not be quoted without the product name.
7. **No-verdict H3.** Village-level records cannot support spatial
   inference; the point estimates exist but the design cannot defend them.
8. **Exploratory H4.** n = 6 and documentation bias.
9. **D-21 is accounting, not inference.** The WDPA split is unadjusted;
   protected areas are not randomly sited.

### 6.5 Implications (stated carefully)

- **For siting policy:** the conversion signal suggests that the parcel-
  scale footprint of tourism extends beyond the facility itself — a 500 m
  buffer is where the effect is measured. Setback rules that regulate only
  the building footprint will miss most of the conversion.
- **For hazard governance:** exposure assessments that rely on a mapped
  inventory should state whether the inventory contains recent events. In
  Wayanad it does not contain the 2024 event, which is the one that killed
  more than 400 people.
- **For monitoring:** a tourism–hazard observatory needs three cadences — a
  facility registry refresh, an event inventory with vintage attributes, and
  a parcel-scale conversion epoch. None of the three is currently public at
  the required quality.

### 6.6 Next steps

1. **H7/H8 (measurement papers)** — hazard-definition sensitivity and
   inventory-recency bias; both computable from existing data, both need a
   new §7 pin before computation.
2. **H5 (dose–response)** — continuous distance model; needs a pin.
3. **H6 (timing)** — facility opening years; data acquisition is the binding
   constraint.
4. **Site 2 (Mussoorie)** — identical recipe, rainfall pinned pre-freeze.
5. **GPS-level conflict data** — the only route to a defensible H3.

---

## 7. Conclusion

Wayanad's tourism facilities are located where land converts fast and where
mapped landslides are dense. That much the data support. What the data do
not support is the sentence most likely to be written about them — that
tourism development is putting people in the path of landslides. The
deadliest event in the district's history contained no tourism facility and
no building at all, and it sits outside the inventory on which the exposure
signal is based.

The defensible conclusion is narrower and more useful: **tourism presence is
associated with parcel-scale land conversion and with mapped-hazard density,
and the exposure picture is limited by a hazard inventory that does not
capture recent events.** Fixing that measurement gap — not arguing about
whether tourism is "good" or "bad" — is the actionable finding.

---

## 8. Reproducibility, data and code

- **Pre-registration:** `docs/preregistration_wayanad.md`, R6 freeze,
  deviations D-1…D-21 append-only, **R9 = `bcaa9223…`**.
- **Facts of record (sha256, first 8):** H1 `85d1597c`; H2a `f3432795`;
  H2b `e50ae8bd`; H3 `dd73bddb`; D-20 `e1ab4cbe`; H4 `d945c4a6`;
  dispute table `7a1996cd`; **D-21 `a9a1b29f`** (accounting JSON), display
  stack `1b888fd1`.
- **Scripts of record:** see §4.5. Figures regenerate with
  `python3 scripts/p6_render_maps.py && python3 scripts/p7_render_maps.py`;
  D-21 with `python3 scripts/p7_2000_vs_now.py`.
- **Data manifest:** 36 entries, each with source, licence and sha256.
  No file was added for D-21.
- **Licences:** GLAD CC-BY 4.0; Hansen CC-BY 4.0; ESA WorldCover CC BY 4.0;
  CHIRPS public domain with attribution (Funk et al., 2015); OSM ODbL;
  WDPA and Kerala WMS inventory as documented in the manifest.

**Ethics.** No human subjects; dispute records are from published/open
sources; facility locations are commercial premises.

---

## References

Achu, A. L., Aju, C. D., Thomas, J., Raicy, M. C., et al. (2025). Decoding
the dynamics of July 2024 Mundakkai–Chooralmala landslide in Kerala
(India). *Landslides* 22(4), 1181–1197.
https://doi.org/10.1007/s10346-024-02454-y

Aiswarya, A. N., Amrutha, A. S., Pradeep, G. S., & Vijith, H. (2026).
Landslide susceptibility and local antecedent rainfall thresholds in the
Highland Western Ghats Kerala India. *Discover Hazards* 2(1).
https://doi.org/10.1007/s44475-026-00056-x

Ajin, R. S., Nandakumar, D., Rajaneesh, A., Oommen, T., et al. (2022). The
tale of three landslides in the Western Ghats, India. *Geoenvironmental
Disasters* 9(1). https://doi.org/10.1186/s40677-022-00218-1

Anoop, N. R., & Ganesh, T. (2020). The forests and elephants of Wayanad.
*Current Science* 118(3), 362.
https://doi.org/10.18520/cs/v118/i3/362-367

Bailey, K. M., McCleery, R. A., Binford, M. W., & Zweig, C. L. (2015).
Land-cover change within and around protected areas in a biodiversity
hotspot. *Journal of Land Use Science* 11(2), 154–176.
https://doi.org/10.1080/1747423x.2015.1086905

Bijosh, M. G., & Abraham, J. (2024). Land use and land cover changes in
Wayanad district of Kerala. *Journal of Veterinary and Animal Sciences*
55(3), 516–523. https://doi.org/10.51966/jvas.2024.55.3.516-523

Drisiya, J., & Singh, S. (2026). Integrated eco-environmental risk mapping
in the mountainous tropical landscapes of the Western Ghats, Kerala.
*Frontiers in Remote Sensing* 7.
https://doi.org/10.3389/frsen.2026.1803946

Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., et al. (2015). The
climate hazards infrared precipitation with stations — a new environmental
record for monitoring extremes. *Scientific Data* 2, 150066.

Guria, R., Mishra, M., & Das, J. (2025). MARCOS, CoCoSo and GRA MCDM
models for landslide susceptibility assessment in Wayanad district.
*Advances in Geographic Information Science*, 261–289.
https://doi.org/10.1007/978-3-031-89246-2_11

Karanth, K. K., & DeFries, R. (2010). Nature-based tourism in Indian
protected areas. *Conservation Letters* 4(2), 137–149.
https://doi.org/10.1111/j.1755-263x.2010.00154.x

Katkar, R., Vijaywargiya, J., & Ramiya, A. M. (2024). Assessing changing
landslide risks in Wayanad, Kerala through temporal susceptibility mapping.
*IEEE InGARSS*, 1–4.
https://doi.org/10.1109/ingarss61818.2024.10983924

Kellengere Shankarnarayan, V. (2026). Landslide susceptibility in the
Western Ghats controlled by terrain and tourism driven urbanisation.
**Preprint**, Research Square.
https://doi.org/10.21203/rs.3.rs-10568295/v1

Manawat, R., & Yadav, D. K. (2025). Land-use and land-cover dynamics in
Wayanad, Kerala: QGIS, MOLUSCE and CA-ANN. *Lecture Notes in Electrical
Engineering*, 295–307. https://doi.org/10.1007/978-981-96-8070-2_24

Morrison, J., Chatterjee, M., Ramkumar, K., Tiwari, S. K., et al. (2025).
Spatiotemporal distribution of negative human–elephant interactions in
Wayanad district, Kerala. *Global Ecology and Conservation* 62, e03742.
https://doi.org/10.1016/j.gecco.2025.e03742

Pandya, R., Dev, H. S., Rai, N. D., & Fletcher, R. (2022). Rendering land
touristifiable: (eco)tourism and land use change. *Tourism Geographies*
25(4), 1068–1084. https://doi.org/10.1080/14616688.2022.2077425

Potapov, P., Hansen, M. C., Pickens, A., Hernández-Serna, A., et al.
(2022). The global 2000–2020 land cover and land use change dataset derived
from the Landsat archive. *Frontiers in Remote Sensing* 3.
https://doi.org/10.3389/frsen.2022.856903

Ramesh, M. V., Ekkirala, H. C., Singh, B., Kumar M, N., et al. (2025).
Mundakkai–Chooralmala landslide: assessment of initiation, progression, and
impact. *Scientific Reports* 15, 26961.
https://doi.org/10.1038/s41598-025-07828-3

Saha, K., Ghatak, D., & Muralee, N. S. S. (2022). Impact of plantation
induced forest degradation on emerging infectious disease outbreaks —
Wayanad district. *IJERPH* 19(12), 7036.
https://doi.org/10.3390/ijerph19127036

Santangelo, M., Marchesini, I., Bucci, F., Cardinali, M., et al. (2015).
Reducing mapping errors in the production of landslide inventory maps.
*NHESS* 15(9), 2111–2126.
https://doi.org/10.5194/nhess-15-2111-2015

Sengupta, A., Binoy, V. V., & Radhakrishna, S. (2020). Human–elephant
conflict in Kerala: a rapid appraisal using compensation records. *Human
Ecology* 48(1), 101–109. https://doi.org/10.1007/s10745-020-00128-6

Shukla, R., Öztürk, U., Levin-Keitel, M., Agrawal, S., et al. (2026).
Regulated tourism can become a tool for reducing landslide risk in
Himalayan urban centres. *Environmental Research Letters* 21(15), 151001.
https://doi.org/10.1088/1748-9326/ae83ce

Tanyaş, H., & Lombardo, L. (2019). Completeness index for earthquake-
induced landslide inventories. *Engineering Geology* 264, 105331.
https://doi.org/10.1016/j.enggeo.2019.105331

Hansen, M. C., Potapov, P. V., Moore, R., Hancher, M., et al. (2013).
High-resolution global maps of 21st-century forest cover change. *Science*
342, 850–853. (Dataset: GFC-2024 v1.12.)

Zanaga, D., et al. (2021). ESA WorldCover 10 m 2021 v200. Dataset, CC BY
4.0. https://doi.org/10.5281/zenodo.7254221

---

## Appendix A — Verdict and hash ledger

| artifact | sha256 (first 8) |
|---|---|
| prereg R8 (D-20) | `da2baee8` |
| **prereg R9 (D-21)** | **`bcaa9223`** |
| H1 facts | `85d1597c` |
| H2a facts | `f3432795` |
| H2b facts | `e50ae8bd` |
| H3 facts | `dd73bddb` |
| D-20 rainfall facts | `e1ab4cbe` |
| H4 facts | `d945c4a6` |
| H4 dispute table | `7a1996cd` |
| **D-21 accounting facts** | **`a9a1b29f`** |
| D-21 500 m display stack | `1b888fd1` |

## Appendix B — Deviations that affect reading (summary)

| id | what it did | effect on claims |
|---|---|---|
| D-3 / D-18 | H3 downgraded to descriptive fallback (records lack GPS) | H3 has no verdict; no p-values |
| D-5 | H4 event-observation process; n < 15 → exploratory | H4 cannot support inference |
| D-13 | Built-up endpoint operationalised as 2020 (2021 sensitivity) because no 2025 product exists | H1 period is 2000–2020, stated everywhere |
| D-15 | Landslide inventory is a WMS proxy without attributes/vintage | Bounds H2a |
| D-16 | Monte Carlo p-value rule (1 + #{T_j ≥ T_obs})/1001 | H2a p-value definition |
| D-17a | Independent re-render/rerun of H2a | Confirms, does not remove, proxy caveat |
| D-19 | H4 measurement recipe and event table | Pre-pinned |
| D-20 | Post-hoc rainfall sensitivity | Non-inferential; cannot alter H3 |
| **D-21** | **Descriptive 2000-vs-now accounting (R9)** | **No test; not promotable to H1–H4** |

## Appendix C — Figures

| figure | content |
|---|---|
| F1 | Study site: verified facilities and protected-area complexes |
| F2 | Topography: elevation bands and slope ≥ 25° |
| F3 | H1 matched pairs over built-up change 2000–2020 |
| F4 | H2a hazard KDE surface and facility percentiles |
| F5 | H2b two event populations (2024 scar vs inventory buffers) |
| F6 | H3 incident hotspots, forest cover, D-20 rainfall (post-hoc) |
| F7 | H4 disputes and the exposure hotspot |
| **F8** | **Built-up 2000 vs 2020 and expansion (500 m cells)** |
| **F9** | **Forest 2000 vs 2024 and loss 2001–2024 / 2021–2024** |

---

*End of report. Site 2 (Mussoorie) is preplanned; its results are not part
of this document.*
