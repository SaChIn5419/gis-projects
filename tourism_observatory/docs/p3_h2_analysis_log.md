# P3 H2 analysis log — Wayanad (2026-10-28)

Status: **H2a complete, run 2 (D-17a refetch)** — registered + D-16 corrected
inference, verdict below and updated in §8; H2b registers follow in the same
log. Governance: prereg §7 D-15 (input substitution, pre-computation), §7
D-16 (sign-test defect, correction registered pre-computation), §7 D-17
(coverage-window error found by extent audit, correction + rerun ordered
before H2b); freezes R7b/R7c. §3 H2 text byte-unchanged throughout.
Sections 3–7 report the **first run, superseded by the D-17a refetch** and
retained verbatim for audit; the run of record is §8.

---

## 1. Input substitution (D-15, logged before any H2 statistic)

The frozen H2a(ii)/H2b(b) input — the ISRO Landslide Atlas **vector**
inventory — does not exist in any obtainable public form: PDF only
(data-audit D-5), Bhuvan WFS disabled (2026-10-23), GetFeatureInfo returns
empty GML at every probe *including* coordinates where GetMap visibly renders
polygons, capability Abstracts empty for all six candidate Kerala layers.
An earlier "byte-identical across six layers" finding was retracted the same
day: it was a WMS 1.3.0 `CRS=EPSG:4326` lat,lon axis-order bug (correct
protocol: WMS 1.1.1 + `SRS=EPSG:4326`, lon,lat BBOX).

**Substitution (user decision 2026-10-28):** polygonized 10 m tiled GetMap
renders of `disaster:kl_landslides_new` →
`data/processed/inventory_wms_kl_landslides_new_32643.gpkg` (first run:
1,151 polygons, 29.82 km² over the D-15 window; **superseded by the D-17a
district-complete refetch: 990 polygons, 24.061 km² — see §8**; QA
`outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json`). Registered test family
**unchanged** (H2a Holm within {i,ii}; H2b descriptive (a)+(b)). Measurement
recipe pinned in D-15 before computation.

Validity caveats carried into every statement below:

1. No feature attributes or dates are retrievable — layer selection criteria
   and vintage are undocumented (capabilities `<Abstract/>` empty).
2. The Jul-2024 Chooralmala–Mundakkai event is absent from **all six**
   candidate layers (≤0.5 % of the digitized VAP8 scar covered) — the proxy
   predates or excludes it. Georeferencing is validated instead by: BBOX
   honoured (disjoint renders → disjoint content), all 1,151 polygons inside
   the district, 7 proxy polygons within 500 m of the VAP8 scar (2 touching).
3. Boundary precision ±10 m (10 m pixels).
4. Documentation bias presumed (mapped-landslide density near roads and
   settlements), as in any inventory.

## 2. Domain and draws (D-15 pins)

- Eligible placement domain (hazard-free): 2,020 1 km parcel-grid cell centres
  → **876 eligible** after (i) AOI ∩ ¬WDPA(all_touched) ∩ ¬water (WorldCover
  80/90 ∪ CCI-210), (ii) ≤2,000 m from OSM road ≥ tertiary, (iii) CCI-2005 ≠ 190,
  (iv) elevation within the facility [5th, 95th] percentile band **[736, 917] m**.
- Observed facilities: **107/107** verified points evaluable (same set as H1).
- Nulls: 1,000 rejection-sampled draws per facility, one
  `default_rng(20261022)` stream over facilities sorted by `facility_id`,
  calipers elevation ±150 m and road-distance [0.6, 1.4]·d (nearest ≥
  tertiary road). Caliper pool size min/median **15/71**; pool size does not
  correlate with |percentile − 0.5| (|r| = 0.006), so small pools do not drive
  the percentile results.
- KDE (ii): proxy polygons rasterized as area fractions on the frozen 30 m
  grid, Gaussian σ = 500 m, 3σ truncation; surface stored as
  `outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif` (QA gate reopened the
  actual GeoTIFF).

## 3. Registered results (D-15 convention — run 1, superseded by D-17a; retained verbatim)

From `outputs/qaqc/p3_h2a_facts_2026-10-28.json`, key `tests`:

