# LEARNING.md — Jhabua Agroforestry Land Screening (VM0047)

Living reference for the project. Every file below, how it works, how to run it, and
what it is for. Read this when you want to revisit a file or when a new session starts.

> **Update 2026-10-21:** the zip screening core and the old repo scaffold were merged.
> Sections 3.1 and 3.7–3.9 describe the *old* scaffold and are kept for history.
> **Section 10 is the current implementation and the teaching walkthrough.**
> Start there if you are new to the project.

---

## 1. Project overview

**Goal** — split one Indian district (Jhabua, MP) into candidate *degraded land* for a
nature-based carbon project (agroforestry under Verra **VM0047 ARR v1.1**), using only
free public data, with full QA/QC and documentation. The result is a reusable,
config-driven pipeline + documentation you can hand to a contractor and cite on a CV.

**Deliverables**
- Eligible-land area + **exclusion reason-code waterfall** (every pixel: one reason, or
  eligible).
- **QA/QC gate** (CRS, grid alignment, geometry validity, no-data share, area
  reconciliation) — runs before any analysis.
- **Stability map** from ~300 sensitivity scenarios (Dirichlet weights, buffers ±30°,
  slope 15–20°) → 0–100 "robust / sensitive / unlikely".
- **Validation**: stratified points (eligible AND excluded), confusion matrix +
  per-class accuracy + hectare-weighted area estimate with CI (Olofsson et al. 2014).
- 3–4 maps (study area, exclusions, suitability, top villages) + README + methodology /
  assumptions / limitations.

**Reference projects (scaled, never data)** — IBCRI: 10,000 ha / 5.6 Mt / 14 tCO₂·ha⁻¹·yr⁻¹
(Sylvera A, VM0047 ARR v1.1). Swiftgreen: 20,000 ha / 11.4 M trees / 8.55 Mt / ~11 tCO₂·ha⁻¹·yr⁻¹.
Cite the developer pages, never claim their data. Screening is pre-feasibility only.

---

## 2. The 4-week plan (do not reorder)

| Week | What | Key files |
|---|---|---|
| **W1** | Foundations: repo + `config.yaml` (`eligibility.mode`); data acquisition + SHA256 manifests; GEE account + tutorials; cloud-masked dry/monsoon composites; **dummy end-to-end run**; QA gate module | `config.yaml`, `run_pipeline.py`, `src/qaqc.py`, `data/manifest.json` (coming) |
| **W2** | Screening: load + clip + reproject to EPSG:32643; validity checks; per-pixel reason codes (first failing filter wins); exclusion waterfall + chart; composites in QGIS; first maps | `src/ingest.py`, `src/screening.py`, `src/qaqc.py` |
| **W3** | Scoring + sensitivity: weighted overlay (NDVI 30 / slope 25 / water 25 / road 20); Dirichlet ~300 scenarios, buffers ±30°, slope 15–20; stability score 0–100; stratified validation incl. excluded pixels; confusion matrix + per-class + hectare-weighted CI | `src/scoring.py`, `src/sensitivity.py`, `src/validation.py` |
| **W4** | Validation + maps + docs: 3–4 maps; methodology.md + assumptions.md + limitations.md; README; QA report; polish | `docs/*`, `README.md` |

Cut order if short: extra maps → village stats (fall back to block) → third map.
Keep: waterfall, QA gate, stability map, excluded-pixel validation, eligibility mode.

---

## 3. File reference (in this order of creation)

### 3.1 `config.yaml` — every tunable choice lives here
**Purpose** — nothing else infers a number; the pipeline reads it. The single most
important file for the interview ("how do you change a weight?").
**How it works** — sections: `project` (CRS, district, boundary, source year), `eligibility`
(mode census|area + the now-deprecated `non_forest_years` so a reviewer can see the
v1.0→v1.1 change), `landcover` (candidate/exclude classes, cropland gets code 6), `exclusions`
(slope, buffers, min patch), `suitability` (weights + stability), `validation`, `outputs`.
**Usage** — `python run_pipeline.py config/jhabua.yaml`.
**Application** — changing the slope cutoff is one keystroke; the QA gate and the
output names never change.

### 3.2 `README.md` — the one-page brief
**Purpose** — someone else can run the pipeline from one command; start here.
**How it works** — summary, deliverables, method note (v1.1 eligibility rule + why the
v1.0 10-year rule is NOT used), references, what the output will look like.
**Usage** — read before running; the "how to contribute" section points at the QA gate.
**Application** — the CV cover email is seeded from this: name the project, say it models
IBCRI/Swiftgreen, pre-feasibility only.

