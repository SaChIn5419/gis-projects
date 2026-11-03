# P7 — Literature review and gap analysis: what Wayanad Site 1 adds

**Status:** task artifact for the P7 research report.
**Task:** literature-gap analysis + 2000-vs-now comparison + paper-style report.
**Design state:** prereg `da2baee8…` (R8) → **R9 `bcaa9223…`** (D-21 pin,
descriptive 2000-vs-now accounting, §7 append-only; §3/§4 byte-unchanged).
**Date of searches:** 2026-11-03.
**Evidence level of this document:** titles **and** abstracts were retrieved
via the OpenAlex API (13 query sets, ~100 records screened); full texts were
**not** opened for most entries. Claims about individual papers below are
therefore abstract-level. Where a paper's finding matters to our
positioning, the abstract was read in full and is quoted or paraphrased
conservatively. Nothing here is a substitute for reading the PDFs.

---

## §1 Search protocol (reproducible)

- **Interface:** OpenAlex REST (`api.openalex.org/works?search=…`,
  `sort=relevance_score:desc`, 8 records per query, `mailto` set). Crossref
  and Semantic Scholar were not needed after OpenAlex coverage proved
  adequate. Web-search UI was unavailable in this environment (HTTP 402);
  API access was stable except intermittent 429/504 (retried with delays).
- **Query sets (13):** tourism landslide risk Western Ghats; tourism
  development land use change protected area India; Wayanad land use land
  cover change Kerala; human–elephant conflict Western Ghats Kerala;
  built-up area expansion change detection Landsat India; landslide
  inventory completeness bias mapping; tourism road development Himalayan
  landslides; global built-up change GLAD Landsat 2000–2020; Wayanad
  landslide 2024 Mundakkai Chooralmala; human–elephant conflict Wayanad;
  tourism growth Kerala Western Ghats environmental pressure; landslide
  early warning Western Ghats Kerala; tourism infrastructure exposure
  natural hazard mountains.
- **Screening logic:** keep peer-reviewed work with a spatial/land-use or
  hazard-exposure design; keep official-product papers for the data
  section; keep preprints only where flagged and never as established
  evidence. Grey literature and news were not used for evidence claims.

---

## §2 What the literature already establishes

### 2.1 Tourism development converts land — including in and around protected areas

- **Karanth & DeFries (2010)** interviewed facilities around 10 Indian
  protected areas: average visitation growth **14.9 % yr⁻¹ (2002–2008)**,
  **72 % of facilities built after 2000**, and **85 % within 5 km of a PA
  boundary**. Employment contributions were marginal. This is the closest
  Indian precedent for our facility universe — and it is 15 years old.
- **Bailey et al. (2015)** measured land-cover change within and around
  protected areas of a biodiversity hotspot: agriculture expanded and
  **settlements increased around every protected area**, with urban
  expansion up to 10 %.
- **Pandya et al. (2022)** documented tourism-driven land-use change at
  Corbett Tiger Reserve: land purchases by outsiders, then villagers
  converting agricultural land to tourism enterprises — i.e. conversion is
  **parcel-level and locally driven**, not only "resort construction".
- Scenario and trajectory studies (Algarve, southern Portugal, coastal
  India) converge: tourism is a primary LUCC driver, but attribution is
  usually **scenario-based or correlational at district/regional scale**.

### 2.2 Wayanad's land cover has already been mapped and modelled

- **Saha et al. (2022)** reconstruct Wayanad's forest→agriculture/plantation
  conversion from 1950–2018 and link it to human–animal conflict and
  emerging infectious disease.
- **Bijosh & Abraham (2024)** classify Wayanad Landsat imagery at three
  epochs over 23 years into nine classes (max-likelihood): coffee-dominated
  mixed crop increased (+0.84 % by 2014, +11.84 % by 2022 vs 1999) and
  deciduous forest declined.
- **Manawat & Yadav (2025)** apply MOLUSCE/CA-ANN to model Wayanad LULC
  dynamics and project change.

**Consequence:** "Wayanad lacks land-cover change evidence" is **false**.
Any paper claiming that is not credible. What is missing is not the map —
it is **attribution at the decision unit** (the parcel/facility).

### 2.3 Landslide susceptibility in Wayanad is a crowded field

- **Guria et al. (2025):** MARCOS/CoCoSo/GRA MCDM susceptibility for
  Wayanad district.
