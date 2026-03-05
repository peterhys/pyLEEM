import numpy as np


def find_onset(profiles):
    """Find the onset of a profile.

    The profiles can be full images or line profiles.
    Here we look at the "relative difference". The
    np.gradient is not used beucase it tracks two steps at a time.

    :param list profiles: List of profiles to find the onset of.
    :return: Index of the profile with the steepest rise.
    :rtype: int
    """

    profile_sums = np.array([profile.sum() for profile in profiles], dtype=np.float64)
    profile_diff = np.diff(profile_sums) / profile_sums[:-1]

    return np.argmax(profile_diff)


def find_stitch_points(abscissa_ranges, method="midpoint"):
    """Locate the stitch points between the ranges.

    :param list abscissa_ranges: List of abscissa ranges.
    :param str method: Method to locate the stitch points.
    :return: List of stitch points.
    :rtype: list
    """

    if method == "end":
        stitch_points = [r[1] for r in abscissa_ranges[:-1]]
    elif method == "start":
        stitch_points = [r[0] for r in abscissa_ranges[1:]]
    elif method == "midpoint":
        stitch_points = [
            (abscissa_ranges[i][0] + abscissa_ranges[i + 1][1]) / 2
            for i in range(len(abscissa_ranges) - 1)
        ]
    else:
        raise ValueError(f"Invalid method: {method}")

    return stitch_points


def stitch_profiles(abscissas, profiles, mask_points):
    """Stitch profiles together based on mask points.

    The abscissas and profile are assumed to be sorted.
    Currently, if the abscissa of a profile lands exactly on a mask point,
    the point is included in the both profiles.

    This can lead to an issue that at same x value, there
    are two different y values.

    :param list abscissas: List of abscissas for each profile.
    :param list profiles: List of profiles to stitch.
    :param list mask_points: List of mask points between profiles.
    :return: Stitched profile and abscissa.
    :rtype: tuple
    """
    masked_profiles = []
    masked_abscissas = []
    for i, (abscissa, profile) in enumerate(zip(abscissas, profiles)):
        mask = (abscissa >= mask_points[i]) & (abscissa <= mask_points[i + 1])
        masked_profiles.append(profile[mask])
        masked_abscissas.append(abscissa[mask])

    return np.concatenate(masked_abscissas), np.concatenate(masked_profiles)
