# P1 provenance & data-completeness report — Wayanad tourism observatory

Generated: 2026-10-23 · Phase P1 (baseline-only acquisition) · Feeds checkpoint **C2**
go/no-go · Scope boundary: prereg §5 — no H1–H4 outcome maps, no treatment-vs-control
tests, no construction dating were performed or derived.

---

## 1. Analysis grid (frozen definition)

| property | value |
|---|---|
| CRS | EPSG:32643 (UTM 43N; zone confirmed from district lon extent 75.7742–76.4443 E, dev-D-9(c) OI-3) |
| snap rule | AOI envelope snapped **outward** to 300 m multiples (`envelope_anchor`) |
| origin | (584100, 1324500) |
| 30 m grid | 1950 × 2450 (bounds 584100, 1266000, 657600, 1324500) |
| 300 m grid | 195 × 245 (identical envelope, nested — CCI-LC native analysis grid) |
| AOI | geoBoundaries IND-ADM2 shape 76128533B82539771173603, 2026.393 km² (official ≈2131 km²; simplified-boundary −4.9% recorded) |

## 2. Source acquisition ledger (raw files on disk, SHA-256 in `data/manifest.json`)

Manifest convention: every entry records a file actually present with its SHA-256 at
recording time; QA does **not** read the manifest — it opens the files (Jhabua rule).

| id | product / version | bytes | sha256 (first 16) | licence | audit ref |
|---|---|---|---|---|---|
| boundary_raw | geoBoundaries IND-ADM2 simplified (commit 9469f09) | — | `d68db39cd3e2d089` | ODbL | §1 AOI |
| registry_homestays_raw | keralatourism.org approved-homestay list snapshot 2026-10-22 | — | `1c7d664c6bb5a115` | public web page, attribution | D-1 |
| dem_cop_n11e075 | Copernicus GLO-30 N11E075 | 20,008,561 | `dbddab328128c587` | free w/ attribution | D-7 |
| dem_cop_n11e076 | Copernicus GLO-30 N11E076 | 44,177,013 | `717edb70dcd7f132` | free w/ attribution | D-7 |
| worldcover_2021_n09e075 | ESA WorldCover 10 m 2021 v200 tile N09E075 | 75,590,338 | `913f22dd9ba2b05f` | CC BY 4.0 | D-15 |
| hansen_treecover2000 | Hansen GFC-2024 v1.12, treecover2000, tile **20N_070E** | 146,712,076 | `f5794be5db12c9db` | CC BY 4.0 | D-16 |
| cci_lulc_2005 | ESA CCI-LC L4 LCCS 300 m annual **2005, v2.0.7cds**, tile N00E045 | 26,928,572 | `cf9e4c2134168f12` | CC BY 4.0 | D-14 (OI-2 closed) |
| wdpa_ind_oct2026 | WDPA/WDOECM Oct 2026 Public IND (pinned, = Jhabua release) | 262,364,833 | `2d5ea2f72cd35c46` | **NOT redistributable** | D-18 |
| osm_southern_zone_20261026 | Geofabrik southern-zone PBF, dated redirect of `-latest` | 558,498,689 | `e646eb588cef6284` | ODbL | dev-D-4 current-network proxy |
| d2_classified_wayanad_portal | Kerala Tourism classified portal, Wayanad slice snapshot (111 cards) | 149,605 | `3a493ba297c6485e` | public web page, attribution | D-2 |
| d3_ecostat_hotels_2014_15 | ecostat "Hotels & Restaurants Kerala 2014-15" (pub. 286) | 3,098,964 | `f8bb418fe3503291` | public govt publication | D-3 |
| d4_kts_arrivals_2025_26 | Kerala tourist statistics 2025-26 (arrivals series) | 419,559 | `7fe9107c81ffd401` | public govt publication | D-4 (V1 target; provenance-only pre-freeze) |
| d4_kts_book_2019 | ecostat Kerala Tourism Statistics 2019 (book series) | 3,450,479 | `481c812a6d104ea3` | public govt publication | D-4 |
| oi4_homestay_order_m5_1903 | Homestay order M5-1903/2015 dated 06-08-2019 (quotes GO 299/06, GO 324/15) | 44,430 | `85288c0d536a6ad3` | public govt order | D-1 / OI-4 closure evidence |

Derived products also hashed in the manifest: `boundary_wayanad` (`1d4f92cdc028726b`),
`registry_homestays_wayanad` (`fda3aefd0bc501b1`), `registry_geocoded_r2`
(`…2026-10-23.csv`, round-2 geocoding; geojson twin + geocode-log hashes recorded in
the entry note). **17 sources total.**

Git/ignore posture: all payloads under `data/raw/` are ignored; WDPA is hard-denied by
`.gitignore` (non-redistributable) with its SHA-256 as the only provenance trace;
small provenance files (manifest, ingest facts, QA reports, geocode logs, the official
CCI legend PDF in `docs/reference/`) are allowlisted and tracked.

