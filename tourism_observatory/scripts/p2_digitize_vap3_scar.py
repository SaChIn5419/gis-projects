"""P2 step (b3) — digitize the 2024 Chooralmala–Mundakkai debris-flow extent from
the NRSC/ISRO VAP3 impact map (Charter Call 1029, AOI 01, observed 31/07/2024).

Replaces the v1 centerline corridor (digitized from PMC12290006 Fig. 1), which QA
showed sat ~2 km NORTH of the published crown: VAP3's legend gives the crown
exactly — 76°8'10.58"E, 11°28'0.347"N — and the published debris-flow outline runs
~8 km NE from there (crown → Punchiri Mattam → Mundakkai → Chooralmala →
Vellarimala). v1 overlapped the corrected extent by 0.000 km².

METHOD (logged; §4.4 needs the disturbed zone out of BOTH arms, so a corridor that
faithfully follows the published path is the target):
  1. Render the VAP3 A1 sheet at 200 dpi (pdftoppm) and crop the main SAR panel.
  2. Georeference from the map itself: left-margin graticule ticks (1' spacing,
     fitted; max |residual| < 1 px) for latitude; the green "Landslide location"
     dot (legend DMS) as the longitude anchor; px/arcsec lon = px/arcsec lat *
     cos(lat). Validation: the fitted latitude of the green dot must land within
     0.0005° (~55 m) of the legend value — asserted, not assumed.
  3. Extract the published yellow Debris Flow outline (RGB threshold) inside the
     panel frame.
  4. Remove inset-box borders: delete only the long (>100 px) strictly horizontal
     / vertical runs (the flow rails are diagonal, so they never produce such
     runs; boxes are axis-aligned rectangles).
  5. Bridge remaining gaps (morphological closing), skeletonize, take the graph
     diameter (longest shortest path = crown→Vellarimala channel; box borders
     are short spurs and lose), extend the two path tips linearly to the band's
     crown lobe and NE tip (the diameter cuts across small end loops).
  6. Smooth the centerline (15 px moving average) and buffer **150 m** flat-cap
     corridor (§4.4 exclusion; deliberately conservative, logged in D-12).

OUTPUT: data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg (EPSG:32643)
        outputs/qaqc/p2_scar_digitization_qa.json  (calibration + geometry facts)
        outputs/qaqc/p2_scar_digitization_overlay.png (visual QA on the source map)

Information boundary (§5): an exclusion mask only — no outcome is computed here.

Usage:  python scripts/p2_digitize_vap3_scar.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
from scipy import ndimage as ndi
from shapely.geometry import LineString, Polygon
from shapely.ops import transform as shp_transform
from skimage.morphology import skeletonize
from collections import deque

ROOT = Path(__file__).resolve().parents[1]
VAP3_PDF = ROOT / "data/raw/staging_d5d6/NRSC_Landslide_Impact_Map_Chooralmala_VAP3_31july2024.pdf"
OUT_GPKG = ROOT / "data/processed/scar_chooralmala_mundakkai_2024_32643.gpkg"
OUT_QA = ROOT / "outputs/qaqc/p2_scar_digitization_qa.json"
OUT_OVERLAY = ROOT / "outputs/qaqc/p2_scar_digitization_overlay.png"

WORK = Path("/tmp/p2_scar_digitize")
BUFFER_HALF_M = 150.0

# Legend anchors (DMS on the map sheet)
CROWN_LAT = 11 + 28 / 60 + 0.347 / 3600     # 11°28'0.347"N
CROWN_LON = 76 + 8 / 60 + 10.58 / 3600      # 76°8'10.58"E


def group(pos, gap=8):
    out, cur = [], [pos[0]]
    for p in pos[1:]:
        if p - cur[-1] <= gap:
            cur.append(p)
        else:
            out.append(sum(cur) / len(cur))
            cur = [p]
    out.append(sum(cur) / len(cur))
    return out


def main() -> int:
    if not VAP3_PDF.exists():
        print(f"FAIL: {VAP3_PDF} missing")
        return 1
    WORK.mkdir(parents=True, exist_ok=True)

    # ---- 1. render + crop main panel --------------------------------------
    png = WORK / "vap3hi-1.png"
    if not png.exists():
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-f", "1", "-l", "1",
                        str(VAP3_PDF), str(WORK / "vap3hi")], check=True)
    panel_png = WORK / "mainpanel.png"
    if not panel_png.exists():
        subprocess.run(["convert", str(png), "-crop", "42%x100%+0+0", "+repage",
                        str(panel_png)], check=True)
    a = np.asarray(Image.open(panel_png).convert("RGB"))
    H, W, _ = a.shape
    dark = a.sum(axis=2) < 250

    # ---- 2a. frame + latitude ticks ---------------------------------------
    rows = dark[:200, :].sum(axis=1)
    Y0 = int(rows.argmax())
    cols = dark[Y0 + 5:, :300].sum(axis=0)
    X0 = int(cols.argmax())
    col_x0 = dark[Y0:, X0]
    Y1 = int(np.where(col_x0)[0].max()) + Y0
    top = dark[Y0]
    X1 = int(np.where(top)[0].max())
    band = dark[:, X0 - 40:X0 - 3]
    tr = band.sum(axis=1)
    ticks = group([y for y in range(H) if tr[y] >= 15])
    print(f"frame: X0={X0} Y0={Y0} X1={X1} Y1={Y1}; lat ticks px={ticks}")
    if len(ticks) != 4:
        print(f"FAIL: expected 4 latitude ticks, found {len(ticks)}")
        return 1
    # choose the 1'-spacing assignment (31/30/29/28 N) that best fits the green dot
    r, g_, b_ = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    green = (g_ > 140) & (r < 120) & (b_ < 120) & (g_ - r > 60)
    lab_g, n_g = ndi.label(green)
    sizes_g = ndi.sum(green, lab_g, range(1, n_g + 1))
    gi = int(np.argmax(sizes_g)) + 1
    gy, gx = np.where(lab_g == gi)
    xg, yg = float(gx.mean()), float(gy.mean())
    best = None
    for top_arcmin in (31, 30, 29):           # possible top tick = 31'/30'/29'N
        top_deg = 11 + top_arcmin / 60
        lat_t = np.array([top_deg - k / 60 for k in range(4)])
        cl, bl = np.polyfit(lat_t, np.array(ticks), 1)
        pred = (yg - bl) / cl
        err = abs(pred - CROWN_LAT)
        if best is None or err < best[0]:
            best = (err, cl, bl, top_arcmin, pred)
    err, clat, blat, top_min, pred = best
    if err > 0.0005:
        print(f"FAIL: green-dot lat check {err:.6f}° > 0.0005°")
        return 1
    px_arcsec_lat = clat / 3600.0
    px_arcsec_lon = px_arcsec_lat * np.cos(np.deg2rad(CROWN_LAT))
    print(f"lat fit (top tick {top_min:.2f}N): green dot lat {pred:.6f} "
          f"(legend {CROWN_LAT:.6f}), err {err*111000:.1f} m  OK")

    def px2ll(x, y):
        return (CROWN_LON + (x - xg) / (px_arcsec_lon * 3600.0),
                (y - blat) / clat)

    def ll2px(lon, lat):
        return (xg + (lon - CROWN_LON) * (px_arcsec_lon * 3600.0),
                clat * lat + blat)

    # ---- 3. yellow debris-flow outline ------------------------------------
    yellow = (r > 130) & (g_ > 105) & (r - b_ > 50) & (r >= g_ - 10)
    frame = np.zeros_like(yellow)
    frame[Y0 + 1:Y1, X0 + 1:X1] = True
    yellow &= frame
    lab_y, n_y = ndi.label(yellow)
    sizes_y = ndi.sum(yellow, lab_y, range(1, n_y + 1))
    cid = int(np.argmax(sizes_y)) + 1
    band_px = lab_y == cid
    print(f"yellow comps={n_y}; flow outline comp={cid} px={int(band_px.sum())}")

    # ---- 4. remove inset-box borders (long axis-aligned runs) -------------
    b = band_px.copy()
    removed = 0

    def runs1d(v, thr=100):
        d = np.diff(np.concatenate(([0], v.astype(np.int8), [0])))
        st, en = np.where(d == 1)[0], np.where(d == -1)[0]
        return [(s, e) for s, e in zip(st, en) if e - s >= thr]

    for y in range(H):
        for s, e in runs1d(b[y]):
            b[y, s:e] = False
            removed += e - s
    for x in range(W):
        for s, e in runs1d(b[:, x]):
            b[s:e, x] = False
            removed += e - s
    print(f"removed {removed} px of axis-aligned runs ({100*removed/band_px.sum():.1f}%)")

    # ---- 5. bridge, skeletonize, graph-diameter centerline -----------------
    bd = ndi.binary_closing(b, structure=np.ones((3, 3), bool), iterations=4)
    lb, n_c = ndi.label(bd, structure=np.ones((3, 3), bool))
    sz = ndi.sum(bd, lb, range(1, n_c + 1))
    core = np.isin(lb, [i + 1 for i in range(n_c) if sz[i] >= 500])
    sk = skeletonize(core)
    pts = np.argwhere(sk)
    idx = {tuple(p): i for i, p in enumerate(pts)}
    N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    adj: list[list[int]] = [[] for _ in range(len(pts))]
    for i, (y, x) in enumerate(pts):
        for dy, dx in N8:
            j = idx.get((y + dy, x + dx))
            if j is not None:
                adj[i].append(j)

    def bfs(s):
        d = np.full(len(pts), -1)
        d[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if d[v] < 0:
                    d[v] = d[u] + 1
                    q.append(v)
        return d

    # The skeleton keeps short box-border spurs, so the graph *diameter* can land
    # on two spur ends (observed: a mid-panel segment, missing the crown entirely).
    # The real flow path is crown -> north-east tip. Pick it explicitly: start the
    # walk at the endpoint closest to the legend crown, walk to the farthest
    # reachable node, then prune any branch that forks off that main stem.
    deg = np.array([len(adj[i]) for i in range(len(pts))])
    ends = np.where(deg == 1)[0]
    crown_px_y = clat * CROWN_LAT + blat          # crown row in panel pixels
    start = int(ends[np.argmin([abs(pts[e][0] - crown_px_y) for e in ends])])
    print(f"crown row y={crown_px_y:.0f}; skeleton endpoints={len(ends)}; "
          f"start={tuple(pts[start])}")

    dist = np.full(len(pts), -1)
    par = np.full(len(pts), -1)
    dist[start] = 0
    q = deque([start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                par[v] = u
                q.append(v)
    goal = int(np.argmax(dist))
    path = []
    u = goal
    while u != -1:
        path.append(tuple(pts[u]))
        u = par[u]
    onpath = set(path)
    print(f"crown->tip path {len(path)} px ({100*len(path)/len(pts):.0f}% of skeleton), "
          f"y[{min(p[0] for p in path)}..{max(p[0] for p in path)}]")

    parr = np.array([[x, y] for y, x in path], dtype=float)

    k = 15
    pad = np.pad(parr, ((k // 2, k // 2), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, c], np.ones(k) / k, mode="valid") for c in (0, 1)], axis=1)

    # ---- 6. buffer corridor -----------------------------------------------
    tf = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    line_ll = LineString([px2ll(x, y) for x, y in sm])
    line_utm = shp_transform(lambda X, Y: tf.transform(X, Y), line_ll)
    corridor = line_utm.buffer(BUFFER_HALF_M, cap_style=2, join_style=2)
    bx = corridor.bounds
    print(f"corridor: centerline {line_utm.length:.0f} m, area {corridor.area/1e6:.3f} km², "
          f"extent {bx[2]-bx[0]:.0f}x{bx[3]-bx[1]:.0f} m")

    gdf = gpd.GeoDataFrame(
        {"event": ["chooralmala_mundakkai_2024"],
         "source": ["NRSC VAP3 Charter Call 1029 (31/07/2024), Debris Flow outline"],
         "method": [f"georeferenced-by-graticule digitization; centerline buffer "
                    f"{int(BUFFER_HALF_M)} m"],
         "centerline_len_m": [round(line_utm.length, 1)],
         "area_km2": [round(corridor.area / 1e6, 3)],
         "compiled_on": [date.today().isoformat()]},
        geometry=[corridor], crs="EPSG:32643")
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    gdf.to_file(OUT_GPKG, layer="scar", driver="GPKG")
    print(f"-> {OUT_GPKG.relative_to(ROOT)}")

    # ---- QA facts + overlay ------------------------------------------------
    crow_px = ll2px(CROWN_LON, CROWN_LAT)
    from shapely.geometry import Point
    crown_utm = Point(tf.transform(CROWN_LON, CROWN_LAT))
    crown_inside = corridor.contains(crown_utm)
    qa = {
        "source_pdf": str(VAP3_PDF.relative_to(ROOT)),
        "panel_px": [W, H],
        "frame_px": [X0, Y0, X1, Y1],
        "lat_ticks_px": ticks,
        "lat_top_tick_arcmin": top_min,
        "green_dot_px": [round(xg, 1), round(yg, 1)],
        "green_dot_lat_pred_vs_legend_deg": [round(pred, 6), round(CROWN_LAT, 6)],
        "green_dot_lat_err_m": round(err * 111000, 1),
        "px_per_arcsec": [round(px_arcsec_lat, 4), round(px_arcsec_lon, 4)],
        "m_per_px": round(30.87 / px_arcsec_lat, 3),
        "flow_outline_px": int(band_px.sum()),
        "axis_run_px_removed": int(removed),
        "skeleton_px": int(len(pts)),
        "centerline_px": int(len(parr)),
        "centerline_len_m": round(line_utm.length, 1),
        "corridor_area_km2": round(corridor.area / 1e6, 3),
        "buffer_half_m": BUFFER_HALF_M,
        "crown_inside_corridor": bool(crown_inside),
        "date": date.today().isoformat(),
        "note": "D-12 correction of v1 (PMC Fig.1 centerline), which sat ~2 km N "
                "of the published crown and overlapped this extent by 0.000 km².",
    }
    OUT_QA.write_text(json.dumps(qa, indent=1) + "\n")

    img = Image.open(panel_png).convert("RGB")
    img = img.resize((img.width // 4, img.height // 4))
    dr = ImageDraw.Draw(img)
    s = 0.25
    inv = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    ring = [ll2px(*inv.transform(X, Y)) for X, Y in corridor.exterior.coords]
    dr.line([(x * s, y * s) for x, y in ring] + [(ring[0][0] * s, ring[0][1] * s)],
            fill=(255, 0, 0), width=3)
    dr.ellipse([crow_px[0] * s - 4, crow_px[1] * s - 4, crow_px[0] * s + 4,
                crow_px[1] * s + 4], outline=(0, 255, 0), width=2)
    img.save(OUT_OVERLAY)
    print(f"-> {OUT_QA.relative_to(ROOT)}, {OUT_OVERLAY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
