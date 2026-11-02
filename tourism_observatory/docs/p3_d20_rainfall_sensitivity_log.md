# P3 — D-20 post-hoc rainfall sensitivity log (Wayanad H3 appendix)

**Status: COMPLETED 2026-11-02 under prereg §7 D-20 (freeze R8 =
`da2baee87b9dad57cd1c9d0077242e0cbbf36233d98d842e90d291beba9d98e8`,
hashed BEFORE any rainfall statistic; verified byte-stable after the run).
Everything below is labelled POST-HOC SENSITIVITY and is non-inferential
by the D-20(e) precommitment — H3's registered no-verdict stands unchanged.**

**Label discipline (binding):** these reads answer the user-requested
rainfall question ("Option B") that D-18 recorded as unavailable. They
join the appendix of the H3 block; they are NOT part of the registered
test family, and P4–P5 may quote them only as post-hoc annotations.

---

## §1 Reproduction of the run of record (deterministic)

The sensitivity script imports the H3 module of record and asserts identity
before producing anything: screen kept **2,704** / elephant **2,018**;
geocode cache **425** names (no network — cache complete); placement tiers
place 1,089 / range 1,043 / section 572, **0 unplaced**; grid **8,112
cells** (4,423 outside WDPA). All exact matches to
`p3_h3_facts_2026-11-02.json`.

## §2 Read 1 — seasonality (no new data; D-20(a))

Month of occurrence histogram (2,704 kept records):

| J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 154 | 165 | 156 | 158 | 218 | 285 | **363** | 299 | 184 | 240 | **295** | 187 |

- **SW monsoon (Jun–Sep) share: 0.4183** (elephant subset 0.4351).
- **NE monsoon (Oct–Dec) share: 0.2670** (elephant 0.2488).
- Dry-quarter (Jan–Apr) share ≈ 0.234.

**Reading (descriptive):** incidents occur year-round; the Jul spike
(363) and the Nov secondary peak (295) follow a two-monsoon rhythm
(SW > NE), but there is **no monsoon lock-in** — 23% of incidents fall in
the dry quarter. V2 ("season-dependent" per the paper) carries as:
*mildly season-weighted, not season-gated*. The elephant subset tracks
the all-records pattern (its crop-depredation dominance drives both).

## §3 Read 2 — spatial rainfall covariates (D-20(b))

CHIRPS v2.0 0.05° monthly 2011–2014 (public domain; Funk et al. 2015
attribution), 48 gzipped monthly GeoTIFFs window-read to the bbox
75.70–76.50 E / 11.40–12.02 N (transient downloads in /tmp/opencode; only
the 15×19 px bbox stack and derived layers enter `data/`). Native subset
QC: 48 nodata edge px = one coverage-edge pixel identical across months;
Jul-2014 district-window mean 481 mm; realistic SW-monsoon cycle.
Derived record-window layers (bilinear to the origin-aligned 500 m grid):

- `rain_annual_total_mm_2011_2014`: native range 1,076–3,759 mm;
  district-median 500 m cell mean **2,396 mm** (1,126–3,609) — the
  orographic gradient inside the district is real (~3× top-to-bottom).
- `rain_monsoon_jun_sep_share`: 0.499–0.645 native; 0.54–0.64 on cells.

**Overlap reader (same formulas as the D-18 run of record; three arms):**

| covariate | arm | mean pct @ top-decile | ρ vs incident KDE |
|---|---|---|---|
| rain_annual_total_mm_2011_2014 | all cells | **0.133** | **−0.572** |
| rain_annual_total_mm_2011_2014 | outside-WDPA | 0.209 | −0.234 |
| rain_annual_total_mm_2011_2014 | elephant subset | 0.129 | −0.583 |
| rain_monsoon_jun_sep_share | all cells | 0.330 | −0.151 |
| rain_monsoon_jun_sep_share | outside-WDPA | 0.448 | +0.078 |
| rain_monsoon_jun_sep_share | elephant subset | 0.330 | −0.144 |

**Reading (descriptive, non-inferential):**
(i) the incident hotspot surface lies in the **lower-rainfall parts of
the district**: covariate-top-decile (wettest) cells sit at the 13th incident percentile, and the signed association is
strongly negative (−0.572). This is a *grade of magnitude* bigger than
every pre-2011 covariate in the D-18 run.
(ii) It is **direction-consistent with H3's stable feature**, not a
contradiction of it: the negative-rainfall area IS the human-modified
farming belt (the forest-cover-share association was the one stable
feature of the registered run, −0.178); the rainfall read adds that the
human-influence corridor is specifically the **drier eastern farming
valley**, not the wetter forested west.
(iii) outside-WDPA (where almost all crop depredation lives) attenuates
but preserves sign (−0.234); the monsoon-share covariate is near-null
overall (−0.151 primary, sign-fragile +0.078 outside-WDPA).
(iv) **This read must not be quoted as H3 confirmation or as a rainfall
→ conflict mechanism.** It is a cross-sectional association on a
village-massed register; rainfall here is a 4-year climatology of the
register window, not per-event rainfall (no attribution language is
licensed).

## §4 Governance record

- Prefetch order honored: D-20 written → prereg hashed → **R8 recorded in
  PROJECTSTATE before fetching/computing** → manifest entries for the
  three CHIRPS artifacts (source, licence, sha256) → only then the
  sensitivity run.
- Prereg verified byte-stable at R8 after the run (no post-pin edit).
- IMD 0.25° recorded as fallback; **not triggered** (CHIRPS usable
  end-to-end vsicurl-free direct fetch; ~14.5 MB per monthly gz).
- Files of record: `scripts/p3_fetch_chirps.py`,
  `scripts/p3_h3_rainfall_sensitivity.py`,
  `data/raw/chirps_v2_monthly_2011_2014_wayanad_bbox_4326.tif`
  (sha `58fdd6a5…`), `data/processed/chirps_rain_annual_2011_2014_32643.tif`
  (`5200897d…`), `data/processed/chirps_rain_monsoon_share_2011_2014_32643.tif`
  (`5bfacd9f…`), facts `outputs/qaqc/p3_h3_rainfall_sensitivity_2026-11-02.json`
  (sha `e1ab4cbef5c3697e7cccbd1cdd9dffdbd6573b2d7675bc1afbf2311de95c9e4c`).
- Manifest now **36 entries**.
