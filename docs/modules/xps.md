# `pyleem.xps`

X-ray Photoelectron Spectroscopy (XPS) analysis.

{py:class}`~pyleem.xps.XPSAnalyzer`
converts the pixel axis to a binding energy scale using the incident photon
energy and the ROI calibration. Basic peak estimation is provided for rough peak detection.
Basic peak fitting uses a Shirley background calculation and a composite pseudo-Voigt model
via `lmfit`.

{py:class}`~pyleem.xps.XPSGroup` processes multiple spectra together and can calibrate
`pixel_per_ev` and `peak_shift` from scans acquired at known start voltages. The peak
shift is calculated by comparing the fitted peak position to a reference peak.

## Example

```python
from pyleem.calibrate import calibrate_profile_config
from pyleem.xps import XPSAnalyzer, XPSGroup
import glob
import matplotlib.pyplot as plt

# XPS calibration
roi = calibrate_profile_config("config.toml", XPSGroup)

# XPSAnalyzer
analyzer = XPSAnalyzer("data.dat", roi, incident_voltage=400)

# Fit with two peaks; baseline = (left_bg, right_bg) intensities
result, bg = analyzer.fit(num_peaks=2, baseline=(200, 80))

fig, axes = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
analyzer.plot_fit(axes, result, bg)
plt.tight_layout()
plt.show()

# Access fit parameters
for name, param in result.params.items():
    print(f"{name}: {param.value:.3f}")

# XPSGroup
paths = sorted(glob.glob("sample/*.dat"))
group = XPSGroup(paths, roi, incident_voltage=400)
```

```{eval-rst}
.. automodule:: pyleem.xps
   :members:
   :show-inheritance:
```
