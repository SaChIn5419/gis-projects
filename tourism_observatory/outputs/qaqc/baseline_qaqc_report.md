# P1 baseline QA report — Wayanad

Generated (UTC): 2026-10-23T08:07:26+00:00
Scope: baseline layers only (qa.scope_pre_c1) — no outcome layers exist
Rule: files opened directly; manifest not read (Jhabua fail-fast QA)

**Result: PASS** (0 critical failures, 0 warnings, 62 checks)

## Checks

| status | check | detail |
|---|---|---|
| PASS | dem_copernicus30m_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | dem_copernicus30m_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | dem_copernicus30m_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | dem_copernicus30m_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | dem_copernicus30m_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | dem_copernicus30m_32643.tif: value band | min 117.909 / max 2171.604 within (0, 3500) |
| PASS | dem_copernicus30m_32643.tif: nodata share in AOI | 0.0000% (fail >5%) |
| PASS | slope_deg_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | slope_deg_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | slope_deg_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | slope_deg_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | slope_deg_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | slope_deg_32643.tif: value band | min 0.000 / max 66.922 within (0, 80) |
| PASS | slope_deg_32643.tif: nodata share in AOI | 0.0000% (fail >5%) |
| PASS | worldcover_2021_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | worldcover_2021_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | worldcover_2021_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | worldcover_2021_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | worldcover_2021_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | worldcover_2021_32643.tif: allowed classes | classes [10, 30, 40, 50, 60, 80, 90]; unexpected [] |
| PASS | worldcover_2021_32643.tif: nodata share in AOI | 0.0000% (fail >5%) |
| PASS | hansen_treecover2000_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | hansen_treecover2000_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | hansen_treecover2000_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | hansen_treecover2000_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | hansen_treecover2000_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | hansen_treecover2000_32643.tif: value band | min 0.000 / max 100.000 within (0, 100) |
| PASS | hansen_treecover2000_32643.tif: nodata share in AOI | 0.0000% (warn >20%) |
| PASS | wdpa_all_touched_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | wdpa_all_touched_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | wdpa_all_touched_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | wdpa_all_touched_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | wdpa_all_touched_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | wdpa_all_touched_32643.tif: allowed classes | classes [0, 1]; unexpected [] |
| PASS | wdpa_all_touched_32643.tif: burn share in AOI | protected share 42.4302% (warn if <1% or >99%) |
| PASS | road_dist_m_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | road_dist_m_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | road_dist_m_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | road_dist_m_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | road_dist_m_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | road_dist_m_32643.tif: value band | min 0.000 / max 5860.375 within (0, 50000) |
| PASS | aoi_mask_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | aoi_mask_32643.tif: measured resolution | measured 30 x 30 m (expected 30) |
| PASS | aoi_mask_32643.tif: shape | shape (1950, 2450) (expected (1950, 2450)) |
| PASS | aoi_mask_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | aoi_mask_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | aoi_mask_32643.tif: allowed classes | classes [1]; unexpected [] |
| PASS | aoi_mask_32643.tif: nodata share in AOI | 0.0000% (warn >20%) |
| PASS | cci_lulc_2005_32643.tif: CRS | CRS EPSG:32643 (expected EPSG:32643) |
| PASS | cci_lulc_2005_32643.tif: measured resolution | measured 300 x 300 m (expected 300) |
| PASS | cci_lulc_2005_32643.tif: shape | shape (195, 245) (expected (195, 245)) |
| PASS | cci_lulc_2005_32643.tif: grid origin (envelope anchor) | origin (584100.0, 1324500.0) (expected (584100.0, 1324500.0)) |
| PASS | cci_lulc_2005_32643.tif: extent covers AOI envelope | raster bounds [584100.0, 1266000.0, 657600.0, 1324500.0] vs AOI [np.float64(584346.3), np.float64(1266151.5), np.float64(657445.0), np.float64(1324378.1)] |
| PASS | cci_lulc_2005_32643.tif: allowed classes | classes [10, 11, 12, 20, 30, 40, 50, 60, 61, 70, 100, 110, 120, 121, 130, 170, 180, 190, 210]; unexpected [] |
| PASS | cci_lulc_2005_32643.tif: nodata share in AOI | 0.0000% (warn >20%) |
| PASS | area-sum: AOI mask vs boundary vector | mask 2026.412 km² vs vector 2026.393 km² = +0.001% (fail >2%) |
| PASS | area-sum: WorldCover classes tile the AOI | class areas sum 2026.413 km² vs mask 2026.4121 km² |
| PASS | area-sum: WDPA raster >= vector union (all_touched rule) | raster 863.923 km² vs union 855.782 km² (sum 1164.121 km² double-counts overlaps) |
| PASS | area-sum: WDPA raster within all_touched margin | raster 863.923 km²; allowance 1074.727 km² |
| PASS | roads: feature count | 13205 highway features |
| PASS | roads: share inside AOI after clip | 100.0% inside (clipped layer expected ≥95%) |
| PASS | grid consistency: all 30 m layers identical shape | {(1950, 2450)} |

## Layer measurements (from opened files)

| file | dtype | nodata | measured res (m) | shape | nodata share in AOI | values |
|---|---|---|---|---|---|---|
| dem_copernicus30m_32643.tif | float32 | -9999.0 | [30.0, 30.0] | [1950, 2450] | 0.0 | 117.909 … 2171.604 |
| slope_deg_32643.tif | float32 | -9999.0 | [30.0, 30.0] | [1950, 2450] | 0.0 | 0.0 … 66.922 |
| worldcover_2021_32643.tif | uint8 | 0.0 | [30.0, 30.0] | [1950, 2450] | 0.0 | [10, 30, 40, 50, 60, 80, 90] |
| hansen_treecover2000_32643.tif | uint8 | 255.0 | [30.0, 30.0] | [1950, 2450] | 0.0 | 0.0 … 100.0 |
| wdpa_all_touched_32643.tif | uint8 | 0.0 | [30.0, 30.0] | [1950, 2450] | 0.5757 | [0, 1] |
| road_dist_m_32643.tif | float32 | None | [30.0, 30.0] | [1950, 2450] | 0.0 | 0.0 … 5860.375 |
| aoi_mask_32643.tif | uint8 | 0.0 | [30.0, 30.0] | [1950, 2450] | 0.0 | [1] |
| cci_lulc_2005_32643.tif | uint8 | 0.0 | [300.0, 300.0] | [195, 245] | 0.0 | [10, 11, 12, 20, 30, 40, 50, 60, 61, 70, 100, 110, 120, 121, 130, 170, 180, 190, |

## Area checks

- **aoi_mask_km2**: 2026.412
- **boundary_vector_km2**: 2026.393
- **aoi_diff_pct**: 0.001
- **worldcover_class_area_km2**: {10: 1816.199, 30: 117.614, 40: 63.616, 50: 16.216, 60: 0.219, 80: 12.465, 90: 0.084}
- **worldcover_sum_km2**: 2026.413
- **wdpa_vector_km2**: 855.782
- **wdpa_vector_sum_km2**: 1164.121
- **wdpa_raster_km2**: 863.923
- **road_features**: 13205

