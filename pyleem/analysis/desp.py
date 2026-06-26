import cv2
import numpy as np
import matplotlib.pyplot as plt
from pyleem.analyzer import Analyzer
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

    return result


def disk_kernel(radius):
    """Build a zero-mean filled-disk kernel."""
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
    """Find the best match over radii using multiple threads."""
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

    The image is processed minimally by subtracting a background.

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


class DESPAnalyzerBase(Analyzer):
    """Base class for DESP analyzer."""

    def __init__(
        self,
        readers,
        roi=None,
        onset=0,
        gaussian_kernel=3,
        gaussian_sigma=0,
        use_morph=True,
        morph_kernel=3,
    ):
        super().__init__(readers, roi=roi, onset=onset)
        self.gaussian_kernel = gaussian_kernel
        self.gaussian_sigma = gaussian_sigma
        self.use_morph = use_morph
        self.morph_kernel = morph_kernel

    def get_processed_image(self, index):
        """Return the processed image."""
        return preprocess_image(
            self.get_raw_image(index),
            gaussian_kernel=self.gaussian_kernel,
            gaussian_sigma=self.gaussian_sigma,
            use_morph=self.use_morph,
            morph_kernel=self.morph_kernel,
        )

    def get_energy_convert_function(self, params):
        """Return the energy conversion function."""

        def model_func(x, a, c):
            return a * x**2 + c

        return partial(model_func, **params)


class DESPCalibration(DESPAnalyzerBase):
    """Calibration analyzer for DESP patterns."""

    save_keys = ("parabola_params",)

    def analyze(self, window):
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
        start_voltages = []
        for index in self.indices:
            _, _, r = get_radius(self.get_image(index, "processed"))
            radii.append(r)
            start_voltages.append(self.get_metadata("Start Voltage", index)[0])

        fit_result = parabola_fit(start_voltages, radii, window=window)

        return {
            "parabola_params": dict(fit_result.best_values),
            "fit_result": fit_result,
            "radii": radii,
        }


class DESPAnalyzer(DESPAnalyzerBase):
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

    def __init__(self, readers, parabola_params, roi=None, **parameters):
        super().__init__(readers, roi=roi, **parameters)

        self.parabola_params = parabola_params
        self.convert_to_energy = self.get_energy_convert_function(parabola_params)

        self.x_array = []
        self.y_array = []
        self.radii_array = []
        self.energy_array = []

        for index in self.indices:
            x, y, r = get_radius(self.get_image(index, "processed"))
            self.x_array.append(x)
            self.y_array.append(y)
            self.radii_array.append(r)
            self.energy_array.append(self.convert_to_energy(r))

    def annotate_image(self, index, ax):
        """Annotate DESP radius and energy on an image axes."""
        x = self.x_array[index]
        y = self.y_array[index]
        radius = self.radii_array[index]
        energy = self.energy_array[index]

        circle = plt.Circle((x, y), radius, color="r", fill=False, linewidth=2)
        ax.add_patch(circle)
        ax.plot(x, y, "r+", markersize=5)

        text = f"radius = {radius:.2f} px\nenergy = {energy:.2f} eV"
        ax.text(
            0.03,
            0.97,
            text,
            transform=ax.transAxes,
            ha="left",
            va="top",
            color="white",
            fontsize=10,
            bbox={"facecolor": "black", "alpha": 0.6, "edgecolor": "none", "pad": 4},
        )

        return ax

    def plot_energy(self, ax=None):
        """Plot the energy vs. time.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        """
        ax = ax or plt.gca()
        time_intervals = [reader.metadata["TimeInterval"][0] for reader in self.readers]
        ax.plot(time_intervals, self.energy_array)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Electron Energy [eV]")

        return ax
