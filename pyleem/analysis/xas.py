import matplotlib.pyplot as plt
from pyleem.analysis.fullfield import FullFieldAnalyzer


class XASAnalyzer(FullFieldAnalyzer):
    """Analyzer for X-ray absorption image stacks.

    A typical step of the XAS analysis is to correct image drift (transform)
    and extract the area intensity over the image stack (energy).

    The drift correction needs to be manually applied due to the
    expensive computation. The intensity vs. stack can be plotted.

    """

    def plot_intensity(self, ax=None):
        """Plot ROI intensity vs. Beam Energy."""
        ax = ax or plt.gca()

        energy_range = [
            self.get_metadata("Beam Energy", index)[0] for index in self.indices
        ]
        intensities = self.get_intensities()

        ax.plot(energy_range, intensities)
        ax.set_xlabel("Beam Energy [eV]")
        ax.set_ylabel("Intensity")

        return ax
