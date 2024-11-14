"""Functions for XPS analysis."""

import skimage.measure
import numpy as np
from lmfit.models import VoigtModel, PseudoVoigtModel
from lmfit import Parameters
import pandas as pd
from pyleem import RawReader
import skimage
from roifile import ImagejRoi, ROI_TYPE
from dataclasses import dataclass, field


def shirley_substract(y, dx, base_diff, iterations=20, tol=1e-6):
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


def xps_model(peaks, constraints=None):
    """Create XPS model for XPS fitting.

    :param list peaks: The list of peaks to fit. The peak should be a string.
    :param dict constraints: The constraints for the parameter fitting.
    """

    model_list = []
    constraints = constraints or {}

    for pk in peaks:
        model_list.append(PseudoVoigtModel(prefix=pk + "_"))
        # model_list.append(VoigtModel(prefix=pk + "_"))

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
    bg_total,
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
    ax.plot(x, y, label="XPS data")
    ax.plot(x, result.best_fit + bg_total, label="total fit")
    ax.plot(x, bg_total, label="bg")
    for prefix, fit_array in result.eval_components().items():
        ax.plot(x, fit_array + bg_total, label=f"{prefix}fit")
    ax.set_title(title)
    ax.legend()

    ax.set_ylabel("Intensity")
    res_ax.set_ylabel("Residuals")
    # res_ax.plot(x, y - result.best_fit - bg_total, label="residuals")
    res_ax.plot(x, result.residual, label="residuals")
    res_ax.set_xlabel(xlabel)

    if inverted:
        ax.invert_xaxis()
        res_ax.invert_xaxis()


def output_fit_result(results, area=False, uncertainty=True):
    """Output the fitting results.

    :param results: The fitting results.
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


def shift_KE(start_voltage, peak_shift, rel_ke):
    """Adjust KE peak position."""

    return start_voltage + peak_shift + rel_ke


def read_xps(file, pixperev, incident_voltage, start_voltage, peak_shift):
    """Read XPS data and plot it.

    This function supports two different types of csv file style.
    The plot profile directly from ImageJ that contains header but incorrect;
    And the data exported using the ROIProfile plugin in ImageJ.
    """

    df = pd.read_csv(file, header=0)
    # print(df)
    # drop unnamed column
    # sometimes ImageJ settings contains row number
    # disable in ImageJ options > I/O > Save row numbers
    # df.drop(
    #     df.columns[df.columns.str.contains("unnamed", case=False)], axis=1, inplace=True
    # )
    # df.drop(
    #     df.columns[df.columns.str==""], axis=1, inplace=True
    # )
    df.columns = ["pixel", "intensity"]
    df["KE"] = start_voltage + peak_shift + df["pixel"] / pixperev
    df["BE"] = incident_voltage - df["KE"]
    return df


import re
import os
from itertools import zip_longest

file_format = re.compile(
    # 20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C
    # position is optional
    r"(\d{8})_XPS_Sample(\d)_([A-Z]{1,2})_(\d[A-Z]{2})_"
    r"(\d{1,4})eV_(\d{1,4})eV_([A-Za-z]{1,2}\d[a-z])_?([A-Z]\d{0,1})?"
)
file_keys = [
    "date",
    "sample",
    "condition",
    "aperture",
    "incident_voltage",
    "start_voltage",
    "element",
    "position",  # optional
]


def parse_file_info(file, file_format, file_keys):
    basefile = os.path.basename(file)
    match = file_format.match(basefile)
    if match:
        return zip_longest(file_keys, match.groups(), fillvalue="NA")
    else:
        raise ValueError(f"File name {file} does not match the expected format")


def profile_roi(image, roi, pixel_per_ev, incident_voltage, start_voltage, peak_shift):
    """Profile the image based on the ROI object."""

    profile = skimage.measure.profile_line(image, **roi)
    KE = (start_voltage + peak_shift + df["pixel"] / pixel_per_ev,)
    df = pd.DataFrame(
        {
            "intensity": profile,
            "pixel": np.arange(len(profile)),
            "kinetic energy": KE,
            "binding energy": incident_voltage - KE,
        }
    )

    return df


@dataclass
class LineROI:
    """Region of interest for a line.

    ROI parameters can be directly passed to the constructor, or a ROI file from
    ImageJ.
    """

    def __init__(self, file=None, **kwargs):
        """Initialize the ROI object.

        If a roi file is pass then the parameters are loaded onto the file.
        """

        if file:
            roif = ImagejRoi.fromfile(file)
            self.src = (roif.y1, roif.x1)
            self.dst = (roif.y2, roif.x2)
            self.linewidth = roif.stroke_width

        else:
            assert "src" in kwargs and "dst" in kwargs and "linewidth" in kwargs
        self.order = 1
        self.mode = "nearest"
        self.cval = 0
        self.reduce_func = np.mean

        self.__dict__.update(kwargs)

    def tofile(self, file):
        """Save the ROI to a file."""

        roif = ImagejRoi(
            type="line",
            x1=self.src[1],
            y1=self.src[0],
            x2=self.dst[1],
            y2=self.dst[0],
            stroke_width=self.linewidth,
            stroke_color=b"M\xff\xff\x00",  # default yellow
            roitype=ROI_TYPE.LINE,
        )
        roif.tofile(file)
