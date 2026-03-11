import numpy as np
import cv2
from pyleem.analysis import Analyzer
from pyleem.desp import (
    preprocess_image,
    get_radius,
    calibrate_desp,
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

    x, y, radius = get_radius(image)
    assert 90 < x < 110 and 90 < y < 110 and 45 < radius < 55


def test_get_radius_with_noise():
    """Test circle detection with noisy image."""
    image = np.random.randint(0, 50, (200, 200), dtype=np.uint8)
    cv2.circle(image, (100, 100), 60, 200, -1)

    x, y, radius = get_radius(image)
    assert 80 < x < 120 and 80 < y < 120 and 40 < radius < 80


class TestCalibrateDESP:
    """Test calibrate_desp function."""

    def test_calibrate_desp(self, desp_files):
        """Test calibrate_desp function."""
        analyzers = [Analyzer(desp_raw_file) for desp_raw_file in desp_files]
        cal_result = calibrate_desp(analyzers)
        assert np.isclose(cal_result["potential_func"](30), 205, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](35), 207.5, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](40), 210, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](45), 212.5, rtol=0.1)
        assert np.isclose(cal_result["potential_func"](50), 215, rtol=0.1)


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
        assert desp_analyzer.potential_func(30) == 205
        assert desp_analyzer.potential_func(35) == 207.5
        assert desp_analyzer.potential_func(40) == 210
        assert desp_analyzer.potential_func(45) == 212.5
        assert desp_analyzer.potential_func(50) == 215

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
    assert np.isclose(func(20), 200, rtol=0.1)
    assert np.isclose(func(60), 220, rtol=0.1)
