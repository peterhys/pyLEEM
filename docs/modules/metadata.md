# `pyleem.metadata`

Binary metadata parsing for UView LEEM `.dat` files.

The module parses the 16384-byte header block that precedes the image data in
every UView `.dat` file.

All metadata values are returned as `(value, unit)` tuples.  Common keys
include `"Start Voltage"`, `"ImageHeight"`, `"ImageWidth"`, `"TimeStamp"`, and
`"Camera Exposure"`.


```{eval-rst}
.. automodule:: pyleem.metadata
   :members:
   :show-inheritance:
```
