# Agroforestry Land Screening – Jhabua, MP

**Independent pre-feasibility portfolio project. Public data only. Not Equilibrium Earth; not a carbon-credit forecast.**

A config-driven GIS screening workflow for a VM0047 ARR-style agroforestry project in
Jhabua district, Madhya Pradesh. The project is an independent reproduction of the kind
of screening workflow used to find candidate degraded land; it does not use Equilibrium
data, branding, or claimed company results.

## Real Jhabua result (21 Oct 2026)

| Accounting step | Area (ha) | Share of district |
|---|---:|---:|
| District | 343,380.6 | 100.0% |
| Methodology-eligible (Stage A) | 324,094.0 | 94.4% |
| Candidate after design screens (Stage B) | 251,292.8 | 73.2% |
| Candidate still carrying a confidence flag | 197,590.4 | 57.5% |

Main exclusions:

| Screen | Removed (ha) | Stage |
|---|---:|---|
| Woody cover (WorldCover tree / Hansen >=10%) | 19,286.6 | A |
| Built-up / water / wetland | 4,300.2 | B |
| Protected areas (WDPA, all designations) | 68,149.1 | B |
| Steep slope (>20°) | 144.2 | B |
| Small patches (<1 ha) | 207.7 | B |
| Recent woody removal (Hansen, last 10 years) | 0.0 | A |
| Cropland (census mode keeps cropland) | 0.0 | B |

The candidate is still 73.2% of the district because **census mode keeps cropland** and
because Jhabua has very little Hansen-mapped forest loss. The 197,590 ha flagged area is
mostly cropland kept as a data-confidence flag, not an exclusion. These figures are for
fieldwork targeting; they are not a project boundary, eligibility determination, or
credit estimate.

## What the code does

1. **`src/ingest.py`** builds one aligned 30 m stack in EPSG:32643 from the raw layers:
   district mask, WorldCover, Hansen treecover/loss/gain, slope, WDPA, and optional
   Sentinel-2 NDVI/BSI. Missing raw sources stop the run; nothing is zero-filled.
2. **`src/qaqc.py`** opens the actual GeoTIFFs and checks CRS, resolution, grid, nodata,
   value ranges, boundary area, and district area. Critical failures stop the run.
3. **`src/screening.py`** applies a two-stage waterfall:
   - **Stage A — methodology + data validity** → `methodology_eligible_ha`
   - **Stage B — design / safeguard screens** → `candidate_ha`
   Every pixel gets one reason code; the area balance must close.
4. **`scripts/make_maps.py`** generates the portfolio maps from the actual rasters:
   study area, reason codes, exclusion waterfall, and a mixed-code close-up.

Outputs:

- `outputs/jhabua_agroforestry_screening/reason_codes.tif`
- `outputs/jhabua_agroforestry_screening/confidence_flags.tif`
- `outputs/jhabua_agroforestry_screening/waterfall.csv`
- `outputs/jhabua_agroforestry_screening/run_summary.json`
- `outputs/qaqc/qaqc_report.md`
- `outputs/maps/01_study_area.png` … `04_candidate_closeup.png`

## Method note (important)

VM0047 v1.1 census eligibility is **pre-existing woody biomass < 10%**
(§4.3(8)(a); §6.2(1)), not the v1.0 “non-forest for ten years” test. The 10-year rule
that remains is §4.4.2(1), a **census exclusion** for woody biomass removed in the last
10 years. The code labels it as a methodology exclusion, not as an eligibility test.
See `docs/assumptions.md`.

Area-based mode is **intentionally disabled** until the §1.1/§4.4.1 evidence (managed
forest, timber harvest, native-ecosystem degradation) exists.

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

# maps
python scripts/make_maps.py config/jhabua.yaml

# or one command
python run_pipeline.py config/jhabua.yaml --run
```

Tests:

```bash
python -m pytest -q          # 17 tests
python src/qaqc.py --selftest
```

## Data status and provenance

All six required sources are present locally; the raw rasters are git-ignored:

| Layer | Source | Version / tile |
|---|---|---|
| WorldCover | ESA WorldCover 2021 v200 | `N21E072`, `N21E075` |
| Hansen treecover/loss/gain | Hansen GFC 2024 v1.12 | `30N_070E` |
| DEM | Copernicus DEM GLO-30 | `N22E074`, `N22E075`, `N23E074`, `N23E075` |
| Protected areas | WDPA / Protected Planet | `WDPA_WDOECM_Oct2026_Public_IND` |
| Boundary | geoBoundaries 2.0.1 India ADM2 | Jhabua feature |
| Sentinel-2 | GEE 2024 dry/monsoon composites | map background / optional scoring |

Hashes, URLs, acquisition dates, and clip notes are in `data/manifest.json`. The WDPA
source includes **Reserve Forest and Protected Forest** designations, not only IUCN
I–IV. Treating every polygon as a no-go screen is deliberately conservative and
over-excludes some multiple-use forest; this is documented in `docs/limitations.md`.

WDPA terms are non-commercial. The raw WDPA download is not redistributed; only derived
maps/tables and the clipped local working layer are used. Attribution: UNEP-WCMC and
IUCN, Protected Planet.

## Repository layout

```text
config/                 live Jhabua config
src/ingest.py           raw → aligned 30 m stack
src/qaqc.py             measured QA gate
src/screening.py        two-stage waterfall + reason codes
scripts/make_maps.py    portfolio maps from the outputs
docs/                   method, assumptions, data sources, limitations, case study
outputs/maps/           selected portfolio maps (PNG)
data/manifest.json      raw-source provenance and real-run summary
```

## Limitations

- 30 m screen for targeting fieldwork, not for registration or verification.
- The WDPA screen is conservative: all designations, including Reserve/Protected Forest.
- Hansen tree cover is sparse in Jhabua; only 2,441 aligned 30 m pixels have >=10% cover.
  The candidate may overstate land that is legally or socially unavailable.
- Hansen ends in 2024; 2025–2026 removals are invisible.
- Census mode keeps cropland, so the candidate is much larger than a project boundary.
- No tenure, FPIC, PESA-FRA, safeguard, baseline, additionality, leakage, or credit work.
- No field validation.

Read `docs/limitations.md` before quoting a hectare figure.

## References

- Verra VM0047 v1.1 PDF: `verra-verify/vm0047_v11.pdf`
  SHA256 `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`
- IBCRI / Swiftgreen project pages are used only as reference scales, never as data.
- `docs/assumptions.md` — verified clauses and the canonical reason-code table.
- `docs/methodology.md` — step-by-step method.
- `docs/limitations.md` — what cannot be claimed.
- `docs/data_sources.md` — actual sources, URLs, and download notes.
- `docs/case_study.md` — portfolio write-up and CV bullets.
- `learning.md` — full walkthrough of the method and code.
