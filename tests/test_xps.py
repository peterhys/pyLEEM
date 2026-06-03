import pytest
import numpy as np
import scipy.stats
from pyleem.analysis.xps import (
    shirley_background,
    pseudo_voigt_fits,
    parameter_estimation,
    parameter_contraint,
    fit_xps,
    XPSAnalyzer,
    XPSConfig,
    XPSGroup,
    calibrate_xps,
)
import matplotlib.pyplot as plt
from lmfit.models import PseudoVoigtModel
from pyleem.analyzer import ProfileAnalyzer


def test_shirley_background(xps_array):
    """Test Shirley background calculation."""
    extracted_bg = shirley_background(xps_array[0, :], 100.0)
    x = np.arange(128)
    background = 100 / (1 + np.exp(0.06 * (x - 60)))

    # test roughly equal
    assert np.allclose(extracted_bg, background, rtol=0.5, atol=2)


def test_shirley_convergence():
    """Test Shirley background convergence."""
    mean, sigma = 0, 1
    x = np.linspace(mean - 3 * sigma, mean + 3 * sigma, 101)
    tan_bg = -np.atan(x) - (-np.atan(x)).min()
    sig = scipy.stats.norm.pdf(x, mean, sigma) * 20

    total_sig = tan_bg + sig
    # base_diff is the difference between left and right baseline values
    base_diff = tan_bg[0] - tan_bg[-1]
    s_bg1 = shirley_background(total_sig, base_diff)
    total_sig_2 = s_bg1 + sig
    s_bg2 = shirley_background(total_sig_2, base_diff)
    total_sig_3 = s_bg2 + sig
    s_bg3 = shirley_background(total_sig_3, base_diff)

    assert np.allclose(s_bg3, s_bg2, rtol=0.005)


def test_shirley_background_edge_cases():
    """Test edge cases for Shirley background."""
    # Flat signal
    flat_signal = np.ones(100) * 10
    bg = shirley_background(flat_signal, 0.0, iterations=0)
    assert np.all(bg == 0)

    # Random signal with base_diff
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

    # Verify constraints
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
    # Single peak
    peaks = ["peak1"]
    constraints = {"peak1_center": {"value": 5.0, "min": 4.0, "max": 6.0}}
    model, params = pseudo_voigt_fits(peaks, constraints)
    assert params["peak1_center"].value == 5.0

    # No constraints
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

    # Request 2 peaks but only 1 exists - should split
    centers, _, _ = parameter_estimation(profile, 2, peak_prominence=0.05)
    assert len(centers) == 2
    assert centers[0] < centers[1]


def test_parameter_contraint():
    """Test parameter constraint generation."""
    x = np.linspace(0, 100, 2000)
    peaks_data = [
        50 * np.exp(-((x - pos) ** 2) / (2 * 3**2)) for pos in [20, 40, 60, 80]
    ]
    profile = sum(peaks_data) + 3

    constraints = parameter_contraint(profile, 4, peak_prominence=0.05)

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

    constraints = parameter_contraint(profile, 1, peak_prominence=0.1)
    peak_labels = ["p1"]
    baseline = (10, 5)
    result, bg = fit_xps(profile, x, baseline, peak_labels, constraints)

    assert result is not None
    assert isinstance(bg, np.ndarray) and len(bg) == len(profile)


