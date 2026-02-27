"""File readers for LEEM data formats."""

from pyleem.metadata import get_metadata
import numpy as np
import os
from datetime import datetime
import skimage
from abc import ABC, abstractmethod
import h5py


class Reader(ABC):
    """Abstract base class for LEEM data readers."""

    @abstractmethod
    def metadata(self):
        """Return metadata as dictionary in (value, unit) format."""
        pass

    @abstractmethod
    def read_image(self):
        """Read and return image data from file."""
        pass

    @abstractmethod
    def read_profile(self, roi):
        """Extract profile data from image.

        :param dict or LineROI roi: Region of interest.
        """
        pass

    @abstractmethod
    def __lt__(self, other):
        """Enable sorting by comparison."""
        pass


class UViewReader(Reader):
    """Reader for UView LEEM raw .dat files.

    UView .dat files contain a single image with combined file and image
    headers in a metadata block.

    :param str or Path path: Path to .dat file.
    """

    METASIZE = 16384

    def __init__(self, path):
        self.path = path
        self.metabytes = self.read_metabytes(self.METASIZE)
        self._metadata = get_metadata(self.metabytes)

    @property
    def metadata(self):
        """Return the parsed metadata dictionary."""
        return self._metadata

    def read_metabytes(self, metasize):
        """Read metadata bytes from file.

        :param int metasize: Number of bytes to read.
        :return: Raw metadata bytes.
        :rtype: bytes
        """
        with open(self.path, "rb") as f:
            metabytes = f.read(metasize)
        return metabytes

    def read_image(self):
        """Read the image data from file.

        Images are stored at the end of the file as 16-bit unsigned integers
        (little-endian) with shape (height, width).

        :return: Image array.
        :rtype: ndarray
        """
        dt = np.dtype(np.uint16).newbyteorder("<")
        height = self.metadata["ImageHeight"][0]
        width = self.metadata["ImageWidth"][0]

        with open(self.path, "rb") as f:
            f.seek(-height * width * 2, 2)
            img = np.frombuffer(f.read(), dtype=dt).reshape(height, width)
        return img

    def read_profile(self, roi):
        """Extract profile data from the image.

        :param dict or LineROI roi: Region of interest.
        :return: Profile array.
        :rtype: ndarray
        """
        return skimage.measure.profile_line(self.read_image(), **roi.to_dict())

    def __lt__(self, other):
        """Enable sorting by file path."""
        return self.path < other.path

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def to_h5(self, f, gname=None, write_img=True):
        """Write data to an HDF5 file.

        Creates a group in the HDF5 file and saves metadata as group attributes.
        Optionally saves the image data with gzip compression.

        :param h5py.File f: Open HDF5 file object.
        :param str gname: Group name (uses filename if None).
        :param bool write_img: Whether to write image data.
        """
        gname = gname or os.path.splitext(os.path.basename(self.path))[0]
        group = f.create_group(gname)

        for source, (arg, unit) in self.metadata.items():
            if (
                arg is not None
                and not isinstance(arg, bytes)
                and not isinstance(arg, datetime)
            ):
                group.attrs[source] = arg
            if unit is not None:
                group.attrs[source + "_unit"] = unit

        if write_img:
            group.create_dataset("image", data=self.read_image(), compression="gzip")


class H5Reader(Reader):
    """Reader for HDF5 files created by UViewReader.

    Loads LEEM data from the HDF5 format. 
    :param str or Path path: Path to .h5 file.
    :param str gname: Group name (uses first group if None).

    :ivar Path path: Path to HDF5 file.
    :ivar str gname: Group name containing data.
    """

    def __init__(self, path, gname=None):
        self.path = path

        with h5py.File(self.path, "r") as f:
            if gname is None:
                groups = list(f.keys())
                if not groups:
                    raise ValueError(f"No groups found in HDF5 file: {path}")
                self.gname = groups[0]
            else:
                self.gname = gname

            if self.gname not in f:
                raise ValueError(f"Group '{self.gname}' not found in HDF5 file: {path}")


        self._metadata = {}

        with h5py.File(self.path, "r") as f:
            group = f[self.gname]
            attrs = dict(group.attrs)

            # Separate regular and unit attributes
            unit_attrs = {
                k[:-5]: v for k, v in attrs.items() if k.endswith("_unit")
            }

            for key, value in attrs.items():
                if not key.endswith("_unit"):
                    unit = unit_attrs.get(key, None)
                    self._metadata[key] = (value, unit)


    @property
    def metadata(self):
        """Return metadata dictionary in (value, unit) format.

        Metadata is reconstructed from HDF5 group attributes where
        attributes ending in '_unit' are paired with parameter attributes.
        """

        return self._metadata

    def read_image(self):
        """Read image data from the HDF5 file."""

        with h5py.File(self.path, "r") as f:
            group = f[self.gname]
            if "image" in group:
                image = group["image"][:]
            else:
                return None

        return image

    def read_profile(self, roi):
        """Extract profile data from the image.

        :param dict or LineROI roi: Region of interest.
        :return: Profile array.
        :rtype: ndarray
        """
        img = self.read_image()
        if img is None:
            raise ValueError(f"No image data found in group '{self.gname}'")
        return skimage.measure.profile_line(img, **roi)

    def __lt__(self, other):
        """Enable sorting by path and group name."""
        if self.path != other.path:
            return self.path < other.path
        return self.gname < other.gname

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path}, gname='{self.gname}')"
