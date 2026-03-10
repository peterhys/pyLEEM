# `pyleem.roi`

Line ROI for profile extraction.

{py:class}`~pyleem.roi.LineROI` wraps a line from an ImageJ ROI file or
a manually specified line and stores the
calibration parameters (`pixel_per_ev`, `peak_shift`).

## Example

```python
from pyleem.roi import LineROI

# ImageJ .roi file
roi = LineROI("line.roi")

# Specify manually (coordinates in (row, col) / (y, x) order)
roi = LineROI(src=(256, 10), dst=(256, 500), linewidth=20)

# Export back to ImageJ
roi.to_roifile("line.roi")

# Convert to a dict for skimage.measure.profile_line
print(roi.to_dict())
# {'src': (256, 10), 'dst': (256, 500), 'linewidth': 20, ...}
```

```{eval-rst}
.. automodule:: pyleem.roi
   :members:
   :show-inheritance:
```
