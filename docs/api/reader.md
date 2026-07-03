# Reader API

The `Reader` class can be subclassed for different data formats.

## Subclassing `Reader`

For different data formats, the `Reader` class can be subclassed. The subclass
should implement the `__lt__` method to enable sorting, the method `metadata`
and `image` properties are required implementation. A reader is not required to
parse the file path.

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
