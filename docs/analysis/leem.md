# LEEM Analysis

Low Energy Electron Microscopy (LEEM) I-V analysis measures surface dependent
electron reflectivity versus electron energy. The process is similar to XAS, but
the electron energy ("Start Voltage") is varied instead of the X-ray energy.
The start voltage metadata is stored by default in the raw file.

## Example

```python
from pyleem.analysis.leem import LEEMAnalyzer
from pyleem.reader import UViewReader, read_files
from pyleem.roi import RectROI

readers = read_files(
    ["xas_0.dat", "xas_1.dat", "xas_2.dat"],
    reader_cls=UViewReader
)
roi = RectROI(top=20, left=30, bottom=80, right=90)

analyzer = LEEMAnalyzer(readers, roi=roi)
analyzer.correct_drift(sigma=3, crop_size=128)
intensities = analyzer.get_intensities()

ax = analyzer.plot_intensity()
```
