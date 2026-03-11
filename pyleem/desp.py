from pyleem.analysis import Analyzer, AnalyzerGroup
import cv2
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from pyleem.config import Config


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
    :rtype: tuple(float, float, float)
    """

    denoised = cv2.bilateralFilter(image, 15, 100, 100)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # largest contour
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    # Get center from minimum enclosing circle
    (x, y), radius = cv2.minEnclosingCircle(largest_contour)
    return x, y, radius


def calibrate_desp(analyzers):
    """Calibrate radius to potential using multiple images.

    Uses linear interpolation to map pattern radii to electron energies.

    :param list analyzers: List of Analyzer objects.
    :param dict cal_params: Dictionary with 'paths' and 'parameters'.
    :return: Interpolation function mapping radius to potential (potential_func).
    :rtype: dict
    """

    radii = []
    start_voltages = []
    for analyzer in analyzers:
        image = preprocess_image(analyzer.image)
        x, y, radius = get_radius(image)
        radii.append(radius)
        start_voltages.append(analyzer.metadata["Start Voltage"][0])

    interp_func = interp1d(
        radii,
        start_voltages,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )

    return {"potential_func": interp_func}


class DESPConfig(Config):
    """Config for DESP analyzer.

    [calibration]
    # a directory containing the files
    path_pattern = "Au_sample/*.dat"
    """

    def calibrate_results(self, cal_section):
        """Calibrate radius to potential using multiple images."""
        paths = sorted(self.get_patterned_paths(cal_section["path_pattern"]))
        # assert len(paths) > 0, "No files found in the directory"
        analyzers = [Analyzer(path) for path in paths]

        return calibrate_desp(analyzers)


class DESPAnalyzer(Analyzer):
    """Analyzer for amorphous DESP patterns.

    Analyzes DESP micrographs to detect circular diffraction patterns
    and measure charging effects through pattern radius changes.

    :param str or Path path: Path to LEEM data file.
    :param callable interp_func: Interpolation function for radius-to-potential conversion.

    :ivar float x: X-coordinate of circle center.
    :ivar float y: Y-coordinate of circle center.
    :ivar float radius: Circle radius in pixels.
    :ivar float potential: Surface potential if interpolation function provided.
    """

    def __init__(self, path, potential_func):
        assert callable(potential_func), "potential_func must be a callable"
        super().__init__(path)

        self.x, self.y, self.radius = get_radius(self.processed_image)

        self.potential = potential_func(self.radius)
        self.potential_func = potential_func

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

    def __init__(self, paths, potential_func):
        assert len(paths) > 0, "Paths cannot be empty"

        self.analyzers = [DESPAnalyzer(path, potential_func) for path in paths]
        self.potential_func = potential_func
        super().__init__(self.analyzers)

    def plot_potential(self, ax):
        """Plot the potential vs. time.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax.plot(self.time_intervals, self.get_attrs("potential"))
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Potential [V]")
