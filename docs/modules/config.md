# `pyleem.config`

The module provides the `Config` base class and domain-specific subclasses for
reading and writing TOML configuration files. Configuration files store data
paths, an ROI file, domain-specific calibration parameters, and a
`[calibration.result]` section that caches the final calibration values.

Domain-specific subclasses (`SEESConfig`, `XPSConfig`, `DESPConfig`) implement
`calibrate_results` to drive the appropriate calibration routine from the
config file. Detailed config class and toml file format are provided in the domain
specific modules. For calibration, the subclass should implement the `calibrate_results`
method.

## Config file format

```toml
# config.toml
[base]
roi = "line.roi"

[calibration]
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]

[calibration.parameters]
num_peaks        = 1
baselines        = [[197, 100], [197, 100], [197, 100]]
ref_index        = 0
ref_value        = 285.0
incident_voltage = 400

[calibration.result]
pixel_per_ev = 165.8
peak_shift   = 3.72
```

## Example

```python
from pyleem.config import Config

config = Config("config.toml")
roi = config.get_roi()

# path based on the base directory
paths = config.get_paths(["a.dat", "b.dat"])
paths = config.get_patterned_paths("*.dat")

# read write sections
# show complete configuration
full_config = config.read_section()
# show specific section
section = config.read_section("calibration.parameters")
config.write_section("calibration.result", {"pixel_per_ev": 16.0, "peak_shift": 0.5})
```

```{eval-rst}
.. automodule:: pyleem.config
   :members:
   :show-inheritance:
```
