# Limitations — state these before anyone quotes a hectare

## Data

- **WorldCover 2021, Hansen 2000–2024, DEM and WDPA are not in the repo yet.**
  No real Jhabua screening result exists until those files are placed in `data/raw/`.
- WorldCover is a 10 m classified product; Hansen is a 30 m model. Both have their own
  errors and neither measures “woody biomass” directly.
- Hansen `lossyear` is binary. The screen treats any loss up to `start_year` as zero
  current canopy, which can overstate eligible area.
- Hansen ends in 2024; the configured start year is 2026. Removals in 2025–2026 are
  invisible.
- Sentinel-2 composites are 2024 and are used only for optional scoring indices, not
  for the eligibility rule.

## Rule interpretation

- The census route uses <10% pre-existing woody biomass (§4.3(8)(a), §6.2(1)).
  The 10-year rule in §4.4.2(1) is an **exclusion**, not the old v1.0 “non-forest for
  ten years” test.
- Hansen loss includes natural disturbance. §4.4.2(1) is about removal of woody
  biomass serving a similar purpose to the planting units; the raster proxy cannot
  distinguish causes.
- Shrubs/thickets can exceed 10% woody biomass without registering as tree canopy.
  With `shrubland: flag`, the direction of bias may be to overstate eligible area.
- Area-based mode is disabled until managed-forest/timber-harvest/native-ecosystem
  evidence exists.

## Scope

- No tenure, FPIC, PESA-FRA, safeguard or community-consultation assessment.
- No baseline, additionality, leakage or credit calculation.
- No field validation yet. Census-based projects also require a complete t0 census of
  planting units, GPS/markers, and ≤50 units/ha — none of that is represented here.
- The 30 m screen is for targeting fieldwork, not for registration or verification.
