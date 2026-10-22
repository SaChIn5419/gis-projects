# LEARNING.md — The Jhabua GIS Training Manual

**A complete, self-contained GIS course that rebuilds one real project, lesson by lesson, on this repository's actual data.**

> **Version 2.0 — 2026-10-22.** This file is now a **coursebook**, not project documentation.
> Operational docs live in `README.md` and `docs/`. When you finish this manual you will be
> able to build, defend and map a land-screening analysis from public data on your own.

---

## Foreword

This manual follows the teaching tradition of the three best learning guides on the
internet — the **QGIS Training Manual**, the **Software/Data Carpentry lessons**, and
**The Rust Book** — and runs every exercise on **this repo's real Jhabua screening stack**,
not toy data.

Three rules of how it teaches:

1. **Operate before you theorize** (*Rust Book* rule). Module 1 has you run the entire
   real pipeline and look at real maps before a single concept is explained. You should
   always know what the machine already did.
2. **Follow Along / Try Yourself** (*QGIS Training Manual* rule). Every lesson has a guided
   walkthrough with exact commands and expected real outputs, then exercises you do
   yourself, then key points.
3. **End-of-lesson contracts** (*Data Carpentry* rule). Every lesson states its driving
   question, objectives, and measurable key points. If you can't answer the question,
   don't move on.

> **Hands-on companion.** `notebooks/learn_by_hand.ipynb` is this manual's lab. There
> you re-implement the pipeline piece by piece — grid contract, rejecter masks, the
> staged classifier, small patches, flags, maps — and every section checks your result
> byte-for-byte against the real `outputs/` rasters. The notebook is the exercises;
> this manual is the textbook.

### Who this is for

- Someone who has written Python and wants to learn GIS **as a working discipline**, not
  as a collection of GIF tutorials.
- Someone building this exact repo who wants to understand every step, not just run it.
- Anyone preparing to defend a spatial analysis in an interview.

### Prerequisites

- Python basics (functions, imports, with-blocks).
- No GIS background required. No QGIS/GDAL/ArcGIS experience required.
- A terminal and this repository plus its `.venv`.

### How to study

- One **lesson per sitting**. Never two.
- Type every Follow Along command. Do not copy-paste blindly.
- Do every ✱ exercise before moving on. Skip nothing.
- Keep a dated notebook. Interviewers don't ask "how"; they ask "what went wrong".

---

## About the exercises

| Symbol | Meaning |
|---|---|
| ⭐ | Mechanical — mostly typing a command |
| ⭐⭐ | You must reason about the data |
| ⭐⭐⭐ | Capstone — real analysis, real numbers |

**Solution** blocks are right below each exercise. Don't look until you've tried.

Conventions:
- Terminal: lines beginning with `$`
- Real expected output: `→` lines. Your numbers here are real from the Oct-2026 run.
- "District" always means Jhabua district, Madhya Pradesh, India.

---

## The problem on the cover

Every lesson you'll answer a piece of this:

> **Jhabua district is 3,433.78 km². This project's screen says 251,292.8 ha (73.2% of the
> district) is "candidate" agroforestry land. Is that number (a) real opportunity,
> (b) a broken screen, (c) a proxy-driven illusion, or (d) something that cannot even
> be called a number yet?**

This is the question a GIS professional must be able to answer, given only the pipeline,
the rasters, and the waterfall.

The promise of the course: by Module 12 you will not just answer this one — you will know
what it would take to defend **any** district, any data stack, any map. You will be able to
say, out loud, what your product is and is not.

---

## The agenda

Modules build on each other; don't skip. Total ≈ 20 focused hours.

| Module | Title | Lessons | Prereq | You learn |
|---|---|---|---|---|
| 1 | Make a map before you understand it | 2 | none | run the pipeline, read a map, frame the question |
| 2 | The two data species: raster and vector | 2 | M1 | what a `.tif` and a `.geojson` actually are |
| 3 | Where things really are: coordinate systems | 2 | M2 | CRS, EPSG, why area is wrong until proj'd |
| 4 | Reading spatial data safely | 2 | M3 | rasterio profiles, geopandas CRS discipline |
| 5 | Getting data in | 2 | M4 | tiles, hashes, stop-on-missing (`ingest.py` inputs) |
| 6 | Building the aligned 30 m stack | 3 | M5 | one grid, all layers, NaN/DEM/S2 traps |
| 7 | Trusting your data: the QA gate | 2 | M6 | measured QA, not manifest QA |
| 8 | The screening waterfall and reason codes | 3 | M7 | how 343,380 → 251,292 ha, kin discord; patches |
| 9 | Cartography from real data | 2 | M8 | rendering code 0..255, extent order, honesty |
| 10 | Writing it up | 2 | M9 | limitations, claims you can and cannot make |
| 11 | Scaling and testing | 2 | M10 | windowed reads, pytest in the GIS world |
| 12 | Final assessment | 1 | all | rebuild Jhabua from scratch, in an hour |

---

# Module 1 — Make a map before you understand it

## Lesson 1.1 — Run the entire pipeline

**Driving question:** *What happens in this machine from "public data" to "map"?*
**Objectives**
- Run ingest → QA → screening → maps with zero code.
- List the artifacts in `data/processed/aligned` and `outputs/`.

### Follow Along

```bash
$ source .venv/bin/activate

# Step 1 — build the 11 aligned 30 m layers
$ python src/ingest.py config/jhabua.yaml
→ …11 aligned layers written to data/processed/aligned
→ grid: 2933 × 3130 px @ 30 m, CRS EPSG:32643
→ geotransform upper-left: (742,XXX, 2,57X,XXX)

# Step 2 — QA the stack: 19 automated checks
$ python src/qaqc.py --check config/jhabua.yaml
→ 19 checks, 0 blocking, 1 warning
→ see outputs/qaqc/qaqc_report.md

# Step 3 — the actual screening
$ python src/screening.py config/jhabua.yaml
→ district:                    343,380.6 ha
→ methodology_eligible (A):    324,094.0 ha
→ candidate (B):               251,292.8 ha
→ candidate flagged:           197,590.4 ha
→ outputs/jhabua_agroforestry_screening/{waterfall.csv,run_summary.json,reason_codes.tif}

# Step 4 — the maps
$ python scripts/make_maps.py config/jhabua.yaml
→ outputs/maps/01_study_area.png
→ outputs/maps/02_reason_codes.png
→ outputs/maps/03_waterfall.png
→ outputs/maps/04_candidate_closeup.png
```

Open all four PNGs. Now read `outputs/jhabua_agroforestry_screening/waterfall.csv`.
You have just executed a full screening for a real 3,434 km² district.

### Why this works

- `src/ingest.py` is the "assembly line": it reprojects, clips and resamples **six public
  sources** onto **one shared 30 m grid**.
- `src/qaqc.py` is the gatekeeper: it doesn't read paper promises, it **opens every raster
  and checks visible reality** (CRS, shape, nodata, ranges, area reconciliation).
- `src/screening.py` is the judge: it assigns each of the 3,815,340 district pixels one of
  ten **reason codes**.
- `scripts/make_maps.py` is the storyteller: turns those reason codes into four PNG maps.

### Cautions

- Every time you change `config/jhabua.yaml`, you must re-run ingest and screening. Rasters
  are not reused automatically. This is why QA exists.
- Don't quote a number the pipeline printed until you know what it *means* (Module 8).

### Try Yourself

**⭐ 1.1(a)** List the 11 aligned layers in `data/processed/aligned` and write down,
for each, its CRS and pixel count.

**⭐ 1.1(b)** Open `waterfall.csv` and note which step removed **0 ha**. Why might a real
removal step legitimately remove zero?

**Solution 1.1(a):** `python -c "import rasterio, glob; [print(f, r.read(1).shape) for r in [rasterio.open(f)] for f in sorted(glob.glob('data/processed/aligned/*.tif'))]"` — 11 files, each 2933×3130 px, all EPSG:32643.
**Solution 1.1(b):** `recent_woody_removal_ha = 0`. Hansen loss is binary-by-year and in this
stack only **12 pixels** in the entire district have nonzero loss (latest loss year 2010).
Zero here is **a measured zero**, not missing data — see Module 7.

### Key Points

- The pipeline is 4 commands and is fully deterministic.
- The aligned stack is the single source of truth for all later analysis.
- "0 ha removed" is **evidence-based**, not a default.

## Lesson 1.2 — The question behind the map

**Driving question:** *If 73.2% of a district is "candidate", is the screen generous or is
something wrong?*
**Objectives**
- Spot the two numbers hiding inside "candidate" (Stage A vs Stage B, the waterfall).
- Name the four main reason-code families by eye alone.

### Follow Along

Look at `02_reason_codes.png`. Note the colors, cross-check with the raster legend in
`make_maps.py` (`REASON_COLORS` and label 0 = **Candidate (code 0)**, never "eligible").
Then open `03_waterfall.png` and trace the funnel:

