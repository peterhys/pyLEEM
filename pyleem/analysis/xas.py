import matplotlib.pyplot as plt
import numpy as np

from pyleem.analyzer import Analyzer
from pyleem.operation.drift import drift_correct


class XASAnalyzer(Analyzer):
    """Analyzer for X-ray absorption image stacks.

    A typical step of the XAS analysis is to correct image drift (transform)
    and extract the area intensity over the image stack (energy).

    The drift correction needs to be mannually applied due to the
    expansive computation. The instensity vs. stack can be plotted.
    """

    def __init__(self, readers, roi, onset=0):
        """Create an XAS analyzer."""
        super().__init__(readers, roi=roi, onset=onset)

    def get_processed_image(self, index):
        """Return the drift-corrected image."""

        if hasattr(self, "corrected_images"):
            return self.corrected_images[index]
        else:
            return self.get_raw_image(index)

    def get_intensities(self):
        """Return ROI mean intensity for the stack."""
        return np.array([self.get_measurement(index).mean for index in self.indices])

    def drift_correct(self, **drift_parameters):
        """Return the drift-corrected image."""
        images = np.stack([self.get_raw_image(index) for index in self.indices])
        self.corrected_images, self.correction_shifts = drift_correct(
            images,
            **drift_parameters,
        )

        return self.corrected_images, self.correction_shifts

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
