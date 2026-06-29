# `pyleem.analysis.xps`

X-ray Photoelectron Spectroscopy (XPS) analysis. The analysis requires
calibration parameters `pixel_per_ev` and `peak_shift`. The calibration analyzer
needs to run first to obtain the calibration parameters. The base class `SpectraBase`
provides the basic stitching profile analysis.

{py:class}`~pyleem.analysis.xps.XPSCalibration` derives `pixel_per_ev` and
`peak_shift` from a stack of readers with `"Start Voltage"` and
`"Incident Voltage"` metadata. The calibration `analyze()` method uses XPS fitting
methods that require baseline intensities, total number of peaks, reference peak
index and energy value.

{py:class}`~pyleem.analysis.xps.XPSAnalyzer` converts the pixel axis to binding
energy, fits profiles with Shirley background subtraction and pseudo-Voigt
peaks, plots fit results, and can stitch profiles through the shared spectra base class.

The LEEM spectra analyzer has limited energy range, large energy range spectra requires
to be stitched together. The stitching method takes a list of indices and determines
the overlapped regions, and outputs a combined profile.

## Example

```python
from pyleem.analysis.xps import XPSAnalyzer, XPSCalibration
from pyleem.reader import UViewReader, read_files
from pyleem.roi import LineROI

readers = read_files(
    ["xps_0.dat", "xps_1.dat", "xps_2.dat"],
    reader_cls=UViewReader,
    metadata_list=[
        {"Incident Voltage": (400, "eV")},
        {"Incident Voltage": (400, "eV")},
        {"Incident Voltage": (400, "eV")},
    ],
)
roi = LineROI(src=(0, 0), dst=(0, 127), linewidth=1)

calibration = XPSCalibration(readers, roi=roi)
cal_result = calibration.analyze(
    baselines=[(197, 100)] * len(readers),
    num_peaks=1,
    ref_index=0,
    ref_value=285.0,
)
pixel_per_ev = cal_result["pixel_per_ev"]
peak_shift = cal_result["peak_shift"]

analyzer = XPSAnalyzer(
    readers,
    roi=roi,
    pixel_per_ev=pixel_per_ev,
    peak_shift=peak_shift,
)

binding_energy = analyzer.get_binding_energy(0)
fit_result, background = analyzer.fit(0, num_peaks=1, baseline=(200, 100))
stitched_energy, stitched_profile = analyzer.stitch_profiles([0, 1, 2])

ax = analyzer.plot_profile(
    0,
    show_fit=True,
    num_peaks=1,
    baseline=(200, 100),
)
print(fit_result.best_values)
```

## Stitching Profiles

The `stitch_method` argument can be `"midpoint"`, `"start"`, or `"end"`.

```python
# Use the calibrated analyzer from the example above.
stitched_energy, stitched_profile = analyzer.stitch_profiles(
    indices=[0, 1, 2],
    stitch_method="midpoint",
)

ax.plot(stitched_energy, stitched_profile)
ax.set_xlabel("Binding Energy [eV]")
ax.set_ylabel("Intensity")
```

```{eval-rst}
.. automodule:: pyleem.analysis.xps
   :members:
   :show-inheritance:
```
