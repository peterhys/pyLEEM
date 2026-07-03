import numpy as np
import pytest
from roifile import ImagejRoi, ROI_TYPE
from pyleem.roi import (
    AreaROI,
    LineROI,
    NoROI,
    OvalROI,
    PolygonROI,
    RectROI,
    ROIMeasurement,
)


@pytest.fixture
def non_line_roi(tmp_path):
    """Create a non-line ImageJ ROI."""
    roi = ImagejRoi(
        roitype=ROI_TYPE.NOROI,
    )
    roi.tofile(tmp_path / "non_line.roi")
    return tmp_path / "non_line.roi"


class TestLineROI:
    """Test LineROI class."""

    def test_from_kwargs(self, roi):
        """Test LineROI initialization from kwargs."""

        assert roi.src == (0, 0)
        assert roi.dst == (0, 127)
        assert roi.linewidth == 1

    def test_profile_with_kwargs(self):
        """Test LineROI passes options to profile_line."""

        image = np.arange(9).reshape(3, 3)
        roi = LineROI(src=(0, 0), dst=(0, 4), linewidth=1)

        profile = roi.profile(image, order=0, mode="constant", cval=-1)

        assert np.array_equal(profile, np.array([0, 1, 2, -1, -1]))

    def test_missing_fields_raises(self):
        """Test missing fields raises ValueError."""

        with pytest.raises(ValueError, match="missing fields"):
            LineROI(src=(0, 0))  # dst and linewidth missing

    def test_invalid_linewidth_raises(self):
        """Test LineROI rejects invalid linewidth."""

        with pytest.raises(ValueError, match="linewidth"):
            LineROI(src=(0, 0), dst=(0, 10), linewidth=0)

    def test_invalid_roi_type_raises(self, non_line_roi):
        """Test LineROI rejects non-line ImageJ ROI files."""

        with pytest.raises(ValueError, match="Expected LINE ROI, got NOROI"):
            LineROI(roi_file=non_line_roi)

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

    def test_profile(self, roi, xps_array):
        """Test LineROI profile method."""

        profile = roi.profile(xps_array)
        assert len(profile) == 128 and isinstance(profile, np.ndarray)
        assert np.array_equal(profile, xps_array[0, :])

    def test_measure(self, roi, xps_array):
        """Test LineROI measure returns profile statistics."""

        measurement = roi.measure(xps_array)
        assert isinstance(measurement, ROIMeasurement)
        assert np.array_equal(measurement.profile, xps_array[0, :])
        assert measurement.mean == float(xps_array[0, :].mean())
        assert measurement.total == float(xps_array[0, :].sum())
        assert measurement.minimum == float(xps_array[0, :].min())
        assert measurement.maximum == float(xps_array[0, :].max())
        assert measurement.n_pixels == 128

    def test_tofile(self, roi, tmp_path):
        """Test LineROI saves to ImageJ ROI file."""

        roi.tofile(tmp_path / "line.roi")
        roi_object = ImagejRoi.fromfile(tmp_path / "line.roi")
        assert roi_object.x1 == 0.0
        assert roi_object.y1 == 0.0
        assert roi_object.x2 == 127.0
        assert roi_object.y2 == 0.0
        assert roi_object.stroke_width == 1.0
        assert roi_object.stroke_color == b"M\xff\xff\x00"
        assert roi_object.roitype == ROI_TYPE.LINE


class TestNoROI:
    """Test NoROI placeholder behavior."""

    def test_measure_raises_not_implemented_error(self):
        """Test NoROI.measure raises the intended error."""
        roi = NoROI()

        with pytest.raises(NotImplementedError, match="No ROI selected"):
            roi.measure(np.ones((2, 2)))

        with pytest.raises(NotImplementedError, match="No ROI selected"):
            roi.profile(np.ones((2, 2)))

        with pytest.raises(NotImplementedError, match="No ROI selected"):
            roi.fromfile(ImagejRoi(roitype=ROI_TYPE.LINE))

        with pytest.raises(NotImplementedError, match="No ROI selected"):
            roi.tofile("no_roi.roi")


