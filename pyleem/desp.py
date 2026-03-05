from pyleem.analysis import Analyzer, AnalyzerGroup
import cv2
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt


def preprocess_image(image, gamma=0.5, blur_kernel=5, morph_kernel_size=3):
    """Preprocess DESP image in circular patterns.

    Normalizes image, applies gamma correction for contrast enhancement,
    median blur for noise reduction, and morphological closing.

    :param ndarray image: Input image array.
    :param float gamma: Gamma correction value (< 1 increases contrast).
    :param int blur_kernel: Kernel size for median blur (must be odd).
    :param int morph_kernel_size: Kernel size for morphological operations.
    :return: Processed image as uint8 in 0-255 range.
    :rtype: ndarray
    """
    # normalization
    image_normalized = (image - image.min()) / (image.max() - image.min())
    # gamma color correction
    image_enhanced = np.power(image_normalized, gamma)
    # smoothing while perserve edges
    image_uint8 = (image_enhanced * 255).astype(np.uint8)
    image_processed = cv2.medianBlur(image_uint8, blur_kernel)

    # morphological operations to clean up the gaps in images
    # given that the circle is solid
    kernel = np.ones((morph_kernel_size, morph_kernel_size), np.uint8)
    image_processed = cv2.morphologyEx(image_processed, cv2.MORPH_CLOSE, kernel)

    return image_processed


def get_radius(image):
    """Detect and measure the circular pattern in a DESP image.

    In this process we assume that there is only one circular pattern in the image.
    Uses bilateral filtering, Otsu thresholding, contour detection,
    and minimum enclosing circle to determine center and radius.

    :param ndarray image: Preprocessed DESP image (uint8).
    :return: Circle center (x, y) and radius in pixels.
    :rtype: tuple(int, int, int)
    """

    denoised = cv2.bilateralFilter(image, 15, 100, 100)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # largest contour
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    # Get center from minimum enclosing circle
    (x, y), radius = cv2.minEnclosingCircle(largest_contour)
    return int(x), int(y), int(radius)


class DESPAnalyzer(Analyzer):
    """Analyzer for amorphous DESP patterns.

    Analyzes DESP micrographs to detect circular diffraction patterns
    and measure charging effects through pattern radius changes.

    :param str or Path path: Path to LEEM data file.
    :param callable interp_func: Interpolation function for radius-to-potential conversion.

    :ivar int x: X-coordinate of circle center.
    :ivar int y: Y-coordinate of circle center.
    :ivar int radius: Circle radius in pixels.
    :ivar float potential: Surface potential if interpolation function provided.
    """

    def __init__(self, path, interp_func=None):
        super().__init__(path)

        self.x, self.y, self.radius = get_radius(self.processed_image)

        if interp_func is not None:
            self.potential = interp_func(self.radius).item()
            self.interp_func = interp_func

    @property
    def processed_image(self):
        """Return processed image (not stored due to size)."""
        return preprocess_image(self.image)

    def plot_radius(self, ax):
        """Plot the detected circle on the DESP pattern.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax.imshow(self.processed_image, cmap="gray")
        circle = plt.Circle(
            (self.x, self.y), self.radius, color="r", fill=False, linewidth=2
        )
        ax.add_patch(circle)
        ax.plot(self.x, self.y, "r+", markersize=5)


class DESPGroup(AnalyzerGroup):
    """Batch analyzer for multiple amorphous DESP patterns.

    Processes multiple DESP micrographs and calibrates radius-to-voltage
    relationship using standard patterns with known voltages.

    :param list paths: List of paths to DESP data files.
    :param kwargs: Additional keyword arguments for AnalyzerGroup.
    """

    def __init__(self, paths, **kwargs):
        super().__init__(paths, analyzer=DESPAnalyzer, **kwargs)

    def calibrate(self):
        """Create radius-to-voltage calibration function.

        Uses linear interpolation to map pattern radii to electron energies.

        :return: Interpolation function mapping radius to voltage.
        :rtype: callable
        """
        interp_func = interp1d(
            self.get_attrs("radius"),
            self.get_metas("Start Voltage"),
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate",
        )
        return interp_func

    def plot_potential(self, ax):
        """Plot the potential vs. time.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax.plot(self.time_intervals, self.get_attrs("potential"))
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Potential [V]")
