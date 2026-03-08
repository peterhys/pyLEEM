# `pyleem.reader`

Reader interfaces for loading raw UView data and extracting image profiles.

{py:class}`~pyleem.reader.Reader` is an abstract base class that defines the interface all readers must implement.
{py:class}`~pyleem.reader.UViewReader` is the concrete implementation for Elmitec UView `.dat` files.

## Example

```python
from pyleem.reader import UViewReader

reader = UViewReader("data.dat")

# Access parsed metadata
print(reader.metadata["Start Voltage"])  # (4.5, 'V')
print(reader.metadata["ImageHeight"])  # (1024, None)

# Load the raw image
image = reader.read_image()  # ndarray, shape (height, width), uint16

# Extract a line profile using a LineROI
from pyleem.roi import LineROI

roi = LineROI(src=(256, 0), dst=(256, 511), linewidth=10)
profile = reader.read_profile(roi)  # 1D ndarray

```

## Subclassing `Reader`

Implement a custom reader to support other file formats.  All four abstract
methods must be provided.

```python
from pyleem.reader import Reader
import numpy as np


class MyReader(Reader):
    def __init__(self, path):
        self.path = path
        # parse your format here

    @property
    def metadata(self):
        # Return a dict of {key: (value, unit)} pairs.
        return {"Start Voltage": (5.0, "V"), ...}

    def read_image(self):
        # Return a 2D ndarray (height, width).
        return np.zeros((512, 512), dtype=np.uint16)

    def read_profile(self, roi):
        import skimage

        return skimage.measure.profile_line(self.read_image(), **roi.to_dict())

    def __lt__(self, other):
        return self.path < other.path
```

Pass your reader by subclassing `Analyzer` directly (see `pyleem.analysis`).

```{eval-rst}
.. automodule:: pyleem.reader
   :members:
   :show-inheritance:
```
