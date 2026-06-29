import matplotlib.pyplot as plt
import numpy as np
import pytest
import scipy.stats

from pyleem.analysis.xps import (
    XPSAnalyzer,
    XPSCalibration,
    fit_xps,
    parameter_constraint,
    parameter_estimation,
    pseudo_voigt_fits,
    shirley_background,
)


def test_shirley_background(xps_array):
    """Test Shirley background calculation."""
    extracted_bg = shirley_background(xps_array[0, :], 100.0)
    x = np.arange(128)
    background = 100 / (1 + np.exp(0.06 * (x - 60)))

    assert np.allclose(extracted_bg, background, rtol=0.5, atol=2)


def test_shirley_convergence():
    """Test Shirley background convergence."""
    mean, sigma = 0, 1
    x = np.linspace(mean - 3 * sigma, mean + 3 * sigma, 101)
    tan_bg = -np.atan(x) - (-np.atan(x)).min()
    sig = scipy.stats.norm.pdf(x, mean, sigma) * 20

    total_sig = tan_bg + sig
    base_diff = tan_bg[0] - tan_bg[-1]
    s_bg1 = shirley_background(total_sig, base_diff)
    total_sig_2 = s_bg1 + sig
    s_bg2 = shirley_background(total_sig_2, base_diff)
    total_sig_3 = s_bg2 + sig
    s_bg3 = shirley_background(total_sig_3, base_diff)

    assert np.allclose(s_bg3, s_bg2, rtol=0.005)


def test_shirley_background_edge_cases():
    """Test edge cases for Shirley background."""
    flat_signal = np.ones(100) * 10
    bg = shirley_background(flat_signal, 0.0, iterations=0)
    assert np.all(bg == 0)

    signal = np.random.rand(50) * 10 + 5
    bg = shirley_background(signal, 1.0, iterations=5, tol=1e-3)
    assert len(bg) == len(signal)


def test_pseudo_voigt_fits():
    """Test pseudo-Voigt model creation."""
    peaks = ["peak1", "peak2"]
    constraints = {
        "peak1_center": {"value": 1.0, "min": 0.5, "max": 1.5, "vary": False},
        "peak2_center": {"value": 2.0, "min": 1.5, "max": 2.5},
    }
    model, params = pseudo_voigt_fits(peaks, constraints)

    assert model is not None and params is not None

    for peak in peaks:
        for suffix in ["amplitude", "sigma", "fraction"]:
            assert f"{peak}_{suffix}" in params
            assert params[f"{peak}_{suffix}"].min == 0

    for key, value in constraints.items():
        assert params[key].value == value["value"]
        assert params[key].min == value["min"]
        assert params[key].max == value["max"]
        assert params[key].vary == value.get("vary", True)


def test_pseudo_voigt_fits_variants():
    """Test pseudo-Voigt with single peak and no constraints."""
    peaks = ["peak1"]
    constraints = {"peak1_center": {"value": 5.0, "min": 4.0, "max": 6.0}}
    model, params = pseudo_voigt_fits(peaks, constraints)
    assert params["peak1_center"].value == 5.0

    peaks = ["p1", "p2", "p3"]
    model, params = pseudo_voigt_fits(peaks)
    for peak in peaks:
        for suffix in ["center", "amplitude", "sigma", "fraction"]:
            assert f"{peak}_{suffix}" in params
            assert params[f"{peak}_{suffix}"].min == 0


def test_parameter_estimation():
    """Test parameter estimation for peak fitting."""
    x = np.linspace(0, 100, 1000)
    peak1 = 50 * np.exp(-((x - 30) ** 2) / (2 * 5**2))
    peak2 = 30 * np.exp(-((x - 70) ** 2) / (2 * 3**2))
    profile = peak1 + peak2 + 5

    centers, _, _ = parameter_estimation(profile, 2, peak_prominence=0.1)

    assert len(centers) == 2
    assert 250 < centers[0] < 350 and 650 < centers[1] < 750


def test_parameter_estimation_edge_cases():
    """Test parameter estimation with single peak and high prominence."""
    x = np.linspace(0, 100, 500)
    peak = 100 * np.exp(-((x - 50) ** 2) / (2 * 10**2))
    profile = peak + 2

    centers, _, _ = parameter_estimation(profile, 2, peak_prominence=0.05)
    assert len(centers) == 2
    assert centers[0] < centers[1]


