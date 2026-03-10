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


def test_to_dict_method():
    """Test to_dict returns correct keys."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    roi_dict = roi.to_dict()

    # Check that only the profile_line keys are included
    expected_keys = ["src", "dst", "linewidth", "order", "mode", "cval", "reduce_func"]
    assert set(roi_dict.keys()) == set(expected_keys)


def test_to_roifile(tmp_path):
    """Test saving ROI to file."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    roi_file = tmp_path / "test_out.roi"
    roi.to_roifile(roi_file)

    roif_out = ImagejRoi.fromfile(roi_file)
    assert roif_out.x1 == 0 and roif_out.y1 == 0
    assert roif_out.x2 == 9 and roif_out.y2 == 9
    assert roif_out.stroke_width == 1


def test_roi_read_profile(xps_array, roi):
    """Test reader read_profile method."""
    profile = roi.read_profile(xps_array)
    assert len(profile) == 128 and isinstance(profile, np.ndarray)
    assert np.array_equal(profile, xps_array[0, :])
