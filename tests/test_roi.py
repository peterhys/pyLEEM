from pyleem.roi import LineROI
from roifile import ImagejRoi, ROI_TYPE
import numpy as np


def test_init_from_file(tmp_path):
    """Test LineROI initialization from file."""
    roi_file = tmp_path / "test.roi"
    roif = ImagejRoi(
        x1=0,
        y1=0,
        x2=9,
        y2=9,
        stroke_width=1,
        stroke_color=b"M\xff\xff\x00",
        roitype=ROI_TYPE.LINE,
    )
    roif.tofile(roi_file)
    roi = LineROI(roi_file=roi_file, linewidth=10)

    assert roi.src == (0, 0) and roi.dst == (9, 9) and roi.linewidth == 10
    assert roi.order == 1 and roi.mode == "nearest" and roi.cval == 0
    assert roi.reduce_func == np.mean


def test_init_from_kwargs():
    """Test LineROI initialization from kwargs."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1, order=2)
    assert roi.src == (0, 0) and roi.dst == (9, 9)
    assert roi.linewidth == 1
    assert roi.order == 2


def test_calibrate():
    """Test ROI calibration."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)

    # Initially not calibrated
    assert not roi.is_calibrated
    assert roi.pixel_per_ev is None
    assert roi.peak_shift is None

    # Calibrate
    roi.calibrate(pixel_per_ev=165.0, peak_shift=5.0, custom_param=42)

    assert roi.is_calibrated
    assert roi.pixel_per_ev == 165.0
    assert roi.peak_shift == 5.0
    assert roi.custom_param == 42


def test_init_with_calibration_params():
    """Test initialization with calibration parameters."""
    roi = LineROI(
        src=(0, 0), dst=(9, 9), linewidth=1, pixel_per_ev=165.0, peak_shift=5.0
    )

    # Should be automatically calibrated
    assert roi.is_calibrated
    assert roi.pixel_per_ev == 165.0
    assert roi.peak_shift == 5.0


def test_is_calibrated_property():
    """Test is_calibrated property behavior."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)

    # Check initial state
    assert hasattr(roi, "is_calibrated")
    assert not roi.is_calibrated

    # After calibration
    roi.calibrate(pixel_per_ev=165.0, peak_shift=5.0)
    assert roi.is_calibrated


def test_to_dict_method():
    """Test to_dict returns correct keys."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    roi_dict = roi.to_dict()

    # Check that only the profile_line keys are included
    expected_keys = ["src", "dst", "linewidth", "order", "mode", "cval", "reduce_func"]
    assert set(roi_dict.keys()) == set(expected_keys)

    # Calibration params should NOT be in to_dict
    roi.calibrate(pixel_per_ev=165.0, peak_shift=10.0)
    roi_dict = roi.to_dict()
    assert "pixel_per_ev" not in roi_dict
    assert "peak_shift" not in roi_dict


def test_to_roifile(tmp_path):
    """Test saving ROI to file."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    roi_file = tmp_path / "test_out.roi"
    roi.to_roifile(roi_file)

    roif_out = ImagejRoi.fromfile(roi_file)
    assert roif_out.x1 == 0 and roif_out.y1 == 0
    assert roif_out.x2 == 9 and roif_out.y2 == 9
    assert roif_out.stroke_width == 1
