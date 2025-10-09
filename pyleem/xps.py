"""Functions for XPS analysis."""

import re
import os
from lmfit.models import PseudoVoigtModel
import numpy as np
import pandas as pd

from itertools import zip_longest
from pyleem.reader import RawReader
import scipy.signal
import scipy.ndimage
import skimage
import skimage.measure
import matplotlib.pyplot as plt
from datetime import datetime


def shirley_background(y, dx, base_diff, iterations=20, tol=1e-6):
    """Shirley background calculation.

    The following code is modified based on the code from Kane O'Donnell.
    Here we modify the background subtraction to two steps:
    1. Calculate the constant shift of the background.
    2. Iteratively calculate the Shirley background.

    Because of the noise, here

    :param ndarray dx: The step size of the x-axis.
    :param ndarray y: The intensity of the peak, corresponding to the x.
    :param float base_diff: The difference between the left and right base of the peak background.
    :param int iterations: Th max number of iterations to perform.
    """
    ite = 0
    y = np.array(y)
    n = len(y)
    bg = np.zeros(n)
    peak_sum = np.trapezoid(y, dx=dx)
    k = (
        base_diff / peak_sum
    )  # initial guess that uses the whole peak region (since we assume bg is 0)

    while ite < iterations:

        # calculate the integral
        diff = y - bg
        diff[0] = 0.5 * (diff[0])
        diff[-1] = 0.5 * (diff[-1])
        bg_new = dx * np.cumsum(diff[::-1])[::-1] * k
        if np.linalg.norm(bg_new - bg) < tol:
            # print(f"Converged after {ite} iterations.")
            break
        else:
            bg = bg_new
        ite += 1

    return bg


def pseudo_voigt_fits(peaks, constraints=None):
    """Create XPS model for XPS fitting.

    :param list peaks: The list of peaks to fit. The peak should be a string.
    :param dict constraints: The constraints for the parameter fitting.
    """

    model_list = []
    constraints = constraints or {}

    for pk in peaks:
        model_list.append(PseudoVoigtModel(prefix=pk + "_"))

    model = np.sum(model_list)

    # preset parameters to 0
    # can be overwritten by the constraints
    for suffix in ["center", "amplitude", "sigma", "fraction"]:
        for pk in peaks:
            model.set_param_hint(pk + "_" + suffix, min=0)

    for key, value in constraints.items():
        model.set_param_hint(key, **value)

    params = model.make_params()
    return model, params


def plot_xps_fits(
    ax,
    res_ax,
    x,
    y,
    bg,
    result,
    title="",
    xlabel="Binding Energy [eV]",
    inverted=True,
):
    """Plot the XPS fits.

    :param ax: The axis to plot the data.
    :param res_ax: The axis to plot the residuals.
    :param ndarray x: The x-axis data.
    :param ndarray y: The y-axis data.
    :param model: The model to fit.
    :param params: The parameters for the model.
    :param result: The result of the fitting.
    :param str title: The title of the plot.
    """
    ax.plot(x, y, label="experimental data")
    ax.plot(x, result.best_fit + bg, label="total fit")
    ax.plot(x, bg, label="background")
    for prefix, fit_array in result.eval_components().items():
        ax.plot(x, fit_array + bg, label=f"{prefix}fit")
    ax.set_title(title)
    ax.legend()

    ax.set_ylabel("Intensity")
    res_ax.set_ylabel("Residuals")
    res_ax.plot(x, result.residual, label="residuals")
    res_ax.set_xlabel(xlabel)

    if inverted:
        ax.invert_xaxis()
        res_ax.invert_xaxis()


def df_fit_result(results, area=False, uncertainty=True):
    """Output the fitting results.

    :param results: The fitting results.
    :param bool area: If True, then calculate the area of the peak.
    :param bool uncertainty: If True, then include the uncertainty in the fitting.
    """
    report_list = []
    for label, r in results:

        report_dict = {"Sample": label}
        if hasattr(r, "uvars") and uncertainty:
            report_dict.update(r.uvars)
        else:
            report_dict.update(r.params.valuesdict())
        if area:
            area = []
            for key, value in r.params.items():
                if "amplitude" in key:
                    label = key.replace("_amplitude", "_area")
                    area.append([label, r.params[key].value])
            total_area = sum(list(zip(*area))[1])
            for label, value in area:
                report_dict[label] = value / total_area
        report_dict["Reduced_chi"] = r.redchi

        report_list.append(report_dict)

    report_df = pd.DataFrame(report_list)
    report_df = report_df.set_index("Sample")
    return report_df


