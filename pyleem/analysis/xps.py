from lmfit.models import PseudoVoigtModel
import numpy as np
from pyleem.analyzer import Analyzer
from pyleem.analysis.spectra import SpectraBase
import scipy.ndimage
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


def pseudo_voigt_fits(peak_constraints):
    """Create composite pseudo-Voigt model for XPS peak fitting.

    Combines multiple pseudo-Voigt peaks (Gaussian-Lorentzian mixture)
    into single fitting model with optional parameter constraints.

    The constraints are nested dictionaries with the following structure:

    Example::

        {
            "label": {
                "param": {"value": value, "min": min, "max": max, "vary": vary}
            }
        }

    :param dict peak_constraints: Dictionary of peak constraints for lmfit.
    :return: Composite model and initial parameters.
    :rtype: tuple(lmfit.Model, lmfit.Parameters)
    """

    if not peak_constraints:
        raise ValueError("peak_constraints must contain at least one peak")

    model_list = []
    for label in peak_constraints:
        model_list.append(PseudoVoigtModel(prefix=label + "_"))

    model = np.sum(model_list)

    default_hints = {
        "center": {"min": 0},
        "amplitude": {"min": 0},
        "sigma": {"min": 0},
        "fraction": {"min": 0, "max": 1},
    }

    for label, constraints in peak_constraints.items():
        for param_name, defaults in default_hints.items():
            default_hint = defaults.copy()
            default_hint.update(constraints.get(param_name, {}))
            model.set_param_hint(label + "_" + param_name, **default_hint)

    params = model.make_params()
    return model, params


def parameter_estimation(
    profile,
    abscissa,
    num_peaks,
    peak_prominence=0.1,
    smooth_sigma=None,
):
    """Estimate initial parameters for XPS peak fitting.

    Uses scipy peak detection to locate peaks and estimate positions,
    widths, and areas. The values are estimates for automatic fitting.

    :param ndarray profile: XPS intensity profile.
    :param ndarray abscissa: XPS binding energy abscissa.
    :param int num_peaks: Expected number of peaks.
    :param float peak_prominence: Minimum prominence as a fraction of signal range.
    :param int smooth_sigma: Optional Gaussian smoothing sigma for detection.
    :return: Peak centers, estimated widths, and areas.
    :rtype: tuple(ndarray, ndarray, ndarray)
    """

    if num_peaks < 1:
        raise ValueError("num_peaks must be at least 1")

    profile = np.asarray(profile)

    if smooth_sigma is not None:
        smoothed_profile = scipy.ndimage.gaussian_filter1d(profile, smooth_sigma)
    else:
        smoothed_profile = profile
    prominence = peak_prominence * np.ptp(smoothed_profile)
    peaks, _ = scipy.signal.find_peaks(smoothed_profile, prominence=prominence)

    # Find peak widths
    widths, width_heights, left_ips, right_ips = scipy.signal.peak_widths(
        profile, peaks, rel_height=0.5
    )

    # skip the peak that is too narrow (needs to be larger than 1 pixel)
    valid = widths >= 2
    peaks = peaks[valid]
    widths = widths[valid]
    left_ips = left_ips[valid]
    right_ips = right_ips[valid]

    # if no peaks are found, would raise an error as well because num_peaks
    # is required to be at least 1.
    if len(peaks) < num_peaks:
        raise ValueError(f"found {len(peaks)} peaks, but expected {num_peaks}")

    abscissa_per_pixel = np.abs(np.diff(abscissa)).mean()
    sigmas = widths / 2 * abscissa_per_pixel

    # Here we first calculate the FWHM area and then estimate the full area
    # with a correction factor of 1.3176 (rough estimate)
    # This is assuming a 0.5 fraction of Gaussian and 0.5 fraction of Lorentzian.
    peak_areas = np.empty(len(peaks))
    for i, peak in enumerate(peaks):
        left = max(0, int(np.floor(left_ips[i])))
        right = min(len(profile), int(np.ceil(right_ips[i])))

        peak_areas[i] = profile[left:right].sum() * abscissa_per_pixel * 1.3176

    return abscissa[peaks], sigmas, peak_areas


