import numpy as np
from pyleem.reader import UViewReader
import matplotlib.pyplot as plt
import os
from scipy.ndimage import gaussian_filter
from pyleem.utils import find_stitch_points, stitch_profiles, find_onset


class Analyzer:
    """Base analyzer class for LEEM data analysis.

    Provides core functionality for analyzing LEEM data files using
    UViewReader to access metadata and image data.
    To use a different reader class, subclass the Analyzer and
    redefine the READER_CLS attribute.

    :param str or Path path: Path to LEEM data file.
    :ivar Path path: Path to data file.
    :ivar str name: Filename without extension.
    :ivar UViewReader reader: Reader instance for accessing file data.
    """

    READER_CLS = UViewReader

    def __init__(self, path):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.reader = self.READER_CLS(path)

    @property
    def metadata(self):
        """Return the metadata from the reader."""
        return self.reader.metadata

    def __lt__(self, other):
        """Enable sorting by file path."""
        return self.path < other.path

    @property
    def image(self):
        """Return the image data from the reader."""
        return self.reader.read_image()

    def plot_image(self, ax=None):
        """Plot the raw image data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax = ax or plt.gca()
        ax.imshow(self.image, label=self.name)
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")
        ax.set_title("Raw Image Data")

        return ax


class ProfileAnalyzer(Analyzer):
    """Base class for LEEM profile and spectrum analysis.

    Extracts line profiles from LEEM images using a region of interest (ROI).

    :param str or Path path: Path to LEEM data file.
    :param dict or LineROI roi: Region of interest defining the line profile.
    :param kwargs: Additional keyword arguments.

    :ivar ndarray profile: 1D array of intensity values along ROI.
    :ivar ndarray pixel: Pixel indices corresponding to profile.
    :ivar ndarray abscissa: X-axis values (pixels or calibrated units).
    :ivar ndarray ordinate: Y-axis values (intensity or processed values).
    """

    def __init__(self, path, roi):
        super().__init__(path)

        self.profile = self.reader.read_profile(roi)
        self.pixel = np.arange(len(self.profile))
        self.roi = roi

        self._abscissa, self._abscissa_label = self.pixel, "Pixel"
        self._ordinate, self._ordinate_label = self.profile, "Intensity"

    @property
    def abscissa(self):
        """Return the abscissa values."""
        return self._abscissa

    @property
    def ordinate(self):
        """Return the ordinate values."""
        return self._ordinate

    @property
    def abscissa_label(self):
        """Return the abscissa label."""
        return self._abscissa_label

    @property
    def ordinate_label(self):
        """Return the ordinate label."""
        return self._ordinate_label

    def filtered_profile(self, sigma):
        """Apply Gaussian filtering to the profile.

        :param float sigma: Standard deviation for Gaussian kernel.
        :return: Filtered profile.
        :rtype: ndarray
        """
        return gaussian_filter(self.profile, sigma=sigma)

    def plot_profile(self, ax=None):
        """Plot the profile data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """

        ax = ax or plt.gca()
        ax.plot(self.abscissa, self.ordinate, label=self.name)
        ax.set_xlabel(self.abscissa_label)
        ax.set_ylabel(self.ordinate_label)

        return ax


class StitchAnalyzer:
    """Analyzer for stitching multiple profiles together.

    The analyzer stitches multiple profiles together to create a new profile.
    The profiles need to be the same class and have the same labels for
    the abscissa. The result object is for analysis only,
    no metadata or any original attributes are preserved.
    """

    def __init__(self, analyzers, stitch_points=None, method="midpoint", **kwargs):
        """Initialize stitched analyzer from list of analyzers.

        :param list analyzers: List of analyzer objects to stitch.
        :param list stitch_points: Explicit stitch points; auto-computed if None.
        :param str method: Method for auto stitch point selection ('midpoint', 'start', 'end').
        :param kwargs: Additional attributes to set.
        :raises ValueError: If analyzers have mismatched types or labels.
        """

        assert self.validate_analyzers(analyzers)

        # Sort analyzers by minimum abscissa value
        analyzers = sorted(analyzers, key=lambda x: x.abscissa.min())
        abscissa_ranges = [
            (analyzer.abscissa.min(), analyzer.abscissa.max()) for analyzer in analyzers
        ]
        self.analyzers = analyzers

        if stitch_points is None:
            stitch_points = find_stitch_points(abscissa_ranges, method)
        elif len(stitch_points) != len(analyzers) - 1:
            raise ValueError(
                f"Expected {len(analyzers) - 1} stitch points, got {len(stitch_points)}"
            )
        self.stitch_points = stitch_points

        mask_points = [abscissa_ranges[0][0]] + stitch_points + [abscissa_ranges[-1][1]]
        profiles = [analyzer.profile for analyzer in analyzers]
        abscissas = [analyzer.abscissa for analyzer in analyzers]
        abscissa, ordinate = stitch_profiles(abscissas, profiles, mask_points)

        # The final abscissa follows the order of the analzers
        is_descending = self.analyzers[0].abscissa[0] > self.analyzers[0].abscissa[-1]

        sorted_indices = np.argsort(abscissa)
        if is_descending:
            sorted_indices = sorted_indices[::-1]
        self.abscissa = abscissa[sorted_indices]
        self.ordinate = ordinate[sorted_indices]

        self.abscissa_label = analyzers[0].abscissa_label
        self.ordinate_label = analyzers[0].ordinate_label
        # Store source class for method lookup
        self.source_class = type(analyzers[0])
        self.__dict__.update(kwargs)

    def validate_analyzers(self, analyzers):
        """Validate that all analyzers are compatible for stitching.

        :param list analyzers: List of analyzer objects.
        :return: True if all analyzers are compatible.
        :rtype: bool
        :raises TypeError: If analyzers are not all the same type.
        :raises ValueError: If abscissa or ordinate labels don't match.
        """
        # Validate all analyzers are the same type and same x, y labels
        if len(set([type(analyzer) for analyzer in analyzers])) != 1:
            raise TypeError(f"All analyzers must be the same type.")
        if len(set([analyzer.abscissa_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Abscissa labels don't match.")
        if len(set([analyzer.ordinate_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Ordinate labels don't match.")

        return True

    def __getattr__(self, name):
        """Dynamically inherit methods from source class.

        This allows the summed analyzer to call any method that exists
        in the original analyzer class.
        """
        if hasattr(self.source_class, name):
            attr = getattr(self.source_class, name)
            if callable(attr):
                return lambda *args, **kwargs: attr(self, *args, **kwargs)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )


class AnalyzerGroup:
    """Base class for batch analysis of multiple LEEM files.

    Manages a collection of analyzer instances for processing multiple
    data files together.

    :param list paths: List of paths to LEEM data files.
    :param type analyzer: Analyzer class to instantiate for each file.
    :param kwargs: Additional keyword arguments for each analyzer.

    :ivar list paths: List of file paths.
    :ivar list analyzers: List of analyzer instances.
    :ivar list time_intervals: Time intervals in seconds from first acquisition.
    """

    def __init__(self, analyzers):

        self.analyzers = analyzers
        self.time_intervals = self.get_time_intervals()

    def __len__(self):
        """Return the number of analyzers in the group."""
        return len(self.analyzers)

    def __iter__(self):
        """Iterate over the analyzers in the group."""
        return iter(self.analyzers)

    def __getitem__(self, index):
        """Get the analyzer at the specified index."""
        return self.analyzers[index]

    def get_metas(self, key):
        """Get metadata values from all analyzers.

        :param str key: Metadata key to retrieve.
        :return: List of metadata values.
        :rtype: list
        """
        return [analyzer.metadata[key][0] for analyzer in self.analyzers]

    def get_attrs(self, attr_name):
        """Get attribute values from all analyzers.

        :param str attr_name: Attribute name to retrieve.
        :return: List of attribute values.
        :rtype: list
        """
        return [getattr(analyzer, attr_name) for analyzer in self.analyzers]

    def get_time_intervals(self):
        """Calculate time intervals from the first acquisition.

        :return: List of time intervals in seconds.
        :rtype: list
        """
        timestamps = self.get_metas("TimeStamp")
        timedelta_list = np.cumsum(np.diff(timestamps, prepend=timestamps[0]))
        return [timedelta.total_seconds() for timedelta in timedelta_list]

    def find_onset(self):
        """Find the onset of the time series.

        In cases that the collection is turned on before the source,
        first several frames do not have signal. Here we detect through
        simple gradient analysis where the onset is.

        If the groups are images, we take the sum of the image and then find the onset.
        If the groups are profiles, we find the onset of the profiles.

        :return: Index of the analyzer with the steepest rise.
        :rtype: int
        """

        try:
            profiles = self.get_attrs("profile")
        except AttributeError:
            profiles = [analyzer.image.sum() for analyzer in self.analyzers]

        return find_onset(profiles)