### 3.3 `run_pipeline.py` — one-command entry point
**Purpose** — the "one command" the job post asks for. Loads the config, validates that
every expected key exists (so a typo can't silently drop a module), prints the run plan.
**How it works** — `load_config()` reads the YAML; a `required` dict lists every key every
module needs; missing keys → fatal exit before anything runs. The print plan is the handoff
to the team.
**Usage** — `python run_pipeline.py config/jhabua.yaml`.
**Application** — every new district becomes a new `config/<district>.yaml`; the pipeline
needs no editing.

### 3.4 `TODO.md` — the 30-item tracker, P0/P1/P2, with the cut order
**Purpose** — the work is tracked in one place; P0 first (builds the case), then P1
(screening), P2 (validation + maps), P3 (docs). Items marked `[x]` mean done.
**How it works** — plain Markdown; no tooling.
**Usage** — rewrite at the end of each session so a later session picks up the same state.
**Application** — the "next action" line in `docs/PROJECTSTATE.md` mirrors the P0/P1/P2
order.

### 3.5 `docs/PROJECTSTATE.md` — the progress tracker (the "memory graph")
**Purpose** — so a later session picks up the same state instead of re-deriving decisions.
**How it works** — phase status table, key decisions (why), blockers, artifact hashes,
next action. Updated after every session.
**Usage** — read this first thing in any session; update it before ending.
**Application** — the tracker is the project's memory: `docs/PROJECTSTATE.md` + `MEMORY.md`
(Hermes memory dir).

### 3.6 `docs/assumptions.md` — the verified eligibility rule
**Purpose** — states exactly which rule the screen implements, from the primary source,
with the v1.0→v1.1 change documented.
**How it works** — sections: eligibility rule (§4.3 of the PDF), what the v1.0 rule was and
why we do NOT use it anymore, area-based mode exclusions, reason-code table, data sources,
limitations, provenance (SHA256 of the Verra PDF).
**Usage** — cited whenever someone asks "what's the eligibility rule?" or "why is 10-year
non-forest not a rule?".
**Application** — the interview answer to "how did you decide what counts as degraded
land?".

### 3.7 `src/qaqc.py` — the QA/QC gate (before any analysis)
**Purpose** — the gate that decides "this data is good enough to screen". Checks:
CRS, grid alignment, geometry validity, no-data coverage, area reconciliation. Critical
failures stop the run; warnings are logged. Exits non-zero on critical failure.
**How it works**

- `GateResult` — one audit row (check name, kind, pass/fail, message, detail).
- `run_selftest()` — the "dummy end-to-end run": synthetic arrays with known answers.
  Deliberately includes two broken layers (misaligned origin + 0.5 ha drift) and proves the
  gate catches them. Prints the results; exits 1 when any is broken.
- `check_crs(record)` — declared CRS vs `WORKING_CRS` (EPSG:32643).
- `check_grid_alignment(records)` — pairwise resolution + origin comparison; first
  mismatch wins.
- `check_geometry_validity(records)` — needs geopandas; if missing, recorded PENDING
  (not PASS — a check that passes without looking at data is decoration).
- `check_nodata_share(record)` — S2 composite no-data/cloud-shadow share vs threshold;
  PENDING until rasterio installs.
- `check_area_reconciliation(config, records)` — `eligible + sum(excluded) == district
  area` within 1%. The accounting that stops silent errors.
- `write_report(...)` — writes `outputs/qaqc/qaqc_report.md`.
- `main(argv)` — argparse: `--selftest`, `--check config.yaml`, `--report config.yaml`.

Usage:
```bash
python src/qaqc.py --selftest      # prove logic on fake arrays (Week 1)
python src/qaqc.py --check config.yaml   # check vs data/manifest.json
python src/qaqc.py --report config.yaml  # write outputs/qaqc/qaqc_report.md
```
**Application** — this is the "maintenance of QA/QC" line on the CV. The gate lives in
Week 1, before any analysis module.

### 3.8 `src/ingest.py` (W2) — load + clip + reproject
**Purpose** — every layer enters the same frame: district clip, EPSG:32643, 10 m grid,
checksummed manifest record.
**How it works** — reads the config boundary, clips each source to it, reprojects to 32643,
computes (rows × resolution) × (cols × resolution)/10 000 = `area_ha`, writes the manifest
record, prints a summary.
**Usage** — `python src/ingest.py config/jhabua.yaml`.
**Application** — the manifest is the contract between the user's files and every later
module.

### 3.9 `src/screening.py` (W2) — reason codes + waterfall
**Purpose** — per-pixel first-failing-filter reason codes (0–8), then the waterfall table
+ chart.
**How it works** — a mask dict `{code: boolean array where the filter REJECTS}`; the loop
assigns a code only where `code == 0` (first failing filter wins); the reason array drives
the waterfall: district area → − tree cover → − cropland → … → = eligible.
**Usage** — `python src/screening.py config/jhabua.yaml`.
**Application** — the review line: "exclusion reason codes so a reviewer can see why any
piece of land was rejected".

### 3.10 `src/scoring.py` (W3) — weighted suitability
**Purpose** — weighted overlay (NDVI 30 / slope 25 / water distance 25 / road distance 20)
and Low/Medium/High classification.
**How it works** — rescaled layers, weighted sum, thresholds from config, class assignment.
**Usage** — `python src/scoring.py config/jhabua.yaml`.
**Application** — the stability map in `sensitivity.py` tests this exact module across
weight draws (Dirichlet), buffer offsets, and slope cutoffs.

### 3.11 `src/sensitivity.py` (W3) — stability score 0–100
**Purpose** — quantify assumption risk instead of arguing with one weight set.
**How it works** — precompute distance transforms once; threshold per scenario; running
per-pixel counter at 30 m (never store all 300 full rasters — 300 × 4 M pixels would be
10–30 minutes of pure Python/NumPy). Classes: robust ≥ 80%, sensitive 30–80%, unlikely < 30%.
**Usage** — `python src/sensitivity.py config/jhabua.yaml`.
**Application** — the interview answer "why a confidence map?" — "weights were judgment
calls, so I tested how much the answer depended on them".

### 3.12 `src/validation.py` (W3) — sampling + accuracy
**Purpose** — stratified samples in eligible areas AND excluded pixels (esp. reason code 3
recet forest loss, code 6 cropland); confusion matrix; producer's/user's per-class accuracy;
hectare-weighted area estimate with CI (Olofsson et al. 2014).
**How it works** — random points in the eligible set + points in the excluded set; the
human labels (or an automated basemap check, clearly flagged as automated); the confusion
matrix and the area estimator.
**Usage** — `python src/validation.py config/jhabua.yaml`.
**Application** — "validated with N points, overall accuracy within ±9% worst case (n=120),
per-class ranges".

### 3.13 `src/report.py` (W4) — maps + exports
**Purpose** — 3–4 clean layouts: study area, exclusions, suitability, top villages; plus
GeoPackage/Parquet exports for a BI tool.
**How it works** — QGIS layout templates driven by the processed shapefiles; print PDFs.
**Usage** — `python src/report.py config/jhabua.yaml`.
**Application** — the deliverable the interviews actually open (maps + Excel-friendly
tables).

---

## 4. Key decisions

| Decision | Why |
|---|---|
| `eligibility.mode` = census \| area | VM0047 v1.1 has two approaches; the rules, cropland handling and waterfall derive from this one key. Census: ≤50 planting units/ha, <10% pre-existing woody biomass (or continuous-cropped/settlements/other lands). Area: non-forest→forest change or existing forest not managed for wood products in 10 yrs. |
| Cropland = its own reason code (6) | VM0047 census method explicitly treats cropland as eligible; blanket exclusion is wrong. Keep it + sensitivity test. |
| Reason code 7 (no-data/outside coverage) | Without it the area balance can never close. |
| QA gate before analysis | Prevents the screen from silently running on bad data — the gate that makes "QA/QC" a defensible line. |
| 4 weeks, not 3 | Learning Earth Engine, building the pipeline, hand-labelling points, writing docs: no slack. |
| Cut order: extra maps → village stats → third map | Keeps the differentiators (waterfall, QA gate, stability map, excluded-pixel validation). |

---

## 5. Rules of the game (the "quit rules")

- **Area reconciliation must close.** If it doesn't, stop and find the gap (usually a
  no-data class or a clipped boundary) before continuing.
