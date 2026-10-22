# Case study — Land screening for agroforestry in Jhabua, Madhya Pradesh

**Independent project.** Not affiliated with, commissioned by, or endorsed by any
company or organization. Public data only. Pre-feasibility only — no carbon-credit
forecasts, no eligibility determinations.

## 1. The question

I asked a deliberately hard screening question: on a 30 m grid, using only free public
data, how much of an Indian district could plausibly be *candidate* land for an
agroforestry restoration project under the VM0047 ARR (Agriculture, Forestry and
Reforestation) census route — and, critically, **what can that number honestly be
called?**

## 2. The method

A config-driven, fully reproducible pipeline (Python, rasterio, geopandas, numpy,
scipy), structured as four stages:

1. **Ingest six public sources onto one shared 30 m grid** (EPSG:32643):
   ESA WorldCover 2021 v200, Hansen GFC 2024 v1.12 (treecover/loss/gain),
   Copernicus DEM GLO-30, WDPA Oct-2026 (India), Sentinel-2 2024 composites,
   geoBoundaries ADM2. Missing sources **stop the pipeline** — no zero-filling.
2. **QA gate (19 checks)**, measured on the actual rasters: identity, coverage,
   plausibility and area reconciliation (raster district hectares vs vector district
   hectares within tolerance). Hard failures block the analysis.
3. **Two-stage exclusion waterfall with per-pixel reason codes.** Stage A applies
   methodology validity gates (VM0047 §4.3(8)(a)/§6.2(1) <10% pre-existing woody
   biomass; §4.4.2(1) recent-removal exclusion). Stage B applies design screens
   (built-up/water/wetland; protected areas; steep slope; operable patch size).
   Every excluded pixel carries exactly one documented reason code; "first failing
   rule wins" makes the attribution auditable.
4. **A measured zero is a result, not a gap.** The recent-removal screen removes 0 ha
   because only 12 aligned 30 m pixels in the district carry any Hansen loss
   (latest year 2010). That is evidence, and it is reported as such.

## 3. The result

| Waterfall step | Removed (ha) | Remaining (ha) |
|---|---:|---:|
| District (Jhabua ADM2, EPSG:32643 @ 30 m) | — | 343,380.6 |
| Pre-existing woody biomass ≥10% (Stage A) | 19,286.6 | 324,094.0 |
| Recent woody removal ≤10 yr (Stage A) | 0.0 | 324,094.0 |
| Built-up / water / wetland (Stage B) | 4,300.2 | 319,793.8 |
| Cropland exclusion (Stage B) — **off by design, census route** | 0.0 | 319,793.8 |
| Protected areas (WDPA, any polygon) (Stage B) | 68,149.1 | 251,644.7 |
| Steep slope >20° (Stage B) | 144.2 | 251,500.5 |
| Patches <1 ha (Stage B) | 207.7 | **251,292.8 (candidate)** |
| Candidate carrying ≥1 confidence flag | — | 197,590.4 |

The four maps in `outputs/maps/` (study area, reason codes, waterfall, candidate
close-up) are rendered from the same rasters that produced these numbers — no
hand-copied values.

## 4. What the 73.2% figure means (and does not mean)

The candidate is 251,292.8 ha — 73.2% of the district. The two design decisions that
produce that magnitude:

- **Census mode keeps cropland.** §4.3(8)(b) and §6.2(2) place continuous cropping
  inside the census route, so cropland (60.6% of the district) stays in the pool.
- **The WDPA screen is deliberately conservative.** Every WDPA polygon is excluded,
  including multiple-use designations such as Reserve/Protected Forest, not just
  IUCN I–IV. This intentionally over-excludes and trades area for defensibility.

Therefore the correct reading is: *a targeting pool for fieldwork*, never a project
boundary, never an eligibility claim, and never a carbon estimate.

## 5. Limitations I would state before quoting any number

- 30 m grid: pixel-level uncertainty ±0.09 ha; suited for targeting, not registration.
- Hansen is a 2000–2024 model at 30 m and woody biomass is only a proxy (canopy % and
  WorldCover classes); shrub thickets can exceed 10% woody biomass without registering.
  The screen flags, does not penalize, shrubland candidates.
- Hansen ends 2024 while the (hypothetical) start year is 2026; 2025–2026 removals
  are invisible and reported as a limitation.
- No tenure, FPIC, PESA/FRA, safeguard, baseline, additionality or leakage
  assessment. No field validation. Sentinel-2 composites are a backdrop, not a rule.
- The district boundary (geoBoundaries ADM2) includes a small detached southwestern
  component, which is kept, not silently dissolved.

## 6. What I would do next

1. Run the **WDPA IUCN I–IV sensitivity** — a one-line config change that moves tens of
   thousands of hectares and sharpens the WDPA narrative.
2. Woody-threshold sensitivity (10% vs 15%+) and shrubland exclude-vs-flag.
3. A QGIS `.qgz` project so reviewers can inspect `reason_codes.tif` against imagery.

## 7. Reproduce

```bash
python -m pip install -r requirements.txt
python src/ingest.py config/jhabua.yaml
python src/qaqc.py --check config/jhabua.yaml
python src/screening.py config/jhabua.yaml
python scripts/make_maps.py config/jhabua.yaml
python -m pytest -q
```

Provenance for every source (URL, version, tile, SHA256, acquisition date) is in
`data/manifest.json`. Raw data is never redistributed.

## 8. CV bullets (ready to paste)

- Built an independent, config-driven 30 m GIS screening of agroforestry candidacy for a
  3,434 km² Indian district using only public data (ESA WorldCover, Hansen GFC, Copernicus
  DEM GLO-30, WDPA Oct-2026, Sentinel-2, geoBoundaries) on a single aligned EPSG:32643
  grid, with a 19-check measured QA gate and per-pixel reason-code audit trail.
- Reproduced a VM0047-style two-stage exclusion waterfall: 343,380.6 ha → 324,094.0 ha
  methodology-eligible → 251,292.8 ha candidate, with every exclusion attributed to its
  first failing rule and 100% reconciliation between the raster, the CSV and the maps.
- Diagnosed and fixed three production-grade failure modes during the build — wrong
  Hansen tile latitude band (20N vs 30N), NaN nodata propagation in Sentinel-2 reads,
  and Matplotlib `imshow` extent ordering — each now guarded by an automated check.
- Cut a once-only screen into a teaching artifact: a 12-module GIS training manual and a
  hands-on notebook that re-implements the entire screen from scratch and verifies it
  byte-for-byte against the pipeline outputs.