class TestRectROI:
    """Test RectROI class."""

    def test_area_roi_does_not_have_line_profile_method(self):
        """Test RectROI needs no line profile method."""

        roi = RectROI(top=1, left=1, bottom=3, right=4)
        assert isinstance(roi, AreaROI)
        assert not hasattr(roi, "read_profile")

    def test_rect_mask(self):
        """Test RectROI creates an expected mask."""

        roi = RectROI(top=1, left=2, bottom=3, right=5)
        expected = np.zeros((5, 6), dtype=bool)
        expected[1:3, 2:5] = True
        assert np.array_equal(roi.mask((5, 6)), expected)

    def test_measure(self):
        """Test RectROI measures image intensity."""

        image = np.arange(16).reshape(4, 4)
        roi = RectROI(top=1, left=1, bottom=3, right=3)

        measurement = roi.measure(image)
        assert isinstance(measurement, ROIMeasurement)
        assert measurement == ROIMeasurement(
            mean=7.5,
            total=30.0,
            minimum=5.0,
            maximum=10.0,
            n_pixels=4,
        )
        assert measurement.profile is None

    def test_measure_empty_mask_raises(self):
        """Test measuring an empty mask raises ValueError."""

        image = np.ones((4, 4))
        roi = RectROI(top=10, left=10, bottom=12, right=12)

        with pytest.raises(ValueError, match="selects no pixels"):
            roi.measure(image)

    def test_area_roi_missing_fields_raises(self):
        """Test missing area ROI fields raise ValueError."""

        with pytest.raises(ValueError, match="missing fields"):
            RectROI(top=1, left=1, bottom=3)

    def test_invalid_bounds_raises(self):
        """Test RectROI rejects negative bounds."""

        with pytest.raises(ValueError, match="non-negative"):
            RectROI(top=-1, left=1, bottom=1, right=3)

        with pytest.raises(ValueError, match="positive"):
            RectROI(top=1, left=1, bottom=1, right=3)

    def test_rect_calculates_size(self):
        """Test RectROI calculates height and width."""

        roi = RectROI(top=1, left=2, bottom=4, right=7)

        assert roi.height == 3
        assert roi.width == 5

    def test_rect_from_file(self, tmp_path):
        """Test RectROI initialization from ImageJ file."""

        roif = ImagejRoi(
            top=1,
            left=2,
            bottom=4,
            right=7,
            roitype=ROI_TYPE.RECT,
        )
        roif.tofile(tmp_path / "rect.roi")

        roi = RectROI(roi_file=tmp_path / "rect.roi")
        assert roi.top == 1
        assert roi.left == 2
        assert roi.bottom == 4
        assert roi.right == 7
        assert roi.height == 3
        assert roi.width == 5

    def test_invalid_roi_type_raises(self, non_line_roi):
        """Test RectROI rejects non-rect ImageJ ROI files."""

        with pytest.raises(ValueError, match="Expected RECT ROI, got NOROI"):
            RectROI(roi_file=non_line_roi)

    def test_rect_tofile(self, tmp_path):
        """Test RectROI saves to ImageJ ROI file."""

        roi = RectROI(top=1, left=2, bottom=4, right=7)
        roi.tofile(tmp_path / "rect.roi")
        roi_object = ImagejRoi.fromfile(tmp_path / "rect.roi")

        assert roi_object.top == 1
        assert roi_object.left == 2
        assert roi_object.bottom == 4
        assert roi_object.right == 7
        assert roi_object.roitype == ROI_TYPE.RECT


