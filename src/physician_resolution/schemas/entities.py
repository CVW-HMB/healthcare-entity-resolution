from dataclasses import dataclass, field


@dataclass
class CanonicalPhysician:
    """Resolved canonical physician entity."""

    canonical_id: str
    confidence: float

    npi: str | None = None
    name: str | None = None
    specialty: str | None = None
    primary_facility: str | None = None
    city: str | None = None
    state: str | None = None

    all_facilities: list[str] = field(default_factory=list)
    source_records: list[str] = field(default_factory=list)
    source_count: int = 0

    def to_dict(self) -> dict:
        return {
            "canonical_id": self.canonical_id,
            "confidence": self.confidence,
            "npi": self.npi,
            "name": self.name,
            "specialty": self.specialty,
            "primary_facility": self.primary_facility,
            "city": self.city,
            "state": self.state,
            "all_facilities": self.all_facilities,
            "source_records": self.source_records,
            "source_count": self.source_count,
        }
