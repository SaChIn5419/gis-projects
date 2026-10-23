"""P1 ingest — Kerala Tourism approved-homestay registry (tourism_observatory).

Opens the actual downloaded HTML snapshot (dev-D-6 rule), parses the embedded table,
verifies expected columns, extracts the Wayanad subset, and reports QA facts.
No outcome analysis — facility existence/registry only (prereg §5).
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "keralatourism_approved_homestays_2026-10-22.html"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "registry_homestays_wayanad_2026-10-22.csv"


def main() -> int:
    if not RAW.exists() or RAW.stat().st_size < 100_000:
        print(f"FAIL: raw file missing or implausibly small: {RAW}")
        return 1

    tables = pd.read_html(RAW, header=None)
    if not tables:
        print("FAIL: no tables parsed")
        return 1

    # Registry table: the wide state-wide table (no <th> header row — titles are inside
    # <td class="sub_heading">, so pandas returns integer column names). Its first data
    # row is the column-label row; verify that before anything else.
    reg = None
    for t in tables:
        if len(t) > 50:
            reg = t
            break
    if reg is None:
        print(f"FAIL: registry table not found; table sizes={[len(t) for t in tables]}")
        return 1

    expected_labels = ["#", "name & address", "district", "contact info", "approved as",
                       "order number", "valid upto"]
    first = [str(v).strip().lower() for v in reg.iloc[0]]
    ok = sum(any(e in c for c in first) for e in expected_labels)
    if ok < 5:
        print(f"FAIL: header row not pattern-matched: {first}")
        return 1
    reg = reg.iloc[1:].reset_index(drop=True)
    reg.columns = ["sl", "name_address", "district", "contact", "approved_as",
                   "order_date", "valid_upto"]
    if not len(reg):
        print("FAIL: empty registry after header removal")
        return 1

    n_total = len(reg)
    dist_counts = reg["district"].astype(str).str.strip().value_counts()
    wdf = reg[reg["district"].astype(str).str.strip().str.lower() == "wayanad"].copy()

    # Duplicate-detection (relevant for H4/H1 counting discipline: no silent double rows)
    dup_names = wdf["name_address"].duplicated().sum()

    print(f"total homestay rows (all Kerala) : {n_total}")
    print(f"Wayanad rows                     : {len(wdf)}")
    print(f"district coverage                : {reg['district'].nunique()} districts")
    print(f"top 5 districts by rows          : {dict(dist_counts.head(5))}")
    print(f"Wayanad duplicate name rows      : {dup_names}")
    print("top Wayanad names:")
    for nm in wdf["name_address"].head(8):
        print(f"  - {str(nm).split(chr(10))[0][:70]}")

    # Approval-date sanity: the order_date strings carry the latest approval order date.
    years = pd.to_datetime(wdf["order_date"].astype(str)
                           .str.extract(r"dated (\d{2}-\d{2}-(\d{4}))", expand=False)[1],
                           format="%Y", errors="coerce")
    print(f"Wayanad approval-order years     : min={years.min():.0f} max={years.max():.0f} "
          f"(order dates = latest approval, NOT construction — dev-D-4 note)")

    wdf.to_csv(OUT, index=False)
    print(f"written: {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
