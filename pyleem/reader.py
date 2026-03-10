from pyleem.metadata import get_metadata
import numpy as np
import skimage
from abc import ABC, abstractmethod


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


    def __lt__(self, other):
        """Enable sorting by file path."""
        return self.path < other.path

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"
