#!/usr/bin/env python3
"""P2 placebo arm: extract OSM POI points (amenity/shop/building/tourism) from the
southern-zone .osm.pbf (GEOFABRIK), project to EPSG:32643, and count POI presence within
500 m of each matched Wayanad parcel (treated vs control). Output: wayanad_placebo_poi.csv,
placebo_summary.csv.

Reads from: data/raw/southern-zone-261020.osm.pbf  (GEOFABRIK southern India)
Writes to: data/processed/wayanad_placebo_poi.csv, data/processed/placebo_summary.csv
"""
import json, math, os, re, ctypes
import pandas as pd
from osgeo import ogr, osr

BND = 'data/raw/southern-zone-261020.osm.pbf'
OUT_POI = 'data/processed/wayanad_placebo_poi.csv'
OUT_SUM = 'data/processed/placebo_summary.csv'

mp = pd.read_csv('data/processed/matched_pairs_2026-10-26.csv')
tids = set(mp['treated']); cid = set(mp['control'])

ds = ogr.Open(BND)
layer = ds.GetLayer('points')

src = osr.SpatialReference(); src.ImportFromEPSG(4326)
dst = osr.SpatialReference(); dst.ImportFromEPSG(32643)
ct = osr.CoordinateTransformation(src, dst)
from pyproj import Transformer
_proj = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)

def classify(ot):
    tags = {}
    if not ot:
        return tags
    for m in re.finditer(r'"([a-z0-9_]+)"\s*=>\s*"([^"]*)"', str(ot)):
        tags[m.group(1)] = m.group(2)
    return tags

rows = []
count = 0
for feat in layer:
    ot = feat.GetField('other_tags')
    tags = classify(ot)
    if not tags:
        continue
    if not (tags.get('tourism') or tags.get('amenity') or tags.get('shop') or tags.get('office')):
        continue
    geom = feat.GetGeometryRef()
    if geom is None:
        continue
    lon, lat = geom.GetX(0), geom.GetY(0)
    # pyproj transformer EPSG:4364 -> EPSG:32643 (always_xy: lon, lat -> easting, northing)
    x, y = _proj.transform(float(lon), float(lat))
    rows.append({'x32643': x, 'y32643': y,
                 'amenity': tags.get('amenity'),
                 'shop': tags.get('shop'),
                 'tourism': tags.get('tourism'),
                 'office': tags.get('office'),
                 'name': str(feat.GetField('name'))})
    count += 1
    if count % 50000 == 0:
        print('  streamed', count)

print('total POI points:', count)
if rows:
    pd.DataFrame(rows).to_csv(OUT_POI, index=False)
    print('saved', OUT_POI, pd.DataFrame(rows).shape)
else:
    print('no POI rows found')
