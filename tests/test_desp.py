import cv2
import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyleem.analysis.desp import (
    DESPAnalyzer,
    DESPCalibration,
    disk_kernel,
    eval_radii,
    get_radius,
    get_radius_convolve,
    match_score,
    parabola_fit,
    preprocess_image,
)


@pytest.fixture
def parabola_func():

    def model_func(x, a, c):
        return a * x**2 + c

    return model_func


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

    assert 90 < x < 110
    assert 90 < y < 110
    assert 45 < radius < 55


def test_get_radius_with_noise():
    """Test circle detection with noisy image."""
    image = np.random.default_rng(0).integers(0, 50, (200, 200), dtype=np.uint8)
    cv2.circle(image, (100, 100), 60, 200, -1)

    processed_image = preprocess_image(image)
    x, y, radius = get_radius(processed_image)

    assert 80 < x < 120
    assert 80 < y < 120
    assert 40 < radius < 80


def test_parabola_fit(parabola_func):
    """Test parabola fit function."""
    voltages = [14, 21, 30]
    radii = [30, 40, 50]

    fit_result = parabola_fit(voltages, radii)

    assert fit_result.best_values["a"] == pytest.approx(0.01, rel=0.1)
    assert fit_result.best_values["c"] == pytest.approx(5, rel=0.1)
    assert parabola_func(35, **fit_result.best_values) == pytest.approx(17.25)


def test_parabola_fit_window(parabola_func):
    """Test parabola fit function with a window."""
    voltages = [14, 21, 30, 200]
    radii = [30, 40, 50, 40]
    window = np.array(voltages) < 40

    fit_result = parabola_fit(voltages, radii, window=window)

    assert fit_result.best_values["a"] == pytest.approx(0.01, rel=0.1)
    assert fit_result.best_values["c"] == pytest.approx(5, rel=0.1)
    assert parabola_func(35, **fit_result.best_values) == pytest.approx(17.25)


def test_disk_template():
    """Test disk template function."""
    template = disk_kernel(10)

    assert template.shape == (21, 21)
    assert template.dtype == np.float32
    assert template.mean() == pytest.approx(0.0, abs=1e-6)


def test_match_score():
    """Test match score function."""
    image = np.zeros((100, 100), dtype=np.float32)
    cv2.circle(image, (50, 50), 20, 1000, -1)

    score, x, y, radius = match_score(image, 20)

    assert score > 0
    assert x == pytest.approx(50, abs=1e-6)
    assert y == pytest.approx(50, abs=1e-6)
    assert radius == pytest.approx(20, abs=1e-6)


def test_center_and_radius():
    """Test convolve radius detection finds the known disk."""
    for x, y, radius in [(80, 80, 20), (60, 60, 30), (40, 40, 40)]:
        image = np.zeros((180, 180), dtype=np.uint16)
        cv2.circle(image, (x, y), radius, 1000, -1)

        x_found, y_found, radius_found = get_radius_convolve(
            image, r_min=20, r_max=40, step_size=2
        )

        assert x_found == pytest.approx(x, abs=1e-6)
        assert y_found == pytest.approx(y, abs=1e-6)
        assert radius_found == pytest.approx(radius, abs=1e-6)


class TestEvalRadii:
    """Test eval_radii function."""

    @pytest.fixture
    def disk_image(self):
        """Test fixture creates a disk image."""
        image = np.zeros((130, 130), dtype=np.float32)
        cv2.circle(image, (60, 60), 20, 1000, -1)
        return image

    def test_best_radius_threaded(self, disk_image):
        """Test threaded search finds the correct radius."""
        radii = [10, 15, 20, 25, 30]
        _, _, _, radius = eval_radii(disk_image, radii, use_threads=True)

        assert radius == pytest.approx(20, abs=1e-6)

    def test_best_radius_sequential(self, disk_image):
        """Test sequential search finds the correct radius."""
        radii = [10, 15, 20, 25, 30]
        _, _, _, radius = eval_radii(disk_image, radii, use_threads=False)

        assert radius == pytest.approx(20, abs=1e-6)

    def test_single_radius(self, disk_image):
        """Test single radius search still returns a valid result."""
        result = eval_radii(disk_image, [20], use_threads=False)

        assert result[1] == pytest.approx(60, abs=1e-6)
        assert result[2] == pytest.approx(60, abs=1e-6)
        assert result[3] == pytest.approx(20, abs=1e-6)

        result = eval_radii(disk_image, [20], use_threads=True)

        assert result[1] == pytest.approx(60, abs=1e-6)
        assert result[2] == pytest.approx(60, abs=1e-6)
        assert result[3] == pytest.approx(20, abs=1e-6)


