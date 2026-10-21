#!/usr/bin/env python3
"""One-command entry point for the Jhabua agroforestry land screening.

Usage:
    python run_pipeline.py                         # validate config/jhabua.yaml and print the plan
    python run_pipeline.py config/jhabua.yaml
    python run_pipeline.py config/jhabua.yaml --run

`--run` executes: ingest -> QA gate -> screening. Without it, the script only
validates the configuration and prints what would run, which is safe before the
raw layers exist.

The pipeline is deliberately config-driven. If a key is missing, this script
stops before any module runs, so a typo cannot silently drop a rule.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


REQUIRED = {
    "project": ["name", "district", "start_year", "eligibility_mode", "boundary"],
    "methodology": ["standard", "version", "source_pdf_sha256"],
    "grid": ["crs", "resolution_m"],
    "paths": ["aligned_dir", "output_dir", "layers", "sources"],
    "screening": ["stage_a_order", "stage_b_order", "clause_refs", "woody", "design_screens"],
    "qa": ["reference_area_km2", "area_tolerance_pct"],
}


def validate_shape(cfg: dict) -> list[str]:
    missing = []
    for section, keys in REQUIRED.items():
        if section not in cfg:
            missing.append(f"{section} (section missing)")
            continue
        for key in keys:
            if key not in cfg[section]:
                missing.append(f"{section}.{key}")
    return missing


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Jhabua screening pipeline")
    parser.add_argument("config", nargs="?", default="config/jhabua.yaml")
    parser.add_argument("--run", action="store_true", help="run ingest -> qaqc -> screening")
    args = parser.parse_args(argv)

    path = Path(args.config)
    if not path.exists():
        print(f"FATAL: config not found: {path}")
        return 1
    try:
        cfg = load_config(path)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: cannot load config {path}: {exc}")
        return 1

    missing = validate_shape(cfg)
    if missing:
        print("FATAL: config missing keys: " + ", ".join(missing))
        return 1

    mode = cfg["project"]["eligibility_mode"]
    print(f"config OK: {cfg['project']['name']} ({cfg['project']['district']})")
    print(f"  eligibility_mode = {mode}")
    print(f"  grid             = {cfg['grid']['crs']} @ {cfg['grid']['resolution_m']} m")
    print(f"  aligned layers   = {cfg['paths']['aligned_dir']}")
    print(f"  reference area   = {cfg['qa']['reference_area_km2']} km2")
    print("  plan: ingest -> qaqc -> screening -> scoring -> sensitivity -> validation -> maps")
    if mode == "area":
        print("FATAL: area mode is intentionally disabled until §1.1/§4.4.1 evidence exists.")
        return 1

    if not args.run:
        print("  (validation only; add --run to execute ingest -> qaqc -> screening)")
        return 0

    # Import after validation so a bad config produces a readable error first.
    from src import ingest, qaqc, screening

    print("\n[1/3] ingest")
    rc = ingest.main([str(path)])
    if rc != 0:
        print("pipeline stopped at ingest")
        return rc

    print("\n[2/3] QA/QC gate")
    rc = qaqc.main(["--check", str(path)])
    if rc != 0:
        print("pipeline stopped at QA/QC gate")
        return rc

    print("\n[3/3] screening")
    screening.main([str(path)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
