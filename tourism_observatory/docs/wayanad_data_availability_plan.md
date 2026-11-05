PLAN — Wayanad open upgrades: data availability & quality
Status: 2026-11-04 (conversation date; Kerala Tourism "approved homestays as on 04-11-2026" matches this date)

OPEN ITEMS AND WHAT DATA IS NEEDED
------------------------
#1 H1 temporal-ordering sensitivity:
   - Needs facility construction/registration/operation dates (lower bound on facility presence
     during the 2000-2020 GLAD window) for the 107 verified parcels.
   - FOUND: Kerala Tourism "List of approved Homestays as on 04-11-2026" (official
     Dept. of Tourism, GoK) has approval-order date + Valid To for each facility.
     Parsed 7 Wayanad rows (all approved 2024; valid-to 2027): data/processed/wayanad_approved_homestays_2026-11-04.json
   - Historical full list (Homestays.pdf Wayanad §11): FOUND 4 pre-2020 facilities with
     registration dates: The Green Woods Homestay (2018-01-19), Cheeral Green Homestay
     (2019-06-05), Paulo Stays Homestay (2019-07-08), Sai Holiday Homestay (2019-12-22).
   - COMBINED dated set: 11 Wayanad facilities (7 current 2024 + 4 historical pre-2020).
     Saved as data/processed/wayanad_dated_facilities_2026-11-04.json.
   - QUALITY: high official source; approval date is registration/operation start lower bound,
     not construction date. Only ~11 dated facilities vs 107 registered, so n is small.
   - RECOMMEND: geocode the 4 pre-2020 facility names to parcels, then run the sensitivity on
     cut dates (2020): facilities with approval <= 2020 (present >= 2000-2020) versus all
     (approval > 2020).

#2 Placebo/negative-control arm — DONE (run). Placebo_pois.csv (312,554 OSM POI points) +
#2_placebo_summary.csv. Mean POI within 500m: treated 19.58 vs control 6.30 (total 979 vs 315).
#   Interpretation: tourism facility parcels sit in development-active zones (3.1x POI density).
# Quality: OSM POI coverage adequate for POI-counts/placebo; building-tag sparsity noted.
# Next: #3 NRSC Atlas second hazard - ingestion script READY (scripts/p3_landslide_inventory_ingest.py,
   docs/qa_gate_crs_check.md); waits on vector archive hand-off to produce the real layer.
   #5 manual (needs second coder).
   #6 (needs deviation pin D-22) - D-22 logged in docs/protocol_deviations.md.

#3 Second hazard definition for R-1:
   - Needs an attribute-bearing landslide inventory (independent of D-15 WMS proxy).
   - FOUND: NRSC Landslide Atlas of India (~80,000 landslides 1998-2022, 17 states incl. Western
     Ghats; event-based, seasonal, route-wise inventories); Bhuvan event/seasonal WMS inventories;
     Bhukosh (GSI) 2015-2020 inventory (~4,032 events in nearby Western Ghats districts).
   - QUALITY: NRSC Atlas is official but attributes/resolution vary; the WMS hazard is a proxy.
     Bhuvan WMS is explicitly "approximate". Probe (2026-11-04): bhukosh.gov.in -> DNS fail
     (wrong host); bhukosh.gsi.gov.in -> timeout; kerala.data.gov.in/catalog/bhukosh -> reachable
     but Vue-SSR SPA with no static download links; ndem.nrsc.gov.in and
     bhuvan-app1.nrsc.gov.in -> reachable, vector archive is credentialed/logged.
     ACTION NEEDED: vector archive download before the second hazard layer can be computed.
     Until then, R-1/R-3 exposure re-assessment is blocked on this.

#4 (done)  Moran's I: treatment 0.32, Hansen 0.46 -> p-values likely anti-conservative.

#5 (manual): second-coder verification - protocol DRAWN (docs/p5_inter_rater_protocol_wayanad.md);
   execution pending a named second coder.

#6 (document): H4 reframing - deviation pin D-22 logged in docs/protocol_deviations.md before
   any wording change.

WHAT IS FULLY RUN
-----------------
#7  Cross-product H1: GLAD built-up +10.33 pp (p=0.0025); Hansen loss +0.08 pp (p=0.91).
#8  Caliper sensitivity: 54% of frozen pairs within 50% width; 78% within 150%.

NEXT EXECUTABLE STEPS (in priority order)
-----------------------------------------
1. #1 - Build the dated facility table from the 7 approved homestays + the historical
        keralatourism PDF (if it has pre-2020 Wayanad entries). Deterministic once we check
        the PDF.
2. #2 - Run OSM extraction (if a Wayanad-bounded OSM extract is needed; the 558 MB southern
        zone file is already present) and build the placebo commercial-pressure score.
3. #3 - Download/curate NRSC Atlas event/route-wise landslide inventory for Wayanad.
4. #5 - Write the inter-rater verification protocol (manual; needs a second coder).
5. #6 - After deviation pin D-22, reword H4 register/report wording.

DATA QUALITY SUMMARY
--------------------
- Official GoK tourism: high for current status, low historical coverage in a snapshot.
- OSM: adequate for counts/placebo; weak for exact facility footprint.
- NRSC Atlas: official, pan-India, Western Ghats included; attribute and resolution variance.
- D-15 WMS proxy: labelled proxy; no attributes/vintage (bounded in R-1).

Deliverables: this plan file; dated facility table above; OSM extraction script (when #2 starts);
NRSC inventory pull log (when #3 starts).
