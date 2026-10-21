# Assumptions — verified against Verra VM0047 v1.1 (14 May 2025)

**Source checked:** `verra-verify/vm0047_v11.pdf`
**SHA256:** `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`
**PDF:** 81 pages, 1,171,574 bytes. Clause numbers below were read from that file.

## 1. The rule the screen implements

The project uses the **census-based** approach. VM0047 v1.1 §4.3(8) says the project
activity occurs:

> a) within an area with less than 10% pre-existing woody biomass cover; and/or
> b) in an area subject to continuous cropping, or in “settlements” or “other lands”
> land use categories.

§6.2 then states the census crediting baseline requires the project activity to:

> 1) occur within an area with pre-existing woody biomass cover of less than 10%; and
> 2) occur in an area subject to continuous cropping, or in “settlements,” or “other
> lands” land use categories.

The code treats `WOODY_COVER` as a Stage-A methodology filter: pixels with
`treecover2000 >= 10%` **or** WorldCover tree/mangrove are excluded. Cropland is not
itself a Stage-A exclusion; it is a design choice. That is conservative: a cropland
pixel with ≥10% woody cover is still excluded by the woody test.

## 2. The 10-year rule that is real — and what it is not

VM0047 v1.1 §4.4.2 (Census-based Approach Exclusions) says the methodology is not
applicable where:

> 1) Woody biomass, which serves a similar purpose as the planting units in the project,
> has been removed within the last 10 years (confirmed via pre-project photos and/or
> attestation).
> 2) Soil disturbance from the project activity involves soil inversion to a depth
> exceeding 25 cm.

So the 10-year look-back **is** a v1.1 rule, but it is an **exclusion**, not the
eligibility test. The old v1.0 “non-forest for at least 10 years” rule is still wrong
and is not used. The code implements §4.4.2(1) as `RECENT_WOODY_REMOVAL`, using Hansen
loss where `treecover2000 >= 10%` as a proxy.

This proxy has two limitations:

- Hansen loss is a binary annual disturbance flag. A pixel that lost some cover is
  treated as zero current canopy in `woody_mask()`, which can overstate eligible area.
- Hansen loss includes natural disturbance (fire, drought), while §4.4.2(1) is about
  removal of woody biomass that serves a similar purpose to the planting units. The
  proxy may exclude pixels that were not project-driven removal.

## 3. Area-based mode is explicitly disabled

The area-based route is **not** a switch that only changes cropland handling. §1.1 and
§4.4.1 require evidence that:

- the land is non-forest, or existing forest has not been managed for wood products in
  the past ten years; and
- clearing pre-existing woody biomass did not involve timber harvesting or degradation
  of native ecosystems; and
- planting density does not silently use the census route (<50 units/ha).

The repository has no managed-forest, timber-harvest or native-ecosystem dataset.
`screening.validate_config()` therefore raises `NotImplementedError` for
`eligibility_mode: area`. No area-mode hectare figure may be reported until those
layers and tests exist.

## 4. Reason codes — single canonical table

These are the codes written by `src/screening.py` and checked by `src/qaqc.py`.
They replace the earlier scaffold’s table, which had codes 3–6 in a different order.

| Code | Name | Stage | Rule source |
|---:|---|---|---|
| 0 | `ELIGIBLE` | result | — |
| 1 | `WOODY_COVER` | A methodology | §4.3(8)(a); §6.2(1) |
| 2 | `BUILTUP_WATER_WETLAND` | B design | land-cover screen |
| 3 | `CROPLAND` | B design | §4.3(8)(b) makes cropland eligible; exclusion is a design choice |
| 4 | `RECENT_WOODY_REMOVAL` | A methodology | §4.4.2(1), census only |
| 5 | `STEEP_SLOPE` | B design | project design screen |
| 6 | `PROTECTED` | B design | WDPA safeguard screen |
| 7 | `NODATA` | A data validity | area-balance closure |
| 8 | `SMALL_PATCH` | B design | transaction-cost screen |

`OUTSIDE = 255` means outside the district and is never counted in any area.

## 5. Data sources and status

| Layer | Source | Status in this repo |
|---|---|---|
| District boundary | geoBoundaries ADM2, Jhabua feature | present; 3,433.78 km² in EPSG:32643 |
| WorldCover | ESA WorldCover 2021 v200, 10 m | **missing raw file** |
| Hansen treecover/loss/gain | Hansen GFC 30 m | **missing raw files** |
| DEM / slope | Copernicus DEM or SRTM 30 m | **missing raw file** |
| Protected areas | WDPA India | **missing raw file** |
| Sentinel-2 dry/monsoon | GEE composites, 2024 | present; 8 bands, EPSG:4326, ~10 m |
| Processed S2 (legacy) | EPSG:32643, 9.586 m | present; not on the 30 m screening grid |

The aligned 30 m stack does not exist yet. Until the missing raw sources are placed in
`data/raw/`, `src/ingest.py` exits with a missing-source list and writes nothing.

## 6. Grid and resampling assumptions

- Effective resolution is **30 m** because Hansen and the DEM are native 30 m.
- WorldCover (10 m, categorical) is aggregated with **majority/mode**.
- Hansen layers are resampled **nearest** to preserve class/percent values.
- DEM is resampled **bilinear**, then slope is computed with **Horn (1981)**.
- Sentinel-2 NDVI/BSI are averaged to 30 m as optional scoring layers.
- WDPA is rasterised with `all_touched=True`, a conservative no-go mask.
- The 30 m grid origin is snapped to the district envelope; the mask is rasterised
  without `all_touched`, so the edge is slightly conservative.

## 7. Limitations to state to a reviewer

- Canopy cover is a proxy for woody biomass, not the same physical quantity.
- Shrubs/thickets (`shrubland: flag`) can exceed 10% woody biomass without registering
  as tree canopy; the direction of bias may overstate eligible area.
- Hansen `lossyear` is binary; the code collapses any loss to zero canopy, which can
  overstate eligible area.
- Hansen data end in 2024 while `start_year` is 2026; 2025–2026 removals are invisible.
- WorldCover 2021 and Hansen 2000–2024 are different vintages.
- No tenure/PESA-FRA check; Jhabua is a Scheduled Area.
- This is pre-feasibility only. No credits are projected; field data, baselines,
  leakage and third-party verification are required before any credit forecast.

## 8. Provenance

- Primary source: `verra-verify/vm0047_v11.pdf` (Verra VM0047 v1.1).
- Hash above matches `README.md` and `docs/PROJECTSTATE.md`.
- The VCS project IDs sometimes mentioned in secondary write-ups (e.g. 5589/5697) do
  **not** appear in this repository’s documentation and are not used as evidence here.
