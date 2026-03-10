# `pyleem.xps`

X-ray Photoelectron Spectroscopy (XPS) analysis.

{py:class}`~pyleem.xps.XPSAnalyzer` converts the pixel axis to a binding energy
scale using the incident photon energy and the ROI calibration. Basic peak fitting uses a
Shirley background subtraction and a pseudo-Voigt model via `lmfit`.

{py:class}`~pyleem.xps.XPSGroup` processes multiple spectra together.
{py:func}`~pyleem.xps.calibrate_xps` derives `pixel_per_ev` and `peak_shift` by
fitting peaks in pixel space across scans acquired at known start voltages. Pass
`incident_voltage` and optionally `ref_index` / `ref_value` in `cal_params` to
anchor the energy scale to a known reference peak.

## Example

```python
from pyleem.xps import XPSAnalyzer, XPSGroup, calibrate_xps
from pyleem.analysis import ProfileAnalyzer
from pyleem.roi import LineROI
import glob
import matplotlib.pyplot as plt

# XPS calibration
# from config file
base_params, cal_params = read_config("config.toml")
roi = base_params["roi"]
paths = base_params["paths"]

# manually set the paths
roi = LineROI(src=(256, 10), dst=(256, 500), linewidth=20)
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
cal_params = {
    "baselines": [(200, 80), (200, 80), (200, 80)],
    "num_peaks": 1,
    "ref_index": 0,
    "ref_value": 84.0,   # Au 4f7/2 reference in eV
    "incident_voltage": 400,
}
cal_result = calibrate_xps([ProfileAnalyzer(path, roi) for path in paths], cal_params)
pixel_per_ev, peak_shift = cal_result["pixel_per_ev"], cal_result["peak_shift"]

# XPSAnalyzer
analyzer = XPSAnalyzer("data.dat", roi, pixel_per_ev, peak_shift, incident_voltage=400)

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
group = XPSGroup(paths, roi, pixel_per_ev, peak_shift, incident_voltage=400)
```

```{eval-rst}
.. automodule:: pyleem.xps
   :members:
   :show-inheritance:
```
