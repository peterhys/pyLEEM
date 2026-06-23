from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np
from pyleem.metadata import get_metadata_fixed_header


class Reader(ABC):
    """Abstract base class for LEEM data readers.

    The reader should implement the get_image and get_metadata methods.
    The property metadata and image are default and extract values at runtime.

    The reader does not necessary need to parse a physical file path.'
    However, the comparison operator __lt__ is required to be implemented
    so that the reader is sortable.
    """

    @abstractmethod
    def __lt__(self, other):
        """Enable sorting reader objects."""
        pass

    @property
    def metadata(self):
        """Return metadata as dictionary in (value, unit) format.

        The method force the child class to posses the _metadata attribute.
        """
        return self._metadata

    @property
    @abstractmethod
    def image(self):
        """Return image data as numpy array."""
        pass

    def plot_image(self, ax=None, **kwargs):
        """Plot the raw image data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax = ax or plt.gca()
        ax.imshow(self.image, **kwargs)
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")
        ax.set_title("Raw Image Data")

        return ax


class ReaderGroup:
    """Reader for a group of readers.

    :param list paths: List of paths to LEEM data files. The path should be
        sorted accordingly.
    """

    READER_CLS = NotImplementedError

    def __init__(self, paths):

        self.readers = [self.READER_CLS(path) for path in paths]
        self.time_intervals = self.get_time_intervals()
        for time_interval, reader in zip(self.time_intervals, self.readers):
            reader._metadata.update({"TimeInterval": (time_interval, "s")})

    def get_time_intervals(self):
        """Calculate time intervals from the first acquisition.

        :return: List of time intervals in seconds.
        :rtype: list
        """
        timestamps = [reader.metadata["TimeStamp"][0] for reader in self.readers]
        timedelta_list = np.cumsum(np.diff(timestamps, prepend=timestamps[0]))
        return [timedelta.total_seconds() for timedelta in timedelta_list]


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
        self._metadata = get_metadata_fixed_header(self.metabytes)

    def __lt__(self, other):
        """Sorting by file path."""
        return self.path < other.path

    def read_metabytes(self, metasize):
        """Read metadata bytes from file.

        :param int metasize: Number of bytes to read.
        :return: Raw metadata bytes.
        :rtype: bytes
        """
        with open(self.path, "rb") as f:
            metabytes = f.read(metasize)
        return metabytes

    @property
    def image(self):
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


class UViewReaderGroup(ReaderGroup):
    """Reader for a group of UView LEEM raw .dat files.

    :param list paths: List of paths to LEEM data files. The path should be
        sorted accordingly.
    """

    READER_CLS = UViewReader
