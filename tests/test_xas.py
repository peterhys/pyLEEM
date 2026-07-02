import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyleem.analysis.xas import XASAnalyzer
from pyleem.roi import RectROI


def test_xas_plot_intensity(xas_readers):
    """Test XASAnalyzer plots ROI intensity by Beam Energy."""
    roi = RectROI(top=0, left=0, bottom=256, right=64)
    analyzer = XASAnalyzer(xas_readers, roi=roi)
    fig, ax = plt.subplots()

    returned = analyzer.plot_intensity(ax=ax)

    line = ax.lines[0]
    assert returned is ax
    assert np.array_equal(line.get_xdata(), np.array([10.0, 11.0, 12.0, 13.0]))
    assert line.get_ydata() == pytest.approx([0.0, 1000.0, 0.0, 1000.0])
    assert ax.get_xlabel() == "Beam Energy [eV]"
    assert ax.get_ylabel() == "Intensity"
    plt.close(fig)
