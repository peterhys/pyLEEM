"""Metadata text annotation for image analyzers."""

DEFAULT_METADATA_LABELS = {
    "FOV": ("FOV", None, None),
    "MCH": ("Main Chamber Pressure", ".2e", None),
    "Sample Temp.": ("Sample Temperature", ".1f", "deg C"),
    "Objective": ("Objective", ".1f", None),
    "Start Voltage": ("Start Voltage", ".2f", "eV"),
    "TimeInterval": ("Time Interval", ".2f", "s"),
}


def format_value(value, value_format=None):
    """Return a metadata value formatted for metadata text.

    If the value_format is not provided, return the string value.
    """
    if value_format is None:
        value_str = str(value)
    else:
        value_str = format(value, value_format)
    return value_str


def format_unit(metadata_unit, unit_name):
    """Return the unit text for a metadata field."""
    if unit_name is None:
        return metadata_unit or ""

    return unit_name


def format_line(label, value_text, unit_text=""):
    """Return one metadata text line."""
    text_parts = [value_text]
    if unit_text:
        text_parts.append(unit_text)

    text = " ".join(text_parts).strip()
    if not label:
        return text

    return f"{label}: {text}".strip()


def format_lines(metadata, metadata_labels):
    """Return formatted metadata text lines from metadata and metadata labels.

    metadata_labels maps source metadata keys to
    (display_name, value_format, unit_name) tuples.
    Dictionary order controls the output order.
    """
    lines = []

    for key, (display_name, value_format, unit_name) in metadata_labels.items():
        value, metadata_unit = metadata[key]
        value_text = format_value(value, value_format) if value_format else str(value)
        unit_text = format_unit(metadata_unit, unit_name)
        lines.append(format_line(display_name, value_text, unit_text))

    return lines


class MetadataTextMixin:
    """Mixin that adds selected metadata text to Analyzer image plots.

    Inherit from this mixin before the analyzer class, then call
    annotate_metadata from the subclass annotate_image method.

    Example::

        class MetadataXPSAnalyzer(MetadataTextMixin, XPSAnalyzer):

            metadata_labels = DEFAULT_METADATA_LABELS

            def annotate_image(self, index, ax):
                ax = super().annotate_image(index, ax)
                return self.annotate_metadata(index, ax)
    """

    metadata_labels = DEFAULT_METADATA_LABELS

    def get_metadata_text(self, index, labels=None):
        """Return formatted metadata text for one image index."""
        labels = self.metadata_labels if labels is None else labels
        metadata = {key: self.get_metadata(key, index) for key in labels}
        lines = format_lines(metadata, labels)
        return "\n".join(lines)

    def annotate_metadata(
        self,
        index,
        ax,
        labels=None,
        position=(0.03, 0.97),
        color="white",
        **kwargs,
    ):
        """Add configured metadata text to an image axes."""
        text = self.get_metadata_text(index, labels=labels)
        if not text:
            return ax

        ax.text(
            position[0],
            position[1],
            text,
            transform=ax.transAxes,
            ha="left",
            va="top",
            color=color,
            **kwargs,
        )

        return ax
