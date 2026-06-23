import pytest
from pyleem.analyzer import Analyzer, AnalyzerGroup


class TestAnalyzer:
    """Test suite for Analyzer class."""

    def test_init(self, xps_raw_file):
        """Test analyzer instantiation and basic properties."""
        obj = Analyzer(xps_raw_file)

        assert obj.path == xps_raw_file
        assert obj.name == "test"
        assert obj.metadata == obj.reader.metadata


class TestAnalyzerGroup:
    """Test suite for AnalyzerGroup class."""

    @pytest.fixture
    def analyzer_group(self, xps_multiple_raw_files):
        """Create an AnalyzerGroup for testing."""
        return AnalyzerGroup([Analyzer(path) for path in xps_multiple_raw_files])

    def test_iter(self, analyzer_group):
        """Test iteration yields all analyzer instances."""

        assert len(analyzer_group) == 3

    def test_getitem(self, analyzer_group):
        """Test indexing returns the correct analyzer."""
        assert analyzer_group[0] is analyzer_group.analyzers[0]

    def test_get_metas(self, analyzer_group):
        """Test get_metas returns a value for each file."""
        voltages = analyzer_group.get_metadata_list("Start Voltage")
        assert voltages == [114.0, 115.0, 116.0]

    def test_get_attrs(self, analyzer_group):
        """Test get_attrs returns the named attribute from each analyzer."""

        names = analyzer_group.get_attribute_list("name")
        assert names == [a.name for a in analyzer_group.analyzers]
