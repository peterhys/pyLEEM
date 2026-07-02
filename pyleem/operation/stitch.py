"""Operation functions to stitch profiles together."""

import numpy as np


def find_stitch_points(x_ranges, method="midpoint"):
    """Locate the stitch points between the ranges.

    :param list x_ranges: List of abscissa ranges.
    :param str method: Method to locate the stitch points.
    :return: List of stitch points.
    :rtype: list
    """

    if method == "end":
        stitch_points = [r[1] for r in x_ranges[:-1]]
    elif method == "start":
        stitch_points = [r[0] for r in x_ranges[1:]]
    elif method == "midpoint":
        stitch_points = [
            (x_ranges[i][1] + x_ranges[i + 1][0]) / 2 for i in range(len(x_ranges) - 1)
        ]
    else:
        raise ValueError(f"Invalid method: {method}")

    return stitch_points


def stitch_profiles(x_array_list, y_array_list, mask_points):
    """Stitch profiles together based on mask points.

    Each x and y array is assumed to be sorted.
    Currently, if the abscissa of a profile lands exactly on a mask point,
    the point is included in the first profile and excluded from the second profile.
    For the last profile, the last mask point is included.

    This can lead to an issue that at same x value, there
    are two different y values.

    :param list x_array_list: List of x arrays for each profile.
    :param list y_array_list: List of y arrays for each profile.
    :param list mask_points: List of mask points between profiles.
    :return: Stitched profile and abscissa.
    :rtype: tuple
    """
    masked_y_array_list = []
    masked_x_array_list = []
    for i, (x_array, y_array) in enumerate(zip(x_array_list, y_array_list)):
        if i == len(x_array_list) - 1:
            mask = (x_array >= mask_points[i]) & (x_array <= mask_points[i + 1])
        else:
            mask = (x_array >= mask_points[i]) & (x_array < mask_points[i + 1])
        masked_y_array_list.append(y_array[mask])
        masked_x_array_list.append(x_array[mask])

    return np.concatenate(masked_x_array_list), np.concatenate(masked_y_array_list)
