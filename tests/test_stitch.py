import pytest
import numpy as np
from pyleem.analyzer import ProfileAnalyzer, Analyzer
from pyleem.analysis.stitch import StitchAnalyzer


class TestStitchAnalyzer:
    """Test suite for StitchAnalyzer class."""

    @pytest.fixture
    def stitch_analyzers(self, xps_multiple_raw_files, roi):
        """Create 3 ProfileAnalyzers with overlapping abscissa ranges.

        Each analyzer has a profile of length 128, with abscissas shifted by
        40 per step so adjacent profiles overlap.
            - Analyzer 0: abscissa [0..127]
            - Analyzer 1: abscissa [40..167]
            - Analyzer 2: abscissa [80..207]
        The ordinate is set to the index of the analyzer (0, 1, 2) for verification.
        """
        analyzers = []
        for i in range(3):
            obj = ProfileAnalyzer(xps_multiple_raw_files[i], roi)
            obj._abscissa = np.arange(i * 40, i * 40 + 128, dtype=float)
            obj._ordinate = np.ones(128) * i
            obj._abscissa_label = "Pixel"
            obj._ordinate_label = "Value"
            analyzers.append(obj)
        return analyzers

    def test_init(self, stitch_analyzers):
        """Test StitchGroup initialization and stitch points."""
        obj = StitchAnalyzer(stitch_analyzers, stitch_method="start")
        assert obj.stitch_points == [40.0, 80.0]

    def test_custom_stitch_points(self, stitch_analyzers):
        """Test StitchGroup with explicit stitch points."""
        stitch_points = [45.0, 85.0]
        obj = StitchAnalyzer(stitch_analyzers, stitch_points=stitch_points)
        assert obj.stitch_points == stitch_points

    def test_stitch_profile(self, stitch_analyzers):
        """Test StitchAnalyzer stitch_profile method."""
        obj = StitchAnalyzer(stitch_analyzers, stitch_method="start")

        assert np.array_equal(obj.abscissa, np.arange(208, dtype=float))
        assert np.array_equal(obj.ordinate, [0] * 40 + [1] * 40 + [2] * 128)
        assert obj.abscissa_label == "Pixel"
        assert obj.ordinate_label == "Value"

    def test_metadata(self, stitch_analyzers):
        """Test StitchAnalyzer metadata property."""
        obj = StitchAnalyzer(stitch_analyzers, stitch_method="start")
        assert obj.metadata == {}

        obj = StitchAnalyzer(
            stitch_analyzers,
            stitch_method="start",
            metadata={"Start Voltage": (10, "eV")},
        )
        assert obj.metadata == {"Start Voltage": (10, "eV")}

    def test_validation_errors(self, stitch_analyzers, xps_raw_file):
        """Test StitchAnalyzer validation errors for invalid inputs."""
        with pytest.raises(AssertionError, match="Expected 2 stitch points, got 1"):
            StitchAnalyzer(stitch_analyzers, stitch_points=[50.0])

        mixed = [Analyzer(xps_raw_file)] + stitch_analyzers[:2]
        with pytest.raises(TypeError, match="All analyzers must be the same type"):
            StitchAnalyzer(mixed)

        stitch_analyzers[1]._abscissa_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Abscissa labels don't match"):
            StitchAnalyzer(stitch_analyzers)

        stitch_analyzers[1]._abscissa_label = stitch_analyzers[0].abscissa_label
        stitch_analyzers[1]._ordinate_label = "DifferentLabel"
        with pytest.raises(ValueError, match="Ordinate labels don't match"):
            StitchAnalyzer(stitch_analyzers)
