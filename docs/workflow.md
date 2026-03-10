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
`calibrate` module).  First create the ROI from ImageJ (or manually via the
`roi` module), then write a config that points to the calibration files:

```toml
# config.toml
[base]
paths = ["data_0eV.dat", "data_100eV.dat", "data_200eV.dat"]
roi   = "line.roi"

# calibration parameters are optional and
# will be computed automatically if omitted
[calibration]
pixel_per_ev = 166.0
peak_shift   = 3.75
```

For example, to calibrate the SEES data:

```python
from pyleem.calibrate import read_config, read_config_result, write_config_result
from pyleem.analysis import ProfileAnalyzer
from pyleem.sees import calibrate_sees

# Read paths and ROI from the config
base_params, cal_params = read_config("config.toml")
roi   = base_params["roi"]
paths = base_params["paths"]

cal_result = calibrate_sees([ProfileAnalyzer(path, roi) for path in paths], cal_params)
write_config_result("config.toml", cal_result)
pixel_per_ev = cal_result["pixel_per_ev"]
peak_shift   = cal_result["peak_shift"]
```

On subsequent runs, skip re-fitting and reload the saved result:

```python
result = read_config_result("config.toml")
pixel_per_ev = result["pixel_per_ev"]
peak_shift   = result["peak_shift"]
```

## Analysis

The domain-specific analyzer and analyzer group classes are used to perform the analysis.

### Single-file analysis

```python
from pyleem.sees import SEESAnalyzer
import matplotlib.pyplot as plt

analyzer = SEESAnalyzer("data_0eV.dat", roi, pixel_per_ev, peak_shift, sigma=10)
print(analyzer.potential)  # eV

fig, ax = plt.subplots()
analyzer.plot(ax, show_fit=True)
plt.show()
```

### Batch and time-series analysis

```python
from pyleem.sees import SEESGroup
import glob

paths = sorted(glob.glob("sample/*.dat"))
group = SEESGroup(paths, roi, pixel_per_ev, peak_shift, sigma=10)

potentials = group.get_attrs("potential")
time_intervals = group.get_time_intervals()
```
