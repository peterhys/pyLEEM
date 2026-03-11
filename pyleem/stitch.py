from pyleem.utils import find_stitch_points, stitch_profiles
from pyleem.analysis import AnalyzerGroup
import numpy as np


class StitchAnalyzer:
    """Analyzer for stitching multiple profiles together.

    The analyzer takes an anlzyer class, and it generates
    all methods from the source analyzer class.

    The abscissa and ordinate are directly provided to the analyer.
    """

    def __init__(
        self,
        analyzer_class,
        abscissa,
        ordinate,
        abscissa_label,
        ordinate_label,
        metadata,
    ):
        self.analyzer_class = analyzer_class
        self.abscissa = abscissa
        self.ordinate = ordinate
        self.abscissa_label = abscissa_label
        self.ordinate_label = ordinate_label
        self._metadata = metadata

    @property
    def metadata(self):
        """Return the metadata."""
        return self._metadata

    def __getattr__(self, name):
        """Dynamically inherit methods from source class.

        This allows the summed analyzer to call any method that exists
        in the original analyzer class. The error message is also
        customized to the source analyzer class.
        """
        if hasattr(self.analyzer_class, name):
            attr = getattr(self.analyzer_class, name)
            if callable(attr):
                return lambda *args, **kwargs: attr(self, *args, **kwargs)
        raise AttributeError(
            f"'{self.analyzer_class.__name__}' object has no attribute '{name}'"
        )


class StitchGroup(AnalyzerGroup):
    """Analyzer for stitching multiple profiles together.

    The analyzer stitches multiple profiles together to create a new profile.
    The profiles need to be the same class and have the same labels for
    the abscissa. The result object is for analysis only,
    the metadata of the first analyzer is perseved in the final analyzer.
    """

    def __init__(self, analyzers, stitch_points=None, method="midpoint"):
        """Initialize stitched group from list of analyzers.

        :param list analyzers: List of analyzer objects to stitch.
        :param list stitch_points: Explicit stitch points; auto-computed if None.
        :param str method: Method for auto stitch point
            selection ('midpoint', 'start', 'end'). Defaults to 'midpoint'.
        :raises ValueError: If analyzers have mismatched types or labels.
        """
        assert self.validate_analyzers(analyzers)
        analyzers = sorted(analyzers, key=lambda x: x.abscissa.min())
        super().__init__(analyzers)

        self.abscissa_ranges = [
            (analyzer.abscissa.min(), analyzer.abscissa.max())
            for analyzer in self.analyzers
        ]
        self.stitch_points = stitch_points or find_stitch_points(
            self.abscissa_ranges, method
        )

        assert len(self.stitch_points) == len(analyzers) - 1, (
            f"Expected {len(analyzers) - 1} "
            f"stitch points, got {len(self.stitch_points)}"
        )

        self.mask_points = (
            [self.abscissa_ranges[0][0]]
            + self.stitch_points
            + [self.abscissa_ranges[-1][1]]
        )

        self._stitch_analyzer = self.stitch_profile()

    @property
    def stitched_analyzer(self):
        """Return the stitched analyzer."""
        return self._stitch_analyzer

    def stitch_profile(self):
        """Stitch the profiles together."""
        profiles = self.get_attrs("profile")
        abscissas = self.get_attrs("abscissa")
        abscissa, ordinate = stitch_profiles(abscissas, profiles, self.mask_points)

        # Final abscissa
        # The final abscissa follows the order of the analzers
        is_descending = self.analyzers[0].abscissa[0] > self.analyzers[0].abscissa[-1]

        sorted_indices = np.argsort(abscissa)
        if is_descending:
            sorted_indices = sorted_indices[::-1]

        stitch_analyzer = StitchAnalyzer(
            self.analyzers[0].__class__,
            abscissa[sorted_indices],
            ordinate[sorted_indices],
            self.analyzers[0].abscissa_label,
            self.analyzers[0].ordinate_label,
            self.analyzers[0].metadata,
        )

        return stitch_analyzer

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
        if len(set([analyzer.abscissa_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Abscissa labels don't match.")
        if len(set([analyzer.ordinate_label for analyzer in analyzers])) != 1:
            raise ValueError(f"Ordinate labels don't match.")

        return True
