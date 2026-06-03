# `pyleem.analysis.desp`

Diffuse Elastic Scattering Pattern (DESP) analysis.

DESP analysis tracks the radius of the circular diffraction ring in a series of
LEEM micrographs.  A change in radius corresponds to a shift in the collected
electron energy.

{py:class}`~pyleem.analysis.desp.DESPAnalyzer` detects the circle using OpenCV (bilateral
filter, Otsu threshold, minimum enclosing circle). Pass a `potential_func`
interpolation function to compute the surface potential on
construction.

{py:class}`~pyleem.analysis.desp.DESPGroup` processes a batch of files with a shared
`potential_func`. {py:func}`~pyleem.analysis.desp.calibrate_desp` builds the radius to potential
interpolation function from standard-sample measurements and returns it in a dict
under the key `"potential_func"`.

{py:class}`~pyleem.analysis.desp.DESPConfig` drives calibration from a TOML config file
(see the `config` module). The config file uses `path_pattern` (a glob pattern)
under `[calibration]` instead of an explicit paths list.

## Example

```python
from pyleem.analyzer import Analyzer
from pyleem.analysis.desp import DESPAnalyzer, DESPConfig, DESPGroup, calibrate_desp
import glob
import matplotlib.pyplot as plt

# DESP calibration

# from config file
config = DESPConfig("desp_config.toml")
cal_result = config.calibrate(update=True)
potential_func = cal_result["potential_func"]

# manually
Au_paths = sorted(glob.glob("Au/*.dat"))
cal_result = calibrate_desp([Analyzer(path) for path in Au_paths])
potential_func = cal_result["potential_func"]

# DESPAnalyzer
analyzer = DESPAnalyzer("data.dat", potential_func)
print(f"Potential: {analyzer.potential:.2f} eV")
fig, ax = plt.subplots()
analyzer.plot_radius(ax)
plt.show()

# DESPGroup
paths = sorted(glob.glob("sample/*.dat"))
group = DESPGroup(paths, potential_func)

fig, ax = plt.subplots()
group.plot_potential(ax)
plt.show()
```

```{eval-rst}
.. automodule:: pyleem.analysis.desp
   :members:
   :show-inheritance:
```
