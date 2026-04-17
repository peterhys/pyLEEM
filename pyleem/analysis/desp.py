from pyleem.analyzer import Analyzer, AnalyzerGroup
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pyleem.config import Config
from lmfit import Model
from functools import partial
from scipy.signal import fftconvolve
from concurrent.futures import ThreadPoolExecutor, as_completed


def preprocess_image(
    image, gaussian_kernel=3, gaussian_sigma=0, use_morph=True, morph_kernel=3
):
    """Preprocess DESP image for disk pattern detection.

    Applies Gaussian blur, normalization, Otsu thresholding, and morphological operations.
    The morphological operations are optional.

    :param ndarray image: Input image array.
    :param int gaussian_kernel: Kernel size for Gaussian blur (must be odd).
    :param float gaussian_sigma: Sigma for Gaussian blur.
    :param bool use_morph: Whether to use morphological operations.
    :param int morph_kernel: Kernel size for morphological operations.
    :return: Processed image as uint8 in 0-255 range.
    :rtype: ndarray
    """

    image_gauss = cv2.GaussianBlur(
        image, (gaussian_kernel, gaussian_kernel), gaussian_sigma
    )
    image_norm = cv2.normalize(image_gauss, None, 0, 255, cv2.NORM_MINMAX).astype(
        np.uint8
    )
    _, image = cv2.threshold(image_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if use_morph:
        kernel = np.ones((morph_kernel, morph_kernel), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    return image


def get_radius(image):
    """Detect and measure the disk pattern in a DESP image.

    In this process we assume that there is only one disk pattern in the image.
    Uses contour detection and minimum enclosing circle to determine center and radius.

    :param ndarray image: Preprocessed DESP image (uint8).
    :return: Disk center (x, y) and radius in pixels.
    :rtype: tuple(float, float, float)
    """

    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    if len(contours) == 0:
        raise ValueError("No disk pattern found in image.")
    (x, y), r = cv2.minEnclosingCircle(largest_contour)
    return x, y, r


def parabola_fit(voltages, radii, window=None):
    """Fit a parabola to the voltages and radii.

    :param list voltages: List of voltages.
    :param list radii: List of radii.
    :param int window: Window size for the fit.
    :return: Fit result.
    :rtype: lmfit.ModelResult
    """

    voltages = np.asarray(voltages)
    radii = np.asarray(radii)

    if window is not None:
        voltages = voltages[window]
        radii = radii[window]

    def model_func(x, a, c):
        return a * x**2 + c

    model = Model(model_func)
    params = model.make_params(a=1e-4, c=0)

    result = model.fit(voltages, params, x=radii)

    fit_func = partial(model_func, **result.best_values)
    return fit_func, result


def calibrate_desp(analyzers, metadata=None, window=None):
    """Calibrate radius to potential using multiple images.

    Uses linear interpolation to map pattern radii to electron energies.
    The disk detection defaults to contour detection.
    The radius of the pattern is related to the square of the voltage.
    The relationship is fitted to a parabola.

    :param list analyzers: List of Analyzer objects.
    :param dict metadata: Optional dictionary with a 'Start Voltage' key whose value
        is a list of voltages. If None, the start voltage is read from each analyzer's metadata.
    :param int window: Window size for the fit.
    :return: Interpolation function mapping radius to potential (radius_to_energy_func).
    :rtype: dict
    """

    radii = []
    start_voltages = [] if metadata is None else metadata["Start Voltage"]
    for analyzer in analyzers:
        _, _, r = get_radius(preprocess_image(analyzer.image))
        radii.append(r)
        if metadata is None:
            start_voltages.append(analyzer.metadata["Start Voltage"][0])

    fit_function, fit_result = parabola_fit(start_voltages, radii, window=window)

    return {"radius_to_energy_func": fit_function, "fit_result": fit_result}


def disk_kernel(radius):
    """Zero-mean filled-disk kernel."""
    r = int(radius)
    y, x = np.ogrid[-r : r + 1, -r : r + 1]
    mask = (x * x + y * y) <= r * r
    k = mask.astype(np.float32)
    k -= k.mean()  # zero-mean => robust to offset
    k /= np.linalg.norm(k) + 1e-12  # normalize
    return k


def match_score(im, radius):
    """Compute the match score for a given radius.

    The correlation map is computed using the FFT.
    """
    k = disk_kernel(radius)
    corr = fftconvolve(im, k[::-1, ::-1], mode="same")
    y, x = np.unravel_index(np.argmax(corr), corr.shape)
    return corr[y, x], x, y, radius


def eval_radii(image, radii, use_threads=True, max_workers=None):
    """Best match over radii, multi-threaded."""
    best = None

    if use_threads:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(match_score, image, r) for r in radii]
            for fut in as_completed(futures):  # the order does not matter
                score, x, y, r_ = fut.result()
                if best is None or score > best[0]:
                    best = (score, x, y, r_)
    else:
        for r in radii:
            score, x, y, r_ = match_score(image, r)
            if best is None or score > best[0]:
                best = (score, x, y, r_)

    return best


def get_radius_convolve(
    image, r_min, r_max, step_size, use_threads=True, max_workers=None
):
    """Get the radius of the disk pattern in the image.

    The image is processed minimualy by subtracting a background.

    :param ndarray image: Input image array.
    :param int r_min: Minimum radius.
    :param int r_max: Maximum radius.
    :param int step_size: Step size.
    :param bool use_threads: Whether to use threads.
    :param int max_workers: Maximum number of workers.
    :return: Best x, y, and radius.
    :rtype: tuple(float, float, float)
    """

    img = image.astype(np.float32)
    bg = cv2.GaussianBlur(img, (0, 0), 40)
    img_subtracted = img - bg

    radii = list(range(int(r_min), int(r_max) + 1, int(step_size)))
    _, x, y, r = eval_radii(img_subtracted, radii, use_threads, max_workers)

    return x, y, r


class DESPConfig(Config):
    """Config for DESP analyzer.

    .. code-block:: toml

        [calibration]
        # a directory containing the files
        path_pattern = "Au_sample/*.dat"
    """

    def calibrate_results(self, cal_section):
        """Calibrate radius to electron energy using multiple images."""
        paths = sorted(self.get_patterned_paths(cal_section["path_pattern"]))
        # assert len(paths) > 0, "No files found in the directory"
        analyzers = [Analyzer(path) for path in paths]
        metadata = cal_section.get("metadata", None)
        window = cal_section.get("window", None)

        return calibrate_desp(analyzers, metadata, window)


class DESPAnalyzer(Analyzer):
    """Analyzer for amorphous DESP patterns.

    Analyzes DESP micrographs to detect circular diffraction patterns
    and measure charging effects through pattern radius changes.

    :param str or Path path: Path to LEEM data file.
    :param callable interp_func: Interpolation function for radius-to-energy conversion.

    :ivar float x: X-coordinate of circle center.
    :ivar float y: Y-coordinate of circle center.
    :ivar float radius: Circle radius in pixels.
    :ivar float energy: Electron energy if interpolation function provided.
    """

    def __init__(self, path, radius_to_energy_func):
        assert callable(
            radius_to_energy_func
        ), "radius_to_energy_func must be a callable"
        super().__init__(path)

        self.x, self.y, self.radius = get_radius(self.processed_image)

        self.energy = radius_to_energy_func(self.radius)
        self.radius_to_energy_func = radius_to_energy_func

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

    def __init__(self, paths, radius_to_energy_func):
        assert len(paths) > 0, "Paths cannot be empty"

        self.analyzers = [DESPAnalyzer(path, radius_to_energy_func) for path in paths]
        self.radius_to_energy_func = radius_to_energy_func
        super().__init__(self.analyzers)

    def plot_energy(self, ax):
        """Plot the energy vs. time.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax.plot(self.time_intervals, self.get_attrs("energy"))
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Electron Energy [eV]")
