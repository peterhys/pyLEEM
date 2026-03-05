import pytest
from pyleem.calibrate import (
    read_config,
    read_config_result,
    write_config_result,
    calibrate_profile_config,
)
from pyleem.roi import LineROI
from pyleem import calibrate


@pytest.fixture
def roi_file(tmp_path, roi):
    """Save the conftest roi fixture to a temporary ImageJ ROI file."""

    roi_path = tmp_path / "test.roi"
    roi.to_roifile(roi_path)
    return roi_path


def make_config(tmp_path, roi_file, files, extra_sections="", name="config.toml"):
    """Write a minimal TOML config file in tmp_path and return its path."""

    path_list = ", ".join(f'"{f.name}"' for f in files)
    content = f'[base]\npaths = [{path_list}]\nroi = "{roi_file.name}"\n'
    content += extra_sections
    config_path = tmp_path / name
    config_path.write_text(content)
    return config_path


def test_read_config_base_params(tmp_path, roi_file, xps_multiple_raw_files):
    """Test read_config with base parameters."""

    config_path = make_config(tmp_path, roi_file, xps_multiple_raw_files)
    base_params, cal_params = read_config(config_path)

    assert isinstance(base_params["roi"], LineROI)
    assert base_params["paths"] == [tmp_path / f.name for f in xps_multiple_raw_files]
    assert cal_params == {}


def test_read_config_with_calibration(tmp_path, roi_file, xps_multiple_raw_files):
    """Test read_config with calibration."""

    config_path = make_config(
        tmp_path,
        roi_file,
        xps_multiple_raw_files,
        extra_sections="[calibration]\nnum_peaks = 2\n",
    )
    _, cal_params = read_config(config_path)
    assert cal_params == {"num_peaks": 2}


def test_read_config_result(tmp_path, roi_file, xps_multiple_raw_files):
    """Test read_config_result."""

    config_path = make_config(
        tmp_path,
        roi_file,
        xps_multiple_raw_files,
        extra_sections="[result]\npixel_per_ev = 16.0\npeak_shift = 1.5\n",
    )
    result = read_config_result(config_path)
    assert result["pixel_per_ev"] == 16.0
    assert result["peak_shift"] == 1.5


def test_write_config_result(tmp_path, roi_file, xps_multiple_raw_files):
    """Test write_config_result."""

    config_path = make_config(tmp_path, roi_file, xps_multiple_raw_files)
    write_config_result(config_path, {"pixel_per_ev": 16.0, "peak_shift": 0.5})

    result = read_config_result(config_path)
    assert result["pixel_per_ev"] == 16.0
    assert result["peak_shift"] == 0.5


def test_calibrate_profile_config_reset(tmp_path, roi_file, xps_multiple_raw_files):
    """Test calibrate_profile_config with reset=True."""

    config_path = make_config(tmp_path, roi_file, xps_multiple_raw_files)
    cal_result = {"pixel_per_ev": 16.0, "peak_shift": 0.0}

    class MockGroup:
        def __init__(self, **kwargs):
            pass

        def calibrate(self, cal_params, plot=False):
            return cal_result

    roi = calibrate_profile_config(config_path, MockGroup, reset=True)

    assert isinstance(roi, LineROI)
    assert roi.is_calibrated
    assert roi.pixel_per_ev == 16.0
    assert roi.peak_shift == 0.0
    assert read_config_result(config_path)["pixel_per_ev"] == 16.0


def test_calibrate_profile_config_no_reset(
    tmp_path, roi_file, xps_multiple_raw_files, monkeypatch
):
    """Test calibrate_profile_config without reset.

    Verifies that neither calibrate nor write_config_result is called.
    """

    config_path = make_config(
        tmp_path,
        roi_file,
        xps_multiple_raw_files,
        extra_sections="[result]\npixel_per_ev = 16.0\npeak_shift = 0.0\n",
    )

    monkeypatch.setattr(
        calibrate,
        "write_config_result",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("write_config_result should not be called")
        ),
    )

    class MockGroup:
        def __init__(self, **kwargs):
            pass

        def calibrate(self, cal_params, plot=False):
            raise AssertionError("calibrate should not be called")

    roi = calibrate_profile_config(config_path, MockGroup, reset=False)

    assert isinstance(roi, LineROI)
    assert roi.is_calibrated
    assert roi.pixel_per_ev == 16.0
