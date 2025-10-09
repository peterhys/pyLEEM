import os
import configparser
from pyleem.roi import LineROI
from pyleem.xps import fit_pixel_per_ev, fit_peak_shift
from pyleem.se import fit_se_profile


def calibrate_xps(src_dir, config, roi, plot=False):
    """Parse a particular section of the configuration file."""

    xps_params = dict(config["calibration.conversion"])

    files = xps_params["files"].split(",")
    xps_params["files"] = [os.path.join(src_dir, f.strip()) for f in files]
    pixel_per_ev = fit_pixel_per_ev(roi=roi, plot=plot, **xps_params)

    xps_reference = dict(config["calibration.reference"])
    xps_reference["file"] = os.path.join(src_dir, xps_reference["file"])
    peak_shift = fit_peak_shift(
        roi=roi, plot=plot, pixel_per_ev=pixel_per_ev, **xps_reference
    )

    return pixel_per_ev, peak_shift


def calibrate_se(src_dir, config, roi, plot=False):
    """Calibrate the pixel per ev only from the secondary electron profile."""

    se_params = dict(config["calibration.conversion"])
    files = se_params["files"].split(",")
    se_params["files"] = [os.path.join(src_dir, f.strip()) for f in files]
    pixel_per_ev, peak_shift = fit_se_profile(roi=roi, plot=plot, **se_params)

    return pixel_per_ev, peak_shift


CONFIG_REGISTRY = {
    "SE": calibrate_se,
    "XPS": calibrate_xps,
}


def calibrate(config_path, config_type, reset=False, plot=False):
    """Calibrate the pixel per ev and peak shift.

    The function parse the config file based on the config type.
    """

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_path)

    src_dir = os.path.dirname(config_path)
    roi_path = os.path.join(src_dir, config["base"]["roi_file"])
    roi = LineROI(file=roi_path)

    assert config_type in CONFIG_REGISTRY, f"Config type {config_type} is not supported"

    assert (
        config["base"]["config_type"] == config_type
    ), f'Incorrect config type {config["base"]["config_type"]} for {config_type}'

    if not reset:

        pixel_per_ev = float(config["calibration.result"]["pixel_per_ev"])
        peak_shift = float(config["calibration.result"]["peak_shift"])

    else:
        pixel_per_ev, peak_shift = CONFIG_REGISTRY[config_type](
            src_dir, config, roi, plot
        )
        if not config.has_section("calibration.result"):
            config.add_section("calibration.result")
        config["calibration.result"]["pixel_per_ev"] = str(pixel_per_ev)
        config["calibration.result"]["peak_shift"] = str(peak_shift)

    with open(config_path, "w") as configfile:
        config.write(configfile)

    return pixel_per_ev, peak_shift, config
