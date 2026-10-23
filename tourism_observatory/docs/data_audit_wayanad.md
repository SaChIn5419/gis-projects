# Data audit — Wayanad (P0 deliverable, §6 checklist)

**Status: FROZEN pre-analysis.** Companion to
`tourism_observatory/docs/preregistration_wayanad.md`.
Checklist basis (adopted from the program's data-audit gate): assets identifiable ·
multi-year imagery · hazard+exposure at compatible resolution · observed outcome to
validate against · ≥1 economic quantity without invented assumptions · reproducible.

**Verdict v1 (frozen original): PASS** — 6/6 checklist items satisfied, with three tracked risks (R1–R3).
**Verdict v2 (post-C1, per deviation entry D-6 in preregistration): CONDITIONAL GO — P1 baseline acquisition only.**
Reason: "to-download / digitize / to-obtain" statuses are not confirmed availability;
public existence ≠ file on disk; the PASS qualification is deferred to the P1
data-completeness report. P1 authorized scope: downloads + documentation, baseline
terrain/accessibility covariates, facility-existence verification, geocoding and
raster-alignment tests, provenance reports — **no H1–H4 outcome maps, no
treatment-vs-control tests.**

## 1. How to read each row

Columns: **Status** = verified-public / to-download / digitize / fallback-needed.
**Risk** = L(low) / M(medium) / H(high) with mitigation.

## 2. Registry & tourism data

| # | Source | What it gives | Access / license | Coverage | Gaps | Status | Risk |
|---|---|---|---|---|---|---|---|
| D-1 | Kerala Tourism approved-homestay list (`keralatourism.org/where-to-stay/download_approved_list/4`) | Name, full address, district, order no., approval date | Public web list; use with attribution | All annexures, from Dt. 2015 scheme | Approved subset only — unregistered facilities invisible | to-download (verify file formats) | L — geocoding success-rate log kept |
| D-2 | Kerala Tourism service-provider portal (hotels/resorts classified by district) | Classified hotel/resort registry | Public portal | Statewide | Classified hotels ≠ all operating resorts | to-download | L |
| D-3 | Dept. of Economics & Statistics hotel & restaurant survey (ecostat publications: 286, 119, 150) | District hotel counts **with year-of-starting cohorts** (Wayanad = 413) | Public PDFs | Historical cohorts | Survey years uneven | to-download | L |
| D-4 | Kerala Tourism Statistics (annual series) | District-wise arrivals (domestic/foreign) over 20+ years | Public PDFs | 2000s→present | 2020–21 pandemic disruption | to-download | L — **V1 target** |

## 3. Hazard & terrain

| # | Source | What it gives | Access / license | Coverage | Gaps | Status | Risk |
|---|---|---|---|---|---|---|---|
| D-5 | ISRO/NRSC *Landslide Atlas of India* (2023) | District incidence, exposure ranks, route inventories (Wayanad among Kerala top exposure) | Public PDF (ndem.nrsc.gov.in) | 1998–2022 | Shapefile download unclear → **digitize points** | to-download + digitize | M — digitization effort logged |
| D-6 | 2024 Chooralmala–Mundakkai post-event studies (published + news) | Scar extents, mapped observations | Literature | One event | Variable precision across sources | to-compile, cite each | M — cross-source consistency check required |
| D-7 | DEM (Copernicus GLO-30 / CartoDEM) → slope, HAND, drainage | Continuous terrain | Open | Global | 30 m limits micro-scale slope | to-download | L |
| D-8 | IMD gauges + IMERG 0.1° (+ ERA5 for context only) | Extreme-rainfall timing for landslide windows | Open / IMD registration | 1980→ | IMERG primaries fine for seasonal, not point-scale | to-download | L |

## 4. Wildlife conflict (V2 hinge — tracked risk R1)

| # | Source | What it gives | Access / license | Coverage | Gaps | Status | Risk |
|---|---|---|---|---|---|---|---|
| D-9 | WII–PE *Kerala HEC Report* (2008–2025), MoEFCC PDF | State dataset: mortality, casualties, **hotspot maps**, LULC links | Public PDF (moef.gov.in) | Kerala statewide | Maps, not confirmed point shapefiles | to-download + digitize | M |
| D-10 | "Elephants in the farm…" (2025, *Frontiers*) — 1,942 Wayanad incidents 2011–2023, seasonal risk modelling | Published benchmark + possibly data availability statement | Paper public; raw points **unconfirmed** | Wayanad 2011–2023 | Points may not be in supplement | to-obtain → **fallback chain: paper data statement → author contact → RTI → hotspot digitize** | **H (R1)** — H3 downgrades to hotspot-only if all fail; logged |

## 5. Land systems & exposure

| # | Source | What it gives | Access / license | Coverage | Gaps | Status | Risk |
|---|---|---|---|---|---|---|---|
| D-11 | Landsat 5/7/8/9 (GEE) | 30 m time series (baseline + outcome composites) | Open | 1984→present | Monsoon cloud → dry-window compositing | to-build | L |
| D-12 | Sentinel-1 SAR (GEE/ASF) | Wet-season structural change where cloud defeats optical | Open | 2014→ | Speckle handling | to-build | L |
| D-13 | Sentinel-2 (GEE; reuse `s2_composites.py` pattern) | 10 m dry-season composites | Open | 2015→ | Cloud calendar per above | to-build | L |
| D-14 | ESA CCI Land Cover annual 300 m (1992–2022) + CLC-style trajectory check | Long trajectory backbone | Open | Annual | 300 m coarse → assist, not primary | to-download | L |
| D-15 | ESA WorldCover 2020/21, GLAD 30 m annual | Recent catch-up classification | Open | 2000/2020 | Class harmonization across products required — **harmonization table documented, not ad hoc** | to-download | M — class-harmonization decisions pre-frozen in ingest config |
| D-16 | Hansen GFC | Tree cover/loss proxy for H1 robustness | Open | 2000→23 | — | to-download | L |
| D-17 | Google Open Buildings v3 + OSM + WorldPop | Building footprints / population exposure | Open (CC BY / ODbL) | India covered | OLM resort detection partial | to-download | L |
| D-18 | WDPA | Protected-area exclusion (both arms) | Free, registration required, **not redistributable** — attribution recorded in data_sources doc | Global | All-polygons conservative rule (Jhabua precedent) | to-download | L |
| D-19 | MoEFCC *Elephant Corridors of India 2023* + WTI | Corridor polygons & threat tables | Public PDF | Approved corridors | Georeferencing coarse | digitize if needed for H3 covariates | M |

## 6. Community events (tracked risk R2) — observed-outcome category separate from HEC

| # | Source | What it gives | Status | Risk |
|---|---|---|---|---|
| D-20 | Documented events: Muthanga (2001), Jenu Kuruba estate/forest disputes, others found via court/press/NGO reports | Structured table: date · location · type (protest/legal/grievance) · source URL (never a severity score) | **manual compilation ongoing** | **M (R2)** — documentation bias stated explicitly in brief; coverage is archive-dependent |
| D-21 | Kerala forest dept. / revenue orders where discoverable | Official confirmation of some events | opportunistic | L |

## 7. Assets & economic quantities (checklist items 5–6)

- **Asset register:** buildings (D-17) intersected with hazard classes → exposure registers.
- **Economic quantity without invented assumptions:** accommodation cohort investment proxy
  (D-3 year-of-starting) + NGT-style capacity/utilization stats *where Wayanad equivalents
  exist* → candidate adaptation-cost comparisons remain **scenario ranges only**.
- **Reproducibility:** every source lands in `data/manifest.json` with hashes (Jhabua
  pattern); registry-derived layers re-derivable from committed digitization scripts.

## 8. Three tracked risks summary

| ID | Risk | Severity | Mitigation chain | Residual |
|---|---|---|---|---|
| R1 | HEC incident points unavailable | H | paper data statement → author contact → RTI → hotspot digitize; H3 downgrade documented | M |
| R2 | Community-event compilation bias | M | source-linked event table; explicit caveat; separate category | M |
| R3 | Imagery-dating of tourist construction post-cloud/registry gaps | M | registry dates proxy first; image dating only post-freeze; agreement reported | L |

**Checklist sign-off:** assets ✅ · multi-year imagery ✅ · compatible resolution ✅ ·
observed outcome for validation ✅ (D-9/D-10 primary; D-5/D-6 hazard) · economic quantity
✅ (scenario-only) · reproducible ✅ → **GO for P1 data acquisition once user cross-checks.**

*(v1 wording — superseded on 2026-10-22 by verdict v2 CONDITIONAL GO in the header above;
recorded as dev-D-6 and dev-D-9. Original text retained.)*

---

## 9. C1 review outcome (2026-10-22) — status supersedes the v1 line above

| Review action register item | Disposition | Where recorded |
|---|---|---|
| BLOCK — H2 null model + scar contradiction | Resolved: H2 split into H2a (siting preference, hazard-blind eligibility domain, calibrated access/elevation null) + H2b (event exposure, descriptive register); populations separated | prereg D-2 |
| BLOCK — HEC data feasibility | Resolved: hard ordered gate (paper → data statement → point screen); fallback = descriptive hotspot-overlap only, no count models on rasterized hotspots | prereg D-3; risk R1 chain unchanged |
| HIGH — H1 timing/units/buffer overlap | Resolved: association estimand (causal language barred), timing cohorts incl. pre-existing-development stratum, exact 1 km parcel grid, facility-cluster rule, 750 m from facility point, ≥50% parcel rule, transition-matrix output | prereg D-4 |
| HIGH — H3 temporal leakage | Resolved: primary covariates = pre-2011 baseline; no covariate window after 2023 | prereg D-3 |
| HIGH — H4 observation process | Resolved: dispute unit, dedup rule, precision classes, separate report types, reportable-area permutation null, EXPLORATORY flag if <15 disputes | prereg D-5 |
| HIGH — audit PASS vs unverified data | Resolved: verdict → CONDITIONAL GO (v2, above); verification = file on disk + manifest hash | prereg D-6 |
| NORMAL — references + V1–V3 tightening | Resolved: V1 category-alignment precondition, V2 comparability precondition, V3 scar-mapping-only wording; ledger added | prereg D-7; matrix §E |

## 10. Source-type ledger & verification tasks

Every row of §2–§6 gains the fields `type ∈ {peer-reviewed, official inventory,
institutional report, official statistics, news, NGO documentation, grey, open
satellite/raster (unclassified source data)}` and `independence` (links to other
sources). Assignments below were **corrected at dev-D-9** (an earlier draft assigned
audit-D-19 twice and mislabeled audit-D-9 "peer-reviewed+official"; it is institutional):

| audit rows | Type | Independence notes |
|---|---|---|
| D-1 · D-2 · D-3 · D-4 | official statistics / registry | categories differ across products; aligned first per dev-D-7 before any agreement number |
| D-5 | official inventory | basis of matrix lit-B2/lit-B3 — one evidentiary stream |
| D-6 | peer-reviewed + news mix (per-source) | cross-source consistency check required (risk M) |
| D-7 · D-8 | open satellite data + official gauge data | independent providers |
| D-9 | institutional report | shares WII–PE origin with matrix lit-C2/lit-C4 — one stream; **not peer-reviewed** |
| D-10 | peer-reviewed (verify; data statement pending) | identical source to matrix lit-C1 under the dev-D-9 ID convention |
| D-11 – D-17 | open satellite/raster or open vector | independent providers; class harmonization pre-frozen (D-15 note) |
| D-18 | official inventory (licensed; **not redistributable**) | attribution recorded only |
| D-19 | official inventory + WTI institutional | corridors; overlaps matrix lit-C5 — one stream |
| D-20 | news / NGO / court mix (manual compilation) | grey tier; documentation-bias caveat (risk R2) |
| D-21 | official record | corroboration only |

Independence rule: two sources deriving from one underlying report are treated as one
evidentiary stream. Verification queue (P1 documentation, unchanged): audit-D-10 (= lit-C1)
full text + data statement; matrix lit-B1 Mussoorie susceptibility method/AUC exactness;
remaining `verify`-flagged DOIs. Row-ID prefixes follow dev-D-9: `audit-D-x` here,
`lit-Cx`/`lit-Mx` in the matrix, `dev-D-x` in the preregistration.

## 11. P1 acquisition log (append-only; PREREG §5 boundary respected)

Original §2–§6 tabular statuses are retained above; this section records what has
actually landed as a file with a SHA-256 in `data/manifest.json` (verification rule per
dev-D-6). Nothing here is outcome analysis.

| date | audit source | acquired | artifact | QA result |
|---|---|---|---|---|
| 2026-10-22 | §1 AOI boundary (geoBoundaries IND ADM2, pinned `9469f09`, ID `IND-ADM2-76128533`) | ✅ simplified GeoJSON, 736 features | `data/raw/geoBoundaries-IND-ADM2_simplified.geojson` | Wayanad feature extracted (exactly 1 match); reprojected EPSG:32643; area 2,026.4 km²; lon extent 75.77–76.44 E → **UTM zone 43 confirmed** (OI-3 closed) |
| 2026-10-22 | §2 audit-D-1 approved-homestay registry | ✅ live page snapshot as on 22-10-2026 | `data/raw/keralatourism_approved_homestays_2026-10-22.html` → parsed Wayanad CSV | 1,386 rows / 14 districts; **51 Wayanad facilities; 0 duplicate names**; all 51 carry dated orders |

**Empirical findings affecting registered design (recorded, not acted upon):**

1. **OI-4 (registry temporal coverage) — partially closed by evidence.** The live list
   shows only *currently valid* approvals; the Wayanad subset's order dates are 2024/2025/
   2026 (17 + 17 + 17), with scheme numbers referencing the 2015 framework. The order
   date is a **latest-approval/renewal date, not a construction or first-approval date**.
   Consequence for dev-D-4: the "pre-existing development" stratum will be large, and
   first-approval dating for older facilities requires historical annexure PDFs (available
   for the 2015 scheme) or imagery evidence. Geocoding/existence verification comes next;
   no timing claims are made now.
2. **Boundary simplification.** Simplified ADM2 understates district area vs the official
   ≈2,131 km² (≈4.9%). Acceptable for AOI/parcel work; recorded in the manifest. If
   parcel-edge sensitivity matters post-freeze, the unsimplified ADM2 file is the fallback
   (same pinned release, recorded as a potential dev entry only if adopted).
3. Registry "Approved as" classes (Diamond/Gold/Silver House) are retained as facility
   attributes — usable later ONLY as descriptors; any class-based comparison is
   post-freeze analysis, not P1.

Open P1 items (unchanged): audit-D-2/D-3/D-4 registries; §3 hazard/terrain downloads;
audit-D-10 HEC gate (R1); geocoding + imagery existence verification; baseline terrain/
access covariates (GEE composites) after these.

### 2026-10-23 — baseline covariate acquisition (7 raw sources) + ingest + QA gate

| date | audit source | acquired | artifact | QA result |
|---|---|---|---|---|
| 2026-10-23 | §3 audit-D-7 terrain | ✅ Copernicus GLO-30 tiles N11E075 + N11E076 | `data/raw/Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif` (`dbddab32…`) + `…_E076_00_DEM.tif` (`717edb70…`) | warped 30 m `dem_copernicus30m_32643.tif`; inside AOI 117.9–2171.6 m, nodata 0%; slope (Horn) 0–66.9° inside AOI; gate PASS on value band |
| 2026-10-23 | §5 audit-D-15 land cover | ✅ ESA WorldCover 10 m 2021 v200 tile N09E075 | `data/raw/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif` (`913f22dd…`) | mode-resampled 30 m; AOI classes {10,30,40,50,60,80,90} ⊆ allowed; classes tile AOI exactly (area-sum PASS) |
| 2026-10-23 | §5 audit-D-16 tree cover | ✅ Hansen GFC-2024 v1.12 tile **20N_070E** | `data/raw/Hansen_GFC-2024-v1.12_treecover2000_20N_070E.tif` (`f5794be5…`) | 0–100, 83.1% ≥10% (year-2000 baseline); **incident:** first pick `10N_070E` was wrong (GFC tiles named by NORTH edge; 10N = 0–10N) — deleted before ingest, corrected note in manifest |
| 2026-10-23 | §5 audit-D-14 historical LULC (OI-2) | ✅ ESA CCI-LC L4 300 m annual **2005, v2.0.7cds**, tile N00E045 (PC-signed blob) | `data/raw/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2005-v2.0.7cds-N00E045-lccs_class.tif` (`cf9e4c21…`) | exact vintage fixed (OI-2 closed); **incident:** first gate run rejected codes 11/12/61/121 — resolved against official `CCI-LC_Maps_Legend.pdf` (now tracked in `docs/reference/`): full 38-code legend incl. sub-codes; **210 = water bodies** (190 = urban); class set corrected in ingest + QA, never guessed |
| 2026-10-23 | §5 audit-D-18 protected areas | ✅ WDPA/WDOECM Oct 2026 Public IND (pinned, = Jhabua release), 262 MB | `data/raw/WDPA_WDOECM_Oct2026_Public_IND.zip` (`2d5ea2f7…`; git-ignored, hard-deny) | **incident:** release ships a File Geodatabase, not shapefiles — `build_wdpa` rewritten (vsizip `.gdb` + extraction fallback); 12 polygons clipped, union 855.8 km² (sum 1164.1 double-counts the WGESA∩Nilgiri 298.4 km² overlap — **incident:** the gate's sum-rule compared against an unreachable number, rule corrected to union); raster 863.9 km², protected share 42.43% |
| 2026-10-23 | §5 (access covariate, dev-D-4 label) | ✅ Geofabrik southern-zone PBF, dated redirect `southern-zone-261020.osm.pbf` | `data/raw/southern-zone-261020.osm.pbf` (`e646eb58…`) | 13,205 highway features clipped (100% inside AOI); `road_dist_m_32643.tif` 0–5860 m in AOI; labelled **current-network proxy** |
| 2026-10-23 | §1 AOI mask | ✅ rasterised AOI mask | `data/processed/aoi_mask_32643.tif` | 2026.412 km² vs vector 2026.393 km² (+0.001%, fail >2%) |
| 2026-10-23 | **QA gate (all 8 rasters)** | ✅ `scripts/p1_baseline_qaqc.py` opens every file | `outputs/qaqc/baseline_qaqc_report.md` | **PASS — 0 critical, 0 warnings, 62 checks** (grid identity, bands, classes, nodata, area-sums). DEM sub-300 m fringe investigated first: all such pixels within ~2 km of district edge (median 373 m), independent elevation API agrees (328/299 m vs DEM 117–300; controls 735/734) → genuine boundary-fringe terrain, not an artifact |
| 2026-10-23 | §2 audit-D-1 geocoding (round 2) | ✅ 51/51, **100% inside district** | `data/processed/registry_geocoded_2026-10-23.csv` + `.geojson` (`registry_geocoded_r2` manifest entry); log `outputs/qaqc/geocode_log.json` | precision P2×2, P3×12, P4×23, P5×14 vs round 1's P5×43 (round 1 archived as `_r1`); PIN-first + Photon ladder; no jitter; P3/P5 capped at locality-level claims; 44 facilities share 11 locality centroids |
| 2026-10-23 | §2 audit-D-1 coverage start year | ✅ verified from parsed orders | same registry CSV | orders span **2024-01-27 → 2026-07-03** (17/17/17), file `M5-1903/2015`, 3-yr validity to 2027–2029 → snapshot semantics confirmed; coverage-start = 2024 for the current list; no historical claims possible from this file alone |

**Supersession note (append-only):** the "Open P1 items" line immediately above is
superseded for geocoding (done, round 2) and for baseline terrain/access covariates
(acquired as downloaded tiles + OSM clip rather than GEE composites — same covariates,
different acquisition path; recorded here as an acquisition-path deviation, not a
design change). **Still open:** audit-D-2/D-3/D-4 registry downloads, audit-D-10 HEC
gate (R1), imagery existence verification (facility-exact placement), §3 hazard
downloads (D-5…D-8 — not P1-blocking for C2's baseline-completeness question).

### 2026-10-23 (later) — R1 gate executed + citation/OI verifications + D-2/D-3/D-4 acquisitions

| date | item | verdict / artifact | evidence |
|---|---|---|---|
| 2026-10-23 | **audit-D-10 = lit-C1 HEC data-availability gate (R1)** | **READY — village/aggregate level; NOT_READY — point level.** Figshare dataset open: DOI `10.6084/m9.figshare.27908769.v1`, CC BY 4.0, 4 sheets (2011–2014), 2,762 rows, columns `Place, Range, Section, Nature of Lost, Species, Date, Time, Remarks` | Paper DAS verbatim: *"Data will be made available on request. Original_records_sensitive_data_removed_including_namesandaddress.xlsx (Figshare)"*. Points do not exist at source: *"did not contain GPS locations … recorded to the village name level"*, locations *"simulat[ed] … using conditional random sampling"* → the paper→data-statement→point-screen chain terminates at the source (no GPS ever collected); author contact/RTI cannot recover non-existent coordinates. Consequence per the registered fallback in this row: H3 stays at village/hotspot-level descriptive use — **no point outcomes, no count models on rasterized hotspots** (decision text unchanged; logged here). |
| 2026-10-23 | **§2 D-10 row description — CORRECTION (append-only supersession of the row text)** | The paper is **Morrison et al. (2025), *Global Ecology and Conservation* 62:e03742**, DOI `10.1016/j.gecco.2025.e03742` — **not** *Frontiers*; the 1,942 negative HEI events are **2011–2014** (2011–2023 is only the projection window of the 26 raster stacks) | The row's "(2025, *Frontiers*) — 1,942 incidents 2011–2023" is a three-way conflation (journal / year-window / period); matrix lit-C1 carries the same conflation, corrected under its own append-only log |
| 2026-10-23 | **OI-4 scheme start year** | **VERIFIED — two dates; file number is not a start year.** Scheme origin **2006** (`GO (MS) No. 299/06/TSM dated 18-08-2006`), revised **2015** (`GO (MS) No. 324/15/TSM dated 28-12-2015`, Diamond/Gold/Silver), under order `M5-1903/2015` dated 06-08-2019 | artifact `data/raw/homestay_order_M5-1903_90th_2019.pdf` (`85288c0d…`); verbatim *"valid for three years from the date of issue"*. Annexure PDFs exist only for 2017/2019/2020/2022/2023 batches → the earlier "all annexures, from Dt. 2015 scheme" wording is superseded: **no 2015/2016-dated approvals are published** |
| 2026-10-23 | **OI-5 / matrix lit verifications** | **M1 VERIFIED** (Topuz & Deniz 2023, DOI `10.1057/s41599-023-01609-x`: AHP weighted-overlay; CR = 0.085 criteria / 0.019 land-use forms; 19% district suitable) · **B1 VERIFIED** (Ram et al. 2020, DOI `10.1007/s12040-020-01428-7`: bivariate Yule LSM; success-rate AUC 0.75, prediction-rate AUC 0.70; ~15% high+very-high ✓ matches matrix) · **A4 half-verified** (DOI `10.1007/s41324-020-00368-0` confirmed; the "2009–2019" figures NOT confirmable — closed access, no abstract; row keeps its verify flag on numbers) · **B4 half-verified** (DOI `10.1016/j.ijdrr.2015.08.008` venue confirmed; the 18% Mussoorie Grade-5 figure is secondary-corroborated only — primary Elsevier full text blocked) | verification is documentation work under dev-D-8; ledger detail appended to `literature_matrix.md` |
| 2026-10-23 | §2 audit-D-2 classified portal | ✅ Wayanad slice snapshot | `data/raw/keralatourism_classified_wayanad_2026-10-23.html` (`3a493ba2…`) — 111/111 cards (38 resorts, 47 homestays, 13 hotels linked); assembled via form-POST + 3 scrollajax chunks (anti-bot GET returns only the auto-submit form; method recorded in manifest note) |
| 2026-10-23 | §2 audit-D-3 hotel survey | ✅ ecostat publication 286 only | `data/raw/ecostat_286_report_hotels_restaurants_2014-15.pdf` (`f8bb418f…`) — Table 1.1 Wayanad = 413 (346 panchayat + 67 municipality; cohorts 7,3,9,8,16,24,104,242). **Correction:** the row's "(publications 286, 119, 150)" conflated series — 119/150 are *Kerala Tourism Statistics* books (= D-4); **no hotel survey later than 2014-15 exists on ecostat** (search-bounded) |
| 2026-10-23 | §2 audit-D-4 Kerala Tourism Statistics | ✅ two series, provenance-only | `data/raw/keralatourism_tourist_statistics_2025-26.pdf` (`7fe9107c…`, arrivals series, index 2003–2025) + `data/raw/ecostat_150_kerala_tourism_statistics_2019.pdf` (`481c812a…`, book series 2017/2018/2019). **No arrivals numbers computed or compared pre-freeze** (prereg §5; V1 target remains post-freeze) |

**Residual uncertainty (logged, not resolved):** "fresh vs renewal" order semantics —
no `renew`/`fresh` token exists in the registry, portal, or order PDFs; rolling 3-year
windows support "latest approval/renewal" as **inference only** (NOT CONFIRMED).
A4 validation numbers and B4 primary-text confirmation remain open in the matrix queue;
rows A5/B5 were outside this verification queue and stay `verify`-flagged.
