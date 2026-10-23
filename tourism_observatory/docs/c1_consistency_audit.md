# C1 cross-file consistency audit (2026-10-22)

Scope: all 2026-10-22 artifacts of the Wayanad investigation — `preregistration_wayanad.md`,
`literature_matrix.md`, `data_audit_wayanad.md`, `config/wayanad.yaml`, `README.md`,
plus `docs/PROJECTSTATE.md` §9. Method: byte-level re-read of every file, cross-reference
of hypotheses ↔ deviation entries ↔ audit verdicts ↔ config ↔ status pages, SHA-256
verification of the frozen triad, then administrative fixes applied under **dev-D-9**.

## 1. Verified consistent (no action)

1. **Deviation-trail integrity.** D-0 … D-9 form an unbroken append-only chain; no frozen
   hypothesis text was edited at any point. Original prereg §3-H2 (single H2) and §4
   matching rules remain in place, correctly superseded by dev-D-2/dev-D-4 without deletion.
2. **Verdict chain.** Audit verdict v1 (retained) → v2 CONDITIONAL GO marker matches
   dev-D-6; `config/wayanad.yaml` `audit_status: CONDITIONAL_GO` matches; README P1
   "AUTHORIZED under CONDITIONAL GO" matches; PROJECTSTATE §9 authorization statement
   matches. No file claims analysis-phase authorization.
3. **Information boundary.** The yaml `forbidden_until_c1_final` list aligns with prereg
   §5: change rasters, NDVI/built-up deltas, BACI outputs, HEC surfaces, exposure
   registers, imagery construction dating — all absent from the baseline config by design.
4. **Scope statements.** "Exactly two sites, no third case, no foreign benchmark" identical
   in README, prereg, matrix, PROJECTSTATE.
5. **Labeled proxies.** Road-access covariate labeled current-OSM proxy in both dev-D-4
   and the yaml (`osm_roads_current` comment) — consistent with review §6.
6. **Hash discipline.** R2 hashes re-verified on disk before edits; after dev-D-9 edits,
   R3 computed and recorded. See §5.
7. **Audit §9 disposition table.** Every C1 action-register item maps to a concrete
   deviation entry; no register item left undispositioned.

## 2. Findings fixed (administrative, applied under dev-D-9)

| # | Finding | Fix | Original wording preserved |
|---|---|---|---|
| F-1 | Triple ID-space collision: matrix §D rows `D1–D4` vs audit source IDs `D-1…D-21` vs prereg deviation IDs `D-x`; plus "C1" = both the sign-off checkpoint and the HEC-paper row (matrix C1) | Binding ID convention in dev-D-9 (`lit-Cx`/`lit-Mx`, `audit-D-x`, `dev-D-x`, `checkpoint-C1`); matrix rows renamed M1–M4 incl. §E table | Rows quoted in git history + summary below |
| F-2 | Matrix M1 author string garbled: "Topuz & Với" | "Topuz, M. et al." — citation remains in the verify queue | "Topuz & Với" (this table) |
| F-3 | Audit §8 closing line "→ **GO for P1 data acquisition once user cross-checks**" contradicted verdict v2 | Superseded marker appended; v1 text retained verbatim | ✓ (marker quote below) |
| F-4 | Audit §9 header typo "supersêdes" | "supersedes" | — |
| F-5 | Audit §10 ledger: audit-D-19 assigned twice; audit-D-9 mislabeled "peer-reviewed+official" (it is institutional); audit-D-18/-20/-21 and audit-D-11…D-17 untyped; taxonomy lacked an open-data type | Ledger rewritten with corrected table + `open satellite/raster` category | Earlier line: "Assigned so far: D-1/D-2/D-3/D-4 official statistics · D-5/D-19 official inventory · D-6 news/institutional mix (per-source) · D-9/D-19 peer-reviewed+official mix · D-10 peer-reviewed (verify) · D-21 official." |
| F-6 | README structure tree stale: "checklist PASS 6/6" | "verdict v2 CONDITIONAL GO" | "checklist PASS 6/6" |

Authoritative wording trail for F-3 and F-6 (originals):

> F-3 original: "✅ (scenario-only) · reproducible ✅ → **GO for P1 data acquisition once
> user cross-checks.**" — now followed by a superseded marker; text unchanged.
> F-6 original: "(FROZEN: 21 sources, checklist PASS 6/6, risks R1–R3)".

## 3. Intentional superseded-text trail (correct as designed — no edit)

These prereg §4/§6 sentences contradict dev-D-2…D-4/dev-D-7 **on purpose**: the document
freeze requires original text retention, and §7 deviations are the control mechanism.
Readers checking consistency must read §3/§4/§6 together with §7:

- §4 "approximately 1 km grid or nearest-equal split" → superseded by dev-D-4 (exact
  AOI-snapped 1 km city-block grid).
- §4 "no facility within 750 m of the parcel boundary" → superseded by dev-D-4
  (750 m measured **from the nearest facility point**).
- §6 V1 "counts within ~10%" → superseded by dev-D-7 (category-alignment precondition;
  ≤ 10 percentage points on comparable cohort-year rows only).
- §3-H2 single hypothesis and the scar-exclusion coupling → superseded by dev-D-2
  (H2a/H2b split; scar exclusions confined to the H1 frame).

