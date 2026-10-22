# Limitations — what this screen does and does not claim

This is an **independent pre-feasibility screen**. It is not an Equilibrium Earth
project, not a project design, and not a carbon-credit forecast. Do not quote any
ha figure as a project boundary or an eligibility determination.

## Data

- The screening stack is a **30 m approximation**, built from:
  - ESA WorldCover 2021 v200,
  - Hansen GFC 2024 v1.12,
  - Copernicus DEM GLO-30,
  - WDPA Oct 2026 (India),
  - geoBoundaries 2.0.1 India ADM2,
  - Sentinel-2 2024 composites.
- WorldCover is a 10 m classified product; Hansen is a 30 m model. Both have their
  own errors and neither measures “woody biomass” directly.
- Hansen tree cover is sparse in Jhabua: only **2,441** aligned 30 m pixels inside
  the district have ≥10% tree cover. This is a genuine limitation of the Hansen
  proxy in a dry, patchy landscape, not an ingest bug.
- Hansen loss is also sparse inside the district: **12** aligned 30 m pixels with
  nonzero loss, with the maximum loss year 2010. The recent-removal screen is
  therefore **zero in this run** because the evidence, as measured, is zero.
- Hansen ends in 2024, while the configured start year is 2026. Removals in
  2025–2026 are invisible.
- Sentinel-2 composites are 2024 and are used only for map backgrounds and optional
  scoring; they do **not** drive the eligibility rule.

## Screens

- The **WDPA screen uses all polygons**, including Reserve Forest and Protected
  Forest designations, not only IUCN I–IV. This is deliberately conservative and
  over-excludes some multiple-use forest. It should be read as a design screen, not
  as a statement that all of those areas are legally unavailable.
- Census mode **keeps cropland**, so the candidate area is much larger than an
  actual project boundary. This is intentional in the config; the candidate is a
  search space, not an approved project area.
- Hansen `lossyear` is binary. The screen treats any loss up to `start_year` as
  zero current canopy, which can overstate eligible area where loss happened under
  a different land use.
- Shrubs/thickets can exceed 10% woody biomass without registering as tree canopy.
  With `shrubland: flag`, the direction of bias may be to overstate eligible area.
- Area-based mode is disabled until managed-forest/timber-harvest/native-ecosystem
  evidence exists.
- The 10-year rule in §4.4.2(1) is a census exclusion, not the old v1.0 “non-forest
  for ten years” test.

## Scope

- No tenure, FPIC, PESA-FRA, safeguard or community-consultation assessment.
- No baseline, additionality, leakage or credit calculation.
- No field validation yet. Census-based projects also require a complete t0 census
  of planting units, GPS/markers, and ≤50 units/ha — none of that is represented
  here.
- The 30 m screen is for targeting fieldwork, not for registration or verification.
- The district boundary is geoBoundaries ADM2; it includes a small detached
  component at the southwest. Both parts are included in the mask.
