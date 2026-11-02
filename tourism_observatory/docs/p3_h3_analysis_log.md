# P3 — H3 analysis log (Wayanad tourism_observatory)

**Hypothesis (H3, §4):** human–elephant conflict (HEC) incident hotspots aggregate
toward pre-2011 human-influenced, non-protected covariates (forest edge,
cropland, early forest loss, road access — and, as a secondary/LEAKY context
layer, 2000–2020 built-up gain).

**Status: computed 2026-11-02 under the D-3 registered DOWNGRADE (prereg §7
D-18, freeze R7d). Descriptive hotspot-overlap recipe only — no p-values, no
confidence intervals, no count model. The outcome below is a direction check,
not a test; H3 carries no falsification verdict under the registered recipe.**

---

## §1 Record-availability gate (R1 / audit-D-10 → D-18)

Frozen H3 §4 registered a count model (Poisson/NB, exposure = records per
cell, IRR + Moran's I on residuals). The R1 gate proved that this input class
cannot support it: the Morrison et al. (2025) GECCO 62:e03742 HEC records
**never carried GPS** — locations were recorded to village (place) name only,
and the paper simulated points by conditional random sampling. Place-massed
counts cannot be decomposed to cells without re-importing the paper's own
simulation, which would not be an independent observation. Therefore:

- **D-3 / D-18 registered fallback:** descriptive incident-hotspot surface
  (KDE, σ = 1,000 m, on 500 m cells), overlap with covariates expressed as
  record-weighted percentiles + Spearman ρ; **no p-values or CIs anywhere**;
  V2 direction check against the paper's stated drivers. All of this was
  pinned in §7 D-18 (freeze R7d, hash
  `943e9f9ce0c8367d6181f4d5a76a172c27836554dc0e5b833d216fd64e171174`)
  **before** any H3 outcome was computed.

## §2 Inputs (all ids in `data/manifest.json`, 31 entries)

| input | id / path | notes |
|---|---|---|
| Incident records | `h3_incident_records` → raw/staging_h3 xlsx (sha `c86dd642…`) | 4 sheets 2011–2014 |
| Author R code | raw/staging_h3 Code_to_pre-process.txt (sha `ac15d8a7…`) | parsing reference |
| Geocode cache | `h3_place_geocodes_2026-10-28` (sha `180bff99…`) | Nominatim/OSM, ODbL; **path pinned verbatim in D-18** |
| Hansen treecover 2000 | `hansen_treecover2000` | pre-period context |
| Hansen lossyear (derived) | `hansen_lossyear_32643` (sha `b2c788dc…`) | new prep, §10 |
| DEM | P1 grid dem_copernicus30m | covariate |
| WDPA | P1 wdpa_all_touched | protection mask (nodata-trap: 0 = outside WDPA) |
| CCI LULC 2005 | `cci_lulc_2005` | pre-2011 land-cover (bbox-clipped, district-masked in-script) |
| Built-up change | `builtup_change_2000_2020` (1=expansion) | **LEAKY secondary** |
| Roads | `roads_wayanad` gpkg (ODbL) | 2026 snapshot, vintage-caveated |
| Facility universe | `facility_existence_universe_2026-10-23` | tourism presence covariate |
| District | geoBoundaries ADM2 wayanad_boundary | AOI |

## §3 Screen (2011–2014)

- Sheets parsed: 2011: 446, 2012: 721, 2013: 890, 2014: 688 → **2,745 rows**.
- Dropped: **26 unparsable dates** (typo years 2101/0013/2027, epoch-null
  1970 rows), **15 outside the 2011–2014 window** → **2,704 kept**
  (2011-01-01 … 2014-12-24).
- Nature of lost: crop 2,377 · cattle 267 · attack 30 · property 19 · nil 11.
- Species: `ELP` 1,557 + `ELEPHANT` 244 (+ multi-tag rows) → **elephant flag
  TRUE for 2,018 rows**; next groups wild boar (167+), tiger (162+52), macaque,
  leopard. Construct-validity note (D-3 gate): records are a wildlife-risk
  register dominated by elephants, as the paper states.
- Structure: 367 unique place names + 58 sections across 4 ranges
  (Bathery, Kurichiat, Muthanga, Tholpetty). **The 2014 sheet has no Place
  column** (paper-side omission) — its 688 records geolocate via section /
  range only, which is why the range tier is the largest.

## §4 Geocoding (D-18 recipe)

- Nominatim, viewbox-bounded `75.70,11.40,76.50,12.02`, suffix
  ", Wayanad, Kerala, India", 1 req/s, local UA; tier order **place →
  section → range-centroid** (range centroid from median of matched records
  per range).
- Cache `h3_place_geocodes_2026-10-28.csv`: **425 unique (name, tier) pairs
  (367 place + 58 section), 99 matched** by Nominatim; unmatched names fall
  to the range tier at assign-time.
- **Record-level placement: 2,704/2,704 placed, 0 unplaced** — tiers:
  place 1,089 · range 1,043 · section 572. Precision is per the D-18 tier
  design: unmatched places/sections are serious precision loss (≈1,600
  records at range centroid = ~40 km ambiguity) and this is recorded as a
  **treat-with-care caveat on every surface below** (the surface is a
  place-name hotspot surface, not an incident map).

## §5 Incident hotspot surface

- Grid: 500 m cells over the district envelope → **8,112 cells in district**
  (4,423 outside WDPA = sensitivity subset).
- KDE: Gaussian, **σ = 1,000 m**, each record weighted 1 (aggregated at its
  place point), neighbours summed; surface converted to a percentile rank for
  all overlap reads. No cell weighting beyond record counts.

## §6 Overlap — primary (all 8,112 cells; record-weighted percentile reads)

Reported values: `mean_pct_at_top_decile` = record-weighted mean of the
incident-KDE percentile among the covariate's top-decile cells
(0.5 = district-median incident density); `rho` = Spearman ρ between
covariate cell value and incident density. **No tests, by recipe.**

| covariate (pre-2011 primary) | mean_pct@top-decile | share>median | ρ |
|---|---|---|---|
| forest edge density | 0.457 | 0.43 | **+0.038** |
| forest cover share | 0.405 | 0.39 | **−0.178** |
| cropland share | 0.509 | 0.19 | +0.064 |
| urban share 2005 | 0.501 | 0.0025 | +0.023 |
| forest loss 2001–2010 | 0.468 | 0.10 | +0.039 |
| road density (2026 proxy) | 0.407 | 0.34 | +0.064 |
| elevation | 0.660 | 0.80 | +0.004 |
| facilities within 1 km | 0.497 | 0.10 | −0.015 |
| built-up gain 2000–2020 (LEAKY) | 0.456 | 0.58 | +0.104 |

**Reading.** Every human-modification covariate is *signed positively* in the
global sense (ρ > 0) — but the magnitudes are tiny: edge +0.038, cropland
+0.064, roads +0.064, early forest loss +0.039. Forest **cover** share is
strongly negative (−0.178): the incident hotspot surface sits *off* dense
forest — consistent with incidents being reported where people and crops are.
Covariate top-decile cells average at or slightly above/below the district
median incident percentile (0.41–0.51), i.e., high-covariate cells are **not**
niche-shifted incident hotspots in any operationally meaningful way.

## §7 Sensitivities

- **Outside-WDPA only (4,423 cells):** all signs preserved vs primary except
  elevation (+0.004 → −0.043) and facilities (−0.015 → −0.058) — both
  numerically indistinguishable from zero. Edge +0.046, cropland +0.052,
  roads +0.025, loss +0.075, forest cover −0.051. The D-18 rule (wait for
  *both* arms before any claim) terminates the same way: **no measurable
  directional claim survives; the only stable feature is the negative
  forest-cover association**, which outside WDPA attenuates to −0.051.
- **Elephant subset (2,018 records):** indistinguishable from all-records
  (edge +0.067, cropland +0.094, forest cover −0.218, facilities +0.013,
  roads +0.070, loss +0.047). The elephant-dominance of the register does not
  mask a different spatial signal; the surface is elephant-driven but
  weakly differentiated.

## §8 V2 direction check vs paper-stated drivers

The paper (C1, Morrison et al. 2025) states negative-HEI concentration around
the sanctuary landscape / forest edge (season-dependent) with cropland
context. Our V2 check: forest-edge ρ = +0.038, top-decile incident percentile
= 0.457 (at the district median). **Descriptive support for an edge
concentration is fragile at best** — the signed direction matches, the
magnitude does not support any operational claim. Under the D-18 recipe this
is the registered *descriptive* answer; the paper's higher-resolution signal
came from simulated points, which our geocoded village massing cannot
reproduce (that inability is exactly why D-3 downgraded H3).

## §9 Outcome of record

**H3 is reported as descriptive under D-18 and carries no falsification
verdict.** The registered direction-check conclusion: (i) the incident
hotspot surface does not contradict the human-influence direction (every
pre-2011 human-modification covariate is signed positively); (ii) it is
operationally *near-null* in magnitude after Village/Range-mass geocoding
(|ρ| ≤ 0.07 for all pre-2011 covariates except the negative forest-cover
association, −0.178); (iii) forest-cover share is the only stable
directional feature across all three arms (−0.178 / −0.051 / −0.218) —
incident mass sits in non-forest, human-modified land. The facility-proximity
covariate is null in every arm (−0.015 / −0.058 / +0.013): the incidental
2011–2014 register gives no support to a "tourism attraction" proximity
signal — same direction as the H2 register reading, not a new mechanism.

## §10 Governance / compute record

1. **Host-restart interruption:** the H3 run started 2026-10-28 under the
   D-18 pin, was killed by a host restart mid-geocode (150/425 names cached),
   and was resumed 2026-11-02 from the same D-18-pinned cache file
   (`h3_place_geocodes_2026-10-28.csv` — path already frozen pre-marathon,
   so no re-pin or re-hash of the *pin* was needed; the file itself was
   hashed post-completion, `180bff99…`).
2. **Pre-outcome bug fixes (both stages fixed before any overlap output
   existed):** (a) `str.contains` without `na=False` manufactured NA in the
   elephant mask; (b) an index misalignment between the filtered frame and
   the concat ax injected 40 NaN pseudo-rows (which had inflated the placed
   count and would have degraded the KDE). Neither bug reached an outcome —
   the first two launch attempts crashed at the KDE stage before the overlap
   block ran and no facts JSON existed at that point.
3. **Missing covariate raster:** the D-18-pinned covariate list included the
   mean loss-year surface, which P1 never materialised (only treecover-2000
   and a binary loss mask existed). Prep script `p3_prep_lossyear.py`
   (sha `936be90b…`, QC: 93,050 px / 8,374.5 ha, years 1..24) warps the
   existing manifest raw tile (`hansen_gfc2024_lossyear_20n070e`) onto the P1
   grid; the derived artifact is manifest entry `hansen_lossyear_32643`
   (sha `b2c788dc…`). This precedes all outcomes; frozen D-18 covariate list
   unchanged (loss was a pinned covariate whose grid realization was absent).
4. **Input-name correction:** the script originally opened a raster filename
   that does not exist (`glad_glcluc2020_builtup_change_32643.tif`); corrected
   to the run-of-record artifact `builtup_change_2000_2020_32643.tif`
   (same semantics: 1 = expansion). Also pre-outcome.
5. Run of record: `scripts/p3_h3_analysis.py` sha
   `7d2c4b684cef198ee78f009c2c23bb9074358e2e8174c13d876fab170fadadc7`; facts
   `outputs/qaqc/p3_h3_facts_2026-11-02.json` sha
   `dd73bddb6e457f0b766dd98a20fd5567fe187e1629bc379ea64a45bacb1bcb40`.

## §11 Caveats (carried to the evidence brief)

- Village-level geocoded massing; the surface is a place-name hotspot
  surface, not a point process — no GPS exists at source (audit-D-10).
- Records cover 2011–2014 only (the paper's record window).
- No Poisson/NB/IRR/residual Moran's I, no p-values/CIs — by registered
  design (D-18), not by choice of convenience.
- Road density uses the 2026-10 OSM snapshot (post-window accessibility
  proxy, vintage-caveated); facility universe is current-existence, likewise
  vintage-caveated.
- Seasonal rainfall: no raster exists in the data audit — covariate
  unavailable, documented, not silently dropped.
- Built-up gain 2000–2020 is LABELLED-LEAKY secondary (window ends 2020, not
  pre-2011); primary interpretation uses pre-2011 covariates only.
- Documentation/effort bias: records are forest-department compensation
  registers — reporting effort concentrates near roads and range offices;
  part of the hotspot shape reflects access, not incidence (H4 carries the
  same family of caveat).