| stat | mean percentile | signs (+/−/tie) | p_sign_raw | p_holm |
|---|---|---|---|---|
| (i) slope ≥ 25° | 0.503 | +1 / −35 / 71 | 1.08e-09 | 2.15e-09 |
| (ii) KDE density | 0.5611 | +36 / −71 / 0 | 9.23e-04 | 9.23e-04 |

Descriptive (i): observed share on slope ≥25° = 0.009 (1 facility, F027 at
27.6°, its own null share 0.0) vs mean null share 0.003.

**These two sign-test p-values are not interpretable — see §4.**

## 4. Defect in the registered sign test (D-16 proof)

Inspecting the incoherence (mean percentile 0.503 vs signs −35/+1) exposed an
analytical defect in the D-15(d) convention, valid in either direction and
independent of the observed results: under exchangeability of the observed
point with its null draws, a **point-massed** metric does not give
P(sign +) = 0.5.

- **(i) binary**, per-facility null probability q ≈ 0.003: among non-ties,
  P(+) = q. Expected positives ≈ 107·q ≈ 0.35 — the observed **+1 is exactly
  the null expectation**; the 35 negatives are what H0 predicts, not evidence
  against it. The registered p = 2.15e-09 is an artifact of testing against
  50/50 when the convention's own null is ≈0.3 %.
- **(ii) zero-inflated**, pool zero-fraction π₀ ≈ 0.66: H0 gives
  P(+) = 1−π₀ ≈ 0.34, P(−) = π₀ ≈ 0.66. Expected split ≈ **+36/−71 — exactly
  the observed split**. Registered p = 9.23e-04 is likewise an artifact.

The midrank **mean** percentile is unaffected (E = 0.5 under H0 by the same
algebra) and remains reportable. Timing disclosure: discovered on inspecting
the first computation; the derivation does not depend on any result's
direction, and no outcome determined the choice of correction. D-16 was
written to prereg §7 and the prereg re-hashed (R7b) **before** the corrected
tests were computed.

## 5. Corrected family inference (D-16, registered before computation)

The correction is the test form already frozen in §3 H2 itself: *Monte Carlo
observed-vs-null exceedance p-value*. T_obs at the 107 observed facilities vs
T_j at the j-th matched null draw of every facility (same deterministic
seeded draws), p = (1 + #{T_j ≥ T_obs})/1001, Holm across {i,ii}.

| stat | T_obs | null T_j mean | null T_j p95 | p_raw | **p_holm** |
|---|---|---|---|---|---|
| (i) count on slope ≥25° | 1 | 0.355 | 3 | 0.293 | **0.293** |
| (ii) mean observed KDE density | 0.0012524 | 0.0004923 | 0.0009179 | 0.01199 | **0.02398** |

Facts key: `corrected_tests_D16`. Registered outputs (§3) retained verbatim in
the same file with `registered_sign_tests_status` = non-interpretable.

## 6. H2a verdict (frozen §3 rule: *falsified if observed overlap ≤ null
expectation*)

- **(ii) Atlas-inventory density — the "Atlas mapped landslides" component of
  H2: observed overlap 0.001252 EXCEEDS null expectation** (null mean
  0.000492, p95 0.000918), corrected exceedance **p_holm = 0.024** →
  **not falsified**; the registered claim "more than expected under
  terrain-matched random placement" holds on this statistic.
- **(i) slope ≥25° share:** observed count 1 vs null mean 0.355 →
  directionally above (so the "≤ null" falsification condition is not met)
  but not significant (p_holm = 0.29) → **no detectable slope-share
  preference**; contributes no support.
- **Overall H2a: NOT falsified**, resting on the significant (ii) result;
  (i) is a non-significant directional excess.

Interpretation guard (frozen D-2): this is a **siting-preference** result
only — facilities are placed in higher landslide-inventory-density terrain
than elevation- and road-access-matched random locations. It is *not* an
exposure or risk claim; exposure claims require H2b. It is also not a
susceptibility score and never substituted for an occurrence probability.
Residual confounds: the inventory proxy's undocumented vintage/selection,
its documentation bias (partially mitigated by the road-distance caliper),
and its exclusion of the Jul-2024 event.

## 7. Artifacts and hashes (run 1, superseded by D-17a; files overwritten in place — data artifacts are gitignored, so the audit trail is these hashes + the PROJECTSTATE/manifest records)

