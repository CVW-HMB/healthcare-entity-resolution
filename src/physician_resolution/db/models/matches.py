import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MatchPair(Base):
    """Record of a match comparison between two source records."""

    __tablename__ = "match_pairs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id_1: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_records.id"),
        nullable=False,
    )
    source_id_2: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_records.id"),
        nullable=False,
    )
    similarity_score: Mapped[float | None] = mapped_column(Float)
    match_decision: Mapped[str | None] = mapped_column(String(20))
    match_type: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