## 4. Open items (non-blockers; P1 ingest / documentation tasks)

- **OI-1** yaml `boundary_source: geoBoundaries ADM2` — snapshot version unpinned; pin at
  download (recorded dev-D-9(c)).
- **OI-2** yaml `chi_cci_lulc_2005` is a placeholder layer ID; exact 2005 CCI vintage fixed
  at ingest (dev-D-9(c)).
- **OI-3** CRS UTM 43N vs 44N unconfirmed — decided from the district extent at ingest,
  never assumed (dev-D-9(c); Jhabua snap/QA convention).
- **OI-4** Registry temporal coverage: audit-D-1 states "from Dt. 2015 scheme" loosely —
  verify the homestay list's actual start year during P1, because it bounds the facility
  timing cohorts in dev-D-4.
- **OI-5** `verify`-flagged citations: matrix M1 exact reference, lit-A4 journal status,
  lit-B4 venue (Rautela 2015), lit-C1 (= audit-D-10) data-availability statement — P1
  documentation queue; the lit-C1 statement also feeds the dev-D-3 HEC gate.

## 5. Hash state

- Before edits, R2 verified on disk (audit `327263b4…`, matrix `697dc1f5…`, prereg
  `d3e4cde2…`).
- After dev-D-9, hashes changed: recorded as **R3** in `docs/PROJECTSTATE.md` §9
  (audit `aab7ef4d…`, matrix `578a995a…`, prereg `2985fb4e…`). R2 retained there for
  history.

## 6. Remaining blockers for checkpoint-C1 final sign-off

**None at the document-consistency level.** Both review BLOCKERs were resolved at
dev-D-2/dev-D-3; all HIGH/NORMAL items at dev-D-4…D-8; the ID/typo/verdict remnants above
at dev-D-9. What still separates "revisions complete" from "C1 signed" is verification,
not consistency:

1. Reviewer's own final cross-check of this audit + the corrected artifacts (their stated
   position: upload ≠ verification).
2. P1 empirical verifications, each of which must be logged, never silent:
   files on disk + SHA-256 in `data/manifest.json`; audit-D-10 HEC point availability
   (R1 ordered gate); audit-D-1 registry coverage start year; baseline composite QA
   (open GeoTIFFs, not manifests).

P1 baseline-only acquisition is authorized and can begin before sign-off, with the
boundary in prereg §5 unchanged.

## 7. Addendum (2026-10-22, post-P1 first acquisitions)

After this audit was finalized, P1 began (audit §11 log; `data/manifest.json`): the
geoBoundaries snapshot was pinned (OI-1 closed), the boundary was ingested and QA'd at
EPSG:32643 (OI-3 closed), and the Kerala approved-homestay registry (§2 audit-D-1) was
acquired and parsed — 51 Wayanad facilities, 0 duplicate names. The snapshot-semantics
finding (order date = latest renewal of a *currently valid* list) partially closes OI-4
and strengthens the case for dev-D-4's pre-existing-development stratum. The audit's
hash revision moved R3 → R4 in `docs/PROJECTSTATE.md` §9 as a result of that append-only
log; no consistency-audit finding changed.

## 8. Addendum (2026-10-23, checkpoint-C1 final sign-off recorded)

§6's two remaining conditions are now met and logged:

1. **Reviewer final cross-check — performed; final sign-off granted 2026-10-23**
   (explicit: "c1 sign off yes"). Recorded as **prereg dev-D-10**; README phase table
   now reads C1 = SIGNED (P0 deviation range D-2…D-10).
2. **P1 empirical verifications — all logged, none silent:**
   - files + SHA-256 for **17 sources** in `data/manifest.json` (9 baseline/registry raw
     downloads, boundary + registry + geocode derivatives, 5 registry/order documents
     added 2026-10-23);
   - baseline QA gate **PASS — 0 critical, 0 warnings, 62 checks**, files opened
     directly (`outputs/qaqc/baseline_qaqc_report.md`);
   - **audit-D-10 R1 gate executed:** READY at village/aggregate level (open Figshare
     dataset, CC BY 4.0), points **do not exist at source** (no GPS ever recorded) →
     the registered H3 fallback stands; the D-10 row's "*Frontiers* / 2011–2023"
     description is a superseded three-way conflation (actually *GECCO* 62:e03742,
     events 2011–2014) — corrected under append-only in data-audit §11 + matrix
     "Verification results";
   - **audit-D-1 coverage start year:** orders 2024-01-27 → 2026-07-03 (17/17/17),
     file `M5-1903/2015`, 3-year validity; **OI-4 closed at scheme level**
     (GO 299/06 = 2006 origin, GO 324/15 = 2015 revision; order PDF hashed).

**checkpoint-C1 = SIGNED.** P1 is complete for its registered scope; the next decision
is **C2** (P1 data-completeness go/no-go) using `docs/p1_provenance_report.md`.
Hash revision **R4 → R5** for the frozen three (this audit, matrix, prereg) is recorded
in `docs/PROJECTSTATE.md` §9, computed after these edits. Non-blocking items carried
forward (unchanged status, not C1 blockers): matrix A4-numbers/B4-primary/A5/B5 verify
flags, queue item 4 (C1↔C2 independence), audit-D-5…D-8 hazard downloads, and
facility-exact existence verification (precision-capped geocoding logged instead).
