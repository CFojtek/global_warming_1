import logging

import numpy as np
import pandas as pd
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from src.global_warming_1.config import Config

logger = logging.getLogger(__name__)


def get_station_data(df: pd.DataFrame) -> pd.DataFrame:
    """Get data from stations only. Remove modelled temperatures and global temperature data."""
    station_columns = df.columns[
        ~df.columns.str.contains("CNRM|Year|Global Temp", regex=True)
    ]
    return df[station_columns]


def _match_modelled_location(column: str, locations: set[str]) -> str | None:
    modelled_location = column.rsplit(" for ", maxsplit=1)[-1]
    if modelled_location in locations:
        return modelled_location

    matches = [
        location for location in locations if location.startswith(modelled_location)
    ]
    return matches[0] if len(matches) == 1 else None


def clean_and_store_temperature_data(conf: Config) -> None:
    """Clean and store temperature data by removing:
    - stations with all NaN values
    - stations with less than conf.trend_data_fraction of data points
    Both the measured and modelled temperature data are cleaned and stored in separate files.
    """
    df = pd.read_csv(conf.raw_temperature_data_path, index_col=0)
    df_stations = get_station_data(df)
    logger.info(f"Original shape: {df_stations.shape}")

    df_stations = df_stations.dropna(axis=1, how="all")
    logger.info(
        f"Shape after removing stations with all NaN values: {df_stations.shape}"
    )

    df_trend = df_stations.loc[
        (df_stations.index >= conf.trend_year_start)
        & (df_stations.index <= conf.trend_year_end)
    ]
    min_data_points = int(len(df_trend) * conf.trend_data_fraction)
    df_stations = df_stations.loc[
        :, df_trend.dropna(axis=1, thresh=min_data_points).columns
    ]
    logger.info(
        f"Shape after removing stations with less than {conf.trend_data_fraction * 100}% data points for trend calculation: {df_stations.shape}"
    )

    kept_locations = set(df_stations.columns)
    modelled_columns = []
    for column in df.columns:
        if "CNRM" in column and _match_modelled_location(column, kept_locations):
            modelled_columns.append(column)

    df_modelled = df[modelled_columns]
    logger.info(
        f"Shape of modelled temperature data after cleaning: {df_modelled.shape}"
    )

    df_stations.to_csv(conf.cleaned_station_temperature_data_path)
    df_modelled.to_csv(conf.cleaned_modelled_temperature_data_path)


def remove_locations_without_coordinates(config: Config) -> None:
    """Remove locations from temperature data where no coordinates were found. This is necessary because some station names are not recognized by the geocoder."""
    coords = pd.read_csv(config.coordinate_data_path, index_col=0)
    station_temps = pd.read_csv(
        config.cleaned_station_temperature_data_path, index_col=0
    )
    modelled_temps = pd.read_csv(
        config.cleaned_modelled_temperature_data_path, index_col=0
    )

    locations_in_temps = set(station_temps.columns)
    locations_with_coords = set(coords.index)

    locations_to_remove = locations_in_temps - locations_with_coords
    station_temps = station_temps.drop(columns=locations_to_remove)
    modelled_columns = [
        column
        for column in modelled_temps.columns
        if _match_modelled_location(column, locations_in_temps) in locations_with_coords
    ]
    modelled_temps = modelled_temps[modelled_columns]
    logger.info(
        f"Shape of station temperature data after removing locations without coordinates: {station_temps.shape}"
    )
    logger.info(
        f"Shape of modelled temperature data after removing locations without coordinates: {modelled_temps.shape}"
    )
    station_temps.to_csv(config.cleaned_station_temperature_data_path)
    modelled_temps.to_csv(config.cleaned_modelled_temperature_data_path)


def calculate_trend_per_decade(series: pd.Series) -> float:
    """Calculate trend in units per decade over given pandas series, ignoring NaNs."""
    x = series.index.to_numpy(dtype=float)  # years
    y = series.to_numpy(dtype=float)
    mask = ~np.isnan(y)

    slope_per_year = np.polyfit(x[mask], y[mask], 1)[0]
    return slope_per_year * 10  # Convert to units per decade


def compute_temperature_trends(df: pd.DataFrame, config: Config) -> pd.Series:
    """Compute temperature trends over a dataframe with temperature data. Returns a new df with the trend per location."""
    df = df.loc[
        (df.index >= config.trend_year_start) & (df.index <= config.trend_year_end)
    ]

    df_trends = df.apply(calculate_trend_per_decade)
    return df_trends


def compute_and_store_statistical_summary(df: pd.DataFrame, config: Config) -> None:
    """Computes and stores statistical summary of a dataframe"""
    grouped = df.groupby("type").describe()
    grouped.to_csv(config.plot_folder / "metadata_stations_summary.csv")

    tukey_data = df[["type", "trend_per_decade"]].dropna()
    tukey = pairwise_tukeyhsd(
        endog=tukey_data["trend_per_decade"],
        groups=tukey_data["type"],
        alpha=0.05,
    )

    tukey_table = tukey.summary().data
    tukey_df = pd.DataFrame(tukey_table[1:], columns=tukey_table[0])
    tukey_df.to_csv(config.plot_folder / "tukey_hsd_results.csv", index=False)
