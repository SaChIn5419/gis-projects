# P3 — H1 land-conversion analysis log (Wayanad)

Status: **H1 computed and reported.** Frozen design at R6; measurement spec =
dev-D-14 (pinned 2026-10-26, before any treatment/control comparison). This
file records the implementation mechanics and their QA evidence; any change to
a frozen rule or to D-14 is a §7 deviation-log entry.

**Information boundary (§5):** this is the first script that compares outcome
rasters between arms. Permitted because freeze R6 is recorded in
`../../docs/PROJECTSTATE.md` §9 and D-14 pinned the metric, geometry and test
battery before any arm difference was computed.

## Implementation — `scripts/p3_h1_analysis.py`

- **Units:** the 50 matched pairs (`data/processed/matched_pairs_2026-10-26.csv`,
  seed 20261022).
- **Treatment geometry:** pixel union of per-radius buffers (500 m primary;
  250 m / 1,000 m sensitivities) around **all verified facility points inside
  the treated parcel** (facility points = `facility_existence_universe_2026-10-23.csv`,
  same spatial join as `p2_match.py`; overlapping buffers counted once).
- **Control geometry:** buffer of the same radius around the centroid of the
  matched **control** parcel (D-14(i); controls have no facility point by
  construction).
- **Metric (D-14(ii)):** on the frozen 30 m grid, restricted to the matching
  eligibility mask (AOI ∩ ¬WorldCover-water ∩ ¬WDPA-all_touched ∩ ¬scar-v2),
  applied identically inside every buffer:
  - numerator = GLAD expansion pixels (class 1) whose CCI-2005 class is
    vegetated/cropland (families 10–12, 20–30, 40–50, 60–75, 100–180; all
    except urban 190 and water 210);
  - denominator = buffer pixels non-built at baseline (GLAD 2000: classes 0/1)
    with the same CCI restriction;
  - rate = numerator / denominator, %.
- **Tests (D-14(iii)):** paired t-test AND Wilcoxon signed-rank on
  d_i = treatment − control; Holm correction across the three radius tests,
  applied per test family.
- **Robustness (D-14(iv)) at 500 m:** (a) WorldCover-2021 strict built (same
  denominator) and (b) Hansen loss 2001–2024 clearing proxy (its own
  denominator: baseline pixels with Hansen 2000 tree cover > 0).
- **Stratum (D-14(v)):** the pre-existing-development stratum is reported
  **empty** — all 51 registry order dates are 2023–2026; imagery-based
  construction dating was not run. Labelled limitation.

### Measurement details (logged here; no rule changed)

1. **Grid congruence.** P1/P2 covariate layers sit on origin `584100, 1324500`;
   P3 outcome rasters on `584340, 1324380` (both 30 m, EPSG:32643). The offset
   is an exact multiple of 30 m in x and y, so pixel **edges coincide**; the
   eligibility mask is computed on the covariate grid and cropped to the
   outcome window (congruence asserted in code).
2. **CCI 2005 upscaling.** CCI ships at 300 m on the same origin; nearest
   upscale by exact 10× repeat → per-30 m-pixel family mask (no interpolation,
   no new information).
3. **Rasterisation rule.** All buffer geometries are rasterised with the
   pixel-centre rule (`all_touched=False`) identically on both arms.
4. **Robustness-(a) numerator** additionally carries the CCI vegetated/cropland
   restriction so numerator ⊆ denominator by construction — the consistent
   reading of D-14's "same denominator".
5. **QA fidelity metric.** Treatment geometry is a union of k facility buffers;
   the rasterisation-fidelity check therefore compares rasterised pixels
   against the true union area clipped to the grid (not against a single
   πr² circle, which would mis-flag multi-facility parcels).

## Results (`outputs/qaqc/p3_h1_facts_2026-10-28.json`)

| Radius | Treatment mean | Control mean | Mean diff | paired t (Holm) | Wilcoxon (Holm) |
|---|---|---|---|---|---|
| 250 m | 45.53 % | 21.52 % | **+24.01 pp** | p = 7.0e-08 | p = 4.5e-08 |
| **500 m (primary)** | **38.43 %** | **22.11 %** | **+16.32 pp** | **p = 1.7e-06** | **p = 6.5e-07** |
| 1,000 m | 32.84 % | 21.23 % | **+11.61 pp** | p = 1.8e-05 | p = 3.8e-05 |

All 50 pairs had non-zero denominators (no pairs dropped). The effect is
negative-monotone in radius (+24 → +16 → +12 pp), consistent with a
facility-localised conversion signal diluting with distance.

**Robustness (500 m):** WorldCover-strict-built diff **+5.24 pp**; Hansen
loss-proxy diff **+1.96 pp** — both signs agree with the primary run, as §3 H1
requires.

**Verdict by the frozen §3 rule:** treatment > control at every radius, both
tests significant after Holm correction, robustness directions agree → **H1 is
NOT falsified; the hypothesised direction is supported.** (Final claim language
belongs to the P5 evidence brief; nothing here is composited with other
categories.)

**Transition matrix (D-4 reporting, pooled 500 m, eligible pixels):** full
CCI-family × GLAD built-status (2000/2020) counts per arm are in the facts JSON
e.g. cropland 10–12: treatment 5,577 expansion px vs control 1,901 — the
dominant contribution to the contrast.

## QA gate

- Rasterisation fidelity: max |deviation| = **2.20 %** vs clipped geometry area.
- Zero-denominator geometries: **0**. Numerator > denominator violations: **0**.
- Treatment/control geometry overlap at 500 m: **0 px** (independent buffers).
- Pairs with missing facility points: **none**.

## Outputs

- `data/processed/h1_pair_rates_2026-10-28.csv` — per-pair numerators,
  denominators, rates and differences at all three radii.
- `outputs/qaqc/p3_h1_facts_2026-10-28.json` — tests, Holm-corrected p-values,
  robustness, transition matrices, stratum note, QA checks.

## Next

- H3 (HEC association) — hard data gate per D-3: audit the HEC incident-table
  availability first; downgrade path is frozen.
- H2 (hazard overlap) — needs the D-5 Atlas inventory decision (vector data
  not publicly available; bounded options remain — see
  `outputs/qaqc/d5d6_research_notes.md`).
- H4 (community-event overlap) — needs the structured event table compiled.
