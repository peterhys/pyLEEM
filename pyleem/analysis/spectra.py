"""Base analyzer for spectra analysis."""

from pyleem.analyzer import Analyzer
import numpy as np
from pyleem.utils import find_stitch_points, stitch_profiles


def kinetic_energy(pixel, start_voltage, pixel_per_ev, peak_shift):

    return start_voltage + peak_shift + pixel / pixel_per_ev


class SpectraAnalyzer(Analyzer):
    """Analyzer for spectra analysis."""

    def __init__(self, readers, roi, pixel_per_ev, peak_shift):
        super().__init__(readers, roi)
        self.pixel_per_ev = pixel_per_ev
        self.peak_shift = peak_shift

    def get_kinetic_energy(self, index):
        pixel = self.get_pixel(index)
        start_voltage = self.get_metadata("Start Voltage", index)[0]
        return kinetic_energy(pixel, start_voltage, self.pixel_per_ev, self.peak_shift)

    def get_pixel(self, index):
        """Return the pixel positions for a profile."""
        return np.arange(len(self.get_profile(index)))
