# P4 — H4 analysis log (Wayanad tourism_observatory)

**Hypothesis (H3 → H4, §3):** documented grievance/protest event locations
overlap tourism-hazard exposure hotspots **more than expected by area
proportion**. §3 falsification rule: **falsified iff observed overlap ≤ the
area-proportion expectation** (point-estimate rule, unchanged at R7e).

**Status: computed 2026-11-02 under prereg §7 D-19 (freeze R7e, hash
`c4ac960629b01169685dd2149f0f04f323e3ab839ee266a30489208acde01f93`,
re-hashed before any H4 statistic existed). n = 6 cell-eligible disputes
< 15 ⇒ **EXPLORATORY** (D-5): the permutation read-out below is reported as
pinned, but **no significance language is drawn from it** and the wording
throughout is "the spatial distribution of documented records".

**Outcome: NOT falsified — T_obs = 1 vs expectation E = 0.457** (observed
overlap 1/6 exceeds the area-proportion expectation; permutation
p = 0.368, B = 10,000). Exploratory; interpreted as the spatial
distribution of documented records only, with the mandatory
documentation-bias caveat.

---

## §1 Event table (D-5; pinned in D-19 before computation)

8 disputes / 12 records compiled from open web sources →
`data/processed/h4_event_table_2026-11-02.csv` (sha
`c452c653b2077a52610e822ea67c7445da6b75c98940ed2ce259b03229aa608a`,
recorded **inside the D-19 pin before computing**; manifest id
`h4_event_table_2026-11-02`). Record fields per §4 D-5: dispute ID · record
type · dates · location label + precision class · source URL · corroboration.

| dispute | records / type | where / precision | cell-test status |
|---|---|---|---|
| D-001 Muthanga AGMS land-rights agitation | occupation + 19 Feb 2003 police firing + litigation (protest/legal) | Muthanga (locality); Tvm march record excluded as out-of-AOI | **eligible** (3 records, one anchor) |
| D-002 Wayanad WLS relocation dispute (Kattunaikar/Mullu Kurumba) | grievance, 2002→ongoing (LCW, 2,612 HH) | Valavayal (locality) | **eligible** |
| D-003 Chooralmala–Mundakkai rehabilitation-delay protests | protest, 23 Feb 2025→ongoing | Chooralmala (locality) | **eligible** |
| D-004 Valathoor quarry protest | protest, 13 Sep 2024 | Valathoor (locality) | **eligible** |
| D-005 Vengappally quarry-encroachment grievance | grievance, 28 Aug 2025 | Vengappally (locality) | **eligible** |
| D-006 Jenu Kuruba Nagarahole reoccupation | protest, 5 May 2025 | Karadi Kallu, Kodagu KA (locality) | **excluded — out of AOI** (tabled because §4 named it; no Wayanad-specific Jenu Kuruba 2025 event exists — verified) |
| D-007 KSHRC illegal-quarrying directive | official report, 17 Jan 2025 | district-wide (district) | **excluded — district precision (§4 D-5)** |
| D-008 Kanjirathinal family land-recovery struggle | sit-in (protest) + 2023 KSHRC directive (legal; district → excluded at record level) | Kalpetta (locality) | **eligible** (anchor = protest site) |

Dedup decisions (D-5): D-002 kept separate from D-001 (relocation-from-
sanctuary vs Muthanga land-distribution — distinct campaigns, overlapping
parties); D-003 vs D-004 distinct (ongoing rehabilitation protest series vs
one site-level quarry protest); D-007/D-008-R2 record-level facts retained
for register breadth only.

## §2 D-19 pin sequence (governance)

R7d (`943e9f9c…`) verified byte-stable before editing → D-19 appended (§7,
append-only; §3/§4 byte-unchanged) → **R7e = full-file re-hash
`c4ac9606…` recorded in PROJECTSTATE before the script was created** — the
hash was re-verified after the run: unchanged (no post-pin text change).

## §3 Geocoding

Nominatim (D-18 recipe: viewbox 75.70,11.40,76.50,12.02, suffix
", Wayanad, Kerala, India", 1 req/s), deterministic query rule pinned in
D-19(b). Cache `data/processed/h4_event_geocodes_2026-11-02.csv` (path
pinned verbatim; sha `4b68abc4…`; manifest `h4_event_geocodes_2026-11-02`).
All 6 anchors matched: Muthanga (11.6715, 76.3619), Valavayal (11.7084,
76.1878), Chooralmala (11.4992, 76.1599), Valathoor (11.5174, 76.1874),
Vengappally (11.6108, 76.0458), Kalpetta (11.6103, 76.0828). Every
cell-eligible dispute unrolled to **one distinct geocode**, so the
D-19(f) "centroid of record footprints" convention is exercised at
single-point strength (no multi-point centroid ambiguity).

## §4 Hotspot + reportable area (as pinned)

- **Tourism footprint:** 107 verified facilities → 500 m buffer union =
  **63.24 km²**.
- **Hazard footprint:** 1 km buffers around the D-15 inventory-proxy
  polygons (992.90 km²) ∪ 2024 scar (1.781 km²) = 993.21 km².
- **Hotspot = tourism ∩ hazard = 15.0578 km² = 0.74% of the district**.
- **Reportable area (D-5):** 3,761 grid cells containing ≥1 OSM building
  footprint (69,126-footprint 2026-10 extract) = **940.25 km²** as
  cell-union (668.49 km² of it inside the district — the cell-union rule
  is what D-19 pinned and what the permutation samples).

## §5 Test result (D-19(f)/(g))

Per-dispute read (anchor → nearest hotspot distance, disclosure):

