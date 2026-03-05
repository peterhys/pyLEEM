import tomllib
import tomlkit
from pathlib import Path
from pyleem.roi import LineROI


def read_config(config_path):
    """Read configuration from TOML file.

    :param str or Path config_path: Path to configuration file.
    :return: Base parameters and calibration parameters.
    :rtype: tuple(dict, dict)
    """

    config_path = Path(config_path)
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    base_dir = config_path.parent
    paths = [base_dir / f for f in config["base"]["paths"]]
    roi = LineROI(roi_file=base_dir / config["base"]["roi"])

    base_params = {**config["base"], "roi": roi, "paths": paths}
    cal_params = config.get("calibration", {})

    return base_params, cal_params


def read_config_result(config_path):
    """Read configuration result from TOML file.

    :param str or Path config_path: Path to configuration file.
    :return: Configuration result parameters.
    :rtype: dict
    """

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    return config["result"]


def write_config_result(config_path, cal_result):
    """Write calibration results to TOML file.

    :param str or Path config_path: Path to configuration file.
    :param dict cal_result: Calibration results.
    """

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    config["result"] = cal_result

    with open(config_path, "w") as f:
        tomlkit.dump(config, f)


def calibrate_profile_config(config_path, analyzer_group, reset=True, plot=False):
    """Calibrate line profile analyzer group using configuration file.

    :param str or Path config_path: Path to configuration file.
    :param type analyzer_group: Analyzer group class to calibrate.
    :param bool reset: Whether to recalculate calibration.
    :param bool plot: Whether to display calibration plots.
    :return: Calibrated ROI object.
    :rtype: LineROI
    """

    base_params, cal_params = read_config(config_path)
    group = analyzer_group(**base_params)

    if reset:
        cal_result = group.calibrate(cal_params, plot=plot)
        write_config_result(config_path, cal_result)
    else:
        cal_result = read_config_result(config_path)

    roi = base_params["roi"]
    roi.calibrate(**cal_result)

    return roi
