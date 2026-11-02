# P4 — Wayanad risk register (tourism-environment observatory)

**Purpose.** This register converts the frozen, preregistered P3 outcomes
(H1–H4) into decision-facing risk entries. It is **exposure-evidence
synthesis, not a probabilistic risk assessment**: entries state what the
measured evidence shows, which hypothesis carries it, the evidence grade,
and the caveat blast-radius. No entry may outrank its evidence grade.

**Evidence base of record** (all artifacts hash-pinned; see §5):
H1 (`p3_h1_facts_2026-10-28.json`), H2a (`p3_h2a_facts_2026-10-28.json`),
H2b (`p3_h2b_facts_2026-10-28.json`), H3 (`p3_h3_facts_2026-11-02.json`),
H4 (`p4_h4_facts_2026-11-02.json`), D-20 rainfall sensitivity
(`p3_h3_rainfall_sensitivity_2026-11-02.json`). Governing freeze: **R6**
(§8 signed); deviation log §7 D-1…D-20 append-only; R-chain
… → R7e `c4ac9606…` → **R8 `da2baee8…`** (D-20 pin, pre-rainfall-computation).

---

## §1 Risk entries

### R-1 — Landslide-exposure co-location with tourism facilities
- **Evidence:** H2a(ii) — observed mean hazard-KDE density across the 107
  verified facilities = **0.002921** vs null mean **0.001145** (≈2.55×;
  null p95 = 0.002164), B = 1,001 seeded Monte Carlo, **p_holm = 0.014**
  across the frozen family {H1, H2a(i), H2a(ii)}. H2b(b) register: 1 km
  buffers around the 990 mapped-inventory proxy polygons cover
  **992.90 km² (46.6% of district)** and contain **26/107 facilities**,
  **73,027** Google-Open-Buildings footprints (±10 m jitter:
  71,980–74,050), **1,370.1 km** of mapped roads.
- **Grade: Moderate-High.** Significant after family correction and
  D-17a refetch agreement — but the hazard input is a WMS-rendered proxy
  (D-15) without attributes/vintage, so exposure-to-mapped-stock, not
  validated hazard.
- **Blast radius:** D-15 proxy caveat bounds this entry (see §2); the
  slope-share companion test was null (H2a(i), p_holm = 0.293) — exposure
  rides *inventory density*, not steepness alone.

### R-2 — Built-up conversion pressure in the protected remnant class
- **Evidence:** H1 — matched-pair (50/50) difference in built-up change
  2000–2020: treatment > control at the primary 500 m radius
  (**+16.32 pp**, paired t = 5.64, **p_holm = 1.7e-06**) and at all
  tested radii (250 m: **+24.01 pp**, 1,000 m: **+11.61 pp**);
  robustness directions agree (ESA WorldCover strict: +5.24 pp; Hansen
  loss: +1.96 pp).
- **Grade: High** — strongest powered result in the block, family-
  corrected, robustness-consistent; facility-holding remnant parcels are
  demonstrably on faster conversion trajectories than matched
  non-facility parcels.
- **Blast radius:** matching covariates include the current-existence
  facility set; the claim is *association under the frozen match*,
  not a causal rate.

### R-3 — 2024 mass-casualty debris-flow footprint currently
  facility-free (status register)
- **Evidence:** H2b(a) — the digitized NRSC scar (Chooralmala–Mundakkai,
  Union 1.781 km²; VAP3 31-Jul-2024, ±15 m georef, 150 m corridor):
  **0 facilities, 0 buildings** (both Google pre-event stock and OSM
  2026 snapshot), **1 mapped road segment, 0.758 km, class
  `construction`** (±15 m jitter: 0.72–0.835 km).
- **Grade: Descriptive fact** (enumeration, not inference).
- **Interpretation guard:** the hazard footprints (a) and (b) have
  **different event populations** (Jul-2024 event *excluded* from the
  proxy inventory) and must never be merged into one exposure number;
  OSM building stock is partly post-event rebuild.

### R-4 — Human–elephant conflict adjacency: **no verdict**
- **Evidence:** H3 under the D-3/D-18 registered downgrade — direction
  check only. Stable feature: **negative forest-cover association**
  (ρ = −0.178 primary / −0.051 outside-WDPA / −0.218 elephant subset);
  all human-modification covariates signed positive but near-null
  (|ρ| ≤ 0.07); facility proximity null in every arm. **D-20 post-hoc
  rainfall sensitivity** (facts `p3_h3_rainfall_sensitivity_2026-11-02.json`,
  sha `e1ab4cbe…`, §5): seasonality SW-monsoon (Jun–Sep) share **0.4183**
  all / 0.4351 elephant, NE (Oct–Dec) 0.2670 — mildly season-weighted, no
  monsoon lock-in; record-window covariates: `rain_annual_total_mm_2011_2014`
  ρ = **−0.572** primary / −0.234 outside-WDPA / −0.583 elephant (wettest
  decile cells sit at the 13th incident percentile), `rain_monsoon_jun_sep_share`
  near-null and sign-fragile (−0.151 primary / +0.078 outside-WDPA).
  Reading: hotspots in the drier human-modified farming belt — direction-
  consistent with the stable negative forest-cover feature; **labelled
  POST-HOC SENSITIVITY, non-inferential; cannot alter this verdict.**
