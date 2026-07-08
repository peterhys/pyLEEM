import matplotlib.pyplot as plt
from pyleem.roi import NoROI
import numpy as np


class Analyzer:
    """Base analyzer class for LEEM data analysis.

    Provides core functionality for domain-specific LEEM analysis.
    Raw images come from readers. Processed images default to raw images.
    Annotated images default to processed images.

    All variable access should be index aware.

    :param iterable readers: Reader objects used by the analyzer.
    :ivar list readers: List of readers.
    :ivar ROI roi: ROI for measuring the image.
    """

    REGISTRY = {}

    def __init_subclass__(cls, **kwargs):
        """Register the analyzer class in the registry."""
        super().__init_subclass__(**kwargs)
        cls.REGISTRY[cls.__name__] = cls

    def __init__(self, readers, roi=None):

        if not readers:
            raise ValueError("readers cannot be empty")

        self.readers = readers

        self.roi = roi or NoROI()
        self.indices = range(len(self.readers))

    def annotate_image(self, index, ax):
        """Annotate the image for matplotlib plotting.

        Override to annotate the image. Currently, the annotate_image method
        does not take additional arguments. The idea is that the whole image
        stack should be annotated the same way.
        """
        return ax

    def get_autolevel(self, image):
        """Return percentile display limits for image contrast."""

        vmin, vmax = np.percentile(image, [1, 99])
        if vmin == vmax:
            # in case the image is uniform
            return float(vmin) - 0.5, float(vmax) + 0.5

        return float(vmin), float(vmax)

    def plot_image(self, index, ax=None, annotate=False, autolevel=False):
        """Plot image data.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        :param bool autolevel: auto leveling the image. Act as auto-contrast.
        """
        ax = ax or plt.gca()

        image = self.get_processed_image(index)
        if autolevel:
            vmin, vmax = self.get_autolevel(image)
            ax.imshow(image, vmin=vmin, vmax=vmax)
        else:
            ax.imshow(image)

        if annotate:
            self.annotate_image(index, ax)

        ax.set_xlabel("X [pixels]")
        ax.set_ylabel("Y [pixels]")
        ax.set_title("Image Data")

        return ax

    def get_measurement(self, index):
        """Measure the image data."""
        image = self.get_processed_image(index)

        return self.roi.measure(image)

    def get_profile(self, index):
        """Extract the line profile from the image data."""
        return self.get_measurement(index).profile

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
