import numpy as np
import pytest
from scipy.ndimage import shift

from pyleem.operation.drift import apply_shifts, calculate_drift, relative_shifts


def marker_image(shape=(64, 64)):
    """Create an asymmetric image with enough structure for registration."""
    image = np.zeros(shape, dtype=float)
    image[18:30, 22:36] = 1.0
    image[42:50, 9:19] = 0.5
    image[12:16, 45:52] = 0.75
    return image


def test_calculate_drift_alignment():
    """Test calculate_drift returns correction shifts that align images."""
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

    correction_shifts = calculate_drift(
        images,
        sigma=0,
        upsample_factor=1,
    )
    corrected_images = apply_shifts(images, correction_shifts)

    assert correction_shifts == pytest.approx(-drift_shifts)
    assert corrected_images[1] == pytest.approx(corrected_images[0], abs=1e-6)
    assert corrected_images[2] == pytest.approx(corrected_images[0], abs=1e-6)


def test_apply_shifts_expand():
    """Test expanded shifting creates room for translated image content."""
    image = np.zeros((3, 4), dtype=float)
    image[1, 1] = 1.0
    images = np.stack([image, image])
    shifts = np.array(
        [
            [0.0, 0.0],
            [2.0, -1.0],
        ]
    )

    shifted_images = apply_shifts(images, shifts, expand=True)

    assert shifted_images.shape == (2, 5, 5)
    assert shifted_images[0, 1, 2] == pytest.approx(1.0)
    assert shifted_images[1, 3, 1] == pytest.approx(1.0)
    assert shifted_images.sum() == pytest.approx(2.0)


def test_apply_shifts_raises():
    """Test apply_shifts rejects shift stacks with the wrong length."""
    images = np.stack([marker_image(), marker_image()])
    shifts = np.zeros((1, 2), dtype=float)

    with pytest.raises(ValueError, match="images and shifts must have the same length"):
        apply_shifts(images, shifts)


def test_apply_shifts_expand():
    """Test apply_shifts can expand the output canvas."""
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

    correction_shifts = calculate_drift(
        images,
        sigma=0,
        upsample_factor=1,
    )
    corrected_images = apply_shifts(images, correction_shifts, expand=True)

    assert correction_shifts == pytest.approx(-drift_shifts)
    assert corrected_images.shape == (3, 71, 71)


def test_relative_shifts():
    """Test threaded pair registration matches serial pair registration."""
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

    serial_shifts, serial_weights = relative_shifts(
        images,
        upsample_factor=1,
        max_workers=1,
    )
    threaded_shifts, threaded_weights = relative_shifts(
        images,
        upsample_factor=1,
        max_workers=2,
        chunk_size=1,
    )

    assert threaded_shifts == pytest.approx(serial_shifts)
    assert threaded_weights == pytest.approx(serial_weights)


def test_relative_shifts_max_distance():
    """Test max_distance limits pair registration to nearby frames."""
    image = marker_image()
    drift_shifts = np.array(
        [
            [0.0, 0.0],
            [2.0, -1.0],
            [4.0, -2.0],
            [6.0, -3.0],
        ]
    )
    images = np.stack(
        [
            shift(image, drift_shift, order=1, mode="constant", cval=0.0)
            for drift_shift in drift_shifts
        ]
    )

    shift_matrix, weights = relative_shifts(
        images,
        upsample_factor=1,
        max_distance=1,
    )

    assert weights[0, 1] > 0
    assert weights[1, 2] > 0
    assert weights[2, 3] > 0
    assert weights[0, 2] == 0
    assert weights[0, 3] == 0
    assert weights[1, 3] == 0
    assert shift_matrix[0, 2] == pytest.approx([0, 0])
    assert shift_matrix[1, 3] == pytest.approx([0, 0])


def test_relative_shifts_raises():
    """Test max_distance must include at least adjacent pairs."""
    images = np.stack([marker_image(), marker_image()])

    with pytest.raises(ValueError, match="max_distance must be at least 1"):
        relative_shifts(images, max_distance=0)


def test_calculate_drift():
    """Test max_workers=None selects automatic threaded drift correction."""
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

    correction_shifts = calculate_drift(
        images,
        sigma=0,
        upsample_factor=1,
        max_workers=None,
        chunk_size=1,
    )
    corrected_images = apply_shifts(images, correction_shifts)

    assert correction_shifts == pytest.approx(-drift_shifts)
    assert corrected_images[1] == pytest.approx(corrected_images[0], abs=1e-6)
    assert corrected_images[2] == pytest.approx(corrected_images[0], abs=1e-6)
