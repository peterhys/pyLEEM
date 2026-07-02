import warnings

import numpy as np

from pyleem.analysis.fullfield import FullFieldAnalyzer
from pyleem.roi import RectROI


def test_fullfield_get_intensities(fullfield_readers):
    """Test FullFieldAnalyzer ROI mean intensities."""
    roi_1 = RectROI(top=0, left=0, bottom=256, right=64)
    roi_2 = RectROI(top=0, left=32, bottom=256, right=96)
    roi_3 = RectROI(top=0, left=64, bottom=256, right=128)

    analyzer = FullFieldAnalyzer(fullfield_readers, roi=roi_1)
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([0.0, 1000.0, 0.0, 1000.0]))

    analyzer = FullFieldAnalyzer(fullfield_readers, roi=roi_2)
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([500.0, 1000.0, 0.0, 500.0]))

    analyzer = FullFieldAnalyzer(fullfield_readers, roi=roi_3)
    intensities = analyzer.get_intensities()
    assert np.array_equal(intensities, np.array([1000.0, 1000.0, 0.0, 0.0]))


def test_fullfield_get_processed_image(fullfield_readers):
    """Test FullFieldAnalyzer get_processed_image after drift correction."""
    analyzer = FullFieldAnalyzer(
        fullfield_readers,
        roi=RectROI(top=0, left=0, bottom=256, right=64),
    )
    assert np.array_equal(analyzer.get_processed_image(0), analyzer.get_raw_image(0))

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Could not determine RMS error",
            category=UserWarning,
        )
        analyzer.correct_drift()

    assert hasattr(analyzer, "correction_shifts")
    assert analyzer.get_processed_image(1).shape == analyzer.get_raw_image(1).shape
