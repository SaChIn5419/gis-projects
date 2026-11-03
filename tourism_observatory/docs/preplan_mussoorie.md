# Preplan — Mussoorie (Site 2, Uttarakhand)

**Status: PREPLAN. Nothing here is frozen. No hypothesis is registered yet and
no outcome layer has been opened.** This document exists to decide *what* Site 2
can measure before the Wayanad machinery is pointed at it. It is deliberately
evidence-first: the three scoping findings in §2 change the design, and pretending
otherwise would transplant a rule that does not fit.

Program scope is unchanged (user, 2026-10-22): exactly two sites, Wayanad then
Mussoorie; no third case, no foreign benchmark. Wayanad remains the method
anchor and stays at **prereg R9**; nothing in this file touches it.

---

## 1. Site definition (computed 2026-11-03, before any outcome work)

Script: `scripts/p8_site2_scoping.py`. Facts of record:
`outputs/qaqc/p8_site2_scoping_facts_2026-11-03.json` (**`c36a7c51`**).
Processed frame: `data/processed/dehradun_boundary_32644.geojson` (**`3f3a72ab`**).

These are **site-definition facts only** — where the site is, what land is under
which protection class, how much land is left. No arm comparison, no change
measurement, no test.

| item | value |
|---|---|
| frame | Dehradun district, geoBoundaries ADM2 (`shapeID 76128533B67005208112053`) |
| area (simplified boundary) | **3,095.742 km²** |
| extent | 77.5759–78.3133 E, 29.9597–30.9908 N |
| CRS | **EPSG:32644** (UTM 44N) |
| anchor | Mussoorie town centre 78.0740 E, 30.4598 N |
| WDPA Oct-2026 features intersecting | 198 |
| — Reserve Forest | 1,246.15 km² |
| — Doon Valley Ecologically Sensitive Area | 1,779.35 km² |
| — Reserve Forest ∩ ESA (overlap, not additive) | 830.59 km² |
| — **WDPA union inside district** | **2,194.93 km² (70.9 %)** |
| — WDPA-free land in district | 900.81 km² |
| — IUCN I–IV / National Park / Wildlife Sanctuary | **none** |
| — Ramsar | Asan, 4.00 km² (valley) |

Rings around the anchor, clipped to the district:

| ring | zone km² | WDPA % | WDPA-free km² |
|---|---|---|---|
| 5 km | 51.50 | 71.1 | 14.89 |
| **8 km** | **115.91** | **83.7** | **18.93** |
| 10 km | 171.67 | 88.4 | 19.92 |

## 2. What the scoping findings break

Three findings matter; each one invalidates a Wayanad default if carried over
unexamined.

**(F1) The district straddles the UTM zone edge.** 40.0 % of Dehradun lies east
of 78° E, and Mussoorie sits at 78.074° E. Wayanad's "zone from the district
extent" rule would have chosen zone 43 and put the AOI 3.07° off-centre. The zone
must therefore follow the **AOI anchor**, not the district centroid.

**(F2) The Wayanad protection rule excludes 71 % of the district and 84 % of the
AOI.** In Wayanad, WDPA = a handful of protected-area complexes. In Uttarakhand,
WDPA carries *Reserve Forest* administrative polygons and the *Doon Valley ESA*
— the very land the hill station sits inside. Excluding "all WDPA, both arms"
would leave **18.93 km²** of eligible land in the 8 km ring: no control universe,
no design. It also leaves the district's only strict protection (Asan Ramsar,
4 km²) far away in the valley.

**(F3) The non-WDPA land around Mussoorie is essentially the town footprint.**
WDPA-free area is 14.9 km² at 5 km, 18.9 km² at 8 km, 19.9 km² at 10 km — it
saturates. Widening the ring does not buy controls; it buys more forest. A
Wayanad-style "parcel with facility vs matched parcel without" design has almost
no candidate controls unless forest land is admitted into the domain.

## 3. Decisions proposed for the Site 2 preregistration

