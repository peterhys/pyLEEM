"""Base analyzer for spectra analysis."""

from pyleem.analyzer import Analyzer
import numpy as np
from pyleem.operation.stitch import find_stitch_points, stitch_profiles


def kinetic_energy(pixel, start_voltage, pixel_per_ev, peak_shift):

    return start_voltage + peak_shift + pixel / pixel_per_ev


class SpectraBase(Analyzer):
    """Analyzer for spectra analysis."""

    def __init__(self, readers, roi, pixel_per_ev, peak_shift, onset=0):
        super().__init__(readers, roi=roi, onset=onset)
        self.pixel_per_ev = pixel_per_ev
        self.peak_shift = peak_shift

    def get_kinetic_energy(self, index):
        pixel = self.get_pixel(index)
        start_voltage = self.get_metadata("Start Voltage", index)[0]
        return kinetic_energy(pixel, start_voltage, self.pixel_per_ev, self.peak_shift)

    def stitch_profiles(self, indices, stitch_method="midpoint"):
        """Stitch profiles together.

        The indices needs to be in the order of stitching.
        """
        x_array_list = [self.get_kinetic_energy(index) for index in indices]
        profile_list = [self.get_profile(index) for index in indices]

        x_ranges = [(x[0], x[-1]) for x in x_array_list]
        stitch_points = find_stitch_points(x_ranges, method=stitch_method)

        mask_points = [x_ranges[0][0], *stitch_points, x_ranges[-1][1]]

        return stitch_profiles(x_array_list, profile_list, mask_points)
