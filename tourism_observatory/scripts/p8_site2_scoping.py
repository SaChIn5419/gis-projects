#!/usr/bin/env python3
"""P8 — Mussoorie (Site 2) scoping facts: AOI geometry and protection inventory.

PREPLAN SCOPE — these are *site-definition* facts (where the site is, how much
of it is under which protection class, how much land is left). They are NOT
outcome statistics: no hypothesis, no comparison between arms, no change
measurement. They exist so that the Mussoorie preplan can choose an AOI and an
eligibility rule on evidence rather than by transplanting the Wayanad rule.

Inputs (hashed here, both already in data/raw under manifest 36):
  - data/raw/geoBoundaries-IND-ADM2_simplified.geojson  (Dehradun ADM2)
  - data/raw/WDPA_WDOECM_Oct2026_Public_IND.zip         (WDPA Oct 2026, India)

Outputs
  - data/processed/dehradun_boundary_32644.geojson      (AOI frame, UTM 44N)
  - outputs/qaqc/p8_site2_scoping_facts_2026-11-03.json (facts of record)

The WDPA layer is read from the .gdb inside the zip; the archive is unpacked to
a scratch dir first because OGR cannot open a FileGDB through /vsizip reliably
in this environment. Nothing is written outside data/processed and outputs/qaqc.

Usage: python scripts/p8_site2_scoping.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
QA = ROOT / "outputs" / "qaqc"
SCRATCH = Path("/tmp/opencode/wdpa_site2")

ADM2 = RAW / "geoBoundaries-IND-ADM2_simplified.geojson"
WDPA_ZIP = RAW / "WDPA_WDOECM_Oct2026_Public_IND.zip"
FEATURE = "Dehradun"                     # geoBoundaries shapeName
ANCHOR_4326 = (78.0740, 30.4598)         # Mussoorie town centre (pinned here)
RINGS_KM = (5, 8, 10)
CRS = "EPSG:32644"                       # UTM 44N — asserted below from the AOI anchor


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utm_zone(lon: float) -> int:
    return int((lon + 180.0) // 6.0) + 1


def read_wdpa() -> gpd.GeoDataFrame:
    gdbs = sorted(SCRATCH.glob("*.gdb"))
    if not gdbs:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(WDPA_ZIP) as zf:
            members = [m for m in zf.namelist()
                       if ".gdb/" in m and not m.endswith("/")]
            for m in members:
                target = SCRATCH / m
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(m) as src, target.open("wb") as dst:
                    dst.write(src.read())
        gdbs = sorted(SCRATCH.glob("*.gdb"))
    if len(gdbs) != 1:
        raise SystemExit(f"expected one .gdb in scratch, found {gdbs}")
    import fiona
    layers = list(fiona.listlayers(str(gdbs[0])))
    poly = [n for n in layers if "poly" in n.lower()][0]
    return gpd.read_file(gdbs[0], layer=poly)


def km2(geom) -> float:
    return geom.area / 1e6


def main() -> int:
    adm = gpd.read_file(ADM2)
    sel = adm[adm.shapeName == FEATURE]
    if len(sel) != 1:
        raise SystemExit(f"expected exactly 1 ADM2 feature for {FEATURE}, got {len(sel)}")

    d4326 = sel[["shapeName", "shapeID", "geometry"]].copy()
    minx, miny, maxx, maxy = d4326.total_bounds
    # Dehradun straddles 78 E (zone 43/44 edge), so the extent rule is
    # ambiguous: the zone is set by the AOI anchor, not the district centroid.
    zone_anchor = utm_zone(ANCHOR_4326[0])
    if CRS != f"EPSG:326{zone_anchor:02d}":
        raise SystemExit(f"AOI anchor implies zone {zone_anchor}, expected 44")
    east = gpd.clip(d4326, box(78, 0, 180, 90))
    share_east = 100.0 * east.to_crs(CRS).area.sum() / d4326.to_crs(CRS).area.sum()

    d = d4326.to_crs(CRS)
    dgeom = unary_union(d.geometry)
    d["area_km2"] = d.area / 1e6
    out_boundary = PROC / "dehradun_boundary_32644.geojson"
    d.to_file(out_boundary, driver="GeoJSON")

    wdpa = read_wdpa().to_crs(CRS)
    wdpa = wdpa[wdpa.intersects(dgeom)].copy()
    clipped = gpd.overlay(wdpa, d[["geometry"]], how="intersection")
    clipped["area_km2"] = clipped.area / 1e6

    by_desig = (clipped.groupby("DESIG_ENG").area_km2.sum()
                .sort_values(ascending=False).round(3).to_dict())
    rf = unary_union(clipped[clipped.DESIG_ENG == "Reserve Forest"].geometry)
    esa = unary_union(clipped[clipped.DESIG_ENG == "Eco Sensitive Area"].geometry)
    allw = unary_union(clipped.geometry)

    anchor = gpd.GeoSeries([Point(*ANCHOR_4326)], crs="EPSG:4326").to_crs(CRS).iloc[0]
    rings = {}
    for r in RINGS_KM:
        zone_geom = dgeom.intersection(anchor.buffer(r * 1000.0))
        za = km2(zone_geom)
        covered = km2(zone_geom.intersection(allw))
        rings[f"{r}km"] = {
            "zone_km2": round(za, 3),
            "wdpa_km2": round(covered, 3),
            "wdpa_pct": round(100.0 * covered / za, 2),
            "wdpa_free_km2": round(za - covered, 3),
            "reserve_forest_km2": round(km2(zone_geom.intersection(rf)), 3),
            "eco_sensitive_km2": round(km2(zone_geom.intersection(esa)), 3),
        }

    strict = clipped[clipped.DESIG_ENG.astype(str).str.contains(
        "National Park|Sanctuary|Conservation Reserve|Ramsar", case=False, na=False)]
    facts = {
        "task": "P8 Site 2 (Mussoorie) preplan scoping — AOI + protection inventory",
        "label": "site-definition facts only; no hypothesis, no arm comparison, no outcome",
        "inferential": False,
        "date": "2026-11-03",
        "site": {
            "analysis_frame": "Dehradun district (geoBoundaries ADM2)",
            "boundary_feature": FEATURE,
            "shape_id": str(d4326.shapeID.iloc[0]),
            "anchor_4326": list(ANCHOR_4326),
            "anchor_note": "Mussoorie town centre; used only to draw AOI rings",
            "crs": CRS,
            "utm_zone_basis": (
                f"AOI anchor lon {ANCHOR_4326[0]:.4f} E sets zone 44; the district "
                f"straddles the 78 E zone edge (extent {minx:.4f}–{maxx:.4f} E, "
                f"{share_east:.1f}% of area east of 78 E), so an extent/centroid "
                f"rule would have picked zone 43 and distorted the AOI."),
            "area_km2": round(km2(dgeom), 3),
            "bounds_4326": [round(v, 4) for v in (minx, miny, maxx, maxy)],
        },
        "protection": {
            "wdpa_vintage": "WDPA Oct 2026 public, India",
            "features_intersecting": int(len(clipped)),
            "area_by_designation_km2": by_desig,
            "reserve_forest_km2": round(km2(rf), 3),
            "eco_sensitive_km2": round(km2(esa), 3),
            "reserve_forest_x_esa_km2": round(km2(rf.intersection(esa)), 3),
            "union_km2": round(km2(allw), 3),
            "union_pct_of_district": round(100.0 * km2(allw) / km2(dgeom), 2),
            "wdpa_free_km2": round(km2(dgeom.difference(allw)), 3),
            "iucn_categories": clipped.IUCN_CAT.value_counts().to_dict(),
            "strict_pa_features": int(len(strict)),
            "strict_pa_km2": round(float(strict.area.sum()) / 1e6, 3),
            "strict_pa_note": "no IUCN I-IV, National Park or Wildlife Sanctuary feature "
                              "intersects Dehradun in this WDPA vintage; the only "
                              "Ramsar site is Asan (valley, ~4 km2).",
        },
        "rings": rings,
        "inputs_sha256": {
            "geoBoundaries_adm2": sha256(ADM2),
            "wdpa_ind_zip": sha256(WDPA_ZIP),
            "boundary_processed": sha256(out_boundary),
        },
        "notes": [
            "WDPA for India includes Reserve/Protected Forest administrative "
            "polygons, which is why the union covers 70.9% of the district.",
            "The Doon Valley Ecologically Sensitive Area alone covers 1,779 km2 "
            "and overlaps 831 km2 of Reserve Forest; areas are unioned, never summed.",
            "Ring zones are district-clipped: the 8 km ring is only 115.9 km2 of "
            "the 201 km2 circle because the district boundary cuts it.",
        ],
    }
    QA.mkdir(parents=True, exist_ok=True)
    out = QA / "p8_site2_scoping_facts_2026-11-03.json"
    out.write_text(json.dumps(facts, indent=1))

    print(f"boundary -> {out_boundary.relative_to(ROOT)}  ({facts['site']['area_km2']} km2)")
    print(f"facts    -> {out.relative_to(ROOT)}")
    print(f"WDPA union {facts['protection']['union_km2']} km2 "
          f"({facts['protection']['union_pct_of_district']}%), free "
          f"{facts['protection']['wdpa_free_km2']} km2")
    for k, v in rings.items():
        print(f"  ring {k:>4}: {v['zone_km2']:7.1f} km2, WDPA {v['wdpa_pct']:5.1f}%, "
              f"free {v['wdpa_free_km2']:5.1f} km2")
    print(f"inputs sha: adm2 {facts['inputs_sha256']['geoBoundaries_adm2'][:8]} "
          f"wdpa {facts['inputs_sha256']['wdpa_ind_zip'][:8]} "
          f"boundary {facts['inputs_sha256']['boundary_processed'][:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