| file | sha256 (first 16) |
|---|---|
| `outputs/qaqc/p3_h2a_facts_2026-10-28.json` | `25968f6e6e621b51` |
| `data/processed/h2a_facility_percentiles_2026-10-28.csv` | `25ef81f4479d65f3` |
| `outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif` | `7bb4c5318023e3a1` |
| `scripts/p3_h2a_analysis.py` | `e2bab79c8df4fc820` |
| `data/processed/inventory_wms_kl_landslides_new_32643.gpkg` | `4411b9bb7a238dcf` |
| `outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json` | `1e95024dd8fb8d97` |

Inputs of record: `facility_existence_universe_2026-10-23.csv` (107 verified),
`roads_wayanad_32643.gpkg` (≥tertiary), `parcels_1km_32643.gpkg`,
`aoi_mask_32643.tif` (frozen 30 m grid), `slope_deg_32643.tif`,
`dem_copernicus30m_32643.tif`, `worldcover_2021_32643.tif`,
`wdpa_all_touched_32643.tif` (note: nodata=0 declared but 0 = outside WDPA),
`cci_lulc_2005_32643.tif` (300 m, sampled by coordinates).

## 8. D-17a refetch + rerun (2026-10-28) — run of record

An objective extent audit (run while preparing H2b) found the D-15 fetch
window `75.75–76.47 E / 11.20–11.82 N` truncated the district
(`75.7742–76.4443 E / 11.4515–11.9781 N`) against its **north edge**, where
16 of the 107 facilities lie. Logged as prereg §7 D-17 (freeze R7c, written
before the refetch); no outcome value entered the discovery. The inventory
was refetched over the district-complete window `75.75–76.47 E / 11.42–12.00 N`
(same layer/protocol/10 m/50 %-overlap recipe, 72 tiles, script byte-unchanged
except the BBOX constant + de-hardcoded QA note), and `p3_h2a_analysis.py` was
rerun **unchanged** (same seed, same calipers, same D-16 corrected tests).

Refetch QA: **990 polygons, 24.061 km², all inside the district**; **229
polys (3.568 km²) north of 11.82 N** — the strip the first window missed;
VAP8 check reproduced (2 intersecting, 7 within 500 m, 0 touching; 1.48 %
scar coverage — the Jul-2024 event is still absent, as in run 1).

Run-2 registered outputs (D-15 convention, non-interpretable per D-16):
(i) mean pct 0.503, signs +1/−35, p_holm 2.15e-09 (artifact);
(ii) mean pct 0.579, signs +44/−63, p_holm 0.0814 (artifact).

**Run-2 corrected family inference (D-16, the verdict basis):**

| stat | T_obs | null T_j mean | null T_j p95 | p_raw | **p_holm** |
|---|---|---|---|---|---|
| (i) count on slope ≥25° | 1 | 0.355 | 3 | 0.293 | **0.293** |
| (ii) mean observed KDE density | 0.0029206 | 0.0011454 | 0.0021635 | 0.006993 | **0.01399** |

**Run-2 H2a verdict: NOT falsified — unchanged, now on the district-complete
inventory.** (ii) strengthens: T_obs 0.002921 vs null mean 0.001145 (run 1:
0.001252 vs 0.000492), exceedance p_holm 0.024 → **0.014**; (i) unchanged
(p_holm 0.293). All interpretation guards of §6 carry over verbatim.

Run-2 hashes (files of record; run-1 hashes in §7 retained above):

| file | sha256 (first 16) |
|---|---|
| `outputs/qaqc/p3_h2a_facts_2026-10-28.json` | `f34327954bdd76c9` |
| `data/processed/h2a_facility_percentiles_2026-10-28.csv` | `3214370aa6b1e6fd` |
| `outputs/qaqc/p3_h2a_kde_inventory_500m_32643.tif` | `c9a1c6af71736388` |
| `scripts/p3_h2a_analysis.py` | `e2bab79c8df4fc820` (unchanged) |
| `data/processed/inventory_wms_kl_landslides_new_32643.gpkg` | `c12ee632fe7da200` |
| `data/raw/staging_h2/kl_landslides_new_wayanad_mosaic_10m.tif` | `17938cee277734df` |
| `outputs/qaqc/h2_wms_inventory_facts_2026-10-28.json` | `4eb2712f6307cf9b` |

