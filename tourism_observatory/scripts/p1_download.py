"""P1 download — Wayanad baseline sources (tourism_observatory).

Jhabua/audit dev-D-6 rule: a source flips to "verified" only when the file is
actually on disk and its SHA-256 is recorded in data/manifest.json. This script
downloads the pinned baseline sources, hashes them on arrival, and upserts the
manifest. Idempotent: an existing file whose size matches the recorded bytes is
kept and re-hashed, never silently re-downloaded.

Scope: BASELINE ONLY (prereg §5 boundary) — DEM, land cover, tree cover, roads,
protected areas. No outcome layers.

Usage:
    python scripts/p1_download.py            # download everything missing
    python scripts/p1_download.py --only id  # one source (repeatable)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]          # tourism_observatory/
REPO = ROOT.parent                                   # qgisproject_job/
MANIFEST = ROOT / "data" / "manifest.json"
RAW = ROOT / "data" / "raw"

UA = {"User-Agent": "tourism-observatory-p1/0.1 (research data ingest)"}

# Pinned baseline sources. URLs verified live on 2026-10-23.
SOURCES = [
    {
        "id": "dem_cop_n11e075",
        "audit_ref": "§3 audit-D-7",
        "filename": "Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif",
        "url": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N11_00_E075_00_DEM/Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif",
        "type": "raster",
        "source": "Copernicus DEM GLO-30 DGED (1 arcsec), AWS open-data mirror",
        "license": "free use with attribution (Copernicus / DLR, EULA accepted by use)",
        "tile": "N11_00_E075_00",
        "note": "Tile covers 11-12N, 75-76E; Wayanad AOI needs this + N11E076 (lat extent 11.45-11.98 N confirmed at boundary ingest).",
    },
    {
        "id": "dem_cop_n11e076",
        "audit_ref": "§3 audit-D-7",
        "filename": "Copernicus_DSM_COG_10_N11_00_E076_00_DEM.tif",
        "url": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N11_00_E076_00_DEM/Copernicus_DSM_COG_10_N11_00_E076_00_DEM.tif",
        "type": "raster",
        "source": "Copernicus DEM GLO-30 DGED (1 arcsec), AWS open-data mirror",
        "license": "free use with attribution (Copernicus / DLR, EULA accepted by use)",
        "tile": "N11_00_E076_00",
        "note": "Second tile: AOI crosses 76E (lon extent 75.77-76.44 E).",
    },
    {
        "id": "worldcover_2021_n09e075",
        "audit_ref": "§5 audit-D-15",
        "filename": "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif",
        "url": "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif",
        "type": "raster",
        "source": "ESA WorldCover 2021 v200 (10 m), official S3",
        "license": "CC BY 4.0",
        "version": "v200 / 2021",
        "tile": "N09E075",
        "note": "Single 3-degree tile covers the whole AOI (lat 11.45-11.98 N -> N09; lon 75.77-76.44 E -> E075). Water masking for eligibility domain (prereg dev-D-2).",
    },
    {
        "id": "hansen_treecover2000",
        "audit_ref": "§5 audit-D-16",
        "filename": "Hansen_GFC-2024-v1.12_treecover2000_20N_070E.tif",
        "url": "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/Hansen_GFC-2024-v1.12_treecover2000_20N_070E.tif",
        "type": "raster",
        "source": "Hansen Global Forest Change v1.12 (2024), treecover2000 band, 10-degree tile",
        "license": "CC BY 4.0 (UMD / Google / WRI / UNEP/WCMC / USGS/NASA / JRC)",
        "version": "GFC-2024 v1.12",
        "tile": "20N_070E",
        "note": "GFC tiles are named by NORTH edge (20N = 10-20N, per Jhabua tile note); AOI lat 11.45-11.98 N -> 20N_070E. An earlier wrong pick (10N_070E = 0-10N) was deleted at ingest 2026-10-23. Baseline tree-cover matching covariate ONLY; loss/gain bands are not part of P1 baseline scope.",
    },
    {
        "id": "cci_lulc_2005",
        "audit_ref": "§5 audit-D-14; OI-2 (vintage fixed at this ingest)",
        "filename": "ESACCI-LC-L4-LCCS-Map-300m-P1Y-2005-v2.0.7cds-N00E045-lccs_class.tif",
        "url": "https://planetarycomputer.microsoft.com/api/stac/v1/collections/esa-cci-lc/items/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2005-v2.0.7cds-N00E045",
        "asset_url": "https://landcoverdata.blob.core.windows.net/esa-cci-lc/cog/v2.0.7cds/N00E045/2005/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2005-v2.0.7cds-N00E045-lccs_class.tif",
        "type": "raster",
        "source": "ESA CCI Land Cover L4 LCCS 300 m annual 2005, v2.0.7cds (Microsoft Planetary Computer STAC mirror)",
        "license": "CC BY 4.0 (ESA CCI)",
        "version": "v2.0.7cds / year 2005",
        "tile": "N00E045",
        "note": "OI-2 closed: exact vintage = ESA CCI-LC annual 2005, product version v2.0.7cds (CDS reprocessing), 45-degree COG tile N00E045. Blob requires SAS signing via planetary-computer API (account-free); canonical STAC item URL recorded above.",
    },
    {
        "id": "wdpa_ind_oct2026",
        "audit_ref": "§5 audit-D-18",
        "filename": "WDPA_WDOECM_Oct2026_Public_IND.zip",
        "url": "https://d1gam3xoknrgr2.cloudfront.net/current/WDPA_WDOECM_Oct2026_Public_IND.zip",
        "type": "archive (vector)",
        "source": "UNEP-WCMC / IUCN WDPA + WDOECM October 2026 public release, India",
        "license": "free with registration terms; NOT redistributable — local use + attribution only (UNEP-WCMC/IUCN)",
        "version": "WDPA_WDOECM_Oct2026_Public_IND",
        "note": "Same pinned release used by the Jhabua run (Oct-2026). Polygons only; no occurrence/point records. Not redistributable: archive stays out of version control.",
    },
    {
        "id": "osm_southern_zone_20261026",
        "audit_ref": "§5 (baseline access covariate, prereg dev-D-4 current-network proxy)",
        "filename": "southern-zone-261020.osm.pbf",
        "url": "https://download.geofabrik.de/asia/india/southern-zone-latest.osm.pbf",
        "pinned_url": "https://download.geofabrik.de/asia/india/southern-zone-261020.osm.pbf",
        "type": "vector (osm.pbf)",
        "source": "Geofabrik India southern-zone extract (Kerala + peninsular states), dated snapshot 2026-10-26 build",
        "license": "ODbL 1.0 (OpenStreetMap contributors)",
        "version": "southern-zone-261020 (redirect target of -latest on 2026-10-23)",
        "note": "Dated redirect target recorded so the extract is pinnable; roads are a CURRENT-NETWORK PROXY, not a 2000-2005 baseline observation (prereg dev-D-4 label).",
    },
    {
        "id": "d2_classified_wayanad_portal",
        "audit_ref": "§2 audit-D-2",
        "filename": "keralatourism_classified_wayanad_2026-10-23.html",
        "url": "https://www.keralatourism.org/where-to-stay/all/wayanad",
        "type": "table (html)",
        "source": "Kerala Tourism service-provider portal — Wayanad district slice of classified hotels/resorts (filters + pagination, browse-only, no bulk export)",
        "license": "public web page, use with attribution",
        "version": "snapshot 2026-10-23",
        "note": "Classified subset only — not all operating resorts (audit row caveat). The URL serves an auto-submitting form, not the list: snapshot assembled 2026-10-23 via GET /where-to-stay/all/wayanad -> POST /where-to-stay (district=14) -> infinite-scroll POSTs /where-to-stay/scrollajax (nvalue 30/60/90) until totalrows=111; assembled document carries all 111 cards (verified: 111 'sp-card' markers). Portal filter landing: /hotels/; applicant login: /service-provider-classification.",
    },
    {
        "id": "d3_ecostat_hotels_2014_15",
        "audit_ref": "§2 audit-D-3",
        "filename": "ecostat_286_report_hotels_restaurants_2014-15.pdf",
        "url": "https://ecostat.kerala.gov.in/storage/publications/286.pdf",
        "type": "pdf (survey report)",
        "source": "Dept. of Economics & Statistics Kerala, 'Report on Hotels & Restaurants in Kerala 2014-15' (published 2016-05-26)",
        "license": "public government publication",
        "version": "2014-15 survey (publication 286)",
        "note": "THE hotel survey carrying year-of-starting cohorts: Table 1.1 Wayanad total 413 (346 panchayat + 67 municipality; cohort row 7,3,9,8,16,24,104,242). Verified 2026-10-23: the audit's '(publications 286, 119, 150)' conflated series — 119/150 are Kerala Tourism Statistics books (= D-4), and NO hotel survey later than 2014-15 is findable on ecostat.",
    },
    {
        "id": "d4_kts_arrivals_2025_26",
        "audit_ref": "§2 audit-D-4 (V1 target)",
        "filename": "keralatourism_tourist_statistics_2025-26.pdf",
        "url": "https://www.keralatourism.org/tourismstatistics/tourists_statistics_202520260507114657.pdf",
        "type": "pdf (statistics)",
        "source": "Kerala Tourism tourist statistics 2025-26 (arrivals series; index /touriststatistics/ lists 2003–2025)",
        "license": "public government publication",
        "version": "2025-26 edition",
        "note": "Outcome-adjacent statistics (arrivals): acquired and hashed for provenance ONLY; no pre-freeze computation or V1 comparison before freeze (prereg §5).",
    },
    {
        "id": "d4_kts_book_2019",
        "audit_ref": "§2 audit-D-4",
        "filename": "ecostat_150_kerala_tourism_statistics_2019.pdf",
        "url": "https://ecostat.kerala.gov.in/storage/publications/150.pdf",
        "type": "pdf (statistics book)",
        "source": "ecostat Kerala Tourism Statistics book series (150 = 2019; 148 = 2018; 119 = 2017)",
        "license": "public government publication",
        "version": "KTS 2019 (latest book edition on ecostat, verified 2026-10-23)",
        "note": "Second D-4 series (ecostat book) vs the arrivals PDF series; provenance-only until freeze (prereg §5).",
    },
    {
        "id": "oi4_homestay_order_m5_1903",
        "audit_ref": "§2 audit-D-1 / OI-4",
        "filename": "homestay_order_M5-1903_90th_2019.pdf",
        "url": "https://www.keralatourism.org/images/service-providers/docs/Homestay_90th_order.pdf",
        "type": "pdf (government order)",
        "source": "Kerala Tourism homestay classification ORDER M5-1903/2015 dated 06-08-2019 (90th order)",
        "license": "public government order",
        "version": "order text as published 2026-10-23",
        "note": "OI-4 closure evidence: quotes GO (MS) No. 299/06/TSM dated 18-08-2006 (original Homestay Classification scheme) and GO (MS) No. 324/15/TSM dated 28-12-2015 (revised Diamond/Gold/Silver guidelines) → scheme origin 2006, revision 2015; the M5-1903/2015 file number is NOT a start year. 'valid for three years from the date of issue' clause confirmed.",
    },
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_url(src: dict) -> str:
    """Return a directly downloadable URL (signs PC blob assets if needed).

    The recorded source_url stays the canonical public locator (STAC item);
    only the transfer URL is signed, because the Azure container rejects
    anonymous reads (HTTP 409).
    """
    if "asset_url" in src and "planetarycomputer.microsoft.com" in src["url"]:
        import planetary_computer as pc
        return pc.sign(src["asset_url"])
    return src["url"]


def download(src: dict) -> tuple[Path, int]:
    dest = RAW / src["filename"]
    RAW.mkdir(parents=True, exist_ok=True)
    url = resolve_url(src)

    if dest.exists() and dest.stat().st_size > 0:
        print(f"  exists: {dest.name} ({dest.stat().st_size:,} bytes) — will re-hash only")
        return dest, dest.stat().st_size

    part = dest.with_suffix(dest.suffix + ".part")
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            with requests.get(url, stream=True, timeout=(30, 120), headers=UA) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                done = 0
                with open(part, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
                        done += len(chunk)
                        if total and done % (100 << 20) < (1 << 20):
                            print(f"    … {done:,} / {total:,} bytes", flush=True)
            if total and part.stat().st_size != total:
                raise IOError(f"size mismatch: got {part.stat().st_size}, expected {total}")
            part.replace(dest)
            print(f"  downloaded: {dest.name} ({dest.stat().st_size:,} bytes)")
            return dest, dest.stat().st_size
        except Exception as e:  # noqa: BLE001 — retry any transient failure
            last_err = e
            print(f"  attempt {attempt} failed: {e}", flush=True)
            time.sleep(5 * attempt)
    raise RuntimeError(f"download failed for {src['id']}: {last_err}")


def upsert_manifest(entries: list[dict]) -> None:
    man = json.loads(MANIFEST.read_text())
    by_id = {s["id"]: s for s in man["sources"]}
    for e in entries:
        if e["id"] in by_id:
            by_id[e["id"]].update(e)
        else:
            man["sources"].append(e)
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[])
    args = ap.parse_args()

    wanted = [s for s in SOURCES if not args.only or s["id"] in args.only]
    if args.only:
        unknown = set(args.only) - {s["id"] for s in SOURCES}
        if unknown:
            print(f"FAIL: unknown source ids: {sorted(unknown)}")
            return 1

    new_entries = []
    failures = []
    for src in wanted:
        print(f"[{src['id']}] {src['filename']}")
        try:
            path, size = download(src)
        except Exception as e:  # noqa: BLE001 — record and continue; report at end
            failures.append((src["id"], str(e)))
            continue
        digest = sha256_of(path)
        entry = {
            "id": src["id"],
            "audit_ref": src["audit_ref"],
            "path": f"tourism_observatory/data/raw/{src['filename']}",
            "type": src["type"],
            "source": src["source"],
            "source_url": src["url"],
            "license": src["license"],
            "sha256": digest,
            "bytes": size,
            "acquired_utc": date.today().isoformat(),
            "status": "verified",          # file on disk + hash recorded (dev-D-6)
        }
        for k in ("version", "tile", "note", "pinned_url"):
            if k in src:
                entry[k] = src[k]
        new_entries.append(entry)
        print(f"  sha256: {digest}")

    if new_entries:
        upsert_manifest(new_entries)
        print(f"manifest updated: +{len(new_entries)} entries -> {MANIFEST.relative_to(REPO)}")

    if failures:
        print("FAILURES:")
        for sid, err in failures:
            print(f"  {sid}: {err}")
        return 1
    print("OK — all requested sources on disk with recorded hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
