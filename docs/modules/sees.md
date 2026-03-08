# `pyleem.sees`

Secondary Electron Energy Spectroscopy (SEES) analysis.

{py:class}`~pyleem.sees.SEESAnalyzer` extracts the SE onset from a single profile,
and calculates the zero voltage value from the onset position. The surface
potential is then calculated by comparing onset shift to known standard (Au).
For noisy sample, a built-in Gaussian filter is used to smooth the profile, with
adjustable sigma defined at the construction time.
{py:class}`~pyleem.sees.SEESGroup` processes
a time series of files and can calibrate the pixel per eV and peak shift from
data files acquired at known voltages.


## Example

```python
from pyleem.calibrate import calibrate_profile_config
from pyleem.sees import SEESAnalyzer, SEESGroup
import glob
import matplotlib.pyplot as plt

# SEES calibration
roi = calibrate_profile_config("config.toml", SEESGroup)

# SEESAnalyzer
analyzer = SEESAnalyzer("data.dat", roi, sigma=10)
print(f"Potential: {analyzer.surface_potential:.3f} eV")

fig, ax = plt.subplots()
analyzer.plot(ax, show_fit=True)
plt.show()

# SEESGroup
paths = sorted(glob.glob("sample/*.dat"))
group = SEESGroup(paths, roi, sigma=10)

potentials = group.get_attrs("surface_potential")
time_intervals = group.get_time_intervals()
```

```{eval-rst}
.. automodule:: pyleem.sees
   :members:
   :show-inheritance:
```
