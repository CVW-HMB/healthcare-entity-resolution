"""Normalize source data into PhysicianRecord objects."""

import hashlib

import pandas as pd

from ..logging import get_logger
from ..schemas.records import PhysicianRecord
from .geocoder import geocode_zip
from .name_parser import parse_name

logger = get_logger("etl.normalizer")


def _generate_source_id(source: str, row: pd.Series, index: int) -> str:
    """Generate a unique source ID for a record."""

    # Use source_id from CSV if present
    if "source_id" in row and pd.notna(row.get("source_id")):
        return str(row["source_id"])

    # Use a hash of key fields to create stable IDs
    if source == "cms" and pd.notna(row.get("npi")):
        key = f"cms_{row['npi']}_{row.get('procedure_date', '')}_{index}"
    elif source == "license":
        key = f"license_{row.get('license_number', index)}"
    elif source == "hospital":
        key = f"hospital_{row.get('hospital_id', '')}_{row.get('physician_name', '')}_{index}"
    elif source == "publication":
        key = f"pub_{row.get('publication_id', '')}_{row.get('author_name', '')}_{index}"
    else:
        key = f"{source}_{index}"

    return hashlib.md5(key.encode()).hexdigest()[:16]


def normalize_cms_claims(df: pd.DataFrame) -> list[PhysicianRecord]:
    """Normalize CMS claims data."""
    records = []

    for idx, row in df.iterrows():
        parsed = parse_name(row.get("provider_name", ""))

        # Geocode based on facility (we don't have direct address in CMS)
        lat, lon = None, None

        npi = row.get("npi")
        if pd.isna(npi) or not npi or "X" in str(npi):
            npi = None

        record = PhysicianRecord(
            source="cms",
            source_id=_generate_source_id("cms", row, idx),
            npi=npi,
            name_raw=row.get("provider_name"),
            name_first=parsed.first,
            name_last=parsed.last,
            name_middle=parsed.middle,
            name_suffix=parsed.suffix,
            specialty=row.get("provider_specialty"),
            facility_name=row.get("facility_name"),
            latitude=lat,
            longitude=lon,
        )
        records.append(record)

    logger.info(f"Normalized {len(records)} CMS records")
    return records


def normalize_state_licenses(df: pd.DataFrame) -> list[PhysicianRecord]:
    """Normalize state license data."""
    records = []

    for idx, row in df.iterrows():
        parsed = parse_name(row.get("physician_name", ""))

        # Geocode from zip
        zip_code = row.get("address_zip")
        lat, lon = geocode_zip(zip_code) if pd.notna(zip_code) else (None, None)

        record = PhysicianRecord(
            source="license",
            source_id=_generate_source_id("license", row, idx),
            npi=None,  # Licenses don't have NPI
            name_raw=row.get("physician_name"),
            name_first=parsed.first,
            name_last=parsed.last,
            name_middle=parsed.middle,
            name_suffix=parsed.suffix,
            specialty=row.get("specialty"),
            facility_name=None,
            facility_address=row.get("address_line1"),
            facility_city=row.get("address_city"),
            facility_state=row.get("address_state"),
            facility_zip=zip_code,
            latitude=lat,
            longitude=lon,
        )
        records.append(record)

    logger.info(f"Normalized {len(records)} license records")
    return records


def normalize_hospital_affiliations(df: pd.DataFrame) -> list[PhysicianRecord]:
    """Normalize hospital affiliation data."""
    records = []

    for idx, row in df.iterrows():
        parsed = parse_name(row.get("physician_name", ""))

        npi = row.get("npi")
        if pd.isna(npi) or not npi:
            npi = None

        record = PhysicianRecord(
            source="hospital",
            source_id=_generate_source_id("hospital", row, idx),
            npi=npi,
            name_raw=row.get("physician_name"),
            name_first=parsed.first,
            name_last=parsed.last,
            name_middle=parsed.middle,
            name_suffix=parsed.suffix,
            specialty=row.get("department"),
            facility_name=row.get("hospital_name"),
            latitude=None,
            longitude=None,
        )
        records.append(record)

    logger.info(f"Normalized {len(records)} hospital records")
    return records


def normalize_publications(df: pd.DataFrame) -> list[PhysicianRecord]:
    """Normalize publication data."""
    records = []

    for idx, row in df.iterrows():
        parsed = parse_name(row.get("author_name", ""))

        # Try to parse affiliation for location
        affiliation = row.get("author_affiliation", "")
        city, state = None, None
        if affiliation and "," in affiliation:
            parts = [p.strip() for p in affiliation.split(",")]
            if len(parts) >= 2:
                # Last part might be state
                if len(parts[-1]) == 2:
                    state = parts[-1].upper()
                    city = parts[-2] if len(parts) > 2 else None

        record = PhysicianRecord(
            source="publication",
            source_id=_generate_source_id("publication", row, idx),
            npi=None,  # Publications don't have NPI
            name_raw=row.get("author_name"),
            name_first=parsed.first,
            name_last=parsed.last,
            name_middle=parsed.middle,
            name_suffix=parsed.suffix,
            specialty=None,  # Can't determine from publication
            facility_name=parts[0] if affiliation and parts else None,
            facility_city=city,
            facility_state=state,
            latitude=None,
            longitude=None,
        )
        records.append(record)

    logger.info(f"Normalized {len(records)} publication records")
    return records


def normalize_all(sources: dict[str, pd.DataFrame]) -> list[PhysicianRecord]:
    """Normalize all source data into PhysicianRecords."""
    all_records = []

    if "cms" in sources:
        all_records.extend(normalize_cms_claims(sources["cms"]))

    if "license" in sources:
        all_records.extend(normalize_state_licenses(sources["license"]))

    if "hospital" in sources:
        all_records.extend(normalize_hospital_affiliations(sources["hospital"]))

    if "publication" in sources:
        all_records.extend(normalize_publications(sources["publication"]))

    logger.info(f"Total normalized records: {len(all_records)}")
    return all_records
