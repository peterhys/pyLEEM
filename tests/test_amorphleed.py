import numpy as np
import cv2
from pyleem.amorphleed import (
    preprocess_image,
    get_radius,
    AmorphLEEDAnalyzer,
    AmorphLEEDGroup,
)
import pytest
import matplotlib.pyplot as plt


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


class TestAmorphLEEDAnalyzer:
    """Test AmorphLEEDAnalyzer class."""

    @pytest.fixture
    def leed_analyzer(self, leed_raw_file):
        """Create an AmorphLEEDAnalyzer instance."""
        return AmorphLEEDAnalyzer(leed_raw_file)

    def test_init(self, leed_analyzer):
        """Test analyzer initialization."""
        assert leed_analyzer.x == 64
        assert leed_analyzer.y == 128
        assert np.allclose(leed_analyzer.radius, 40)

    def test_processed_image_property(self, leed_analyzer):
        """Test processed_image property."""
        assert isinstance(leed_analyzer.processed_image, np.ndarray)
        assert leed_analyzer.processed_image.shape == (256, 128)
        assert leed_analyzer.processed_image.dtype == np.uint8
        assert leed_analyzer.processed_image.min() == 0
        assert leed_analyzer.processed_image.max() == 255


class TestAmorphLEEDGroup:
    """Test AmorphLEEDGroup class."""

    @pytest.fixture
    def leed_group(self, leed_files):
        """Create an AmorphLEEDGroup instance."""
        return AmorphLEEDGroup(leed_files)

    def test_init(self, leed_group):
        """Test group initialization."""
        assert np.allclose(leed_group.get_attrs("radius"), [30, 40, 50])

    def test_calibrate_method(self, leed_group):
        """Test calibration returns interpolation function."""

        interp_func = leed_group.calibrate()
        assert np.allclose(interp_func(30), 200)
        assert np.allclose(interp_func(35), 200.5)
        assert np.allclose(interp_func(40), 201)
        assert np.allclose(interp_func(45), 201.5)
        assert np.allclose(interp_func(50), 202)
        assert np.allclose(interp_func(55), 202.5)
