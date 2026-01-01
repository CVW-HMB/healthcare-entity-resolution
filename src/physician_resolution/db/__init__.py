"""Database module."""

from .bulk import bulk_insert_source_records, bulk_upsert_source_records
from .models import (
    Base,
    CanonicalPhysician,
    InfluenceScore,
    MatchPair,
    Referral,
    SourceCanonicalMapping,
    SourceRecord,
)
from .session import create_tables, drop_tables, get_engine, get_session

__all__ = [
    "get_engine",
    "get_session",
    "create_tables",
    "drop_tables",
    "Base",
    "SourceRecord",
    "CanonicalPhysician",
    "SourceCanonicalMapping",
    "MatchPair",
    "Referral",
    "InfluenceScore",
    "bulk_insert_source_records",
    "bulk_upsert_source_records",
]