- **Katkar et al. (2024):** temporal susceptibility for July 2023, December
  2023 and July 2024 using GEE with static (SRTM DEM, Bhoonidhi landslides,
  lineament, lithology, soil) and dynamic (IMERG rainfall, SMAP soil
  moisture, Sentinel-2 NDVI, Dynamic World LULC) layers.
- **Kellengere Shankarnarayan (2026, preprint, not peer-reviewed):**
  multi-temporal inventory (Landsat + spectral indices + BERT text mining)
  and RF/gradient-boosting susceptibility for four Western Ghats hotspots
  **including Wayanad**, explicitly framing **tourism-driven urbanisation**
  as an "under-quantified predisposing factor". *This is the closest
  overlap with our framing and must be cited, not ignored.*
- **Drisiya & Singh (2026):** InVEST Urban Nature Access + Habitat Risk
  Assessment for Idukki (2011–2025); built-up land shows the highest mean
  habitat risk (R̄ = 0.42) — the adjacent-district version of the same
  question.
- The 2024 disaster itself is now well documented: **Achu et al. (2025,
  Landslides)** on formation mechanisms and lessons; **Ramesh et al.
  (2025, Sci. Rep.)** on initiation, progression and impact (>400 deaths);
  **Aiswarya et al. (2026)** on susceptibility and local antecedent
  rainfall thresholds in the highland Western Ghats; **Ajin et al. (2022)**
  on three 2021 landslides where anthropogenic land activity, geomorphic
  processes and forest fragmentation were each implicated.

**Consequence:** "tourism urbanisation may increase landslide
susceptibility in Wayanad" is **already published as a framing** (2026
preprint). Our contribution cannot be that sentence.

### 2.4 Conflict and measurement-quality literatures exist and are usable

- **Morrison et al. (2025, GECCO)** compiled **1,942 human–elephant
  interaction records (2011–2014)** from compensation records and modelled
  them with a 10-algorithm ensemble across 16 variables. Crucially, the
  records are **village-level, not GPS** — which is exactly why our H3 was
  downgraded (D-3/D-18).
- **Sengupta et al. (2020)** and **Anoop & Ganesh (2020)** provide Kerala/
  Wayanad conflict context and conservation framing.
- **Tanyaş & Lombardo (2019)** define a **completeness index** for landslide
  inventories; **Santangelo et al. (2015)** quantify mapping error in
  inventory production. Both say the same thing our H2b implies: an
  inventory is a **measurement**, not a census.
- **Potapov et al. (2022)** document the GLAD 2000–2020 product (30 m
  forest, cropland, built-up, water) used for our primary land-conversion
  endpoint.

---

## §3 The gaps — and what this study actually does about them

| # | Gap in the literature | Closest prior work | What this study does | Genuinely new? |
|---|---|---|---|---|
| **G1** | Land conversion attributed to tourism is measured at district/taluk scale or by scenario; there is **no parcel-level counterfactual for facility presence**. | Karanth & DeFries 2010 (facility proximity to PAs); Pandya et al. 2022 (qualitative parcel conversion); Bijosh & Abraham 2024 (district LULC) | **H1:** 50 matched treatment/control pairs of *protected-remnant parcels*; Δ built-up 2000–2020 = **+16.32 pp @500 m** (Holm p = 1.7 × 10⁻⁶), consistent at 250 m (+24.01) and 1,000 m (+11.61) and under two independent built-up/forest indicators | **Yes** — the counterfactual at the parcel scale is the contribution, not the district trend |
| **G2** | Susceptibility maps are cell-level; **facility exposure is rarely tested against a terrain-matched sampling null**. | Katkar et al. 2024; Guria et al. 2025; Kellengere Shankarnarayan 2026 | **H2a:** observed facility-vs-inventory KDE overlap **T = 0.002921** vs null mean **0.001145** (~2.55×, above null p95), seeded B = 1,001, **p_holm = 0.014**; companion slope-share test null (p = 0.293) | **Yes** — an exposure *test*, not another susceptibility surface |
| **G3** | Nobody enumerates **what is actually inside a mapped hazard footprint** in a tourism landscape. | Event papers (Achu et al. 2025; Ramesh et al. 2025) document the event, not the asset overlap | **H2b:** 2024 scar (1.781 km²): **0 facilities, 0 buildings**, 0.758 km of `construction` road; 1 km inventory buffers (992.90 km², 46.6 % of district): **26/107 facilities**, **73,027 buildings**, 1,370.1 km roads | **Yes** — the null asset count inside the scar is a publishable, uncomfortable result |
| **G4** | Inventory incompleteness is treated as a nuisance, not a **result**; exposure studies rarely test whether the inventory contains the event that mattered. | Tanyaş & Lombardo 2019; Santangelo et al. 2015 | The 2024 scar sits **outside** the mapped-inventory proxy used for H2a; the H2a signal therefore describes **susceptibility terrain**, not the recent event. This is stated as a boundary, and D-20 adds a rainfall sensitivity labelled post-hoc | **Partly** — the *demonstration* (event outside inventory → exposure estimated from a different population) is new for tourism exposure; the completeness theory is not |
| **G5** | Tourism–hazard papers routinely over-claim from correlational maps. Few pre-register, pre-pin, or report **no-verdict**. | — | Frozen §3/§4, append-only §7 (D-1…D-21), R6→R9 hash chain, explicit **NO VERDICT** for H3 and **EXPLORATORY** for H4, non-inferential labelling of D-20 and D-21 | **Yes as method** — reproducibility/claim-discipline is a contribution in this subfield |
| **G6** | Almost no quantitative work links tourism expansion to **environmental disputes** spatially. | Muthanga (2001) and Jenu Kuruba (2025) appear in policy literature, not spatial analysis | **H4:** T = 1/6 documented disputes overlap the exposure hotspot vs area-proportion E = 0.457 (pinned p = 0.368; n = 6, non-inferential), margins 24/94/143 m | **Exploratory only** — do not claim more |
| **G7** | Single-site studies cannot separate site-specific co-location from a repeating pattern. | — | Two-site design (Wayanad + Mussoorie), identical recipe, rainfall pinned pre-freeze for Site 2 | **Pending** — a design contribution, not yet a result |

