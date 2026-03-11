# `pyleem.stitch`

Profile stitching for combining multiple overlapping spectra into a single
continuous spectrum.

{py:class}`~pyleem.stitch.StitchGroup` accepts a list of same-type
`ProfileAnalyzer` instances whose abscissa ranges overlap. It sorts them by
their minimum abscissa value, computes or accepts explicit stitch points, and
delegates concatenation to {py:func}`~pyleem.utils.stitch_profiles`.

The result is exposed through the {py:attr}`~pyleem.stitch.StitchGroup.stitched_analyzer`
property, which returns a {py:class}`~pyleem.stitch.StitchAnalyzer`. This
lightweight object stores `abscissa`, `ordinate`, and the axis labels, and
forwards any method call that exists on the source analyzer class via
`__getattr__`.

## Example

```python
from pyleem.xps import XPSAnalyzer
from pyleem.stitch import StitchGroup
from pyleem.roi import LineROI
import matplotlib.pyplot as plt

roi = LineROI(src=(256, 0), dst=(256, 511), linewidth=10)

# Three XPS scans with overlapping energy ranges
analyzers = [
    XPSAnalyzer(path, roi, pixel_per_ev, peak_shift, incident_voltage=400)
    for path in ["data_280eV.dat", "data_284eV.dat", "data_288eV.dat"]
]

# Auto-compute stitch points at the midpoint of each overlap
group = StitchGroup(analyzers, method="midpoint")

print(group.stitch_points)  # list of N-1 cut values

# Access the stitched result
stitched = group.stitched_analyzer
print(stitched.abscissa_label)  # "Binding Energy [eV]"

# Plot the stitched spectrum — method forwarded from XPSAnalyzer
fig, ax = plt.subplots()
stitched.plot_profile(ax)
plt.show()

# Provide explicit stitch points instead
group = StitchGroup(analyzers, stitch_points=[195.0, 197.5])
stitched = group.stitched_analyzer
```

```{eval-rst}
.. automodule:: pyleem.stitch
   :members:
   :show-inheritance:
```
