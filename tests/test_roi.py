from pyleem.roi import LineROI
from roifile import ImagejRoi, ROI_TYPE
import numpy as np
import pytest
import h5py


def test_line_roi(tmp_path):
    """Test LineROI class."""

    # Test initialization with file
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
    roi = LineROI(file=roi_file, linewidth=10)

    assert roi.src == (0, 0)
    assert roi.dst == (9, 9)
    assert roi.linewidth == 10
    assert roi.order == 1
    assert roi.mode == "nearest"
    assert roi.cval == 0
    assert roi.reduce_func == np.mean

    # Test initialization with kwargs
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    assert roi.src == (0, 0)
    assert roi.dst == (9, 9)
    assert roi.linewidth == 1

    # Test tofile method
    roi_file_out = tmp_path / "test_out.roi"
    roi.to_roifile(roi_file_out)
    roif_out = ImagejRoi.fromfile(roi_file_out)
    assert roif_out.x1 == 0
    assert roif_out.y1 == 0
    assert roif_out.x2 == 9
    assert roif_out.y2 == 9
    assert roif_out.stroke_width == 1
    assert roif_out.roitype == ROI_TYPE.LINE


def test_line_roi_mapping():
    """Test the LineROI class act as a Mapping."""

    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    assert len(roi) == 7
    assert sorted(list(roi.keys())) == sorted(
        ["src", "dst", "linewidth", "order", "mode", "cval", "reduce_func"]
    )

    assert roi["src"] == (0, 0)
    assert roi["dst"] == (9, 9)
    assert roi["linewidth"] == 1
    with pytest.raises(
        TypeError, match="'LineROI' object does not support item assignment"
    ):
        roi["src"] = 5


def test_to_h5(tmp_path):
    """Test the to_h5 method of the LineROI class."""
    roi = LineROI(src=(0, 0), dst=(9, 9), linewidth=1)
    h5_file = tmp_path / "test.h5"
    with h5py.File(h5_file.as_posix(), "w") as f:
        roi.to_h5(f)

    with h5py.File(h5_file, "r") as f:
        group = f["roi"]

        assert np.array_equal(group.attrs["src"], (0, 0))
        assert np.array_equal(group.attrs["dst"], (9, 9))
        assert group.attrs["linewidth"] == 1
        assert group.attrs["order"] == 1
        assert group.attrs["mode"] == "nearest"
        assert group.attrs["cval"] == 0
        assert group.attrs["reduce_func"] == "mean"
        assert group.attrs["roi_type"] == "line"
