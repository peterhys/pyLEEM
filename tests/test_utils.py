import pytest
import numpy as np
from pyleem.utils import find_onset, find_stitch_points, stitch_profiles


def test_find_onset():
    """Test find_onset with 2D images.

    Low noise frames followed by signal frames."""

    shape = (20, 20)
    images = np.zeros((10, *shape))
    images[:5] = np.random.normal(0.1, 0.1, (5, *shape))
    images[5:] = np.random.normal(0.1, 0.1, (5, *shape)) + 10  # added signal

    onset_idx = find_onset(images)
    assert onset_idx == 4


def test_find_stitch_points():
    """Test find_stitch_points across all supported methods and edge cases."""
    ranges = [(0, 10), (5, 15), (10, 20)]
    assert find_stitch_points(ranges, method="midpoint") == pytest.approx([7.5, 12.5])
    assert find_stitch_points(ranges, method="end") == [10, 15]
    assert find_stitch_points(ranges, method="start") == [5, 10]
    # signle range no stitch points
    assert find_stitch_points([(0, 10)], method="midpoint") == []

    with pytest.raises(ValueError, match="Invalid method: other"):
        find_stitch_points([(0, 10), (5, 15)], method="other")


def test_stitch_profiles():
    """Test stitch_profiles with 3 overlapping profiles and midpoint stitch cuts.

    Profile abscissas overlap: profile i+1 starts before profile i ends.
    Stitch points fall between overlapping regions so each profile contributes
    a non-duplicate, contiguous segment to the result.

    Profiles:
        - Profile 0: x=[0..4],  y=[10,20,30,40,50]
        - Profile 1: x=[3..7],  y=[60,70,80,90,100]
        - Profile 2: x=[6..10], y=[110,120,130,140,150]

    Mask points [0, 3.5, 6.5, 10] select:
        - Profile 0: x in [0, 3.5]   -> x=[0,1,2,3],   y=[10,20,30,40]
        - Profile 1: x in [3.5, 6.5] -> x=[4,5,6],     y=[70,80,90]
        - Profile 2: x in [6.5, 10]  -> x=[7,8,9,10],  y=[120,130,140,150]
    """
    abscissas = [
        np.array([0, 1, 2, 3, 4]),
        np.array([3, 4, 5, 6, 7]),
        np.array([6, 7, 8, 9, 10]),
    ]
    profiles = [
        np.array([10, 20, 30, 40, 50]),
        np.array([60, 70, 80, 90, 100]),
        np.array([110, 120, 130, 140, 150]),
    ]

    # stitch points off abscissa values
    mask_points = [0, 3.5, 6.5, 10]

    stitched_x, stitched_y = stitch_profiles(abscissas, profiles, mask_points)

    expected_x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    expected_y = np.array([10, 20, 30, 40, 70, 80, 90, 120, 130, 140, 150])

    assert all(stitched_x == expected_x)
    assert all(stitched_y == expected_y)

    # stitch points on abscissa values
    mask_points = [0, 3, 6, 10]
    stitched_x, stitched_y = stitch_profiles(abscissas, profiles, mask_points)

    expected_x = np.array([0, 1, 2, 3, 3, 4, 5, 6, 6, 7, 8, 9, 10])
    expected_y = np.array([10, 20, 30, 40, 60, 70, 80, 90, 110, 120, 130, 140, 150])

    assert all(stitched_x == expected_x)
    assert all(stitched_y == expected_y)
