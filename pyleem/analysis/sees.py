import numpy as np
import matplotlib.pyplot as plt
from pyleem.analyzer import ProfileAnalyzer, AnalyzerGroup
from pyleem.config import Config


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


def calibrate_sees(analyzers, cal_params, metadata=None):
    """Calibrate energy scale using onset positions."""
    sigma = cal_params.get("sigma", 10)
    onset_pos = []
    start_voltages = [] if metadata is None else metadata["Start Voltage"]
    for analyzer in analyzers:
        onset_pos.append(SEES_onset(analyzer.process_profile(sigma))[2])
        if metadata is None:
            start_voltages.append(analyzer.metadata["Start Voltage"][0])

    onset_pos = np.array(onset_pos)

    pixel_per_ev = cal_params.get("pixel_per_ev", None) or np.mean(
        np.diff(onset_pos) / -np.diff(start_voltages)
    )
    peak_shift = cal_params.get("peak_shift", None) or np.mean(
        start_voltages + onset_pos / pixel_per_ev
    )

    return {"pixel_per_ev": pixel_per_ev, "peak_shift": peak_shift}


class SEESConfig(Config):
    """Config for SEES analyzer."""

    def calibrate_results(self, cal_section):
        """Calibrate energy scale using onset positions."""
        roi = self.get_roi()
        paths = self.get_paths(cal_section["paths"])
        analyzers = [ProfileAnalyzer(path, roi) for path in paths]
        cal_params = cal_section.get("parameters", {})
        metadata = cal_section.get("metadata", None)

        return calibrate_sees(analyzers, cal_params, metadata)


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
        processed_profile = self.process_profile(sigma)

        self.pk_idx, self.slope, self.onset_pos = SEES_onset(processed_profile)
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
