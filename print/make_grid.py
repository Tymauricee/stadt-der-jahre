"""Stadt der Jahre: 3D-printed city for a 16x16 WS2812B LED panel (10 mm pitch).

One square tower per year and sea, sitting exactly on top of its LED.
Tower height = 4 mm + (anomaly + 2 °C) * 10 mm, so 0 °C (normal) = 24 mm.
Back block: Sea of Japan, front block: NW European shelf. A small notch marks the front.
The underside has a 5.7 x 5.7 x 2.0 mm pocket for every LED, so the plate clicks onto
the panel (5.7 mm fitted best in our print test; adjust POCKET for your printer).

Run:  pip install manifold3d trimesh
      python make_grid.py   ->  stadt_der_jahre_grid.stl
Print: white PLA, 0.2 mm layers, no supports, plate down. Thin white walls glow best.
"""
import csv, pathlib
from manifold3d import Manifold
import trimesh

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / 'data' / 'sst_annual_anomalies_1982_2024.csv'
P = 10.0        # LED pitch of the panel
T = 8.0         # tower width
PLATE = 2.6     # base plate thickness
N = 16          # LEDs per side
POCKET, POCKET_D = 5.7, 2.0   # LED pockets in the underside (WS2812B 5050 = 5.0 x 5.0 x 1.6 mm)

def height(a):
    return 4 + (a + 2) * 10

def cell(year, jp):
    """Same layout as the firmware: column = year in decade, row = decade (row 0 = back)."""
    dec = (year - 1980) // 10
    return 3 + year % 10, (3 if jp else 9) + (4 - dec)

def pockets():
    m = None
    for i in range(N):
        for j in range(N):
            c = Manifold.cube([POCKET, POCKET, POCKET_D + 0.5]).translate([i * P + (P - POCKET) / 2, j * P + (P - POCKET) / 2, -0.5])
            m = c if m is None else m + c
    return m

def build(rows):
    body = Manifold.cube([N * P, N * P, PLATE])
    body = body - Manifold.cube([10, 1.5, PLATE + 1]).translate([N * P / 2 - 5, -0.5, -0.5])   # front notch
    for r in rows:
        year = int(r['year'])
        for key, jp in (('sea_of_japan', True), ('nw_european_shelf', False)):
            col, row = cell(year, jp)
            x0, y0 = col * P + (P - T) / 2, (N - 1 - row) * P + (P - T) / 2
            body = body + Manifold.cube([T, T, height(float(r[key]))]).translate([x0, y0, PLATE - 0.01])
    return body - pockets()

if __name__ == '__main__':
    rows = list(csv.DictReader(open(DATA)))
    mesh = build(rows).to_mesh()
    tm = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)
    out = HERE / 'stadt_der_jahre_grid.stl'
    tm.export(out)
    print(out.name, 'size mm', (tm.bounds[1] - tm.bounds[0]).round(1).tolist(), f'volume {tm.volume / 1000:.1f} cm3', 'watertight', tm.is_watertight)
