#!/usr/bin/env python3
"""P2 placebo summary: count OSM POI points within 500 m of each treated/control matched
parcel and produce a treated-vs-control comparison table for the placebo arm.

Inputs:
  data/processed/parcels_1km_32643.gpkg      - 1km equal-area parcel polygons (EPSG:32643)
  data/processed/matched_pairs_2026-10-26.csv - 50 treated / 50 control matched pairs
  data/processed/wayanad_placebo_poi.csv    - OSM POI points projected to EPSG:32643

Writes: data/processed/placebo_summary.csv
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

PROC = 'data/processed'
PAIR = f'{PROC}/matched_pairs_2026-10-26.csv'
POI = f'{PROC}/wayanad_placebo_poi.csv'
PARCELS = f'{PROC}/parcels_1km_32643.gpkg'
OUT = f'{PROC}/placebo_summary.csv'

CENTER_RADIUS_M = 500.0

parcels = gpd.read_file(PARCELS)
mp = pd.read_csv(PAIR)
matched = parcels[parcels['parcel_id'].isin(set(mp['treated']) | set(mp['control']))].copy()
matched['arm'] = np.where(matched['parcel_id'].isin(set(mp['treated'])), 'treated', 'control')
print('matched treated/control parcels:', (matched['arm'] == 'treated').sum(), '/', (matched['arm'] == 'control').sum())

pois = gpd.GeoDataFrame(
    pd.read_csv(f'{PROC}/wayanad_placebo_poi.csv'),
    geometry=gpd.points_from_xy(pd.read_csv(f'{PROC}/wayanad_placebo_poi.csv', usecols=['x32643', 'y32643']), crs='EPSG:32643'),
    crs='EPSG:32643')

rows = []
for _, p in matched.iterrows():
    buf = p.geometry.buffer(500.0)
    cnt = pois.geometry.within(buf).sum()
    rows.append({'parcel_id': p['parcel_id'], 'arm': p['arm'], 'poi_within_500m': int(cnt)})

summ = pd.DataFrame(rows)
summary = summ.groupby('arm')['poi_within_500m'].agg(['count', 'sum', 'mean']).reset_index()
summary.to_csv(OUT, index=False)
print('placebo_summary.csv written')
print(summary.to_string(index=False))

t = summary[summary['arm'] == 'treated']['sum'].iloc[0]
c = summary[summary['arm'] == 'control']['sum'].iloc[0]
print(f'\nMean POI within 500m - treated: {summary[summary["arm"]=="treated"]["mean"].iloc[0]:.2f} | control: {summary[summary["arm"]=="control"]["mean"].iloc[0]:.2f}')
print(f'Total POI within 500m - treated: {t} | control: {c}')
