# Methodology — Jhabua screening

This is a **pre-feasibility land screen**, not a carbon-credit calculation. It answers
one question: *which 30 m pixels survive the VM0047 v1.1 census eligibility test and a
transparent set of design screens?*

## 1. Inputs and grid

All layers enter one grid: `EPSG:32643` (UTM 43N), 30 m, north-up, same width/height.
The grid origin is snapped to the district envelope. The district mask is rasterised
from the Jhabua feature in the geoBoundaries ADM2 file.

| Layer | Native form | Transform to 30 m |
|---|---|---|
| WorldCover 2021 | 10 m categorical | majority/mode |
| Hansen treecover2000 | 30 m percent | nearest |
| Hansen lossyear | 30 m class | nearest |
| Hansen gain | 30 m binary | nearest |
| DEM | 30 m continuous | bilinear, then Horn slope |
| WDPA | vector polygons | rasterise, `all_touched=True` |
| Sentinel-2 NDVI/BSI | ~10 m float | average (optional scoring layers) |

Nothing is disaggregated upward. A 30 m Hansen pixel is not split into nine 10 m
pixels: that would invent information.

## 2. Stage A — methodology and data validity

Stage A rejects a pixel if any of these is true:

1. **NODATA** — missing in a required layer inside the district.
2. **WOODY_COVER** — WorldCover tree/mangrove **or** Hansen `treecover2000 >= 10%`.
   Source: VM0047 v1.1 §4.3(8)(a), §6.2(1).
3. **RECENT_WOODY_REMOVAL** — Hansen loss in the last 10 years on a pixel that had
   `treecover2000 >= 10%`. Source: §4.4.2(1), census-based exclusion.

`methodology_eligible_ha` = district minus Stage A. Cropland is **included** at this
stage; excluding it is a design choice, not a methodology rule.

Order inside Stage A changes only *which code is attributed* when several rules fail.
The eligible mask is the plain intersection of all Stage-A passes, so it is
order-invariant.

## 3. Stage B — design and safeguard screens

In the configured order:

1. **BUILTUP_WATER_WETLAND** — WorldCover 50/80/90.
2. **CROPLAND** — WorldCover 40; kept in census, excluded in the design variant.
3. **PROTECTED** — WDPA raster = 1.
4. **STEEP_SLOPE** — Horn slope > 20°.
5. **SMALL_PATCH** — eligible patches < 1 ha, 8-connectivity.

These are not quoted as methodology clauses. `candidate_ha` is what remains.

## 4. Waterfall and QA

Every district pixel receives exactly one code. The screen asserts:

```
sum(code areas) == district area
```

If it does not, the run stops. It also checks:

- raster CRS, transform, shape and **measured** resolution;
- district area vs `qa.reference_area_km2` within 1%;
- Hansen loss year <= configured vintage;
- value ranges and WorldCover classes;
- nodata share inside the district per layer;
- optional S2 index bounds.

`src/qaqc.py` is a separate gate that opens the actual GeoTIFFs before screening.

## 5. Why area mode is refused

The area-based route (§1.1, §4.4.1) is not a different cropland switch. It requires
evidence about managed forest, timber harvesting and native-ecosystem degradation over
the last ten years. Those datasets are absent. Reporting an area-mode hectare figure
from the census rules would be a category error, so the code raises
`NotImplementedError` instead.

## 6. What the numbers mean

- `methodology_eligible_ha` — area that survives the methodology/data-validity test.
- `candidate_ha` — area after project design screens and patch removal.
- Neither is a credit estimate. Baselines, additionality, leakage, field validation and
  verification are out of scope.
