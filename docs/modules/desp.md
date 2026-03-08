# `pyleem.desp`

Diffuse Elastic Scattering Pattern (DESP) analysis.

DESP analysis tracks the radius of the
circular diffraction ring in a series of LEEM micrographs.  A change in radius
corresponds to the shift of the electron energy collected.

{py:class}`~pyleem.desp.DESPAnalyzer` detects the circle using OpenCV (bilateral
filter, Otsu threshold, minimum enclosing circle).
{py:class}`~pyleem.desp.DESPGroup` calibrates
an interpolation function based on radius measurements on a standard sample (Au).

## Example

```python
from pyleem.desp import DESPAnalyzer, DESPGroup
import glob
import matplotlib.pyplot as plt


Au_paths  = sorted(glob.glob("Au/*.dat"))
Au_group  = DESPGroup(Au_paths)
interp_func  = Au_group.calibrate()   # radius to electron energy


# DESPAnalyzer
analyzer = DESPAnalyzer("data.dat", interp_func=interp_func)
print(f"Potential: {analyzer.potential:.2f} eV")
fig, ax = plt.subplots()
analyzer.plot_radius(ax)
plt.show()

# DESPGroup
paths = sorted(glob.glob("sample/*.dat"))
group = DESPGroup(paths, interp_func=interp_func)

fig, ax = plt.subplots()
group.plot_potential(ax)
plt.show()


```

```{eval-rst}
.. automodule:: pyleem.desp
   :members:
   :show-inheritance:
```