---

## §4 Novelty assessment — what we can and cannot claim

### 4.1 Not new (must not be claimed)

1. **"Tourism drives land-use change in Wayanad."** Saha et al. (2022),
   Bijosh & Abraham (2024) and Manawat & Yadav (2025) already cover the
   district trend and its modelling.
2. **"Wayanad is landslide-prone and susceptibility can be mapped."** At
   least four studies do this, including a 2026 preprint that already names
   tourism-driven urbanisation as a predisposing factor.
3. **"Facilities cluster near protected areas in India."** Karanth & DeFries
   (2010) established that 15 years ago.
4. **"Forest is being lost in Wayanad."** Established since at least 2022;
   our D-21 numbers are a *consistent accounting*, not a discovery.

### 4.2 New (defensible claims)

1. **Parcel-level counterfactual for facility presence** (H1). To our
   knowledge, no Indian tourism study matches facility-holding remnant
   parcels to comparable non-facility parcels and estimates conversion
   with paired inference. This is the paper's spine.
2. **Facility-level exposure tested against a terrain-matched null** (H2a),
   with a pre-registered radius family and a seeded Monte Carlo. Moves the
   field from "susceptibility where facilities are" to "are facilities
   where susceptibility is, more than chance?".
3. **Asset enumeration inside hazard footprints** (H2b), including the
   striking result that the 2024 scar contained **no** mapped tourist
   facility or building while the 1 km inventory buffers contain 26/107
   facilities and ~73k buildings. This inverts the usual assumption that
   tourism assets sit in the mapped hazard zones.
4. **A measurement-bias demonstration**: the exposure signal comes from an
   inventory that does not contain the 2024 event, and the built-up
   *absolute* extent differs 15× between GLAD and WorldCover while the
   *change* estimate is product-robust in sign. Few papers report this
   honestly.
5. **Claim-discipline as a methodological contribution**: pre-registration,
   pinned deviations, no-verdict reporting, and post-hoc labelling that
   cannot be upgraded.

### 4.3 The uncomfortable positioning

Kellengere Shankarnarayan (2026, **preprint**) reaches the same high-level
framing — tourism-driven urbanisation on steep forested slopes as an
under-quantified predisposing factor, with Wayanad as one of four hotspots.
Our paper must therefore be explicit:

> The *framing* is no longer novel; the *identification strategy* is.

If that preprint is peer-reviewed before we submit, we cite it as prior
framing and position our contribution as the **facility-level
counterfactual + exposure null + asset enumeration**, none of which it
does (it builds a susceptibility surface, not an exposure test).

---

## §5 Claim-strength ledger (what the report may say)