- **Ambiguous requirement → data-confidence flag, not a rule.** E.g. regrowth to 10–30%
  cover is flagged, not coded. The primary document (the methodology PDF) is the rule,
  not my guess.
- **Excluded pixels must be sampled.** If you only sample eligible land you can measure
  commission but never omission — the screen then cannot claim it found all the degraded
  land it should have.

---

## 6. Reference scales (never projections)

| Project | Hectares | Lifetime removals | Rate | Rating |
|---|---|---|---|---|
| IBCRI | 10,000 | 5.6 Mt | 14 tCO₂·ha⁻¹·yr⁻¹ | Sylvera A, VM0047 ARR v1.1 |
| Swiftgreen | 20,000 | 8.55 Mt | ~11 tCO₂·ha⁻¹·yr⁻¹ | Sylvera A, VM0047, 40 yrs |

Use these in Step 13 only as an illustrative band (8–14 × high-suitability ha), never a
credit forecast.

---

## 8. Data import — why GEE for the pipe, Python for the analysis

**Why GEE for the data, and Python for the analysis.** Every layer is public and
downloadable without a platform; the screening is a Python analysis
(rasterio/geopandas/NumPy). The only reason to touch Google Earth Engine is to
get the Sentinel-2 cloud-masked composites (and optionally WorldCover/Hansen)
without downloading raw orbit data.

- `ee` on PyPI (v0.2, snarez/ee) is an abandoned client: it cannot import on
  Python 3.12 or 3.14 (`import StringIO` fails), so it is **not** part of the
  pipeline and is **not** in requirements.txt.
- The GEE path is the free, non-commercial **Code Editor (browser)**: paste the
  script below, run the exports, download the GeoTIFFs into data/raw/.
- Everything after data acquisition is Python: ingest (clip/reproject), QA gate,
  screening, scoring, sensitivity, validation, maps. That is where the
  "GeoPandas/Rasterio/NumPy" job-skill value lives.

### GEE script
`scripts/s2_composites.py` — paste into the Code Editor. It masks Sentinel-2
with the QA60 cloud bit, builds a dry-season (Jan–Jun) and monsoon-season
(Jun–Sep) median composite, computes NDVI and a bare-soil index (BSI), and
exports both to Drive as 10 m GeoTIFFs into a `s2_jhabua` folder. The
region/asset name at the bottom is a placeholder you replace with your Jhabua
boundary asset.

