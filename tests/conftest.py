"""Pytest fixtures for testing."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from physician_resolution.schemas.records import ParsedName, PhysicianRecord


@pytest.fixture
def sample_physician_record():
    """Create a sample physician record."""
    return PhysicianRecord(
        source="cms",
        source_id="test_001",
        npi="1234567890",
        name_raw="SMITH, JOHN A",
        name_first="JOHN",
        name_last="SMITH",
        name_middle="A",
        specialty="Internal Medicine",
        facility_name="Memorial Hospital",
        facility_city="Boston",
        facility_state="MA",
        facility_zip="02101",
    )


@pytest.fixture
def sample_records():
    """Create a list of sample physician records for testing."""
    return [
        PhysicianRecord(
            source="cms",
            source_id="cms_001",
            npi="1234567890",
            name_raw="SMITH, JOHN A",
            name_first="JOHN",
            name_last="SMITH",
            name_middle="A",
            specialty="Internal Medicine",
            facility_state="MA",
        ),
        PhysicianRecord(
            source="license",
            source_id="lic_001",
            npi=None,
            name_raw="John A. Smith, MD",
            name_first="John",
            name_last="Smith",
            name_middle="A",
            specialty="Internal Med",
            facility_state="MA",
        ),
        PhysicianRecord(
            source="hospital",
            source_id="hosp_001",
            npi="1234567890",
            name_raw="Dr. John Smith",
            name_first="John",
            name_last="Smith",
            name_middle=None,
            specialty="Internal Medicine",
            facility_state="MA",
        ),
        PhysicianRecord(
            source="cms",
            source_id="cms_002",
            npi="9876543210",
            name_raw="JONES, MARY B",
            name_first="MARY",
            name_last="JONES",
            name_middle="B",
            specialty="Cardiology",
            facility_state="NY",
        ),
        PhysicianRecord(
            source="license",
            source_id="lic_002",
            npi=None,
            name_raw="Mary Jones, MD",
            name_first="Mary",
            name_last="Jones",
            name_middle=None,
            specialty="Cardiovascular Disease",
            facility_state="NY",
        ),
    ]


@pytest.fixture
def sample_matches():
    """Create sample match tuples."""
    return [
        ("cms_001", "lic_001", 0.92),
        ("cms_001", "hosp_001", 0.95),
        ("lic_001", "hosp_001", 0.88),
        ("cms_002", "lic_002", 0.90),
    ]


@pytest.fixture
def sample_parsed_name():
    """Create a sample parsed name."""
    return ParsedName(
        first="John",
        last="Smith",
        middle="Andrew",
        suffix="MD",
        title="Dr",
    )
