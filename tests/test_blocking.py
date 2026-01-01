"""Tests for blocking strategies."""

from physician_resolution.matching.blocking import (
    block_by_last_name_first_initial,
    block_by_last_name_state,
    block_by_npi,
    block_by_soundex_state,
    get_candidate_pairs,
)
from physician_resolution.schemas.records import PhysicianRecord


class TestBlockByNPI:
    """Tests for NPI-based blocking."""

    def test_groups_by_npi(self, sample_records):
        """Test records with same NPI are grouped."""
        blocks = block_by_npi(sample_records)

        # Should have at least one block (records with NPI 1234567890)
        assert len(blocks) >= 1

        # Check NPI 1234567890 block
        if "1234567890" in blocks:
            block = blocks["1234567890"]
            assert len(block) == 2  # cms_001 and hosp_001

    def test_ignores_missing_npi(self, sample_records):
        """Test records without NPI are not included."""
        blocks = block_by_npi(sample_records)

        for npi, block in blocks.items():
            for record in block:
                assert record.npi is not None

    def test_requires_multiple_records(self):
        """Test blocks with single record are filtered out."""
        records = [
            PhysicianRecord(source="cms", source_id="a", npi="1111111111"),
            PhysicianRecord(source="cms", source_id="b", npi="2222222222"),
        ]

        blocks = block_by_npi(records)
        assert len(blocks) == 0  # Each NPI only appears once


class TestBlockByLastNameState:
    """Tests for last name + state blocking."""

    def test_groups_by_last_name_and_state(self, sample_records):
        """Test records with same last name and state are grouped."""
        blocks = block_by_last_name_state(sample_records)

        # Should have blocks
        assert len(blocks) >= 1

        # Check SMITH|MA block
        if "SMITH|MA" in blocks:
            block = blocks["SMITH|MA"]
            assert len(block) == 3

    def test_different_states_different_blocks(self):
        """Test same name in different states are separate."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last="Smith", facility_state="MA"),
            PhysicianRecord(source="b", source_id="b", name_last="Smith", facility_state="CA"),
        ]

        blocks = block_by_last_name_state(records)

        # Each should be in its own block (but filtered out since size 1)
        assert len(blocks) == 0

    def test_ignores_missing_last_name(self):
        """Test records without last name are ignored."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last=None, facility_state="MA"),
            PhysicianRecord(source="b", source_id="b", name_last="Smith", facility_state="MA"),
        ]

        blocks = block_by_last_name_state(records)
        assert len(blocks) == 0  # Only one record with last name


class TestBlockBySoundexState:
    """Tests for phonetic blocking."""

    def test_groups_similar_sounding_names(self):
        """Test similar sounding names are grouped."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last="Smith", facility_state="MA"),
            PhysicianRecord(source="b", source_id="b", name_last="Smyth", facility_state="MA"),
        ]

        blocks = block_by_soundex_state(records)

        # Smith and Smyth should be in same block
        assert len(blocks) == 1

    def test_different_sounds_different_blocks(self):
        """Test different sounding names are separate."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last="Smith", facility_state="MA"),
            PhysicianRecord(source="b", source_id="b", name_last="Jones", facility_state="MA"),
        ]

        blocks = block_by_soundex_state(records)

        # Should be separate (but filtered since size 1 each)
        assert len(blocks) == 0


class TestBlockByLastNameFirstInitial:
    """Tests for last name + first initial blocking."""

    def test_groups_by_last_name_and_initial(self):
        """Test records with same last name and first initial are grouped."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last="Smith", name_first="John"),
            PhysicianRecord(source="b", source_id="b", name_last="Smith", name_first="James"),
            PhysicianRecord(source="c", source_id="c", name_last="Smith", name_first="Mary"),
        ]

        blocks = block_by_last_name_first_initial(records)

        # Should have SMITH|J block with 2 records
        assert "SMITH|J" in blocks
        assert len(blocks["SMITH|J"]) == 2

    def test_different_initials_different_blocks(self):
        """Test same last name with different initials are separate."""
        records = [
            PhysicianRecord(source="a", source_id="a", name_last="Smith", name_first="John"),
            PhysicianRecord(source="b", source_id="b", name_last="Smith", name_first="Mary"),
        ]

        blocks = block_by_last_name_first_initial(records)

        # Each in its own block (filtered out since size 1)
        assert len(blocks) == 0


class TestGetCandidatePairs:
    """Tests for candidate pair generation."""

    def test_generates_pairs(self, sample_records):
        """Test pairs are generated."""
        pairs = get_candidate_pairs(sample_records)
        assert len(pairs) > 0

    def test_pairs_are_unique(self, sample_records):
        """Test no duplicate pairs."""
        pairs = get_candidate_pairs(sample_records)
        pair_keys = set()

        for rec1, rec2 in pairs:
            key = tuple(sorted([rec1.source_id, rec2.source_id]))
            assert key not in pair_keys
            pair_keys.add(key)

    def test_pairs_are_ordered(self, sample_records):
        """Test pairs have consistent ordering."""
        pairs = get_candidate_pairs(sample_records)

        for rec1, rec2 in pairs:
            assert rec1.source_id < rec2.source_id

    def test_respects_soundex_flag(self, sample_records):
        """Test soundex can be disabled."""
        pairs_with = get_candidate_pairs(sample_records, use_soundex=True)
        pairs_without = get_candidate_pairs(sample_records, use_soundex=False)

        # With soundex should have >= pairs than without
        assert len(pairs_with) >= len(pairs_without)
