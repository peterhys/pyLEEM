import matplotlib.pyplot as plt
from pyleem.analyzer import Analyzer
from pyleem.annotation.metatext import (
    DEFAULT_METADATA_LABELS,
    MetadataTextMixin,
    format_lines,
)


class MetadataReader:
    """Reader stub with image and metadata attributes."""

    def __init__(self, image, metadata):
        self.image = image
        self.metadata = metadata


def test_format_str_lines():
    """Test metadata labels control display name, value format, and unit."""
    metadata = {
        "FOV": (50, "um"),
        "MCH": (2.4e-9, "Torr"),
        "Sample Temp.": (23.456, "C"),
        "Objective": (1600, "mA"),
        "Start Voltage": (20, "eV"),
    }
    metadata_labels = {
        "FOV": ("FOV", ".1f", None),
        "MCH": ("Pressure", ".2e", None),
        "Sample Temp.": ("Temperature", ".1f", "deg C"),
        "Objective": ("OBJ", ".1f", None),
        "Start Voltage": ("Start Voltage", ".2f", "eV"),
    }

    lines = format_lines(metadata, metadata_labels)

    assert lines == [
        "FOV: 50.0 um",
        "Pressure: 2.40e-09 Torr",
        "Temperature: 23.5 deg C",
        "OBJ: 1600.0 mA",
        "Start Voltage: 20.00 eV",
    ]


def test_overlay_text_mixin(xps_reader):
    """Test MetadataTextMixin leaves annotate_image composition to subclasses."""

    class MetadataOverlay(MetadataTextMixin, Analyzer):
        """Analyzer with metadata text overlay."""

        metadata_labels = {
            "Start Voltage": ("Start Voltage", ".2f", "eV"),
            "Incident Voltage": ("Incident", ".1f", None),
        }

        def annotate_image(self, index, ax):
            ax = super().annotate_image(index, ax)
            return self.annotate_metadata(index, ax)

    analyzer = MetadataOverlay([xps_reader])
    fig, ax = plt.subplots()

    returned = analyzer.plot_image(0, ax=ax, annotate=True)

    assert returned is ax
    assert len(ax.texts) == 1
    assert ax.texts[0].get_text() == ("Start Voltage: 200.00 eV\nIncident: 400.0 eV")
    assert ax.texts[0].get_color() == "white"
    assert not hasattr(MetadataTextMixin, "add_scale_bar")
    plt.close(fig)
