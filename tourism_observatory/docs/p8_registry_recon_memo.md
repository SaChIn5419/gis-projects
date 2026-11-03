# P8 / R-M1 — Registry reconnaissance source memo (Mussoorie)

**Status: reconnaissance complete, non-inferential.** Recipe pinned in
`docs/preplan_mussoorie.md` §4.2 before execution. Facts of record:
`outputs/qaqc/p8_registry_recon_facts_2026-11-03.json` (**`d6bc656b`**).
Listing table: `data/processed/registry_uttarastays_all_2026-11-03.csv`
(**`ae8f238f`**, 1,034 rows, manifest `registry_uttarastays_2026-11-03`).

No tourism impact is measured here. These are counts of candidate facilities, and
they exist to make gate **G-M1** decidable.

---

## 1. What each source actually is

### S1 — `uttarastays.com` (UTDB booking initiative)

The state homestay **portal** (`homestay.uttarakhandtourism.gov.in`) is a
registration system, not a register: every listing route returns
`Frontend/Notfound`, and the only public inventory it exposes is the booking
platform it links to. The API host (`api.uttarastays.com/customerui/v1/…`)
returns **client-side-encrypted payloads**, so it was not used; the rendered
public page was read instead.

| measure | value |
|---|---|
| listings, state-wide | **1,034** |
| in Dehradun district | 66 |
| inside the 8 km AOI | **7** (0.68 % of state listings) |
| approval dates published | **no** |
| crawl completeness | stated total 1,034 = parsed 1,034 (verified) |

AOI listings: Forest Inn, Ghais Sunrise, Hill Top, Kavi, Kotli The Paradise,
Natures Lap, Sukoon — all Homestays, all Mussoorie locality.

**What it can support:** existence of a listing, name, address, room rate.
**What it cannot:** hotels (it is a homestay/B&B platform), approval dates, a
census of the town's accommodation stock.

### S2 — OpenStreetMap, `tourism=hotel|guest_house|apartment|resort|chalet|hostel`

ODbL 1.0. Overpass was at capacity (HTTP 502) for part of the session and
required exponential backoff; the final successful query returned 42 elements in
the AOI bbox, all inside the clipped ring.

| class | count |
|---|---|
| hotel | 24 |
| guest_house | 7 |
| chalet | 2 |
| hostel | 9 |
| **deduplicated total** | **40** (2 duplicate node/way pairs removed) |
| **commercial (excl. hostel)** | **32** |

The `hostel` class is contaminated: 9 of 40 are institutional — `DIT boys
Hostel`, `IMS boys hostel`, `Ganga Hostel`, `Girls Hostel`, `Kaveri`, `Narmada`,
`Mahanadi`, plus `Bunkotel`. Mussoorie's boarding-school economy makes
`tourism=hostel` a poor proxy for visitor accommodation, so those 9 are excluded
from the commercial count and reported separately rather than silently dropped.

**What it can support:** coordinates, names, rough class, a presence flag.
**What it cannot:** approval/registration status, dates, coverage certainty.

### S3 — Ministry of Tourism approved hotels

`tourism.gov.in/approved-hotels-and-restaurants` and `/approved-hotels` both
render a generic shell (≈670 characters, no state filter, no Uttarakhand
content) and the CMS WordPress search returns nothing for "approved". Recorded
as **unavailable** from this environment, not as "no approved hotels exist".

## 2. The finding that matters

**G-M1 fails on every source.** Threshold was ≥ 40 confirmed facilities in the
AOI; S1 yields 7, S2 yields 32 commercial (40 including hostels).

That number is not credible as a description of Mussoorie, which plainly hosts
far more accommodation than 32 businesses. The correct reading is therefore
**coverage failure, not town size**:

- S1 covers one product class (homestays) and only those that sell through the
  state-linked platform.
- S2 covers what volunteers have mapped; Indian hill-station hotel coverage is
  known to be partial.

Consequence for the design: neither source is a census, so a parcel-level
"treated vs matched control" H1 built on them measures **the subset that is
enumerable**, not tourism expansion as such. Whether that bias runs upward
(marketed, larger, more formal properties — plausibly more construction) or
downward is not knowable from these data, which is precisely why it must be
declared before, not after, estimation.

## 3. Additional observations

- **Cross-source name overlap is 0**, yet `Natures Lap Homestay` (S1) and
  `Hotel Nature's Lap` (OSM) are almost certainly one business. Name-only
  matching under-resolves duplicates, so any union count (46) overstates
  distinct facilities.
- **No approval dates anywhere.** Wayanad's treatment timing came from approval
  numbers in the Kerala list. Mussoorie has no equivalent, so any timing signal
  would have to come from imagery first-appearance — which Wayanad's design
  explicitly banned pre-freeze. This is a prereg-level change, not a config edit.
- **Localities were corrected during the run.** Kanatal (~24 km) and Dhanolti
  (~16 km) were initially admitted as AOI localities and removed after a
  distance check; membership is by stated locality label, not by geocode.

## 4. Options for C-M1

| option | treatment definition | cost | what it buys / costs |
|---|---|---|---|
| **A. Presence-based** | S2 commercial ∪ S1 listings, existence-verified | low (done) | 32–39 facilities, no dates; coverage bias is explicit but unquantified; H1 becomes "expansion near *mapped/listed* accommodation" |
| **B. Bounded census** | digitise all accommodation in the AOI from imagery + Google Open Buildings, classify visually | moderate–high (town core ≈ 5 km², AOI 116 km²) | restores a near-census with existence verification and no approval-date need; makes H1 defensible as "conversion near accommodation" |
| **C. Descriptive only** | no treatment arm; report facility density vs forest-edge change | low | keeps Site 2 as a descriptive extension of D-21; no H1 for Site 2 |

**Recommendation:** B if a Site 2 hypothesis test is wanted, C if not. Option A is
the weakest of the three because it silently equates "not mapped" with "not
there", and the direction of that error is unknown.

## 5. What this memo does not do

It does not choose the option, does not touch the Wayanad preregistration (R9
stands), and does not convert any of these counts into a tourism-impact claim.