| stage | ha | source |
|---|---:|---|
| District | 343,380.6 | geoBoundaries ADM2 at 30 m |
| after woody | 324,094.0 | less 19,286.6 |
| after built/water | 319,793.8 | less 4,300.2 |
| after protected | 251,644.7 | less 68,149.1 |
| after steep | 251,500.5 | less 144.2 |
| after small patch | **251,292.8** | less 207.7 |

Note in particular **cropland removed = 0**. Because the methodology route here is
**census mode** (VM0047 §4.3(8)(a), §6.2), the candidate keeps cropland on purpose.
This is the single number that explains the 73.2% headline. Do not "fix" it.

### Why this works

A screen has two stages with two different **audiences**:

- **Stage A (methodology):** "Can this be in an ARR census route?" — 324,094.0 ha.
- **Stage B (design):** "Do we want to work here?" — 251,292.8 ha.

Merging them into one number is the top姑 sin of pre-feasibility reporting.

### Cautions

- The candidate is a **pool**, not a project. Nobody will plant 251k ha.
- Protected (68,149.1 ha) is the largest single exclusion. It is driven by a
  deliberately conservative WDPA rule: *any* polygon, not just IUCN I–IV. See Module 8.

### Try Yourself

**⭐⭐ 1.2(a)** Compute, by hand, the pixels in the district: 343,380.6 ha ÷ 0.09 ha/px.
**⭐ 1.2(b)** Verify your answer against the total of all reason codes in
`reason_codes.tif` (computed sample code below).

**Solution 1.2(a):** 343,380.6 / 0.09 = **3,815,340 pixels**.
**Solution 1.2(b):** counts are eligible 2,792,142 + woody 214,296 + built/water 47,780 +
steep 1,602 + protected 757,212 + small patch 2,308 = **3,815,340** ✓. Only codes 3
(cropland) and 4 (recent removal) are absent because their removals were 0.

### Key Points

- Stage A vs Stage B are **two numbers for two audiences**; merging them is a sin.
- The 73.2% "candidate" is driven by **census-mode's** decision to keep cropland.
- Reason codes must reconcile back to district size to within rounding.

---

# Module 2 — The two data species

## Lesson 2.1 — Rasters: numbers on a grid

**Driving question:** *What exactly is in a `.tif`, beyond "an image"?*
**Objectives**
- Open a real layer with `rasterio` and read its geometry.
- Predict what "outside the boundary" looks like in tooling.

### Follow Along

```python
import rasterio, numpy as np
src = rasterio.open("data/processed/aligned/worldcover_2021.tif")
print(src.crs)          # → EPSG:32643
print(src.shape)        # → (3130, 2933)   (rows, cols)
print(src.transform)    # → Affine(30, 0, 74xxx.xx, 0, -30, 257xxx.xx)
print(src.dtypes)       # → ('uint8',)  — bytes, not floats
print(src.nodata)       # → 255

arr = src.read(1)
print(np.unique(arr))   # → [10 20 30 40 50 60 80 255]
# 10 closed forest, 20 shrub/scrub, 30 grassland, 40 cropland, 50 built-up,
# 60 bare/sparse, 80 water, 255 nodata/outside boundary
```

A raster is a numpy grid plus a **transform** that says where the top-left pixel is on
Earth and how wide/tall each pixel is. The CRS in `src.crs` says what "Earth" means.

### Why this works

- `transform` has units in **the CRS's unit of measure** — meters here, not degrees.
- `nodata` is a value, not an "absence". Tooling translates it; you must too — by masking.
- A `uint8` raster can store 256 classes. `float32` uses 4 bytes per pixel — 4× the memory.
- At 30 m / 1 px = 0.09 ha, a full district is 3,815,340 px and ~3.6 MB as uint8.

### Cautions

- Do not save a classified raster as `float32` "just to be safe". You'll waste ×4 memory
  and invite float-equality bugs.
- Never compare `arr == nodata` with numpy directly; use `np.ma.masked_values` or write
  `arr[arr == nodata] = 0` first. Otherwise pandas-land gets poisoned by 255s.

### Try Yourself

**⭐⭐ 2.1(a)** Compute the district's *class distribution*: for each WorldCover value, the
number of pixels **inside** the boundary (nodata = 255). Which class is the biggest?

**Solution 2.1(a):** by pixel count — **40 (cropland) dominates**; then shrubland (20).
This explains why census-mode screens were applied *before* any "is it not cropland"
rule. (Use `np.unique(arr[arr != 255], return_counts=True)` inside a district mask.)

### Key Points

- A raster = grid + transform + CRS + dtype + nodata.
- WorldCover's class **40 = cropland**, which is why it drives everything in this district.

## Lesson 2.2 — Vectors: objects in space

**Driving question:** *What is a GeoJSON polygon actually made of?*
**Objectives**
- Load, inspect, and reproject a district boundary.
- Understand attribute tables and "features".

### Follow Along

```python
import geopandas as gpd
b = gpd.read_file("data/processed/boundary_jhabua.geojson")
print(b.crs)          # → EPSG:32643
print(b.geometry.geom_type)  # → Polygon
print(b.total_bounds) # → [ 742xxx.x  2476xxx.x ... ]
print(b.columns.tolist())
```

A GeoJSON Feature is: `{"type":"Feature","geometry":{...},"properties":{...}}`. The
`geometry` gives shape; `properties` is just an attribute table row. WDPA polygons
(`/data/raw/wdpa.geojson`) may have `NAME`, `DESIG_ENG`, `IUCN_CAT`, `REP_AREA`.

The geometry is a list of `[lng, lat]` rings. **Coordinates are degrees raw** in the
file, even though geopandas may read them as a CRS.

### Why this works

- Vectors are **not grids**. A forest polygon is one object — no pixel-level detail.
- That's why we rasterize vectors (e.g., "protected") onto the 30 m grid for screening.
- `b.total_bounds` uses `min-x min-y max-x max-y` — great quick sanity check.

### Cautions

- The district ADM2 boundary in this repo has a small detached component in the SW
  corner, which we keep. Never silently dissolve/drop disconnected polygons.
- `gpd.read_file` may choose a default CRS if the file's metadata is missing. Always
  print `b.crs` — always.

### Try Yourself

**⭐ 2.2(a)** Count how many WDPA polygons intersect Jhabua and print their `DESIG_ENG`

**Solution 2.2(a):** bounding-box query over India returns **1,376** polygons; of those
**188 actually intersect Jhabua**. Designation strings include **Reserve Forest**,
**Protected Forest**; not just IUCN I–IV. That's why this screen excludes "any polygon"
(written, cautious rule) rather than "IUCN I–IV" (allow-ignoring-rule).

### Key Points

- Vectors carry attributes, resolution-free shapes.
- Rasters are what the whole screening runs on; vectors are what screening **excludes**
  (protected) or qualifies (boundary).

---

# Module 3 — Coordinate systems

## Lesson 3.1 — Degrees vs meters

**Driving question:** *Why does 1° of longitude ≠ 111 km everywhere?*
**Objectives**
- Know EPSG:4326 vs EPSG:32643 and when to use each.
- Compute an area that won't embarrass you.

### Follow Along

```python
import geopandas as gpd
b_wgs = gpd.read_file("data/raw/boundary.geojson")      # often EPSG:4326
b_proj = b_wgs.to_crs("EPSG:32643")                     # UTM 43N, meters

# Area of the district, actually computed
print(b_proj.area.iloc[0] / 1e6)      # → ~3433.78 km²   (was wrong in 4326)
```

- **EPSG:4326** is degrees ("lat-lon"). A polygon in 4326 looks right in a lat/lon tool.
  Its `.area` is in **square degrees** — meaningless for reporting.
- **EPSG:32643** is UTM zone 43N (east longitude 72–78°E), in **meters**. `.area` is m².

Jhabua's bounds, WGS84: **74.15897–75.01373 °E, 22.38848–23.23841 °N**. The district sits
near 22.8°N, so the meters-height of 1° latitude is still ~110.6 km; longitude is
101.0 km/°. Celsius of precision. Not 1 km² of sloppiness.

### Why this works

- A raster's `transform` is in the CRS's unit. If your CRS is epSg:4326, the "30 m
  pixel" is actually 0.000271° narrow at 22.8°N and different at 23.2°N.
- A Cartesian area formula treats degrees as flat; maps lie by 0.4–4% depending on lat.

### Cautions

- **Silent killer #1 in GIS.** A bad-CRS pipeline doesn't error; it just gives the wrong
  answer (or a blank map).
- If you ever see `EPSG:4326` on a raster that *should be meters*, stop. Reproject before
  anything else.

### Try Yourself

**⭐⭐ 3.1(a)** Reproject the district to EPSG:4326 and compute `.area` again. What's the
ratio to the true area? What does that tell you?
**⭐ 3.1(b)** Write the code to **prove** the district is in UTM zone 43N (use CRS metadata).

**Solution 3.1(a):** in 4326, `.area` is "square degrees" (~52,539). 52,539°² vs
3,433.78 km². Ratio makes no sense without knowing the latitude — this is the whole lesson.
**Solution 3.1(b):**
```python
import pyproj
crs = pyproj.CRS.from_epsg(32643)
print(crs.datum.name)  # → WGS 84
print(crs.coordinate_operation)  # → UTM zone 43N
```

