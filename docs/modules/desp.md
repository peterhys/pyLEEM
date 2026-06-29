# `pyleem.analysis.desp`

Diffuse Elastic Scattering Pattern (DESP) analysis. The analysis requires
the pattern radius to energy conversion parabola parameters. The calibration analyzer
needs to run on standard sample to obtain the calibration parameters.

We can obtain the scattering energy and intensity from the pattern. The DESPAnalyzer
can obtain the stack information from the sample measurements. The analyzer also
profile image processing method and radius extraction method. 

{py:class}`~pyleem.analysis.desp.DESPCalibration` derives the calibration
parameters from a reader stack with `"Start Voltage"` metadata. Its
`analyze()` method measures the DESP radius for each image, fits voltage as a
parabola of radius, and returns the fitted values under `"parabola_params"`.

{py:class}`~pyleem.analysis.desp.DESPAnalyzer` uses the calibrated parabola
parameters to measure the disk center, disk radius, and electron energy for
each image in the stack. It can annotate images with the detected disk and plot
electron energy against the reader time intervals.

## Example

```python
from pyleem.analysis.desp import DESPAnalyzer, DESPCalibration
from pyleem.reader import UViewReader, read_files

readers = read_files(
    ["desp_0.dat", "desp_1.dat", "desp_2.dat"],
    reader_cls=UViewReader,
)

calibration = DESPCalibration(readers)
cal_result = calibration.analyze(window=None)
parabola_params = cal_result["parabola_params"]

analyzer = DESPAnalyzer(readers, parabola_params=parabola_params)

radius = analyzer.radii_array[0]
energy = analyzer.energy_array[0]

# plot the image with the radius and energy annotated
ax = analyzer.plot_image(index=0, annotate=True)

# plot the energy vs. time
ax = analyzer.plot_energy()
```

```{eval-rst}
.. automodule:: pyleem.analysis.desp
   :members:
   :show-inheritance:
```