## 3. Derived baseline stack (`data/processed/`, facts in `outputs/qaqc/ingest_facts.json`)

| layer | res | key measured content |
|---|---|---|
| `dem_copernicus30m_32643.tif` + `slope_deg_32643.tif` | 30 m | inside AOI: 117.9–2171.6 m (mean 844.6); slope 0–66.9° inside AOI (73.1° grid-wide); nodata 0% |
| `worldcover_2021_32643.tif` | 30 m (mode) | AOI classes {10,30,40,50,60,80,90}; tree cover 1816.2 km², cropland 63.6, built 16.2, water 12.5; classes tile AOI exactly |
| `hansen_treecover2000_32643.tif` | 30 m | 0–100; 83.1% of grid ≥10% tree cover (2000 baseline) |
| `cci_lulc_2005_32643.tif` | 300 m | 19 official classes present; urban (190) = 4 cells; water (210) = 638 cells; legend sourced from official `CCI-LC_Maps_Legend.pdf` (tracked copy) |
| `wdpa_all_touched_32643.tif` + `wdpa_wayanad_32643.gpkg` | 30 m | 12 polygons; **union** 855.8 km² (sum 1164.1 double-counts overlaps); raster 863.9 km²; protected share of AOI 42.43%; not redistributable |
| `roads_wayanad_32643.gpkg` + `road_dist_m_32643.tif` | 30 m | 13,205 clipped highway features; distance 0–5860 m in AOI; **current-network proxy**, not baseline-period observation (dev-D-4 label) |
| `aoi_mask_32643.tif` | 30 m | 2026.412 km² vs vector 2026.393 km² (+0.001%) |

## 4. QA gate — empirical verification (opens actual files, never the manifest)

**Result: PASS — 0 critical failures, 0 warnings, 62 checks**
(`outputs/qaqc/baseline_qaqc_report.md`, generated 2026-10-23T08:07Z)

Covers: CRS / resolution / shape / origin / AOI-envelope coverage for all 8 rasters,
value bands and class sets, nodata shares, area-sum rules (AOI mask, WorldCover
partition, WDPA union), roads clip sanity, cross-layer grid identity.

Rule corrections made *at the gate*, each kept as an explicit record rather than a
silent edit:

1. **CCI-LC legend** — QA/ingest allowed-set extended to the full official 38-code
   legend (sub-codes 11/12/61/…; **210 = water bodies**, 190 = urban; 80 is
   needleleaved deciduous, *not* water). Source of truth: official
   `CCI-LC_Maps_Legend.pdf`, now tracked in `docs/reference/`.
2. **WDPA union vs sum** — the "raster ≥ vector" rule compared against the polygon
   *sum*; WDPA designations overlap (Western Ghats Eco-sensitive Area contains the
   Nilgiri PA slice, intersection 298.4 km²), so the sum (1164.1 km²) double-counts
   and is unreachable by any union raster. Rule now tests against the union
   (855.8 km²; raster 863.9 ✓); both numbers reported.
3. **all_touched margin** — allowance forgot the base area (could never pass);
   now union × 1.25 + 5 km².
4. **WDPA nodata semantics** — unprotected = nodata legitimately (57.6% of AOI);
   replaced the generic 20% warn with a failed-burn guard (warn only if protected
   share <1% or >99%).

## 5. DEM low-value finding — investigated, not an artifact

Grid-wide minimum of 2.81 m (whole snapped rectangle) triggered review; measured
facts: inside the AOI the minimum is 117.9 m, and **every sub-300 m pixel lies within
~2 km of the district edge** (median 373 m) — the simplified boundary fringes into
Kozhikode-side lowlands. Independent elevation API checks on the lowest points returned
328 m / 299 m against the DEM's 117–300 m (API grid smoothing), with mid-district
controls at 735/734 m. Verdict: genuine boundary-fringe terrain; no masking applied;
QA band (0–3500 m) unchanged.

## 6. Registry coverage & geocoding precision (audit-D-1)

**Coverage (audit-D-1 coverage start year verified):** all 51 Wayanad rows carry dated
orders spanning **2024-01-27 → 2026-07-03** (17/17/17 across 2024/2025/2026), all under
file number `M5-1903/2015`, validity 3 years (expiries 2027-01 → 2029-03). The list is
a snapshot of *currently valid* approvals — pre-2024 approvals whose orders lapsed are
not enumerable from it (timing-cohort caveat for dev-D-4; OI-4 partially closed).

**Geocoding (round 2, 2026-10-23; round 1 archived):**

| | round 1 (archived `_r1`) | round 2 (current) |
|---|---|---|
| geocoded | 51/51 | 51/51 |
| inside district | not achieved at fine precision | **51/51 (100%)** |
| precision | P4×8, **P5×43** | P2×2, P3×12, P4×23, P5×14 |
| engines | Nominatim only | Nominatim 44, Photon 7 |

