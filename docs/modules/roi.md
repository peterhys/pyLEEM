# `pyleem.roi`

ROI for image measurements. The ROI is a core element in the analyzer analysis,
and is required for analyzer construction. For analysis that do not require an ROI,
a placeholder NoROI is used. In particular, a LineROI is used to extract line profile from the image, and the
AreaROI is used to extract area information or perform other types of analysis.

The ROI class can be constructed using a ImageJ ROI file or manually specified parameters.
The ROI class can be subclassed and it should carry the analysis methods.

## Example

```python
import numpy as np

from pyleem.roi import LineROI, RectROI

image = np.arange(10000).reshape(100, 100)

# Line ROI: extract a line profile and intensity statistics.
line_roi = LineROI(src=(10, 5), dst=(10, 80), linewidth=3)
line_measurement = line_roi.measure(image)
profile = line_measurement.profile

# Area ROI: measure intensity statistics inside a rectangle.
area_roi = RectROI(top=20, left=30, bottom=50, right=60)
area_measurement = area_roi.measure(image)
mean_intensity = area_measurement.mean

# Save and reload ImageJ ROI files.
line_roi.tofile("line.roi")
area_roi.tofile("area.roi")
line_roi = LineROI(roi_file="line.roi")
```

## Subclassing

The ROI classes can be subclassed to add custom selection or analysis logic.
The required methods are `measure`, `profile`, `fromfile`, and `tofile`.


```{eval-rst}
.. automodule:: pyleem.roi
   :members:
   :show-inheritance:
   :exclude-members: reduce_func
```