| dispute | distance to hotspot (m) | overlaps (r = 1,000 m) | E_i |
|---|---|---|---|
| D-001 Muthanga | 24,605 | no | 0.0762 |
| D-002 Valavayal | 10,923 | no | 0.0762 |
| D-003 Chooralmala | **1,093.9** | **no — by 94 m beyond its precision radius** | 0.0762 |
| D-004 Valathoor | **24.0** | **yes** | 0.0762 |
| D-005 Vengappally | 3,245 | no | 0.0762 |
| D-008 Kalpetta | **1,142.6** | no — by 143 m | 0.0762 |

- **T_obs = 1 of 6 disputes overlap** (D-004, the Valathoor quarry protest
  next to the 2024 landslide corridor).
- **Deterministic area-proportion expectation E = 6 × 0.0762 = 0.4572**
  (each dispute's 1 km precision footprint overlap probability against the
  reportable area).
- **§3 rule: T_obs = 1 > E = 0.457 ⇒ NOT falsified** (point-estimate rule).
- **Permutation null (pinned):** B = 10,000, seed 20261102, locations
  uniform over the reportable-area union with each dispute's own radius →
  #{T_j ≥ 1} = 3,684 → **p = (1 + 3,684)/10,001 = 0.3685**. Under D-5 this
  is a pinned read-out, not an inference: with n = 6 the test is
  **EXPLORATORY** and no significance claim is made either way.
- Overlap arithmetic equivalent form used: dispute overlaps iff anchor ∈
  dilate(hotspot, precision radius) — mathematically identical to the
  pinned footprint-intersection definition.

**Reading (descriptive, D-5 wording):** the one dispute that falls inside
the exposure hotspot zone is the quarry protest immediately adjacent to the
2024 landslide corridor (Valathoor, 24 m off the hotspot boundary). The
rehabilitation-delay protest at Chooralmala — the dispute one would most
expect "inside" the exposure zone — sits 94 m beyond its village-scale
precision footprint from the nearest exposure-zone point; the landscape
feature the register actually witnesses is *hazard-adjacent land friction*
(both quarry disputes + the landslide-corridor context), not
"facility-tourism" conflict per se. This is the spatial distribution of
documented records, not an exposure estimate.

## §6 Governance / compute record (full disclosure)

1. **Run A** (correct anchors mathematically; anchor lat/lon *columns*
   accidentally written in projected metres) crashed at a print statement
   before any facts file existed; the dispute-table CSV of that run was
   superseded.
2. **Run B** (bugged): my lat/lon "fix" operated on an already-projected
   coordinate, re-projecting projected metres as if geographic —
   anchors corrupted to invalid points; it wrote an all-False facts JSON
   (`T_obs=0`) **that was then superseded**. No decision was taken on
   run-B text; the arithmetic was visibly absurd (northing as latitude).
3. **Run C (run of record):** centroid computed geographically, projected
   once; anchors match Nominatim display results; D-19's recipe text never
   changed between A/B/C — the pin's anchor rule is exercised identically
   (single-point anchors), so no re-hash was required; run A's overlap
   pattern (T_obs = 1) and run C agree, and run B's corruption is disclosed
   here. Run-of-record shas below.
4. EXPLORATORY flag (n = 6 < 15): as pinned; D-5's no-significance-language
   rule is respected — the p value is reported because D-19 pinned its
   formula, not because it carries an inferential decision.

## §7 Caveats (mandatory, carried to the evidence brief)

- **Documentation/effort bias (mandatory):** the register comes from press
  and Land Conflict Watch; reporting likelihood rises with media attention
  and near-landslide salience — both records nearest the exposure zone
  (D-004, D-003) are within 3 km of the 2024 catastrophe scene, which
  itself drives national coverage. The register is not an exposure sample.
- n = 6 < 15 ⇒ EXPLORATORY (D-5); no significance language.
- Village-scale anchors + 1 km precision radius are interpretations, as
  pinned in D-19(e); the D-003/D-008 outcomes sit <150 m from the decision
  boundary, so their "no-overlap" status is fragile to precision radius —
  reported above, not quietly smoothed away.
- Reportable area = current OSM building snapshot (2026-10-28; vintage-
  caveated), not a population-weighted null; the D-5 cell-union rule gives
  the permutation domain 940 km² including 272 km² outside the district
  polygon — as pinned, disclosed here.
- The exposure-hotspot definition is a register-time construct (verified
  facility universe, 2026 snapshot; hazard footprints from the D-15
  inventory proxy + mapped 2024 scar), not per-dispute-era exposure.
- Dispute dates range 2001–2026; the frozen hazards footprints used are the
  same for all records (no era adjustment); part of the hotspot shape
  reflects where *facilities* are, and H2's documentation-bias caveats on
  the facility universe apply equally here.

## §8 Files of record

| artifact | sha256 |
|---|---|
| prereg (pin, freeze R7e) | `c4ac960629b01169685dd2149f0f04f323e3ab839ee266a30489208acde01f93` |
| scripts/p4_h4_analysis.py | `53a7b57cf18a710f7d863cccbe3dd62dd5a246a1b16728e69e9dc7e37ec2ee2e` |
| data/processed/h4_event_table_2026-11-02.csv | `c452c653b2077a52610e822ea67c7445da6b75c98940ed2ce259b03229aa608a` (pinned in D-19) |
| data/processed/h4_event_geocodes_2026-11-02.csv | `4b68abc49beeca8c9577e7e017fce22f2ab457b4ba25e244d5a3b84cc39aa607` |
| outputs/qaqc/p4_h4_facts_2026-11-02.json | `d945c4a6339843ba251e515373ea1bd117573c9533fe0ad7ca3baab30cca7a37` |
| outputs/qaqc/p4_h4_dispute_table_2026-11-02.csv | `7a1996cd529e0665997adf8bbf255306f449cd59d9e0ba5d719d756178bd66f5` |
