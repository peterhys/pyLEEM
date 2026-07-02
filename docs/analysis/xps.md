# XPS Analysis

X-ray Photoelectron Spectroscopy (XPS) analysis requires calibration
parameters `pixel_per_ev` and `peak_shift`. The calibration analyzer needs to
run first to obtain the calibration parameters. The base class `SpectraBase`
provides the basic stitching profile analysis.

{py:class}`~pyleem.analysis.xps.XPSCalibration` derives `pixel_per_ev` and
`peak_shift` from a stack of readers with `"Start Voltage"` and
`"Incident Voltage"` metadata. The calibration `analyze()` method uses XPS
fitting methods that require baseline intensities, total number of peaks,
reference peak index and energy value.

{py:class}`~pyleem.analysis.xps.XPSAnalyzer` converts the pixel axis to
binding energy, fits profiles with Shirley background subtraction and
pseudo-Voigt peaks, plots fit results, and can stitch profiles through the
shared spectra base class. Automatic peak fitting detects peaks on the
background-subtracted signal. Manual fitting can be done by provding
a dictionary of peak constraints. The constraints follows the `lmfit` format.

The LEEM spectra analyzer has limited energy range, large energy range spectra
requires to be stitched together. The stitching method takes a list of indices
and determines the overlapped regions, and outputs a combined profile.

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

## Peak Fitting

The peak fitting takes the profile and abscissa as input. The fit result
is a dictionary of the fit, background and other fitting parameters.

### Manual Peak Fitting

For analyzer, the manual peak fitting can be done by passing a dictionary
of peak constraints. The constraints follows the `lmfit` format.

```python
peak_constraints = {
    "peak1": {
        "center": {"value": 531.0, "min": 530.5, "max": 531.5},
        "sigma": {"value": 0.4, "min": 0.05, "max": 1.2},
    "peak2": ... 
}
```

The `fit_xps` function can be used to fit spectrum directly without the analyzer.
The function is useful if more detailed control needed. For example, if we
want to fit a spectrum with a specific range, we can use the `fit_range` argument.

```python
from pyleem.analysis.xps import fit_xps

peak_constraints = {
    "peak1": {
        "center": {"value": 531.0, "min": 530.5, "max": 531.5},
        "sigma": {"value": 0.4, "min": 0.05, "max": 1.2},
        "amplitude": {"value": 800, "min": 0},
        "fraction": {"value": 0.5, "min": 0, "max": 1},
    },
    "peak2": {
        "center": {"value": 529.2, "min": 528.6, "max": 529.8},
        "sigma": {"value": 0.5, "min": 0.05, "max": 1.2},
        "amplitude": {"value": 200, "min": 0},
        "fraction": {"value": 0.5, "min": 0, "max": 1},
    },
}

fit_result = fit_xps(
    stitched_profile,
    stitched_energy,
    baseline=(120, 80), # optional
    peak_constraints=peak_constraints, # optional
    fit_range=(528.1, 532.8), # optional
)
```

### Automatic Peak Fitting

For automatic fitting, pass `num_peaks` instead of `peak_constraints`. Use
`peak_prominence` and `smooth_sigma` to make peak detection less
sensitive to noise or single-point stitch spikes.

```python
fit_result = fit_xps(
    stitched_profile,
    stitched_energy,
    num_peaks=2,
    peak_prominence=0.1,
    smooth_sigma=2,
)
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
