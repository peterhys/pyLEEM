# Reader: Reading Data

Reader interfaces load raw LEEM data and expose image and metadata access.

{py:class}`~pyleem.reader.Reader` defines the reader API.
{py:class}`~pyleem.reader.UViewReader` parses UView `.dat` files.
{py:func}`~pyleem.reader.read_files` reads a list of files and returns a list
of readers.

For large data stacks, it is recommended to parse the data in groups to obtain
the time interval metadata ("TimeInterval" key). This is calculated based on
the order of the timestamps in the metadata. Additional metadata can be added
to the reader. Reader also allows quick access to the raw image data.


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

## API and Reference

- {doc}`../api/reader`: For custom reader implementations.
- {doc}`../ref/reader_ref`: For full module details.
