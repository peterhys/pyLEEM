import numpy as np
import cv2
from pyleem.analyzer import Analyzer
from pyleem.analysis.desp import (
    preprocess_image,
    get_radius,
    calibrate_desp,
    parabola_fit,
    disk_template,
    match_score,
    eval_radii,
    get_radius_match_template,
    DESPAnalyzer,
    DESPConfig,
    DESPGroup,
)
import pytest


def test_preprocess_basic():
    """Test basic preprocessing with normalization."""
    image = np.random.rand(100, 100) * 1000
    result = preprocess_image(image)

    assert result.dtype == np.uint8
    assert result.shape == image.shape
    assert 0 <= result.min() <= result.max() <= 255


def test_get_radius_circle():
    """Test circle detection from clean circle."""
    image = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(image, (100, 100), 50, 255, -1)

    processed_image = preprocess_image(image)
    x, y, radius = get_radius(processed_image)
    assert 90 < x < 110 and 90 < y < 110 and 45 < radius < 55


def test_get_radius_with_noise():
    """Test circle detection with noisy image."""
    image = np.random.randint(0, 50, (200, 200), dtype=np.uint8)
    cv2.circle(image, (100, 100), 60, 200, -1)

    processed_image = preprocess_image(image)
    x, y, radius = get_radius(processed_image)
    assert 80 < x < 120 and 80 < y < 120 and 40 < radius < 80


def test_parabola_fit():
    """Test parabola fit function."""
    voltages = [14, 21, 30]
    radii = [30, 40, 50]
    fit_function, fit_result = parabola_fit(voltages, radii)
    assert np.isclose(fit_result.best_values["a"], 0.01, rtol=0.1)
    assert np.isclose(fit_result.best_values["c"], 5, rtol=0.1)

    assert fit_function(35) == 17.25


def test_parabola_fit_window():
    """Test parabola fit function with window.
    Here we remove the outliners from the fit.
    """
    voltages = [14, 21, 30, 200]
    radii = [30, 40, 50, 40]
    window = np.array(voltages) < 40
    fit_function, fit_result = parabola_fit(voltages, radii, window=window)
    assert np.isclose(fit_result.best_values["a"], 0.01, rtol=0.1)
    assert np.isclose(fit_result.best_values["c"], 5, rtol=0.1)
    assert fit_function(35) == 17.25


def test_disk_template():
    """Test disk template function."""
    tmpl = disk_template(10)
    assert tmpl.shape == (21, 21)
    assert tmpl.dtype == np.float32
    assert np.isclose(tmpl.mean(), 0.0, atol=1e-6)


def test_match_score():
    """Test match score function."""
    image = np.zeros((100, 100), dtype=np.float32)
    cv2.circle(image, (50, 50), 20, 1000, -1)
    score, x, y, r = match_score(image, 20)
    assert score == 1.0  # match perfectly
    assert x == 50
    assert y == 50
    assert r == 20


def test_center_and_radius():
    """Detected x, y, r are close to the true values."""

    for x, y, r in [(80, 80, 20), (60, 60, 30), (40, 40, 40)]:
        img = np.zeros((180, 180), dtype=np.uint16)
        cv2.circle(img, (x, y), r, 1000, -1)
        x_, y_, r_ = get_radius_match_template(img, r_min=20, r_max=40, step_size=2)

        assert x_ == x
        assert y_ == y
        assert r_ == r


class TestEvalRadii:
    """Test eval_radii function."""

    @pytest.fixture
    def disk_image(self):
        """Float32 image containing a disk of radius 20 at (60, 60)."""
        image = np.zeros((130, 130), dtype=np.float32)
        cv2.circle(image, (60, 60), 20, 1000, -1)
        return image

    def test_best_radius_threaded(self, disk_image):
        """Multi-threaded search finds the correct radius."""
        radii = [10, 15, 20, 25, 30]
        _, _, _, best_r = eval_radii(disk_image, radii, use_threads=True)
        assert best_r == 20

    def test_best_radius_sequential(self, disk_image):
        """Sequential search finds the correct radius."""
        radii = [10, 15, 20, 25, 30]
        _, _, _, best_r = eval_radii(disk_image, radii, use_threads=False)
        assert best_r == 20

    def test_single_radius(self, disk_image):
        """Single-element radii list still returns a valid result."""
        result = eval_radii(disk_image, [20], use_threads=False)
        assert result == (1.0, 60, 60, 20)
        result = eval_radii(disk_image, [20], use_threads=True)
        assert result == (1.0, 60, 60, 20)