FILE_FORMAT = re.compile(
    # 20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C
    # position is optional
    # regex returns None if position is not present
    r"(\d{8})_XPS_Sample(\d)_([A-Z]{1,2})_(\d[A-Z]{2})_"
    r"(\d{1,4})eV_(\d{1,4})eV_([A-Za-z]{1,2}\d[a-z])_?([A-Z]\d{0,1})?"
)
FILE_KEYS = [
    ("date", str),
    ("sample", str),
    ("condition", str),
    ("aperture", str),
    ("incident_voltage", float),
    ("start_voltage", float),
    ("element", str),
    ("position", str),  # optional
]


def parse_filename(file, file_format=FILE_FORMAT, file_keys=FILE_KEYS):
    """Parse the filename based on the file format.

    Currently, some experiment metadata is encoded in the filename.
    """
    basefile = os.path.basename(file)
    match = file_format.match(basefile)
    if match:
        file_info = {"filename": file}
        for (key, tp), value in zip_longest(file_keys, match.groups()):
            file_info[key] = tp(value)
        return file_info
    else:
        raise ValueError(f"File name {file} does not match the expected format")


def read_profile(file, incident_voltage, start_voltage, pixperev, peak_shift):
    """Read XPS profile data.

    This function supports two different types of csv file style.
    The plot profile directly from ImageJ.
    And the data exported using the ROIProfile plugin in ImageJ.
    If more than two columns are detected, then only grab the last
    two columns.
    """

    df = pd.read_csv(file, header=0)
    if df.shape[1] > 2:
        df = df.iloc[:, -2:]
    df.columns = ["pixel", "intensity"]
    df["kinetic energy"] = start_voltage + peak_shift + df["pixel"] / pixperev
    df["binding energy"] = incident_voltage - df["kinetic energy"]
    return df


def profile_roi(image, roi, incident_voltage, start_voltage, pixel_per_ev, peak_shift):
    """Profile the image based on the ROI object."""

    profile = skimage.measure.profile_line(image, **roi)
    pixel = np.arange(len(profile))
    ke = start_voltage + peak_shift + pixel / pixel_per_ev
    df = pd.DataFrame(
        {
            "intensity": profile,
            "pixel": np.arange(len(profile)),
            "kinetic energy": ke,
            "binding energy": incident_voltage - ke,
        }
    )

    return df


class XPSReader(RawReader):
    """Read XPS specific LEEM raw data.

    The class reads the raw data, parses filename,
    and profile the XPS data. Currently it does not allow
    custom tags.

    For file that is not the standard foramt, use a custom
    file function for parse_func. The parsed dictionary
    has to have "incident_voltage" and "start_voltage" keys.

    TODO:
        - Consider check the start voltage against metadata.

    """

    def __init__(self, path, roi, pixel_per_ev, peak_shift, parse_func=parse_filename):
        super().__init__(path)
        self.info = parse_func(path)
        self.roi = roi

        # by default the start voltage is based on the filename
        # assert self.file_info["start_voltage"] == self.imgmeta['Start Voltage'][0]

        self.profile = profile_roi(
            self.read_image(),
            roi,
            self.info["incident_voltage"],
            self.info["start_voltage"],
            pixel_per_ev,
            peak_shift,
        )

    def custom_h5(self, group):
        """Add XPS specific metadata to the h5 group.

        Create the profile group and add the roi and profile data.
        The dimension is set to be the binding energy.
        """

        group.attrs.update({k: v for k, v in self.info.items() if v})
        profile_group = group.create_group("profile")
        intensity = profile_group.create_dataset(
            "intensity", data=self.profile["intensity"]
        )

        be = profile_group.create_dataset(
            "binding energy", data=self.profile["binding energy"]
        )
        be.attrs["unit"] = "eV"
        be.make_scale()

        intensity.dims[0].label = "binding energy"
        intensity.dims[0].attach_scale(be)

        self.roi.to_h5(profile_group)


