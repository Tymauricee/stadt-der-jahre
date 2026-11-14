"""Reproduces the numbers of the exhibition from the data table.

    python trend.py

Prints the linear trend per decade for both seas, the ratio (about x3),
and the record years (warmer than every year before, counted from 1990).
"""
import csv, pathlib

rows = list(csv.DictReader(open(pathlib.Path(__file__).parent / 'sst_annual_anomalies_1982_2024.csv')))
years = [int(r['year']) for r in rows]

def slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def records(ys, start=1990):
    best, out = float('-inf'), []
    for y, v in zip(years, ys):
        if v > best:
            best = v
            if y >= start: out.append(y)
    return out

trend = {}
for key, name in (('sea_of_japan', 'Sea of Japan'), ('nw_european_shelf', 'NW European shelf')):
    ys = [float(r[key]) for r in rows]
    trend[key] = slope(years, ys) * 10
    print(f'{name:18} trend {trend[key]:+.2f} °C per decade, '
          f'about {trend[key] * (years[-1] - years[0]) / 10:+.1f} °C over {years[0]}–{years[-1]}, '
          f'records: {", ".join(map(str, records(ys)))}')
print(f'ratio: x{trend["sea_of_japan"] / trend["nw_european_shelf"]:.1f}')
