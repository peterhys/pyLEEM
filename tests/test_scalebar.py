import matplotlib.pyplot as plt
import numpy as np
import pytest
from pyleem.analyzer import Analyzer
from pyleem.annotation.scalebar import ScaleBarMixin
from pyleem.reader import Reader


class MockReader(Reader):
    """Reader stub with image and metadata attributes."""

    def __init__(self, image, metadata):
        self.image = image
        self.metadata = metadata

    def __lt__(self, other):
        return False

    def image(self):
        return self.image

    def metadata(self):
        return self.metadata


def test_scalebar_metadata():
    """Test scale bar geometry uses FOV and image dimensions."""
    reader = MockReader(
        np.zeros((512, 1024)),
        {
            "FOV": (50, "um"),
            "ImageHeight": (512, None),
            "ImageWidth": (1024, None),
        },
    )

    class ScaleBarAnalyzer(ScaleBarMixin, Analyzer):
        """Analyzer with scale bar overlay."""

        def annotate_image(self, index, ax):
            ax = super().annotate_image(index, ax)
            return self.add_scalebar(
                index,
                ax,
                target_um=5,
                x_margin=20,
                y_margin=20,
                thickness=5,
            )

    analyzer = ScaleBarAnalyzer([reader])
    fig, ax = plt.subplots()

    analyzer.plot_image(0, ax=ax, annotate=True)

    assert ax.lines[0].get_xdata() == pytest.approx([901.6, 1004.0])
    assert ax.lines[0].get_ydata() == pytest.approx([492.0, 492.0])
    assert ax.lines[0].get_linewidth() == pytest.approx(5)
    assert ax.texts[0].get_text() == "5 um"
    assert ax.texts[0].get_position() == pytest.approx((952.8, 472.0))
    plt.close(fig)


def test_scalebar_bar_width():
    """Test caller can supply bar width without FOV metadata."""
    reader = MockReader(
        np.zeros((512, 1024)),
        {
            "ImageHeight": (512, None),
            "ImageWidth": (1024, None),
        },
    )

    class ScaleBarAnalyzer(ScaleBarMixin, Analyzer):
        """Analyzer with scale bar overlay."""

        def annotate_image(self, index, ax):
            ax = super().annotate_image(index, ax)
            return self.add_scalebar(index, ax, target_um=5, bar_width=120)

    analyzer = ScaleBarAnalyzer([reader])
    fig, ax = plt.subplots()

    analyzer.plot_image(0, ax=ax, annotate=True)

    assert ax.lines[0].get_xdata() == pytest.approx([884.0, 1004.0])
    assert ax.lines[0].get_ydata() == pytest.approx([492.0, 492.0])
    assert ax.texts[0].get_text() == "5 um"
    assert ax.texts[0].get_position() == pytest.approx((944.0, 472.0))
    plt.close(fig)
