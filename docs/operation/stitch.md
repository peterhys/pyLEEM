# Sitch Spectra

Profile stitching utilities for combining multiple overlapping spectra into a
single continuous profile.

The current implementation exposes two functions:

1. {py:func}`~pyleem.operation.stitch.find_stitch_points` computes cut values
    between neighboring x ranges using `"midpoint"`, `"start"`, or `"end"` strategy.
2. {py:func}`~pyleem.operation.stitch.stitch_profiles` applies mask boundaries to
    x/y profile arrays and concatenates the selected segments.


## Example

```python
import numpy as np

from pyleem.operation.stitch import find_stitch_points, stitch_profiles

x_arrays = [
    np.array([0, 1, 2, 3, 4]),
    np.array([3, 4, 5, 6, 7]),
    np.array([6, 7, 8, 9, 10]),
]
y_arrays = [
    np.array([10, 20, 30, 40, 50]),
    np.array([60, 70, 80, 90, 100]),
    np.array([110, 120, 130, 140, 150]),
]

x_ranges = [(x[0], x[-1]) for x in x_arrays]
stitch_points = find_stitch_points(x_ranges, method="midpoint")
mask_points = [x_ranges[0][0], *stitch_points, x_ranges[-1][1]]

stitched_x, stitched_y = stitch_profiles(x_arrays, y_arrays, mask_points)
```
