# `pyleem.reader`

Reader interfaces for loading raw LEEM data and extracting image profiles.

{py:class}`~pyleem.reader.Reader` defines the reader API.
{py:class}`~pyleem.reader.UViewReader` parses UView `.dat` files.
{py:func}`~pyleem.reader.read_files` reads a list of files and returns a list of readers.

For large data stacks, it is recommended to parse the data in groups to obtain the time
interval metadata ("TimeInterval" key). This is calculated based on the order of the timestamps in the metadata.
Additional metadata can be added to the reader. Reader also allows quick access to the raw image data.


## Example

```python
from pyleem.reader import UViewReader, read_files

readers = read_files(
    ["data_0.dat", "data_1.dat", "data_2.dat"],
    reader_cls=UViewReader,
    metadata_list=[
        {"Voltage": (4, "V")},
        {"Voltage": (4.5, "V")},
        {"Voltage": (5, "V")},
    ],
)

# Access parsed metadata
print(readers[0].metadata["Voltage"])  # (4, 'V')
print(readers[0].metadata["TimeInterval"])  # (0.0, 's')

# Load the raw image
# ndarray, shape (height, width), uint16
image = readers[0].image

# Extract a line profile using a LineROI
from pyleem.roi import LineROI

roi = LineROI(src=(256, 0), dst=(256, 511), linewidth=10)
profile = roi.measure(image).profile
```

## Subclassing `Reader`

For different data formats, the `Reader` class can be subclassed. The
subclass should implement the `__lt__` method to enable sorting, the method
`metadata` and `image` properties are required implementation. A reader
is not required to parse the file path.

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
        return {
            "Start Voltage": (5.0, "V"),
            # ...
        }

    @property
    def image(self):
        # Return the image data as a numpy array.
        return ...

    def __lt__(self, other):
        # Sorting by file path.
        return self.path < other.path
```

```{eval-rst}
.. automodule:: pyleem.reader
   :members:
   :show-inheritance:
```
