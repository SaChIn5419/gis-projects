# QA Gate + CRS Check — Landslide Inventory Ingestion (p3)

**Purpose.** A repeatable pre-analysis gate that the second-hazard landslide layer
passes before it is used to re-derive R-1/R-3 exposure. Catches CRS mismatch, empty
clipping, and attribute-less-archive failures before they silently change the hazard
definition.

**Signed-off:** 2026-11-05 (script validated end-to-end against the D-15 WMS proxy
inventory — 990 raw features → 543 clipped features, EPSG:32643, attributes preserved).

---

## 1. CRS check

| Step | What | Pass criterion | Fail → |
|---|---|---|---|
| C1 | Raw inventory CRS declared? | Yes, or assign without error | Abort — cannot clip safely |
| C2 | Inventory aligned to project CRS (EPSG:32643)? | `inventory.to_crs(32643)` | Abort — wrong-zone analysis |
| C3 | AOI aligned to project CRS (EPSG:32643)? | `aoi.to_crs(32643)` | Abort |
| C4 | Output geometry in EPSG:32643? | `output.crs.to_epsg() == 32643` | Abort — reprojection drift |

## 2. Attribute check (fail-fast)

The archive must carry **at least one attribute column** (e.g. event ID, date, type).
If the raw inventory is a bare spatial layer (no attributes), the script aborts with an
explicit message rather than silently producing an attribute-less layer that would
silently change R-1/R-3. This is the single most important QA gate: a WMS-rendered
proxy is *not* the same as an attribute-bearing inventory.

## 3. Clipping QA

| Metric | Pass |
|---|---|
| Output feature count | > 0 (non-empty AOI coverage) |
| No duplicate rows | dedupe on attribute columns, keep first |
| Extent within AOI | output total_bounds ⊆ AOI total_bounds |

## 4. Post-write verification

The script prints, after export:

- output feature count
- output CRS (EPSG:32643)
- geometry type(s)
- first 6 attribute columns
- QA PASS/FAIL line

## 5. Known environment note (non-fatal)

The miniforge3 PROJ data path (`share/proj/proj.db`) is not auto-discovered in this
sandbox, so the script prints a `proj_create_from_database` warning. It is harmless —
geometry/layers still read and reproject correctly — but `PROJ_DATA` should point at
`<miniforge3>/share/proj` when running in a fresh environment. Documented once, not
re-litigated; keep it as-is.

## 6. Pre-run read-only checks (before handing off the archive)

The operator should (non-interactively) verify:

1. Archive CRS declared and plausible for India (EPSG:32643, or a local CRS to be
   transformed to 32643).
2. Attribute schema present.
3. AOI is the Wayanad district boundary (EPSG:32643), not a smaller study scallop.
4. Clip produces a non-trivial count (not 0, not equal to the full archive unless
   the AOI covers everything).
