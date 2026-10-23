# LEEDER Analysis

LEED Ewald radius analysis (LEEDER) requires the pattern radius
to energy conversion parabola parameters. The calibration analyzer needs to run
on standard sample to obtain the calibration parameters.

We can obtain the scattering energy and intensity from the pattern. The
LEEDERAnalyzer can obtain the stack information from the sample measurements. The
analyzer also profile image processing method and radius extraction method.

{py:class}`~pyleem.analysis.leeder.LEEDERCalibration` derives the calibration
parameters from a reader stack with `"Start Voltage"` metadata. Its
`analyze()` method measures the LEEDER radius for each image, fits voltage as a
parabola of radius, and returns the fitted values under `"parabola_params"`.

{py:class}`~pyleem.analysis.leeder.LEEDERAnalyzer` uses the calibrated parabola
parameters to measure the disk center, disk radius, and electron energy for
each image in the stack. It can annotate images with the detected disk and plot
electron energy against the reader time intervals.

## Example

```python
from pyleem.analysis.leeder import LEEDERAnalyzer, LEEDERCalibration
from pyleem.reader import UViewReader, read_files

readers = read_files(
    ["leeder_0.dat", "leeder_1.dat", "leeder_2.dat"],
    reader_cls=UViewReader,
)

calibration = LEEDERCalibration(readers)
cal_result = calibration.analyze(window=None)
parabola_params = cal_result["parabola_params"]

analyzer = LEEDERAnalyzer(readers, parabola_params=parabola_params)

radius = analyzer.radii_array[0]
energy = analyzer.energy_array[0]

# plot the image with the radius and energy annotated
ax = analyzer.plot_image(index=0, annotate=True)

# plot the energy vs. time
ax = analyzer.plot_energy()
```
