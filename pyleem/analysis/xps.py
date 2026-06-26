from lmfit.models import PseudoVoigtModel
import numpy as np
from pyleem.analyzer import Analyzer
from pyleem.analysis.spectra import SpectraBase
import scipy.signal
import matplotlib.pyplot as plt


def shirley_background(profile, base_diff, iterations=20, tol=1e-6):
    """Calculate Shirley background for XPS spectra.

    Implements iterative Shirley algorithm for background subtraction.
    Background at each point is proportional to integrated peak area
    toward higher binding energy. Here we simply assume that the x
    axis is in descending BE order.

    Modified from code by Kane O'Donnell.

    :param ndarray profile: Intensity values of spectrum.
    :param float base_diff: Difference between left and right baseline intensities.
    :param int iterations: Maximum iterations.
    :param float tol: Convergence tolerance.
    :return: Calculated background intensity values.
    :rtype: ndarray
    """
    n = len(profile)
    bg = np.zeros(n)
    cumulative_integral = np.empty(n)

    for ite in range(iterations):
        diff = profile - bg

        # Vectorized cumulative integral
        intervals = 0.5 * (diff[:-1] + diff[1:])
        cumulative_integral[n - 1] = 0
        cumulative_integral[-2::-1] = np.cumsum(intervals[::-1])

        total_integral = cumulative_integral[0]

        if abs(total_integral) < 1e-10:
            break

        k = base_diff / total_integral
        bg_new = k * cumulative_integral

        if np.linalg.norm(bg_new - bg) < tol:
            break

        bg = bg_new

    return bg


def pseudo_voigt_fits(peaks, constraints=None):
    """Create composite pseudo-Voigt model for XPS peak fitting.

    Combines multiple pseudo-Voigt peaks (Gaussian-Lorentzian mixture)
    into single fitting model with optional parameter constraints.

    :param list peaks: List of peak identifiers (e.g., ["C1s", "O1s"]).
    :param dict constraints: Parameter constraints for lmfit.
    :return: Composite model and initial parameters.
    :rtype: tuple(lmfit.Model, lmfit.Parameters)
    """

    model_list = []
    constraints = constraints or {}

    for pk in peaks:
        model_list.append(PseudoVoigtModel(prefix=pk + "_"))

    model = np.sum(model_list)

    # Preset parameters to 0 (can be overwritten by constraints)
    for suffix in ["center", "amplitude", "sigma", "fraction"]:
        for pk in peaks:
            model.set_param_hint(pk + "_" + suffix, min=0)

    for key, value in constraints.items():
        model.set_param_hint(key, **value)

    params = model.make_params()
    return model, params


def parameter_estimation(profile, num_peaks, peak_prominence=0.1):
    """Estimate initial parameters for XPS peak fitting.

    Uses scipy peak detection to locate peaks and estimate positions,
    widths, and areas.

    :param ndarray profile: XPS intensity profile.
    :param int num_peaks: Expected number of peaks.
    :param float peak_prominence: Minimum prominence (fraction of max).
    :return: Peak centers, estimated widths, and areas.
    :rtype: tuple(ndarray, ndarray, ndarray)
    """
    # Find peaks
    prominence = max(profile) * peak_prominence
    peaks, _ = scipy.signal.find_peaks(profile, prominence=prominence)

    while len(peaks) > num_peaks:
        prominence = prominence * 1.5
        peaks, _ = scipy.signal.find_peaks(profile, prominence=prominence)

    # Find peak widths
    widths, width_heights, left_ips, right_ips = scipy.signal.peak_widths(
        profile, peaks, rel_height=0.5
    )

    sigmas = np.array(widths) / 2
    # Peak area (by summation)
    peak_areas = np.empty(len(peaks))
    for i, p in enumerate(peaks):
        peak_areas[i] = profile[
            left_ips[i].astype(int) : right_ips[i].astype(int)
        ].sum()

    if len(peaks) < num_peaks:
        if len(peaks) == 1:
            peak = peaks[0]
            peaks = np.array([peak - 0.1 * sigmas[0], peak + 0.1 * sigmas[0]])
            sigmas = np.array([sigmas[0], sigmas[0]])
            peak_areas = np.array([peak_areas[0] / 2, peak_areas[0] / 2])

    return peaks, sigmas, peak_areas