### Consequences for the work
- The composite year (2024 in the script) is a fixed assumption. A variable
  monsoon shifts dry-season bare soil and wet-season NDVI, which moves the
  "degraded vs cropland" line — that is exactly what the stability map is for.
- Exports are storage-driver (a few hundred MB per stack); the pipeline never
  downloads raw orbit data.
- You (the project owner) download the GeoTIFFs and record SHA256 in
  data/manifest.json before `src/ingest.py` can run.

### Where the work lives
```text
/home/sachindb/Documents/qgisproject_job/
├── config.yaml          # all parameters (eligibility.mode etc.)
├── README.md            # brief
├── run_pipeline.py      # one command entry point
├── scripts/s2_composites.py   # GEE data-import script (Code Editor)
├── src/qaqc.py          # QA gate (written)
├── src/ingest.py        # clip + reproject + manifest (next)
├── docs/PROJECTSTATE.md # progress tracker (memory graph)
├── docs/assumptions.md  # verified eligibility rule
├── TODO.md              # 30-item tracker
└── verra-verify/        # VM0047 v1.1 PDF + extracted text
    └── archived/
```



---

## 9. Next steps
1. data/manifest.json SHA256 per layer (WorldCover, Hansen, GEE composites,
   DEM, OSM, WDPA, boundary).
2. Project venv — done (Python 3.12, pyyaml + geopandas + rasterio + scipy + pytest).
3. Run `src/qaqc.py --check` for the first real gate report.
4. src/ingest.py → then screening, scoring, sensitivity, validation.

*The current merge and walkthrough are in Section 10.*

---

# 10. The 2026-10-21 merge — current implementation and full walkthrough

This section is the current state of the project. It explains **what** was built,
**why** each decision was made, and **how** to read, run and extend it. The earlier
sections remain useful history, but the file names and some rules changed.

## 10.1 The problem: two half-pipelines, not one

When we started, there were two real but unreconciled workspaces:

| | Repo scaffold | Zip screening core |
|---|---|---|
| Config | `config.yaml` | `jhabua.yaml` |
| Screening | no `screening.py` | `screening.py` (19 KB, tested) |
| Ingest | `src/ingest.py` (old, 10 m) | none — expected pre-aligned layers |
| QA | `src/qaqc.py` (manifest-checking) | none |
| Tests | none | 12 synthetic + 1 CLI |
| Data | boundary + S2 | none |

The earlier review was of the **repo scaffold**: the `qaqc.py` that checked a JSON
manifest, the `343,378 ha` S2 result, and the `config.yaml` with a 10% eligibility
cutoff and a 30% Hansen exclusion. Those files were real — they were just in the other
branch. The zip was a newer screening core that assumed ingest/QA already existed.

The zip files were extracted into the project and hashed. The `files/` folder the user
created contains the same five files (same SHA256 values as `files.zip`), so there was
no third variant to reconcile.

**Decision:** keep the zip’s `screening.py` as the canonical screening engine, and
rebuild ingest and QA around the seven aligned layers it needs. The old scaffold is
archived at `archived/v1_scaffold/` for audit; the root `config.yaml` was removed so
nobody accidentally runs the old thresholds.

Current file tree (the parts that matter):

```text
config/jhabua.yaml           # one config, one reason-code contract
src/screening.py             # two-stage waterfall, pure functions + GeoTIFF I/O
src/ingest.py                # raw -> aligned 30 m stack
src/qaqc.py                  # measures the actual rasters
run_pipeline.py              # validate, or --run ingest -> qaqc -> screening
tests/test_screening.py      # synthetic rules tests
tests/test_io.py             # CLI + measured-resolution tests
tests/test_ingest.py         # synthetic raw -> aligned -> QA integration test
docs/assumptions.md          # verified clauses + canonical code table
docs/methodology.md          # step-by-step method
docs/limitations.md          # what cannot be claimed
docs/data_sources.md         # expected raw files and download notes
docs/PROJECTSTATE.md         # state / hashes / next action
```

## 10.2 Why the screening core is the right foundation

The zip’s `screening.py` does four things that the old scaffold did not:

1. **Separates methodology from design.** Stage A is “what VM0047 requires”; Stage B
   is “what this project chooses”. A reviewer can see both numbers.
2. **Writes a `basis` for every waterfall row.** If a clause is not recorded, the row
   says `NO CLAUSE RECORDED` instead of pretending.
3. **Makes the eligible mask order-invariant.** Filter order changes attribution, not
   the set of pixels that survive all Stage-A rules.
4. **Closes the area balance.** Every district pixel gets exactly one code; the sum of
   code areas must equal the district area.

Those properties are more valuable than adding another map. They are the difference
between a defensible screen and a coloured raster.

## 10.3 The methodology, clause by clause

The primary source is `verra-verify/vm0047_v11.pdf`, 81 pages, SHA256:

```text
2fdccb9764a0b06283e974142d0ff250910f81686dc53bcc197f6cf90d53de3d
```

That hash matches `README.md`, `docs/PROJECTSTATE.md` and `docs/assumptions.md`.

### 10.3.1 Census eligibility — §4.3(8) and §6.2

§4.3(8) says the project activity occurs:

> a) within an area with less than 10% pre-existing woody biomass cover; and/or
> b) in an area subject to continuous cropping, or in “settlements” or “other lands”
> land use categories.

