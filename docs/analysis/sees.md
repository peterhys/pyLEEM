# SEES Analysis

Secondary Electron Energy Spectroscopy (SEES) analysis requires calibration
parameters `pixel_per_ev` and `peak_shift`. The calibration analyzer needs to
run first to obtain the calibration parameters. The base class `SEESBase`
provides the basic Gaussian smoothing of the profile through the parameter
`sigma`.

{py:func}`~pyleem.analysis.sees.SEES_onset` finds the steepest profile rise
and extrapolates the onset position in pixel coordinates.

{py:class}`~pyleem.analysis.sees.SEESCalibration` derives `pixel_per_ev` and
`peak_shift` from a stack of readers with `"Start Voltage"` metadata.

{py:class}`~pyleem.analysis.sees.SEESAnalyzer` analyzes SEES profiles with the
calibrated parameters. It converts profile pixels to kinetic energy, returns
the surface potential, and can plot the profile with an optional onset fit
overlay.

## Example

```python
from pyleem.analysis.sees import SEESAnalyzer, SEESCalibration
from pyleem.reader import UViewReader, read_files
from pyleem.roi import LineROI

readers = read_files(
    ["sees_0.dat", "sees_1.dat", "sees_2.dat"],
    reader_cls=UViewReader,
)
roi = LineROI(src=(0, 0), dst=(0, 127), linewidth=1)

calibration = SEESCalibration(readers, roi=roi)
cal_result = calibration.analyze(sigma=0)
pixel_per_ev = cal_result["pixel_per_ev"]
peak_shift = cal_result["peak_shift"]

analyzer = SEESAnalyzer(
    [readers[0]],
    roi=roi,
    pixel_per_ev=pixel_per_ev,
    peak_shift=peak_shift,
    sigma=10,
)
result = analyzer.analyze_profile(index=0)
surface_potential = result["surface_potential"]

ax = analyzer.plot_profile(0, show_fit=True)
```
