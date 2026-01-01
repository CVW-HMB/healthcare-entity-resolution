"""Tests for similarity scoring."""

from physician_resolution.matching.similarity import (
    calculate_first_name_similarity,
    calculate_last_name_similarity,
    calculate_location_score,
    calculate_name_similarity,
    calculate_npi_match,
    calculate_similarity,
    calculate_specialty_similarity,
)


class TestNameSimilarity:
    """Tests for name similarity functions."""

    def test_exact_match(self):
        """Test exact name match."""
        score = calculate_name_similarity("JOHN SMITH", "JOHN SMITH")
        assert score == 1.0

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        score = calculate_name_similarity("John Smith", "JOHN SMITH")
        assert score == 1.0

    def test_similar_names(self):
        """Test similar names get high score."""
        score = calculate_name_similarity("JOHN SMITH", "JOHN SMYTH")
        assert score > 0.8

    def test_different_names(self):
        """Test different names get low score."""
        score = calculate_name_similarity("JOHN SMITH", "MARY JONES")
        assert score < 0.5

    def test_reordered_names(self):
        """Test reordered names still match."""
        score = calculate_name_similarity("SMITH, JOHN", "JOHN SMITH")
        assert score > 0.8

    def test_abbreviated_name(self):
        """Test abbreviated name matches."""
        score = calculate_name_similarity("J SMITH", "JOHN SMITH")
        assert score > 0.6

    def test_empty_name(self):
        """Test empty name returns 0."""
        score = calculate_name_similarity("", "JOHN SMITH")
        assert score == 0.0

    def test_none_name(self):
        """Test None name returns 0."""
        score = calculate_name_similarity(None, "JOHN SMITH")
        assert score == 0.0


class TestFirstNameSimilarity:
    """Tests for first name similarity."""

    def test_exact_match(self):
        """Test exact first name match."""
        score = calculate_first_name_similarity("John", "John")
        assert score == 1.0

    def test_initial_matches_full(self):
        """Test initial matches full name."""
        score = calculate_first_name_similarity("J", "John")
        assert score == 0.8

    def test_full_matches_initial(self):
        """Test full name matches initial."""
        score = calculate_first_name_similarity("John", "J")
        assert score == 0.8

    def test_missing_first_name(self):
        """Test missing first name returns neutral score."""
        score = calculate_first_name_similarity(None, "John")
        assert score == 0.5


class TestLastNameSimilarity:
    """Tests for last name similarity."""

    def test_exact_match(self):
        """Test exact last name match."""
        score = calculate_last_name_similarity("Smith", "Smith")
        assert score == 1.0

    def test_apostrophe_handling(self):
        """Test apostrophe is handled."""
        score = calculate_last_name_similarity("O'Brien", "OBrien")
        assert score == 1.0

    def test_hyphen_handling(self):
        """Test hyphen is handled."""
        score = calculate_last_name_similarity("Smith-Jones", "SmithJones")
        assert score == 1.0

    def test_missing_last_name(self):
        """Test missing last name returns 0."""
        score = calculate_last_name_similarity(None, "Smith")
        assert score == 0.0


class TestNPIMatch:
    """Tests for NPI matching."""

    def test_exact_match(self):
        """Test exact NPI match."""
        score = calculate_npi_match("1234567890", "1234567890")
        assert score == 1.0

    def test_different_npis(self):
        """Test different NPIs return conflict score."""
        score = calculate_npi_match("1234567890", "0987654321")
        assert score == 0.0

    def test_missing_npi(self):
        """Test missing NPI returns None."""
        score = calculate_npi_match(None, "1234567890")
        assert score is None

    def test_both_missing(self):
        """Test both missing returns None."""
        score = calculate_npi_match(None, None)
        assert score is None

    def test_invalid_npi_length(self):
        """Test invalid NPI length returns None."""
        score = calculate_npi_match("12345", "1234567890")
        assert score is None


class TestLocationScore:
    """Tests for location scoring."""

    def test_same_location(self):
        """Test same location returns high score."""
        score = calculate_location_score(42.36, -71.05, 42.36, -71.05)
        assert score == 1.0

    def test_nearby_locations(self):
        """Test nearby locations return high score."""
        # About 5 miles apart
        score = calculate_location_score(42.36, -71.05, 42.40, -71.05)
        assert score >= 0.7

    def test_same_state_fallback(self):
        """Test same state returns moderate score when no coords."""
        score = calculate_location_score(None, None, None, None, "MA", "MA")
        assert score == 0.3

    def test_different_state_fallback(self):
        """Test different states return low score."""
        score = calculate_location_score(None, None, None, None, "MA", "CA")
        assert score == 0.1


class TestSpecialtySimilarity:
    """Tests for specialty matching."""

    def test_exact_match(self):
        """Test exact specialty match."""
        score = calculate_specialty_similarity("Internal Medicine", "Internal Medicine")
        assert score == 1.0

    def test_abbreviation_match(self):
        """Test abbreviation matches full name."""
        score = calculate_specialty_similarity("Internal Medicine", "Internal Med")
        assert score == 1.0

    def test_different_specialties(self):
        """Test different specialties return low score."""
        score = calculate_specialty_similarity("Cardiology", "Dermatology")
        assert score == 0.0

    def test_missing_specialty(self):
        """Test missing specialty returns None."""
        score = calculate_specialty_similarity(None, "Cardiology")
        assert score is None


class TestCalculateSimilarity:
    """Tests for overall similarity calculation."""

    def test_with_npi_match(self, sample_records):
        """Test similarity when NPIs match."""
        rec1 = sample_records[0]  # Has NPI 1234567890
        rec2 = sample_records[2]  # Also has NPI 1234567890

        scores = calculate_similarity(rec1, rec2)
        assert scores.npi_match == 1.0
        assert scores.overall_score >= 0.9

    def test_with_npi_conflict(self, sample_records):
        """Test similarity when NPIs conflict."""
        rec1 = sample_records[0]  # NPI 1234567890
        rec2 = sample_records[3]  # NPI 9876543210

        scores = calculate_similarity(rec1, rec2)
        assert scores.npi_match == 0.0
        assert scores.overall_score == 0.0

    def test_without_npi(self, sample_records):
        """Test similarity when NPI is missing."""
        rec1 = sample_records[0]  # Has NPI
        rec2 = sample_records[1]  # No NPI

        scores = calculate_similarity(rec1, rec2)
        assert scores.npi_match is None
        assert 0 < scores.overall_score < 1