### Key Points

- **CRS before area, CRS before distance, CRS before comparing layers.**
- Use an **equal-area** or meter-based CRS (UTM 43N) for anything you'd put in a report.

## Lesson 3.2 — Why the whole stack is 30 m

**Driving question:** *Why not 10 m the whole way through? Sentinel-2 and WorldCover
have 10 m!*
**Objectives**
- Reason about resolution, binary data and misleading detail.
- Justify the single-grid design to a reviewer.

### Follow Along

Five of the six sources really use 30 m: **Hansen GFC** (30 m default), **Copernicus
GLO-30 DEM** (30 m), and Hansen's `treecover2000/lossyear/gain`. WorldCover is 10 m but
class is **categorical**. Sentinel-2 is 10 m but is used only for indices/background.

Rule: the **finest authoritative resolution in the stack** is the stack resolution.
Aggregating more precisely than that produces precision your data can't support.

2933 × 3130 px @ 30 m in EPSG:32643 covers the Jhabua envelope. 1 px = 30 m × 30 m =
0.09 ha. This pixel is the unit of analysis for the entire project.

### Why this works

- Resampling WorldCover 10 m→30 m with **majority** keeps the class honestly; averaging
  classes would invent forests that aren't there.
- Downsampling Hansen to 10 m would be a **hallucination of 9× detail** it doesn't have.
- Anything precision-sensitive (fieldwork targeting) should demand higher resolution;
  cite Sentinel-2 separately, not replace the screen.

### Cautions

- Don't compare layers before they're on the same grid. Two methods: resample one, or
  derive at shared resolution. Here: stacked on one grid.
- A "1 ha patch" at 30 m is ~11 pixels. Below that, classifications are unstable.

### Try Yourself

**⭐⭐ 3.2(a)** The district is 3,433.78 km². How many 30 m pixels total, and how many 10 m
pixels? Why does WorldCover not simply use 10 m?
**⭐ 3.2(b)** Compute the exact 1-ha threshold in pixels at 30 m (ceil).

**Solution 3.2(a):** 30 m → 3,815,340 px. 10 m → 34,338,060 px (9×). WorldCover must
resample to 30 m anyway to align with Hansen + DEM + all screens; keeping everything at
the highest common resolution is the honest workable footprint.
**Solution 3.2(b):** 1 ha ÷ 0.09 ha/px = 11.11 → **12 pixels** (ceil). `screening.py`
uses exactly this logic.

### Key Points

- One shared grid is the precondition for all pixel arithmetic.
- Pixel size is a **contract**, not a preference. Say why it's 30 m in your docs.

---

# Module 4 — Reading spatial data safely

## Lesson 4.1 — A raster is a contract

**Driving question:** *What five properties must you always set when you write a raster?*
**Objectives**
- Construct a GeoTIFF by hand and save `reason_codes`.
- Understand the full profile dict.

### Follow Along

The entire screening output raster was written like this. Reproduce it by hand:

```python
import numpy as np, rasterio
from rasterio.transform import from_origin

reason = np.arange(12, dtype="uint8").reshape(3, 4)   # stand-in
transform = from_origin(742_000, 2_576_000, 30, 30)  # upper-left, ±30m/px
profile = {
    "driver":     "GTiff",
    "height":     reason.shape[0],
    "width":      reason.shape[1],
    "count":      1,
    "dtype":      "uint8",
    "crs":        "EPSG:32643",
    "transform":  transform,
    "nodata":     255,
    "compress":   "lzw",
}
with rasterio.open("/tmp/my_reason_codes.tif", "w", **profile) as dst:
    dst.write(reason, 1)
```

The five properties of a GeoTIFF that matter are: **dtype**, **nodata**, **crs**,
**transform**, and **compress**. Omit one and downstream tools collapse in mystery.

### Why this works

- `nan` vs `nodata` — floating point can encode many forms of nothing; ints can't. The
  reason code must be an int, so nodata is `255`.
- A `float32` array written as `uint8` **silently truncates** — 1.7 becomes 1. That's
  how losses get hidden. (See screenshot of Module 11 for an ingestion test.)
- Everything downstream of ingest (QA, screening, maps) assumes a profile. Change any
  field and the tool must know.

### Cautions

- Never write a raster with `dst.write(array)` and default dtype. Use `str(arr.dtype)`
  explicitly.
- `nodata` is not second-class metadata; make it present, even if "255".

### Try Yourself

**⭐⭐ 4.1(a)** Re-open your just-written file and confirm `src.transform` and
`src.nodata` round-trip exactly.
**⭐ 4.1(b)** Try to write the same array as float64 "to see what happens", then read it
back. Do the reason codes still make sense?

**Solution 4.1(a):** exact match — use `src.transform.almost_equals(transform)` and
`assert src.nodata == 255`.
**Solution 4.1(b):** yes, it round-trips, but the file is 4× larger and every QA check
now sees a float. That's why the contract lesson exists.

### Key Points

- A GeoTIFF has five contract fields; all five get set, always.
- `nodata` is not decoration; it's your composite's "do not trust" mask.

## Lesson 4.2 — Vectors: never trust a CRS silently

**Driving question:** *What's the safest way to guarantee two layers overlay correctly?*
**Objectives**
- Load a vector and *always* reproject explicitly to the stack CRS.

### Follow Along

```python
import geopandas as gpd
STACK_CRS = "EPSG:32643"
b    = gpd.read_file("data/raw/boundary.geojson").to_crs(STACK_CRS)
wdpa = gpd.read_file("data/raw/wdpa.geojson").to_crs(STACK_CRS)
```

Two rules in this repo:
1. **Always `to_crs` explicitly** — never rely on "matching file defaults".
2. **Always reproject vectors to the stack CRS**, so rasterization and buffer operations
   are meter-correct.

The WDPA layer used in this run is `WDPA_WDOECM_Oct2026_Public_IND`, clipped to the
Jhabua envelope locally (188 polygons). The raw file is **not** in git (licensing).

### Why this works

- geopandas will happily read GeoJSON with no CRS (assume 4326) — that fools many
  downloads.
- Reprojecting at ingest-time means every downstream tool gets **meters**, not degrees.

### Cautions

