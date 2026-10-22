# Data sources — real Jhabua stack

`src/ingest.py` reads the paths in `config/jhabua.yaml → paths.sources`. The local
raw files in `data/raw/` are the actual working copies. They are clipped/mosaicked
to the Jhabua envelope (74.14–75.03°E, 22.37–23.25°N) and are git-ignored.

The canonical provenance record, including SHA256 hashes and acquisition dates, is
`data/manifest.json`.

## Required sources actually used on 21 Oct 2026

| Layer | Local file | Public source | Version / tile | Native resolution |
|---|---|---|---|---|
| WorldCover | `data/raw/worldcover_2021.tif` | ESA WorldCover 2021 v200 | `N21E072`, `N21E075` | 10 m |
| Hansen treecover | `data/raw/hansen_treecover2000.tif` | Hansen GFC 2024 v1.12 | `30N_070E` | 30 m |
| Hansen loss | `data/raw/hansen_lossyear.tif` | Hansen GFC 2024 v1.12 | `30N_070E` | 30 m |
| Hansen gain | `data/raw/hansen_gain.tif` | Hansen GFC 2024 v1.12 | `30N_070E` | 30 m |
| DEM | `data/raw/dem_30m.tif` | Copernicus DEM GLO-30 | `N22E074`, `N22E075`, `N23E074`, `N23E075` | 30 m |
| Protected areas | `data/raw/wdpa.geojson` | WDPA / Protected Planet | `WDPA_WDOECM_Oct2026_Public_IND` | vector |
| Boundary | `data/raw/boundary.geojson` | geoBoundaries 2.0.1 India ADM2 | Jhabua feature | vector |
| Sentinel-2 dry | `data/raw/s2_dry_2024.tif` | GEE Sentinel-2 dry-season median | 2024 | ~10 m |
| Sentinel-2 monsoon | `data/raw/s2_monsoon_2024.tif` | GEE Sentinel-2 monsoon median | 2024 | ~10 m |

## How the local working layers were built

- WorldCover: two public tiles were mosacked and clipped to the Jhabua envelope.
- Hansen: the correct `30N_070E` tile was clipped; values were preserved.
- DEM: four Copernicus GLO-30 COGs were mosacked and clipped.
- WDPA: India polygons only, clipped to the Jhabua envelope. Raw WDPA data are not
  redistributed in the repository.
- Boundary: geoBoundaries ADM2 file with the Jhabua feature selected by
  `project.boundary_feature`.
- Sentinel-2 composites were not re-downloaded; the existing 2024 8-band files are
  used for map backgrounds and optional scoring indices.

## Notes on the actual tiles

- The first Hansen tile was accidentally `20N_070E`, which covers 20°N down to
  10°N. Jhabua is 22.4–23.2°N, so it was replaced with `30N_070E`.
- WorldCover classes present in Jhabua: **10, 20, 30, 40, 50, 60, 80**. Class 95
  (mangroves) is in the config but absent in the district.
- WDPA contains **Reserve Forest** and **Protected Forest** designations, not only
  IUCN I–IV. All polygons are treated as a conservative protected-area screen.

## Why ingest stops on a missing source

`src/ingest.py` refuses to build a partial stack. If a path in
`config/jhabua.yaml → paths.sources` is missing, the run stops and lists the missing
files. It does not zero-fill. This is deliberate; a silent zero-filled raster can
make a screen look clean while actually being empty.

## Post-download workflow

```bash
python src/ingest.py config/jhabua.yaml
python src/qaqc.py --check config/jhabua.yaml
python src/screening.py config/jhabua.yaml
python scripts/make_maps.py config/jhabua.yaml
```

Before any downstream use, verify the QA report and inspect
`outputs/jhabua_agroforestry_screening/reason_codes.tif` against the imagery.
