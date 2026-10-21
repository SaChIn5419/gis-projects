# TODO — Jhabua agroforestry land screening

## Done
- [x] Read VM0047 v1.1 and verify the census rule: `<10% pre-existing woody biomass`
      (§4.3(8)(a); §6.2(1)); §4.4.2(1) is the separate 10-year removal exclusion.
- [x] Pin the PDF SHA256 `2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d`.
- [x] Reconcile the zip screening core with the repo scaffold.
- [x] Canonical reason-code table (0–8) in code, config, docs and QA gate.
- [x] Two-stage waterfall (`methodology_eligible_ha` vs `candidate_ha`).
- [x] Disable area mode explicitly until §1.1/§4.4.1 evidence exists.
- [x] Measure the real transform in `load_layers()` and reject wrong resolution.
- [x] Add `protected_areas` to nodata handling.
- [x] Rewrite `src/ingest.py` for seven aligned 30 m layers (+ optional S2 indices).
- [x] Rewrite `src/qaqc.py` to measure actual rasters, not a manifest.
- [x] Add synthetic ingest + QA + CLI tests (17 pass).
- [x] Set `qa.reference_area_km2 = 3433.78` from the EPSG:32643 boundary.

## P0 — real data
- [ ] Put WorldCover 2021, Hansen treecover/loss/gain, DEM and WDPA in `data/raw/`.
- [ ] Run `python src/ingest.py config/jhabua.yaml` and inspect the aligned manifest.
- [ ] Run `python src/qaqc.py --check config/jhabua.yaml`.
- [ ] Run `python src/screening.py config/jhabua.yaml`.
- [ ] Visually check the reason-code raster in QGIS against the imagery.

## P1 — screening follow-up
- [ ] Run sensitivity variants: `threshold_pct` 10/15/20; `shrubland` flag/exclude;
      `source` worldcover/hansen/either; `min_patch_ha` 0.5/1/2.
- [ ] Replace the binary Hansen-loss proxy with a post-loss canopy product or document
      the bias with a sensitivity band.
- [ ] Add the 2025–2026 Hansen gap to the limitations section.
- [ ] Decide whether WDPA should include all IUCN categories or only I–IV.

## P2 — scoring, validation, maps
- [ ] Weighted suitability (NDVI / slope / water / road).
- [ ] ~300 Dirichlet scenarios + stability map.
- [ ] Stratified validation including excluded pixels.
- [ ] Maps: study area, exclusions, suitability, top villages.

## P3 — docs
- [ ] `docs/methodology.md`, `docs/limitations.md`.
- [ ] Final QA report and README screenshot.
