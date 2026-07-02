import matplotlib.pyplot as plt
import numpy as np

from pyleem.analyzer import Analyzer
from pyleem.operation.drift import calculate_drift
from scipy.ndimage import shift


class FullFieldAnalyzer(Analyzer):
    """Analyzer for full-field image stacks.

    A typical step of the full-field analysis is to correct image drift (transform)
    and extract the area intensity over the image stack.

    For LEEM, the analysis can be applied to LEEM-IV.
    For XAS, the analysis can be applied to XAS absorption spectra over beam energy.
    """

    def get_processed_image(self, index):
        """Return the drift-corrected image."""

        if hasattr(self, "correction_shifts"):
            return shift(self.get_raw_image(index), shift=self.correction_shifts[index])
        else:
            return self.get_raw_image(index)

    def get_intensities(self):
        """Return ROI mean intensity for the stack."""
        return np.array([self.get_measurement(index).mean for index in self.indices])

    def correct_drift(self, **kwargs):
        """Correct the drift of the image stack."""
        self.correction_shifts = self.calculate_drift(**kwargs)

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
        return calculate_drift(
            images,
            sigma=sigma,
            crop_size=crop_size,
            upsample_factor=upsample_factor,
            max_workers=max_workers,
            chunk_size=chunk_size,
            max_distance=max_distance,
            reference_index=reference_index,
        )
