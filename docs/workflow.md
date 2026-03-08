# Workflow

The workflow of pyLEEM analysis consists of two parts: calibration and analysis.

## Calibration

For profile analysis (SEES, XPS, etc.), the pixel per eV and peak shift values
need to be calibrated, and typically done by shifting the spectrum under different start
voltages. The calibration process can be done by using the `calibrate` module (see
the `calibrate` module for more details). The process
can be streamlined by creating a configuration file to specify the data files
and region of interest (ROI) files. Subsequent runs can directly extract the
calibration results from the configuration file.

To start first create the roi file from ImageJ. (Manual ROI creation is also supported
through the `roi` module.) The configuration file is a TOML file that points to
the data files, roi file and the calibration parameters.

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

For example, to calibrate the SEES data, and obtain the calibrated roi:

```python
from pyleem.calibrate import calibrate_profile_config
from pyleem.sees import SEESGroup

roi = calibrate_profile_config("config.toml", SEESGroup, reset=True, plot=True)
```

To only extract the calibration results without re-fitting, run:

```python
roi = calibrate_profile_config("config.toml", SEESGroup, reset=False)
```

## Analysis

The domain specific `Analyzer` and `AnalyzerGroup` classes are used to perform the analysis.

### Single-file analysis

```python
from pyleem.sees import SEESAnalyzer
import matplotlib.pyplot as plt

analyzer = SEESAnalyzer("data_0eV.dat", roi, sigma=10)
print(analyzer.surface_potential)  # eV

fig, ax = plt.subplots()
analyzer.plot(ax, show_fit=True)
plt.show()
```

### Batch and time-series analysis

```python
from pyleem.sees import SEESGroup
import glob

paths = sorted(glob.glob("sample/*.dat"))
group = SEESGroup(paths, roi, sigma=10)

potentials = group.get_attrs("surface_potential")
time_intervals = group.get_time_intervals()
```