def parameter_estimation(profile, num_peaks, peak_prominence=0.1):
    """Vary crude way to estimate parameters for peak fitting."""
    # find peaks
    prominence = max(profile) * peak_prominence
    peaks, _ = scipy.signal.find_peaks(profile, prominence=prominence)

    while len(peaks) > num_peaks:

        prominence = prominence * 1.5
        peaks, _ = scipy.signal.find_peaks(profile, prominence=prominence)

    # find peak widths
    widths, width_heights, left_ips, right_ips = scipy.signal.peak_widths(
        profile, peaks, rel_height=0.5
    )

    sigmas = np.array(widths) / 2
    # peak area (by summation)
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


def plot_xps(
    profiles,
    results,
    bgs,
    titles,
    x_axes=None,
    xlabel="pixel",
    inverted=True,
):
    """A even higher level of plotting."""

    if x_axes is None:
        x_axes = np.arange(len(profiles[0]))

    nrows = len(profiles)
    fig, axs = plt.subplots(
        2, nrows, height_ratios=[2, 1], figsize=(10, 6), sharex="col", sharey="row"
    )

    if nrows == 1:
        plot_xps_fits(
            axs[0],
            axs[1],
            x_axes,
            profiles[0],
            bgs[0],
            results[0],
            xlabel=xlabel,
            title=titles[0],
        )
        if inverted:
            axs[0].invert_xaxis()
    else:
        for i, (profile, result, bg) in enumerate(zip(profiles, results, bgs)):
            plot_xps_fits(
                axs[0, i],
                axs[1, i],
                x_axes,
                profile,
                bg,
                result,
                xlabel=xlabel,
                title=titles[i],
            )


def xps_fitting(
    profile,
    background_values=None,
    background_indices=None,
    num_peaks=1,
    dx=1,
    x_data=None,
    fixed_fraction=True,
    peak_prominence=0.1,
):
    """Semi automatic fitting of XPS data."""

    background_indices = background_indices or (50, -50)
    if background_values is None:
        bg_left = profile[: background_indices[0]].mean()
        bg_right = profile[background_indices[1] :].mean()
    else:
        bg_left, bg_right = background_values

    if x_data is None:
        x_data = np.arange(len(profile))

    # background subtraction
    bg = shirley_background(profile - bg_right, dx, bg_left - bg_right) + bg_right

    # approximate parameters
    profile_sub = profile - bg

    centers, sigmas, peak_areas = parameter_estimation(
        profile_sub, num_peaks, peak_prominence
    )

    constr = {}
    for i in range(1, num_peaks + 1):  # start with 1
        constr[f"p{i}_center"] = {"value": centers[i - 1]}
        constr[f"p{i}_amplitude"] = {"value": peak_areas[i - 1]}
        constr[f"p{i}_sigma"] = {"value": sigmas[i - 1]}

    model, param = pseudo_voigt_fits([f"p{i}" for i in range(1, num_peaks + 1)], constr)
    result = model.fit(profile_sub, x=x_data, params=param)

    return result, bg


def fit_pixel_per_ev(
    files,
    roi,
    background_values,
    num_peaks,
    plot=False,
    peak_prominence=0.1,
    **kwargs,
):

    background_values = background_values.split(",")
    background_values = np.array([float(f) for f in background_values]).reshape(-1, 2)

    num_peaks = int(num_peaks)

    xps_objs = [RawReader(f) for f in files]

    profiles = [skimage.measure.profile_line(c.read_image(), **roi) for c in xps_objs]

    results = []
    bgs = []
    for profile, background in zip(profiles, background_values):
        result, bg = xps_fitting(
            profile,
            background_values=background,
            num_peaks=num_peaks,
            peak_prominence=peak_prominence,
        )
        results.append(result)
        bgs.append(bg)

    delta_ev = (
        xps_objs[1].imgmeta["Start Voltage"][0]
        - xps_objs[0].imgmeta["Start Voltage"][0]
    )

    peak_diff = []

    for i in range(1, num_peaks + 1):
        peak_diff.append(
            results[1].best_values[f"p{i}_center"]
            - results[0].best_values[f"p{i}_center"]
        )
    peak_diff = np.array(peak_diff).mean()

    pixel_per_ev = peak_diff / -delta_ev
    print(f"pixel_per_ev: {pixel_per_ev}")

    if plot:
        plot_xps(
            profiles,
            results,
            bgs,
            [
                f"pixel_per_ev calibration start voltage: {obj.imgmeta['Start Voltage'][0]}"
                for obj in xps_objs
            ],
            xlabel="pixel",
        )

    return pixel_per_ev


