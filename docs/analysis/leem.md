# LEEM Analysis

Low Energy Electron Microscopy (LEEM) I-V analysis measures surface-dependent
electron reflectivity versus electron energy. {py:class}`~pyleem.analysis.leem.LEEMIVAnalyzer`
is the analyzer for LEEM I-V analysis. Drift correction is available as an explicit step 
before intensity extraction. If the `correct_drift` method is not called, the raw image is 
used for analysis. The shift information can be separately accessed from the method
`calculate_drift()`. The analysis measures the intensity over the image stack versus electron 
energy ("Start Voltage"). The "Start Voltage" metadata is stored by default in the raw file.
The analyzer uses the {py:class}`~pyleem.analysis.fullfield.FullFieldBase` base class for 
drift correction logics.

## Example

```python
from pyleem.analysis.leem import LEEMIVAnalyzer
from pyleem.reader import UViewReader, read_files
from pyleem.roi import RectROI

readers = read_files(
    ["xas_0.dat", "xas_1.dat", "xas_2.dat"],
    reader_cls=UViewReader
)
roi = RectROI(top=20, left=30, bottom=80, right=90)

analyzer = LEEMIVAnalyzer(readers, roi=roi)
analyzer.correct_drift(sigma=3, crop_size=128)
intensities = analyzer.get_intensities()

ax = analyzer.plot_intensity()
```
