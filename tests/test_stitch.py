import pytest
import numpy as np
from pyleem.analysis import ProfileAnalyzer, Analyzer
from pyleem.stitch import StitchAnalyzer, StitchGroup


class TestStitchAnalyzer:
    """Test suite for StitchAnalyzer class."""

    @pytest.fixture
    def stitch_analyzer(self):
        """Create a minimal StitchAnalyzer backed by ProfileAnalyzer methods."""
        return StitchAnalyzer(
            ProfileAnalyzer,
            abscissa=np.arange(10, dtype=float),
            ordinate=np.ones(10),
            abscissa_label="Pixel",
            ordinate_label="Value",
            metadata={"Start Voltage": (10, "eV")},
        )

    def test_init(self, stitch_analyzer):
        """Test StitchAnalyzer stores all constructor arguments.

        And overwrite default attributes.
        """

        assert np.array_equal(stitch_analyzer.abscissa, np.arange(10, dtype=float))
        assert np.array_equal(stitch_analyzer.ordinate, np.ones(10))
        assert stitch_analyzer.abscissa_label == "Pixel"
        assert stitch_analyzer.ordinate_label == "Value"

    def test_getattr_callable(self, stitch_analyzer):
        """Test that callable methods from analyzer_class are forwarded."""
        assert callable(stitch_analyzer.plot_profile)

    def test_getattr_unknown_raises(self, stitch_analyzer):
        """Test AttributeError is raised for unknown attributes."""
        with pytest.raises(
            AttributeError,
            match="'ProfileAnalyzer' object has no attribute 'attribute'",
        ):
            _ = stitch_analyzer.attribute

    def test_metadata(self, stitch_analyzer):
        """Test metadata is preserved."""
        assert stitch_analyzer.metadata["Start Voltage"] == (10, "eV")


class TestStitchGroup:
    """Test suite for StitchGroup class."""

    @pytest.fixture
    def stitch_analyzers(self, xps_multiple_raw_files, roi):
        """Create 3 ProfileAnalyzers with overlapping abscissa ranges.

        Each analyzer has a profile of length 128, with abscissas shifted by
        40 per step so adjacent profiles overlap.
            - Analyzer 0: abscissa [0..127]
            - Analyzer 1: abscissa [40..167]
            - Analyzer 2: abscissa [80..207]
        """
        analyzers = []
        for i in range(3):
            obj = ProfileAnalyzer(xps_multiple_raw_files[i], roi)
            obj._abscissa = np.arange(i * 40, i * 40 + 128)
            analyzers.append(obj)
        return analyzers

    def test_init(self, stitch_analyzers):
        """Test StitchGroup initialization and stitch points."""
        obj = StitchGroup(stitch_analyzers, method="start")
        assert obj.stitch_points == [40.0, 80.0]

    def test_stitched_analyzer(self, stitch_analyzers):
        """Test stitched_analyzer property returns a StitchAnalyzer."""
        obj = StitchGroup(stitch_analyzers)
        assert isinstance(obj.stitched_analyzer, StitchAnalyzer)
        assert len(obj.stitched_analyzer.abscissa) == len(
            obj.stitched_analyzer.ordinate
        )

    def test_custom_stitch_points(self, stitch_analyzers):
        """Test StitchGroup with explicit stitch points."""
        stitch_points = [45.0, 85.0]
        obj = StitchGroup(stitch_analyzers, stitch_points=stitch_points)
        assert obj.stitch_points == stitch_points
        assert len(obj.stitched_analyzer.abscissa) == len(
            obj.stitched_analyzer.ordinate
        )

    def test_validation_errors(self, xps_raw_file, stitch_analyzers):
        """Test StitchGroup validation errors for invalid inputs."""
        with pytest.raises(AssertionError, match="Expected 2 stitch points, got 1"):
            StitchGroup(stitch_analyzers, stitch_points=[50.0])

        mixed = [Analyzer(xps_raw_file)] + stitch_analyzers[:2]
        with pytest.raises(TypeError, match="All analyzers must be the same type"):
            StitchGroup(mixed)

        stitch_analyzers[1]._abscissa_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Abscissa labels don't match"):
            StitchGroup(stitch_analyzers)

        stitch_analyzers[1]._abscissa_label = stitch_analyzers[0].abscissa_label
        stitch_analyzers[1]._ordinate_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Ordinate labels don't match"):
            StitchGroup(stitch_analyzers)