class TestDESPCalibration:
    """Test DESPCalibration class."""

    def test_analyze(self, desp_readers, parabola_func):
        """Test calibration uses old DESP fit parameters."""
        calibration = DESPCalibration(desp_readers)

        result = calibration.analyze(window=None)
        params = result["parabola_params"]

        assert result["radii"] == pytest.approx([20, 40, 60], rel=0.1)
        assert params["a"] == pytest.approx(0.01, rel=0.1)
        assert params["c"] == pytest.approx(5, rel=0.1)
        assert parabola_func(30, **params) == pytest.approx(14, rel=0.1)
        assert parabola_func(35, **params) == pytest.approx(17.25, rel=0.1)
        assert parabola_func(40, **params) == pytest.approx(21, rel=0.1)
        assert parabola_func(45, **params) == pytest.approx(25.25, rel=0.1)
        assert parabola_func(50, **params) == pytest.approx(30, rel=0.1)
        assert result["fit_result"].best_values == params

    def test_metadata_override(self, desp_readers, parabola_func):
        """Test metadata values can force old override parameters."""
        for reader, voltage in zip(desp_readers, [10, 34, 74]):
            reader.metadata["Start Voltage"] = [voltage]
        calibration = DESPCalibration(desp_readers)

        result = calibration.analyze(window=None)
        params = result["parabola_params"]

        assert params["a"] == pytest.approx(0.02, rel=0.1)
        assert params["c"] == pytest.approx(2, rel=0.1)
        assert parabola_func(30, **params) == pytest.approx(20, rel=0.1)
        assert parabola_func(50, **params) == pytest.approx(52, rel=0.1)
        assert parabola_func(70, **params) == pytest.approx(100, rel=0.1)

    def test_window(self, desp_readers, parabola_func):
        """Test window removes the old outlier calibration point."""
        for reader, voltage in zip(desp_readers, [10, 34, 104]):
            reader.metadata["Start Voltage"] = [voltage]
        calibration = DESPCalibration(desp_readers)

        result = calibration.analyze(window=np.array([True, True, False]))
        params = result["parabola_params"]

        assert params["a"] == pytest.approx(0.02, rel=0.1)
        assert params["c"] == pytest.approx(2, rel=0.1)
        assert parabola_func(20, **params) == pytest.approx(10, rel=0.1)
        assert parabola_func(40, **params) == pytest.approx(34, rel=0.1)
        assert parabola_func(60, **params) == pytest.approx(74, rel=0.1)

    def test_save_keys(self):
        """Test calibration saves only parabola parameters."""
        assert DESPCalibration.save_keys == ["parabola_params"]


class TestDESPAnalyzer:
    """Test DESPAnalyzer class."""

    @pytest.fixture
    def desp_analyzer(self, desp_readers):
        """Test fixture creates a DESPAnalyzer instance."""
        return DESPAnalyzer(desp_readers, parabola_params={"a": 0.01, "c": 5})

    def test_init(self, desp_analyzer):
        """Test analyzer initialization."""
        assert desp_analyzer.x_array == pytest.approx([64, 64, 64], abs=1)
        assert desp_analyzer.y_array == pytest.approx([128, 128, 128], abs=1)
        assert desp_analyzer.radii_array == pytest.approx([20, 40, 60], rel=0.1)
        assert desp_analyzer.energy_array == pytest.approx([9, 21, 41], rel=0.1)

    def test_processed_image(self, desp_analyzer):
        """Test processed image method."""
        image = desp_analyzer.get_processed_image(1)

        assert isinstance(image, np.ndarray)
        assert image.shape == (256, 128)
        assert image.dtype == np.uint8
        assert image.min() == 0
        assert image.max() == 255

    @pytest.mark.parametrize(
        "radius, energy", [(30, 14), (35, 17.25), (40, 21), (45, 25.25), (50, 30)]
    )
    def test_convert_to_energy(self, desp_analyzer, radius, energy):
        """Test radius to energy conversion."""
        assert desp_analyzer.convert_to_energy(radius) == pytest.approx(energy)

    def test_annotate_image(self, desp_analyzer):
        """Test annotate image draws circle and label."""
        fig, ax = plt.subplots()

        try:
            result = desp_analyzer.annotate_image(1, ax)
            text = ax.texts[0].get_text()

            assert result is ax
            assert len(ax.patches) == 1
            assert len(ax.lines) == 1
            assert "radius = " in text
            assert "energy = " in text
            assert "px" in text
            assert "eV" in text
        finally:
            plt.close(fig)

    def test_plot_energy(self, desp_analyzer):
        """Test plot energy draws energy over time."""
        fig, ax = plt.subplots()

        try:
            result = desp_analyzer.plot_energy(ax)

            assert result is ax
            assert len(ax.lines) == 1
            assert ax.get_xlabel() == "Time [s]"
            assert ax.get_ylabel() == "Electron Energy [eV]"
            assert list(ax.lines[0].get_ydata()) == pytest.approx([9, 21, 41], rel=0.1)
        finally:
            plt.close(fig)
