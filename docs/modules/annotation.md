# `pyleem.annotation`

Annotation mixins add plotting overlays to analyzer image plots. They are
designed as class mixins that compose with `Analyzer` subclasses through
`annotate_image()`. The method can be used by itself as well.

## Metadata Text

Use `MetadataTextMixin` to place selected reader metadata on image axes.

```{eval-rst}
.. automodule:: pyleem.annotation.metatext
   :members:
   :show-inheritance:
```

## Scale Bar

Use `ScaleBarMixin` to draw a FOV-calibrated scale bar on image axes.

```{eval-rst}
.. automodule:: pyleem.annotation.scalebar
   :members:
   :show-inheritance:
```

## ROI Drawing

Use `ROIAnnotationMixin` to draw supported ROI objects on image
axes.

```{eval-rst}
.. automodule:: pyleem.annotation.drawroi
   :members:
   :show-inheritance:
```
