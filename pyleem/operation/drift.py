"""Drift correction for stacks of LEEM images.

This module adapts the pairwise image-registration approach described by
de Jong et al., Ultramicroscopy 213, 112913 (2020), DOI:
10.1016/j.ultramic.2019.112913, and demonstrated in the MIT-licensed
TAdeJong/LEEM-analysis drift correction notebook:
https://github.com/TAdeJong/LEEM-analysis/blob/master/2%20-%20Driftcorrection.ipynb
"""

import numpy as np
from scipy.ndimage import shift as shift_image
from skimage import filters
from skimage.registration import phase_cross_correlation


def crop_center(image, crop_size):
    """Return the centered crop of an image."""
    if crop_size is None:
        return image

    if np.isscalar(crop_size):
        crop_height = crop_width = int(crop_size)
    else:
        crop_height, crop_width = crop_size

    height, width = image.shape
    if crop_height > height or crop_width > width:
        raise ValueError("crop_size cannot be larger than the image")

    top = (height - crop_height) // 2
    left = (width - crop_width) // 2

    return image[top : top + crop_height, left : left + crop_width]


def filter_image(image, sigma=3, crop_size=None):
    """Crop, smooth, edge-filter, and center one image for registration."""
    image = crop_center(np.asarray(image, dtype=float), crop_size)

    if sigma and sigma > 0:
        image = filters.gaussian(image, sigma=sigma, mode="nearest")

    image = filters.sobel(image)

    return image - image.mean()


def filter_images(images, sigma=3, crop_size=None):
    """Filter an image stack for drift registration."""
    return np.stack(
        [filter_image(image, sigma=sigma, crop_size=crop_size) for image in images]
    )


def relative_shifts(images, upsample_factor=10):
    """Return pairwise shifts needed to align image j to image i."""
    count = images.shape[0]
    shifts = np.zeros((count, count, 2), dtype=float)
    weights = np.zeros((count, count), dtype=float)

    for i in range(count):
        weights[i, i] = 1.0
        for j in range(i + 1, count):
            shift, error, _ = phase_cross_correlation(
                images[i],
                images[j],
                upsample_factor=upsample_factor,
            )
            if np.isfinite(error):
                weight = 1.0 / max(float(error), 1e-6)
            else:
                weight = 0.0

            shifts[i, j] = shift
            shifts[j, i] = -shift
            weights[i, j] = weight
            weights[j, i] = weight

    return shifts, weights


def absolute_shifts(relative_shift_array, weights=None, reference_index=0):
    """Reduce pairwise shifts to correction shifts for each image."""
    count = relative_shift_array.shape[0]
    if count == 1:
        return np.zeros((1, 2), dtype=float)

    rows = []
    values = []

    for i in range(count):
        for j in range(i + 1, count):
            weight = 1.0 if weights is None else weights[i, j]
            if weight <= 0:
                continue

            row = np.zeros(count, dtype=float)
            row[i] = -weight
            row[j] = weight
            rows.append(row)
            values.append(relative_shift_array[i, j] * weight)

    if not rows:
        raise ValueError("no pairwise shifts are available")

    matrix = np.stack(rows)
    targets = np.stack(values)
    correction_shifts = np.zeros((count, 2), dtype=float)

    for axis in range(2):
        correction_shifts[:, axis] = np.linalg.lstsq(
            matrix,
            targets[:, axis],
            rcond=None,
        )[0]

    return correction_shifts - correction_shifts[reference_index]


def apply_shifts(images, shifts, order=1, mode="constant", cval=0.0):
    """Apply correction shifts to every image in a stack."""
    return np.stack(
        [
            shift_image(image, shift=shift, order=order, mode=mode, cval=cval)
            for image, shift in zip(images, shifts)
        ]
    )


def drift_correct(
    images,
    sigma=3,
    crop_size=None,
    upsample_factor=10,
    reference_index=0,
    order=1,
    mode="constant",
    cval=0.0,
):
    """Correct drift in an image stack.

    Shifts use NumPy image-axis order, (y, x). The returned shifts are the
    correction shifts applied to each image, relative to reference_index.
    """
    stack = np.asarray(images)
    registration_images = filter_images(stack, sigma=sigma, crop_size=crop_size)
    shift_matrix, weights = relative_shifts(
        registration_images,
        upsample_factor=upsample_factor,
    )
    correction_shifts = absolute_shifts(
        shift_matrix,
        weights=weights,
        reference_index=reference_index,
    )
    corrected_images = apply_shifts(
        stack,
        correction_shifts,
        order=order,
        mode=mode,
        cval=cval,
    )

    return corrected_images, correction_shifts