§6.2 is stricter for the census crediting baseline:

> 1) occur within an area with pre-existing woody biomass cover of less than 10%; and
> 2) occur in an area subject to continuous cropping, or in “settlements,” or “other
> lands” land use categories.

The code treats `WOODY_COVER` as Stage A: WorldCover tree/mangrove **or** Hansen
`treecover2000 >= 10%` rejects the pixel. Cropland is *not* a Stage-A rejection; it is
a Stage-B design choice. That is conservative: a cropland pixel with 15% woody cover is
still rejected by the woody test.

### 10.3.2 The 10-year rule — §4.4.2(1), not the old v1.0 rule

§4.4.2 says the census approach is not applicable where:

> 1) Woody biomass, which serves a similar purpose as the planting units in the project,
> has been removed within the last 10 years (confirmed via pre-project photos and/or
> attestation).

So the 10-year look-back **is real**, but it is an **exclusion**, not the eligibility
test. The old v1.0 “non-forest for at least ten years” rule is still wrong. The code
implements `RECENT_WOODY_REMOVAL` as: Hansen loss in the last 10 years on a pixel whose
`treecover2000 >= 10%`.

Two consequences:

- A pixel can pass the <10% test and still be excluded because woody biomass was
  removed recently.
- The proxy cannot tell natural disturbance from project-driven removal. That is a
  stated limitation, not a hidden assumption.

### 10.3.3 Area mode — §1.1 and §4.4.1

Area-based mode is not “census but with cropland excluded”. §1.1 allows non-forest to
forest, or existing forest that has not been managed for wood products in the past ten
years. §4.4.1 excludes:

1. land that met the definition of managed forest at any point in the 10-year period;
2. clearing pre-existing woody biomass via timber harvesting or native-ecosystem
   degradation;
3. projects planting fewer than 50 units/ha that could use the census route.

The repository has no managed-forest, timber-harvest or native-ecosystem dataset.
Therefore `validate_config()` raises `NotImplementedError` for `eligibility_mode: area`.
Refusing is the correct engineering decision: a number produced by the census rule
would be mislabeled as area-mode eligibility.

### 10.3.4 What is not a raster rule

§4.3 also contains registration-level conditions: direct planting, land-use maintained,
≤50 planting units/ha, complete t0 census, GPS coordinates, durable markers, unlocatable
units assumed dead. These are not 30 m raster tests. They belong in field protocols and
project design documents, not in a land-cover screen.

## 10.4 The two-stage waterfall

### 10.4.1 Stage membership

```text
STAGE_A = NODATA, WOODY_COVER, RECENT_WOODY_REMOVAL
STAGE_B = BUILTUP_WATER_WETLAND, CROPLAND, PROTECTED, STEEP_SLOPE
SMALL_PATCH runs last
```

Stage A is methodology + data validity. Stage B is project design. This matters because
a reviewer may accept a methodology-exclusion but challenge a design choice (for
example, excluding all cropland). Reporting one merged number hides that distinction.

### 10.4.2 First failing filter wins — but only for attribution

`apply_filters()` starts every district pixel as `ELIGIBLE`, then walks the order:

```python
newly = rejecters[name] & (reason == Reason.ELIGIBLE)
reason[newly] = Reason[name]
```

Only pixels still eligible can be assigned a new code. If a pixel is both protected and
steep, PROTECTED wins if it appears first. The **eligible set** is not affected by that
order because `run_screening()` also computes:

```python
methodology = in_d.copy()
for name in STAGE_A:
    methodology &= ~rej[name]
```

That is a plain AND of all Stage-A passes. The test
`test_eligible_set_is_invariant_to_filter_order` shuffles the order and asserts the
candidate and methodology masks are identical.

### 10.4.3 The canonical reason codes

```text
0  ELIGIBLE
1  WOODY_COVER                  §4.3(8)(a); §6.2(1)
2  BUILTUP_WATER_WETLAND        design
3  CROPLAND                     design (cropland is eligible under census)
4  RECENT_WOODY_REMOVAL         §4.4.2(1), census only
5  STEEP_SLOPE                  design
6  PROTECTED                    design / safeguard
7  NODATA                       data validity
8  SMALL_PATCH                  design / transaction cost
255 OUTSIDE                     outside district, never counted
```

The old scaffold had 3=forest loss, 4=steep, 5=protected, 6=cropland. That table is
gone. Keeping the code order stable is why `test_reason_codes_are_the_canonical_contract`
exists.

### 10.4.4 Waterfall arithmetic

```text
district area
  - NODATA
  - WOODY_COVER
  - RECENT_WOODY_REMOVAL
  = methodology_eligible_ha
  - BUILTUP_WATER_WETLAND
  - CROPLAND (if design says exclude)
  - PROTECTED
  - STEEP_SLOPE
  - SMALL_PATCH
  = candidate_ha
```

`methodology_eligible_ha >= candidate_ha` by construction. Cropland stays in the
methodology number; it is removed only from the candidate if
`exclude_cropland[census]` is true.

## 10.5 Geometry: the part that silently ruins hectares

### 10.5.1 CRS and grid