def parameter_constraint(
    profile, abscissa, num_peaks, peak_prominence=0.1, smooth_sigma=None
):
    """Create parameter constraints dictionary for XPS fitting.

    :param ndarray profile: XPS intensity profile.
    :param int num_peaks: Number of peaks to fit.
    :param float peak_prominence: Minimum prominence as a fraction of signal range.
    :param float smooth_sigma: Optional Gaussian smoothing sigma for detection.
    :return: Constraints dictionary for lmfit.
    :rtype: dict
    """

    centers, sigmas, peak_areas = parameter_estimation(
        profile, abscissa, num_peaks, peak_prominence, smooth_sigma=smooth_sigma
    )

    constr = {}
    for i in range(1, num_peaks + 1):
        constr[f"p{i}"] = {
            "center": {"value": centers[i - 1]},
            "amplitude": {"value": peak_areas[i - 1]},
            "sigma": {"value": sigmas[i - 1]},
        }
    return constr


def xps_background(profile, baseline=None, baseline_average=10):
    """Calculate the Shirley background with baseline offset."""
    if baseline is None:
        baseline = [
            profile[:baseline_average].mean(),
            profile[-baseline_average:].mean(),
        ]

    bl_left, bl_right = baseline
    return shirley_background(profile, bl_left - bl_right) + bl_right


def fit_range_mask(abscissa, fit_range=None):
    """Return a boolean mask for a fit range.

    The fit range is a tuple of (left, right) values.
    """
    abscissa = np.asarray(abscissa)

    if fit_range is None:
        return np.ones(abscissa.shape, dtype=bool)

    low, high = sorted(fit_range)
    return (abscissa >= low) & (abscissa <= high)


def fit_xps(
    profile,
    abscissa,
    baseline=None,
    baseline_average=10,
    num_peaks=None,
    peak_prominence=0.1,
    peak_constraints=None,
    fit_range=None,
    smooth_sigma=None,
):
    """Fit an XPS profile with automatic or manual peak constraints.

    If peak_constraints is provided, those manual constraints define the peaks.
    Otherwise, num_peaks controls automatic detection on the
    background-subtracted signal. fit_range selects the region used for the
    Shirley background.
    """
    profile = np.asarray(profile)
    abscissa = np.asarray(abscissa)

    if profile.shape != abscissa.shape:
        raise ValueError("profile and abscissa must have the same shape")

    if peak_constraints is not None and num_peaks is not None:
        raise ValueError("provide either peak_constraints or num_peaks, not both")

    if peak_constraints is None and num_peaks is None:
        raise ValueError("provide peak_constraints or num_peaks")

    range_mask = fit_range_mask(abscissa, fit_range=fit_range)

    range_profile = profile[range_mask]
    range_abscissa = abscissa[range_mask]
    background = xps_background(range_profile, baseline, baseline_average)
    sub_profile = range_profile - background

    if peak_constraints is None:
        peak_constraints = parameter_constraint(
            sub_profile,
            range_abscissa,
            num_peaks,
            peak_prominence,
            smooth_sigma=smooth_sigma,
        )

    model, params = pseudo_voigt_fits(peak_constraints)
    result = model.fit(sub_profile, x=range_abscissa, params=params)

    return {
        "range_mask": range_mask,
        "range_profile": range_profile,
        "range_abscissa": range_abscissa,
        "background": background,
        "sub_profile": sub_profile,
        "peak_constraints": peak_constraints,
        "peak_labels": list(peak_constraints.keys()),
        "result": result,
    }