def fit_peak_shift(
    file,
    roi,
    background_values,
    num_peaks,
    peak_index,
    pixel_per_ev,
    peak_value,
    incident_voltage,
    plot=False,
    peak_prominence=0.1,
    **kwargs,
):

    background_values = background_values.split(",")
    background_values = [float(f) for f in background_values]

    num_peaks = int(num_peaks)
    peak_index = int(peak_index)
    peak_value = float(peak_value)
    incident_voltage = float(incident_voltage)
    peak_prominence = float(peak_prominence)

    xps_obj = RawReader(file)
    profile = skimage.measure.profile_line(xps_obj.read_image(), **roi)

    result, bg = xps_fitting(
        profile,
        background_values=background_values,
        num_peaks=num_peaks,
        peak_prominence=peak_prominence,
    )
    start_voltage = xps_obj.imgmeta["Start Voltage"][0]

    peak_pos = result.best_values[f"p{peak_index+1}_center"] / pixel_per_ev
    peak_shift = incident_voltage - start_voltage - peak_value - peak_pos

    if plot:
        plot_xps(
            [profile],
            [result],
            [bg],
            [f"absolute ev calibration start voltage: {start_voltage}"],
            x_axes=incident_voltage
            - start_voltage
            - np.arange(len(profile)) / pixel_per_ev
            - peak_shift,
            xlabel="binding energy [eV]",
            inverted=True,
        )

    print(f"peak shift: {peak_shift}")

    return peak_shift


def plot_xps_data(
    files,
    ax,
    title_prefix,
    start_idx=0,
    end_idx=None,
    skip=10,
    show_interval=True,
    incident_voltage=700,
    pixel_per_ev=166,
    peak_shift=0,
    **kwargs,
):
    """Plot XPS data from a list of files"""
    files_subset = files[start_idx:end_idx] if end_idx else files[start_idx:]
    color = plt.cm.Blues(np.linspace(0.2, 1.0, len(files_subset) // skip + 1))

    t_list = []
    for i, f in enumerate(files_subset):
        if i % skip == 0:
            r = RawReader(f)
            r.read_image()
            start_voltage = r.imgmeta["Start Voltage"][0]
            exposure_time = r.imgmeta["Camera Exposure"][0]
            camera_average = r.imgmeta["Camera Average"][0]
            t_list.append(datetime.strptime(r.timestamp, "%Y/%m/%d %H:%M:%S.%f"))
            profile = skimage.measure.profile_line(r.read_image(), **roi)
            profile = scipy.ndimage.gaussian_filter1d(profile, sigma=20.0)
            ev_range = incident_voltage - (
                start_voltage + np.arange(len(profile)) / pixel_per_ev + peak_shift
            )
            ax.plot(ev_range, profile, color=color[i // skip])
    ax.invert_xaxis()
    if "ylim" in kwargs:
        ax.set_ylim(kwargs["ylim"])
    ax.set_xlabel("Binding Energy [eV]")

    if show_interval:
        exp_time = (t_list[-1] - t_list[0]).total_seconds()
        ax.text(
            0.02,
            0.98,
            f"{title_prefix} μXPS \nexp time: {exp_time:.2f} s\nevery {skip} frames",
            transform=ax.transAxes,
            verticalalignment="top",
            horizontalalignment="left",
        )
    else:
        ax.text(
            0.02,
            0.98,
            f"start time: {t_list[0].strftime('%H:%M:%S')}\nend time: {t_list[-1].strftime('%H:%M:%S')}\nevery {skip} frames",
            transform=ax.transAxes,
            verticalalignment="top",
            horizontalalignment="left",
        )
