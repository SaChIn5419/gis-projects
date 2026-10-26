"""P2 step (b3) — compile D-6: 2024 Chooralmala–Mundakkai landslide scar zone.

Preregistered exclusion (§4.4): the 2024 landslide scar zone is excluded from BOTH
matching arms. This script compiles that zone from published, georeferenced sources
into data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg (EPSG:32643), then
records the source hashes into data/manifest.json.

SOURCES (both public, georeferenced; coordinates digitized by eye from the figures —
no geocoding jitter, no automated feature extraction):
  1. Peer-reviewed paper (PMC12290006) Fig. 1 — the COMPLETE debris-flow path
     source(Chooralmala, 842 m) → Mundakkai (955 m) → deposit (1,558 m), with a
     full lat/lon graticule (76°7'E–76°11'E, 11°27'30"N–11°31'N). This is the
     primary control for the corridor centerline and its extent.
  2. NRSC/ISRO Landslide Impact Map, Chooralmala (Charter Call 1029, AOI 01,
     observed 06/07/2024, published 06-08-2024) — debris-flow extent outlined,
     UTM Zone 43N / WGS84, scale 1:5,000. Confirms the corridor position and
     the deposit lobe near the Iruvanipuzha river.

METHOD (logged, not a rule change): a buffered corridor around the digitized
centerline. The centerline is ~2 km long; the debris flow is ~150–250 m wide, so a
~150 m half-width buffer (~300 m corridor) is used to reliably cover the disturbed +
deposited footprint. This is deliberately conservative (over-excludes rather than
under-excludes) — matching only needs to keep the freshly-disturbed zone out of both
arms, and over-excluding a handful of parcels is safer than contaminating a control
parcel with post-event ground.

Information boundary (§5): this is an exclusion mask, not an outcome. The 2024 scar
is used ONLY to keep both arms off disturbed ground (§4.4). No pre/post change is
computed here and no outcome raster is read.

Outputs:
  data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg  (layer: scar, EPSG:32643)
  appends a row to data/manifest.json for each source PDF

Usage:  python scripts/p2_compile_scar_d6.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
MANIFEST = ROOT / "data" / "manifest.json"

STAGE = RAW / "staging_d5d6"
PAPER_PDF = STAGE / "PMC12290006_Fig1_location_runout_map.jpg"  # digitized figure
NRSC_PDF = STAGE / "NRSC_Landslide_Impact_Map_Chooralmala_VAP8_6Aug2024.pdf"
OUT_GPKG = PROC / "scar_chooralmala_mundakkai_2024_32643.gpkg"

# Debris-flow centerline (lon, lat), digitized by eye from PMC12290006 Fig. 1 and
# cross-checked against the NRSC impact map. Source (Chooralmala, 842 m) at the
# north-east, deposit lobe (1,558 m) toward the Iruvanipuzha at the south-west.
CENTERLINE_LL = [
    (76.1490, 11.5010),  # source area (Chooralmala, ~842 m)
    (76.1450, 11.4970),
    (76.1420, 11.4940),
    (76.1390, 11.4905),  # Mundakkai (~955 m)
    (76.1370, 11.4875),
    (76.1360, 11.4840),
    (76.1348, 11.4820),  # deposit toward river (~1,558 m)
]
BUFFER_HALF_M = 150.0  # ~300 m corridor to cover the 150–250 m debris width


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("D-6 scar compilation — Chooralmala–Mundakkai 2024 landslide")
    missing = [p for p in (PAPER_PDF, NRSC_PDF) if not p.exists()]
    if missing:
        print("FAIL: missing source PDFs:", [str(m) for m in missing])
        return 1

    tf = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    xy = [tf.transform(lo, la) for lo, la in CENTERLINE_LL]
    line = LineString(xy)
    corridor = line.buffer(BUFFER_HALF_M, cap_style=2, join_style=2)  # flat ends

    scar = gpd.GeoDataFrame(
        {
            "event": ["chooralmala_mundakkai_2024"],
            "source_primary": ["PMC12290006 Fig.1 (peer-reviewed debris-flow path)"],
            "source_confirm": ["NRSC impact map Charter Call 1029 AOI 01 (06-08-2024)"],
            "method": [f"buffered centerline, half-width {int(BUFFER_HALF_M)} m"],
            "buffer_half_m": [BUFFER_HALF_M],
            "centerline_len_m": [round(line.length, 1)],
            "area_km2": [round(corridor.area / 1e6, 3)],
            "compiled_on": [date.today().isoformat()],
        },
        geometry=[corridor],
        crs="EPSG:32643",
    )
    PROC.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    scar.to_file(OUT_GPKG, layer="scar", driver="GPKG")

    print(f"  centerline length : {line.length:.0f} m")
    print(f"  corridor area     : {corridor.area/1e6:.3f} km² "
          f"(half-width {int(BUFFER_HALF_M)} m)")
    b = scar.total_bounds
    print(f"  bounds (EPSG:32643): {b}")
    print(f"  -> {OUT_GPKG.relative_to(ROOT)}")

    # ---- manifest provenance rows (match data/manifest.json 'sources' schema) ----
    # NOTE: the manifest is append-only provenance kept in P1's exact formatting;
    # we dedupe by row id and only rewrite the file when a row is genuinely new.
    man = json.loads(MANIFEST.read_text())
    rows = man["sources"]
    existing_ids = {r.get("id") for r in rows}
    meta = {
        PAPER_PDF: dict(
            id="d6_scar_paper_path",
            audit_ref="audit §3 D-6 (2024 Chooralmala–Mundakkai scar)",
            type="figure-digitized-raster",
            source="Peer-reviewed debris-flow path — PMC12290006 Fig. 1 "
                   "(location/runout map: source Chooralmala 842 m → Mundakkai 955 m "
                   "→ deposit 1,558 m, with lat/lon graticule)",
            source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC12290006/",
            license="open access (PMC)",
            version="PMC12290006",
            note="D-6 primary: corridor centerline digitized by eye from this "
                 "figure's graticule (no automated extraction, no jitter). "
                 "Compiled by scripts/p2_compile_scar_d6.py into the §4.4 scar "
                 "exclusion corridor."),
        NRSC_PDF: dict(
            id="d6_scar_nrsc_impact_map",
            audit_ref="audit §3 D-6 (2024 Chooralmala–Mundakkai scar)",
            type="figure-digitized-raster",
            source="NRSC/ISRO Landslide Impact Map, Chooralmala (Charter Call 1029, "
                   "AOI 01, observed 06/07/2024, published 06-08-2024); "
                   "UTM Zone 43N / WGS84, scale 1:5,000",
            source_url="https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php",
            license="NRSC/ISRO (Charter rapid-map product)",
            version="VAP8 06-08-2024",
            note="D-6 confirmation: debris-flow extent outlined on-map; confirms "
                 "corridor position + deposit lobe near Iruvanipuzha. "
                 "Compiled by scripts/p2_compile_scar_d6.py."),
    }
    added = []
    for p in (PAPER_PDF, NRSC_PDF):
        m0 = meta[p]
        if m0["id"] in existing_ids:
            continue
        m = m0.copy()
        # manifest paths are repo-root-relative with the project-dir prefix (P1 style)
        m["path"] = f"tourism_observatory/{p.relative_to(ROOT)}"
        m["sha256"] = sha256(p)
        m["bytes"] = p.stat().st_size
        m["acquired_utc"] = date.today().isoformat()
        m["status"] = "verified"
        rows.append(m)
        added.append(m["path"])
    if added:
        man["last_updated"] = date.today().isoformat()
        MANIFEST.write_text(json.dumps(man, indent=1) + "\n")
    print(f"  manifest: +{len(added)} source row(s)"
          f"{' (already present — file untouched)' if not added else ''}")
    print("scar_excluded can now be set true by re-running p2_parcel_covariates.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
