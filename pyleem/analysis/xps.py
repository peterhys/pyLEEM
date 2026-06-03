from lmfit.models import PseudoVoigtModel
import numpy as np
from pyleem.analyzer import ProfileAnalyzer, AnalyzerGroup
import scipy.signal
from pyleem.config import Config


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


def calibrate_xps(analyzers, cal_params, metadata=None):
    """Calibrate pixel_per_eV and peak_shift using multiple spectra."""

    baselines = cal_params["baselines"]
    num_peaks = cal_params["num_peaks"]
    incident_voltage = cal_params["incident_voltage"]
    peak_prominence = cal_params.get("peak_prominence", 0.1)

    pixel_per_ev = cal_params.get("pixel_per_ev", None)
    peak_shift = cal_params.get("peak_shift", None)

    bgs = []
    results = []
    peak_results = []

    for i, analyzer in enumerate(analyzers):
        constraints = parameter_contraint(analyzer.ordinate, num_peaks, peak_prominence)
        peak_labels = [f"p{j}" for j in range(1, num_peaks + 1)]
        result, bg = fit_xps(
            analyzer.ordinate,
            analyzer.pixel,
            baselines[i],
            peak_labels,
            constraints,
        )
        peaks = [v for k, v in result.best_values.items() if "_center" in k]
        results.append(result)
        peak_results.append(peaks)
        bgs.append(bg)

    if metadata is not None:
        start_voltages = np.array(metadata["Start Voltage"])
    else:
        start_voltages = np.array(
            [analyzer.metadata["Start Voltage"][0] for analyzer in analyzers]
        )
    delta_ev = np.diff(start_voltages)

    if "pixel_per_ev" in cal_params:
        pixel_per_ev = cal_params["pixel_per_ev"]
    else:
        # Average over the peaks (the peak splitting should remain the same)
        peak_diff = np.diff(peak_results, axis=0).mean(axis=1)
        pixel_per_ev = np.mean(peak_diff / -delta_ev)

    ref_index = cal_params.get("ref_index", None)
    ref_value = cal_params.get("ref_value", None)

    if "peak_shift" in cal_params:
        peak_shift = cal_params["peak_shift"]
    elif ref_index is None or ref_value is None:
        # No reference peak adjustment
        peak_shift = 0
    else:
        peak_pos = np.array(list(zip(*peak_results))[ref_index]) / pixel_per_ev
        peak_shift = np.mean(incident_voltage - start_voltages - ref_value - peak_pos)

    return {"pixel_per_ev": pixel_per_ev, "peak_shift": peak_shift}


class XPSConfig(Config):
    """Config for XPS analyzer.

    [calibration]
    paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]

    [calibration.parameters]
    baselines = [[197, 100], [197, 100], [197, 100]]
    num_peaks = 1
    incident_voltage = 400
    # optional
    ref_index = 0
    ref_value = 285.0
    peak_prominence = 0.1
    """

    def calibrate_results(self, cal_section):
        """Calibrate pixel_per_eV and peak_shift using multiple spectra.

        Supports calibration with two or more files by analyzing peak
        positions across different accelerating voltages.
        """
        roi = self.get_roi()
        paths = self.get_paths(cal_section["paths"])
        analyzers = [ProfileAnalyzer(path, roi) for path in paths]
        cal_params = cal_section.get("parameters", {})
        metadata = cal_section.get("metadata", None)
        return calibrate_xps(analyzers, cal_params, metadata)


class XPSAnalyzer(ProfileAnalyzer):
    """Analyzer for X-ray photoelectron spectroscopy data.

    Handles energy calibration and provides binding energy scales.

    :param str or Path path: Path to LEEM data file.
    :param dict or LineROI roi: Region of interest for profile extraction.
    :param float incident_voltage: X-ray beam energy.
    """

    def __init__(self, path, roi, pixel_per_ev, peak_shift, incident_voltage):

        super().__init__(path, roi)

        self.metadata["Incident Voltage"] = (incident_voltage, "eV")

        self.KE = (
            self.metadata["Start Voltage"][0] + peak_shift + self.pixel / pixel_per_ev
        )
        self.BE = incident_voltage - self.KE

        self._abscissa, self._abscissa_label = self.BE, "Binding Energy [eV]"

    def fit(self, num_peaks, baseline, peak_prominence=0.1):
        """Fit XPS spectrum with background subtraction.

        :param int num_peaks: Number of peaks to fit.
        :param tuple baseline: Tuple (left, right) background intensities.
        :param float peak_prominence: Peak detection prominence.
        :return: Fit result and Shirley background.
        :rtype: tuple(lmfit.ModelResult, ndarray)
        """

        constraints = parameter_contraint(self.ordinate, num_peaks, peak_prominence)

        # Convert peak positions from pixel space to binding energy space
        for i in range(1, num_peaks + 1):
            pixel_center = constraints[f"p{i}_center"]["value"]
            # Map pixel index to the corresponding x-axis value (binding energy)
            constraints[f"p{i}_center"]["value"] = self.abscissa[int(pixel_center)]

        peak_labels = [f"p{i}" for i in range(1, num_peaks + 1)]

        result, bg = fit_xps(
            self.ordinate, self.abscissa, baseline, peak_labels, constraints
        )

        return result, bg

    def plot_fit(self, axes, result, background):
        """Plot XPS fit results.

        :param tuple axes: Tuple of two axes (profile, residuals).
        :param lmfit.ModelResult result: Fitting result object.
        :param ndarray background: Shirley background array.
        """

        ax_profile, ax_residual = axes
        ax_profile.plot(self.abscissa, self.ordinate, label=f"{self.name} data")
        ax_profile.plot(
            self.abscissa, result.best_fit + background, label=f"{self.name} fit"
        )
        ax_profile.plot(self.abscissa, background, label=f"{self.name} background")
        for prefix, fit_array in result.eval_components().items():
            ax_profile.plot(
                self.abscissa, fit_array + background, label=f"{self.name} {prefix} fit"
            )
        ax_profile.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        ax_profile.set_ylabel(self.ordinate_label)

        ax_residual.set_ylabel("Residuals")
        ax_residual.plot(self.abscissa, result.residual, label=f"{self.name} residuals")
        ax_residual.set_xlabel(self.abscissa_label)
        ax_residual.legend(loc="center left", bbox_to_anchor=(1, 0.5))


class XPSGroup(AnalyzerGroup):
    """Batch analyzer for XPS spectra.

    :param list paths: List of paths to LEEM data files.
    :param dict or LineROI roi: Region of interest for profile extraction.
    :param float incident_voltage: X-ray photon energy in eV.
    """

    def __init__(self, paths, roi, pixel_per_ev, peak_shift, incident_voltage):
        assert len(paths) > 0, "Paths cannot be empty"
        self.analyzers = [
            XPSAnalyzer(path, roi, pixel_per_ev, peak_shift, incident_voltage)
            for path in paths
        ]
        self.incident_voltage = incident_voltage
        self.roi = roi
        super().__init__(self.analyzers)