def test_parameter_constraint():
    """Test parameter constraint generation."""
    x = np.linspace(0, 100, 2000)
    peaks_data = [
        50 * np.exp(-((x - pos) ** 2) / (2 * 3**2)) for pos in [20, 40, 60, 80]
    ]
    profile = sum(peaks_data) + 3

    constraints = parameter_constraint(profile, 4, peak_prominence=0.05)

    for i in range(1, 5):
        assert f"p{i}_center" in constraints
        assert f"p{i}_amplitude" in constraints
        assert f"p{i}_sigma" in constraints
        assert "value" in constraints[f"p{i}_center"]


def test_fit_xps():
    """Test XPS fitting with Shirley background."""
    x = np.linspace(0, 100, 500)
    peak1 = 50 * np.exp(-((x - 40) ** 2) / (2 * 5**2))
    profile = peak1 + np.linspace(10, 5, 500)

    constraints = parameter_constraint(profile, 1, peak_prominence=0.1)
    peak_labels = ["p1"]
    baseline = (10, 5)
    result, bg = fit_xps(profile, x, baseline, peak_labels, constraints)

    assert result is not None
    assert isinstance(bg, np.ndarray) and len(bg) == len(profile)


class TestXPSAnalyzer:
    """Test XPSAnalyzer."""

    @pytest.fixture
    def xps_analyzer(self, xps_reader, roi, pixel_per_ev, peak_shift):
        """Create an XPSAnalyzer instance."""

        return XPSAnalyzer([xps_reader], roi, pixel_per_ev, peak_shift)

    def test_transform_abscissa(self, xps_analyzer):
        """Test transform_abscissa."""
        assert np.array_equal(
            xps_analyzer.get_binding_energy(0),
            200 - np.linspace(0, 8, 128, endpoint=False),
        )

    def test_postprocess(self, xps_analyzer):
        """Test postprocess."""
        kinetic_energy = 200 + np.linspace(0, 8, 128, endpoint=False)
        binding_energy = 400 - kinetic_energy

        assert np.array_equal(xps_analyzer.get_kinetic_energy(0), kinetic_energy)
        assert np.array_equal(xps_analyzer.get_binding_energy(0), binding_energy)

    def test_fit_method(self, xps_analyzer):
        """Test XPS fitting method."""
        result, bg = xps_analyzer.fit(0, 1, (200, 100))

        assert result is not None
        assert hasattr(result, "best_fit")
        assert isinstance(bg, np.ndarray)

    def test_plot_fit(self, xps_analyzer):
        """Test plotting XPS fit."""
        fig, ax = plt.subplots()
        returned_ax = xps_analyzer.plot_profile(
            0,
            ax=ax,
            show_fit=True,
            num_peaks=1,
            baseline=(200, 100),
        )

        assert returned_ax is ax
        assert len(ax.get_lines()) > 0
        assert len(ax.child_axes) == 1
        assert len(ax.child_axes[0].get_lines()) > 0
        plt.close(fig)


class TestXPSCalibration:
    """Test XPSCalibration."""

    @pytest.fixture
    def xps_calibrator(self, xps_readers, roi):
        """Create an XPSCalibration instance."""
        return XPSCalibration(xps_readers, roi)

    def test_calibrate_xps(self, xps_calibrator):
        """Test XPSCalibration analyze method."""

        result = xps_calibrator.analyze(
            baselines=[(197, 100)] * 3,
            num_peaks=1,
            ref_index=0,
            ref_value=285.0,
        )

        assert result["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert result["peak_shift"] == pytest.approx(-4, rel=0.1)

    def test_calibrate_ppev_without_reference(self, xps_calibrator):
        """Test calibration with pixel_per_ev."""
        result = xps_calibrator.analyze(
            baselines=[(197, 100)] * 3,
            num_peaks=1,
            pixel_per_ev=8,
        )
        assert result["pixel_per_ev"] == pytest.approx(8, rel=0.1)
        assert np.allclose(result["peak_shift"], 0, rtol=0.1)

    def test_calibrate_ppev_with_reference(self, xps_calibrator):
        """Test calibration with pixel_per_ev and reference peak."""
        result = xps_calibrator.analyze(
            baselines=[(197, 100)] * 3,
            num_peaks=1,
            pixel_per_ev=16,
            ref_index=0,
            ref_value=285.0,
        )
        assert np.allclose(result["peak_shift"], -4, rtol=0.1)
        assert result["pixel_per_ev"] == 16

    def test_calibrate_with_peak_shift(self, xps_calibrator):
        """Test calibration with explicit peak_shift."""
        result = xps_calibrator.analyze(
            baselines=[(197, 100)] * 3,
            num_peaks=1,
            pixel_per_ev=8,
            peak_shift=8,
        )

        assert result["pixel_per_ev"] == 8
        assert result["peak_shift"] == 8