Jhabua spans roughly 74–75°E and 22–23°N. The project uses **EPSG:32643** (UTM zone
43N) because it is metric, local and appropriate for area/distance math. The grid is
30 m, north-up, with a single transform shared by every layer.

A GeoTIFF transform is an affine matrix:

```text
x = a * col + b * row + c
y = d * col + e * row + f
```

- `a` = pixel width (30)
- `e` = pixel height (−30 for north-up)
- `c`, `f` = top-left origin
- `b`, `d` = rotation/shear; must be 0 for a north-up grid

The first version of the new check mistakenly tested `b` and `c`. `c` is the x origin,
not shear, so every valid raster failed. The fix is:

```python
if abs(transform.b) > 1e-9 or abs(transform.d) > 1e-9:
    raise QAError("rotated/sheared transform")
```

This is a good example of why you test the error path, not just the happy path.

### 10.5.2 Area is measured, not assumed

The config says 30 m. But a stack could have been written at 10 m. If the code used
`30 * 30` while the pixels were 10 m, every hectare would be **nine times too large**.
So `load_layers()` measures the real transform:

```python
measured_res_x = abs(transform.a)
measured_res_y = abs(transform.e)
layers["_pixel_area_ha"] = measured_res_x * measured_res_y / 10_000.0
```

Every later area calculation uses `pixel_area_ha(cfg, layers)`, which prefers the
measured value. A mismatch raises `QAError` before any result is written.

### 10.5.3 Why 30 m, not 10 m

Hansen and the DEM are native 30 m. Disaggregating them to 10 m would invent detail.
WorldCover and Sentinel-2 are ~10 m; they are aggregated **down** to 30 m:

| Layer | Resampling | Why |
|---|---|---|
| WorldCover | `mode` (majority) | categorical class; do not blend class codes |
| Hansen treecover/loss/gain | `nearest` | preserve percent/class values |
| DEM | `bilinear` | continuous surface; smooth before slope |
| S2 NDVI/BSI | `average` | continuous index; average is defensible |
| WDPA | polygon rasterise | `all_touched=True` is conservative for no-go |

### 10.5.4 Nodata and masks

`rasterio.read(1, masked=True)` gives a masked array. `load_layers()` stores the mask
and fills values with 0. Then:

```python
nodata = zeros(...)
for key in NODATA_LAYERS:      # worldcover, treecover, loss, gain, slope, protected
    nodata |= masks[key]
layers["nodata"] = nodata & in_district
```

`protected_areas` was added to `NODATA_LAYERS`: a WDPA raster whose nodata is filled
with 0 would otherwise look like “not protected” and pass silently.

`NODATA` is the first Stage-A code, so a missing pixel cannot be counted as eligible and
cannot break the area balance.

### 10.5.5 Boundary rasterisation

The district mask is rasterised from the Jhabua polygon without `all_touched`. The
30 m pixel centre rule makes the edge slightly conservative. `all_touched=True` would
include every pixel touched by the polygon, overstating area. WDPA uses `all_touched=True`
because for a no-go safeguard, over-inclusion is the safer error.

The reference area is **3,433.78 km²**, computed from the boundary in EPSG:32643. The
config tolerance is 1%. The old `3600.0` was a units/default bug: it was a rough km²
number used as hectares.

## 10.6 Ingest: raw sources to one aligned stack

`src/ingest.py` is intentionally strict: if a required source is missing, it prints
every missing path and exits 2 **before writing anything**. A zero-filled WorldCover
would look like eligible land; a zero-filled Hansen layer would look like no woody
cover. Both would silently inflate the answer.

Order of operations:

1. Load and validate `config/jhabua.yaml`.
2. Check all required sources exist.
3. Read `data/raw/boundary.geojson`, select `shapeName == "Jhabua"`, reproject to
   EPSG:32643, check validity.
4. Build a grid whose origin is snapped to the 30 m lattice:
   `west=floor(minx/30)*30`, `north=ceil(maxy/30)*30`, etc.
5. Rasterise the district mask.
6. Reproject/resample each layer to the grid.
7. Compute Horn slope from the DEM.
8. Rasterise WDPA.
9. Write GeoTIFFs with `nodata`, LZW compression, tiling, and descriptions.
10. Write `data/processed/aligned/manifest.json` with source and output SHA256s.

The seven required outputs are:

```text
district_mask.tif
worldcover_2021.tif
hansen_treecover2000.tif
hansen_lossyear.tif
hansen_gain.tif
slope_deg.tif
protected_areas.tif
```

Optional scoring layers (if the S2 sources exist):

```text
ndvi_dry.tif  ndvi_monsoon.tif  bsi_dry.tif  bsi_monsoon.tif
```

### 10.6.1 Horn slope

Horn’s method uses the 3×3 neighbourhood:

```text
a b c
d e f
g h i
```

```text
dz/dx = ((c + 2f + i) - (a + 2d + g)) / (8 * dx)
dz/dy = ((g + 2h + i) - (a + 2b + c)) / (8 * dy)
slope = degrees(atan(sqrt((dz/dx)^2 + (dz/dy)^2)))
```

