import numpy as np
from pyleem.reader import UViewReader
import matplotlib.pyplot as plt
import os
from scipy.ndimage import gaussian_filter
from pyleem.utils import find_onset
import pathlib


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

    def __init__(self, path, reader=UViewReader, roi=None):
        self.path = path
        self.name = pathlib.Path(path).stem
        self.reader = reader(path)
        self._process_list = []
        self._analysis_list = []
        self.roi = roi

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
        return self.reader.image

    def plot_image(self, ax=None):
        """Plot the raw image data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax = ax or plt.gca()
        ax.imshow(self.image, label=self.name)
        ax.set_xlabel("X [pixels]")
        ax.set_ylabel("Y [pixels]")
        ax.set_title("Raw Image Data")

        return ax

    @property
    def analysis_list(self):
        """Return the analysis processes."""
        return self._analysis_list

    @property
    def process_list(self):
        """Return the processes."""
        return self._process_list

    @property
    def processed_image(self):
        """Return the processed image."""
        image = self.image
        for process in self._process_list:
            image = process(image)
        return image

    @property
    def analysis_results(self):
        """Return the processed analysis."""
        results = {}
        for analysis in self._analysis:
            results[analysis.name] = analysis(self)
        return results

    # def profile(self):
    #     """Return the profile."""
    #     if isinstance(self, LineROI):
    #         return self.roi.read_profile(self.image)
    #     else:
    #         return self.process_profile()

    # def plot_profile(self, ax=None):
    #     """Plot the profile data.

    #     :param matplotlib.axes.Axes ax: Matplotlib axes object.
    #     """

    #     ax = ax or plt.gca()
    #     ax.plot(self.abscissa, self.ordinate, label=self.name)
    #     ax.set_xlabel(self.abscissa_label)
    #     ax.set_ylabel(self.ordinate_label)

    #     return ax


# class ProfileAnalyzer(Analyzer):
#     """Base class for LEEM profile and spectrum analysis.

#     Extracts line profiles from LEEM images using a region of interest (ROI).

#     :param str or Path path: Path to LEEM data file.
#     :param dict or LineROI roi: Region of interest defining the line profile.
#     :param kwargs: Additional keyword arguments.

#     :ivar ndarray profile: 1D array of intensity values along ROI.
#     :ivar ndarray pixel: Pixel indices corresponding to profile.
#     :ivar ndarray abscissa: X-axis values (pixels or calibrated units).
#     :ivar ndarray ordinate: Y-axis values (intensity or processed values).
#     """

#     def __init__(self, path, roi):
#         super().__init__(path)

#         self.roi = roi
#         self._profile = self.roi.read_profile(self.image)
#         self.pixel = np.arange(len(self.profile))
#         self._abscissa, self._abscissa_label = self.pixel, "Pixel"
#         self._ordinate, self._ordinate_label = self.profile, "Intensity"

#     @property
#     def abscissa(self):
#         """Return the abscissa values."""
#         return self._abscissa

#     @property
#     def ordinate(self):
#         """Return the ordinate values."""
#         return self._ordinate

#     @property
#     def abscissa_label(self):
#         """Return the abscissa label."""
#         return self._abscissa_label

#     @property
#     def ordinate_label(self):
#         """Return the ordinate label."""
#         return self._ordinate_label

#     @property
#     def profile(self):
#         """Return the profile.

#         Unlike image, profile is pre-computed.
#         """
#         return self._profile

#     def process_profile(self, sigma):
#         """Default profile filtering method.

#         :param float sigma: Standard deviation for Gaussian kernel.
#         :return: Filtered profile.
#         :rtype: ndarray
#         """
#         return gaussian_filter(self.profile, sigma=sigma)

#     def plot_profile(self, ax=None):
#         """Plot the profile data.

#         :param matplotlib.axes.Axes ax: Matplotlib axes object.
#         """

#         ax = ax or plt.gca()
#         ax.plot(self.abscissa, self.ordinate, label=self.name)
#         ax.set_xlabel(self.abscissa_label)
#         ax.set_ylabel(self.ordinate_label)

#         return ax


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

    def __init__(self, analyzers, roi=None, onset=0):

        if onset is None:
            onset = self.find_onset()
        self.onset = onset

        self.analyzers = analyzers[self.onset :]
        self.roi = roi

        self._process_list = []
        self._analysis_list = []

    @property
    def process_list(self):
        """Return the processes."""
        return self._process_list

    @property
    def analysis_list(self):
        """Return the analysis processes."""
        return self._analysis_list

    @property
    def analysis_results(self):
        """Return the analysis results."""
        results = {}
        for analysis in self._analysis_list:
            results[analysis.name] = analysis(self)
        return results

    def __len__(self):
        """Return the number of analyzers in the group."""
        return len(self.analyzers)

    def __iter__(self):
        """Iterate over the analyzers in the group."""
        return iter(self.analyzers)

    def __getitem__(self, index):
        """Get the analyzer at the specified index."""
        return self.analyzers[index]

    def get_metadata_list(self, key):
        """Get metadata values from all analyzers.

        :param str key: Metadata key to retrieve.
        :return: List of metadata values.
        :rtype: list
        """
        return [analyzer.metadata[key][0] for analyzer in self.analyzers]

    def get_attribute_list(self, attr_name):
        """Get attribute values from all analyzers.

        :param str attr_name: Attribute name to retrieve.
        :return: List of attribute values.
        :rtype: list
        """
        return [getattr(analyzer, attr_name) for analyzer in self.analyzers]

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

        profiles = [analyzer.image.sum() for analyzer in self.analyzers]

        return find_onset(profiles)
