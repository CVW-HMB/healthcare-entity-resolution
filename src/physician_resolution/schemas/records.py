from dataclasses import dataclass


@dataclass
class ParsedName:
    """Parsed components of a physician name."""

    first: str | None = None
    last: str | None = None
    middle: str | None = None
    suffix: str | None = None  # MD, DO, PhD, Jr, III
    title: str | None = None  # Dr., Prof.

    def standardized(self) -> str:
        """Return canonical format: 'LAST, FIRST M'"""
        parts = []
        if self.last:
            parts.append(self.last.upper())
        if self.first:
            first_part = self.first.upper()
            if self.middle:
                first_part += f" {self.middle[0].upper()}"
            if parts:
                parts[0] += ","
            parts.append(first_part)
        return " ".join(parts)


@dataclass
class PhysicianRecord:
    """Normalized physician record from any source."""

    source: str  # "cms", "license", "hospital", "publication"
    source_id: str  # Original ID from source

    # Identifiers
    npi: str | None = None

    # Name fields
    name_raw: str | None = None
    name_first: str | None = None
    name_last: str | None = None
    name_middle: str | None = None
    name_suffix: str | None = None

    # Professional info
    specialty: str | None = None

    # Location
    facility_name: str | None = None
    facility_address: str | None = None
    facility_city: str | None = None
    facility_state: str | None = None
    facility_zip: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def standardized_name(self) -> str:
        """Return standardized name format."""
        parts = []
        if self.name_last:
            parts.append(self.name_last.upper())
        if self.name_first:
            first_part = self.name_first.upper()
            if self.name_middle:
                first_part += f" {self.name_middle[0].upper()}"
            if parts:
                parts[0] += ","
            parts.append(first_part)
        return " ".join(parts)
