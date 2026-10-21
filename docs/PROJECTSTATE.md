# PROJECT STATE — Agroforestry land screening, Jhabua (MP)

**Status tracked here so a later session can pick up the same state.** Update after
every session: DONE → IN PROGRESS → NEXT.

## 1. Headline

Config-driven GIS screening of candidate degraded land (public data only) for an
IBCRI/Swiftgreen-style agroforestry project under VM0047 ARR v1.1. The screening core
and QA gate are implemented; the real Jhabua stack is waiting on six raw sources.

## 2. Phase status

| Phase | What | Status |
|---|---|---|
| W1 Foundations | config, verified assumptions, QA gate, synthetic end-to-end | **DONE** |
| W2 Screening | ingest contract, 30 m aligned stack, reason codes, waterfall | **CODE DONE / DATA PENDING** |
| W3 Scoring | weighted overlay, Dirichlet sensitivity, stability map | not started |
| W4 Validation + maps | stratified sample, accuracy + CI, zonal stats, maps | not started |
| W5 Docs | README, methodology/limitations, learning walkthrough | IN PROGRESS |

## 3. Key decisions (why)

1. **Census mode only.** VM0047 §4.3(8)(a)/§6.2 use <10% pre-existing woody biomass.
   The 10-year rule in §4.4.2(1) is a separate census **exclusion**, not the v1.0
   “non-forest for ten years” test.
2. **Area mode disabled.** §1.1/§4.4.1 need managed-forest, timber-harvest and
   native-ecosystem evidence that this repo does not have. Refuse rather than mislabel.
3. **Two-stage waterfall.** Stage A = methodology/data validity; Stage B = design
   screens. `methodology_eligible_ha` and `candidate_ha` are reported separately.
4. **30 m effective resolution.** WorldCover/S2 aggregate down; Hansen/DEM stay native.
5. **One reason-code contract.** 0 eligible, 1 woody, 2 built/water/wetland, 3 cropland,
   4 recent removal, 5 steep, 6 protected, 7 nodata, 8 small patch, 255 outside.
6. **QA gate measures rasters.** It opens every GeoTIFF; it does not trust a manifest.
7. **No credit forecast.** Pre-feasibility only.

## 4. Artifact hashes

- Verra VM0047 v1.1 PDF: `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`
- Raw boundary: `4fd352176b425954d6188d4c1a590dee70b226171608032e31d5879d849da8e5`
- Jhabua boundary extract: `f35e2f5b04bc6ccbcd99dd0a4d616f8f624df2ca7cbcf67868792e147e159c06`
- S2 dry raw: `e40040b746bdac3a1a241892bebb942a36236b3b3e551bb0e2b29db66021dc35`
- S2 monsoon raw: `8735395ef1c8901e1a013563d6853e4b31d6ed5be68dc658ce812ef50f95663e`
- Jhabua area in EPSG:32643: **3,433.775 km²** → config reference **3,433.78 km²**

## 5. Blockers

- Missing raw layers: WorldCover 2021, Hansen treecover2000/lossyear/gain, DEM 30 m,
  WDPA India. `src/ingest.py` stops and lists them; no partial stack is written.
- Git is initialized; the implementation is committed. Large raw/processed rasters are
  ignored by `.gitignore`. Archive copies of the old scaffold are in `archived/v1_scaffold/`.

## 6. Verification

- `python -m pytest -q` → **17 passed**.
- `python src/qaqc.py --selftest` → **PASS** (clean stack accepted, 10 m corruption caught).
- `python run_pipeline.py config/jhabua.yaml` → validates the live config.

## 7. Next action

Place the six required raw sources in `data/raw/`, then run:

```bash
python src/ingest.py config/jhabua.yaml
python src/qaqc.py --check config/jhabua.yaml
python src/screening.py config/jhabua.yaml
```

Inspect `outputs/jhabua_agroforestry_screening/reason_codes.tif` in QGIS before quoting
any hectare figure.
