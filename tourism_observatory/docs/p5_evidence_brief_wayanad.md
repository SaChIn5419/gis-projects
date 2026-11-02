# P5 — Wayanad evidence brief (Site 1 of 2)

**Status:** Wayanad pipeline COMPLETE (P1 baseline → P2 matching → P3
outcomes H1–H4 → D-20 post-hoc rainfall sensitivity → P4 risk register).
**Audience:** decision-makers consuming the observatory's first site
report; every claim below is traceable to hash-pinned artifacts
(§6). Governing freeze: **R6** (§8 pre-analysis checklist signed);
deviation log D-1…D-20 append-only; R-chain R7→R7a…R7d→R7e→**R8**
(`da2baee8…`, D-20 pin recorded before any rainfall statistic).

---

## §1 Verdict block

| hypothesis | frozen question (plain language) | verdict | grade | test that justifies it |
|---|---|---|---|---|
| **H1** | Do facility-holding protected-remnant parcels convert to built-up faster than matched non-facility parcels? | **NOT falsified — supported** | **High** | Matched-pair (50/50), Δ built-up 2000–2020: **+16.32 pp** @500 m (primary), +24.01 @250 m, +11.61 @1,000 m; paired t = 5.64, **Holm p = 1.7e-06** across the frozen family; robustness signs agree (WorldCover +5.24 pp; Hansen loss +1.96 pp) |
| **H2a** | Is mapped landslide footprint density near facilities higher than chance? | **NOT falsified (density); nil (slope-share)** | **Moderate** | H2a(ii) exceedance: T_obs = 0.002921 vs null mean 0.001145 (~2.55×, above null p95 0.002164), seeded B = 1,001 MC, **p_holm = 0.014**; survived the registered D-17a independent re-render + rerun; companion slope-share test null (p_holm = 0.293) |
| **H2b** | What exactly sits inside the mapped hazard footprints? | Descriptive register (no test by design) | Descriptive | Enumeration: scar register (a) and 1 km-buffer register (b), §3 below |
| **H3** | Do HEC incident hotspots aggregate toward pre-2011 human-influenced, non-protected covariates? | **NO VERDICT** (registered D-3/D-18 downgrade) | No-verdict | Village-massed records (no GPS at source) → descriptive KDE-overlap direction check only: forest-cover ρ = **−0.178 / −0.051 / −0.218** (primary / outside-WDPA / elephant arms) the only stable feature; all human-modification covariates near-null (|ρ| ≤ 0.07); facilities null in every arm |
| **H4** | Do documented disputes overlap tourism-hazard exposure hotspots more than expected by area proportion? | **NOT falsified on the §3 point-estimate rule** — EXPLORATORY | **Exploratory** | T_obs = **1**/6 vs deterministic E = **0.457**; pinned permutation (B = 10,000, seed 20261102) p = 0.368 — reported but **non-inferential (D-5, n < 15)** |

## §2 Consensus statement (what the block establishes)

> Tourism-facility presence in Wayanad's protected remnant class is
> associated with **faster built-up conversion** (H1, high confidence) and
> **higher mapped landslide-inventory density** (H2a, moderate confidence,
> proxy-caveated) than matched comparable land — a convergent
> *co-location of tourism presence and mapped exposure*. The
> community-conflict side is resolved only descriptively: HEC incidents
> consistently locate **off dense forest in human-modified land**, with no
> measurable magnitude and **no facility-proximity signal in any arm**
> (H3, no-verdict); documented disputes cluster around
> **hazard-adjacent land friction** (quarry protest next to the 2024
> corridor), not facility–community conflict (H4, exploratory). The
> supported narrative is **hazard-adjacent development pressure**, not
> "tourism causes conflict".

The D-20 rainfall sensitivity (labelled post-hoc, non-inferential) is
appended as: incident hotspots lie in the **lower-rainfall, human-modified
farming belt** (rain_annual ρ = −0.572 primary / −0.234 outside-WDPA;
wettest decile at the 13th incident percentile), with **no monsoon
lock-in** (SW-monsoon Jun–Sep share 0.4183) — direction-consistent with
the one stable registered H3 feature (negative forest-cover share), but
quotable only as post-hoc sensitivity; H3's no-verdict stands unchanged
(D-20e precommitment).

## §3 Enumeration of record (H2b registers)

| footprint | area | facilities | buildings | roads |
|---|---|---|---|---|
| (a) 2024 scar, Chooralmala–Mundakkai (NRSC VAP3 digitized) | 1.781 km² | **0** | **0** (GOB pre-event and OSM 2026 both) | 1 segment, **0.758 km**, class `construction` |
| (b) 1 km buffers around 990 mapped-inventory proxy polygons (pre-Jul-2024 stock) | 992.90 km² (46.6% district), overlaps 2024 event *excluded* | **26/107** | **73,027** Google (conf ≥ 0.7: 57,291; ±10 m: 71,980–74,050) · **10,389** OSM (2026-10) | **1,370.1 km**, 3,184 segments (OSM 2026-10) |

