import matplotlib.pyplot as plt
import numpy as np

from pyleem.analyzer import Analyzer
from pyleem.operation.drift import calculate_drift
from scipy.ndimage import shift


class XASAnalyzer(Analyzer):
    """Analyzer for X-ray absorption image stacks.

    A typical step of the XAS analysis is to correct image drift (transform)
    and extract the area intensity over the image stack (energy).

    The drift correction needs to be manually applied due to the
    expensive computation. The intensity vs. stack can be plotted.

    """

    def __init__(self, readers, roi, onset=0):
        """Create an XAS analyzer."""
        super().__init__(readers, roi=roi, onset=onset)

    def get_processed_image(self, index):
        """Return the drift-corrected image."""

        if hasattr(self, "correction_shifts"):
            return shift(self.get_raw_image(index), shift=self.correction_shifts[index])
        else:
            return self.get_raw_image(index)

    def get_intensities(self):
        """Return ROI mean intensity for the stack."""
        return np.array([self.get_measurement(index).mean for index in self.indices])

    def calculate_drift(
        self,
        sigma=3,
        crop_size=None,
        upsample_factor=10,
        max_workers=None,
        chunk_size=32,
        max_distance=None,
        reference_index=0,
    ):
        """Calculate the correction shifts."""
        images = np.stack([self.get_raw_image(index) for index in self.indices])
        self.correction_shifts = calculate_drift(
            images,
            sigma=sigma,
            crop_size=crop_size,
            upsample_factor=upsample_factor,
            max_workers=max_workers,
            chunk_size=chunk_size,
            max_distance=max_distance,
            reference_index=reference_index,
        )

        return self.correction_shifts

    def plot_intensity(self, ax=None):
        """Plot ROI intensity vs. incident energy."""
        ax = ax or plt.gca()

        energy_range = [
            self.get_metadata("Incident Energy", index)[0] for index in self.indices
        ]
        intensities = self.get_intensities()

        ax.plot(energy_range, intensities)
        ax.set_xlabel("Incident Energy [eV]")
        ax.set_ylabel("Intensity")

        return ax
