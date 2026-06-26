import numpy as np
import pytest
import matplotlib.pyplot as plt

from pyleem.analysis.sees import SEESAnalyzer, SEESCalibration, SEES_onset


def test_sees_onset(sees_array):
    """Test SEES_onset with ramp profile."""
    profile = sees_array[0, :]
    pk_idx, slope, onset_pos = SEES_onset(profile)

    assert pk_idx == 57
    assert slope == 12.5
    assert onset_pos == pytest.approx(40.0, rel=1e-2)


class TestSEESCalibration:
    """Test SEESCalibration class."""

    def test_calibrate_sees(self, sees_readers, roi):
        """Test calibration with reader metadata."""
        calibration = SEESCalibration(sees_readers, roi)
        cal_result = calibration.analyze(sigma=0)

        assert cal_result["pixel_per_ev"] == 16.0
        assert cal_result["peak_shift"] == pytest.approx(3.75, rel=0.1)

    def test_calibrate_sees_metadata_equivalent(self, sees_readers, roi):
        """Test equivalent metadata gives identical result."""
        for reader, start_voltage in zip(sees_readers, [0.0, 1.0, 2.0]):
            reader.metadata["Start Voltage"] = (start_voltage, "V")

        calibration = SEESCalibration(sees_readers, roi)
        cal_result = calibration.analyze(sigma=0)

        assert cal_result["pixel_per_ev"] == 16.0
        assert cal_result["peak_shift"] == pytest.approx(3.75, rel=0.1)

    def test_calibrate_sees_metadata_overrides(self, sees_readers, roi):
        """Test different metadata changes pixel_per_ev."""
        for reader, start_voltage in zip(sees_readers, [0.0, 2.0, 4.0]):
            reader.metadata["Start Voltage"] = (start_voltage, "V")

        calibration = SEESCalibration(sees_readers, roi)
        cal_result = calibration.analyze(sigma=0)

        assert cal_result["pixel_per_ev"] == pytest.approx(8.0, rel=0.1)

    def test_calibrate_sees_with_pixel_per_ev(self, sees_readers, roi):
        """Test calibration with pixel_per_ev."""
        calibration = SEESCalibration(sees_readers, roi)
        cal_result = calibration.analyze(pixel_per_ev=8)

        assert cal_result["pixel_per_ev"] == 8
        assert cal_result["peak_shift"] == pytest.approx(6, rel=0.1)

    def test_calibrate_sees_with_peak_shift(self, sees_readers, roi):
        """Test calibration with peak_shift."""
        calibration = SEESCalibration(sees_readers, roi)
        cal_result = calibration.analyze(pixel_per_ev=8, peak_shift=8)

        assert cal_result["pixel_per_ev"] == 8
        assert cal_result["peak_shift"] == 8


class TestSEESAnalyzer:
    """Test SEESAnalyzer class."""

    @pytest.fixture
    def sees_analyzer(self, sees_reader, roi, pixel_per_ev, peak_shift):
        """Test create a SEESAnalyzer instance."""
        return SEESAnalyzer([sees_reader], roi, pixel_per_ev, peak_shift, sigma=0)

    def test_processing(self, sees_analyzer):
        """Test processing method."""
        result = sees_analyzer.analyze_profile(0)

        assert result["pk_idx"] == 57
        assert result["slope"] == 12.5
        assert result["onset_pos"] == pytest.approx(40.0, rel=1e-2)
        assert result["surface_potential"] == pytest.approx(-2.5, rel=1e-2)

    def test_transform_abscissa(self, sees_analyzer, pixel_per_ev):
        """Test transform_abscissa method."""
        result = sees_analyzer.analyze_profile(0)
        pixel = np.arange(128)

        assert result["kinetic_energy"] == pytest.approx(
            (pixel - result["onset_pos"]) / pixel_per_ev
        )

    def test_sees_onset(self, sees_analyzer):
        """Test SEES_onset with ramp profile."""
        profile = sees_analyzer.get_profile(0)
        pk_idx, slope, onset_pos = SEES_onset(profile)

        assert pk_idx == 57
        assert slope == 12.5
        assert onset_pos == pytest.approx(40.0, rel=1e-2)

    def test_plot_profile(self, sees_analyzer):
        """Test plot_profile returns the axes."""
        fig, ax = plt.subplots()

        returned_ax = sees_analyzer.plot_profile(0, ax=ax, show_fit=True)

        assert returned_ax is ax
        assert len(ax.lines) == 2
        plt.close(fig)
