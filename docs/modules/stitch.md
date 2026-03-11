# `pyleem.analysis.stitch`

Profile stitching for combining multiple overlapping spectra into a single
continuous spectrum.

{py:class}`~pyleem.analysis.stitch.StitchAnalyzer` is a subclass of
{py:class}`~pyleem.analyzer.ProfileAnalyzer` that combines a list of same-type
analyzers with overlapping abscissa ranges into one continuous profile. The
analyzers are sorted by their minimum abscissa value. The stitch points are either
supplied explicitly or auto-computed via {py:func}`~pyleem.utils.find_stitch_points`
using a `stitch_method` (`'midpoint'`, `'start'`, or `'end'`). Because it has no
file, `image` and `reader` are unavailable; metadata can be passed directly to
the constructor.

## Example

```python
from pyleem.analysis.xps import XPSAnalyzer
from pyleem.analysis.stitch import StitchAnalyzer
from pyleem.roi import LineROI
import matplotlib.pyplot as plt

roi = LineROI(src=(256, 0), dst=(256, 511), linewidth=10)

# Three XPS scans with overlapping energy ranges
analyzers = [
    XPSAnalyzer(path, roi, pixel_per_ev, peak_shift, incident_voltage=400)
    for path in ["data_280eV.dat", "data_284eV.dat", "data_288eV.dat"]
]

# Generate the stitch analyzer
stitch_analyzer = StitchAnalyzer(analyzers, stitch_method="midpoint")

print(stitch_analyzer.stitch_points)
print(stitch_analyzer.abscissa_label) # Binding Energy [eV]

# Provide explicit stitch points instead
# And provide metadata
stitch_analyzer = StitchAnalyzer(
    analyzers, stitch_points=[195.0, 197.5], metadata={"Incident Voltage": (400, "eV")}
)
```

```{eval-rst}
.. automodule:: pyleem.analysis.stitch
   :members:
   :show-inheritance:
```
