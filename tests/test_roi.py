import numpy as np
import pytest
from roifile import ImagejRoi, ROI_TYPE
from pyleem.roi import LineROI


class TestLIneROI:
    """Test LineROI class."""

    def test_from_kwargs(self, roi):
        """Test LineROI initialization from kwargs."""

        assert roi.src == (0, 0)
        assert roi.dst == (0, 127)
        assert roi.linewidth == 1

    def test_defaults(self, roi):
        """Test LineROI defaults."""

        assert roi.order == 1
        assert roi.mode == "nearest"
        assert roi.cval == 0
        assert roi.reduce_func == np.mean

    def test_missing_fields_raises(self):
        """Test missing fields raises ValueError."""

        with pytest.raises(ValueError, match="missing fields"):
            LineROI(src=(0, 0))  # dst and linewidth missing

    def test_override_defaults(self):
        """Test LineROI overrides defaults."""

        roi = LineROI(src=(0, 0), dst=(0, 127), linewidth=3, mode="constant", cval=1.0)
        assert roi.mode == "constant"
        assert roi.cval == 1.0

    def test_from_file(self, tmp_path):
        """Test LineROI initialization from file.

        Here we modify the roi file src and dst instead of using the fixture.
        """

        roif = ImagejRoi(
            x1=0.0,
            y1=1.0,
            x2=9.0,
            y2=10.0,
            stroke_width=10,
            stroke_color=b"M\xff\xff\x00",
            roitype=ROI_TYPE.LINE,
        )
        roif.tofile(tmp_path / "test.roi")

        roi = LineROI(roi_file=tmp_path / "test.roi", linewidth=10)
        assert roi.src == (1.0, 0.0)
        assert roi.dst == (10.0, 9.0)
        assert roi.linewidth == 10
        assert roi.order == 1
        assert roi.mode == "nearest"
        assert roi.cval == 0
        assert roi.reduce_func == np.mean

    def test_read_profile(self, roi, xps_array):
        """Test LineROI read_profile method."""

        profile = roi.read_profile(xps_array)
        assert len(profile) == 128 and isinstance(profile, np.ndarray)
        assert np.array_equal(profile, xps_array[0, :])

    def test_to_roi_object(self, roi):
        """Test LineROI to_roi_object method."""

        roi_object = roi.to_roi_object()
        assert roi_object.x1 == 0.0
        assert roi_object.y1 == 0.0
        assert roi_object.x2 == 127.0
        assert roi_object.y2 == 0.0
        assert roi_object.stroke_width == 1.0
        assert roi_object.stroke_color == b"M\xff\xff\x00"
        assert roi_object.roitype == ROI_TYPE.LINE
