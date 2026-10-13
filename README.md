# Global Warming 1 — Station-Based Temperature Trend Analysis

Analyzes historical surface temperature data from weather stations across a specified geographic region to quantify how warming trends vary with distance to coastline. Stations are classified as **coastal** (0–50 km), **near-coastal** (50–500 km), or **inland** (>500 km), and a Tukey HSD test determines whether trend differences between groups are statistically significant. All results are described in the PDF inside the `./paper` folder.

## What it does

1. **Loads raw temperature data** (measured stations + CNRM modelled) and cleans it by removing stations with missing data below a threshold.
2. **Geocodes station names** to lat/lon using OpenStreetMap's Nominatim API, restricted to user-defined bounds.
3. **Computes distance to coast** for each station using the Natural Earth coastline dataset.
4. **Calculates linear temperature trends** (°C per decade) via OLS for each station between 1950–2017.
5. **Classifies each station** as coastal / near-coastal / inland based on distance thresholds.
6. **Outputs:**
   - Scatter plot: warming trend vs. distance to coast, with OLS fit and grouped scatter (coastal/near-coastal/inland).
   - Map of station locations colour-coded by trend strength.
   - Statistical summary (mean, std, quartiles) per group.
   - Tukey HSD post-hoc results between the three location types.

## Quick Start

### Prerequisites

- Python ≥ 3.13
- [uv](https://github.com/astral-sh/uv) (for dependency management and environment setup)

### Setup

```bash
# Create virtual environment and install dependencies
uv sync

# Activate it
source .venv/bin/activate
```

### Configuration

Edit `config.yaml` to adjust:

| Setting | Description | Default |
|---|---|---|
| `bounds` | Geographic bounding box `[[min_lat, min_lon], [max_lat, max_lon]]` | `[40, -10], [50, 90]` |
| `dist_coastal` | Threshold (km) for "coastal" classification | 50 |
| `dist_inland` | Threshold (km) for "inland" classification | 500 |
| `trend_year_start/end` | Trend calculation window | 1950–2017 |
| `trend_data_fraction` | Minimum fraction of data points required per station | 0.5 |
| `clean_temperature_data` | Run raw → cleaned data transformation (once) | `false` |
| `calculate_coordinates` | Run geocoding (once, rate-limited by Nominatim policy) | `false` |

### Running

```bash
uv run python main.py
```

The pipeline runs end-to-end. Only set `clean_temperature_data` or `calculate_coordinates` to `true` on the first run; subsequent runs skip these steps if your cached CSVs are in place.

Outputs go to `data/processed/` (CSVs) and `plots/` (PNGs + CSV summaries).

## Project Layout

```
├── config.yaml              # All tunable parameters
├── main.py                  # Entry point — orchestrates the pipeline
├── pyproject.toml           # uv project config, dependencies
├── src/global_warming_1/  # Source package
│   ├── config.py            # YAML-based configuration loader
│   ├── geo_utils.py         # Geocoding (Nominatim) + coastal distance computation
│   ├── processing.py        # Data cleaning, trend calculation, statistics
│   └── plotting.py          # matplotlib visualisations
├── data/                    # Raw inputs & processed outputs (gitignored)
│   ├── raw/                 # Raw temperature CSV
│   ├── processed/           # Cleaned station/modelled data + coordinates
│   └── ne_10m_coastline/  # Coastline shapefile (Natural Earth, public domain)
├── plots/                   # Outputs (gitignored)
└── uv.lock                  # Dependency lock file
```

## Dependencies

| Package | Use |
|---|---|
| `geopandas` + `shapely` | Spatial operations (coastline geometry, nearest-point distance) |
| `geopy` | Geocoding station names via Nominatim |
| `matplotlib` | Visualisation |
| `pandas` + `numpy` | Data manipulation and OLS fitting |
| `statsmodels` | Tukey HSD post-hoc test |
| `pyyaml` | Configuration parsing |

## License

MIT (see LICENSE file).

Author: Christian Fojtek
