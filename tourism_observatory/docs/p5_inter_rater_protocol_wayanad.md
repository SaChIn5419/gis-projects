# #5 — Wayanad Site 1 inter-rater verification protocol

**Purpose.** Independent re-verification of the facility-existence and hazard-inventory
evidence base by a second coder, so that the Site 1 register rests on two independent
readings rather than a single interpreter's pass.

**Status.** Protocol drafted 2026-11-04. Execution blocked pending a named second coder
(protocol is ready; no data or tooling required to run it).

---

## 0. Scope

Two verification passes:

| Pass | What is re-read | Record |
|---|---|---|
| 5.1 Facility existence | The 107 verified tourism facilities (registry_geocoded_2026-10-23.geojson, 51-feature subset shown) | facility_verification_quotes_2026-11-04.csv |
| 5.2 Hazard inventory | The landslide inventory used in D-15 proxy and H2a (WMS-rendered, no attributes) | hazard_inventory_verification_2026-11-04.csv |

---

## 1. Roles

- **Coder A** (primary, author of the register): provides the source artifact and the quote.
- **Coder B** (second, independent): re-reads the same artifact and must independently locate the
  same record; disagreement is resolved by a third member (or Codex). Coder B must not have
  completed the primary pass before starting.

---

## 2. Pass 1 — Facility-existence verification (5.1)

For each record in `registry_geocoded_2026-10-23.geojson` (and the 7 approved homestays in
`facility_existence_verdicts_2026-10-23.csv`), Coder B must:

1. Open the record's `name_address` (and `image/`/`visual_note` where present).
2. State, in one sentence, whether the facility exists at the geocoded coordinates as of the
   most recent imagery (2026-? snapshot).
3. Quote the exact visual evidence: the `visual_note` text or an image filename.
4. Record: `FileID, GeoRef, Name, Verdict (exists / not exists / unverifiable), Quote, Source`.

**Acceptance criteria.** 100% of records located; ≥90% of existence verdicts agree with Coder A.
Any disagreement is escalated immediately (see §4).

**Internal-consistency QA.** H2b(a) states the 2024 scar (1.781 km²) contained 0 verified facilities
and 0 buildings. Pass 1 must independently confirm this enumeration (0 facilities, 0 buildings,
±15 m jitter sensitivity already stated). Record as a locked fact.

---

## 3. Pass 2 — Hazard-inventory verification (5.2)

The D-15 WMS proxy was a single-pass WMS-rendered inventory (Bhuvan, no attributes/vintage).
Coder B must:

1. Re-render the landslide inventory from the same WMS service used in the primary analysis
   (document the exact service URL and date).
2. Digitize-verify a 10% random subset of the inventory polygons (stratified: severe / high / medium
   / low) against satellite imagery or a second layer.
3. Report: polygon ID, Area (km²), classification, Coder B's verification of visual match (yes/no),
   and any polygon that fails visual verification.
4. Record: `polygon_id, area_km2, class, Coder B verification, failure_note`.

**Acceptance criteria.** ≥90% of sampled polygons visually match the rendered inventory. Any ≥5%
disagreement triggers review of the D-15 proxy label (exposure-to-mapped-stock, not validated hazard).

---

## 4. Disagreement handling

- All disagreements (facility existence, polygon verification) are logged verbatim.
- Escalate to the user within 24 h of the second coder's pass.
- Resolution: majority of (Coder A, Coder B, third reviewer). No register entry may outrank an
  evidence grade (Pass 2 never upgrades R-1/R-3 without a new pre-computation pin).

---

## 5. Deliverables and provenance

- `facility_verification_quotes_2026-11-04.csv`
- `hazard_inventory_verification_2026-11-04.csv`
- Register §4.2, §5, and R-1/R-3 hazard labels updated only after both passes complete.
- No new statistics introduced by this protocol; only re-verification of existing artifacts.

## 6. Second-coder engagement & run log

When a named second coder is available:

1. **Notify** via the project's project-status channel: `carry[ID]/site1/run-2-coder`.
   Do not share Coder A's verdicts before the pass begins.
2. **Run** the pass using §2 and §3; hand back `facility_verification_quotes.csv` and
   `hazard_inventory_verification.csv`.
3. **Log** the run in `docs/protocol_deviations.md` (deviation row `#22-...`) with the run
   timestamp and any disagreements.
4. **Resolve** disagreements per §4; record the resolution (Coder A / Coder B / third
   reviewer) in the same row.

*Run-by:* date ____  coder ____  disagreements ____  resolution ____.
