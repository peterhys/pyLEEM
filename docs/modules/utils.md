# `pyleem.utils`

Utility functions for pyLEEM package.

| Function | Purpose |
|---|---|
| {py:func}`~pyleem.utils.find_onset` | Locates the steepest relative rise in a list of profiles or scalar sums, returning the index of the onset frame. |
| {py:func}`~pyleem.utils.find_stitch_points` | Computes N-1 cut values between N overlapping abscissa ranges using `"midpoint"`, `"start"`, or `"end"` strategy. |
| {py:func}`~pyleem.utils.stitch_profiles` | Concatenates profiles and their abscissas by masking each to its assigned segment. |


```{eval-rst}
.. automodule:: pyleem.utils
   :members:
```
