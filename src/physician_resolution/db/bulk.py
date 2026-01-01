from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..logging import get_logger
from ..schemas.records import PhysicianRecord
from .models import SourceRecord
from .session import get_engine

logger = get_logger("db.bulk")


def _record_to_row(r: PhysicianRecord) -> dict:
    return {
        "source": r.source,
        "source_id": r.source_id,
        "npi": r.npi,
        "name_raw": r.name_raw,
        "name_first": r.name_first,
        "name_last": r.name_last,
        "name_middle": r.name_middle,
        "specialty": r.specialty,
        "facility_name": r.facility_name,
        "facility_city": r.facility_city,
        "facility_state": r.facility_state,
        "facility_zip": r.facility_zip,
        "latitude": r.latitude,
        "longitude": r.longitude,
    }


def bulk_insert_source_records(records: list[PhysicianRecord], batch_size: int = 1000) -> int:
    """Bulk insert physician records. Returns number inserted."""
    if not records:
        return 0

    engine = get_engine()
    total_inserted = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        rows = [_record_to_row(r) for r in batch]

        with engine.connect() as conn:
            conn.execute(insert(SourceRecord), rows)
            conn.commit()

        total_inserted += len(batch)
        logger.info(f"Inserted batch: {total_inserted}/{len(records)} records")

    return total_inserted


def bulk_upsert_source_records(records: list[PhysicianRecord], batch_size: int = 1000) -> int:
    """Bulk upsert physician records. Returns number upserted."""
    if not records:
        return 0

    engine = get_engine()
    total_upserted = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        rows = [_record_to_row(r) for r in batch]

        stmt = pg_insert(SourceRecord).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "source_id"],
            set_={
                "npi": stmt.excluded.npi,
                "name_raw": stmt.excluded.name_raw,
                "name_first": stmt.excluded.name_first,
                "name_last": stmt.excluded.name_last,
                "name_middle": stmt.excluded.name_middle,
                "specialty": stmt.excluded.specialty,
                "facility_name": stmt.excluded.facility_name,
                "facility_city": stmt.excluded.facility_city,
                "facility_state": stmt.excluded.facility_state,
                "facility_zip": stmt.excluded.facility_zip,
                "latitude": stmt.excluded.latitude,
                "longitude": stmt.excluded.longitude,
            },
        )

        with engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

        total_upserted += len(batch)
        logger.info(f"Upserted batch: {total_upserted}/{len(records)} records")

    return total_upserted
