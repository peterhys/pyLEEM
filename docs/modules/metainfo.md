# `pyleem.metainfo`

Constants and lookup tables used while decoding LEEM metadata blocks.

This module is an internal reference used by {py:mod}`pyleem.metadata`.  It defines
the binary layout of the UView file and image headers, unit codes, and tagged
data formats.  You do not need to import it directly for analysis.

| Constant | Description |
|---|---|
| `FILE_CONTENTS` | List of `(name, struct_format)` for the file header. |
| `IMG_CONTENTS` | List of `(name, struct_format)` for the image header. |
| `UNIT_CODES` | Mapping of integer codes to unit strings (e.g. `{1: "V", 2: "mA"}`). |
| `DATA_TAGS` | Mapping of tag integers to lists of `(name, unit, struct_format)` tuples for special LEEM-specific data fields. |


```{eval-rst}
.. automodule:: pyleem.metainfo
   :members:
   :show-inheritance:
```
