import tomllib
import tomlkit
from pathlib import Path
from functools import reduce
from pyleem.roi import LineROI
import glob


"""
The configuration file is a TOML file that outlines the necessary parameters
in a data folder for analysis. Currently, the file is primarily used for
store calibration parameters and results.

The base section contains the data type. For profile type of files,


The file is structured as follows:

[base]
data_type = "xps"
roi = "line.roi"

[calibration]
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]

[calibration.parameters]
num_peaks = 1
baselines = [[197, 100], [197, 100], [197, 100]]
ref_index = 0
ref_value = 285.0
incident_voltage = 400

[calibration.result]
pixel_per_ev = 166.0
peak_shift = 3.75
"""


class Config:
    """Read and write sections of a TOML configuration file.

    :param str or Path config_path: Path to the TOML configuration file.
    """

    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.base_dir = self.config_path.parent

    def read_section(self, section=None):
        """Read a section by section name.

        :raises KeyError: If the section does not exist.
        """
        with open(self.config_path, "rb") as f:
            node = tomllib.load(f)

        if section is None:
            return node

        return dict(reduce(lambda n, k: n[k], section.split("."), node))

    def write_section(self, section, data):
        """Write data to a section by section name.

        :param str section: Section name.
        :param dict data: Data to write.
        """
        with open(self.config_path, "rb") as f:
            config = tomlkit.load(f)

        parts = section.split(".")
        reduce(lambda n, k: n[k], parts[:-1], config)[parts[-1]] = data

        with open(self.config_path, "w") as f:
            tomlkit.dump(config, f)

    def get_roi(self):
        """Special function to get the ROI from the configuration file."""
        if "roi" in self.read_section("base"):
            return LineROI(roi_file=self.base_dir / self.read_section("base")["roi"])
        else:
            raise ValueError("ROI not found in configuration file.")

    def get_paths(self, paths):
        """Special function to get the paths from the configuration file.

        Adds base directory to the paths.
        """
        return [self.base_dir / p for p in paths]

    def get_patterned_paths(self, pattern):
        """Special function to get the paths from a glob pattern.

        The file paths is unsorted.
        """
        return glob.glob(str(self.base_dir / pattern))

    def calibrate(self, update=False):
        """Calibrate using the calibration parameters.

        The subclass should define the calibrate_results method.
        Additional keyword arguments are passed to the calibrate_results method.
        """

        cal_section = self.read_section("calibration")
        results = self.calibrate_results(cal_section)
        if update:
            self.write_section("calibration.result", results)
        return results
