# XAS Analysis

X-ray Absorption Spectroscopy (XAS) analysis measures ROI intensity across an
image stack. Drift correction is available as an explicit step before intensity
extraction. If `correct_drift` method is not called, the raw image is used for
analysis. The shift information can be separately accessed from the method
`calculate_drift()`.

## Example

```python
from pyleem.analysis.xas import XASAnalyzer
from pyleem.reader import UViewReader, read_files
from pyleem.roi import RectROI

readers = read_files(
    ["xas_0.dat", "xas_1.dat", "xas_2.dat"],
    reader_cls=UViewReader,
    metadata_list=[
        {"Beam Energy": (280.0, "eV")},
        {"Beam Energy": (281.0, "eV")},
        {"Beam Energy": (282.0, "eV")},
    ],
)
roi = RectROI(top=20, left=30, bottom=80, right=90)

analyzer = XASAnalyzer(readers, roi=roi)
analyzer.correct_drift(sigma=3, crop_size=128)
intensities = analyzer.get_intensities()

ax = analyzer.plot_intensity()
```
