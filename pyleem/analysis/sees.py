import numpy as np
import matplotlib.pyplot as plt
from pyleem.analyzer import Analyzer
from scipy.ndimage import gaussian_filter


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


class SEESBase(Analyzer):
    """Base class for SEES analyzer."""

    def get_processed_profile(self, index, sigma):
        """Return the processed profile."""
        return gaussian_filter(self.get_profile(index), sigma=sigma)


class SEESCalibration(SEESBase):
    """Config for SEES analyzer."""

    save_keys = ("pixel_per_ev", "peak_shift")

    def analyze(self, sigma=10, pixel_per_ev=None, peak_shift=None):
        """Calibration of the SEES analyzer."""
        onset_pos = []
        start_voltages = np.array(
            [self.get_metadata("Start Voltage", index)[0] for index in self.indices]
        )
        for index in self.indices:
            profile = self.get_processed_profile(index, sigma)
            onset_pos.append(SEES_onset(profile)[2])

        onset_pos = np.array(onset_pos)

        if pixel_per_ev is None:
            pixel_per_ev = np.mean(np.diff(onset_pos) / -np.diff(start_voltages))
        if peak_shift is None:
            peak_shift = np.mean(start_voltages + onset_pos / pixel_per_ev)

        return {"pixel_per_ev": pixel_per_ev, "peak_shift": peak_shift}


class SEESAnalyzer(SEESBase):
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

    def __init__(self, readers, roi, pixel_per_ev, peak_shift, onset=0, sigma=10):
        super().__init__(readers, roi=roi, onset=onset)

        self.pixel_per_ev = pixel_per_ev
        self.peak_shift = peak_shift
        self.sigma = sigma

    def analyze_profile(self, index):
        """Analyze a profile."""
        profile = self.get_processed_profile(index, self.sigma)
        pk_idx, slope, onset_pos = SEES_onset(profile)
        kinetic_energy = (self.get_pixel(index) - onset_pos) / self.pixel_per_ev
        surface_potential = self.peak_shift - (
            self.get_metadata("Start Voltage", index)[0] + onset_pos / self.pixel_per_ev
        )

        return {
            "kinetic_energy": kinetic_energy,
            "surface_potential": surface_potential,
            "onset_pos": onset_pos,
            "pk_idx": pk_idx,
            "slope": slope,
        }

    def plot_profile(self, ax=None, show_fit=False, index=0):
        """Plot profile with optional onset fit overlay.

        :param matplotlib.axes.Axes ax: Matplotlib axes object.
        :param bool show_fit: Whether to show onset fit line.
        """

        result = self.analyze_profile(index, self.sigma)
        profile = self.get_profile(index)

        ax = ax or plt.gca()

        ax.plot(result["kinetic_energy"], profile)
        if show_fit:
            ax.plot(
                [0, result["kinetic_energy"][result["pk_idx"]]],
                [0, profile[result["pk_idx"]]],
                "--",
                label="fit",
            )
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_xlabel("Energy [eV]")
        ax.set_ylabel("Intensity")

        return ax

