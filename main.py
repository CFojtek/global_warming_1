# %%
import logging
from enum import Enum

import pandas as pd

from global_warming_1.geo_utils import compute_coastal_distances
from global_warming_1.processing import (
    compute_and_store_statistical_summary,
    compute_temperature_trends,
)
from src.global_warming_1.config import Config
from src.global_warming_1.plotting import plot_coastal_distance_vs_trend, plot_stations

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


CONFIG_PATH = "config.yaml"
config = Config.from_yaml(CONFIG_PATH)


class LocationType(Enum):
    COASTAL = "coastal"
    NEAR_COASTAL = "near-coastal"
    INLAND = "inland"


def main():
    if config.clean_temperature_data:
        logger.info("Cleaning temperature data...")
        from src.global_warming_1.processing import clean_and_store_temperature_data

        clean_and_store_temperature_data(config)

    if config.calculate_coordinates:
        logger.info("Calculating coordinates for station locations...")
        from src.global_warming_1.geo_utils import create_coordinate_csv
        from src.global_warming_1.processing import remove_locations_without_coordinates

        create_coordinate_csv(config)
        remove_locations_without_coordinates(config)

    metadata_stations = pd.read_csv(config.coordinate_data_path, index_col=0)
    temps_stations = pd.read_csv(
        config.cleaned_station_temperature_data_path, index_col=0
    )

    metadata_stations["trend_per_decade"] = compute_temperature_trends(
        temps_stations, config
    )
    metadata_stations["dist_coast_km"] = compute_coastal_distances(
        metadata_stations, config
    )

    metadata_stations["type"] = [
        LocationType.COASTAL.value
        if dist <= config.dist_coastal
        else LocationType.NEAR_COASTAL.value
        if dist <= config.dist_inland
        else LocationType.INLAND.value
        for dist in metadata_stations["dist_coast_km"]
    ]

    compute_and_store_statistical_summary(metadata_stations, config)

    plot_coastal_distance_vs_trend(
        metadata_stations,
        type_order=[type.value for type in LocationType],
        save_path=config.plot_folder / "coastal_distance_vs_trend.png",
    )
    plot_stations(
        metadata_stations, save_path=config.plot_folder / "station_locations.png"
    )


if __name__ == "__main__":
    main()