Each is a proposal, not a registration. The intent is that the user signs or
amends them at the C-M1 gate (the Site 2 equivalent of Wayanad's C1).

**M-1 — AOI.** Primary AOI = 8 km ring around the pinned anchor, clipped to
Dehradun district (115.91 km²); sensitivity 5 km and 10 km. *Rationale:* the 8 km
ring contains the whole tourist belt plus its forest edge, and the ring radii
mirror the H1 500 m/250 m/1,000 m sensitivity pattern. *Cost:* the anchor
coordinate is a judgement call and must be stated as such.

**M-2 — Eligibility rule (replaces Wayanad's "exclude all WDPA").** Exclude only
*strict* protection: IUCN I–IV, National Park, Wildlife Sanctuary, Ramsar. Keep
Reserve Forest and the ESA **inside** the domain, recorded as tenure strata, with
a pre-registered robustness run restricted to WDPA-free land. *Rationale:* in
Uttarakhand the RF layer is an administrative forest boundary, not a construction
prohibition perimeter — hill hotels sit on private enclaves inside and beside it;
and excluding it leaves 18.9 km². The robustness run keeps the exclusion rule
visible instead of hiding it. *Falsifiability:* if the WDPA-free-only estimate
reverses sign, the finding is tenure-dependent and must be reported as such.

**M-3 — Unit and estimand.** 500 m parcels on the AOI grid (≈ 464 cells at
8 km), **not** Wayanad's 1 km parcels (116 cells — too few for matching plus
strata). Primary estimand stays the H1 quantity: built-up conversion 2000→2020
inside facility parcels vs matched non-facility parcels. *Open:* if F3 binds
(too few facility-free parcels adjacent to treated ones), the estimand degrades
to a facility-density contrast (see M-7).

**M-4 — Treatment.** A parcel is treated if it contains a tourism accommodation
verified against imagery; controls are parcels with no facility, matched on
terrain (elevation band, slope), distance-to-town, distance-to-road and tenure
stratum. Same existence-verification discipline as Wayanad (no imagery-based
construction dating pre-freeze).

**M-5 — Outcome window.** Built-up 2000 → 2020 (GLAD GLCLUC2020), forest
2000 → 2024 and loss bands by `lossyear` code (Hansen GFC-2024), WorldCover 2021
as an un-averaged cross-check. Identical definitions to Wayanad D-13/D-21 so the
two sites are comparable; stated as a comparability choice, not a claim that the
processes are the same.

**M-6 — Rainfall.** **CHIRPS v2.0**, same pipeline as D-20. *Rationale:*
comparability with Site 1's post-hoc rainfall test; IMD 0.25° would resolve the
Uttarakhand gradient better but would break cross-site comparability and is
gated behind a different licence/registration path. Recorded as a trade-off.

**M-7 — Pre-registered downgrade.** If the C-M1 feasibility gates (§6) fail, Site
2 pre-registers a *descriptive density design* instead of a matched-pair test:
conversion share as a function of facility density at 500 m, with terrain strata,
reported as association only (no counterfactual language). Deciding this before
seeing the data is the point.

## 4. Source plan

Statuses are honest: `local` = present and hashed in this repo; `to fetch` =
endpoint identified, not yet pulled; `unverified` = must be checked before it can
carry a hypothesis.

| need | source | status |
|---|---|---|
| AOI frame | geoBoundaries ADM2 (local snapshot) | **local**, hashed |
| protection | WDPA Oct-2026 India (local zip) | **local**, hashed |
| elevation / slope | Copernicus DEM 30 m, N30 E077–E078 | to fetch (Wayanad tiles are 11N) |
| built-up 2000/2020 | GLAD GLCLUC2020 tiles 30N 075E/080E | to fetch |
| forest 2000 + loss | Hansen GFC-2024 30N 075E/080E | to fetch |
| built-up cross-check | ESA WorldCover 2021 30N 075E/080E | to fetch |
| **tourism registry** | Uttarakhand Tourism Development Board approved
| accommodation / homestay lists | **unverified** — the single biggest risk |
| landslide inventory | GSI / Bhuvan Uttarakhand inventory, or the ISRO Atlas layer used in Wayanad | **unverified** — must be a dated, attributable product |
| roads | OSM (current-network proxy, same caveat as Wayanad dev-D-4) | to fetch |
| buildings | Google Open Buildings v3 (imagery ≤ 2023-05) | to fetch |
| rainfall | CHIRPS v2.0 monthly, AOI bbox | to fetch |

Registry risk is explicit: Wayanad's whole treatment arm came from a public
Kerala Tourism list with approval numbers. If Uttarakhand publishes no comparable
list, the treatment definition changes (OSM/places-based enumeration with a
documented, weaker existence standard) and the report must say so up front.

### 4.1 Endpoint verification (2026-11-03)

Tested with HTTP range requests (`bytes=0-1023`), not assumed from filename
conventions — two conventions differ from Wayanad's:

| product | file tested | result |
|---|---|---|
| Copernicus DEM 30 m, N30 E077 | `…_N30_00_E077_00_DEM.tif` | **206** |
| Copernicus DEM 30 m, N30 E078 | `…_N30_00_E078_00_DEM.tif` | **206** |
| GLAD built-up change, tile 30N 070E | `Change_30N_070E.tif` | **206** |
| Hansen treecover2000, tile 30N 070E | `Hansen_GFC-2024-v1.12_treecover2000_30N_070E.tif` | **206** |
| Hansen lossyear, tile 30N 070E | `Hansen_GFC-2024-v1.12_lossyear_30N_070E.tif` | **206** |
| WorldCover 2021, N30 E075 / N30 E078 | `…_N30E075_Map.tif`, `…_N30E078_Map.tif` | **206** |
| Uttarakhand Tourism portal | `https://uttarakhandtourism.gov.in` | **200** (JS app; no sitemap.xml; no approved-accommodation endpoint discoverable from this environment) |

Two naming corrections that will bite the ingest script if copied from Wayanad:

- **GLAD files are `Change_<tile>.tif`** on the mirror, not the
  `GLCLUC2020_Builtup_change_2000_2020_<tile>.tif` name printed in
  `p3_outcome_ingest.py`'s error message (that script only *reads* staged files,
  so the wrong hint never failed in Wayanad — it would mislead a Site 2 run).
