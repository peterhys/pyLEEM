# `pyleem.analysis.xas`

X-ray Absorption Spectroscopy (XAS) analysis measures ROI intensity across an
image stack. Drift correction is available as an explicit step before intensity
extraction. If `draft_correct` method is not called, the raw image is used
for analysis.

## Example

```python
from pyleem.analysis.xas import XASAnalyzer
from pyleem.reader import UViewReader, read_files
from pyleem.roi import RectROI

readers = read_files(
    ["xas_0.dat", "xas_1.dat", "xas_2.dat"],
    reader_cls=UViewReader,
    metadata_list=[
        {"Incident Energy": (280.0, "eV")},
        {"Incident Energy": (281.0, "eV")},
        {"Incident Energy": (282.0, "eV")},
    ],
)
roi = RectROI(top=20, left=30, bottom=80, right=90)

analyzer = XASAnalyzer(readers, roi=roi)
corrected_images, shifts = analyzer.drift_correct(sigma=3, crop_size=128)
intensities = analyzer.get_intensities()

ax = analyzer.plot_intensity()
```

```{eval-rst}
.. automodule:: pyleem.analysis.xas
   :members:
   :show-inheritance:
```