class TestXPSAnalyzer:
    """Test XPSAnalyzer."""

    @pytest.fixture
    def xps_analyzer(self, xps_raw_file, roi, pixel_per_ev, peak_shift):
        """Create an XPSAnalyzer instance."""
        return XPSAnalyzer(
            xps_raw_file, roi, pixel_per_ev, peak_shift, incident_voltage=400
        )

    def test_init(self, xps_analyzer):
        """Test XPSAnalyzer initialization."""

        assert xps_analyzer.metadata["Incident Voltage"] == (400, "eV")

    def test_transform_abscissa(self, xps_analyzer):
        """Test transform_abscissa."""
        assert np.array_equal(
            xps_analyzer.abscissa, 200 - np.linspace(0, 8, 128, endpoint=False)
        )
        assert xps_analyzer.abscissa_label == "Binding Energy [eV]"

    def test_postprocess(self, xps_analyzer):
        """Test postprocess."""

        assert np.array_equal(
            xps_analyzer.KE, 200 + np.linspace(0, 8, 128, endpoint=False)
        )
        assert np.array_equal(xps_analyzer.BE, 400 - xps_analyzer.KE)

    def test_fit_method(self, xps_analyzer):
        """Test XPS fitting method."""

        result, bg = xps_analyzer.fit(1, (200, 100))

        assert result is not None
        assert hasattr(result, "best_fit")
        assert isinstance(bg, np.ndarray)

    def test_plot_fit(self, xps_analyzer):
        """Test plotting XPS fit."""

        model = PseudoVoigtModel(prefix="p1_")
        params = model.make_params(center=64, amplitude=100, sigma=5, fraction=0.5)

        x = xps_analyzer.pixel
        bg = np.linspace(10, 5, len(x))
        result = model.fit(xps_analyzer.profile - bg, x=x, params=params)

        fig, (ax1, ax2) = plt.subplots(2, 1)
        xps_analyzer.plot_fit((ax1, ax2), result, bg)

        assert len(ax1.get_lines()) > 0 and len(ax2.get_lines()) > 0
        plt.close(fig)


