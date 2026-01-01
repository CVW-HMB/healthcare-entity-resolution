import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SourceCanonicalMapping(Base):
    """Maps source records to canonical physicians."""

    __tablename__ = "source_canonical_mapping"

    source_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_records.id"),
        primary_key=True,
    )
    canonical_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("canonical_physicians.id"),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    match_type: Mapped[str | None] = mapped_column(String(50))
