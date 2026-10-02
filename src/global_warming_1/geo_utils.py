import logging

import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from shapely.geometry import Point as ShapelyPoint
from shapely.ops import nearest_points

from src.global_warming_1.config import Bounds, Config

logger = logging.getLogger(__name__)


import logging

from geopy.extra.rate_limiter import RateLimiter
from geopy.point import Point

logger = logging.getLogger(__name__)


USER_AGENT = "global-warming-1"

PLACE_CLASSES = {"place", "boundary", "aeroway"}
ALIASES = {
    "Gur'Ev": "Atyrau",
    "Turgaj": "Torgay",
    "Aralskoe More": "Aral",
    "Uil": "Oyil",  # verify; Kazakh name of the settlement
    "Kzyl-Zar": "Kyzylzhar",  # verify, name is ambiguous
    "Balhash": "Balkhash",
    "Kzyl-Orda": "Kyzylorda",
    "Cimbaj": "Chimbay",
    "Wien/Hohe War": "Vienna",
    "Klagenfurt-Fl": "Klagenfurt",
    "Split/Marjan": "Split",
    "Paris/Le Bourget": "Le Bourget",
    "Marseille/Marignane France": "Marignane",
    "Trier-Petrisb": "Trier",
    "Milano/Linate": "Milan",
    "Venezia/Tesse": "Tessera, Venice",
    "Primorsko-Aht": "Primorsko-Akhtarsk",
    "Geneve-Cointr": "Geneva",
    "Istanbul/Gozt": "Goztepe, Istanbul",
    "Heniches'K": "Henichesk",
    "Feodosiia": "Feodosia",
    "Debal'Cevo": "Debaltseve",
}


def _in_bounds(lat: float, lon: float, bounds: Bounds) -> bool:
    (min_lat, min_lon), (max_lat, max_lon) = bounds
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _query_variants(location: str) -> list[str]:
    """Candidate queries, most specific first, without duplicates."""
    variants = [
        ALIASES.get(location),
        location,
        location.split("/")[0].strip(),  # "Paris/Le Bourget" -> "Paris"
    ]
    return list(dict.fromkeys(v for v in variants if v))


def get_coordinates_by_location(
    geocode, location: str, config: Config
) -> tuple[float, float] | None:
    """Return (lat, lon) of the best candidate inside config.bounds, else None."""
    (min_lat, min_lon), (max_lat, max_lon) = config.bounds
    viewbox = [Point(min_lat, min_lon), Point(max_lat, max_lon)]

    for query in _query_variants(location):
        try:
            results = geocode(
                query,
                viewbox=viewbox,
                bounded=True,
                exactly_one=False,
                limit=5,
                language="en",
            )
        except Exception as e:
            logger.warning(f"Geocoding failed for {query!r}: {e}")
            continue

        for r in results or []:
            if (
                _in_bounds(r.latitude, r.longitude, config.bounds)
                and r.raw.get("class") in PLACE_CLASSES
            ):
                return r.latitude, r.longitude  # results are importance-ranked
    return None


def create_coordinate_df(locations: list[str], config: Config) -> pd.DataFrame:
    """Geocode locations within config.bounds. Stations as rows, columns lat/lon."""
    ctx = Nominatim(user_agent=USER_AGENT, timeout=10)
    geocode = RateLimiter(
        ctx.geocode,
        min_delay_seconds=1.1,
        max_retries=3,
        error_wait_seconds=5,
        swallow_exceptions=False,
    )

    rows = {}
    for loc in locations:
        coord = get_coordinates_by_location(geocode, loc, config)
        if coord is None:
            logger.warning(f"Coordinates for {loc!r} not found")
            continue
        rows[loc] = {"lat": coord[0], "lon": coord[1]}

    return pd.DataFrame.from_dict(rows, orient="index", columns=["lat", "lon"])


def create_coordinate_csv(config: Config) -> None:
    """Create csv with coordinates (lat, lon) for the station names in the
    cleaned temperature data. Only stations missing from an existing csv are queried."""
    stations = pd.read_csv(
        config.cleaned_station_temperature_data_path, index_col=0
    ).columns.to_list()

    path = config.coordinate_data_path
    if path.exists():
        existing = pd.read_csv(path, index_col=0)
    else:
        existing = pd.DataFrame(columns=["lat", "lon"])

    missing = [s for s in stations if s not in existing.index]
    logger.info(f"{len(existing)} cached, {len(missing)} to geocode")

    new = create_coordinate_df(missing, config)
    df = pd.concat([existing, new]).reindex(
        [s for s in stations if s in existing.index.union(new.index)]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    logger.info(f"Created coordinate dataframe with shape {df.shape}")


def distance_to_coast_km(coast, lat: float, lon: float) -> float:
    """Calcualte distance in km from coordinate point to nearest coastline"""
    target = ShapelyPoint(lon, lat)  # shapely: (x=lon, y=lat)
    nearest = nearest_points(coast, target)[0]  # point on the coastline
    return geodesic((lat, lon), (nearest.y, nearest.x)).km  # geopy: (lat, lon)


def compute_coastal_distances(coord: pd.DataFrame, config: Config) -> pd.Series:
    """Compute distance to coast for each coordinate in the dataframe."""
    coast = gpd.read_file(config.coast_data_path).geometry.union_all()
    distances = [
        distance_to_coast_km(coast, lat, lon) for lat, lon in zip(coord.lat, coord.lon)
    ]
    return pd.Series(distances, index=coord.index, name="dist_coast_km")