Round-2 query ladder: PIN structured → PIN free-text → full address → known-Wayanad
locality → Photon cross-check → district fallback (last resort); candidates scored
in-district > Wayanad-label > finer precision > query order; no point is jittered.
Residual P5 = 11 PIN-centroid placements + 3 district fallbacks. 44 of 51 facilities
share one of 11 locality-centroid coordinates — the honest locality-level placement.

**Claim caps (binding):** P3/P5 = locality-level, *not* facility-exact coordinates;
facility-exact placement requires the separate imagery existence-verification step;
precision classes cap downstream claims; construction dating remains forbidden
(prereg §5). Success-rate log: `outputs/qaqc/geocode_log.json`.

## 7. Verification items — completed 2026-10-23

- **audit-D-10 (R1 ordered gate): READY at village/aggregate level; NOT_READY at point
  level.** Paper: Morrison et al. (2025), *Global Ecology and Conservation* 62:e03742,
  DOI 10.1016/j.gecco.2025.e03742. DAS verbatim: *"Data will be made available on
  request. Original_records_sensitive_data_removed_including_namesandaddress.xlsx
  (Figshare)"* — dataset DOI 10.6084/m9.figshare.27908769.v1 (CC BY 4.0; 4 sheets
  2011–2014; 2,762 rows). Points **do not exist at source** (*"did not contain GPS
  locations … recorded to the village name level"*; simulated locations) → the
  paper→data-statement→point-screen chain terminates at the source; the registered H3
  fallback stands. The audit/matrix row description ("*Frontiers*, 1,942 incidents
  2011–2023") is a superseded three-way conflation — actually *GECCO*, events
  **2011–2014** (2011–2023 = raster projection window only); corrected append-only in
  audit §11 and the matrix verification log. Outcome data was **not downloaded**
  (availability verified only — prereg §5).
- **OI-5 / citation verifications:** M1 **verified** (DOI 10.1057/s41599-023-01609-x;
  CR 0.085 / 0.019; 19% suitable); B1 **verified** (DOI 10.1007/s12040-020-01428-7;
  AUC 0.75/0.70; ~15% high zones matches); A4 DOI confirmed but numbers **not**
  confirmable (closed access — flag stays); B4 venue confirmed (DOI
  10.1016/j.ijdrr.2015.08.008) but 18% figure **secondary-corroborated only** (flag
  stays).
- **OI-4 scheme start year — closed:** scheme origin **2006** (GO (MS) 299/06/TSM,
  18-08-2006), revised **2015** (GO (MS) 324/15/TSM, 28-12-2015), under order
  M5-1903/2015 dated 06-08-2019; the file-number year is *not* a start year. Order PDF
  hashed (`85288c0d…`). Published annexures exist only for 2017/2019/2020/2022/2023
  batches — no 2015/2016 approvals are published (supersession logged in audit §11).
- **D-2 / D-3 / D-4 acquired and hashed:** D-2 portal snapshot (111/111 cards;
  form-POST + scrollajax assembly recorded in manifest note), D-3 = ecostat pub. 286
  only (audit's "119, 150" conflation corrected — those are D-4 books; no hotel survey
  later than 2014-15 exists on ecostat), D-4 = both series (arrivals PDF 2025-26 +
  KTS book 2019) — **provenance-only; no arrivals numbers computed pre-freeze**.

**Residual (non-blocking, carried forward):** "fresh vs renewal" order semantics is
inference only (no `renew` token anywhere); A4 numbers + B4 primary text; matrix rows
A5/B5 outside this queue; queue item 4 (C1↔C2 independence); facility-exact existence
verification (precision-capped geocoding logged instead); audit-D-5…D-8 hazard downloads
(outside C2's baseline-completeness question).

## 8. Data-completeness verdict → input to C2

- **Baseline covariate stack: complete and QA-PASS** — 9 raw baseline/registry sources
  hashed (17 sources total incl. derivatives and registry documents), 8 rasters + 2
  vectors + distance raster on the frozen grid, 0 critical / 0 warnings at the gate.
- **Registry work: complete for P1 scope** — coverage semantics verified (coverage
  start 2024-01-27; scheme 2006/2015 closed at OI-4), geocoding at locality-level
  precision with 100% in-district results, logs archived.
- **R1 ordered gate (audit-D-10): executed and logged** — aggregate READY, points do
  not exist at source; registered fallback unchanged.
- **Acquisition/registry sources D-2/D-3/D-4: on disk with hashes** (D-3/D-4 content
  is provenance-only until freeze).
- **Remaining for C2 to weigh (non-blocking, logged):** A4-numbers/B4-primary verify
  flags, fresh-vs-renewal inference, hazard downloads D-5…D-8, facility-exact existence
  verification. **No baseline-completeness blocker is outstanding — C2 can decide on
  this report.**
