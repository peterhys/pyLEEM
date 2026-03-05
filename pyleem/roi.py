from roifile import ImagejRoi, ROI_TYPE
import numpy as np


class LineROI:
    """Line region of interest for profile extraction.

    Defines a line ROI compatible with skimage.measure.profile_line.
    Can be initialized from ImageJ ROI files or direct parameters.
    Behaves like a dictionary for unpacking into skimage functions.

    In default orientation, x-axis increases left to right, y-axis
    increases top to bottom, origin is at top-left corner.

    :param str or Path roi_file: Path to ImageJ ROI file (loads parameters if provided).
    :param kwargs: ROI parameters (src, dst, linewidth, etc.).

    :ivar tuple src: Starting point (y, x) in image coordinates.
    :ivar tuple dst: Ending point (y, x) in image coordinates.
    :ivar int linewidth: Width of line profile in pixels.
    :ivar int order: Interpolation order (1 for linear).
    :ivar str mode: How to handle values outside image.
    :ivar float cval: Fill value for 'constant' mode.
    :ivar callable reduce_func: Function to aggregate values across line width.
    """

    def __init__(self, roi_file=None, **kwargs):
        """Initialize LineROI from an ImageJ ROI file or keyword arguments.

        When ``roi_file`` is not provided, ``src``, ``dst``, and ``linewidth``
        must be supplied via ``kwargs``.
        """
        if roi_file:
            roif = ImagejRoi.fromfile(roi_file)
            self.src = (roif.y1, roif.x1)
            self.dst = (roif.y2, roif.x2)
            self.linewidth = roif.stroke_width
        else:
            assert "src" in kwargs and "dst" in kwargs and "linewidth" in kwargs
        self.order = 1
        self.mode = "nearest"
        self.cval = 0
        self.reduce_func = np.mean
        self.__dict__.update(kwargs)

        if "pixel_per_ev" in kwargs and "peak_shift" in kwargs:
            self.calibrate(kwargs["pixel_per_ev"], kwargs["peak_shift"])
        else:
            self._is_calibrated = False
            self.pixel_per_ev = None
            self.peak_shift = None

    def to_dict(self):
        """Convert ROI to dictionary for skimage.measure.profile_line.

        :return: Dictionary with keys src, dst, linewidth, order, mode, cval,
            and reduce_func.
        :rtype: dict
        """
        keys = ["src", "dst", "linewidth", "order", "mode", "cval", "reduce_func"]
        return {key: getattr(self, key) for key in keys}

    def calibrate(self, pixel_per_ev, peak_shift, **kwargs):
        """Calibrate ROI parameters.

        :param float pixel_per_ev: Pixel per eV conversion factor.
        :param float peak_shift: Peak shift in pixels.
        :param kwargs: Additional calibration attributes to set on the instance.
        """
        self.pixel_per_ev = pixel_per_ev
        self.peak_shift = peak_shift
        self.__dict__.update(kwargs)
        self._is_calibrated = True

    @property
    def is_calibrated(self):
        """Check whether ROI is calibrated.

        :return: ``True`` if calibration parameters have been set.
        :rtype: bool
        """
        return self._is_calibrated

    def to_roifile(self, file):
        """Save ROI to ImageJ-compatible file.

        :param str or Path file: Output file path.
        """
        roif = ImagejRoi(
            x1=self.src[1],
            y1=self.src[0],
            x2=self.dst[1],
            y2=self.dst[0],
            stroke_width=self.linewidth,
            stroke_color=b"M\xff\xff\x00",  # yellow
            roitype=ROI_TYPE.LINE,
        )
        roif.tofile(file)