| Claim | Evidence | Strength | Failure mode if wrong |
|---|---|---|---|
| Facility-holding remnant parcels convert to built-up faster than matched comparables | H1, 50 pairs, Holm p = 1.7e-06, sign-stable across radii and two robustness indicators | **High** (within design) | Matching cannot remove unobserved parcel quality; 4 unmatched treated units; GLAD class semantics |
| Facilities sit in higher mapped-inventory-density terrain than chance | H2a(ii) p_holm = 0.014, survives D-17a re-render | **Moderate** | Inventory is a WMS proxy with unknown vintage (D-15); slope-share test null |
| The 2024 scar contained no mapped tourist facility or building | H2b enumeration, two independent building sources (GOB pre-event, OSM 2026) | **High** (enumeration) | Building datasets miss structures; scar digitisation error |
| HEC incidents locate off dense forest in human-modified land | H3 descriptive ρ (forest −0.178; human-modification ≤ 0.07), records village-level | **No verdict** | Records have no GPS; village centroid error dominates |
| Documented disputes overlap the exposure hotspot more than area proportion | H4: 1/6 vs E = 0.457, p = 0.368, n = 6 | **Exploratory** | Documentation bias; tiny n |
| Built-up extent roughly doubled, forest loss accelerated after 2020 | D-21 descriptive accounting (1.70×; loss 8.75 → 16.69 → 18.25 km² per period) | **Descriptive only** | Product disagreement (GLAD vs WorldCover 15×); no test, no CI |

---

## §6 Consequences for the report narrative

1. **Lead with the identification strategy, not the district trend.** The
   first paragraph of the introduction should acknowledge the existing
   Wayanad LULC and susceptibility literature and state that the open
   question is *attribution and exposure at the facility scale*.
2. **Cite the 2026 preprint explicitly** in the introduction and discussion,
   with its preprint status stated. Reviewers will find it.
3. **Report the negative results with equal prominence.** H2b's zero
   facilities in the 2024 scar and H3's no-verdict are the most
   policy-relevant findings and the most credible, because they cut against
   the authors' own framing.
4. **Do not call D-21 numbers "findings" without the product caveat.** The
   15× GLAD/WorldCover disagreement belongs in the results, not the
   appendix.
5. **Frame the two-site design as the replication strategy** and be explicit
   that Site 2 is not yet executed.

---

## §7 References (abstract-level reads unless noted)

Achu, A. L., Aju, C. D., Thomas, J., Raicy, M. C., et al. (2025). Decoding
the dynamics of July 2024 Mundakkai–Chooralmala landslide in Kerala
(India): an analysis of formation mechanisms, impacts and lessons learned.
*Landslides* 22(4), 1181–1197. https://doi.org/10.1007/s10346-024-02454-y

Aiswarya, A. N., Amrutha, A. S., Pradeep, G. S., & Vijith, H. (2026).
Landslide susceptibility and local antecedent rainfall thresholds in the
Highland Western Ghats Kerala India. *Discover Hazards* 2(1).
https://doi.org/10.1007/s44475-026-00056-x

Ajin, R. S., Nandakumar, D., Rajaneesh, A., Oommen, T., et al. (2022). The
tale of three landslides in the Western Ghats, India: lessons to be learnt.
*Geoenvironmental Disasters* 9(1).
https://doi.org/10.1186/s40677-022-00218-1

Anoop, N. R., & Ganesh, T. (2020). The forests and elephants of Wayanad:
challenges for future conservation. *Current Science* 118(3), 362.
https://doi.org/10.18520/cs/v118/i3/362-367

Bailey, K. M., McCleery, R. A., Binford, M. W., & Zweig, C. L. (2015).
Land-cover change within and around protected areas in a biodiversity
hotspot. *Journal of Land Use Science* 11(2), 154–176.
https://doi.org/10.1080/1747423x.2015.1086905

Bijosh, M. G., & Abraham, J. (2024). The application of remote sensing and
geographic information system techniques for the analysis of land use and
land cover changes in Wayanad district of Kerala. *Journal of Veterinary
and Animal Sciences* 55(3), 516–523.
https://doi.org/10.51966/jvas.2024.55.3.516-523

Dame, J., Schmidt, S., Müller, J., & Nüsser, M. (2019). Urbanisation and
socio-ecological challenges in high mountain towns: insights from Leh
(Ladakh), India. *Landscape and Urban Planning* 189, 189–199.
https://doi.org/10.1016/j.landurbplan.2019.04.017

