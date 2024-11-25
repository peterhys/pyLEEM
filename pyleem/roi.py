from roifile import ImagejRoi, ROI_TYPE
from collections.abc import Mapping
import numpy as np


class LineROI(Mapping):
    """Region of interest for a line.

    ROI parameters can be directly passed to the constructor, or a ROI file from
    ImageJ. The keys in ROI files are specific to the function
    skimage.measure.profile_line.
    """

    def __init__(self, file=None, **kwargs):
        """Initialize the ROI object.

        If a roi file is pass then the parameters are loaded onto the file.
        In the default figure orientation, the x-axis ascends from left to right,
        and the y-axis ascends from top to bottom. The origin is at the top-left corner.

        """

        if file:
            roif = ImagejRoi.fromfile(file)
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

    def __getitem__(self, key):
        """Behave somewhat like a dictionary."""
        return getattr(self, key)

    def __iter__(self):
        """Iterate over the keys."""
        return iter(self.__dict__)

    def __len__(self):
        """Return the length of the keys."""
        return len(self.__dict__)

    def to_roifile(self, file):
        """Save the ROI to a file."""

        roif = ImagejRoi(
            x1=self.src[1],
            y1=self.src[0],
            x2=self.dst[1],
            y2=self.dst[0],
            stroke_width=self.linewidth,
            stroke_color=b"M\xff\xff\x00",  # default yellow
            roitype=ROI_TYPE.LINE,
        )
        roif.tofile(file)

    def to_h5(self, group):
        """Save the ROI to a HDF5 group."""

        roi_group = group.create_group("roi")
        for key, value in self.items():
            if key == "reduce_func":
                roi_group.attrs[key] = value.__name__
            else:
                roi_group.attrs[key] = value
        roi_group.attrs["roi_type"] = "line"