def parameter_contraint(profile, num_peaks, peak_prominence=0.1):
    """Create parameter constraints dictionary for XPS fitting.

    :param ndarray profile: XPS intensity profile.
    :param int num_peaks: Number of peaks to fit.
    :param float peak_prominence: Minimum prominence for detection.
    :return: Constraints dictionary for lmfit.
    :rtype: dict
    """

    centers, sigmas, peak_areas = parameter_estimation(
        profile, num_peaks, peak_prominence
    )

    constr = {}
    for i in range(1, num_peaks + 1):
        constr[f"p{i}_center"] = {"value": centers[i - 1]}
        constr[f"p{i}_amplitude"] = {"value": peak_areas[i - 1]}
        constr[f"p{i}_sigma"] = {"value": sigmas[i - 1]}
    return constr


def fit_xps(profile, abscissa, baseline, peak_labels, constraints):
    """Fit XPS spectrum with Shirley background and pseudo-Voigt peaks.

    :param ndarray profile: XPS intensity profile.
    :param ndarray abscissa: X-axis values (pixels or energy).
    :param tuple baseline: Tuple (left_baseline, right_baseline) intensities.
    :param list peak_labels: List of peak label strings.
    :param dict constraints: Parameter constraints from parameter_contraint().
    :return: Fit result and Shirley background.
    :rtype: tuple(lmfit.ModelResult, ndarray)
    """

    bl_left, bl_right = baseline
    # Background subtraction
    bg = shirley_background(profile, bl_left - bl_right) + bl_right
    sub_profile = profile - bg

    model, param = pseudo_voigt_fits(peak_labels, constraints)

    result = model.fit(sub_profile, x=abscissa, params=param)
    return result, bg


class XPSCalibration(Analyzer):
    """Config for XPS analyzer.

    [reader]
    paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
    metadata = [
        {"Incident Voltage": [400, "eV"]},
        {"Incident Voltage": [400, "eV"]},
        {"Incident Voltage": [400, "eV"]}
    ]

    [task]
    baselines = [[197, 100], [197, 100], [197, 100]]
    num_peaks = 1
    # optional
    ref_index = 0
    ref_value = 285.0
    peak_prominence = 0.1
    """

    save_keys = ("pixel_per_ev", "peak_shift")

    def analyze(
        self,
        num_peaks,
        baselines,
        peak_prominence=0.1,
        pixel_per_ev=None,
        peak_shift=None,
        ref_index=None,
        ref_value=None,
    ):
        """Analyze XPS spectrum with background subtraction.

        :param int num_peaks: Number of peaks to fit.
        :param tuple baseline: Tuple (left, right) background intensities.
        :param float peak_prominence: Peak detection prominence.
        :return: Fit result and Shirley background.
        :rtype: tuple(lmfit.ModelResult, ndarray)
        """

        incident_voltage = np.array(
            [self.get_metadata("Incident Voltage", index)[0] for index in self.indices]
        )
        start_voltages = np.array(
            [self.get_metadata("Start Voltage", index)[0] for index in self.indices]
        )
        delta_ev = np.diff(start_voltages)

        bgs = []
        results = []
        peak_results = []

        for index in self.indices:
            profile = self.get_profile(index)
            pixel = self.get_pixel(index)
            constraints = parameter_contraint(profile, num_peaks, peak_prominence)
            peak_labels = [f"p{j}" for j in range(1, num_peaks + 1)]
            result, bg = fit_xps(
                profile, pixel, baselines[index], peak_labels, constraints
            )
            peaks = [v for k, v in result.best_values.items() if "_center" in k]
            results.append(result)
            peak_results.append(peaks)
            bgs.append(bg)

        if pixel_per_ev is None:
            # Average over the peaks (the peak splitting should remain the same)
            peak_diff = np.diff(peak_results, axis=0).mean(axis=1)
            pixel_per_ev = np.mean(peak_diff / -delta_ev)

        if peak_shift is None:
            if ref_index is None or ref_value is None:
                # No reference peak adjustment
                peak_shift = 0
            else:
                peak_pos = np.array(list(zip(*peak_results))[ref_index]) / pixel_per_ev
                peak_shift = np.mean(
                    incident_voltage - start_voltages - ref_value - peak_pos
                )

        return {"pixel_per_ev": pixel_per_ev, "peak_shift": peak_shift}


