import pytest
import numpy as np
from pyleem.analysis.sees import SEES_onset, SEESAnalyzer, SEESGroup, SEESConfig, calibrate_sees
from pyleem.analyzer import ProfileAnalyzer


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
def sees_analyzer(sees_raw_file, roi, pixel_per_ev, peak_shift):
    """Create a SEESAnalyzer instance."""
    return SEESAnalyzer(sees_raw_file, roi, pixel_per_ev, peak_shift, sigma=10)


class TestSEESAnalyzer:
    """Test SEESAnalyzer class."""

    @pytest.fixture
    def sees_analyzer(self, sees_raw_file, roi, pixel_per_ev, peak_shift):
        """Create a SEESAnalyzer instance."""
        return SEESAnalyzer(sees_raw_file, roi, pixel_per_ev, peak_shift, sigma=0)

    def test_processing(self, sees_analyzer):
        """Test processing method."""

        assert sees_analyzer.pk_idx == 57  # filtered profile changes pk_idx
        assert sees_analyzer.slope == 12.5
        assert np.isclose(sees_analyzer.onset_pos, 40.0, rtol=1e-2)
        assert np.isclose(sees_analyzer.potential, -2.5, rtol=1e-2)

    def test_transform_abscissa(self, sees_analyzer):
        """Test transform_abscissa method."""

        # given the 16 pixel per ev
        # the abscissa should be 0 to 8 eV after conversion
        sees_analyzer.abscissa == np.linspace(0, 8, 128, endpoint=False)
        sees_analyzer.abscissa_label == "Energy [eV]"

    def test_sees_onset(self, sees_analyzer):
        """Test SEES_onset with ramp profile.

        The profile is a sigmoid function.
        """
        profile = sees_analyzer.profile
        pk_idx, slope, onset_pos = SEES_onset(profile)
        assert pk_idx == 57
        assert slope == 12.5
        assert np.isclose(onset_pos, 40.0, rtol=1e-2)


class TestCalibrateSEES:
    """Test calibrate_sees function."""

    def test_calibrate_sees(self, sees_multiple_raw_files, roi):
        """Test calibrate_sees function."""
        analyzers = [
            ProfileAnalyzer(sees_raw_file, roi)
            for sees_raw_file in sees_multiple_raw_files
        ]
        cal_result = calibrate_sees(analyzers, {"sigma": 0})
        assert cal_result["pixel_per_ev"] == 16.0
        assert np.isclose(cal_result["peak_shift"], 3.75, rtol=0.1)

    def test_calibrate_sees_with_pixel_per_ev(self, sees_multiple_raw_files, roi):
        """Test calibrate_sees function with pixel_per_ev."""
        analyzers = [
            ProfileAnalyzer(sees_raw_file, roi)
            for sees_raw_file in sees_multiple_raw_files
        ]
        cal_result = calibrate_sees(analyzers, {"pixel_per_ev": 8})
        assert cal_result["pixel_per_ev"] == 8
        assert np.isclose(cal_result["peak_shift"], 6, rtol=0.1)

    def test_calibrate_sees_with_peak_shift(self, sees_multiple_raw_files, roi):
        """Test calibrate_sees function with peak_shift."""
        analyzers = [
            ProfileAnalyzer(sees_raw_file, roi)
            for sees_raw_file in sees_multiple_raw_files
        ]
        cal_result = calibrate_sees(analyzers, {"pixel_per_ev": 8, "peak_shift": 8})
        assert cal_result["pixel_per_ev"] == 8
        assert cal_result["peak_shift"] == 8


class TestSEESGroup:
    """Test SEESGroup class."""

    @pytest.fixture
    def sees_group_empty_raises(self, roi, pixel_per_ev, peak_shift):
        """Create a SEESGroup instance."""
        with pytest.raises(AssertionError, match="Paths cannot be empty"):
            SEESGroup([], roi, pixel_per_ev, peak_shift, sigma=0)


class TestSEESConfig:
    """Test SEESConfig class."""

    @pytest.fixture
    def sees_config_file(self, tmp_path, roi_file, sees_multiple_raw_files):
        """Write a SEES TOML config file with ROI, calibration paths and result.

        The roi file parameter is not used but necessary for maintaining
        the same tmp_path.
        """

        path_list = ", ".join(f'"{f.name}"' for f in sees_multiple_raw_files)
        content = (
            f'[base]\nroi = "test.roi"\n'
            f"[calibration]\npaths = [{path_list}]\n"
            "[calibration.parameters]\nsigma = 0\n"
            "[calibration.result]\npixel_per_ev = 8.0\npeak_shift = 0.0\n"
        )
        config_path = tmp_path / "sees_config.toml"
        config_path.write_text(content)
        return config_path

    def test_calibrate(self, sees_config_file):
        """Test SEESConfig.calibrate with reset=True runs SEES calibration."""

        result = SEESConfig(sees_config_file).calibrate()
        assert np.isclose(result["pixel_per_ev"], 16.0, rtol=0.1)
        assert np.isclose(result["peak_shift"], 3.75, rtol=0.1)

        persisted = SEESConfig(sees_config_file).read_section("calibration.result")
        assert persisted["pixel_per_ev"] == 8.0
        assert persisted["peak_shift"] == 0.0

    def test_calibrate_update(self, sees_config_file):
        """Test SEESConfig.calibrate with update=True persists the result."""

        config = SEESConfig(sees_config_file)
        result = config.calibrate(update=True)
        assert np.isclose(result["pixel_per_ev"], 16.0, rtol=0.1)
        assert np.isclose(result["peak_shift"], 3.75, rtol=0.1)

        persisted = config.read_section("calibration.result")
        assert np.isclose(persisted["pixel_per_ev"], 16.0, rtol=0.1)
        assert np.isclose(persisted["peak_shift"], 3.75, rtol=0.1)
