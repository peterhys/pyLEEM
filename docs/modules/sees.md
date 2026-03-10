# `pyleem.sees`

Secondary Electron Energy Spectroscopy (SEES) analysis.

{py:func}`~pyleem.sees.calibrate_sees` derives `pixel_per_ev` and `peak_shift`
from multiple scans acquired at known start voltages and returns the calibration
result as a dict.
{py:class}`~pyleem.sees.SEESAnalyzer` extracts the SE onset from a single profile
and calculates the surface potential by comparing the onset position to a
calibrated reference. A built-in Gaussian filter smooths the profile; its sigma
is set at construction time.

{py:class}`~pyleem.sees.SEESGroup` processes a time series of files.


## Example

```python
from pyleem.sees import SEESAnalyzer, SEESGroup, calibrate_sees
from pyleem.roi import LineROI
from pyleem.analysis import ProfileAnalyzer
import glob
import matplotlib.pyplot as plt

# SEES calibration

# from config file
base_params, cal_params = read_config("config.toml")
roi = base_params["roi"]
paths = base_params["paths"]

# manually set the paths
roi = LineROI(src=(256, 10), dst=(256, 500), linewidth=20)
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
cal_result = calibrate_sees([ProfileAnalyzer(path, roi) for path in paths])
pixel_per_ev, peak_shift = cal_result["pixel_per_ev"], cal_result["peak_shift"]


# SEESAnalyzer
analyzer = SEESAnalyzer("data.dat", roi, pixel_per_ev, peak_shift, sigma=10)
print(f"Potential: {analyzer.surface_potential:.3f} eV")

fig, ax = plt.subplots()
analyzer.plot(ax, show_fit=True)
plt.show()

# SEESGroup
paths = sorted(glob.glob("sample/*.dat"))
group = SEESGroup(paths, roi, pixel_per_ev, peak_shift, sigma=10)

potentials = group.get_attrs("potential")
time_intervals = group.get_time_intervals()
```

```{eval-rst}
.. automodule:: pyleem.sees
   :members:
   :show-inheritance:
```