## §4 Methods in one paragraph each (audit trail highlights)

1. **Facility + match design (P2):** 123 registry entries → 107
   existence-verified inside district (satellite imagery pass); 1,163-
   parcel protected-remnant grid; deterministic 1:1 no-replacement match,
   frozen calipers/covariates; **50/54 matched**, balance gate
   max |SMD| = 0.0667 < 0.10 → PASS (freeze R6).
2. **Outcomes (P3):** GLAD built-up change primary endpoint (H1);
   seeded Monte Carlo exceedance with D-16 corrected (1+#{T_j ≥ T_obs})/1001
   rule (H2a); overlay registers with ±-m jitter ranges (H2b);
   place-name geocoding → KDE σ = 1 km → percentile/Spearman descriptive
   overlap, three arms (H3, D-18); dispute register → hotspot-overlap
   area-proportion test, EXPLORATORY flag (H4, D-19; runs A/B superseded
   and disclosed).
3. **D-20 post-hoc rainfall sensitivity:** CHIRPS v2.0 0.05° monthly
   2011–2014 (public domain, Funk et al. 2015 attribution), seasonality
   read from record dates + bilinear-warp spatial covariates joined via
   the identical D-18 reader; **cannot alter H3's verdict by precommitment**.

## §5 Limitations (caveat chain with blast radius)

- **WMS-proxy hazard inventory (D-15):** no attributes/vintage; bounds
  R-1/H2a only; bounded by the D-17a re-render agreement; deeper probe
  requires a new §7 pin.
- **Vintages:** GOB ≤ May-2023; OSM 2026-10 (mixed rebuild); roads
  2026-10; facility universe = current existence. No entry may read
  these as historical baselines.
- **Documentation/effort bias** in both registers (compensation records;
  press/LCW): partially absorbed spatially, selection unquantified.
- **D-3 structural ceiling** on H3 (never had GPS).
- H4 **n = 6 < 15** ⇒ EXPLORATORY; margins 24/94/143 m disclosed.
- **No visitation data** — tourism pressure proxied by facility
  existence only.
- Rainfall entered post-hoc only (D-20); Mussoorie will pin it
  pre-freeze.

## §6 Provenance ledger (hash-pinned)

- Prereg of record: `docs/preregistration_wayanad.md` — **R8 =**
  `da2baee87b9dad57cd1c9d0077242e0cbbf36233d98d842e90d291beba9d98e8`
  (D-20 pin, verified byte-stable after the rainfall run).
- QA-facts sha256 (re-verified by QA pass at brief finalization, 2026-11-02):

| facts file | sha256 (first 8) |
|---|---|
| `p3_h1_facts_2026-10-28.json` | `85d1597c` |
| `p3_h2a_facts_2026-10-28.json` | `f3432795` |
| `p3_h2b_facts_2026-10-28.json` | `e50ae8bd` |
| `p3_h3_facts_2026-11-02.json` | `dd73bddb` |
| `p3_h3_rainfall_sensitivity_2026-11-02.json` | `e1ab4cbe` |
| `p4_h4_facts_2026-11-02.json` | `d945c4a6` |
| `p4_h4_dispute_table_2026-11-02.csv` | `7a1996cd` |

- Register disclosure (H2b(b) facility ids, exposure register):
  `h2b_facility_exposure_register_2026-10-28.csv`.
- Data manifest: **36 entries**, all sha256-filled (incl. 3 CHIRPS
  artifacts of D-20: stack `58fdd6a5…`, annual `5200897d…`, monsoon
  `5bfacd9f…`).
- Logs of record: `docs/p3_h1_analysis_log.md`, `docs/p3_h2_analysis_log.md`,
  `docs/p3_h3_analysis_log.md`, `docs/p4_h4_analysis_log.md`,
  `docs/p3_d20_rainfall_sensitivity_log.md`,
  `docs/p4_risk_register_wayanad.md`, this brief.
- Governing chain: R6 §8 freeze → D-1…D-19 append-only → R7e → R8
  (D-20) → this synthesis.

## §7 What Site 2 (Mussoorie) adds

The Wayanad block is one site; the design is a **two-site observatory**.
Mussoorie (P1–P3 preplanned next): rainfall pinned **pre-freeze** as a
registered covariate (landslide triggering is rainfall-driven), mountain-
road-lifeline context, same facility/matching recipe, same grades. The
cross-site comparison separates site-specific co-location from a
repeating pattern.

*End of brief.*
