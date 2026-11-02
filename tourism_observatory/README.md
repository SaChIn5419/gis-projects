# Tourism, Ecological Risk and Community Exposure Observatory

**Scope (user, 2026-10-22): exactly two investigations — Wayanad (Kerala) first, then
Mussoorie (Uttarakhand). No third site. No foreign benchmark.**

This folder isolates the new research program from the Jhabua/VM0047 portfolio
(src/, config/, docs/ remain untouched).

## Structure

```
tourism_observatory/
├── README.md          ← you are here
├── docs/              ← frozen pre-analysis artifacts + per-site docs
│   ├── preregistration_wayanad.md   (FROZEN: hypotheses H1–H4, control rules, info boundary)
│   ├── literature_matrix.md         (FROZEN: ~25 entries, indicators + limitations)
│   └── data_audit_wayanad.md        (FROZEN: 21 sources, verdict v2 CONDITIONAL GO, risks R1–R3)
├── config/            ← wayanad.yaml (P1), then mussoorie.yaml
├── data/              ← raw + processed rasters/tables (git-ignored payloads; hashes in manifests)
├── outputs/           ← maps, waterfalls, registers (no outcome maps before freeze gate C1)
└── scripts/           ← program-specific ingest/analysis scripts (P1+)
```

## Phase status

| Phase | What | Status |
|---|---|---|
| P0 | Literature matrix + preregistered hypotheses + source-by-source data audit | **FROZEN + C1-revised (deviation entries D-2…D-10; hashes R5 in `../docs/PROJECTSTATE.md` §9)** |
| C1 | User cross-check of prereg/matrix/audit | **SIGNED 2026-10-23 — final sign-off recorded at prereg dev-D-10 (review returned REVISE first; all action-register items resolved via deviation log)** |
| P1 | Wayanad **baseline-only** acquisition (registry downloads with manifest hashes, baseline covariates, QA on baseline only, provenance report) | **COMPLETE — 17 sources hashed, QA gate PASS (0 critical/0 warnings/62 checks), `docs/p1_provenance_report.md` filed; feeds C2 go/no-go** — no outcome maps |
| C2 | P1 data-completeness go/no-go on the provenance report | **GO 2026-10-23 (user decision on `docs/p1_provenance_report.md` §7–§8; residuals logged as non-blocking)** |
| P2 | Wayanad **control matching** (facility universe + existence verification, 2024 scar exclusion re-digitized from NRSC VAP3, 1 km parcel grid, baseline covariates, deterministic 1:1 match + balance gate) | **COMPLETE 2026-10-26** (123 facilities / 107 verified; scar v2 D-12; 1,163 usable parcels; arms 54/886; **50/54 matched, max\|SMD\|=0.0667 < 0.10 → PASS**) — §8 checklist **SIGNED, freeze R6 recorded 2026-10-26** (PROJECTSTATE §9) |
| P3 | Wayanad **outcome analysis** under frozen design (H1–H4 computation) | **COMPLETE 2026-10-28 / 2026-11-02** — **H1: NOT falsified** (500 m +16.32 pp, Holm p=1.7e-06; robustness signs agree) · **H2a: NOT falsified** (density exceedance p_holm=0.014, D-16 corrected MC; D-15 D-17 deviations) · **H2b: descriptive registers** · **H3: no verdict by D-18 recipe** (forest-cover −0.18 only stable feature) · **H4: EXPLORATORY, NOT falsified** (T_obs=1 vs E=0.457; D-5) — plus **D-20 post-hoc rainfall sensitivity 2026-11-02** (CHIRPS v2.0; hotspots in the lower-rainfall farming belt ρ=−0.572; no monsoon lock-in; non-inferential, H3 verdict unchanged), `docs/p3_d20_rainfall_sensitivity_log.md`; all outcome logs in `docs/` |
| P4–P5 | Wayanad risk register → evidence brief | **COMPLETE 2026-11-02** — `docs/p4_risk_register_wayanad.md` (R-1…R-5 entries, caveat blast-radius §2, unknowns §3, triggers §4) and `docs/p5_evidence_brief_wayanad.md` (verdict block, consensus statement, hash-pinned provenance §6); register introduces no new statistics |
| P6–P9 | Mussoorie (pipeline revalidation) | after Wayanad review (C4) |

## Non-negotiable working rules (carried from preregistration §5)

1. **No outcome maps before hypotheses + control rules are frozen and cross-checked.**
   Permitted pre-freeze: registry geocoding, facility-existence verification, baseline
   covariates, hazard layers, QA on baseline layers only.
2. Post-freeze changes are append-only deviation log entries — original text never edited.
3. Observed / modelled / assumed are separated in every output; hazard, HEC and community
   events are analyzed as **separate categories** — never composited into one score.
4. Every run passes a QA gate that opens actual GeoTIFFs (Jhabua pattern); waterfall areas
   must sum to AOI area.
5. Loss outputs are exposure registers + scenario ranges; no expected-loss arithmetic
   without evidence-backed P and E.

Validation anchors for Wayanad: V1 registry/land-use consistency (Kerala Tourism/Ecstat),
V2 HEC association vs published 1,942-incident study, V3 2024 landslide extents vs
published inventories.
