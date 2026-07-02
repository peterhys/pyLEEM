from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np
from pyleem.metadata import get_metadata_fixed_header


class Reader(ABC):
    """Abstract base class for LEEM data readers.

    The reader should implement the get_image and get_metadata methods.
    The property metadata and image are default and extract values at runtime.

    The reader does not necessarily need to parse a physical file path.'
    However, the comparison operator __lt__ is required to be implemented
    so that the reader is sortable.
    """

    REGISTRY = {}

    def __init_subclass__(cls, **kwargs):
        """Register the reader class in the registry."""
        super().__init_subclass__(**kwargs)
        cls.REGISTRY[cls.__name__] = cls

    @abstractmethod
    def __lt__(self, other):
        """Enable sorting reader objects."""
        pass

    @property
    def metadata(self):
        """Return metadata as dictionary in (value, unit) format.

        The method forces the child class to possess the _metadata attribute.
        """
        return self._metadata

    def update_metadata(self, metadata):
        """Update the metadata."""
        self._metadata.update(metadata)

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
        ax.set_xlabel("X [pixels]")
        ax.set_ylabel("Y [pixels]")
        ax.set_title("Raw Image Data")

        return ax


class UViewReader(Reader):
    """Reader for UView LEEM raw .dat files.

    UView .dat files contain a single image with combined file and image
    headers in a metadata block.

    Additional metadata data can be added.

    :param str or Path path: Path to .dat file.
    """

    METASIZE = 16384

    def __init__(self, path, metadata=None):
        self.path = path
        self.metabytes = self.read_metabytes(self.METASIZE)
        self._metadata = get_metadata_fixed_header(self.metabytes)

        if metadata is not None:
            self._metadata.update(metadata)

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


def get_time_intervals(readers):
    """Get the time intervals from the readers."""
    timestamps = [reader.metadata["TimeStamp"][0] for reader in readers]
    timedelta_list = np.cumsum(np.diff(timestamps, prepend=timestamps[0]))
    return [timedelta.total_seconds() for timedelta in timedelta_list]


def read_files(paths, reader_cls=UViewReader, metadata_list=None):
    """Read a list of files and add time intervals metadata.

    Additional metadata can be added to the readers with the
    metadata_list parameter.

    TimeInterval metadata, however, is added directly.
    """

    metadata_list = metadata_list or [{}] * len(paths)

    readers = [reader_cls(path) for path in paths]
    time_intervals = get_time_intervals(readers)
    for i, time_interval in enumerate(time_intervals):
        readers[i].update_metadata({"TimeInterval": (time_interval, "s")})
        readers[i].update_metadata(metadata_list[i])
    return readers
