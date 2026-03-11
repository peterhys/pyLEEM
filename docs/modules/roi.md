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

# Read profile from image
profile = roi.read_profile(image)

# Export back to ImageJ file
roi.to_roi_object().tofile("line.roi")
```

```{eval-rst}
.. automodule:: pyleem.roi
   :members:
   :show-inheritance:
```
