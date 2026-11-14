# Data

`sst_annual_anomalies_1982_2024.csv`: yearly sea surface temperature anomalies in °C against the 1991–2020 average.

| Column | Source |
|---|---|
| `sea_of_japan` | Japan Meteorological Agency, area N2 (central Sea of Japan), yearly mean anomaly. [JMA data page](https://www.data.jma.go.jp/gmd/kaiyou/data/shindan/a_1/japan_warm/japan_warm_data.html) |
| `nw_european_shelf` | E.U. Copernicus Marine Service, `OMI_CLIMATE_SST_NORTHWESTSHELF_area_averaged_anomalies` (48–62° N, 18° W–13° E), monthly values averaged per year. [Product page](https://data.marine.copernicus.eu/product/OMI_CLIMATE_SST_NORTHWESTSHELF_area_averaged_anomalies/description) |

- `trend.py` prints the trend per decade, the ratio (×2.9) and the record years.
- `apply_data.py` copies the CSV into the firmware and the page source, for example after you swap in another sea.

Generated using E.U. Copernicus Marine Service information. Sea of Japan data: Japan Meteorological Agency.