Drisiya, J., & Singh, S. (2026). Integrated eco-environmental risk mapping
in the mountainous tropical landscapes of the Western Ghats, Kerala.
*Frontiers in Remote Sensing* 7.
https://doi.org/10.3389/frsen.2026.1803946

Guria, R., Mishra, M., & Das, J. (2025). Application of MARCOS, CoCoSo and
GRA MCDM models in a hybrid approach for landslide susceptibility
assessment in Wayanad district, Kerala (India). In *Advances in Geographic
Information Science*, 261–289.
https://doi.org/10.1007/978-3-031-89246-2_11

Karanth, K. K., & DeFries, R. (2010). Nature-based tourism in Indian
protected areas: new challenges for park management. *Conservation
Letters* 4(2), 137–149.
https://doi.org/10.1111/j.1755-263x.2010.00154.x

Katkar, R., Vijaywargiya, J., & Ramiya, A. M. (2024). Assessing changing
landslide risks in Wayanad, Kerala through temporal susceptibility mapping.
*IEEE India Geoscience and Remote Sensing Symposium (InGARSS)*, 1–4.
https://doi.org/10.1109/ingarss61818.2024.10983924

Kellengere Shankarnarayan, V. (2026). Landslide susceptibility in the
Western Ghats controlled by terrain and tourism driven urbanisation mapped
with remote sensing and machine learning. **Preprint**, Research Square.
https://doi.org/10.21203/rs.3.rs-10568295/v1

Manawat, R., & Yadav, D. K. (2025). Land-use and land-cover dynamics in
Wayanad, Kerala: QGIS, MOLUSCE and CA-ANN approach. *Lecture Notes in
Electrical Engineering*, 295–307.
https://doi.org/10.1007/978-981-96-8070-2_24

Morrison, J., Chatterjee, M., Ramkumar, K., Tiwari, S. K., et al. (2025).
Spatiotemporal distribution of negative human–elephant interactions in
Wayanad district, Kerala, India. *Global Ecology and Conservation* 62,
e03742. https://doi.org/10.1016/j.gecco.2025.e03742

Pandya, R., Dev, H. S., Rai, N. D., & Fletcher, R. (2022). Rendering land
touristifiable: (eco)tourism and land use change. *Tourism Geographies*
25(4), 1068–1084. https://doi.org/10.1080/14616688.2022.2077425

Potapov, P., Hansen, M. C., Pickens, A., Hernández-Serna, A., et al.
(2022). The global 2000–2020 land cover and land use change dataset derived
from the Landsat archive: first results. *Frontiers in Remote Sensing* 3.
https://doi.org/10.3389/frsen.2022.856903

Ramesh, M. V., Ekkirala, H. C., Singh, B., Kumar M, N., et al. (2025).
Mundakkai–Chooralmala landslide: assessment of initiation, progression, and
impact. *Scientific Reports* 15, 26961.
https://doi.org/10.1038/s41598-025-07828-3

Saha, K., Ghatak, D., & Muralee, N. S. S. (2022). Impact of plantation
induced forest degradation on the outbreak of emerging infectious
diseases — Wayanad district, Kerala, India. *IJERPH* 19(12), 7036.
https://doi.org/10.3390/ijerph19127036

Santangelo, M., Marchesini, I., Bucci, F., Cardinali, M., et al. (2015). An
approach to reduce mapping errors in the production of landslide inventory
maps. *NHESS* 15(9), 2111–2126.
https://doi.org/10.5194/nhess-15-2111-2015

Sarfraz, Y., Basharat, M., Riaz, M. T., Akram, M. S., et al. (2022).
Application of statistical and machine learning techniques for landslide
susceptibility mapping in the Himalayan road corridors. *Open Geosciences*
14(1), 1606–1635. https://doi.org/10.1515/geo-2022-0424

Sengupta, A., Binoy, V. V., & Radhakrishna, S. (2020). Human–elephant
conflict in Kerala, India: a rapid appraisal using compensation records.
*Human Ecology* 48(1), 101–109.
https://doi.org/10.1007/s10745-020-00128-6

Shukla, R., Öztürk, U., Levin-Keitel, M., Agrawal, S., et al. (2026).
Regulated tourism can become a tool for reducing landslide risk in
Himalayan urban centres. *Environmental Research Letters* 21(15), 151001.
https://doi.org/10.1088/1748-9326/ae83ce

Tanyaş, H., & Lombardo, L. (2019). Completeness index for earthquake-
induced landslide inventories. *Engineering Geology* 264, 105331.
https://doi.org/10.1016/j.enggeo.2019.105331
