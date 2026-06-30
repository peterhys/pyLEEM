"""Drift correction for stacks of LEEM images.

This module adapts the pairwise image-registration approach described by
de Jong et al., Ultramicroscopy 213, 112913 (2020), DOI:
10.1016/j.ultramic.2019.112913, and demonstrated in the MIT-licensed
TAdeJong/LEEM-analysis drift correction notebook:
https://github.com/TAdeJong/LEEM-analysis/blob/master/2%20-%20Driftcorrection.ipynb
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from scipy.ndimage import shift as scipy_shift
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


def choose_max_workers(max_workers):
    """Choose the number of drift-correction worker threads."""
    if max_workers is None:
        return min(8, os.cpu_count() or 1)

    if max_workers < 1:
        raise ValueError("max_workers must be at least 1")

    return int(max_workers)


def registration_weight(error):
    """Return a least-squares weight from a registration error."""
    if np.isfinite(error):
        return 1.0 / max(float(error), 1e-6)

    return 0.0


def relative_shifts(
    images,
    upsample_factor=10,
    max_workers=None,
    chunk_size=32,
    max_distance=None,
):
    """Return pairwise shifts needed to align image j to image i."""
    if max_distance is not None and max_distance < 1:
        raise ValueError("max_distance must be at least 1")

    images = np.asarray(images)
    frame_count = images.shape[0]
    worker_count = choose_max_workers(max_workers)

    shifts = np.zeros((frame_count, frame_count, 2), dtype=float)
    weights = np.zeros((frame_count, frame_count), dtype=float)
    pairs = frame_pairs(frame_count, max_distance=max_distance)

    if worker_count == 1:
        result_batches = [register_pairs(images, pairs, upsample_factor)]
    else:
        result_batches = register_pairs_threaded(
            images,
            pairs,
            upsample_factor,
            max_workers=worker_count,
            chunk_size=chunk_size,
        )

    for results in result_batches:
        for i, j, shift, error in results:
            weight = registration_weight(error)
            shifts[i, j] = shift
            shifts[j, i] = -shift
            weights[i, j] = weight
            weights[j, i] = weight

    return shifts, weights


def frame_pairs(count, max_distance=None):
    """Yield frame pairs to register."""
    for i in range(count):
        if max_distance is None:
            stop = count
        else:
            stop = min(count, i + max_distance + 1)

        for j in range(i + 1, stop):
            yield i, j


def chunk_pairs(pairs, chunk_size):
    """Yield fixed-size chunks from a stream of frame pairs."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    chunk = []

    for pair in pairs:
        chunk.append(pair)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


def register_pairs(images, pairs, upsample_factor):
    """Register image pairs and return their measured shifts."""
    results = []

    for i, j in pairs:
        shift, error, _ = phase_cross_correlation(
            images[i],
            images[j],
            upsample_factor=upsample_factor,
        )
        results.append((i, j, shift, error))

    return results


def register_pairs_threaded(images, pairs, upsample_factor, max_workers, chunk_size):
    """Register pair chunks with a thread pool."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for pair_chunk in chunk_pairs(pairs, chunk_size):
            future = executor.submit(
                register_pairs,
                images,
                pair_chunk,
                upsample_factor,
            )
            futures.append(future)

        for future in as_completed(futures):
            yield future.result()


def absolute_shifts(relative_shift_array, weights=None, reference_index=0):
    """Reduce pairwise shifts to correction shifts for each image."""
    frame_count = relative_shift_array.shape[0]
    if frame_count == 1:
        return np.zeros((1, 2), dtype=float)

    equation_rows = []
    measured_shifts = []

    for i in range(frame_count):
        for j in range(i + 1, frame_count):
            weight = 1.0 if weights is None else weights[i, j]
            if weight <= 0:
                continue

            # Each equation is: correction[j] - correction[i] = pair shift.
            row = np.zeros(frame_count, dtype=float)
            row[i] = -weight
            row[j] = weight
            equation_rows.append(row)
            measured_shifts.append(relative_shift_array[i, j] * weight)

    if not equation_rows:
        raise ValueError("no pairwise shifts are available")

    matrix = np.stack(equation_rows)
    targets = np.stack(measured_shifts)
    correction_shifts = np.zeros((frame_count, 2), dtype=float)

    for axis in range(2):
        correction_shifts[:, axis] = np.linalg.lstsq(
            matrix, targets[:, axis], rcond=None
        )[0]

    return correction_shifts - correction_shifts[reference_index]


def calculate_drift(
    images,
    sigma=3,
    crop_size=None,
    upsample_factor=10,
    max_workers=None,
    chunk_size=32,
    max_distance=None,
    reference_index=0,
):
    """Estimate correction shifts for an image stack.

    Shifts use NumPy image-axis order, (y, x). The returned shifts are the
    correction shifts applied to each image, relative to reference_index.
    """
    stack = np.asarray(images)
    registration_images = filter_images(stack, sigma=sigma, crop_size=crop_size)
    shift_matrix, weights = relative_shifts(
        registration_images,
        upsample_factor=upsample_factor,
        max_workers=max_workers,
        chunk_size=chunk_size,
        max_distance=max_distance,
    )
    correction_shifts = absolute_shifts(
        shift_matrix,
        weights=weights,
        reference_index=reference_index,
    )

    return correction_shifts


def shift_canvas(image_shape, shifts):
    """Return the canvas shape and offset needed to apply the shifts."""
    shifts = np.round(np.asarray(shifts, dtype=float), decimals=6)

    min_shift = np.floor(shifts.min(axis=0)).astype(int)
    max_shift = np.ceil(shifts.max(axis=0)).astype(int)

    padding_before = np.maximum(-min_shift, 0)
    padding_after = np.maximum(max_shift, 0)

    canvas_shape = np.asarray(image_shape, dtype=int) + padding_before + padding_after
    offset = padding_before

    return tuple(canvas_shape), tuple(offset)


def image_to_canvas(image, canvas_shape, offset, cval=0.0):
    """Copy an image into a larger canvas."""
    canvas = np.full(canvas_shape, cval, dtype=image.dtype)

    top, left = offset
    height, width = image.shape
    canvas[top : top + height, left : left + width] = image

    return canvas


def apply_shifts(images, shifts, cval=0.0, expand=False):
    """Apply correction shifts to an image stack."""
    images = np.asarray(images)
    shifts = np.asarray(shifts, dtype=float)

    if images.ndim != 3:
        raise ValueError("images must be a 3D stack")

    if shifts.shape != (images.shape[0], 2):
        raise ValueError("images and shifts must have the same length")

    if expand:
        canvas_shape, offset = shift_canvas(images.shape[1:], shifts)
        corrected_images = np.empty(
            (images.shape[0], *canvas_shape), dtype=images.dtype
        )

        for index, (image, shift) in enumerate(zip(images, shifts)):
            canvas_image = image_to_canvas(image, canvas_shape, offset, cval=cval)
            corrected_images[index] = scipy_shift(canvas_image, shift=shift, cval=cval)

        return corrected_images

    return np.stack(
        [
            scipy_shift(image, shift=shift, cval=cval)
            for image, shift in zip(images, shifts)
        ]
    )
