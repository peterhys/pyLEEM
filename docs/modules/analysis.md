# `pyleem.analysis`

Core analyzer classes for LEEM images, line profiles, and grouped workflows.

This module contains the base classes used across all domain-specific analyzers:

- {py:class}`~pyleem.analysis.Analyzer` — wraps a single `.dat` file and exposes its image and metadata.
- {py:class}`~pyleem.analysis.ProfileAnalyzer` — extends `Analyzer` with line-profile extraction.
  Subclasses set `_abscissa`, `_abscissa_label`, `_ordinate`, `_ordinate_label` directly in `__init__`
  to define their axis representation. The attributes are property acessed by `abscissa`, `abscissa_label`,
  `ordinate`, and `ordinate_label`.
- {py:class}`~pyleem.analysis.StitchAnalyzer` — merges multiple `ProfileAnalyzer` instances that share
  overlapping abscissa ranges into a single continuous spectrum.
- {py:class}`~pyleem.analysis.AnalyzerGroup` — manages a list of analyzer instances for batch and
  time-series workflows.

## Example

```python
from pyleem.analysis import Analyzer, ProfileAnalyzer, AnalyzerGroup
from pyleem.roi import LineROI
import matplotlib.pyplot as plt

# metadata output
analyzer = Analyzer("data.dat")
print(analyzer.metadata["Start Voltage"])

# plot the raw image
analyzer.plot_image()

# line profile non domain specific
roi = LineROI(src=(256, 10), dst=(256, 500), linewidth=20)
analyzer = ProfileAnalyzer("data.dat", roi)
analyzer.plot_profile()

# batch analysis and time intervals
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
analyzers = [Analyzer(path) for path in paths]
group = AnalyzerGroup(analyzers)
time_intervals = group.get_time_intervals()
```

```{eval-rst}
.. automodule:: pyleem.analysis
   :members:
   :show-inheritance:
```