## 9. H2b registers (2026-10-28) — descriptive exposure, frozen (a)+(b)

Recipe exactly as frozen (D-2 H2b + D-15 pins): register of **facilities,
buildings (Google Open Buildings + OSM) and OSM roads intersecting** (a) the
published 2024 Chooralmala–Mundakkai scar footprint and (b) 1 km buffers
around the proxy inventory polygons. No p-values, no null models — H2b is a
descriptive register by design. Every entry carries the footprint-source
precision class; spatial uncertainty is the count range under a footprint
boundary perturbation of ± the class's positional uncertainty
(a: ±15 m georeferencing; b: ±10 m = 1 WMS pixel).

Building sources: Google Open Buildings v3 (streamed from Google's bucket,
level-6 S2 cells 3ba5/3ba7/3ba9/3baf, raw gzip sha256 hashed in flight;
636,445 footprints in district+pad, confidence 0.650–0.966, CC BY 4.0,
imagery ≤ May 2023) + OSM re-extracted under D-17b (69,126, ODbL).

**(a) 2024 scar footprint** (1.781 km²; precision class: digitized NRSC
impact-map outline, VAP3 31-Jul-2024, ~1.6 m/px, graticule georef ±15 m):

| register | count | uncertainty (±15 m) |
|---|---|---|
| facilities (of 107) | **0** | [0, 0] |
| buildings, Google | **0** | [0, 0] |
| buildings, OSM | **0** | [0, 0] |
| OSM roads | 1 segment, **0.758 km** (class `construction`) | [0.720, 0.835] km |

The mapped 2024 scar contains **no mapped built stock and no facilities** —
the debris-flow corridor is an unpopulated ridge; the only mapped line
feature crossing it is a construction-class track. Exposure in the register
sense is zero; this is a fact about the mapped stock, not a risk statement.

**(b) 1 km buffers around the mapped inventory** (union 992.9 km² = **46.6 %**
of the district's 2,132 km²; precision class: WMS-render polygonized, 10 m px,
±1 px boundary, no attributes/vintage — the proxy **excludes the Jul-2024
event**):

| register | count | uncertainty (±10 m) |
|---|---|---|
| facilities (of 107) | **26** (ids in register CSV) | — (point set, no boundary sensitivity) |
| buildings, Google | **73,027** (57,291 with confidence ≥0.7; 5.65 km² footprint area inside) | [71,980, 74,050] |
| buildings, OSM | **10,389** (1.45 km²) | [10,242, 10,521] |
| OSM roads | 3,184 segments, **1,370.055 km** (residential 433.1, unclassified 402.8, track 201.8, secondary 94.7, tertiary 66.0 km) | [1,355.112, 1,384.882] km |

Reading guard: the buffer union covers **46.6 % of the district**, so these
raw counts are *not* "more than expected by area proportion" and H2b makes
no such claim (no comparative test is registered here); the 26/107 facilities
inside the buffers is a plain register count. Documentation bias (mapped-
landslide density near roads/settlements) inflates the road/building counts
relative to true landslide proximity; building vintages mix pre-event stock
(GOB, imagery ≤ May 2023) with a mixed-vintage 2026-10 OSM snapshot. The
inventory proxy and the 2024 scar cover **different event populations** and
must never be merged into one exposure number. Interpretation guard (D-2):
counts are exposure of the *mapped* stock inside *mapped* footprints — never
risk, never a susceptibility score.

Artifacts (2026-10-28): `outputs/qaqc/p3_h2b_facts_2026-10-28.json`
(`e50ae8bd1701360f…`), `outputs/qaqc/h2b_facility_exposure_register_
2026-10-28.csv` (`550d63506551b0e1…`, 26 rows),
`scripts/p3_h2b_analysis.py` (`6686efe77b3cba9a…`),
`scripts/h2b_fetch_google_buildings.py` (`56001bcf4d84387c…`),
`data/processed/buildings_google_wayanad_32643.gpkg` (`d8ea52b199289347…`,
manifest entry `buildings_google_wayanad`).