class XPSAnalyzer(SpectraBase):
    """Analyzer for X-ray photoelectron spectroscopy data.

    Handles energy calibration and provides binding energy scales.

    :param str or Path path: Path to LEEM data file.
    :param dict or LineROI roi: Region of interest for profile extraction.
    :param float incident_voltage: X-ray beam energy.
    """

    def __init__(self, readers, roi, pixel_per_ev, peak_shift, onset=0):
        super().__init__(
            readers,
            roi=roi,
            onset=onset,
            pixel_per_ev=pixel_per_ev,
            peak_shift=peak_shift,
        )

    def fit(self, index, num_peaks, baseline, peak_prominence=0.1):
        """Fit XPS spectrum with background subtraction.

        :param int num_peaks: Number of peaks to fit.
        :param tuple baseline: Tuple (left, right) background intensities.
        :param float peak_prominence: Peak detection prominence.
        :return: Fit result and Shirley background.
        :rtype: tuple(lmfit.ModelResult, ndarray)
        """

        profile = self.get_profile(index)
        BE = self.get_binding_energy(index)
        constraints = parameter_contraint(profile, num_peaks, peak_prominence)

        # Convert peak positions from pixel space to binding energy space
        for i in range(1, num_peaks + 1):
            pixel_center = constraints[f"p{i}_center"]["value"]
            # Map pixel index to the corresponding x-axis value (binding energy)
            constraints[f"p{i}_center"]["value"] = BE[int(pixel_center)]

        peak_labels = [f"p{i}" for i in range(1, num_peaks + 1)]

        result, bg = fit_xps(profile, BE, baseline, peak_labels, constraints)

        return result, bg

    def get_binding_energy(self, index):
        """Return the binding energy for a given index."""
        kinetic_energy = self.get_kinetic_energy(index)
        incident_voltage = self.get_metadata("Incident Voltage", index)[0]
        return incident_voltage - kinetic_energy

    def plot_profile(self, index, ax=None, show_fit=False, **kwargs):
        """Plot XPS fit results.

        :param tuple axes: Tuple of two axes (profile, residuals).
        :param lmfit.ModelResult result: Fitting result object.
        :param ndarray background: Shirley background array.
        """

        ax = ax or plt.gca()

        profile = self.get_profile(index)
        binding_energy = self.get_binding_energy(index)

        ax.plot(binding_energy, profile, label="data")
        ax.set_ylabel("Intensity")
        ax.set_xlabel("Binding Energy [eV]")

        if show_fit:

            ax.figure.subplots_adjust(bottom=0.35)
            ax_res = ax.inset_axes([0.0, -0.35, 1.0, 0.25])

            result, background = self.fit(index, **kwargs)
            ax.plot(binding_energy, result.best_fit + background, label="fit")
            ax.plot(binding_energy, background, label="background")
            for prefix, fit_array in result.eval_components().items():
                ax.plot(binding_energy, fit_array + background, label=f"{prefix} fit")
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

            ax_res.set_ylabel("Residual Intensity")
            ax_res.plot(binding_energy, result.residual, label="residual")
            ax_res.set_xlabel("Binding Energy [eV]")
            ax_res.legend(loc="center left", bbox_to_anchor=(1, 0.5))

        return ax
