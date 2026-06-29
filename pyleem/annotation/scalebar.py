"""FOV-calibrated scale bar annotations for image analyzers."""


def scalebar_width(width_um, fov_um, image_width):
    """Return scale bar width in pixels."""

    return width_um * (image_width / fov_um)


class ScaleBarMixin:
    """Annotation class that adds a FOV-calibrated scale bar.

    Inherit from this class before the analyzer class, then call
    add_scalebar from the subclass annotate_image method.

    Example:
        class ScaleBarAnalyzer(ScaleBarMixin, Analyzer):

            def annotate_image(self, index, ax):
                ax = super().annotate_image(index, ax)
                return self.add_scalebar(index, ax, target_um=5)
    """

    def get_scalebar_parameter(self, index):
        """Return scale bar parameters for one image index."""

        fov_um = self.get_metadata("FOV", index)[0]
        image_height = self.get_metadata("ImageHeight", index)[0]
        image_width = self.get_metadata("ImageWidth", index)[0]
        return fov_um, image_height, image_width

    def add_scalebar(
        self,
        index,
        ax,
        target_um=5,
        bar_width=None,
        x_margin=20,
        y_margin=20,
        thickness=5,
        color="white",
        unit_label="um",
        **kwargs,
    ):
        """Add a FOV-calibrated scale bar to an image axes.

        The scale bar width can be specified. In this case, it skips
        the FOV calculation and directly uses the bar width pixels.
        In this case the target_um parameter is purely a label.

        """

        image_height = self.get_metadata("ImageHeight", index)[0]
        image_width = self.get_metadata("ImageWidth", index)[0]

        if bar_width is None:
            fov_um = self.get_metadata("FOV", index)[0]
            bar_width = scalebar_width(target_um, fov_um, image_width)

        x2 = image_width - x_margin
        x1 = x2 - bar_width
        y = image_height - y_margin

        ax.plot(
            [x1, x2], [y, y], color=color, linewidth=thickness, solid_capstyle="butt"
        )

        ax.text(
            (x1 + x2) / 2,
            y - y_margin,
            f"{target_um:g} {unit_label}",
            color=color,
            ha="center",
            va="bottom",
            **kwargs,
        )

        return ax
