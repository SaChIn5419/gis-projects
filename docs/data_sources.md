# Data sources and expected filenames

`src/ingest.py` reads the paths in `config/jhabua.yaml → paths.sources`. The filenames
below are the contract. You can download tiles covering the Jhabua envelope
(approximately 74.1–75.1°E, 22.3–23.3°N) and let ingest clip/reproject them; you do not
need to pre-clip.

## Required for the screening stack

| Config key | Expected file | Source | Native resolution | Notes |
|---|---|---|---|---|
| `worldcover` | `data/raw/worldcover_2021.tif` | ESA WorldCover 2021 v200 | 10 m | mosaic the tiles covering the district; class codes 10–100 |
| `hansen_treecover2000` | `data/raw/hansen_treecover2000.tif` | Hansen Global Forest Change | 30 m | percent tree cover in 2000, 0–100 |
| `hansen_lossyear` | `data/raw/hansen_lossyear.tif` | Hansen GFC | 30 m | 0 = no loss; 1..N = year 2000+N |
| `hansen_gain` | `data/raw/hansen_gain.tif` | Hansen GFC | 30 m | 0/1; only 2000–2012 |
| `dem` | `data/raw/dem_30m.tif` | Copernicus GLO-30 or SRTM | 30 m | ingest computes Horn slope |
| `protected_areas` | `data/raw/wdpa.geojson` | WDPA / Protected Planet (India) | vector | any polygon = protected; classify IUCN categories in the limitations |

## Boundary

`data/raw/boundary.geojson` is the geoBoundaries ADM2 file (641 features). Ingest
selects `shapeName == "Jhabua"`. If you replace it with a Jhabua-only file, keep a
`shapeName` column containing `Jhabua`, or update `project.boundary_feature`.

## Optional scoring layers

| Config key | Expected file | Source |
|---|---|---|
| `s2_dry` | `data/raw/s2_dry_2024.tif` | GEE dry-season composite (already present) |
| `s2_monsoon` | `data/raw/s2_monsoon_2024.tif` | GEE monsoon composite (already present) |

Bands 7 and 8 are assumed to be NDVI and BSI, as in `scripts/s2_composites.py`.

## After download

1. Record the SHA256 of every raw file in `data/manifest.json` (or let ingest write the
   aligned manifest; both are useful).
2. Run:
   ```bash
   python src/ingest.py config/jhabua.yaml
   python src/qaqc.py --check config/jhabua.yaml
   ```
3. If ingest stops, read the missing-path list. Do not create zero-filled substitutes.

## What ingest will do

- reproject to EPSG:32643;
- snap to a 30 m grid;
- aggregate WorldCover with majority;
- preserve Hansen values with nearest;
- resample DEM bilinearly and compute Horn slope;
- rasterise WDPA with `all_touched=True`;
- write the seven aligned layers plus `data/processed/aligned/manifest.json`.

The real screen will not run until all six required sources exist. That is deliberate.
