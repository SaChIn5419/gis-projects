# Agroforestry Land Screening – Jhabua, MP

**Independent pre-feasibility screening — public data only. Not Equilibrium / not a credit forecast.**

Config-driven GIS workflow (QGIS + Google Earth Engine + Python/GeoPandas + Rasterio)
to screen candidate degraded land for a Swiftgreen/IBCRI-style agroforestry project,
using Verra **VM0047 ARR v1.1** (14 May 2025).

## What the code does

1. **`src/ingest.py`** builds one aligned 30 m stack from raw layers:
   district mask, WorldCover, Hansen treecover/loss/gain, slope, WDPA, and optional
   Sentinel-2 NDVI/BSI. Missing raw sources stop the run; nothing is zero-filled.
2. **`src/qaqc.py`** opens the actual GeoTIFFs and checks CRS, resolution, grid,
   nodata, value ranges, boundary area and district area. Critical failures stop the run.
3. **`src/screening.py`** applies a two-stage waterfall:
   - **Stage A — methodology + data validity** → `methodology_eligible_ha`
   - **Stage B — design/safeguard screens** → `candidate_ha`
   Every pixel gets one reason code; the area balance must close.
4. Outputs: `reason_codes.tif`, `confidence_flags.tif`, `waterfall.csv`,
   `run_summary.json`, and a QA report in `outputs/qaqc/`.

## Method note (important)

VM0047 v1.1 census eligibility is **pre-existing woody biomass < 10%**
(§4.3(8)(a); §6.2(1)), not the v1.0 “non-forest for ten years” test.
The 10-year rule that remains is §4.4.2(1), a **census exclusion** for woody biomass
removed in the last 10 years. The code labels it as a methodology exclusion, not as an
eligibility test. See `docs/assumptions.md`.

Area-based mode is **intentionally disabled** until the §1.1/§4.4.1 evidence
(managed forest, timber harvest, native-ecosystem degradation) exists.

## Quick start

```bash
# validate config only (safe before data is present)
python run_pipeline.py config/jhabua.yaml

# build the aligned stack (requires the raw sources in data/raw/)
python src/ingest.py config/jhabua.yaml

# gate the stack
python src/qaqc.py --check config/jhabua.yaml

# screen
python src/screening.py config/jhabua.yaml

# or one command
python run_pipeline.py config/jhabua.yaml --run
```

Tests:

```bash
python -m pytest -q          # 17 tests
python src/qaqc.py --selftest
```

## Current data status

Present:

- `data/raw/boundary.geojson` (641 ADM2 features) and the extracted Jhabua feature
  (`3,433.78 km²` in EPSG:32643).
- `data/raw/s2_dry_2024.tif`, `data/raw/s2_monsoon_2024.tif` (8 bands, EPSG:4326, ~10 m).

Missing (needed before the real screen can run):

- WorldCover 2021, Hansen treecover/loss/gain, DEM, WDPA.

The repository therefore has **no real Jhabua screening result yet**. The tests use
synthetic rasters to prove the grid, resampling, QA and waterfall contracts.

## References

- Verra VM0047 v1.1 PDF: `verra-verify/vm0047_v11.pdf`
  SHA256 `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`
- IBCRI / Swiftgreen project pages are used only as reference scales, never as data.
- `docs/assumptions.md` — verified clauses and the canonical reason-code table.
- `docs/methodology.md` — step-by-step method.
- `docs/limitations.md` — what cannot be claimed.
- `docs/data_sources.md` — expected raw files and download notes.
- `learning.md` — full walkthrough of the method and code.
