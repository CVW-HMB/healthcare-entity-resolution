"""Tests for name parsing."""

from physician_resolution.etl.name_parser import parse_name, standardize_name


class TestParseName:
    """Tests for parse_name function."""

    def test_last_first_format(self):
        """Test parsing LAST, FIRST format."""
        result = parse_name("SMITH, JOHN")
        assert result.last == "SMITH"
        assert result.first == "JOHN"
        assert result.middle is None

    def test_last_first_middle_format(self):
        """Test parsing LAST, FIRST MIDDLE format."""
        result = parse_name("SMITH, JOHN ANDREW")
        assert result.last == "SMITH"
        assert result.first == "JOHN"
        assert result.middle == "ANDREW"

    def test_last_first_middle_initial_format(self):
        """Test parsing LAST, FIRST M format."""
        result = parse_name("SMITH, JOHN A")
        assert result.last == "SMITH"
        assert result.first == "JOHN"
        assert result.middle == "A"

    def test_first_last_format(self):
        """Test parsing FIRST LAST format."""
        result = parse_name("John Smith")
        assert result.first == "John"
        assert result.last == "Smith"

    def test_first_middle_last_format(self):
        """Test parsing FIRST MIDDLE LAST format."""
        result = parse_name("John Andrew Smith")
        assert result.first == "John"
        assert result.middle == "Andrew"
        assert result.last == "Smith"

    def test_with_suffix_md(self):
        """Test parsing name with MD suffix."""
        result = parse_name("John Smith, MD")
        assert result.first == "John"
        assert result.last == "Smith"
        assert result.suffix == "MD"

    def test_with_suffix_do(self):
        """Test parsing name with DO suffix."""
        result = parse_name("John Smith, DO")
        assert result.suffix == "DO"

    def test_with_suffix_phd(self):
        """Test parsing name with PhD suffix."""
        result = parse_name("John Smith, PhD")
        assert result.suffix == "PHD"

    def test_with_title_dr(self):
        """Test parsing name with Dr. title."""
        result = parse_name("Dr. John Smith")
        assert result.title == "DR"
        assert result.first == "John"
        assert result.last == "Smith"

    def test_with_title_and_suffix(self):
        """Test parsing name with both title and suffix."""
        result = parse_name("Dr. John Smith, MD")
        assert result.title == "DR"
        assert result.first == "John"
        assert result.last == "Smith"
        assert result.suffix == "MD"

    def test_hyphenated_last_name(self):
        """Test parsing hyphenated last name."""
        result = parse_name("Mary Smith-Jones")
        assert result.first == "Mary"
        assert result.last == "Smith-Jones"

    def test_apostrophe_last_name(self):
        """Test parsing last name with apostrophe."""
        result = parse_name("Sean O'Brien")
        assert result.first == "Sean"
        assert result.last == "O'Brien"

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_name("")
        assert result.first is None
        assert result.last is None

    def test_none_input(self):
        """Test parsing None input."""
        result = parse_name(None)
        assert result.first is None
        assert result.last is None

    def test_single_name(self):
        """Test parsing single name."""
        result = parse_name("Smith")
        assert result.last == "Smith"
        assert result.first is None

    def test_initials_format(self):
        """Test parsing J.A. Smith format."""
        result = parse_name("J.A. Smith")
        assert result.first == "J"
        assert result.middle == "A"
        assert result.last == "Smith"

    def test_complex_suffix(self):
        """Test parsing complex suffix like MD, FACS."""
        result = parse_name("John Smith, MD, FACS")
        assert result.first == "John"
        assert result.last == "Smith"
        assert "MD" in result.suffix
        assert "FACS" in result.suffix


class TestStandardizeName:
    """Tests for standardize_name function."""

    def test_basic_standardization(self):
        """Test basic name standardization."""
        from physician_resolution.schemas.records import ParsedName

        parsed = ParsedName(first="John", last="Smith", middle="Andrew")
        result = standardize_name(parsed)
        assert result == "SMITH, JOHN A"

    def test_no_middle_name(self):
        """Test standardization without middle name."""
        from physician_resolution.schemas.records import ParsedName

        parsed = ParsedName(first="John", last="Smith")
        result = standardize_name(parsed)
        assert result == "SMITH, JOHN"

    def test_empty_parsed_name(self):
        """Test standardization of empty parsed name."""
        from physician_resolution.schemas.records import ParsedName

        parsed = ParsedName()
        result = standardize_name(parsed)
        assert result == ""

    def test_last_name_only(self):
        """Test standardization with only last name."""
        from physician_resolution.schemas.records import ParsedName

        parsed = ParsedName(last="Smith")
        result = standardize_name(parsed)
        assert result == "SMITH,"