- **Grade: No-verdict** — the registered recipe (descriptive, no p-values)
  cannot confirm or falsify H3; village-massed records cannot resolve
  the paper's edge/seasonality findings.
- **Blast radius:** nothing in H3 may be read as tourism-attribution —
  the facility covariate is null in all arms, **supporting the same
  "not-conflict-explained-by-tourism" reading** as H4.

### R-5 — Documented land disputes adjacent to exposure zones
  (EXPLORATORY)
- **Evidence:** H4 — of 6 cell-eligible disputes, **T_obs = 1** overlaps
  the tourism-hazard exposure hotspot (15.06 km² = 0.74% of district)
  within its 1 km precision footprint; deterministic expectation
  **E = 0.457**; §3 rule: observed > expected ⇒ **NOT falsified**
  (point-estimate rule). Pinned permutation read-out
  (B = 10,000, seed 20261102): p = 0.368 — **non-inferential by D-5**
  (n = 6 < 15).
- **Grade: Exploratory.** The margin disclosures are part of the entry:
  D-004 Valathoor quarry protest sits **24 m** off the hotspot boundary
  (the only overlap); D-003 Chooralmala rehab protest misses by
  **94 m**; D-008 Kalpetta by **143 m** — the two most hazard-salient
  disputes sit *just outside* the pinned radius.
- **Reading guard:** the register's one overlap is
  quarry/land-friction conflict next to the 2024 corridor — **not**
  facility–community conflict; documentation bias (press/LCW salience)
  is mandatory here (§2).

---

## §2 Caveat blast-radius table (mandatory dispositions)

| caveat | bounds which entries | disposition in this register |
|---|---|---|
| **D-15** WMS-rendered proxy hazard polygons (no attributes/vintage) | R-1 primary; R-5 hotspot definition | Bounded: H2a(ii) survived a **registered, independent D-17a re-render + rerun** (1,151→990-polynomial extent rebuild; result agreement). Label retained: "exposure to *mapped-inventory density*". A deeper probe (polygon-count weighting / size-deciles) is available but would require a new §7 pin **before** any statistic (post-outcome discipline) — logged as optional QA, not as evidence. |
| **Vintage bounds** (GOB imagery ≤ May-2023 pre-event; OSM snapshot 2026-10-26 mixed incl. rebuild; roads 2026-10; facilities = current-existence universe) | R-1, R-2 (covariates), R-3, R-5 reportable area | Bounded per artifact: each number carries its vintage label; R-3 explicitly split pre-event (GOB) vs post-event (OSM) stock. No entry cites a vintage as if it were a historical baseline. |
| **Documentation/effort bias in both registers** (forest-department compensation records; press/LCW dispute coverage) | R-4, R-5 | Bounded: spatial nulls partially absorb placement propensity (H4 samples within reportable settlement cells); *selection* remains unquantified. R-5 worded as "spatial distribution of documented records". |
| **D-3 bound** (HEC records never carried GPS) | R-4 exclusively | H3 = direction check; the no-verdict **is** the disposition. |
| **H4 n = 6 < 15** | R-5 | EXPLORATORY flag; the permutation p is quoted as a pinned read-out only. |
| **D-20 post-hoc rainfall addition** | R-4 appendix only | Results may be quoted as non-inferential sensitivity annotations; cannot upgrade H3's verdict (binding precommitment in D-20(e)). |

## §3 Unknowns (recorded, not silently dropped)

- No GPS in the HEC source records (audit-D-10) — H3 structural ceiling.
- No official Atlas landslide vector was available at freeze; the D-15
  proxy stands with its label.
- Rainfall entered only as a post-hoc sensitivity (D-20); the registered
  H3 family ran without it; Mussoorie (Site 2) will pin rainfall
  pre-freeze.
- No visitation/footfall data exists in the pipeline: all "tourism
  pressure" is proxied by facility existence, never visitor volume.
- Facility verification is existence-at-imagery (2026 snapshots); no
  occupancy/seasonality of facilities.
- Dispute register (8 disputes) is a press/LCW-based census of
  documented events, not a claimed-complete sample.

## §4 What would change these entries (explicit trigger list)

- Official Atlas vector or attribute-bearing inventory → R-1 re-grade
  possible (requires pre-computation pin).
- Independent rainfall-linked hazard layer (Mussoorie pre-pinned) →
  R-1/R-3 re-exposure assessment.
- GPS-grade HEC observations at source → H3 could leave the D-3
  downgrade and be re-registered for a future freeze.
- n ≥ 15 disputes → H4 leaves EXPLORATORY under the same recipe.

## §5 Provenance / QA

- Every number above is copied from the hashed facts JSONs; QA pass:
  facts re-opened and hashes re-verified before this register was
  finalized (hash table in the evidence brief §6 and PROJECTSTATE §9).
- Register-file discipline: this file is analysis-of-record prose; it
  introduces **no new statistics** (the only later-dated fact set it may
  cite is the D-20 post-hoc sensitivity, labelled as such).

*End of register.*
