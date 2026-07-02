from pyleem.analysis.fullfield import FullFieldAnalyzer
import matplotlib.pyplot as plt


class LEEMIVAnalyzer(FullFieldAnalyzer):
    """Analyzer for LEEM-IV image stacks.

    A typical step of the LEEM-IV analysis is to correct image drift (transform)
    and extract the area intensity over the image stack.
    """

    def plot_intensity(self, ax=None):
        """Plot ROI intensity vs. Start Voltage energy."""
        ax = ax or plt.gca()

        energy_range = [
            self.get_metadata("Start Voltage", index)[0] for index in self.indices
        ]
        intensities = self.get_intensities()

        ax.plot(energy_range, intensities)
        ax.set_xlabel("Energy [eV]")
        ax.set_ylabel("Intensity")

        return ax