DEM holes are filled with the nearest valid value before the gradient; otherwise a
nodata pixel would create an artificial cliff at the edge. The original nodata cells
are restored after slope calculation.

### 10.6.2 Failure modes you should expect

- **Missing source** → exit 2, list of paths, no outputs. This is the current state.
- **Boundary feature not found** → check `shapeName`; the raw file has 641 ADM2 units.
- **Wrong CRS / resolution** → the QA gate catches it.
- **DEM all nodata** → `IngestError`; do not compute slope from a constant.
- **WDPA empty** → protected layer is all zeros; the screening waterfall notes “zero
  protected area” instead of silently passing.

## 10.7 QA/QC: measure, do not trust

The old `qaqc.py` checked a JSON manifest and had real bugs:

- `check_geometry_validity()` appended to an undefined `results` list (NameError).
- `check_nodata_share()` was a placeholder (`float(src.nodatavals[0] and 0.0)`).
- `--report` loaded no manifest and produced a report with no checks.
- `district_area_ha` defaulted to `3600.0`.
- The selftest constructed `GateResult` objects with hard-coded answers; it did not
  inspect any raster.

The new gate opens every required GeoTIFF and checks:

1. file presence;
2. CRS, transform, resolution, shape, band count;
3. grid equality with the district mask;
4. declared nodata and missing share inside the district;
5. value ranges and allowed classes:
   - WorldCover classes,
   - treecover 0–100,
   - lossyear <= configured vintage,
   - gain 0/1,
   - slope 0–90,
   - protected 0/1,
   - S2 indices −1..1;
6. boundary geometry validity and area;
7. district area vs reference within 1%;
8. reason-code balance if a screening output already exists.

Critical failures stop the run. Warnings are recorded. `--report` now actually runs the
checks and writes `outputs/qaqc/qaqc_report.md`; it is not a no-op.

The selftest writes a tiny valid stack, verifies zero critical failures, then rewrites
one layer at 10 m and asserts the gate catches it. That is a test of the gate’s ability
to fail, which is more important than a test that only passes.

## 10.8 Screening: from layers to a defensible number

`run_screening()` is pure: arrays + config in, arrays out. That makes sensitivity runs
cheap and tests fast.

Step by step:

1. `validate_config()` (area mode raises).
2. `check_layers()`: shapes, Hansen vintage, non-empty district.
3. Build rejecters:
   - NODATA from masks;
   - WOODY_COVER from WorldCover/Hansen;
   - RECENT_WOODY_REMOVAL from Hansen loss + 10-year window;
   - built/water/wetland classes;
   - cropland only if the design says exclude;
   - protected;
   - slope > 20°.
4. `methodology` = AND of Stage-A passes.
5. `reason` = first-failing-filter attribution.
6. `patch_stats` before removal; `remove_small_patches`; `patch_stats` after.
7. Assert Stage-A attribution equals the direct methodology mask.
8. `check_area_balance()`: every district pixel has one known code.
9. `compute_flags()`: shrubland, old loss, cropland-kept. Flags are not exclusions.
10. `build_waterfall()`: rows with step, stage, code, basis, removed/remaining hectares.
11. Write `reason_codes.tif`, `confidence_flags.tif`, `waterfall.csv`,
    `run_summary.json`.

### 10.8.1 `canopy_now` and its bias

`woody_mask()` currently does:

```python
canopy_now = np.where(lost_by_start, 0, hansen_treecover2000)
```

Hansen `lossyear` is binary. A pixel with 90% cover that lost once becomes 0% in the
proxy. That can **overstate** eligible area. The correct long-term fix is a post-loss
canopy product or a loss-fraction layer. For now it is documented and should be part of
the sensitivity discussion.

### 10.8.2 `start_year` and data vintage

`start_year: 2026` drives the 10-year look-back (2016–2026). Hansen ends in 2024, so
2025–2026 removals are invisible. The config says this; the limitations doc repeats it.
Do not “fix” it by pretending the data covers 2026.

### 10.8.3 Why `candidate` can be much smaller than `methodology_eligible`

Stage B removes built-up/water/wetland, cropland if configured, protected areas, steep
slopes, and patches <1 ha. Those are design/safeguard choices. They are not VM0047
eligibility rules, and the waterfall labels them as such.

## 10.9 Tests: what each one protects

`tests/test_screening.py`:

- `test_area_closes_and_stage_a_matches_direct_mask` — every pixel coded; Stage A
  attribution agrees with the direct AND.
- `test_first_failing_filter_wins` — protected before steep.
- `test_cropland_kept_in_census_but_flagged` — cropland is methodology-eligible but
  flagged.
- `test_area_mode_is_disabled_not_silently_wrong` — area mode raises.
- `test_small_patch_removed_big_patch_kept` — 2×2 <1 ha removed; big patch kept.
- `test_recent_loss_excluded_old_loss_flagged` — §4.4.2(1) vs confidence flag.
- `test_eligible_set_is_invariant_to_filter_order` — order affects attribution only.
- `test_zero_protected_area_is_reported_not_silent` — zero WDPA is documented.
- `test_waterfall_labels_basis_honestly` — §4.3(8)(a), §4.4.2(1), no clause for design.
- `test_reason_codes_are_the_canonical_contract` — code numbers cannot drift silently.
- `test_reference_area_mismatch_fails` — 10% area error raises.
- `test_hansen_year_beyond_config_fails` — future Hansen year raises.
- `test_bad_orders_rejected` — NODATA first; Stage B membership fixed.
- `test_config_validates`.

