"""ETL module for loading and normalizing physician data."""

from .geocoder import calculate_distance_miles, geocode_zip, locations_nearby
from .loaders import (
    load_all_sources,
    load_cms_claims,
    load_ground_truth,
    load_hospital_affiliations,
    load_publications,
    load_referrals,
    load_state_licenses,
)
from .name_parser import parse_name, standardize_name
from .normalizer import (
    normalize_all,
    normalize_cms_claims,
    normalize_hospital_affiliations,
    normalize_publications,
    normalize_state_licenses,
)

__all__ = [
    # Loaders
    "load_all_sources",
    "load_cms_claims",
    "load_ground_truth",
    "load_hospital_affiliations",
    "load_publications",
    "load_referrals",
    "load_state_licenses",
    # Name parsing
    "parse_name",
    "standardize_name",
    # Normalizers
    "normalize_all",
    "normalize_cms_claims",
    "normalize_hospital_affiliations",
    "normalize_publications",
    "normalize_state_licenses",
    # Geocoding
    "geocode_zip",
    "calculate_distance_miles",
    "locations_nearby",
]
