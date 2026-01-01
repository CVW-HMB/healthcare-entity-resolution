"""Geocoding utilities for zip code to lat/lon conversion."""

import math
from pathlib import Path

import pandas as pd

from ..config import REFERENCE_DIR
from ..logging import get_logger

logger = get_logger("etl.geocoder")

# In-memory cache of zip centroids
_zip_cache: dict[str, tuple[float, float]] = {}

# Approximate centroids for cities used in synthetic data
# In production, you'd load from a real zip centroid file
DEFAULT_CENTROIDS = {
    "02101": (42.3601, -71.0589),  # Boston
    "10001": (40.7484, -73.9967),  # New York
    "90001": (33.9425, -118.2551),  # Los Angeles
    "60601": (41.8819, -87.6278),  # Chicago
    "77001": (29.7545, -95.3536),  # Houston
    "85001": (33.4484, -112.0740),  # Phoenix
    "19101": (39.9526, -75.1652),  # Philadelphia
    "78201": (29.4685, -98.5254),  # San Antonio
    "92101": (32.7194, -117.1628),  # San Diego
    "75201": (32.7872, -96.7985),  # Dallas
    "95101": (37.3361, -121.8906),  # San Jose
    "78701": (30.2747, -97.7404),  # Austin
    "32201": (30.3275, -81.6556),  # Jacksonville
    "76101": (32.7555, -97.3308),  # Fort Worth
    "43201": (39.9860, -83.0030),  # Columbus
    "28201": (35.2145, -80.8386),  # Charlotte
    "98101": (47.6062, -122.3321),  # Seattle
    "80201": (39.7392, -104.9903),  # Denver
    "37201": (36.1659, -86.7844),  # Nashville
    "97201": (45.5051, -122.6750),  # Portland
    "48201": (42.3314, -83.0458),  # Detroit
    "38101": (35.1175, -89.9711),  # Memphis
    "30301": (33.7488, -84.3880),  # Atlanta
    "33101": (25.7617, -80.1918),  # Miami
    "44101": (41.4993, -81.6944),  # Cleveland
    "55401": (44.9778, -93.2650),  # Minneapolis
    "15201": (40.4774, -79.9531),  # Pittsburgh
    "63101": (38.6270, -90.1994),  # St. Louis
    "21201": (39.2904, -76.6122),  # Baltimore
    "33601": (27.9506, -82.4572),  # Tampa
}


def load_zip_centroids(filepath: Path | None = None) -> dict[str, tuple[float, float]]:
    """Load zip code centroids from file."""
    global _zip_cache

    if _zip_cache:
        return _zip_cache

    # Try to load from file
    filepath = filepath or REFERENCE_DIR / "zip_centroids.csv"

    if filepath.exists():
        try:
            df = pd.read_csv(filepath, dtype={"zip": str})
            for _, row in df.iterrows():
                zip_code = str(row["zip"]).zfill(5)
                _zip_cache[zip_code] = (float(row["latitude"]), float(row["longitude"]))
            logger.info(f"Loaded {len(_zip_cache)} zip centroids from {filepath}")
        except Exception as e:
            logger.warning(f"Failed to load zip centroids: {e}")

    # Fall back to defaults
    if not _zip_cache:
        _zip_cache = DEFAULT_CENTROIDS.copy()
        logger.info(f"Using {len(_zip_cache)} default zip centroids")

    return _zip_cache


def geocode_zip(zip_code: str | None) -> tuple[float | None, float | None]:
    """Get lat/lon for a zip code."""
    if not zip_code:
        return None, None

    # Normalize zip to 5 digits
    zip_code = str(zip_code).strip()[:5].zfill(5)

    centroids = load_zip_centroids()

    if zip_code in centroids:
        return centroids[zip_code]

    # Try matching just the first 3 digits (zip3)
    zip3 = zip_code[:3]
    for z, coords in centroids.items():
        if z.startswith(zip3):
            return coords

    return None, None


def calculate_distance_miles(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    """Calculate distance between two points using Haversine formula."""
    if any(x is None for x in [lat1, lon1, lat2, lon2]):
        return None

    # Earth radius in miles
    R = 3959

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def locations_nearby(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
    threshold_miles: float = 50,
) -> bool:
    """Check if two locations are within threshold distance."""
    distance = calculate_distance_miles(lat1, lon1, lat2, lon2)
    if distance is None:
        return False
    return distance <= threshold_miles
