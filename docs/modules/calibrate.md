# `pyleem.calibrate`

The module provides parsing of TOML configuration files. A configuration file
points to calibration files and an ROI. The module can either update the
calibration parameters to the configuration file or read them from the file.
The calibration files are used for dispersive plane analysis (SEES, XPS, etc.).

## Config file format

```toml
# config.toml
[base]
paths = ["data_0eV.dat", "data_100eV.dat", "data_200eV.dat"]
roi   = "line.roi"

[calibration]
# For XPS: additional reference peak parameters are required.
num_peaks  = 1
baselines  = [[197, 100], [197, 100], [197, 100]]
ref_index  = 0
ref_value  = 285.0


[result]
# If result section is present, the calibration function can read
# the calibration parameters. Otherwise, reset=True can update the
# field.
pixel_per_ev = 165.8
peak_shift   = 3.72
```

## Example

```python
from pyleem.calibrate import calibrate_profile_config
from pyleem.sees import SEESGroup

# Run calibration and save result to the TOML
# Plot the calibration plots
roi = calibrate_profile_config("config.toml", SEESGroup, reset=True, plot=True)

# On subsequent runs, reload from the saved [result] section
roi = calibrate_profile_config("config.toml", SEESGroup, reset=False)

print(roi.is_calibrated)  # True
print(roi.pixel_per_ev, roi.peak_shift)
```

The returned `roi` is a calibrated {py:class}`~pyleem.roi.LineROI` ready to be passed to any
{py:class}`~pyleem.analysis.ProfileAnalyzer` or {py:class}`~pyleem.analysis.AnalyzerGroup` subclass.

```{eval-rst}
.. automodule:: pyleem.calibrate
   :members:
   :show-inheritance:
```
