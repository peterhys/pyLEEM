from pyleem.utils import find_stitch_points, stitch_profiles
from pyleem.analyzer import ProfileAnalyzer
import numpy as np


class StitchAnalyzer(ProfileAnalyzer):
    """Analyzer to provide basic profile analysis for stitched profile.

    The class is a subclass of profile analyzer, with some methods
    overwritten due to its lack of metadata, reader, roi, and image.

    Metadata can be supplied directly to the class.
    """

    def __init__(
        self, analyzers, stitch_points=None, stitch_method="midpoint", metadata=None
    ):
        """Initialize stitched group from list of analyzers.

        :param list analyzers: List of analyzer objects to stitch.
        :param list stitch_points: Explicit stitch points; auto-computed if None.
        :param str stitch_method: Method for auto stitch point
            selection ('midpoint', 'start', 'end'). Defaults to 'midpoint'.
        :raises ValueError: If analyzers have mismatched types or labels.
        """
        assert self.validate_analyzers(analyzers)
        self.analyzers = analyzers

        self.stitch_points, self.mask_points = self.get_mask_points(
            stitch_points, stitch_method
        )
        self._abscissa, self._abscissa_label, self._ordinate, self._ordinate_label = (
            self.stitch_profile(self.mask_points)
        )
        self._profile = self.ordinate
        self._metadata = metadata or {}

    @property
    def metadata(self):
        """Return the metadata."""
        return self._metadata

    @property
    def image(self):
        """Raise an error when image is accessed.

        The exception is also raised when plot_image is called.
        """
        raise AttributeError(f"{type(self).__name__} has no image.")

    def __lt__(self, other):
        """Enable sorting by the start of the abscissa."""
        return self.abscissa.min() < other.abscissa.min()

    def get_mask_points(self, stitch_points=None, stitch_method="midpoint"):
        """Get the mask points for the stitched profile.

        The profile is sorted in the ascending order of the abscissa start value.
        """

        analyzers = sorted(self.analyzers, key=lambda x: x.abscissa.min())
        _ranges = [
            (analyzer.abscissa.min(), analyzer.abscissa.max()) for analyzer in analyzers
        ]
        stitch_points = stitch_points or find_stitch_points(_ranges, stitch_method)

        msg = f"Expected {len(analyzers) - 1} stitch points, got {len(stitch_points)}"
        assert len(stitch_points) == len(analyzers) - 1, msg

        mask_points = [_ranges[0][0]] + stitch_points + [_ranges[-1][1]]

        return stitch_points, mask_points

    def stitch_profile(self, mask_points):
        """Stitch the profiles together."""
        ordinates = [analyzer.ordinate for analyzer in self.analyzers]
        abscissas = [analyzer.abscissa for analyzer in self.analyzers]
        abscissa, ordinate = stitch_profiles(abscissas, ordinates, mask_points)

        # Final abscissa
        # The final abscissa follows the order of the analyzers
        sorted_indices = np.argsort(abscissa)
        is_descending = self.analyzers[0].abscissa[0] > self.analyzers[0].abscissa[-1]
        sorted_indices = sorted_indices[::-1] if is_descending else sorted_indices

        abscissa = abscissa[sorted_indices]
        ordinate = ordinate[sorted_indices]

        # Labels
        abscissa_label = self.analyzers[0].abscissa_label
        ordinate_label = self.analyzers[0].ordinate_label

        return abscissa, abscissa_label, ordinate, ordinate_label

    def validate_analyzers(self, analyzers):
        """Validate that all analyzers are compatible for stitching.

        :param list analyzers: List of analyzer objects.
        :return: True if all analyzers are compatible.
        :rtype: bool
        :raises TypeError: If analyzers are not all the same type.
        :raises ValueError: If abscissa or ordinate labels don't match.
        """
        # Validate all analyzers are the same type and same x, y labels
        if len(set([type(analyzer) for analyzer in analyzers])) != 1:
            raise TypeError(f"All analyzers must be the same type.")
        # Validate all analyzers have the same abscissa label and ordinate label
        # This is useful when we want to stitch different stitch profiles
        if len(set([analyzer.abscissa_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Abscissa labels don't match.")
        if len(set([analyzer.ordinate_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Ordinate labels don't match.")

        return True
