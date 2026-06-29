import numpy as np
import pytest
from scipy.ndimage import shift

from pyleem.operation.drift import drift_correct


def marker_image(shape=(64, 64)):
    """Create an asymmetric image with enough structure for registration."""
    image = np.zeros(shape, dtype=float)
    image[18:30, 22:36] = 1.0
    image[42:50, 9:19] = 0.5
    image[12:16, 45:52] = 0.75
    return image


def test_drift_correct_alignment():
    """Test drift_correct aligns images and returns correction shifts."""
    image = marker_image()
    drift_shifts = np.array(
        [
            [0.0, 0.0],
            [3.0, -2.0],
            [-4.0, 5.0],
        ]
    )
    images = np.stack(
        [
            shift(image, drift_shift, order=1, mode="constant", cval=0.0)
            for drift_shift in drift_shifts
        ]
    )

    corrected_images, correction_shifts = drift_correct(
        images,
        sigma=0,
        upsample_factor=1,
    )

    assert correction_shifts == pytest.approx(-drift_shifts)
    assert corrected_images[1] == pytest.approx(corrected_images[0], abs=1e-6)
    assert corrected_images[2] == pytest.approx(corrected_images[0], abs=1e-6)
