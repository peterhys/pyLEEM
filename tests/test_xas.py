import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyleem.analysis.xas import XASAnalyzer
from pyleem.roi import RectROI


def half_field_images(shape=(256, 128)):
    """Create four black-and-white XAS test images.

    Here we have four images:
    - left_black: left half is black, right half is white
    - all_white: all pixels are white
    - all_black: all pixels are black
    - left_white: left half is white, right half is black

    In the tests, we pick three regions to test the profiles.
    """
    _, width = shape
    midpoint = width // 2

    left_black = np.full(shape, 1000, dtype=np.uint16)
    left_black[:, :midpoint] = 0

    all_white = np.full(shape, 1000, dtype=np.uint16)
    all_black = np.zeros(shape, dtype=np.uint16)

    left_white = np.zeros(shape, dtype=np.uint16)
    left_white[:, :midpoint] = 1000

    return [left_black, all_white, all_black, left_white]


@pytest.fixture
def xas_readers(raw_reader_factory):
    """Create XAS readers with known half-field images."""
    images = half_field_images()

    readers = [
        raw_reader_factory(f"xas_{index}.dat", image)
        for index, image in enumerate(images)
    ]
    for index, reader in enumerate(readers):
        reader.update_metadata({"Beam Energy": (10 + index, "eV")})

    return readers


def test_get_intensities(xas_readers):
    """Test XASAnalyzer ROI mean intensities."""
    roi_1 = RectROI(top=0, left=0, bottom=256, right=64)
    roi_2 = RectROI(top=0, left=32, bottom=256, right=96)
    roi_3 = RectROI(top=0, left=64, bottom=256, right=128)

    # left-side ROI, should be black, white, black, white
    analyzer = XASAnalyzer(
        xas_readers,
        roi=roi_1,
    )
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([0.0, 1000.0, 0.0, 1000.0]))

    # middle ROI, should be half, white, black, half
    analyzer = XASAnalyzer(
        xas_readers,
        roi=roi_2,
    )
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([500.0, 1000.0, 0.0, 500.0]))

    # right-side ROI, should be white, white, black, black
    analyzer = XASAnalyzer(
        xas_readers,
        roi=roi_3,
    )
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([1000.0, 1000.0, 0.0, 0.0]))


def test_get_processed_image(xas_readers):
    """Test XASAnalyzer get_processed_image dependency on drift correction."""
    analyzer = XASAnalyzer(
        xas_readers, roi=RectROI(top=0, left=0, bottom=256, right=64)
    )
    assert np.array_equal(analyzer.get_processed_image(0), analyzer.get_raw_image(0))

    with warnings.catch_warnings():
        # The image does not have enough variation for drift correction,
        # which would raise a warning.
        warnings.filterwarnings(
            "ignore",
            message="Could not determine RMS error",
            category=UserWarning,
        )
        analyzer.correct_drift()
    assert hasattr(analyzer, "correction_shifts")
    assert analyzer.get_processed_image(1).shape == analyzer.get_raw_image(1).shape


def test_xas_plot_intensity(xas_readers):
    """Test XASAnalyzer plots ROI intensity by Beam Energy."""
    roi = RectROI(top=0, left=0, bottom=256, right=64)
    analyzer = XASAnalyzer(
        xas_readers,
        roi=roi,
    )
    fig, ax = plt.subplots()

    returned = analyzer.plot_intensity(ax=ax)

    line = ax.lines[0]
    assert returned is ax
    assert np.array_equal(line.get_xdata(), np.array([10.0, 11.0, 12.0, 13.0]))
    assert line.get_ydata() == pytest.approx([0.0, 1000.0, 0.0, 1000.0])
    assert ax.get_xlabel() == "Beam Energy [eV]"
    assert ax.get_ylabel() == "Intensity"
    plt.close(fig)
