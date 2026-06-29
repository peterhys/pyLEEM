import matplotlib.patches as patches
from pyleem.roi import LineROI, OvalROI, PolygonROI, RectROI


def draw_line_roi(ax, roi, color="yellow", linewidth=2, **kwargs):
    """Draw a line ROI on an image axes."""
    row1, col1 = roi.src
    row2, col2 = roi.dst

    (line,) = ax.plot(
        [col1, col2],
        [row1, row2],
        color=color,
        linewidth=linewidth,
        **kwargs,
    )
    return line


def draw_rect_roi(ax, roi, color="yellow", linewidth=2, **kwargs):
    """Draw a rectangular ROI on an image axes."""
    patch = patches.Rectangle(
        (roi.left, roi.top),
        roi.width,
        roi.height,
        fill=False,
        edgecolor=color,
        linewidth=linewidth,
        **kwargs,
    )
    ax.add_patch(patch)
    return patch


def draw_oval_roi(ax, roi, color="yellow", linewidth=2, **kwargs):
    """Draw an oval ROI on an image axes."""
    patch = patches.Ellipse(
        (roi.left + roi.width / 2, roi.top + roi.height / 2),
        roi.width,
        roi.height,
        fill=False,
        edgecolor=color,
        linewidth=linewidth,
        **kwargs,
    )
    ax.add_patch(patch)
    return patch


def draw_polygon_roi(ax, roi, color="yellow", linewidth=2, **kwargs):
    """Draw a polygon ROI on an image axes."""
    points = list(zip(roi.cols, roi.rows))

    patch = patches.Polygon(
        points,
        closed=True,
        fill=False,
        edgecolor=color,
        linewidth=linewidth,
        **kwargs,
    )
    ax.add_patch(patch)
    return patch


ROI_DRAWERS = {
    LineROI: draw_line_roi,
    RectROI: draw_rect_roi,
    OvalROI: draw_oval_roi,
    PolygonROI: draw_polygon_roi,
}


def draw_roi(ax, roi, color="yellow", linewidth=2, **kwargs):
    """Draw an ROI object on an image axes."""
    for roi_class, draw_func in ROI_DRAWERS.items():
        if isinstance(roi, roi_class):
            return draw_func(ax, roi, color=color, linewidth=linewidth, **kwargs)

    raise NotImplementedError(f"ROI drawing is not supported for {type(roi).__name__}")


class ROIAnnotationMixin:
    """Mixin that draws the analyzer ROI on image plots."""

    def annotate_roi(self, ax, roi, color="yellow", linewidth=2, **kwargs):
        """Add ROI annotation to an image axes."""
        draw_roi(ax, roi, color=color, linewidth=linewidth, **kwargs)
        return ax
