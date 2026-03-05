import pytest
import numpy as np
from pyleem.sees import SEES_onset, SEESAnalyzer, SEESGroup


def test_sees_onset(sees_array):
    """Test SEES_onset with ramp profile.

    The profile is a sigmoid function.
    """
    profile = sees_array[0, :]
    pk_idx, slope, onset_pos = SEES_onset(profile)

    assert pk_idx == 57
    assert slope == 12.5
    assert np.isclose(onset_pos, 40.0, rtol=1e-2)


@pytest.fixture
def sees_analyzer(sees_raw_file, roi):
    """Create a SEESAnalyzer instance."""
    return SEESAnalyzer(sees_raw_file, roi, sigma=10)


class TestSEESAnalyzer:
    """Test SEESAnalyzer class."""

    @pytest.fixture
    def sees_analyzer(self, sees_raw_file, roi_calibrated):
        """Create a SEESAnalyzer instance."""
        return SEESAnalyzer(sees_raw_file, roi_calibrated, sigma=0)

    def test_processing(self, sees_analyzer):
        """Test processing method."""
        sees_analyzer.preprocess()
        assert sees_analyzer.pk_idx == 57  # filtered profile changes pk_idx
        assert sees_analyzer.slope == 12.5
        assert np.isclose(sees_analyzer.onset_pos, 40.0, rtol=1e-2)
        assert np.isclose(sees_analyzer.surface_potential, -2.5, rtol=1e-2)
        assert sees_analyzer.onset == 0.0

    def test_transform_abscissa(self, sees_analyzer):
        """Test transform_abscissa method."""

        # given the 16 pixel per ev
        # the abscissa should be 0 to 8 eV after conversion
        sees_analyzer.abscissa = np.linspace(0, 8, 128, endpoint=False)
        sees_analyzer.abscissa_label = "Energy [eV]"

    def test_sees_onset(self, sees_analyzer):
        """Test SEES_onset with ramp profile.

        The profile is a sigmoid function.
        """
        profile = sees_analyzer.profile
        pk_idx, slope, onset_pos = SEES_onset(profile)
        assert pk_idx == 57
        assert slope == 12.5
        assert np.isclose(onset_pos, 40.0, rtol=1e-2)


class TestSEESGroup:
    """Test SEESGroup class."""

    @pytest.fixture
    def sees_group(self, sees_multiple_raw_files, roi):
        """Create a SEESGroup instance."""
        return SEESGroup(sees_multiple_raw_files, roi, sigma=0)

    def test_calibrate(self, sees_group):
        """Test calibration without provided parameters."""
        cal_result = sees_group.calibrate({}, plot=False)
        assert cal_result["pixel_per_ev"] == 16.0
        assert np.isclose(cal_result["peak_shift"], 3.75, rtol=1e-2)

    def test_calibrate_provided_parameters(self, sees_group):
        """Test calibration with provided parameters."""

        # Provide calibration parameters to avoid issues with synthetic data
        cal_params = {"pixel_per_ev": 16.0, "peak_shift": 2.0}
        cal_result = sees_group.calibrate(cal_params, plot=False)

        assert cal_result["pixel_per_ev"] == 16.0
        assert cal_result["peak_shift"] == 2.0
