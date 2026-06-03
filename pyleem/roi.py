from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np
import skimage.measure
from roifile import ImagejRoi, ROI_TYPE


@dataclass
class ROIBase(ABC):
    """Abstract base class for ImageJ-compatible regions of interest."""

    roi_file: str | None = field(default=None, repr=False)
    _required: tuple = field(default=(), init=False, repr=False)

    def __post_init__(self):
        """Post initialization hook to load ROI from file if provided.

        Allow instantiation directly from parameters.
        """
        if self.roi_file:
            self.load_from_file(ImagejRoi.fromfile(self.roi_file))
        else:
            missing = [f for f in self._required if getattr(self, f) is None]
            if missing:
                raise ValueError(f"{type(self).__name__} missing fields: {missing}")

    @abstractmethod
    def load_from_file(self, roi):
        """Load ROI from ImageJ file."""
        pass

    @abstractmethod
    def to_roi_object(self):
        """Save ROI to roifile.ImagejRoi object.

        To convert to a file, use `roi.tofile(file)`.
        """
        pass

    @abstractmethod
    def read_profile(self, image):
        """Extract profile from image."""
        pass


@dataclass
class LineROI(ROIBase):
    """Line ROI for use with skimage.measure.profile_line.

    :ivar tuple src: Starting point (y, x) in image coordinates.
    :ivar tuple dst: Ending point (y, x) in image coordinates.
    :ivar int linewidth: Width of line profile in pixels.
    :ivar int order: Interpolation order (1 for linear).
    :ivar str mode: How to handle values outside image.
    :ivar float cval: Fill value for 'constant' mode.
    :ivar callable reduce_func: Function to aggregate values across line width.
    """

    src: tuple = None
    dst: tuple = None
    linewidth: int = None
    order: int = 1
    mode: str = "nearest"
    cval: float = 0
    reduce_func: callable = field(default=np.mean, repr=False)
    _required: tuple = field(
        default=("src", "dst", "linewidth"), init=False, repr=False
    )

    def load_from_file(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        self.src = (roi.y1, roi.x1)
        self.dst = (roi.y2, roi.x2)
        self.linewidth = roi.stroke_width

    def read_profile(self, image):
        """Extract line profile from image."""
        return skimage.measure.profile_line(
            image,
            self.src,
            self.dst,
            self.linewidth,
            order=self.order,
            mode=self.mode,
            cval=self.cval,
            reduce_func=self.reduce_func,
        )

    def to_roi_object(self):
        """Save to roifile.ImagejRoi object."""
        return ImagejRoi(
            x1=self.src[1],
            y1=self.src[0],
            x2=self.dst[1],
            y2=self.dst[0],
            stroke_width=self.linewidth,
            stroke_color=b"M\xff\xff\x00",
            roitype=ROI_TYPE.LINE,
        )