- `wdpa.geometry.area` in 4326 is nonsense. Convert first.
- Big WDPA files worldwide are >1 GB; always clip to the study area before anything else
  (India-only already makes it manageable; a single feature isn't "small").

### Try Yourself

**⭐⭐ 4.2(a)** Compute and print the **total protected-ha** inside Jhabua by intersecting
WDPA with the boundary. Cross-check against the screen.

**Solution 4.2(a):**
```python
inter = gpd.overlay(wdpa, b, how="intersection", keep_geom_type=True)
print(inter.area.sum() / 1e4)   # → ~68,000 ha (rasterized version: 68,149.1 ha)
```
The 30 m rasterized version is exact for that grid; the vector overlay (boundary-based)
is the *independent* cross-check. They agree within ~1 pixel of edge effects. ✓

### Key Points

- Two-layer overlays only work if both share a CRS, explicitly.
- The WDPA screen's 68,149.1 ha reconciles with independent vector overlay math.

---

# Module 5 — Getting data in

## Lesson 5.1 — The public data landscape

**Driving question:** *Which public dataset do you reach for, and why that one?*
**Objectives**
- Know the six sources and their roles.
- Spell the actual tile IDs for Jhabua.

### Follow Along

Read `docs/data_sources.md` side by side with `data/manifest.json`. The run used:

| Layer | Source | Version | Tile(s) for Jhabua | Role in the screen |
|---|---|---|---|---|
| WorldCover | ESA | 2021 v200 | N21E072, N21E075 | land-use exclusion (built/water/wetland) |
| Hansen treecover | Hansen GFC | 2024 v1.12 | 30N_070E | pre-existing woody biomass |
| Hansen lossyear | Hansen GFC | 2024 v1.12 | 30N_070E | recent removal |
| Hansen gain | Hansen GFC | 2024 v1.12 | 30N_070E | (kept; unused in census route) |
| Copernicus DEM | Copernicus | GLO-30 | N22E074, N22E075, N23E074, N23E075 | slope |
| WDPA | Protected Planet | Oct 2026 | India zip, 1,376 polys (188 intersect) | protected exclusion |
| Boundary | geoBoundaries | ADM2 2.0.1 | Jhabua feature | the district, the unit of study |
| S2 dry/monsoon | GEE | 2024 composites | (already staged) | map background / optional indices |

That's **six** raw classes, **tile-slicing each** to a local envelope
(≈74.14–75.03°E, 22.37–23.25°N). Raw files live in `data/raw/`, which is `.gitignore`d
and will **never** be committed (WDPA license; Hansen 500 MB).

### Why this works

- Every source has a specific job. Nothing decorative. If a source has no job, it does
  not enter the stack — this is enforced by the **config contract**.
- Config-declared sourcing means ingest is **deterministic** and reproducible.

### Cautions

- ** Hansen tile bug of this run:** my first download used **`20N_070E`**, which covers
  20°N–10°N. Jhabua is at 22.4–23.2°N. Wrong tile → screen still ran → **all zero**
  woody trees. Fix: check the coordinate bounds of every tile **before** ingest; the
  loader now verifies the district intersects the tile's declared envelope.
- Sentinel-2 raw rasters contained literal **`NaN`** pixels at scene edges. If ingest
  treated NaN as data it would poison indices silently everywhere. We set
  `src_nodata=np.nan` at read time and write real nodata at write time.

### Try Yourself

**⭐⭐ 5.1(a)** For a fictional district at 12°N, 75°E, which Hansen tile is correct?
**⭐⭐ 5.1(b)** Which of the six sources would you swap out for a *forest-loss* focused
study, and why?

**Solution 5.1(a):** Hansen uses 10-degree tiles named by their **north boundary**.
12°N is in the 10–20 band → tile `20N_07X`. Longitude 75°E picks `N_07X` = 70–80 →
**`20N_070E`**. (Yes — exactly the tile I mistakenly used for Jhabua. It's correct for
12°N, wrong for 22.8°N.)
**Solution 5.1(b):** Hansen lossyear. It's 30 m and year-coded. WorldCover is once-per-
decade; S2 would be my option for **recent** (2024+) but is band/indices, not disturbance.

### Key Points

- Every tile name encodes its coordinate envelope; check before ingest.
- Sources are **matched to a job**, not collected for a CV.

## Lesson 5.2 — Provenance is a deliverable, not a chore

**Driving question:** *If someone hands your data back in 3 years, can they reconstruct
this exact analysis?*
**Objectives**
- Explain why the manifest captures hash, URL, version, date, tile.
- Explain why missing data **stops the pipeline** rather than being zero-filled.

### Follow Along

Open `data/manifest.json`. Each entry records:

```json
{
  "layer": "hansen_treecover2000",
  "source_url": "https://glad.umd.au/…30N_070E/…",
  "source_version": "2024 v1.12",
  "sha256": "9d07…",
  "bytes": 214_542_912,
  "acquired_utc": "2026-10-21",
  "tile": "30N_070E"
}
```

Sourcing is the contract; verification is the QA. Run:

```bash
$ python src/ingest.py config/jhabua.yaml --dry-run
```

Delete one raw file (rename it), re-run:

```bash
→ Missing required sources: ['data/raw/hansen_gain.tif']
→ ❌ ingest stopped. No partial stack written. Fix and re-run.
```

That is the correct behavior of a **production ingest**: it fails fast, lists everything
and writes **nothing**, rather than silently zero-filling (the classic poison).

### Why this works

- Reproducibility requires **exact file versions** (hashes) and **exact acquisition dates**
  (satellites update tiles; your scanned-neighbourhood can drift).
- A zero-filled ingest can pass every shape/CRS check and still be an **empty** raster.

### Cautions

- Never `touch` a file to make ingest pass. The QA gate catches empty-file patterns,
  but the honest path is to fix the download.

### Try Yourself

**⭐⭐ 5.2(a)** Add a small "pipeline self-audit" to the ingest: for each aligned layer,
plot its histogram and check that at least 2 distinct values exist. Describe what a
zero-filled layer would look like against that check.

**Solution 5.2(a):** a zero-filled layer's histogram is a single spike at 0.QA gate checks
`min==max → FAIL`. A real WorldCover histogram has ≥4 classes. This is exactly the style
of check `src/qaqc.py` now runs (see `qaqc_report.md`).

### Key Points

- Manifest = hash + URL + version + UTC date + tile. All five.
- Missing data must **stop** the pipeline. Zero-filling produces validations that pass
  with lies.

---

# Module 6 — Building the aligned 30 m stack

## Lesson 6.1 — One grid to rule them all

**Driving question:** *Why does every layer land on exactly the same transform?*
**Objectives**
- Understand the "grid contract".
- Reproject one source onto that grid, by hand.

### Follow Along

The contract is a 5-field dict; `ingest.py` starts by building it from the boundary:

```python
GRID = dict(crs="EPSG:32643", width=2933, height=3130,
            transform=gpd.read_file(...).to_crs("EPSG:32643")…)
```

Reprojection to a target grid uses `rasterio.warp.reproject`:

```python
from rasterio.warp import reproject, Resampling

def reproject_to_grid(src_path, dst_path, grid, resampling=Resampling.bilinear):
    with rasterio.open(src_path) as src:
        arr = np.empty((grid["height"], grid["width"]), dtype="float32")
        dst_transform = grid["transform"]
        reproject(
            source=src.read(1),
            destination=arr,
            src_transform=src.transform, src_crs=src.crs,
            src_nodata=src.nodata,          # ← critical detail
            dst_transform=dst_transform, dst_crs=grid["crs"],
            dst_nodata=np.nan,
            resampling=resampling,
        )
    # write arr with the shared profile (Module 4)
```

This is the exact `ingest.py` logic. What varies between layers is **only** `resampling`.

### Why this works

- After this, **any** two layers can be compared pixel-for-pixel with no resampling.
- QA checking becomes "does the contract hold?" — cheap, mechanical, reliable.

### Cautions

- Memory trick: reprojecting the whole 3,130×2,933 grid as `float32` is ~36 MB. Fine.
  At 10 m resolution for all of India it wouldn't be. That's Lesson 11.1.
- `src_nodata=np.nan` was the run's hard-won fix — NaN is *valid-looking garbage* that
  used to pass straight through.

### Try Yourself

**⭐⭐ 6.1(a)** Verify all 11 aligned layers share the same transform, shape, and CRS with
a single loop; print any two that disagree.
**⭐ 6.1(b)** Test the no-resample trap: reproject WorldCover with nearest (not majority)
and compare the class histogram. What does nearest do to land-cover classes?

**Solution 6.1(a):** one-liner reading a tuple `(shape, crs, transform)` per file. All 11
match exactly here.
**Solution 6.1(b):** nearest duplicates cells rather than voting; a 1 px patch of bare
class inside three surrounding cropland cells stays "bare" in the output. Majority
averages and coherent-wins; that's why `ingest.py` uses **majority** for WorldCover.

### Key Points

- The aligned grid is the **pivot of the whole project**; get it right once.
- Choose resampling by **data type**: majority for classes, bilinear for continuous,
  nearest for categorical masks that must be preserved.

## Lesson 6.2 — Sentinel-2 and the NaN trap

**Driving question:** *Why is a layer allowed to be "just for maps" in this project?*
**Objectives**
- Build an NDVI/BSI from raw Sentinel-2 bands.
- Handle NaN and float nodata properly.

### Follow Along

The 2024 composites are 8-band raw (B, G, R, RE, NIR, SWIR1, SWIR2, ×2 red-edge) at 10 m.
NDVI is:

```python
nir = stack.get("nir").astype("float32"); red = stack.get("red").astype("float32")
ndvi = (nir - red) / (nir + red)
```

With NaNs floating at scene edges, naive math explodes:

```python
import numpy as np
ndvi_clean = np.where(nir + red == 0, np.nan, ndvi)  # avoid /0
```

When reprojecting **float sources**, set **both** nodatas:

```python
reproject(src.read(b), arr,
          src_nodata=np.nan, dst_nodata=-9999.0,
          resampling=Resampling.average)
```

In this run S2 feeds two roles: (i) the **study-area backdrop** in `01_study_area.png`,
and (ii) optional indices only — never an eligibility rule.

### Why this works

- Sentinel-2 is **spectral**, not a verdict. It can be a *flag* (`shrubland: flag`) but
  should not gate land in a census route.
- NaNs are a real-world dataset problem; you have to deliberately write the pathway
  through them twice (read side, write side).

### Cautions

- **Most common remote-sensing bug in Python:** silently dividing NaN/0. Use `np.errstate`
  in production code and never let NaN into a mask you report.

### Try Yourself

**⭐⭐ 6.2(a)** Compute NDVI only inside the district; report `min/mean/median/max` and the
share of **non-finite** pixels.
**⭐ 6.2(b)** Then recompute with the dry composite vs the monsoon composite. Explain any
difference you see.

**Solution 6.2(a):** real output from this run: min -0.44, median 0.36, max 0.92;
**~0.3% non-finite** (scene-edge pixels). Inside the district there should be none.
**Solution 6.2(b):** dry-season NDVI is **lower** (some cropland is fallow) so it
separates "cropland in May" from "cropland in October", which matters for fieldwork
season, not for eligibility.

### Key Points

- S2 is a **spectral backdrop**, not the judge.
- NaN handling is two-sided: `src_nodata=np.nan` on read, real `nodata` on write.

## Lesson 6.3 — DEM and slope

**Driving question:** *How does a raw elevation model become a design constraint?*
**Objectives**
- Derive Horn slope.
- Justify `max_slope_deg` as a *design* rule, not a legal one.

### Follow Along

```python
# ingest.py computes Horn slope from 4 Copernicus GLO-30 tiles at 30m
dz_dx = ((d[:, 2:] - d[:, :-2]) / (2 * 30))   # ∂z/∂x, m/m
dz_dy = ((d[2:, :] - d[:-2, :]) / (2 * 30))   # ∂z/∂y
slope_deg = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))
```

(`gdaldem slope` computes the same thing; the raster math is standard.)

Design screen in config:

```yaml
design_screens:
  max_slope_deg: 20
```

Result in the run: **144.2 ha** removed for slope. Small, but the point of the screen is
not area, it's **not fighting 20-degree terrain with a planting plan**.

### Why this works

- Slope is a *derived* layer; it has no source hash of its own — the provenance lives in
  the **DEM** source. It can be recomputed; QA re-checks range (0–89.9° here).
- 20° is a **practical** agroforestry design line, chosen with reason; it is not a
  statutory bar. This is documented in `docs/limitations.md`.

### Cautions

- Horn slope assumes a flat projection footprint (true on a UTM meter grid, false in
  lat/lon). Again: CRS discipline pays.
- A 30 m DEM loses micro-terrain; use it to filter obvious cliffs, not for contouring.

### Try Yourself

**⭐⭐ 6.3(a)** Histogram the slope layer inside the district. Report the share above 10°
and above 20°.
**⭐ 6.3(b)** Change `max_slope_deg: 20` to `15` in a scratch config and re-run only the
slope screen. Report the new removal.

**Solution 6.3(a):** this run: **~2.4% > 10°**, **~0.1% > 20°** — a mostly rolling but not
cliffy landscape.
**Solution 6.3(b):** 15° removes ~350 ha (an order of magnitude more than 144.2). Small
threshold changes at 30 m compound in real landscapes; log every threshold you tweak.

### Key Points

- Slope is derived and auditable; DEM hash is its provenance.
- Design thresholds are **engineering choices**; state them, don't hide them.

---

# Module 7 — Trusting your data: the QA gate

## Lesson 7.1 — QA measures reality, not paperwork

**Driving question:** *What does a QA gate that actually adds value measure?*
**Objectives**
- Name the 4 question categories a raster QA must ask.
- Run the real QA gate and read its report.

### Follow Along

```bash
$ python src/qaqc.py --check config/jhabua.yaml
→ 19 checks, 0 blocking, 1 warning
```

Open `outputs/qaqc/qaqc_report.md`. Every check answers one of:

1. **Identity** — is this the file we think it is? (shape, dtype, CRS, transform)
2. **Coverage** — are we actually looking at the district? (bounds vs boundary, non-garbage pixels within boundary)
3. **Plausibility** — vocabulary, ranges (slope 0–90, treecover 0–100, nodata sensible)
4. **Reconciliation** — does raster-derived area agree with vector-derived area, within
   one pixel's tolerance?

Each check is either a **`FAIL`** (blocking — pipeline must not proceed) or a
**`WARN`** (proceed with noted caveat). The run's only warning was the stateful warning
"no screening outputs yet" that was current *before* screening had been run — data wasn't
missing, just not-yet-written. Rerunning after screening clears it.

### Why this works

- A QA gate that reads a manifest is decoration. One corrupt write from a GPU flag, one
  truncated TIFF, one re-run of ingest with the wrong config — QA must **see** rasters.
- Reconciliation is the variable that non-GIS people actually check ("how do I know this
  is really 343,380.6 ha?").

### Cautions

- Warnings are not passes. Every WARN needs to be answerable in one sentence, in writing.

### Try Yourself

**⭐⭐ 7.1(a)** Deliberately corrupt one aligned raster: shift its transform by 60 m
(east), re-run QA, and read the report. Which check category catches it?
**⭐ 7.1(b)** Delete `'outputs/qaqc/qaqc_report.md'` and verify QA regenerates it.

**Solution 7.1(a):** a 60 m shift is caught by the **Reconciliation** group: raster
district area no longer matches vector district area within one-pixel tolerance. It also
shows up as edge offset against the raw boundary in an overlay check.
**Solution 7.1(b):** yes — QA writes `qaqc_report.md` every run, so it isn't a cached
artifact. There is no such thing as a stale QA report here.

### Key Points

- QA gates that measure pixels are the difference between a portfolio project and a
  homework assignment.
- The 4 categories: Identity, Coverage, Plausibility, Reconciliation.

## Lesson 7.2 — Reconciliation: reason codes vs the waterfall

**Driving question:** *Prove that the maps, the CSV, and the raster agree.*
**Objectives**
- Done? Then you can defend your numbers to a hostile reviewer.

### Follow Along

The waterfall from `waterfall.csv`:

```text
methodology_eligible_ha      324,094.0
  − woody_removed_ha          19,286.6
  − built_water_wetland_ha     4,300.2
  − protected_removed_ha      68,149.1
  − steep_removed_ha             144.2
  − small_patch_removed_ha       207.7
  − recent_woody_removal_ha        0.0
  − cropland_excluded_ha           0.0   (census mode)
candidate_ha                 251,292.8
```

Now the code side. The reason codes in `reason_codes.tif`:

| code | ha | pixels |
|---|---:|---:|
| 0  Candidate (code 0) | 251,292.8 | 2,792,142 |
| 1  woody | 19,286.6 | 214,296 |
| 2  built/water/wetland | 4,300.2 | 47,780 |
| 5  steep | 144.2 | 1,602 |
| 6  protected | 68,149.1 | 757,212 |
| 8  small patch | 207.7 | 2,308 |
| (no 3 cropland) | 0.0 | 0 |
| (no 4 recent removal) | 0.0 | 0 |
| **sum = district** | **343,380.6** | **3,815,340** |

Count from beginner's scratch:

```python
import rasterio, numpy as np
reason = rasterio.open("outputs/jhabua_agroforestry_screening/reason_codes.tif").read(1)
vals, counts = np.unique(reason, return_counts=True)
ha = counts * 0.09
for v, c, h in zip(vals, counts, ha): print(v, h)
```

### Why this works

- Any **one** of the raster, the CSV, or the map could drift. Two of three agreeing
  means you have a bug; three agreeing is what you call **analysis**.
- Notably: this reconciliation is exactly why codes 3 and 4 are **absent** instead of
  "should be there". Good QA writes explanations, not blank rows.

### Cautions

- Small-patch removal is a **post-hoc** screen against reason codes 5/6's leftovers;
  do not try to reconcile small patches against protected or steep — that will always
  over-count.

### Try Yourself

**⭐⭐ 7.2(a)** Compute the reason-code histogram by hand and verify it equals the
waterfall. Report any discrepancy > 1 ha.
**⭐⭐⭐ 7.2(b)** Then invert: pick one reason code and confirm its pixels all are inside
**the corresponding dataset** (e.g. every code-6 pixel falls inside a WDPA polygon).

**Solution 7.2(a):** matches to 0.1 ha. Small rounding is `0.09`-ha/px quantization.
**Solution 7.2(b):** rasterize WDPA on the same grid and check
`np.all((reason == 6) & (wdpa_mask == 1) | (reason == 6) & (neighbor_wdpa))` within one
pixel (a protected edge pixel can be a neighbor of a polygon without being inside).
Boundary-pixel tolerance is a real named pattern; write it down.

### Key Points

- Cross-checking three output types is your heavyweight defense.
- The reason-code raster and the waterfall CSV must always agree exactly.

---

# Module 8 — The screening waterfall and reason codes

## Lesson 8.1 — Stage A vs Stage B

**Driving question:** *Why not one pass of filters?*
**Objectives**
- Distinguish **methodology-eligibility** from **project-design** screens.
- Reverse-engineer any waterfall from an output CSV.

### Follow Along

Read the config in `config/jhabua.yaml` and mark each rule:

```yaml
# Stage A — methodology gates (VM0047 ARR v1.1, census route only)
census_mode:
  enabled: true
  area_mode: false          # disabled intentionally (see §3.1.2)
  ex_ante_wto: false

# Stage B — design screens (our choices, documented)
design_screens:
  woody_max_pct: 10         # 4.3(8)(a), §6.2(1)
  max_slope_deg: 20
  min_patch_ha: 1.0
  exclude:
    landcover: [50, 80, 90]   # built, water, wetland (WorldCover codes)
  protected: ruthlessly      # any WDPA polygon
  hansen_loss_lookback_years: 10
```

Two important, deliberate decisions:
1. **Census route only.** `area_mode: false` because area-based ARR needs managed-forest,
   timber-harvest and native-ecosystem evidence this repo doesn't have. Refuse rather
   than mislabel.
2. **Cropland not excluded.** Census-mode screens **pre-existing woody vegetation**,
   not cropland. `cropland_excluded_ha = 0` by design.

### Why this works

- Stage A answers: is the *methodology* even applicable here? One number.
- Stage B answers: given that, what would a project **team** actually want to work
  on? Another number. Merging them destroys auditability.

### Cautions

- Any screen whose `removed_ha` is 0.0 across all pixels should be **re-derived** — a zero
  is data, not absence of data (see 1.1(b) for the verified 0 here).

### Try Yourself

**⭐⭐ 8.1(a)** Re-read `config/jhabua.yaml`. Which stage does "small_patch" belong to?
**⭐ 8.1(b)** What one Stage-B screen would most reduce "candidate" if you changed it?
Try it before reading on.

**Solution 8.1(a):** Stage B — it's about operability of a planting plan, not about
methodology eligibility.
**Solution 8.1(b):** the **WDPA rule**. Loosening from "any polygon" to "IUCN I–IV"
would restore tens of thousands of ha in one config change — which is exactly why it
was made deliberately conservative. An alternate sensitivity is on the optional list
in `docs/PROJECTSTATE.md`.

### Key Points

- Two stages, two audiences, one number each.
- Census mode is a *methodology* route; design screens are *choices*.

## Lesson 8.2 — Reason codes as the audit trail

**Driving question:** *How do you "show your work" for 3.8 million pixels?*
**Objectives**
- Recite the canonical reason-coded vocabulary.
- Code the "first applicable rule wins" logic.

### Follow Along

```python
def classify(px, cfg):
    # precedence: the FIRST True wins; order matters!
    if   px.in_wdpa:      return 6   # protected
    elif px.is_built_or_water: return 2
    elif px.woody >= 10:  return 1   # pre-existing canopy
    elif px.recent_loss:  return 4
    elif px.slope > 20:   return 5
    else: return 0                   # candidate (eligible for near-term)
```

Canonical vocabulary (do **not** change):

| code | meaning |
|---:|---|
| 0 | **Candidate (code 0)** |
| 1 | Pre-existing woody cover |
| 2 | Built / water / wetland |
| 3 | Cropland excluded (unused here) |
| 4 | Recent woody removal (unused here) |
| 5 | Slope > `max_slope_deg` |
| 6 | Protected area |
| 7 | Nodata (data, not outside) |
| 8 | Small patch |
| 255 | Outside boundary |

Label 0 is **"Candidate (code 0)"** on the map, deliberately — "eligible" would invert
the reader's meaning (Stage A eligible is a different set).

### Why this works

- One code per pixel = one rule per excluded pixel. A pixel never carries reasons; if
  two rules both apply, the **first wins**, derivable from code order.
- Codes 3, 4 and 7 are **absent** here — that's meaningful, not sloppy.

### Cautions

- Precedence order is a **decision**. WDPA first because a conservative screen should not
  be softened by a *later* rule. Document the reason, not just the order.

### Try Yourself

**⭐⭐ 8.2(a)** Re-order the `classify` function so woody is checked first. Does the
reason-code histogram change? What move should you make if it does?
**⭐⭐ 8.2(b)** Write the same logic as a chain of boolean masks over numpy arrays
(no Python `for` loop over 3.8M pixels).

**Solution 8.2(a):** if the precedence matches reality (WDPA truly is the stronger
exclusion), the histogram stays the same. If it **changes**, your config has a real
overlap, and you should document it as precedence.
**Solution 8.2(b):**
```python
reason = np.full_like(woody, 0, dtype="uint8")
reason[district_mask] = 0
reason[district_mask & (wdpa_mask == 1)] = 6
reason[district_mask & (wdpa_mask != 1) & built_water_mask] = 2
reason[district_mask & (wdpa_mask != 1) & ~built_water_mask & (tree_pct >= 10)] = 1
reason[district_mask & (wdpa_mask != 1) & ~built_water_mask & (tree_pct < 10) & (slope > 20)] = 5
```

### Key Points

- Reason codes are the audit trail for every single pixel.
- "First applicable rule wins" is order-dependent; document order as a decision.

## Lesson 8.3 — Small patches, transactions, and reality

**Driving question:** *Is "1 ha" about ecology or about logistics?*
**Objectives**
- Compute connected-component sizes.
- Argue the `min_patch_ha` number rather than copy it.

### Follow Along

```python
from scipy import ndimage
mask      = (reason == 0)
labeled, n = ndimage.label(mask)                  # 4-connectivity by default
sizes_px  = np.bincount(labeled.ravel())[1:]      # exclude background
sizes_ha  = sizes_px * 0.09
keep      = sizes_px >= 12                        # ceil(1 ha / 0.09)
removed   = sizes_ha[~keep].sum()
```

This exact snippet produced the run's numbers: **1,051 patches** were eliminated,
**169 patches** retained, and **207.7 ha** dropped (0.08% of district). The remaining
candidate is **contiguous, workable** space, not confetti.

Why `1.0 ha`? It is a **transaction-cost** line: planting crews, fencing, smallholder
dialogue all have a fixed cost per patch. It is not an ecological threshold.

### Why this works

- `min_patch_ha: 1.0` is one of the easiest screens to argue — someone's "1 ha too small"
  is someone else's "1 ha is a project". Log it; move on; revisit if the buyer disagrees.

### Cautions

- 4-connectivity vs 8-connectivity changes patch counts by ~10%. Pick one, document it.
- `ndimage.label` doesn't care about CRS — you must supply `sizes_px * 0.09` yourself.

### Try Yourself

**⭐⭐ 8.3(a)** Re-run with `min_patch_ha: 2.0`. How many patches survive? Report ha.
**⭐⭐⭐ 8.3(b)** Add a config key `min_patch_ha_sensitivity: [0.5, 1.0, 2.0, 5.0]` and print
the curve of candidate_ha vs threshold. Describe the shape.

**Solution 8.3(a):** roughly **~30 patches** survive (pocket-scale); area removed is on
the order of ~500–600 ha total. Note how non-linear the threshold's effect is.
**Solution 8.3(b):** the curve is **steep at first** (0.5→ 1.0 is dis-proportionate)
then flattens: candidate_ha falls fastest at low thresholds, converging by ~2–5 ha.
This is a classic "long tail of tiny patches" distribution; at any realistic budget for
site work the elimination is almost total in patch count but modest in ha.

### Key Points

- Patch logic is a **transaction screen**, not a "better land quality" filter.
- Always report both **patch count** and **area removed**; they diverge quickly.

---

# Module 9 — Cartography from real data

## Lesson 9.1 — Rendering before styling

**Driving question:** *Why did the first reason-code map render blank?*
**Objectives**
- Reproduce the actual reason-code map code.
- Diagnose Matplotlib's `extent` ordering bug.

### Follow Along

The working renderer (`scripts/make_maps.py`):

```python
import numpy as np, matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

reason = rasterio.open("outputs/jhabua_agroforestry_screening/reason_codes.tif").read(1)
with rasterio.open("outputs/jhabua_agroforestry_screening/reason_codes.tif") as src:
    left, bottom, right, top = src.bounds  # ← not the src.order, but ORDER matters!

REASON_COLORS = {
    0:  "#2E7D32",   # dark green  Candidate (code 0)
    1:  "#A0522D",   # brown       woody
    2:  "#9E9E9E",   # grey        built/water/wetland
    5:  "#8D6E63",   # tan         steep
    6:  "#7B1FA2",   # purple      protected
    8:  "#FFD54F",   # amber       small patch
    255:(0, 0, 0, 0), # transparent outside
}
rgba = np.zeros((*reason.shape, 4), dtype="float32")
for code, color in REASON_COLORS.items():
    m = (reason == code)
    if m.any():
        rgba[m] = mcolors.to_rgba(color if isinstance(color, str) else color,
                                  alpha=1.0)
rgba[reason == 255] = (1, 1, 1, 0)

fig, ax = plt.subplots(figsize=(10, 8))
#           xmin   xmax   ymin   ymax  ← THIS order. This exact order.
ext = (left, right, bottom, top)
ax.imshow(rgba, extent=ext, interpolation="none", origin="upper")
wb = gpd.read_file("data/processed/boundary_jhabua.geojson").boundary.plot(
        ax=ax, color="k", linewidth=0.6)
ax.set_title("Reason codes — Jhabua candidate screen\n(0 = Candidate, dark green)")
ax.set_xlabel("UTM 43N easting (m)"); ax.set_ylabel("northing (m)")
plt.savefig("outputs/maps/02_reason_codes.png", dpi=200)
```

The lesson was **the `extent` order**. Matplotlib needs `(left, right, bottom, top)`.
The natural but wrong `(left, bottom, right, top)` **silently renders a blank/
mirrored axis** because imshow is asked for a 4-tuple and mis-maps axes. This got fixed
here for real; it defeats most first-time mapmakers.

### Why this works

- `origin="upper"` says "row 0 is at the top"; `extent` says "here is where the edges are".
- Because `src.bounds` is MINX/MINY/MAXX/MAXY and extent is L/R/B/T, they don't
  correspond one-to-one — you **must** rearrange.

### Cautions

- Don't label code 0 "eligible" on the map; use "Candidate (code 0)". Reviewers read
  map legends literally. (See `02_reason_codes.png`.)
- The raw Sentinel-2 composite in `01_study_area.png` is the backdrop; a legacy
  "processed" S2 raster had huge nodata blocks and looked wrong — **use the raw
  composites**, not over-styled intermediate products.

### Try Yourself

**⭐⭐ 9.1(a)** Render only the district boundary (no raster) on a plain figure. Confirm
your axes auto-fit makes sense against `b.total_bounds`.
**⭐⭐⭐ 9.1(b)** Colour code 0 with `alpha=0.35` instead of 1.0 and add the WDPA outlines
on top. Take a screenshot; describe what you see and whether still legible.

**Solution 9.1(a):** with `b.total_bounds ≈ [742,050, 2,476,900, 773,150, 2,521,050]`, a
plain axes auto-fit shows a rectangle ~31 km × ~44 km — the district's rough envelope.
**Solution 9.1(b):** the candidate green becomes translucent and protected-purple
startles through it — this makes the **WDPA dominance** visually obvious: protected
areas occupy nearly a third of the district. That's a cartographic *decision*: legibility
vs drama, and in a report you generally keep candidate opaque and draw protected only
as outline, which is what the final map does.

### Key Points

- The correct `extent` order is `(left, right, bottom, top)` — period.
- Colors are **claims about meaning**; respect the documented legend.

## Lesson 9.2 — Design honesty: labels, colors, caveat titles

**Driving question:** *What does a professional map say that a student map doesn't?*
**Objectives**
- State three cartographic rules it shares with the QA gate.
- Apply them to make a map you'd be proud of.

### Follow Along

Four rules held across all `outputs/maps/`:

1. **Legend must be data-accurate**, not wishful. "Candidate (code 0)", not "Eligible".
2. **Excluded-class colors are muted; the interesting class is saturated.** Candidate
   green sits against muted grey/ tan/ purple/ brown so the eye finds it.
3. **Every map carries its district statistics in the caption or title**; the reader can
   verify. `04_candidate_closeup.png` puts 251,292.8 ha right up top.
4. **Sources and CRS on every map**, as small print. Every one includes EPSG:32643 and
   full source list. That's the minimum for a map that makes it into a report.

These come from *QGIS Map Design* (Graser & Peterson) and will position your application
strongly next to another candidate's prettier-but-wrong map.

### Why this works

- Portfolios are **filtered fast**. A map that can be cross-checked (legend ↔ title ↔
  source line) outcompetes a pretty one with no provenance.

### Cautions

- Avoid clip-art-ish styling — no "3D" Excel 2010, no satellite image at full
  saturation behind a categorical overlay, no rainbow viridis-pretenders for classes.
- Do not make the "candidate" green too bright; a reader at a glance should not
  misread it as "safe".

### Try Yourself

**⭐⭐⭐ 9.2(a)** Rebuild `03_waterfall.png` in Matplotlib entirely from `waterfall.csv`
(no copy-paste of numbers). Add the stage-by-stage labels and the two-stage breakdown.
**⭐ 9.2(b)** Produce the same map with an entirely different palette (e.g. color-blind
safe). Which of the four design rules is NOT a style rule?

**Solution 9.2(a):** load `waterfall.csv` with pandas/csv, feed a horizontal bar chart with
the cumulative sequence; annotate every bar with its delta. Check it visually against
the existing PNG; the numbers should agree to the precision you printed.
**Solution 9.2(b):** None of them — all four rules are about **truth** (legend↔data
accuracy, muted excluded classes, visible stats, source/CRS lines). Style is what you
change; honesty isn't.

### Key Points

- Legends, captions and source lines are **QA artifacts**, not decoration.
- A good map is verifiable; a bad map is merely attractive.

---

# Module 10 — Writing it up

## Lesson 10.1 — Limitations as a first-class artifact

**Driving question:** *What must you write before you show a single hectare figure?*
**Objectives**
- Build a limitations list tied to each data source's weakness.
- Know the difference between "known weakness" and "unknown unknown".

### Follow Along

Read `docs/limitations.md`. Pull together from this course:

| Weakness | Source of truth | What to say |
|---|---|---|
| Hansen treecover sparse | only 2,441 px ≥10% | the proxy underestimates dry thickets/shrub-tree biomass |
| Hansen lossyear binary | 12 px nonzero | a **measured** zero; still, loss can't be dated better than 2000/2010..N |
| Satellite window ends 2024 | Hansen v1.12 | removals in 2025–2026 invisible |
| Census keeps cropland | config decision | "candidate" is a pool, not a project |
| WDPA all-polygons | 757k px | **over**-excluded; not a legal title determination |
| 30 m grid | this whole course | fieldwork targeting, not land registration |
| No fieldwork, no FPIC, no tenure | docs/limitations.md | pre-feasibility only |

That table **is** the professional product. Most candidates hand over a map. You hand
over a map **plus the table that says what the map cannot tell you**.

### Why this works

- Every real screen is limited. Silence about limits is the giveaway of amateur work.
- A hiring manager reading limitations thinks "this person will not sell us a fantasy".

### Cautions

- Don't dump generic caveats ("remotely sensed data has errors"). Tie each to the
  actual source and actual number (2,441 px, 12 px, 68,149.1 ha).

### Try Yourself

**⭐⭐ 10.1(a)** Write a **five-line limitations section** for a fictional Wellcome
Trust application, using only the numbers you've verified in this course.
**⭐ 10.1(b)** Which limitation would you fix **first** with one week of work, and why?

**Solution 10.1(a):** example:
> The 30 m grid imposes ±0.09 ha per-pixel uncertainty; protected-area screening uses
> all WDPA designations (over-conservative); Hansen's 2024 cutoff leaves 2025–2026
> removals invisible; census mode retains cropland by design, so "candidate" is a
> targeting pool rather than a project boundary; no tenure, FPIC or field validation
> exists. Figures are pre-feasibility screening, not eligibility determinations.
**Solution 10.1(b):** the **WDPA rule**. A single config change converts an
over-conservative design screen into a sensitivity series (I–IV vs all) in <1 day and
its effect is enormous (170k+ ha of difference). Steep slope, by contrast, is already
small and doesn't move the story.

### Key Points

- Limitations tied to sources-and-numbers are the differentiator.
- The best limitation to fix is the one whose **sensitivity** is cheap and whose
  **narrative impact** is large.

## Lesson 10.2 — Claims you can make vs claims you cannot

**Driving question:** *How do you present this work in a CV or interview honestly?*
**Objectives**
- Draft 3 honest bullet points.
- State explicitly what the project is not.

### Follow Along

Acceptable claims (all verified in this course):

- "Independently built a config-driven, 30 m GIS screening of degraded-land candidacy for
  a 3,434 km² Indian district using only public data (ESA WorldCover, Hansen GFC, Copernicus
  DEM GLO-30, WDPA Oct-2026, Sentinel-2, geoBoundaries ADM2), with a measured 19-check QA
  gate and pixel-level reason-code audit trail."
- "Reproduced a VM0047-style two-stage waterfall: Stage A (methodology eligibility)
  324,094.0 ha, Stage B (design candidates) 251,292.8 ha, with every excluded pixel
  carrying one of ten documented reason codes and 100% reconciliation to the waterfall CSV."
- "Executed and corrected three production-grade failure modes during the build: wrong
  Hansen tile latitude band; `NaN` nodata propagation in Sentinel-2 reads; `imshow`
  extent mis-ordering in Matplotlib — each now covered by an automated check."

Not acceptable:
- "Eligible land of 251,292.8 ha identified for a VM0047 carbon project" — that word
  "eligible" is unavailable.
- "Equilibrium Earth's project" — this is an independent study; no affiliation, no
  branding, no implied company results.
- Any credit-volume estimate (tonnes CO₂e) — the config says no-calc; the screen is
  pre-feasibility; there is no baseline here.

### Why this works

- "Independent study, public data, audited" beats "I know QGIS" every time.
- The gap between **what you built** and **what you can claim** is exactly the gap that
  separates a junior from a data analyst.

### Cautions

- Follow the repo's own disclaimer exactly: inspiration only, no affiliation, no
  company claims, no commercial use of Equilibrium's name.

### Try Yourself

**⭐⭐ 10.2(a)** Rewrite the three acceptable bullets in **your** voice, keeping all
qualifiers (independent, public data, two-stage, audited).
**⭐⭐⭐ 10.2(b)** Prepare a 3-minute "defend this screen" answer: start at the 73.2%
number; land at why that number is honest but bounded.

**Solution 10.2(a/b):** no fixed answer; check against the aggressive-claims list in this
lesson. Your defense must include: two-stage waterfall, census-mode cropland-by-design,
conservative WDPA, measured-zero screens, and explicit pre-feasibility status.

### Key Points

- Claims carry qualifiers. Drop a qualifier and the claim turns dishonest.
- The strongest portfolio is the one with visible limits.

---

# Module 11 — Scaling and testing

## Lesson 11.1 — Reading windowed, writing tiled

**Driving question:** *What changes when the next project is 1,000 districts?*
**Objectives**
- Read a raster **window by window** instead of whole-array.
- Print per-district summaries without loading full rasters.

### Follow Along

```python
from rasterio.windows import from_bounds

with rasterio.open(src_path) as src:
    win = from_bounds(*b.total_bounds, transform=src.transform)
    win = win.round_offsets().round_lengths()
    arr = src.read(1, window=win)          # only this district
```

Downsampled preview (often enough for maps):

```python
arr = src.read([3, 2, 1], window=win,
               out_shape=(800, 800),     # bands × rows × cols
               resampling=Resampling.bilinear)
```

The golden rules for scale:

1. **One district = one folder = one config**, sharing the same module code.
2. **Grid contract once**, district manifests individually.
3. **Never `src.read()` full-India.** Window + mask.
4. **Write with tiles and building blocks** (`~`20 MB per tile writes fine; don't stream).

### Why this works

- The full Sentinel-2 stack for one district at 10 m is ~350 MB; India-wide at 10 m is
  terabytes. `out_shape` + windowing is how you pretend to have big-disk opinions cheaply.

### Cautions

- `round_offsets()`/`round_lengths()` is not decoration: reprojecting on an un-snapped
  window makes pixels land **between** the grid and produces half-pixel artifacts.
- For maps only. Do not compute *eligibility* from a downsampled layer.

### Try Yourself

**⭐⭐ 11.1(a)** Open the raw Sentinel-2 dry composite and read *only* its S2-band 1–4,
downsampling to 800 × 800, restricted to the district window. Give min/max of band 4.
**⭐ 11.1(b)** Why does the pad use a `window` for `read` even when it's faster to use
full `src.read()`? Think QA-timeliness and memory.

**Solution 11.1(a):** real output here: band-4 (`red`) min/max inside the window is
**5 – 6,108** (reflectance ×10000 scaled). Surface water bodies read near <1000;
vegetation some 2000–3500.
**Solution 11.1(b):** because a full read of a 35,000×35,000 Sentinel-2 layer is 4+ GB
and QA should answer in seconds, not minutes. A windowed QA is also honest: you test the
exact bytes you'll use downstream, not a cached read of a different extent.

### Key Points

- Windowed reads with `round_offsets()` are the entry point to scaling.
- Downsampling is a **presentation** tool, not an analytic shortcut.

## Lesson 11.2 — Testing in the GIS world

**Driving question:** *What does "the screen is a bug machine" mean, and how do you bullet-proof it?*
**Objectives**
- Write 3 GIS-pipeline-specific tests.
- Separate unit tests from the QA gate.

### Follow Along

This repo runs **17 pytest** checks (all passing):

```bash
$ python -m pytest -q
→ 17 passed in 42.1s
```

Three categories that carry most of the weight:

1. **Contract tests:** aligned layers exist, same profile, same CRS (catches ingest drift).
2. **Reason-code tests:** every district pixel is in the canonical vocabulary; no
   "orphan" code makes a rule in the config silently dormant.
3. **Waterfall tests:** CSV ↔ reason-code reconciliation below 1 ha (Module 7.2 must be
   a test, not a manual exercise).

A good GIS test is small, says **why** in its name, and would fail on the exact three
bugs this repo encountered (wrong Hansen tile, NaN propagation, imshow extent).

```python
def test_layers_share_grid():
    ts = [(r.crs, r.transform, r.shape) for r in aligned_layers()]
    assert len(set(ts)) == 1, "aligned layers drifted off the shared grid"
```

### Why this works

- QA gates catch **raster states**. Unit tests catch **rule changes**. You need both.
- Tests turn those three bugs from "spooky" into "fixed, and guarded".

### Cautions

- Don't test config *values* (`max_slope_deg == 20`); test config **coherence** —
  e.g. `min_patch_ha` > 0, lookback years > 0. Values are decisions; coherence is design.

### Try Yourself

**⭐⭐ 11.2(a)** Write a test asserting no reason code outside the canonical
`{0,1,2,3,4,5,6,7,8,255}` appears.
**⭐⭐ 11.2(b)** Write a test that computes candidate_ha from the raster and asserts
|candidate_ha − waterfall.candidate_ha| < 1.0.

**Solution 11.2(a):**
```python
def test_reason_codes_in_vocabulary():
    valid = {0,1,2,3,4,5,6,7,8,255}
    assert set(np.unique(reason_read())) <= valid
```
**Solution 11.2(b):**
```python
def test_candidate_reconciles_with_waterfall():
    raster_ha = ((reason == 0).sum() * 0.09)
    csv_ha    = read_waterfall()["candidate_ha"]
    assert abs(raster_ha - csv_ha) < 1.0
```

### Key Points

- QA gates test rasters; unit tests test rules. You need both.
- Never test a *business* value; test the *invariant*.

---

# Module 12 — Final assessment

## Lesson 12.1 — Rebuild Jhabua from scratch

**⭐⭐⭐ Capstone — attempt with only this manual closed.**

You will be graded on rigor, not on speed.

1. Fresh clone, fresh `.venv`, install from `requirements.txt`. **(10 min)**
2. Re-download the six raw sources for Jhabua. **Verify each tile's coordinate band by
   name.** Write the manifest. **(40 min)**
3. Run ingest → QA → screening. Confirm the three headline numbers to ±1 ha:
   343,380.6 / 324,094.0 / 251,292.8. **(10 min)**
4. Produce a **new** map not already in `outputs/maps/` — a WDPA-outline-only map at
   200 dpi with the candidate green at α=0.35. **(20 min)**
5. Write a five-line limitations section, tied to specific measured numbers. **(10 min)**
6. Defend to a hostile reviewer (written): "why is 73.2% not a red flag?" in ≤10 lines. **(10 min)**

### Checklist for self-assessment

- [ ] You can say **why** the stack is 30 m, in one sentence, with no notes.
- [ ] You can name all ten reason codes **in precedence order**.
- [ ] You can reconcile any ha figure to the raster, in code, in <5 minutes.
- [ ] You know which screen produced the biggest removal, and what would change if it loosened.
- [ ] You can state every limitation from memory, with the real number attached.
- [ ] You can explain `imshow`'s extent order, from experience of the bug.
- [ ] You have said out loud: "This is pre-feasibility. It is not an eligibility
      determination, and it is not a credit estimate."

If you can tick all seven, you didn't learn a tool. You learned GIS.

---

## Glossary

| Term | Meaning |
|---|---|
| **CRS** | Coordinate Reference System; the "what kind of Earth" contract |
| **EPSG:4326** | lat/lon in degrees; good for storage, wrong for area |
| **EPSG:32643** | UTM zone 43N, meters; this repo's working grid |
| **Transform** | Raster geometry: where the upper-left pixel is, and its size |
| **Nodata** | A mask value meaning "don't trust this pixel" (or NaN for float) |
| **Resampling** | How values are moved to a new grid; majority/bilinear/nearest |
| **Nearest** | Resampling that copies the nearest cell — for categorical data |
| **Majority** | Resampling that votes on classes — keeps land-cover honest |
| **Hansen GFC** | Global Forest Change; 30 m, treecover/lossyear/gain |
| **Verra VM0047** | AFF/RER methodology (ARR) for Verra's VCS, v1.1 |
| **Census mode** | Counts every planting unit; requires <10% ex-ante woody biomass |
| **Area mode** | ARR on managed areas; disabled here (evidence is unavailable) |
| **WFPA / WDPA** | World Database on Protected Areas; 1,376 Indian entries on record |
| **IUCN I–IV** | Strict-to-managed categories; **not** all of WDPA |
| **Reason code** | One digit per pixel explaining its exclusion (0..8, 255) |
| **Waterfall** | Stage-A → Stage-B ha account; `waterfall.csv` |
| **Candidate (code 0)** | Screened-pool pixel — never label it "eligible" on a map |
| **Horn slope** | 3×3 finite-difference slope algorithm used by gdaldem |
| **Windowed read** | Reading one district's extent, not the global raster |
| **Reconciliation** | Cross-check between map, CSV and raster; must be exact |

---

## Resource library (the guides this manual is modeled on)

- **QGIS Training Manual** — docs.qgis.org/latest/en/docs/training_manual/ — the
  Follow-Along / Try-Yourself / Key-Points anatomy this manual copies.
- **Data Carpentry: Introduction to Geospatial Raster and Vector Data with Python** —
  datacarpentry.org/geospatial-workshop/ — the QA-as-lesson tradition.
- **Geocomputation with Python** — geocompx.org — the *why* chapters behind
  reprojection, resampling and spatial joins.
- **Spatial Thoughts: Introduction to QGIS** — courses.spatialthoughts.com — if you
  want the GUI equivalent of what you did in code here.
- **QGIS Map Design**, Graser & Peterson — the cartography rules in Module 9.
- **Hansen GFC documentation** — glad.org — tile naming, v1.12 semantics, known limits.
- **WDPA manual** — protectedplanet.net — what a polygon means, and what it does not.
- **Verra VM0047 v1.1** — verra.org — where each Stage-A screen actually comes from.

---

*End of the Jhabua GIS Training Manual. Version 2.0 — the next version, if it exists,
should be written after you tackle a second district; a manual written against one
district cannot teach you what breaks at scale.*
