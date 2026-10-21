"""Jhabua Agroforestry Land Screening - package marker.

Current modules:
  ingest.py      raw sources -> one aligned 30 m stack + provenance manifest
  qaqc.py        measure the real rasters; stop on critical failures
  screening.py   two-stage waterfall + per-pixel reason codes
  scoring.py     weighted suitability overlay (next)
  sensitivity.py scenario runs + stability score (next)
  validation.py  stratified sampling + confusion matrix + CI (next)
  report.py      maps, tables, exports (next)

Run from the repository root:
  python run_pipeline.py config/jhabua.yaml
"""
