import pytest
from pyleem.config import Config


def make_config(tmp_path, content):
    """Write convert content into a TOML config file."""

    config_path = tmp_path / "config.toml"
    config_path.write_text(content)
    return config_path


@pytest.fixture
def config_content():
    """Write a minimal TOML config file content."""

    content = (
        '[base]\ndata_type = "test"\nroi = "test.roi"\n'
        '[calibration]\npaths = ["test_raw_0.dat", "test_raw_1.dat", "test_raw_2.dat"]\n'
        "[calibration.parameters]\nnum_peaks = 1\nincident_voltage = 400\n"
        "[calibration.result]\npixel_per_ev = 16.0\npeak_shift = 0.0\n"
    )
    return content


@pytest.fixture
def config_file(tmp_path, config_content):
    """Write a minimal TOML config file and return its path."""

    config_path = make_config(tmp_path, config_content)
    return config_path


def test_config_init(tmp_path, config_content):
    """Test Config initialization."""

    config_path = make_config(tmp_path, config_content)
    config = Config(config_path)
    assert config.config_path == config_path
    assert config.base_dir == config_path.parent


def test_config_get_roi(tmp_path, roi, config_content):
    """Test Config.get_roi returns a LineROI."""

    roi_path = tmp_path / "test.roi"
    roi.to_roi_object().tofile(roi_path)

    config_path = make_config(tmp_path, config_content)

    roi = Config(config_path).get_roi()
    assert roi.src == (0.0, 0.0)
    assert roi.dst == (0.0, 127.0)
    assert roi.linewidth == 1


def test_config_get_roi_missing_raises(tmp_path):
    """Test Config.get_roi raises ValueError when roi is absent from base."""

    content = '[base]\ndata_type = "test"\n'
    config_path = make_config(tmp_path, content)

    with pytest.raises(ValueError, match="ROI not found"):
        Config(config_path).get_roi()


def test_config_get_paths(tmp_path, config_content):
    """Test get_paths method."""

    config_path = make_config(tmp_path, config_content)

    paths = ["test_raw_0.dat", "test_raw_1.dat", "test_raw_2.dat"]
    config_paths = Config(config_path).get_paths(paths)
    assert config_paths == [tmp_path / f for f in paths]


def test_config_get_patterned_paths(tmp_path, config_content):
    """Test get_patterned_paths method."""

    config_path = make_config(tmp_path, config_content)
    # create a temporary directory with the files
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for i in range(3):
        (data_dir / f"test_raw_{i}.dat").touch()

    paths = sorted(Config(config_path).get_patterned_paths("data/*.dat"))
    assert paths == [str(data_dir / f"test_raw_{i}.dat") for i in range(3)]


def test_config_read_section(config_file):
    """Test Config.read_section with a flat (top-level) section."""

    result = Config(config_file).read_section("base")
    assert result["data_type"] == "test"
    assert result["roi"] == "test.roi"


def test_config_read_section_nested(config_file):
    """Test Config.read_section with a flat (top-level) section."""

    result = Config(config_file).read_section("calibration.parameters")
    assert result["num_peaks"] == 1
    assert result["incident_voltage"] == 400


def test_config_read_section_full(config_file):
    """Test Config.read_section with a full configuration."""

    result = Config(config_file).read_section()
    assert result["base"]["data_type"] == "test"
    assert result["base"]["roi"] == "test.roi"
    assert result["calibration"]["paths"] == [
        "test_raw_0.dat",
        "test_raw_1.dat",
        "test_raw_2.dat",
    ]
    assert result["calibration"]["parameters"]["num_peaks"] == 1
    assert result["calibration"]["parameters"]["incident_voltage"] == 400
    assert result["calibration"]["result"]["pixel_per_ev"] == 16.0


def test_config_write_section(config_file):
    """Test write_section with a top-level section."""

    Config(config_file).write_section(
        "result", {"pixel_per_ev": 16.0, "peak_shift": 1.5}
    )

    result = Config(config_file).read_section("result")
    assert result["pixel_per_ev"] == 16.0
    assert result["peak_shift"] == 1.5


def test_config_write_section_nested(config_file):
    """Test write_section with a nested section."""

    Config(config_file).write_section(
        "calibration.values", {"pixel_per_ev": 16.0, "peak_shift": 1.5}
    )

    result = Config(config_file).read_section("calibration.values")
    assert result["pixel_per_ev"] == 16.0
    assert result["peak_shift"] == 1.5


class TestConfigCalibrate:
    """Test Config.calibrate method."""

    @pytest.fixture
    def Config_CLS(self):
        """Create a subclass of Config."""

        class MockConfig(Config):
            def calibrate_results(self, cal_section):
                return {"pixel_per_ev": 8.0, "peak_shift": 3.75}

        return MockConfig

    def test_config_calibrate(self, config_file, Config_CLS):
        """Test calibrate method with reset."""

        config = Config_CLS(config_file)

        result = config.calibrate()
        assert result["pixel_per_ev"] == 8.0
        assert result["peak_shift"] == 3.75

        persisted = config.read_section("calibration.result")
        assert persisted["pixel_per_ev"] == 16.0
        assert persisted["peak_shift"] == 0.0

    def test_config_calibrate_update(self, config_file, Config_CLS):
        """Test calibrate method with reset and update."""

        config = Config_CLS(config_file)
        result = config.calibrate(update=True)
        assert result["pixel_per_ev"] == 8.0
        assert result["peak_shift"] == 3.75

        persisted = config.read_section("calibration.result")
        assert persisted["pixel_per_ev"] == 8.0
        assert persisted["peak_shift"] == 3.75
