# `pyleem.calibrate`

The module provides helpers for reading and writing TOML configuration files that
store data paths, an ROI file, optional calibration parameters, and a `[result]`
section with the final `pixel_per_ev` and `peak_shift` values.

## Config file format

```toml
# config.toml
[base]
paths = ["data_0eV.dat", "data_100eV.dat", "data_200eV.dat"]
roi   = "line.roi"

[calibration]
# Passed directly to calibrate_sees / calibrate_xps as cal_params.
# For XPS: baselines, num_peaks, incident_voltage (and optionally ref_index / ref_value).
num_peaks  = 1
baselines  = [[197, 100], [197, 100], [197, 100]]
ref_index  = 0
ref_value  = 285.0
incident_voltage = 400

[result]
# Written by write_config_result; read back by read_config_result.
pixel_per_ev = 165.8
peak_shift   = 3.72
```

## Example

```python
from pyleem.calibrate import read_config, read_config_result, write_config_result
from pyleem.sees import SEESGroup, calibrate_sees

# Read paths, ROI, and calibration parameters from the config
base_params, cal_params = read_config("config.toml")
roi   = base_params["roi"]
paths = base_params["paths"]

write_config_result("config.toml", {"pixel_per_ev": 16.0, "peak_shift": 0.5})
result = read_config_result("config.toml")
```


```{eval-rst}
.. automodule:: pyleem.calibrate
   :members:
   :show-inheritance:
```
