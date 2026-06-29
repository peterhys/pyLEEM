# `pyleem.config` and `pyleem.workflow`

The config and workflow modules work together to build, run and save the analysis.
The config object is a state object that stores the input parameters and output results
from the analyzer class. For analyzer to be properly interact with the workflow, the
input and output parameters should be picklable. The config content follows the TOML format,
with sections named `session`, `reader`, `roi`, `analyzer`, `task`, and `result`. Partial
config content are allowed and can be updated, which allows configuration templates.
The workflow object is a builder object that builds the readers, ROI, and analyzer objects
from the config object. The workflow object also runs the analyzer and saves the result
back to the config object.

## Config sections

### Session

In session section, the reader, roi, and analyzer classes are defined by name.
The classes are accessed through the respective registries.

| Name | Explanation |
| --- | --- |
| `version` | Records the PyLEEM version used to write the config file. |
| `reader` | Reader class name. |
| `roi` | ROI class name. |
| `analyzer` | Analyzer class name. |

### Reader

The reader section defines the reader class inputs. For large data stacks,
`path_pattern` can be used to access the data files through a glob pattern.
Only one of `paths` or `path_pattern` should be provided.

For added metadata, `metadata_list` can be used to add per-reader metadata entries.
For shared metadata, `metadata` can be used to add the same metadata entry to every reader.
When both are provided, the `metadata_list` overrides the `metadata`.

| Name | Explanation |
| --- | --- |
| `paths` | Lists the data files to read, resolved relative to the workflow root. |
| `path_pattern` | Glob pattern used to find data files when `paths` is not provided. |
| `metadata_list` | Adds per-reader metadata entries; these override shared metadata. |
| `metadata` | Adds the same metadata entry to every reader. |

### ROI

The roi section defines the ROI class inputs. The inputs can be a roi file or a manually defined ROI.

### Analyzer

The analyzer section passes settings to the analyzer constructor.

### Task

The task section passes parameters to `analyze()`.

## Example

We start with a calibration template file `xps_calibration_template.toml`.
Here we define the necessary general settings for the calibration:

1. necessary classes in the session.
2. a standardized ROI.
3. reference peaks for C1s.

```toml
[session]
version = "0.3.0"
reader = "UViewReader"
roi = "LineROI"
analyzer = "XPSCalibration"

[roi]
src = [0, 0]
dst = [0, 127]
linewidth = 10

[task]
num_peaks = 1
ref_index = 0
ref_value = 285.0
peak_prominence = 0.1
```

```python
from pyleem.analysis.xps import XPSCalibration
from pyleem.config import load_config, save_config
from pyleem.workflow import Workflow

config = load_config("xps_calibration_template.toml")

workflow = Workflow(
    config,
    root=".",
    reader={
        "paths": ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"],
        "metadata": {"Incident Voltage": [400, "eV"]},
    },
)

# Run and access the result directly
result = workflow.run(
    baselines=[[197, 100], [197, 100], [197, 100]], ref_value=285.0, peak_prominence=0.2
)

# get the updated config
config = workflow.config

# save the result
workflow.save("xps_calibration_result.toml")
```

The saved result file `xps_calibration_result.toml` is as follows, note
the added/updated input parameters and result values. For example, the
peak prominence is updated to 0.2.

```toml
[session]
version = "0.3.0"
reader = "UViewReader"
roi = "LineROI"
analyzer = "XPSCalibration"

[reader]
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
metadata = {"Incident Voltage" = [400, "eV"]}

[roi]
src = [0, 0]
dst = [0, 127]
linewidth = 10

[task]
num_peaks = 1
baselines = [[197, 100], [197, 100], [197, 100]]
ref_index = 0
ref_value = 285.0
peak_prominence = 0.2

[result]
pixel_per_ev = 165.8
peak_shift = 3.72
```

```{eval-rst}
.. automodule:: pyleem.config
   :members:
   :show-inheritance:
```