class XPSCalibration(Analyzer):
    """Config for XPS analyzer.

    Configuration files are recommended due to the complexity of the analysis.

    .. code-block:: toml

        [reader]
        paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]
        metadata = [
            {"Beam Energy" = [400, "eV"]},
            {"Beam Energy" = [400, "eV"]},
            {"Beam Energy" = [400, "eV"]},
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
        pixel_per_ev=None,
        peak_shift=None,
        ref_index=None,
        ref_value=None,
        **fit_kwargs,
    ):
        """Analyze XPS spectrum with background subtraction.

        :param int num_peaks: Number of peaks to fit.
        :param tuple baseline: Tuple (left, right) background intensities.
        :param float peak_prominence: Peak detection prominence.
        :return: Fit result and Shirley background.
        :rtype: tuple(lmfit.ModelResult, ndarray)
        """

        incident_voltage = np.array(
            [self.get_metadata("Beam Energy", index)[0] for index in self.indices]
        )
        start_voltages = np.array(
            [self.get_metadata("Start Voltage", index)[0] for index in self.indices]
        )
        delta_ev = np.diff(start_voltages)

        peak_results = []

        for index in self.indices:
            profile = self.get_profile(index)
            pixel = self.get_pixel(index)
            fit_result = fit_xps(
                profile,
                pixel,
                num_peaks=num_peaks,
                baseline=baselines[index],
                **fit_kwargs,
            )
            peaks = [
                fit_result["result"].best_values[f"{label}_center"]
                for label in fit_result["peak_labels"]
            ]
            peak_results.append(peaks)

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

    :param list readers: List of readers.
    :param ROI roi: Region of interest for profile extraction.
    :param float pixel_per_ev: Pixel per eV.
    :param float peak_shift: Peak shift.
    :param int onset: Onset index.
    """

    def __init__(self, readers, roi, pixel_per_ev, peak_shift, onset=0):
        super().__init__(
            readers,
            roi=roi,
            onset=onset,
            pixel_per_ev=pixel_per_ev,
            peak_shift=peak_shift,
        )

    def fit(
        self,
        index,
        num_peaks=None,
        baseline=None,
        peak_prominence=0.1,
        peak_constraints=None,
        fit_range=None,
        smooth_sigma=None,
    ):
        """Fit XPS spectrum with background subtraction.

        :param int num_peaks: Number of peaks to fit.
        :param tuple baseline: Tuple (left, right) background intensities.
        :param float peak_prominence: Peak detection prominence fraction.
        :param dict peak_constraints: Optional manual peak constraints.
        :param tuple fit_range: Optional range to use for background and fitting.
        :param float smooth_sigma: Optional Gaussian smoothing sigma.
        :return: Fit result.
        :rtype: dict
        """

        profile = self.get_profile(index)
        BE = self.get_binding_energy(index)

        fit_result = fit_xps(
            profile,
            BE,
            baseline=baseline,
            num_peaks=num_peaks,
            peak_prominence=peak_prominence,
            peak_constraints=peak_constraints,
            fit_range=fit_range,
            smooth_sigma=smooth_sigma,
        )

        return fit_result

    def get_binding_energy(self, index):
        """Return the binding energy for a given index."""
        kinetic_energy = self.get_kinetic_energy(index)
        incident_voltage = self.get_metadata("Beam Energy", index)[0]
        return incident_voltage - kinetic_energy

    def plot_profile(self, index, ax=None, show_fit=False, **fit_kwargs):
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

        if show_fit:

            ax.figure.subplots_adjust(bottom=0.35)
            ax_res = ax.inset_axes([0.0, -0.35, 1.0, 0.25])
            ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

            fit_result = self.fit(index, **fit_kwargs)
            ax.plot(
                fit_result["range_abscissa"],
                fit_result["result"].best_fit + fit_result["background"],
                label="fit",
            )
            ax.plot(
                fit_result["range_abscissa"],
                fit_result["background"],
                label="background",
            )
            for label, fit_array in fit_result["result"].eval_components().items():
                ax.plot(
                    fit_result["range_abscissa"],
                    fit_array + fit_result["background"],
                    label=f"{label} fit",
                )
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

            ax_res.set_ylabel("Residual")
            ax_res.plot(
                fit_result["range_abscissa"],
                fit_result["result"].residual,
                label="residual",
            )
            ax_res.set_xlabel("Binding Energy [eV]")
            ax_res.invert_xaxis()
            ax_res.legend(loc="center left", bbox_to_anchor=(1, 0.5))

        else:
            ax.set_xlabel("Binding Energy [eV]")

        return ax
