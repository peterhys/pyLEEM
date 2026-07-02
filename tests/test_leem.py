import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyleem.analysis.leem import LEEMIVAnalyzer
from pyleem.roi import RectROI


def test_leem_plot_intensity(leem_readers):
    """Test LEEMIVAnalyzer plots ROI intensity by Start Voltage."""
    roi = RectROI(top=0, left=0, bottom=256, right=64)
    analyzer = LEEMIVAnalyzer(leem_readers, roi=roi)
    fig, ax = plt.subplots()

    returned = analyzer.plot_intensity(ax=ax)

    line = ax.lines[0]
    assert returned is ax
    assert np.array_equal(line.get_xdata(), np.array([10.0, 11.0, 12.0, 13.0]))
    assert line.get_ydata() == pytest.approx([0.0, 1000.0, 0.0, 1000.0])
    assert ax.get_xlabel() == "Energy [eV]"
    assert ax.get_ylabel() == "Intensity"
    plt.close(fig)