`tests/test_io.py`:

- `test_cli_end_to_end` — write GeoTIFFs, run `main()`, read outputs.
- `test_load_layers_rejects_wrong_resolution` — 30 m stack accepted; 10 m slope rejected;
  measured `0.09 ha` per 30 m pixel.

`tests/test_ingest.py`:

- synthetic boundary + WorldCover 10 m + Hansen 30 m + DEM + WDPA;
- run ingest; assert 20×20 grid at 30 m, WorldCover majority output, slope float32;
- run the QA gate and assert zero critical failures.

Run:

```bash
python -m pytest -q
python src/qaqc.py --selftest
python run_pipeline.py config/jhabua.yaml
```

## 10.10 Debugging log — the failures we actually hit

These are worth reading because they are typical raster/Python failure modes.

1. **Pytest collected the same test modules twice.**
   The staging copies and the canonical `tests/` had the same basenames. Fix:
   `pytest.ini` with `testpaths = tests` and `norecursedirs` for `incoming_files_*`.
   Lesson: test discovery is part of the build.

2. **`GeoDataFrame.write_file` does not exist.**
   The method is `to_file(path, driver="GeoJSON")`. The error came from pandas’
   `__getattr__`, which is why it looked like a pandas problem.
   Lesson: read the traceback’s object, not just the last line.

3. **Rasterio “A valid dtype is required.”**
   A profile built with `height/width/count/crs/transform` but no `dtype` cannot create
   a GeoTIFF. Every writer must pass `dtype=str(arr.dtype)`.
   Lesson: a raster profile is a contract, not a suggestion.

4. **The transform rotation check rejected every north-up raster.**
   I checked `transform.c` as if it were shear. It is the x origin. The correct shear
   terms are `b` and `d`.
   Lesson: affine coefficients are not intuitive; write the equation down.

5. **`uint8` masked arrays cannot be filled with `NaN`.**
   `arr.filled(np.nan)` raises. Use `arr.data.astype(float)` for values and
   `np.ma.getmaskarray(arr)` for validity.
   Lesson: masks and values are separate; don’t force a float fill into an integer array.

6. **The QA selftest used a relative boundary path in a temp directory.**
   It failed with “boundary missing”. The fix was to copy the real boundary into the
   temp project, so the selftest exercises the boundary check too.
   Lesson: a selftest must build the same inputs the real path expects.

7. **Duplicate `transform` keyword in the corruption test.**
   `profile` already had `transform`; passing another one raised `TypeError`. Build a
   new dict with `{**profile, "transform": ...}`.
   Lesson: dict merging is clearer than keyword collisions.

8. **The old QA gate “passed” without looking at data.**
   It checked a manifest, not the raster. The new gate’s first real run correctly
   refused to pass because the aligned layers do not exist.
   Lesson: a check that cannot fail is decoration; make it read the artifact.

## 10.11 How to read a result without fooling yourself

When the real stack exists:

```bash
python src/ingest.py config/jhabua.yaml
python src/qaqc.py --check config/jhabua.yaml
python src/screening.py config/jhabua.yaml
```

Then check, in this order:

1. `outputs/qaqc/qaqc_report.md` — zero critical failures.
2. `outputs/jhabua_agroforestry_screening/waterfall.csv` — Stage A rows have clause
   bases; Stage B rows say “project design screen”.
3. `run_summary.json` — `district_ha` matches the boundary reference; methodology >=
   candidate.
4. `reason_codes.tif` in QGIS — overlay on the S2 composite. Look for obvious
   misclassification: whole villages as eligible, river/water as eligible, tree patches
   as eligible.
5. `confidence_flags.tif` — shrubland and old-loss flags are not exclusions; they tell
   you where the proxy is weak.

Do **not** quote a hectare figure until the QA report is clean and the reason raster has
been visually checked.

## 10.12 What is still not done

- **Raw sources missing:** WorldCover 2021, Hansen treecover/loss/gain, DEM, WDPA.
  Without them, the pipeline is correctly blocked at ingest.
- **Area mode:** intentionally disabled; needs §1.1/§4.4.1 evidence.
- **Scoring/sensitivity/validation/maps:** not written yet.
- **Hansen bias:** `canopy_now` collapses any loss to zero; needs a sensitivity band or
  a post-loss canopy product.
- **Git:** initialized and committed. Large raw/processed rasters are ignored; the
  commit history is a safer handoff point than a bare folder.

## 10.13 The mental model to keep

Think of the project as four contracts:

1. **Config contract** — every threshold and path lives in `config/jhabua.yaml`.
2. **Grid contract** — every layer has the same CRS, transform, shape, resolution.
3. **Accounting contract** — every district pixel has one reason code; the areas sum.
4. **Evidence contract** — every Stage-A row cites a clause; Stage-B rows admit they are
   design choices.

If any contract breaks, stop and fix the contract before adding a map or a score. That
is the whole discipline of the project.
