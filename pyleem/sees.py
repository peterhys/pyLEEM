import numpy as np
import matplotlib.pyplot as plt
from pyleem.analysis import ProfileAnalyzer, AnalyzerGroup


def SEES_onset(profile):
    """Determine onset position of secondary electron emission.

    Locates the steepest rise in the profile by finding maximum
    derivative. Extrapolates linear onset back to zero intensity.

    :param ndarray profile: 1D array of secondary electron intensity values.
    :return: Peak index, slope, and onset position in pixels.
    :rtype: tuple(int, float, float)
    """
    profile_derivative = np.gradient(profile)
    slope = np.max(profile_derivative)
    pk_idx = np.argmax(profile_derivative)
    onset_pos = pk_idx - profile[pk_idx] / slope
    return pk_idx, slope, onset_pos


class SEESAnalyzer(ProfileAnalyzer):
    """Analyzer for secondary electron energy spectroscopy data.

    Analyzes SEES profiles to determine surface potentials by measuring
    secondary electron emission onset. Onset shifts with surface charging.

    :param str or Path path: Path to LEEM data file.
    :param dict or LineROI roi: Region of interest for profile extraction.
    :param float sigma: Gaussian filter sigma for smoothing.

    :ivar int pk_idx: Index of steepest rise.
    :ivar float slope: Maximum derivative.
    :ivar float onset_pos: Extrapolated onset position in pixels.
    :ivar float surface_potential: Measured surface potential in V.
    """

    def __init__(self, path, roi, pixel_per_ev, peak_shift, sigma=10):

        super().__init__(path, roi)

        self.sigma = sigma
        filtered_profile = self.filtered_profile(self.sigma)

        self.pk_idx, self.slope, self.onset_pos = SEES_onset(filtered_profile)
        self.KE = (self.pixel - self.onset_pos) / pixel_per_ev

        self._abscissa, self._abscissa_label = self.KE, "Energy [eV]"

        self.potential = peak_shift - (
            self.metadata["Start Voltage"][0] + self.onset_pos / pixel_per_ev
        )

    def plot(self, ax=None, show_fit=False):
        """Plot profile with optional onset fit overlay.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        :param bool show_fit: Whether to show onset fit line.
        """
        ax = ax or plt.gca()
        ax.plot(self.abscissa, self.ordinate, label=self.name)
        if show_fit:
            ax.plot(
                [0, self.abscissa[self.pk_idx]],
                [0, self.ordinate[self.pk_idx]],
                "--",
                label=f"{self.name} fit",
            )
        ax.set_xlabel(self.abscissa_label)
        ax.set_ylabel(self.ordinate_label)


def calibrate_sees(analyzers, cal_params=None, plot=False):
    """Calibrate energy scale using onset positions.

    :param dict cal_params: Calibration parameters.
    :param bool plot: Whether to display calibration plots.
    :return: Calibration results (pixel_per_ev, peak_shift).
    :rtype: dict
    """
    cal_params = cal_params or {}
    sigma = cal_params.get("sigma", 10)

    onset_pos = []
    start_voltages = []
    for analyzer in analyzers:
        onset_pos.append(SEES_onset(analyzer.filtered_profile(sigma))[2])
        start_voltages.append(analyzer.metadata["Start Voltage"][0])
    
    onset_pos = np.array(onset_pos)

    if cal_params.get("pixel_per_ev", None) is None:
        pixel_per_ev = np.mean(np.diff(onset_pos) / -np.diff(start_voltages))
    else:
        pixel_per_ev = cal_params["pixel_per_ev"]

    if cal_params.get("peak_shift", None) is None:
        peak_shift = np.mean(start_voltages + onset_pos / pixel_per_ev)
    else:
        peak_shift = cal_params["peak_shift"]

    if plot:
        _, ax = plt.subplots(1, 1, figsize=(8, 4.5))
        for analyzer in analyzers:
            analyzer.plot(ax, show_fit=True)
        plt.show()

    return {"pixel_per_ev": pixel_per_ev, "peak_shift": peak_shift}


class SEESGroup(AnalyzerGroup):
    """Batch analyzer for multiple SEES profiles.

    Processes multiple SEES measurements acquired at different
    accelerating voltages. Automatically calibrates energy scale.

    Files should be sorted chronologically.

    :param list paths: List of paths to LEEM data files.
    :param dict or LineROI roi: Region of interest for profile extraction.
    :param float sigma: Gaussian filter sigma for smoothing.
    """

    def __init__(self, paths, roi, pixel_per_ev, peak_shift, sigma=10):
        self.analyzers = [
            SEESAnalyzer(path, roi, pixel_per_ev, peak_shift, sigma) for path in paths
        ]
        self.roi = roi
        super().__init__(self.analyzers)
