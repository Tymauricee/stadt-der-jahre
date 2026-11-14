"""Writes the numbers from sst_annual_anomalies_1982_2024.csv into the firmware and the page.

Use it when you swap in another sea (or another yearly series) for the same 43 years:
    1. edit sst_annual_anomalies_1982_2024.csv
    2. python apply_data.py
    3. python ../web/src/build.py          (rebuilds the page)
    4. python ../print/make_grid.py        (new towers for the print)
    5. upload the firmware again
Names on the page (日本海 / 北海) and in the conclusion scenes are text in
web/src/stadt_der_jahre.src.html; change them there.
"""
import csv, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / 'data' / 'sst_annual_anomalies_1982_2024.csv')))
assert len(rows) == 43 and rows[0]['year'] == '1982', 'the 16x16 layout expects 1982–2024 (43 years)'
jp = [float(r['sea_of_japan']) for r in rows]
eu = [float(r['nw_european_shelf']) for r in rows]

def c_array(v):
    lines = []
    for i in range(0, len(v), 10):
        chunk = ', '.join(f'{x:5.2f}f' for x in v[i:i + 10])
        lines.append(f'  {chunk}{"," if i + 10 < len(v) else ""}  // {1982 + i}–{min(1982 + i + 9, 2024)}')
    return '{\n' + '\n'.join(lines) + '\n};'

ino = ROOT / 'firmware' / 'stadt_der_jahre' / 'stadt_der_jahre.ino'
s = ino.read_text(encoding='utf-8')
for name, v in (('SST_JP', jp), ('SST_EU', eu)):
    s, n = re.subn(r'(const float ' + name + r'\[N_YEARS\] = )\{.*?\};', lambda m: m.group(1) + c_array(v), s, flags=re.S)
    assert n == 1, name
ino.write_text(s, encoding='utf-8')

page = ROOT / 'web' / 'src' / 'stadt_der_jahre.src.html'
s = page.read_text(encoding='utf-8')
for name, v in (('JP', jp), ('EU', eu)):
    s, n = re.subn(r'^const ' + name + r' = \[[^\]]*\];', 'const ' + name + ' = [' + ','.join(f'{x:.2f}' for x in v) + '];', s, flags=re.M)
    assert n == 1, name
page.write_text(s, encoding='utf-8')
print('firmware and page source updated; now run web/src/build.py and print/make_grid.py')
