# pyLEEM

[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/peterhys/PyLEEM/actions/workflows/tests.yml/badge.svg)](https://github.com/peterhys/PyLEEM/actions/workflows/tests.yml)

A Python toolkit for Low Energy Electron Microscopy (LEEM) data analysis. pyLEEM
provides readers, ROI tools, domain-specific analyzers, calibration analyzers,
and workflow recording for reproducible runs.

## Installation

```bash
pip install pyleem
```

## Development installation

Clone the development branch:

```bash
git clone --branch develop https://github.com/peterhys/PyLEEM.git
cd PyLEEM
pip install -e .
```


## Examples

Here we show some examples of its capabilities.

### XPS: binding energy calibration, peak fitting and stitching

```python
from pyleem.analysis.xps import XPSAnalyzer, XPSCalibration
from pyleem.reader import UViewReader, read_files
from pyleem.roi import LineROI

readers = read_files(
    ["xps_0.dat", "xps_1.dat", "xps_2.dat"],
    UViewReader,
    metadata_list=[
        {"Incident Voltage": (400, "eV")},
        {"Incident Voltage": (400, "eV")},
        {"Incident Voltage": (400, "eV")},
    ],
)

roi = LineROI(src=[0, 0], dst=[0, 127], linewidth=1)

calibration = XPSCalibration(readers, roi)
cal_result = calibration.analyze(
    baselines=[(197, 100)] * 3,
    num_peaks=1,
    ref_index=0,
    ref_value=285.0,
)

analyzer = XPSAnalyzer(
    readers,
    roi,
    cal_result["pixel_per_ev"],
    cal_result["peak_shift"],
)

fit_result, background = analyzer.fit(0, num_peaks=1, baseline=(200, 100))

# Automatically stitch profiles into a single spectrum
stitched_energy, stitched_profile = analyzer.stitch_profiles([0, 1, 2])
```


### SEES: surface potential from an onset shift

```python
from pyleem.analysis.sees import SEESAnalyzer, SEESCalibration
from pyleem.reader import UViewReader, read_files
from pyleem.roi import LineROI

readers = read_files(["sees_0.dat", "sees_1.dat", "sees_2.dat"], UViewReader)
roi = LineROI(src=[0, 0], dst=[0, 127], linewidth=1)

calibration = SEESCalibration(readers, roi)
cal_result = calibration.analyze(sigma=0)

analyzer = SEESAnalyzer(
    [readers[0]],
    roi,
    cal_result["pixel_per_ev"],
    cal_result["peak_shift"],
    sigma=10,
)

result = analyzer.analyze_profile(0)
print(result["surface_potential"])
```

### Workflow: run and save analysis results

Workflow file can be partially filled as a template for distribution.

`sees_calibration.toml`

```toml
[session]
reader = "UViewReader"
roi = "LineROI"
analyzer = "SEESCalibration"

[reader]
paths = ["sees_0.dat", "sees_1.dat", "sees_2.dat"]

[roi]
src = [0, 0]
dst = [0, 127]
linewidth = 1

[task]
sigma = 0
```

```python
import pyleem.analysis.sees  # registers SEESCalibration class
from pyleem.config import load_config
from pyleem.workflow import Workflow

config = load_config("sees_calibration.toml")
workflow = Workflow(config)
result = workflow.run()
workflow.save("sees_calibration_run.toml")
```



## Documentation

- [Documentation](https://peterhys.github.io/pyLEEM/)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)

## License

pyLEEM is distributed under the BSD 3-Clause License, see [LICENSE](LICENSE).

Additional Brookhaven National Laboratory, U.S. Department of Energy, and U.S.
Government rights notices are provided in [NOTICE](NOTICE).

Third-party dependencies are distributed under their own licenses, see
[THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES).
