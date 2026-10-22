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
- [x] Download the six real sources and clip/mosaic them into `data/raw/`.
- [x] Fix the Hansen tile (`30N_070E`, not `20N_070E`) before ingest.
- [x] Run the real ingest: 11 aligned layers, 2933 x 3130 grid at 30 m.
- [x] Run the QA gate: 19 checks, 0 blocking, 1 warning (only "no screening output yet"
      at the time of the gate; the screen now exists).
- [x] Run the real screen: 343,380.6 ha district → 324,094.0 ha methodology-eligible →
      251,292.8 ha candidate.
- [x] Record source hashes, URLs and acquisition dates in `data/manifest.json`.
- [x] Generate four portfolio maps from the actual rasters.
- [x] Document the WDPA decision: all polygons, including Reserve/Protected Forest.

## P1 — screening follow-up
- [ ] Run sensitivity variants: `threshold_pct` 10/15/20; `shrubland` flag/exclude;
      `source` worldcover/hansen/either; `min_patch_ha` 0.5/1/2.
- [ ] Replace the binary Hansen-loss proxy with a post-loss canopy product or document
      the bias with a sensitivity band.
- [ ] Add a WDPA sensitivity variant using only IUCN I–IV vs all designations.
- [ ] Add the 2025–2026 Hansen gap to the limitations section.
- [ ] Decide whether the candidate should exclude cropland as a design scenario
      (methodology-eligible area must still be reported with cropland in).

## P2 — scoring, validation, maps
- [ ] Weighted suitability (NDVI / slope / water / road).
- [ ] ~300 Dirichlet scenarios + stability map.
- [ ] Stratified validation including excluded pixels.
- [ ] Village-level summaries and a top-candidate shortlist for fieldwork.
- [ ] Optional QGIS project (`.qgz`) with the reason raster, boundary and basemap.

## P3 — portfolio packaging
- [x] `docs/case_study.md` with results, figures, limitations and CV bullets.
- [ ] Final proofread of maps and case study.
- [ ] Choose public vs private repository; default is private/portfolio use.
- [ ] Commit code, docs and selected outputs; keep raw data ignored.
