# Workflow

The workflow of pyLEEM analysis consists of two parts: calibration and analysis.

## Calibration

For domain specific profile analyzers (SEES, XPS, etc.), `pixel_per_ev` and `peak_shift` must be
determined before creating any analyzer. For domain specific image analyzers,
`potential_func` must be determined before creating any analyzer.
Calibration is performed by the module-level functions
`calibrate_sees`, `calibrate_xps`, or `calibrate_desp`, which accept a list of
analyzer objects and an optional `cal_params` dict.

The process can be streamlined with a TOML configuration file (see the
`config` module). First create the ROI from ImageJ (or manually via the
`roi` module), then write a config that points to the calibration files:

```toml
# config.toml
[base]
roi = "line.roi"

[calibration]
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]

# calibration parameters are domain-specific and optional
[calibration.parameters]
sigma = 10

[calibration.result]
# written by config.calibrate(update=True)
pixel_per_ev = 16.0
peak_shift = 0.5
```

For example, to calibrate the SEES data:

```python
from pyleem.analysis.sees import SEESConfig

config = SEESConfig("config.toml")

# Run calibration and persist the result to [calibration.result]
cal_result = config.calibrate(update=True)
pixel_per_ev = cal_result["pixel_per_ev"]
peak_shift = cal_result["peak_shift"]
```

On subsequent runs, skip re-fitting and 
directly read from the [calibration.result] section.

```python
# read from [calibration.result] section
cal_result = config.read_section("calibration.result")

pixel_per_ev = cal_result["pixel_per_ev"]
peak_shift = cal_result["peak_shift"]
```

The calibration can also be done manually, see domain specific analysis
module for detailed implementation.

## Analysis

The domain-specific analyzer and analyzer group classes are used to perform the analysis.

### Single-file analysis

```python
from pyleem.analysis.sees import SEESAnalyzer
import matplotlib.pyplot as plt

analyzer = SEESAnalyzer("data_0eV.dat", roi, pixel_per_ev, peak_shift, sigma=10)
print(analyzer.potential)  # eV

fig, ax = plt.subplots()
analyzer.plot(ax, show_fit=True)
plt.show()
```

### Batch and time-series analysis

```python
from pyleem.analysis.sees import SEESGroup
import glob

paths = sorted(glob.glob("sample/*.dat"))
group = SEESGroup(paths, roi, pixel_per_ev, peak_shift, sigma=10)

potentials = group.get_attrs("potential")
time_intervals = group.get_time_intervals()
```
