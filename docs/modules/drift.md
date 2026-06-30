# `pyleem.operation.drift`

Drift correction aligns an image stack by estimating pairwise shifts, reducing
them to absolute correction shifts, and applying those shifts to the original
images. 

The drift-correction workflow adapts the pairwise image-registration approach
described by de Jong et al., *Ultramicroscopy* 213, 112913 (2020),
DOI: [10.1016/j.ultramic.2019.112913](https://doi.org/10.1016/j.ultramic.2019.112913).

If you use the drift-correction workflow in published work, please cite:

  de Jong et al., Ultramicroscopy 213, 112913 (2020),
  DOI: 10.1016/j.ultramic.2019.112913.

```{eval-rst}
.. automodule:: pyleem.operation.drift
   :members:
```
