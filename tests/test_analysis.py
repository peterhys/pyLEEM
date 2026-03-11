import pytest
from pyleem.analysis import Analyzer, AnalyzerGroup, ProfileAnalyzer
import matplotlib.pyplot as plt


class TestAnalyzer:
    """Test suite for Analyzer class."""

    def test_init(self, xps_raw_file):
        """Test analyzer instantiation and basic properties."""
        obj = Analyzer(xps_raw_file)

        assert obj.path == xps_raw_file
        assert obj.name == "test"
        assert obj.metadata == obj.reader.metadata

    def test_sort(self, tmp_path, metadata_bytes):
        """Test sorting objects by path."""
        file1 = tmp_path / "a_test.raw"
        file2 = tmp_path / "b_test.raw"

        file1.write_bytes(metadata_bytes + b"\xff" * 2000)
        file2.write_bytes(metadata_bytes + b"\xff" * 2000)

        obj1 = Analyzer(file1)
        obj2 = Analyzer(file2)
        assert obj1 < obj2

    def test_plot_image(self, xps_raw_file):
        """Test plot_image method.

        Plot testing is limited. Here we only test if the run is successful.
        """

        obj = Analyzer(xps_raw_file)

        # Test with provided axes
        fig, ax = plt.subplots()
        obj.plot_image(ax=ax)
        assert len(ax.images) == 1
        plt.close(fig)

        # Test without axes (creates its own)
        obj.plot_image(ax=None)
        assert len(plt.get_fignums()) == 1
        plt.close("all")


class TestProfileAnalyzer:
    """Test suite for ProfileAnalyzer class."""

    def test_corrdinates(self, xps_raw_file, roi):
        """Test coordinates transformation."""
        obj = ProfileAnalyzer(xps_raw_file, roi)
        assert obj.abscissa_label == "Pixel"
        assert obj.ordinate_label == "Intensity"

    def test_plot_profile(self, xps_raw_file, roi):
        """Test plot_profile method.

        Plot testing is limited. Here we only test if the run is successful.
        """
        obj = ProfileAnalyzer(xps_raw_file, roi)

        # Test with provided axes
        fig, ax = plt.subplots()
        obj.plot_profile(ax=ax)
        assert len(ax.lines) == 1
        plt.close(fig)

        # Test without axes (creates its own)
        obj.plot_profile(ax=None)
        assert len(plt.get_fignums()) == 1
        plt.close("all")


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
        voltages = analyzer_group.get_metas("Start Voltage")
        assert voltages == [114.0, 115.0, 116.0]

    def test_get_attrs(self, analyzer_group):
        """Test get_attrs returns the named attribute from each analyzer."""

        names = analyzer_group.get_attrs("name")
        assert names == [a.name for a in analyzer_group.analyzers]

    def test_get_time_intervals(self, analyzer_group):
        """Test that time_intervals starts at 0 and has the correct length.

        The files are temporary files, so the time intervals are very small.
        """
        intervals = analyzer_group.get_time_intervals()
        assert len(intervals) == 3
        assert intervals[0] == 0
        assert intervals[1] == 60
        assert intervals[2] == 120

    def test_find_onset_profiles(self, noisy_raw_file, xps_multiple_raw_files):
        """Test find_onset on a profile-based group returns a valid index."""
        files = [noisy_raw_file, noisy_raw_file] + xps_multiple_raw_files
        analyzer_group = AnalyzerGroup([Analyzer(path) for path in files])

        onset = analyzer_group.find_onset()
        assert onset == 1
