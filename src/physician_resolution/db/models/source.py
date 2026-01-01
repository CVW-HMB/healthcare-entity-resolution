import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SourceRecord(Base):
    """Raw ingested physician record from a data source."""

    __tablename__ = "source_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)

    npi: Mapped[str | None] = mapped_column(String(10))
    name_raw: Mapped[str | None] = mapped_column(String(500))
    name_first: Mapped[str | None] = mapped_column(String(100))
    name_last: Mapped[str | None] = mapped_column(String(100))
    name_middle: Mapped[str | None] = mapped_column(String(50))

    specialty: Mapped[str | None] = mapped_column(String(200))

    facility_name: Mapped[str | None] = mapped_column(String(500))
    facility_city: Mapped[str | None] = mapped_column(String(100))
    facility_state: Mapped[str | None] = mapped_column(String(2))
    facility_zip: Mapped[str | None] = mapped_column(String(10))

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
