"""P2 step (b1) — parse D-2 classified registry (111 cards) + enrich from detail pages.

Preregistered rule (§2): treatment sourcing must geocode BOTH the approved-homestay
list (done in P1: registry_homestays_wayanad_2026-10-22.csv, 51 rows) AND "the
department's accommodation registry by district" = the D-2 classified service-provider
portal snapshot (keralatourism_classified_wayanad_2026-10-23.html, 111 sp-card blocks).

Steps:
  1. Split the assembled snapshot on '<div class="sp-card">' → name, address span,
     category, detail URL + property id.
  2. GET each detail page (polite 0.4 s pacing, 3 retries) and extract the JSON-LD
     PostalAddress (street/locality/region/postcode), telephone, and geo coords if the
     page ever exposes them. Raw HTML is NOT retained (payload); the extracted
     structured fields go to a tracked JSON.
  3. Write registry_classified_wayanad_<date>.csv with a unified name_address field
     for the geocoder (street > locality > card span, joined).

No geocoding and no imagery in this step. Existence verification and treatment
labels follow in later steps; no outcome data is touched (prereg §5).

Usage:  python scripts/p2_classified_registry.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
SNAPSHOT = RAW / "keralatourism_classified_wayanad_2026-10-23.html"
UA = {"User-Agent": "tourism-observatory-p2/0.1 (research; non-commercial)"}
SLEEP = 0.4


def parse_cards(html: str) -> list[dict]:
    parts = html.split('<div class="sp-card">')[1:]
    cards = []
    for seg in parts:
        seg = seg[:4000]
        cat = re.search(r'sp-cat[^>]*>([^<]+)<', seg)
        href = re.search(r'<a href="([^"]+)"', seg)
        name = re.search(r'<h3>(.*?)</h3>', seg, re.S)
        addr = re.search(r'</h3>\s*<span>(.*?)</span>', seg, re.S)
        if not (name and href):
            continue
        cards.append({
            "category": (cat.group(1).strip() if cat else None),
            "detail_url": href.group(1),
            "property_id": (m.group(1) if (m := re.search(r"/(\d+)$", href.group(1))) else None),
            "name": re.sub(r"\s+", " ", name.group(1)).strip(),
            "address_span": (re.sub(r"\s+", " ", addr.group(1)).strip()
                             if addr else None),
        })
    return cards


def get_jsonld(page: str) -> dict | None:
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                         page, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and (
                    "PostalAddress" in json.dumps(it.get("address", ""))
                    or it.get("@type") in ("LocalBusiness", "Hotel", "Resort",
                                           "LodgingBusiness", "Organization")):
                return it
    return None


def main() -> int:
    if not SNAPSHOT.exists():
        print(f"FAIL: missing {SNAPSHOT.relative_to(ROOT)}")
        return 1
    html = SNAPSHOT.read_text(errors="ignore")
    cards = parse_cards(html)
    print(f"cards parsed: {len(cards)}")
    if len(cards) != 111:
        print("FAIL: expected 111 sp-card blocks (P1-verified count)")
        return 1

    details, failures = {}, []
    for i, c in enumerate(cards, 1):
        ld = None
        for attempt in range(1, 4):
            try:
                r = requests.get(c["detail_url"], headers=UA, timeout=30)
                r.raise_for_status()
                ld = get_jsonld(r.text)
                break
            except requests.RequestException as e:
                if attempt == 3:
                    failures.append((c["property_id"], str(e)))
                time.sleep(2 * attempt)
        time.sleep(SLEEP)
        addr = (ld or {}).get("address") or {}
        geo = (ld or {}).get("geo") or {}
        details[c["property_id"]] = {
            "detail_ok": ld is not None,
            "streetAddress": addr.get("streetAddress"),
            "addressLocality": addr.get("addressLocality"),
            "addressRegion": addr.get("addressRegion"),
            "postalCode": addr.get("postalCode"),
            "telephone": (ld or {}).get("telephone"),
            "geo": geo or None,
        }
        if i % 20 == 0:
            print(f"  {i}/{len(cards)} detail pages fetched", flush=True)

    today = date.today().isoformat()
    rows = []
    for n, c in enumerate(cards, 1):
        d = details.get(c["property_id"], {})
        loc = d.get("addressLocality") or ""
        street = (d.get("streetAddress") or "").strip().strip(",") or ""
        span = c["address_span"] or ""
        # unified geocoder text: street + locality (detail) + card span fallback
        bits = [x for x in dict.fromkeys([street, loc, span]) if x and x != ","]
        name_address = ", ".join(bits) if bits else c["name"]
        rows.append({
            "sl": f"c{n:03d}",
            "source": "D2_classified",
            "name": c["name"],
            "name_address": name_address,
            "category": c["category"],
            "address_span": span,
            "streetAddress": street,
            "addressLocality": loc,
            "postalCode": d.get("postalCode"),
            "telephone": d.get("telephone"),
            "detail_url": c["detail_url"],
            "property_id": c["property_id"],
            "detail_ok": d.get("detail_ok", False),
            "has_geo_field": bool(d.get("geo")),
        })
    df = pd.DataFrame(rows)
    out = PROC / f"registry_classified_wayanad_{today}.csv"
    df.to_csv(out, index=False)
    (PROC / f"classified_details_{today}.json").write_text(
        json.dumps(details, indent=1) + "\n")

    print(f"\nrows: {len(df)}; detail_ok: {int(df.detail_ok.sum())}; "
          f"geo field: {int(df.has_geo_field.sum())}; "
          f"street: {int((df.streetAddress != '').sum())}; "
          f"locality: {int((df.addressLocality != '').sum())}; "
          f"pin: {int(df.postalCode.notna().sum())}")
    print("categories:", df.category.value_counts().to_dict())
    if failures:
        print("detail failures:", failures)
    print(f"csv: {out.relative_to(ROOT)}")
    if len(df) != 111:
        print("FAIL: row count != 111")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
