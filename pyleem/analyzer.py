import matplotlib.pyplot as plt
from pyleem.roi import NoROI
import numpy as np


def find_onset(profiles):
    """Find the onset of a profile.

    The profiles can be full images or line profiles.
    Here we look at the "relative difference". The
    np.gradient is not used because it tracks two steps at a time.

    :param list profiles: List of profiles to find the onset of.
    :return: Index of the profile with the steepest rise.
    :rtype: int
    """

    profile_sums = np.array([profile.sum() for profile in profiles], dtype=np.float64)
    profile_diff = np.diff(profile_sums) / profile_sums[:-1]

    return np.argmax(profile_diff)


class Analyzer:
    """Base analyzer class for LEEM data analysis.

    Provides core functionality for domain-specific LEEM analysis.
    Raw images come from readers. Processed images default to raw images.
    Annotated images default to processed images.

    All variable access should be index aware.

    :param iterable readers: Reader objects used by the analyzer.
    :ivar list readers: List of readers after onset.
    :ivar ROI roi: ROI for measuring the image.
    :ivar int onset: Index of the onset of the image.
    """

    REGISTRY = {}

    def __init_subclass__(cls, **kwargs):
        """Register the analyzer class in the registry."""
        super().__init_subclass__(**kwargs)
        cls.REGISTRY[cls.__name__] = cls

    def __init__(self, readers, roi=None, onset=0):

        if not readers:
            raise ValueError("readers cannot be empty")

        if onset is None:
            onset = find_onset([reader.image for reader in readers])
        self.onset = onset

        self.readers = readers[self.onset :]
        if not self.readers:
            raise ValueError("readers empty after onset")
        self.roi = roi or NoROI()
        self.indices = range(len(self.readers))

    def get_image(self, index, kind="raw"):
        """Return the image."""
        if kind == "raw":
            return self.get_raw_image(index)
        elif kind == "processed":
            return self.get_processed_image(index)
        else:
            raise ValueError(f"Invalid image kind: {kind}")

    def annotate_image(self, index, ax):
        """Annotate the image for matplotlib plotting.

        Override to annotate the image. Currently, the annotate_image method
        does not take additional arguments. The idea is that the whole image
        stack should be annotated the same way.
        """
        return ax

    def plot_image(self, index, ax=None, kind="processed", annotate=False):
        """Plot image data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        :param str kind: Kind of image to plot.
        """
        ax = ax or plt.gca()

        image = self.get_image(index, kind=kind)
        ax.imshow(image)

        if annotate:
            self.annotate_image(index, ax)

        ax.set_xlabel("X [pixels]")
        ax.set_ylabel("Y [pixels]")
        ax.set_title(f"{kind.capitalize()} Image Data")

        return ax

    def get_measurement(self, index, kind="processed"):
        """Measure the image data."""
        image = self.get_image(index, kind=kind)

        return self.roi.measure(image)

    def get_profile(self, index, kind="processed"):
        """Extract the line profile from the image data."""
        return self.get_measurement(index, kind=kind).profile

    def get_pixel(self, index):
        """Return the pixel positions for a profile."""
        profile = self.get_profile(index)
        if profile is None:
            raise ValueError("Profile is not available")
        return np.arange(len(profile))

    def get_raw_image(self, index):
        """Return the raw image."""
        return self.readers[index].image

    def get_processed_image(self, index):
        """Return the processed image.

        The method should be overridden if
        the processed image is not the same.
        """
        return self.get_raw_image(index)

    def get_metadata(self, key, index):
        """Get metadata entries from all readers."""
        return self.readers[index].metadata[key]

    def analyze(self, **kwargs):
        """Perform the analysis.

        The method is not required if the analyzer does not need to
        work with configuration and workflow logic.
        The analyze method is recommended to be stack analysis
        logic instead of acting on individual readers.

        For large data output, it is recommended for analyze to save
        the result to a file.
        """
        raise NotImplementedError("'analyze' method is not implemented")


Analyzer.REGISTRY[Analyzer.__name__] = Analyzer