class TestXPSCalibration:

    @pytest.fixture
    def xps_analyzers(self, xps_multiple_raw_files, roi):
        """Create an XPSAnalyzer instance."""
        return [
            ProfileAnalyzer(xps_raw_file, roi)
            for xps_raw_file in xps_multiple_raw_files
        ]

    def test_calibrate_xps(self, xps_analyzers):
        """Test calibrate_xps function."""

        cal_params = {
            "baselines": [(197, 100)] * 3,
            "num_peaks": 1,
            "ref_index": 0,
            "ref_value": 285.0,
            "incident_voltage": 400,
        }

        cal_result = calibrate_xps(xps_analyzers, cal_params)
        assert cal_result["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert cal_result["peak_shift"] == pytest.approx(-4, rel=0.1)

    def test_calibrate_xps_metadata_equivalent(self, xps_analyzers):
        """Supplying the same voltages as analyzer metadata gives identical result."""
        cal_params = {
            "baselines": [(197, 100)] * 3,
            "num_peaks": 1,
            "ref_index": 0,
            "ref_value": 285.0,
            "incident_voltage": 400,
        }
        metadata = {"Start Voltage": [114.0, 115.0, 116.0]}
        cal_result = calibrate_xps(xps_analyzers, cal_params, metadata=metadata)
        assert cal_result["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert cal_result["peak_shift"] == pytest.approx(-4, rel=0.1)

    def test_calibrate_xps_metadata_overrides(self, xps_analyzers):
        """Supplying different voltages overrides the analyzer metadata."""
        cal_params = {
            "baselines": [(197, 100)] * 3,
            "num_peaks": 1,
            "incident_voltage": 400,
        }
        # doubling the voltage step should halve pixel_per_ev
        metadata = {"Start Voltage": [114.0, 116.0, 118.0]}
        cal_result = calibrate_xps(xps_analyzers, cal_params, metadata=metadata)
        assert cal_result["pixel_per_ev"] == pytest.approx(8.0, rel=0.1)

    def test_calibrate_ppev_without_reference(self, xps_analyzers):
        """Test calibration with pixel_per_ev."""
        cal_params = {
            "baselines": [(197, 100)] * 3,
            "num_peaks": 1,
            "pixel_per_ev": 8,
            "incident_voltage": 400,
        }
        cal_result = calibrate_xps(xps_analyzers, cal_params)
        assert cal_result["pixel_per_ev"] == pytest.approx(8, rel=0.1)
        # no reference peak adjustment
        assert np.allclose(cal_result["peak_shift"], 0, rtol=0.1)

    def test_calibrate_ppev_with_reference(self, xps_analyzers):
        """Test calibration with pixel_per_ev and reference peak."""
        cal_params = {
            "baselines": [(197, 100)] * 3,
            "num_peaks": 1,
            "pixel_per_ev": 16,
            "ref_index": 0,
            "ref_value": 285.0,
            "incident_voltage": 400,
        }
        cal_result = calibrate_xps(xps_analyzers, cal_params)
        assert np.allclose(cal_result["peak_shift"], -4, rtol=0.1)
        assert cal_result["pixel_per_ev"] == 16


class TestXPSGroup:
    """Test XPSGroup."""

    @pytest.fixture
    def xps_group_empty_raises(self, roi, pixel_per_ev, peak_shift):
        """Create an XPSGroup instance."""
        with pytest.raises(AssertionError, match="Paths cannot be empty"):
            XPSGroup([], roi, pixel_per_ev, peak_shift, incident_voltage=400)


class TestXPSConfig:
    """Test XPSConfig class."""

    @pytest.fixture
    def xps_config_file(self, tmp_path, roi, xps_multiple_raw_files):
        """Write an XPS TOML config file with ROI, calibration paths and result.

        Here we force the default result to 8.0 pixel_per_ev and 0.0 peak_shift.
        The calculated result is 16.0 pixel_per_ev and -4.0 peak_shift.
        """
        roi_path = tmp_path / "test.roi"
        roi.to_roi_object().tofile(roi_path)

        path_list = ", ".join(f'"{f.name}"' for f in xps_multiple_raw_files)
        content = (
            f'[base]\nroi = "test.roi"\n'
            f"[calibration]\npaths = [{path_list}]\n"
            "[calibration.parameters]\n"
            "num_peaks = 1\n"
            "baselines = [[197, 100], [197, 100], [197, 100]]\n"
            "incident_voltage = 400\n"
            "ref_index = 0\n"
            "ref_value = 285.0\n"
            "[calibration.result]\npixel_per_ev = 8.0\npeak_shift = 0.0\n"
        )
        config_path = tmp_path / "xps_config.toml"
        config_path.write_text(content)
        return config_path

    def test_calibrate(self, xps_config_file):
        """Test XPSConfig.calibrate with reset=True runs XPS calibration."""

        result = XPSConfig(xps_config_file).calibrate()
        assert result["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert result["peak_shift"] == pytest.approx(-4.0, rel=0.1)

        persisted = XPSConfig(xps_config_file).read_section("calibration.result")
        assert persisted["pixel_per_ev"] == 8.0
        assert persisted["peak_shift"] == 0.0

    def test_calibrate_update(self, xps_config_file):
        """Test XPSConfig.calibrate with update=True persists the result."""

        config = XPSConfig(xps_config_file)
        result = config.calibrate(update=True)
        assert result["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert result["peak_shift"] == pytest.approx(-4.0, rel=0.1)

        persisted = config.read_section("calibration.result")
        assert persisted["pixel_per_ev"] == pytest.approx(16.0, rel=0.1)
        assert persisted["peak_shift"] == pytest.approx(-4.0, rel=0.1)

    def test_calibrate_with_metadata_section(
        self, tmp_path, roi, xps_multiple_raw_files
    ):
        """[calibration.metadata] overrides start voltages read from analyzer files."""
        roi_path = tmp_path / "test.roi"
        roi.to_roi_object().tofile(roi_path)

        path_list = ", ".join(f'"{f.name}"' for f in xps_multiple_raw_files)
        content = (
            '[base]\nroi = "test.roi"\n'
            f"[calibration]\npaths = [{path_list}]\n"
            "[calibration.parameters]\n"
            "num_peaks = 1\n"
            "baselines = [[197, 100], [197, 100], [197, 100]]\n"
            "incident_voltage = 400\n"
            # doubling the voltage step should halve pixel_per_ev
            '[calibration.metadata]\n"Start Voltage" = [114.0, 116.0, 118.0]\n'
        )
        config_path = tmp_path / "xps_config_meta.toml"
        config_path.write_text(content)

        result = XPSConfig(config_path).calibrate()
        assert result["pixel_per_ev"] == pytest.approx(8.0, rel=0.1)
