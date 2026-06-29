# `pyleem.analyzer`

Analyzer is the core class for domain-specific analysis. The `Analyzer` class can perform
basic raw data analysis. However, it is not required to subclass the `Analyzer` class.

Analyzers perform analysis on a LEEM data stack. For metadata and information access, they
are accessed by index. In the analysis process, three levels of images are available: 
raw, processed, and annotated. Raw image is the original image, processed image is defined
by the subclass, which is used for analysis. Annotation are allowed for the plotting purposes,
this could be metadata overlay, scale bar or custom annotation.

Each analyzer takes ROI and readers as inputs. For analysis that do not require an ROI, a
placeholder NoROI is used. All ROI analysis are performed on the processed image. Custom
methods can access the raw image for additional analysis.

For designated workflow, configuration file can be used to build, run and save the analysis.
To allow workflow to run the analysis, the `analyze` method is required.  The analyzer should
be free of the configuration logic so other methods can be used for different analysis.

## Example

Here we show a simple example of extracting metadata and plot the image stack vs the metadata.

The processed image is a background-subtracted image. We add the metadata overlay to the image.
Here we show that we can add the metadata to the image as an overlay. And we perform simple
analysis to obtain the image intensity vs the voltage.

```python
from pyleem.analyzer import Analyzer
from pyleem.reader import UViewReader, read_files
from pyleem.roi import LineROI
from pyleem.annotation import MetadataTextMixin
import matplotlib.pyplot as plt


class VoltageProfileAnalyzer(MetadataTextMixin, Analyzer):
    """Analyzer for voltage-dependent line profiles."""

    def get_processed_image(self, index):
        """Return a background-subtracted image."""
        image = self.get_raw_image(index).astype(float)
        background = self.get_raw_image(0).astype(float)
        return image - background

    def annotate_image(self, index, ax):
        """Label the image with the voltage."""
        voltage, unit = self.get_metadata("Voltage", index)
        return self.annotate_metadata(index, ax, labels=["Voltage"])

    def analyze(self):
        """Analyze the total image intensity vs the voltage."""
        image_intensity = [
            self.get_processed_image(index).sum() for index in self.indices
        ]
        voltages = [self.get_metadata("Voltage", index)[0] for index in self.indices]
        return image_intensity, voltages

    def plot_intensity(self, ax=None):
        """Plot the image intensity vs the voltage."""
        image_intensity, voltages = self.analyze()
        ax = ax or plt.gca()
        ax.plot(voltages, image_intensity)
        ax.set_xlabel("Voltage [V]")
        ax.set_ylabel("Intensity")
        return ax


readers = read_files(
    ["data_0.dat", "data_1.dat", "data_2.dat"],
    reader_cls=UViewReader,
    metadata_list=[
        {"Voltage": (4.0, "V")},
        {"Voltage": (4.5, "V")},
        {"Voltage": (5.0, "V")},
    ],
)

analyzer = VoltageProfileAnalyzer(readers)


# Plot the processed image and add the voltage annotation.
# The second image is plotted.
analyzer.plot_image(index=1, annotate=True)

# obtain the analysis result
image_intensity, voltages = analyzer.analyze()

# plot the intensity vs the voltage
analyzer.plot_intensity()
```

```{eval-rst}
.. automodule:: pyleem.analyzer
   :members:
   :show-inheritance:
```