- **Tile geometry differs by product**: Hansen is 10°×10° (one tile, `30N_070E`,
  covers 70–80 E), WorldCover is 3°×3° (needs `N30E075` **and** `N30E078` — the
  district straddles 78 E, same edge as the UTM zone problem), DEM is 1°×1°
  (`N30 E077` + `N30 E078`).

The registry remains the open item: the portal is reachable but the approved
list is not exposed as a document or API that this environment can see.

### 4.2 R-M1 pin — registry reconnaissance (recorded before execution)

**Pinned 2026-11-03, before any count was computed.** This pin fixes the recipe
that makes G-M1 decidable. It authorises enumeration only: no change measurement,
no arm comparison, no tourism-impact statistic.

**Why this and not the state portal.** The registration portal
(`homestay.uttarakhandtourism.gov.in`) is a *registration* system: every listing
route returns `Frontend/Notfound` and the only public data surface it exposes is
the booking platform it links to. The published inventory therefore lives on
**`uttarastays.com`** ("An Initiative taken by Uttarakhand Tourism Development
Board"), whose public property list carries name, full postal address
(`City - X, District - Y, PIN, Uttarakhand`) and nightly rate, with infinite
scroll instead of pagination. Its API (`api.uttarastays.com/customerui/v1/…`)
encrypts payloads client-side; the encrypted route is **not** used — only the
rendered public page.

**Sources, in order, all attempted regardless of earlier success:**

| # | source | what is counted | provenance |
|---|---|---|---|
| S1 | `uttarastays.com/property-list` rendered listing | listings whose address locality is inside the AOI | UTDB booking initiative |
| S2 | OSM Overpass, `tourism=hotel\|guest_house\|apartment\|resort\|chalet` in the AOI bbox | facilities with coordinates inside the AOI polygon | ODbL |
| S3 | Ministry of Tourism approved hotels/restaurants | inspected; recorded as available/unavailable | GoI |

**Counting rules (fixed here, not after seeing numbers):**

1. AOI = 8 km ring ∩ Dehradun district (`M-1` primary zone), EPSG:32644.
2. A listing counts as *inside* if its stated locality is one of the AOI
   localities — Mussoorie, Landour, Kempty, Barlowganj, Jharipani, Dhanolti
   (parsed from the address line). This is **label membership, not a geocode**;
   the limitation is recorded rather than hidden.
3. Duplicates are removed within a source by normalised `(name, address)`.
   Cross-source duplicates are **reported, not merged**: the gate counts
   per-source and union separately, because a homestay on a booking platform and
   an OSM node may be the same building.
4. Counts are reported with the district baseline (all Uttarakhand listings) so
   the AOI share is visible.
5. No approval status, approval date or star rating is inferred from presence in
   any list. Where a source does not publish dates, "no date" is the recorded
   value — it is not imputed.

**What this pin deliberately does not do:** it does not decide the treatment
definition. It produces the counts that C-M1 uses to choose between the
status-based and presence-based options, and the yield that G-M1 tests (≥ 40
verified facilities in the AOI).

**Outputs:** `scripts/p8_registry_recon.py` →
`outputs/qaqc/p8_registry_recon_facts_2026-11-03.json`, plus a source memo at
`docs/p8_registry_recon_memo.md`. Any raw listing file kept goes to `data/raw/`
with a manifest entry.

### 4.3 R-M1 result (executed 2026-11-03)

Facts `d6bc656b`; listings CSV `ae8f238f` (manifest `registry_uttarastays_2026-11-03`);
memo `docs/p8_registry_recon_memo.md`.

| source | state-wide | Dehradun | **inside 8 km AOI** |
|---|---|---|---|
| S1 uttarastays (crawl complete: 1,034/1,034) | 1,034 | 66 | **7** |
| S2 OSM commercial (excl. 9 institutional hostels) | — | — | **32** (40 deduped incl. hostels) |
| S3 Ministry of Tourism | unavailable (JS shell, CMS search empty) | — | — |

**G-M1 (≥ 40) fails on every source.** Mussoorie plainly holds more than 32
accommodations, so this is *coverage failure, not town size*: S1 is a homestay
platform (not hotels), S2 is volunteer mapping. Two consequences stand:

1. **No approval dates exist in any accessible Uttarakhand source.** Wayanad's
   timing proxy cannot be reproduced here; timing would have to come from
   imagery first-appearance, which the Wayanad design banned pre-freeze. That is
   a prereg-level decision.
2. **Cross-source name overlap is 0** while `Natures Lap Homestay` (S1) and
   `Hotel Nature's Lap` (OSM) are visibly the same business, so name matching
   under-resolves duplicates and the union count (46) overstates distinct
   facilities.

C-M1 therefore chooses between: **(A)** presence-based treatment on the 32–39
enumerable facilities with declared coverage bias, **(B)** a bounded census of
the AOI from imagery + Open Buildings, restoring a near-census without dates, or
**(C)** descriptive-only Site 2. Recommendation in the memo: B if a Site 2 test
is wanted, C if not; A is weakest because "not mapped" is silently read as "not
there".


## 5. What carries over unchanged from Wayanad

- The four hypothesis *shapes*: conversion (H1), hazard-overlap of placement
  (H2a density + H2b assets), exposure/hotspot association (H3), and event
  precision (H4) — subject to the M-2/M-3 amendments.
- The discipline: pin-before-compute, append-only deviation log, one hash ledger,
  facts-of-record JSON per block, "no verdict" as a legitimate outcome, observed /
  modelled / assumed kept separate, hazard vs HEC vs community events never
  composited.
- The rendering conventions (short labels, legends outside the frame, display
  rasters separate from analysis rasters).
- The claim discipline: H4 exploratory at small n; any post-hoc sensitivity
  labelled non-inferential.

## 6. Feasibility gates (checked at C-M1, before freeze)

| gate | test | if it fails |
|---|---|---|
| G-M1 | ≥ 40 verified facilities inside the 8 km AOI | widen to 10 km once (pre-registered), else re-scope to the town + forest-edge belt |
| G-M2 | ≥ 25 usable matched pairs with max \|SMD\| < 0.10 | apply M-7 descriptive density design |
| G-M3 | hazard inventory covers ≥ 80 % of the AOI with a dated source | H2 becomes descriptive overlap only |
| G-M4 | built-up classes resolve at 30 m across 2000 and 2020 in this terrain | fall back to Hansen-based indicator, flagged as robustness only |

## 7. What must not happen yet

No hypothesis test, no arm comparison, no conversion percentage, no facility
count quoted as a result, no map showing change. Section 1's numbers are site
description, and even those must not migrate into a claim about tourism impact.

## 8. Sign-off items (C-M1)

1. **M-1** anchor 78.0740 E, 30.4598 N and the 8 km primary ring.
2. **M-2** narrow exclusion rule (strict PA only) + WDPA-free robustness run.
3. **M-3** 500 m parcels (departure from Wayanad's 1 km).
4. **M-6** CHIRPS over IMD, for cross-site comparability.
5. Registry fallback policy if no official Uttarakhand list exists.
