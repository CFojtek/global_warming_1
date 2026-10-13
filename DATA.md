## Project context

Station-based global warming analysis: computes temperature trends from historical meteorological station data, geocodes stations to lat/lon coordinates, and measures distance to coastlines. See README.md for full background.

---

## Directory structure

| Path | Contents |
|---|---|
| `data/raw/` | Original raw data obtained from `https://climatemodels.uchicago.edu/timeseries#BbbBBECBBBBBBDBBBBBGCGDeBBBBDBBEBBBBBDBBBBBBBEBBBBBKbBCBCCBBCCCEwBBBBBBBBBBBBBBBBBBBBBEBBBBFpCBBBBBBBBBFDBBNqBBBBBBBBCBBBBmBlJBBUyBBBDTBCBJpBBBBBBBBBBBBDveBgiBBEBCBDBCCBBGBCCEBBBBECBBBBCBBBBBBBQCBjBBBBBBBBBBBBBBBBBCBBBBBDCEBBBBBBBBBBCcBBBBCDCBBBBBBBBBCBBDBOBBBBBBBBhBCBCCBBBBBBBBBBBBCBBBBCBBCBBBBBBBBBBBBBBBBDBBCBBBBCBCBBBBVBBBBOMBBCCBBDnCCBKBBBGECBBBBCBBDBBBsBCBBBBBBBBBBBBBBCBBBBBBBBBBBBBCCBBBBBBBFCBBBBBBBBFBCBqCDBELBBDBBBBBBBBBDBBCBBBDBBBBBBBBBBBBBBBBCBDBFZBDBBBBBBGnBBBBBCBBBBBBBBBBBBBBBBCf` |
| `data/processed/` | Cleaned / prepared CSVs |
| `data/ne_10m_coastline/` | Geospatial coastline shapefiles used in calculating the distance from station to nearest coastline. Obtained from `https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/` |

---

## 1. `data/raw/temperatures.csv`

Raw temperature data was obtained from time series browser. Temperature data was normalized before downloading.

- **Location:** `data/raw/temperatures.csv`
- **Format:** Wide table (station names as column headers)
- **Rows:** 453 lines → 1 header + 452 data rows (years 1849–2300)
- **Data type:** Contains historical temperature values (deg C) per station per year, and the modelled temperatures for those stations according to RCP2.6 and RCP8.5 models.

---

## 2. `data/processed/cleaned_modelled_temperatures.csv`

- **Location:** `data/processed/cleaned_modelled_temperatures.csv`
- **Format:** Wide table; each station has three model-based columns (×3):
  - `<prefix> Hist for <station>` — historical simulation from CNRM-CM5
  - `<prefix> RCP2.6 for <station>` — low-emissions scenario
  - `<prefix> RCP8.5 for <station>` — high-emissions scenario
- **Model:** CNRM-CM5 climate model
- **Rows:** 454 lines → 1 header + 452 data rows (years 1849–2300)
- **Data type:** Modeled temperature values.

---

## 3. `data/processed/cleaned_station_temperatures.csv`

- **Location:** `data/processed/cleaned_station_temperatures.csv`
- **Format:** Wide table; station names as column headers (one column per station)
- **Rows:** 454 lines → 1 header + 452 data rows (years 1849–2300)
- **Data type:** Processed and cleaned historical temperature data.

---

## 4. `data/processed/coordinates.csv`

- **Location:** `data/processed/coordinates.csv`
- **Format:** Standard two-column CSV
- **Rows:** 83 lines → 1 header + 82 station rows
- **Columns:** `Name`, `lat`, `lon`
- **Data type:** Geodetic coordinates for each meteorological station.

---

## Summary of file counts

| File | Lines | Data rows | Format | Purpose |
|---|---|---|---|---|
| `data/raw/temperatures.csv` | 453 | 452 | Wide | Raw temperature data |
| `processed/cleaned_modelled_temps.csv` | 454 | 452 | Wide (×3 per station) | CNRM-CM5 model projections (Hist, RCP2.6, RCP8.5) |
| `processed/cleaned_station_temps.csv` | 454 | 452 | Wide (~82 stations) | Station-level temperature anomalies |
| `processed/coordinates.csv` | 83 | 82 | Row-per-station | Lat/lon for each station |

All processed tables share the same year range: **1849–2300** (452 time points).
