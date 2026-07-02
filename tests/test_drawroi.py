import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import Ellipse, Polygon, Rectangle

from pyleem.analyzer import Analyzer
from pyleem.annotation.drawroi import ROIAnnotationMixin, draw_roi
from pyleem.reader import Reader
from pyleem.roi import LineROI, OvalROI, PolygonROI, RectROI, NoROI


class MockReader(Reader):
    """Reader stub with image and metadata attributes."""

    def __init__(self, image, metadata=None):
        self._image = image
        self._metadata = metadata or {}

    def __lt__(self, other):
        return False

    @property
    def image(self):
        return self._image


def test_draw_line_roi():
    """Test line ROI drawing converts row/col coordinates to x/y."""
    roi = LineROI(src=(10, 5), dst=(40, 80), linewidth=3)
    fig, ax = plt.subplots()

    artist = draw_roi(ax, roi, color="cyan", linewidth=4)

    assert artist is ax.lines[0]
    assert list(artist.get_xdata()) == [5, 80]
    assert list(artist.get_ydata()) == [10, 40]
    assert artist.get_color() == "cyan"
    assert artist.get_linewidth() == pytest.approx(4)
    plt.close(fig)


def test_draw_area_rois():
    """Test area ROI drawing adds rectangle, oval, and polygon patches."""
    rois = [
        RectROI(top=10, left=20, bottom=50, right=80),
        OvalROI(top=15, left=25, bottom=55, right=85),
        PolygonROI(rows=(10, 20, 30), cols=(5, 25, 15)),
    ]
    fig, ax = plt.subplots()

    artists = [draw_roi(ax, roi, color="red", linewidth=3) for roi in rois]

    rect, oval, polygon = artists
    assert isinstance(rect, Rectangle)
    assert rect.get_xy() == pytest.approx((20, 10))
    assert rect.get_width() == pytest.approx(60)
    assert rect.get_height() == pytest.approx(40)

    assert isinstance(oval, Ellipse)
    assert oval.center == pytest.approx((55, 35))
    assert oval.width == pytest.approx(60)
    assert oval.height == pytest.approx(40)

    assert isinstance(polygon, Polygon)
    assert polygon.get_xy()[:3] == pytest.approx(
        np.array([[5, 10], [25, 20], [15, 30]])
    )
    assert all(artist.get_fill() is False for artist in artists)
    assert all(artist.get_linewidth() == pytest.approx(3) for artist in artists)
    plt.close(fig)


def test_draw_roi_handles_no_roi():
    """Test draw_roi rejects unsupported ROI types."""
    fig, ax = plt.subplots()

    with pytest.raises(NotImplementedError, match="ROI drawing is not supported"):
        draw_roi(ax, NoROI())

    plt.close(fig)


def test_roi_annotation_mixin():
    """Test ROIAnnotationMixin composes with Analyzer image annotation."""

    class ROIAnalyzer(ROIAnnotationMixin, Analyzer):
        """Analyzer with ROI overlay."""

        def annotate_image(self, index, ax):
            return self.annotate_roi(ax, self.roi)

    reader = MockReader(np.zeros((100, 100)))
    roi = RectROI(top=10, left=20, bottom=50, right=80)
    analyzer = ROIAnalyzer([reader], roi=roi)
    fig, ax = plt.subplots()

    returned = analyzer.annotate_image(index=0, ax=ax)

    assert returned is ax
    assert len(ax.patches) == 1
    assert isinstance(ax.patches[0], Rectangle)
    assert ax.patches[0].get_xy() == pytest.approx((20, 10))
    plt.close(fig)
