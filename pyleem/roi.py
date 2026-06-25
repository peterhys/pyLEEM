from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np
import skimage.draw
import skimage.measure
from roifile import ImagejRoi, ROI_TYPE


@dataclass(frozen=True)
class ROIMeasurement:
    """ROI measurement result."""

    mean: float
    total: float
    minimum: float
    maximum: float
    n_pixels: int
    profile: np.ndarray | None = None


def measure_values(values, profile=None):
    """Measure intensity statistics from selected values."""
    if values.size == 0:
        raise ValueError("ROI selects no pixels")

    return ROIMeasurement(
        mean=float(values.mean()),
        total=float(values.sum()),
        minimum=float(values.min()),
        maximum=float(values.max()),
        n_pixels=int(values.size),
        profile=profile,
    )


@dataclass
class ROI(ABC):
    """Abstract base class for ImageJ-compatible regions of interest."""

    roi_file: str | None = field(default=None, repr=False)
    _required: tuple = field(default=(), init=False, repr=False)

    REGISTRY = {}

    def __init_subclass__(cls, **kwargs):
        """Register the ROI class in the registry."""
        super().__init_subclass__(**kwargs)
        cls.REGISTRY[cls.__name__] = cls

    def __post_init__(self):
        """Post initialization hook to load ROI from file if provided.

        Allow instantiation directly from parameters.
        """
        if self.roi_file:
            self.fromfile(ImagejRoi.fromfile(self.roi_file))
        else:
            missing = [f for f in self._required if getattr(self, f) is None]
            if missing:
                raise ValueError(f"{type(self).__name__} missing fields: {missing}")

        self.validate()

    def validate(self):
        """Validate ROI parameters."""
        pass

    def validate_roi_type(self, roi, expected_type):
        """When loading from roi file, validate the ROI type."""
        if roi.roitype != expected_type:
            raise ValueError(
                f"Expected {expected_type.name} ROI, got {roi.roitype.name}"
            )

    @abstractmethod
    def fromfile(self, roi):
        """Load ROI from ImageJ file."""
        pass

    @abstractmethod
    def tofile(self, filename):
        """Save ROI to roifile.ImagejRoi file.

        Use `roi.tofile(filename)` to save the ROI to a file.
        """
        pass


