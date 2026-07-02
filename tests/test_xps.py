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
    peak_constraints = {
        "peak1": {"center": {"value": 1.0, "min": 0.5, "max": 1.5, "vary": False}},
        "peak2": {"center": {"value": 2.0, "min": 1.5, "max": 2.5}},
    }
    model, params = pseudo_voigt_fits(peak_constraints)

    assert model is not None and params is not None

    for peak in peak_constraints:
        for suffix in ["amplitude", "sigma", "fraction"]:
            assert f"{peak}_{suffix}" in params
            assert params[f"{peak}_{suffix}"].min == 0

    assert params["peak1_center"].value == 1.0
    assert params["peak1_center"].min == 0.5
    assert params["peak1_center"].max == 1.5
    assert params["peak1_center"].vary is False
    assert params["peak2_center"].value == 2.0
    assert params["peak2_center"].min == 1.5
    assert params["peak2_center"].max == 2.5


def test_pseudo_voigt_fits_variants():
    """Test pseudo-Voigt with single and minimal constraints."""
    constraints = {"peak1": {"center": {"value": 5.0, "min": 4.0, "max": 6.0}}}
    model, params = pseudo_voigt_fits(constraints)
    assert params["peak1_center"].value == 5.0

    constraints = {"p1": {}, "p2": {}, "p3": {}}
    model, params = pseudo_voigt_fits(constraints)
    for peak in constraints:
        for suffix in ["center", "amplitude", "sigma", "fraction"]:
            assert f"{peak}_{suffix}" in params
            assert params[f"{peak}_{suffix}"].min == 0

    with pytest.raises(
        ValueError, match="peak_constraints must contain at least one peak"
    ):
        pseudo_voigt_fits({})


def test_parameter_estimation():
    """Test parameter estimation for peak fitting."""
    x = np.linspace(0, 100, 1000)
    peak1 = 50 * np.exp(-((x - 30) ** 2) / (2 * 5**2))
    peak2 = 30 * np.exp(-((x - 70) ** 2) / (2 * 3**2))
    profile = peak1 + peak2 + 5

    centers, sigmas, peak_areas = parameter_estimation(
        profile, x, 2, peak_prominence=0.1
    )

    assert len(centers) == 2
    assert centers[0] == pytest.approx(30, abs=0.2)
    assert centers[1] == pytest.approx(70, abs=0.2)
    assert np.all(sigmas > 0)
    assert np.all(peak_areas > 0)


def test_parameter_estimation_raise():
    """Test parameter estimation raises an error if expected peaks are not found."""
    x = np.linspace(0, 100, 500)
    profile = np.zeros(500)
    with pytest.raises(ValueError, match="found 0 peaks, but expected 1"):
        parameter_estimation(profile, x, 1, peak_prominence=0.1)


def test_parameter_estimation_narrow_peak():
    """Test parameter estimation omits narrow peaks."""
    x = np.linspace(0, 100, 500)
    profile = 100 * np.exp(-((x - 50) ** 2) / (2 * 10**2))
    profile[10] = 200

    centers, sigma, peak_area = parameter_estimation(profile, x, 1, peak_prominence=0.1)
    assert len(centers) == 1
    assert centers[0] == pytest.approx(50, abs=0.2)
    assert sigma[0] == pytest.approx(11.7, abs=0.2)
    assert peak_area[0] == pytest.approx(2506.6, abs=50)


def test_parameter_estimation_abscissa_conversion():
    """Test parameter estimation returns the peaks it detects.

    Here we test that the abscissa returns the correct peak
    parameters.
    """
    x = np.linspace(0, 100, 500)
    profile = 100 * np.exp(-((x - 50) ** 2) / (2 * 10**2))

    centers, sigma, peak_area = parameter_estimation(profile, x, 1, peak_prominence=0.1)
    assert len(centers) == 1
    assert centers[0] == pytest.approx(50, abs=0.2)
    # PseudoVogit sigma is 11.7
    assert sigma[0] == pytest.approx(11.7, abs=0.2)
    assert peak_area[0] == pytest.approx(2506.6, abs=50)

    # test abscissa conversion
    abscissa = np.linspace(100, 400, 500)

    centers, sigmas, peak_areas = parameter_estimation(
        profile, abscissa, 1, peak_prominence=0.1
    )

    assert centers[0] == pytest.approx(250, abs=0.6)
    assert sigmas[0] == pytest.approx(35.1, abs=0.6)
    assert peak_areas[0] == pytest.approx(7519.8, abs=100)


def test_parameter_constraint():
    """Test parameter constraint generation."""
    x = np.linspace(0, 100, 2000)
    peaks_data = [
        50 * np.exp(-((x - pos) ** 2) / (2 * 3**2)) for pos in [20, 40, 60, 80]
    ]
    profile = sum(peaks_data)

    constraints = parameter_constraint(profile, x, 4, peak_prominence=0.05)

    for i in range(1, 5):
        peak = constraints[f"p{i}"]
        assert "center" in peak
        assert "amplitude" in peak
        assert "sigma" in peak
        assert "value" in peak["center"]
        assert peak["center"]["value"] == pytest.approx(i * 20, abs=0.2)


def test_fit_xps():
    """Test XPS fitting with Shirley background."""
    x = np.linspace(0, 100, 500)
    peak1 = 50 * np.exp(-((x - 40) ** 2) / (2 * 5**2))
    profile = peak1 + np.linspace(10, 5, 500)

    baseline = (10, 5)
    fit_result = fit_xps(profile, x, baseline=baseline, num_peaks=1)

    assert fit_result["result"] is not None
    assert fit_result["peak_labels"] == ["p1"]
    assert isinstance(fit_result["background"], np.ndarray)
    assert len(fit_result["background"]) == len(profile)


def test_fit_xps_with_peak_constraints():
    """Test XPS fitting with manual nested peak constraints."""
    x = np.linspace(0, 100, 500)
    peak1 = 50 * np.exp(-((x - 40) ** 2) / (2 * 5**2))
    profile = peak1 + np.linspace(10, 5, 500)
    peak_constraints = {
        "peak1": {
            "center": {"value": 40, "min": 35, "max": 45},
            "sigma": {"value": 5, "min": 1, "max": 10},
            "amplitude": {"value": 500, "min": 0},
        }
    }

    fit_result = fit_xps(
        profile,
        x,
        baseline=(10, 5),
        peak_constraints=peak_constraints,
        fit_range=(20, 60),
    )

    assert fit_result["peak_labels"] == ["peak1"]
    assert fit_result["range_abscissa"].min() >= 20
    assert fit_result["range_abscissa"].max() <= 60
    assert fit_result["result"].best_values["peak1_center"] == pytest.approx(40, abs=1)


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
        fit_result = xps_analyzer.fit(0, num_peaks=1, baseline=(200, 100))

        assert fit_result["result"] is not None
        assert hasattr(fit_result["result"], "best_fit")
        assert isinstance(fit_result["background"], np.ndarray)

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