class TestOvalROI:
    """Test OvalROI class."""

    def test_oval_mask(self):
        """Test OvalROI creates an expected mask."""

        roi = OvalROI(top=1, left=1, bottom=4, right=6)
        expected = np.zeros((5, 7), dtype=bool)
        expected[1:4, 1:6] = np.array(
            [
                [False, True, True, True, False],
                [True, True, True, True, True],
                [False, True, True, True, False],
            ]
        )
        assert np.array_equal(roi.mask((5, 7)), expected)

    def test_oval_from_file(self, tmp_path):
        """Test OvalROI initialization from ImageJ file."""

        roif = ImagejRoi(
            top=1,
            left=2,
            bottom=4,
            right=7,
            roitype=ROI_TYPE.OVAL,
        )
        roif.tofile(tmp_path / "oval.roi")

        roi = OvalROI(roi_file=tmp_path / "oval.roi")
        assert roi.top == 1
        assert roi.left == 2
        assert roi.bottom == 4
        assert roi.right == 7
        assert roi.height == 3
        assert roi.width == 5

    def test_invalid_roi_type_raises(self, non_line_roi):
        """Test OvalROI rejects non-oval ImageJ ROI files."""

        with pytest.raises(ValueError, match="Expected OVAL ROI, got NOROI"):
            OvalROI(roi_file=non_line_roi)

    def test_invalid_bounds_raises(self):
        """Test OvalROI rejects zero-size geometry."""

        with pytest.raises(ValueError, match="positive"):
            OvalROI(top=1, left=1, bottom=1, right=3)

    def test_oval_calculates_size(self):
        """Test OvalROI calculates height and width."""

        roi = OvalROI(top=1, left=2, bottom=4, right=7)

        assert roi.height == 3
        assert roi.width == 5

    def test_oval_tofile(self, tmp_path):
        """Test OvalROI saves to ImageJ ROI file."""

        roi = OvalROI(top=1, left=2, bottom=4, right=7)
        roi.tofile(tmp_path / "oval.roi")
        roi_object = ImagejRoi.fromfile(tmp_path / "oval.roi")

        assert roi_object.top == 1
        assert roi_object.left == 2
        assert roi_object.bottom == 4
        assert roi_object.right == 7
        assert roi_object.roitype == ROI_TYPE.OVAL


class TestPolygonROI:
    """Test PolygonROI class."""

    def test_polygon_mask(self):
        """Test PolygonROI creates an expected mask."""

        roi = PolygonROI(rows=(1, 1, 3, 3), cols=(1, 4, 4, 1))
        expected = np.zeros((5, 6), dtype=bool)
        expected[1:4, 1:5] = True
        assert np.array_equal(roi.mask((5, 6)), expected)

    def test_invalid_coordinates_raises(self):
        """Test PolygonROI rejects invalid coordinates."""

        with pytest.raises(ValueError, match="same length"):
            PolygonROI(rows=(1, 2, 3), cols=(1, 2))

        with pytest.raises(ValueError, match="at least three"):
            PolygonROI(rows=(1, 2), cols=(1, 2))

        with pytest.raises(ValueError, match="non-negative"):
            PolygonROI(rows=(-1, 1, 2), cols=(1, 2, 1))

    def test_polygon_fromfile(self, tmp_path):
        """Test PolygonROI initialization from ImageJ file."""

        roif = ImagejRoi.frompoints([[2, 1], [5, 1], [5, 3], [2, 3]])
        roif.roitype = ROI_TYPE.POLYGON
        roif.tofile(tmp_path / "polygon.roi")

        roi = PolygonROI(roi_file=tmp_path / "polygon.roi")
        assert roi.rows == (1, 1, 3, 3)
        assert roi.cols == (2, 5, 5, 2)

    def test_invalid_roi_type_raises(self, non_line_roi):
        """Test PolygonROI rejects non-polygon ImageJ ROI files."""

        with pytest.raises(ValueError, match="Expected POLYGON ROI, got NOROI"):
            PolygonROI(roi_file=non_line_roi)

    def test_polygon_tofile(self, tmp_path):
        """Test PolygonROI saves to ImageJ ROI file."""

        roi = PolygonROI(rows=(1, 1, 3, 3), cols=(2, 5, 5, 2))
        roi.tofile(tmp_path / "polygon.roi")
        roi_object = ImagejRoi.fromfile(tmp_path / "polygon.roi")

        assert roi_object.top == 1
        assert roi_object.left == 2
        assert roi_object.bottom == 4
        assert roi_object.right == 6
        assert roi_object.n_coordinates == 4
        assert np.array_equal(
            roi_object.coordinates(),
            np.array([[2, 1], [5, 1], [5, 3], [2, 3]]),
        )
        assert roi_object.roitype == ROI_TYPE.POLYGON