@dataclass
class NoROI(ROI):
    """NoROI placeholder for analyzer."""

    def measure(self, image, **kwargs):
        """Measure image intensity."""
        raise NotImplementedError("No ROI selected")

    def profile(self, image, **kwargs):
        """Extract line profile from image."""
        raise NotImplementedError("No ROI selected")

    def fromfile(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        raise NotImplementedError("No ROI selected")

    def tofile(self, filename):
        """Save ROI to roifile.ImagejRoi file."""
        raise NotImplementedError("No ROI selected")


@dataclass
class LineROI(ROI):
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
    _required: tuple = field(
        default=("src", "dst", "linewidth"), init=False, repr=False
    )

    def validate(self):
        """Validate line ROI parameters."""
        if self.linewidth < 1:
            raise ValueError("LineROI linewidth must be at least 1")

    def profile(self, image, **kwargs):
        """Extract line profile from image."""
        return skimage.measure.profile_line(
            image,
            self.src,
            self.dst,
            self.linewidth,
            **kwargs,
        )

    def measure(self, image, **kwargs):
        """Measure image intensity along the ROI."""
        profile = self.profile(image, **kwargs)
        return measure_values(profile, profile=profile)

    def fromfile(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        self.validate_roi_type(roi, ROI_TYPE.LINE)

        self.src = (roi.y1, roi.x1)
        self.dst = (roi.y2, roi.x2)
        self.linewidth = roi.stroke_width or 1

    def tofile(self, filename):
        """Save to roifile.ImagejRoi object."""
        ImagejRoi(
            x1=self.src[1],
            y1=self.src[0],
            x2=self.dst[1],
            y2=self.dst[0],
            stroke_width=self.linewidth,
            stroke_color=b"M\xff\xff\x00",
            roitype=ROI_TYPE.LINE,
        ).tofile(filename)


@dataclass
class AreaROI(ROI):
    """Base class for area regions of interest."""

    @abstractmethod
    def mask(self, shape):
        """Return the selected pixels as a boolean mask."""
        pass

    def profile(self, image, **kwargs):
        """Return a profile for the area ROI, if available."""
        return None

    def measure(self, image, **kwargs):
        """Measure image intensity inside the ROI."""
        values = image[self.mask(image.shape)]
        profile = self.profile(image, **kwargs)
        return measure_values(values, profile=profile)


@dataclass
class RectROI(AreaROI):
    """Rectangular area ROI."""

    top: int = None
    left: int = None
    bottom: int = None
    right: int = None
    _required: tuple = field(
        default=("top", "left", "bottom", "right"), init=False, repr=False
    )

    def __post_init__(self):
        """Post initialization hook to calculate height and width."""
        super().__post_init__()
        self.height = self.bottom - self.top
        self.width = self.right - self.left

    def fromfile(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        self.validate_roi_type(roi, ROI_TYPE.RECT)
        self.top, self.left, self.bottom, self.right = (
            roi.top,
            roi.left,
            roi.bottom,
            roi.right,
        )

    def validate(self):
        """Validate rectangular ROI parameters."""

        if self.top < 0 or self.left < 0:
            raise ValueError("ROI bounds must be non-negative")
        if self.bottom - self.top <= 0 or self.right - self.left <= 0:
            raise ValueError("ROI height and width must be positive")

    def mask(self, shape):
        """Return the selected pixels as a boolean mask."""
        selected = np.zeros(shape, dtype=bool)
        selected[
            self.top : self.top + self.height,
            self.left : self.left + self.width,
        ] = True
        return selected

    def tofile(self, filename):
        """Save to roifile.ImagejRoi object."""
        ImagejRoi(
            top=self.top,
            left=self.left,
            bottom=self.bottom,
            right=self.right,
            roitype=ROI_TYPE.RECT,
        ).tofile(filename)


@dataclass
class OvalROI(AreaROI):
    """Oval area ROI."""

    top: int = None
    left: int = None
    bottom: int = None
    right: int = None
    _required: tuple = field(
        default=("top", "left", "bottom", "right"), init=False, repr=False
    )

    def __post_init__(self):
        """Post initialization hook to calculate height and width."""
        super().__post_init__()
        self.height = self.bottom - self.top
        self.width = self.right - self.left

    def fromfile(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        self.validate_roi_type(roi, ROI_TYPE.OVAL)
        self.top, self.left, self.bottom, self.right = (
            roi.top,
            roi.left,
            roi.bottom,
            roi.right,
        )
        self.left = roi.left
        self.bottom = roi.bottom
        self.right = roi.right

    def validate(self):
        """Validate oval ROI parameters."""

        if self.top < 0 or self.left < 0:
            raise ValueError("ROI bounds must be non-negative")
        if self.bottom - self.top <= 0 or self.right - self.left <= 0:
            raise ValueError("ROI height and width must be positive")

    def mask(self, shape):
        """Return the selected pixels as a boolean mask."""
        rows, cols = np.indices(shape)
        row_center = self.top + (self.height - 1) / 2
        col_center = self.left + (self.width - 1) / 2
        row_radius = self.height / 2
        col_radius = self.width / 2

        return ((rows - row_center) / row_radius) ** 2 + (
            (cols - col_center) / col_radius
        ) ** 2 <= 1

    def tofile(self, filename):
        """Save to roifile.ImagejRoi object."""
        ImagejRoi(
            top=self.top,
            left=self.left,
            bottom=self.bottom,
            right=self.right,
            roitype=ROI_TYPE.OVAL,
        ).tofile(filename)


@dataclass
class PolygonROI(AreaROI):
    """Polygon area ROI."""

    rows: tuple = None
    cols: tuple = None
    _required: tuple = field(default=("rows", "cols"), init=False, repr=False)

    def validate(self):
        """Validate polygon ROI parameters."""
        if len(self.rows) != len(self.cols):
            raise ValueError("PolygonROI rows and cols must have same length")
        if len(self.rows) < 3:
            raise ValueError("PolygonROI requires at least three points")
        if min(self.rows) < 0 or min(self.cols) < 0:
            raise ValueError("PolygonROI coordinates must be non-negative")

    def mask(self, shape):
        """Return the selected pixels as a boolean mask."""
        selected = np.zeros(shape, dtype=bool)
        rows, cols = skimage.draw.polygon(self.rows, self.cols, shape=shape)
        selected[rows, cols] = True
        return selected

    def fromfile(self, roi):
        """Load ROI from roifile.ImagejRoi object."""
        self.validate_roi_type(roi, ROI_TYPE.POLYGON)

        coordinates = roi.coordinates()
        self.cols = tuple(coordinates[:, 0])
        self.rows = tuple(coordinates[:, 1])

    def tofile(self, filename):
        """Save to roifile.ImagejRoi object."""
        roi = ImagejRoi.frompoints(np.column_stack((self.cols, self.rows)))
        roi.roitype = ROI_TYPE.POLYGON
        roi.tofile(filename)
