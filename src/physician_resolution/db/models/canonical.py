from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CanonicalPhysician(Base):
    """Resolved canonical physician entity."""

    __tablename__ = "canonical_physicians"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # PHY_{npi} or PHY_{uuid}

    npi: Mapped[str | None] = mapped_column(String(10))
    name: Mapped[str | None] = mapped_column(String(200))
    specialty: Mapped[str | None] = mapped_column(String(200))
    primary_facility: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(2))

    confidence_score: Mapped[float | None] = mapped_column(Float)
    source_count: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
