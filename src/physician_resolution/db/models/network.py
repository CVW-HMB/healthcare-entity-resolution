import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Referral(Base):
    """Referral relationship between two physicians."""

    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referring_physician_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("canonical_physicians.id"),
        nullable=False,
    )
    receiving_physician_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("canonical_physicians.id"),
        nullable=False,
    )
    referral_count: Mapped[int | None] = mapped_column(Integer)
    last_referral_date: Mapped[date | None] = mapped_column(Date)


class InfluenceScore(Base):
    """Influence metrics for a physician."""

    __tablename__ = "influence_scores"

    physician_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("canonical_physicians.id"),
        primary_key=True,
    )
    pagerank_score: Mapped[float | None] = mapped_column(Float)
    referral_in_count: Mapped[int | None] = mapped_column(Integer)
    referral_out_count: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
