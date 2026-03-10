import pytest
import numpy as np
from pyleem.analysis import Analyzer, AnalyzerGroup, ProfileAnalyzer, StitchAnalyzer
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


class TestStitchAnalyzer:
    """Test suite for StitchAnalyzer class."""

    @pytest.fixture
    def stitch_analyzers(self, xps_multiple_raw_files, roi):
        """Create 3 ProfileAnalyzers with overlapping abscissa ranges.

        Each analyzer has a profile of length 60, with abscissas shifted by
        40 per step so adjacent profiles overlap by 88 points.
            - Analyzer 0: abscissa [0..127]
            - Analyzer 1: abscissa [40..167]
            - Analyzer 2: abscissa [80..207]
        """

        analyzers = []
        for i in range(3):
            obj = ProfileAnalyzer(xps_multiple_raw_files[i], roi)
            # redefine the abscissa to allow stitching
            obj._abscissa = np.arange(i * 40, i * 40 + 128)
            analyzers.append(obj)
        return analyzers

    def test_init(self, stitch_analyzers):
        """Test StitchAnalyzer initialization and basic attributes."""
        obj = StitchAnalyzer(stitch_analyzers, method="start")

        assert obj.stitch_points == [40.0, 80.0]

    def test_custom_stitch_points(self, stitch_analyzers):
        """Test StitchAnalyzer with explicit stitch points."""
        stitch_points = [45.0, 85.0]
        obj = StitchAnalyzer(stitch_analyzers, stitch_points=stitch_points)

        assert obj.stitch_points == stitch_points
        assert len(obj.abscissa) == len(obj.ordinate)

    def test_validation_errors(self, xps_raw_file, stitch_analyzers):
        """Test StitchAnalyzer validation errors for invalid inputs."""
        # Test wrong number of stitch points
        with pytest.raises(ValueError, match="Expected 2 stitch points, got 1"):
            StitchAnalyzer(stitch_analyzers, stitch_points=[50.0])

        # Test mismatched analyzer types
        mixed = [Analyzer(xps_raw_file)] + stitch_analyzers[:2]
        with pytest.raises(TypeError, match="All analyzers must be the same type"):
            StitchAnalyzer(mixed)

        # Test mismatched abscissa labels
        stitch_analyzers[1]._abscissa_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Abscissa labels don't match"):
            StitchAnalyzer(stitch_analyzers)

        # Reset and test mismatched ordinate labels
        stitch_analyzers[1]._abscissa_label = stitch_analyzers[0].abscissa_label
        stitch_analyzers[1]._ordinate_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Ordinate labels don't match"):
            StitchAnalyzer(stitch_analyzers)

    def test_getattr(self, stitch_analyzers):
        """Test StitchAnalyzer inherits callable methods and raises AttributeError for unknown ones."""
        obj = StitchAnalyzer(stitch_analyzers)

        assert callable(obj.plot_profile)
        with pytest.raises(AttributeError):
            _ = obj.non_existent_attribute


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
