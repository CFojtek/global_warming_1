from dataclasses import dataclass
from pathlib import Path
from typing import Self

import yaml

Bounds = tuple[tuple[float, float], tuple[float, float]]


@dataclass(frozen=True)
class Config:
    data_folder: Path
    plot_folder: Path
    temperature_data: str
    coordinate_data: str
    coast_data: str
    bounds: Bounds  # ((min_lat, min_lon), (max_lat, max_lon))
    dist_coastal: float  # 0-dist_coastal km is coastal region
    dist_inland: float  # >dist_inland km is inland region
    trend_year_start: float  # Year to start calculating temperature trends
    trend_year_end: float  # Year to end calculating temperature trends
    trend_data_fraction: (
        float  # Fraction of data points required to calculate trend (0-1)
    )
    clean_temperature_data: (
        bool  # Whether to clean temperature data. Has to be done only once
    )
    calculate_coordinates: (
        bool  # Whether to calculate coordinates. Has to be done only once
    )

    @property
    def raw_temperature_data_path(self) -> Path:
        return self.data_folder / "raw" / self.temperature_data

    @property
    def cleaned_station_temperature_data_path(self) -> Path:
        return (
            self.data_folder / "processed" / f"cleaned_station_{self.temperature_data}"
        )

    @property
    def cleaned_modelled_temperature_data_path(self) -> Path:
        return (
            self.data_folder / "processed" / f"cleaned_modelled_{self.temperature_data}"
        )

    @property
    def coordinate_data_path(self) -> Path:
        return self.data_folder / "processed" / self.coordinate_data

    @property
    def coast_data_path(self) -> Path:
        return self.data_folder / self.coast_data

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> Self:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        # YAML gives strings/lists; convert to the types the dataclass expects
        raw["data_folder"] = Path(raw["data_folder"])
        raw["plot_folder"] = Path(raw["plot_folder"])
        raw["bounds"] = tuple(tuple(corner) for corner in raw["bounds"])
        raw["dist_coastal"] = float(raw["dist_coastal"])
        raw["dist_inland"] = float(raw["dist_inland"])
        raw["trend_year_start"] = float(raw["trend_year_start"])
        raw["trend_year_end"] = float(raw["trend_year_end"])
        raw["trend_data_fraction"] = float(raw["trend_data_fraction"])
        raw["clean_temperature_data"] = bool(raw["clean_temperature_data"])
        raw["calculate_coordinates"] = bool(raw["calculate_coordinates"])
        return cls(**raw)
