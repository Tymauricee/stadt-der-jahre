"""Erzeugt vereinfachte Küstenlinien (Natural Earth 1:50m) für zwei Kartenausschnitte
und projiziert schematische Strömungen/Wege, Ausgabe als JSON für die Ausstellungsseite.

Makes the two maps of the conclusion scenes (maps.json). Only needed if you change
the map areas or the drawn currents and fish routes.
  1. Download ne_50m_land.geojson (Natural Earth, public domain), e.g. from
     https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_50m_land.geojson
     and put it next to this script.
  2. pip install shapely
  3. python make_maps.py   ->  maps.json, then python build.py
"""
import json, math, pathlib
from shapely.geometry import shape, box, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).parent
land = json.load(open(HERE / 'ne_50m_land.geojson'))
geoms = [shape(f['geometry']) for f in land['features']]

MAPS = {
    # Ausschnitt (lon0, lat0, lon1, lat1), Breite in px
    'jp': dict(bbox=(124.0, 30.0, 147.5, 47.0), W=620),
    'eu': dict(bbox=(-24.0, 44.0, 15.0, 65.0), W=620),
}

# schematische Linien (lon, lat) – Strömungen und Wanderwege
LINES = {
    'jp': {
        'kuroshio': [(125.6,30.0),(128.0,30.2),(130.4,30.4),(132.2,31.4),(134.4,32.4),(136.8,33.1),(139.0,33.9),(140.6,34.5),(142.2,35.3),(144.6,35.9),(147.4,36.2)],
        'tsushima': [(127.6,30.3),(128.2,32.0),(129.2,33.8),(130.5,35.1),(132.3,36.1),(134.3,36.6),(136.0,37.4),(137.4,38.3),(138.6,39.3),(139.2,40.3),(139.5,41.1),(140.3,41.5),(141.4,41.55),(143.0,41.7)],
        'soya':     [(139.5,41.1),(139.3,42.4),(140.3,43.6),(141.2,44.8),(141.8,45.65),(143.0,45.5)],
        'buri':     [(129.4,34.4),(131.8,36.3),(135.2,37.4),(137.8,38.9),(138.9,40.6),(139.1,42.4),(140.6,44.2)],
    },
    'eu': {
        'atlantic': [(-24.0,50.0),(-17.0,53.0),(-11.5,56.5),(-6.5,59.6),(-3.6,60.7),(0.4,60.1),(1.6,58.0),(2.8,56.2),(4.6,54.9),(6.8,55.4),(7.6,57.4),(5.4,58.0),(4.4,59.6),(4.6,61.4),(6.2,62.9),(8.6,64.2)],
        'channel':  [(-8.0,48.4),(-4.5,49.6),(-1.0,50.2),(1.4,50.9),(2.8,52.2),(4.0,53.6)],
        'mackerel': [(-9.5,47.0),(-12.5,52.0),(-13.0,56.5),(-10.5,60.5),(-12.5,63.0)],
        'sardine':  [(-6.0,46.5),(-5.0,48.8),(-2.4,50.0),(1.2,50.8),(2.6,52.4),(3.6,54.0)],
    },
}
POINTS = {
    'jp': {'tsushimaStrait': (129.6,34.3), 'tsugaru': (140.6,41.5), 'measure': (135.4,38.6), 'hokkaido': (141.6,43.2),
           'korea': (127.9,36.6), 'honshu': (137.6,36.2), 'pacific': (142.5,33.0), 'kyushu': (130.7,32.6)},
    'eu': {'northsea': (3.0,56.2), 'south': (3.4,53.1), 'uk': (-2.2,53.2), 'norway': (8.6,61.3), 'atl': (-16.5,57.5),
           'ireland': (-8.0,53.2), 'biscay': (-5.5,45.6)},
}
RECTS = {'eu': {'copernicus': (-18.0, 48.0, 13.0, 62.0)}}

out = {}
for key, m in MAPS.items():
    lon0, lat0, lon1, lat1 = m['bbox']
    k = math.cos(math.radians((lat0 + lat1) / 2))
    W = m['W']; sx = W / ((lon1 - lon0) * k); H = round((lat1 - lat0) * sx)
    P = lambda lon, lat: (round((lon - lon0) * k * sx, 1), round((lat1 - lat) * sx, 1))
    clip = box(lon0 - 1, lat0 - 1, lon1 + 1, lat1 + 1)
    parts = []
    for g in geoms:
        if not g.intersects(clip): continue
        c = g.intersection(clip)
        polys = [c] if isinstance(c, Polygon) else [p for p in getattr(c, 'geoms', []) if isinstance(p, Polygon)]
        for p in polys:
            if p.area < 0.01: continue
            p = p.simplify(0.03, preserve_topology=True)
            ring = [P(x, y) for x, y in p.exterior.coords]
            parts.append('M' + 'L'.join(f'{x},{y}' for x, y in ring) + 'Z')
    lines = {n: [P(x, y) for x, y in pts] for n, pts in LINES[key].items()}
    points = {n: P(*v) for n, v in POINTS[key].items()}
    rects = {n: [*P(r[0], r[3]), *P(r[2], r[1])] for n, r in RECTS.get(key, {}).items()}
    out[key] = dict(W=W, H=H, land=''.join(parts), lines=lines, points=points, rects=rects, proj=[lon0, lat1, round(k * sx, 5), round(sx, 5)])
    print(key, 'size', W, H, 'land chars', len(out[key]['land']))

json.dump(out, open(HERE / 'maps.json', 'w'), separators=(',', ':'))