class TestCalibrateDESP:
    """Test calibrate_desp function."""

    def test_calibrate_desp(self, desp_files):
        """Test calibrate_desp function."""
        analyzers = [Analyzer(desp_raw_file) for desp_raw_file in desp_files]
        cal_result = calibrate_desp(analyzers)

        assert np.isclose(cal_result["potential_func"](30), 14, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](35), 17.25, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](40), 21, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](45), 25.25, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](50), 30, rtol=0.1)

    def test_calibrate_desp_metadata_equivalent(self, desp_files):
        """Supplying the same voltages as analyzer metadata gives identical result."""
        analyzers = [Analyzer(f) for f in desp_files]
        metadata = {"Start Voltage": [9.0, 21.0, 41.0]}
        cal_result = calibrate_desp(analyzers, metadata=metadata)
        assert np.isclose(cal_result["potential_func"](30), 14, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](40), 21, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](50), 30, rtol=0.1)

    def test_calibrate_desp_metadata_overrides(self, desp_files):
        """Supplying different voltages overrides the analyzer metadata.

        Radii 20, 40, 60 mapped to 10, 34, 74 instead of 14, 21, 30.
        Represents 0.02 x^2 + 2 potential function.
        """
        analyzers = [Analyzer(f) for f in desp_files]

        metadata = {"Start Voltage": [10, 34, 74]}
        cal_result = calibrate_desp(analyzers, metadata=metadata)
        assert np.isclose(cal_result["potential_func"](30), 20, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](50), 52, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](70), 100, rtol=0.1)


class TestDESPAnalyzer:
    """Test DESPAnalyzer class."""

    @pytest.fixture
    def desp_analyzer(self, desp_raw_file, desp_potential_func):
        """Create an DESPAnalyzer instance."""
        return DESPAnalyzer(desp_raw_file, desp_potential_func)

    def test_init(self, desp_analyzer):
        """Test analyzer initialization."""
        assert desp_analyzer.x == 64
        assert desp_analyzer.y == 128
        assert np.isclose(desp_analyzer.radius, 40, rtol=0.1)

    def test_processed_image_property(self, desp_analyzer):
        """Test processed_image property."""
        assert isinstance(desp_analyzer.processed_image, np.ndarray)
        assert desp_analyzer.processed_image.shape == (256, 128)
        assert desp_analyzer.processed_image.dtype == np.uint8
        assert desp_analyzer.processed_image.min() == 0
        assert desp_analyzer.processed_image.max() == 255

    def test_potential_func(self, desp_analyzer):
        """Test potential_func property."""
        assert desp_analyzer.potential_func(30) == 14
        assert desp_analyzer.potential_func(35) == 17.25
        assert desp_analyzer.potential_func(40) == 21
        assert desp_analyzer.potential_func(45) == 25.25
        assert desp_analyzer.potential_func(50) == 30

    def test_potential_non_func_raises(self, desp_files):
        """Test group initialization with non-function potential_func."""
        with pytest.raises(AssertionError, match="potential_func must be a callable"):
            DESPGroup(desp_files, potential_func=1)


class TestDESPGroup:
    """Test DESPGroup class."""

    def test_empty_paths_raises(self):
        """Test group initialization with empty paths."""
        with pytest.raises(AssertionError, match="Paths cannot be empty"):
            DESPGroup([], potential_func=lambda x: x)


def test_calibrate_reset(tmp_path, desp_files):
    """Test that the calibrated potential_func interpolates correctly.

    The desp_files parameter is not used but necessary for maintaining
    the same tmp_path. When the path is searched, the files can be found.
    """

    content = f'[calibration]\npath_pattern = "*.dat"\n'
    config_path = tmp_path / "config.toml"
    config_path.write_text(content)

    result = DESPConfig(config_path).calibrate()
    func = result["potential_func"]
    assert callable(func)
    assert np.isclose(func(20), 9, rtol=0.1)
    assert np.isclose(func(40), 21, rtol=0.1)
    assert np.isclose(func(60), 41, rtol=0.1)


def test_calibrate_with_metadata_section(tmp_path, desp_files):
    """[calibration.metadata] overrides start voltages read from analyzer files."""
    content = (
        '[calibration]\npath_pattern = "*.dat"\n'
        "[calibration.metadata]\n"
        '"Start Voltage" = [10, 34, 74]\n'
    )
    config_path = tmp_path / "config.toml"
    config_path.write_text(content)

    result = DESPConfig(config_path).calibrate()
    func = result["potential_func"]
    assert callable(func)
    # radii 20, 40, 60 now map to 10, 34, 74
    assert np.isclose(func(20), 10, rtol=0.1)
    assert np.isclose(func(40), 34, rtol=0.1)
    assert np.isclose(func(60), 74, rtol=0.1)
