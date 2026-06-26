import pytest
import tomlkit

from pyleem.config import Config, load_config, save_config


def make_config(tmp_path, content):
    """Write content into a TOML config file."""

    config_path = tmp_path / "config.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


CONFIG_CONTENT = """
[session]
reader = "UViewReader"
roi = "LineROI"
analyzer = "XPSAnalyzer"

[reader]
paths = ["test_raw_0.dat", "test_raw_1.dat", "test_raw_2.dat"]

[roi]
roi_file = "test.roi"

[analyzer]
onset = 0

[task]
num_peaks = 1
incident_voltage = 400

[result]
pixel_per_ev = 16.0
peak_shift = 0.0
"""


@pytest.fixture
def config_content():
    """Write a minimal TOML config file content."""

    return CONFIG_CONTENT.strip()


@pytest.fixture
def config_file(tmp_path, config_content):
    """Write a minimal TOML config file and return its path."""

    return make_config(tmp_path, config_content)


def test_config_init():
    """Test Config initialization."""

    config = Config(
        {
            "session": {"reader": "UViewReader", "analyzer": "XPSAnalyzer"},
            "reader": {"paths": ["test_raw_0.dat"]},
        }
    )

    assert config.session == {"reader": "UViewReader", "analyzer": "XPSAnalyzer"}
    assert config.reader == {"paths": ["test_raw_0.dat"]}
    assert config.roi == {}
    assert config.analyzer == {}
    assert config.task == {}
    assert config.result == {}


def test_config_content_content(config_file):
    """Test content returns a full configuration."""

    config = load_config(config_file)
    content = config.content

    assert content["session"]["reader"] == "UViewReader"
    assert content["session"]["roi"] == "LineROI"
    assert content["reader"]["paths"] == [
        "test_raw_0.dat",
        "test_raw_1.dat",
        "test_raw_2.dat",
    ]
    assert content["roi"]["roi_file"] == "test.roi"
    assert content["task"]["num_peaks"] == 1
    assert content["task"]["incident_voltage"] == 400
    assert content["result"]["pixel_per_ev"] == 16.0


def test_load_config_properties(config_file):
    """Test load_config returns a Config from TOML."""

    config = load_config(config_file)

    assert config.session == {
        "reader": "UViewReader",
        "roi": "LineROI",
        "analyzer": "XPSAnalyzer",
    }
    assert config.reader == {
        "paths": ["test_raw_0.dat", "test_raw_1.dat", "test_raw_2.dat"]
    }
    assert config.roi == {"roi_file": "test.roi"}
    assert config.analyzer == {"onset": 0}
    assert config.task == {"num_peaks": 1, "incident_voltage": 400}
    assert config.result == {"pixel_per_ev": 16.0, "peak_shift": 0.0}


def test_config_attribute_error(config_file):
    """Test Config raises for unknown attributes."""

    config = load_config(config_file)

    with pytest.raises(AttributeError, match="missing"):
        config.missing


def test_config_is_immutable(config_file):
    """Test Config blocks direct attribute assignment."""

    config = load_config(config_file)

    with pytest.raises(
        AttributeError, match="Config is immutable. Use with_changes method."
    ):
        config.task = {"num_peaks": 2}


def test_config_content_is_copied(config_file):
    """Test content changes do not mutate Config."""

    config = load_config(config_file)
    content = config.content
    content["task"]["num_peaks"] = 2

    assert config.task["num_peaks"] == 1

    config = load_config(config_file)
    task = config.task
    task["num_peaks"] = 2

    assert config.task["num_peaks"] == 1


def test_config_with_changes(config_file):
    """Test with_changes updates a section in a new Config."""

    config = load_config(config_file)
    updated = config.with_changes(task={"num_peaks": 2})

    assert config.task["num_peaks"] == 1
    assert updated.task["num_peaks"] == 2
    assert updated.task["incident_voltage"] == 400

    updated = config.with_changes(
        task={"calibration": {"pixel_per_ev": 8.0, "peak_shift": 3.75}}
    )

    assert "calibration" not in config.task
    assert updated.task["calibration"]["pixel_per_ev"] == 8.0
    assert updated.task["calibration"]["peak_shift"] == 3.75


def test_config_with_changes_replaces_result(config_file):
    """Test with_changes replaces result."""

    config = load_config(config_file)
    updated = config.with_changes(result={"pixel_per_ev": 8.0})

    assert config.result == {"pixel_per_ev": 16.0, "peak_shift": 0.0}
    assert updated.result == {"pixel_per_ev": 8.0}


def test_config_with_changes_raises(config_file):
    """Test with_changes raises for unknown sections."""

    config = load_config(config_file)

    with pytest.raises(KeyError, match="Unknown config section: missing"):
        config.with_changes(missing={})


def test_save_config_writes(tmp_path, config_file):
    """Test save_config writes standard TOML sections."""

    config = load_config(config_file).with_changes(task={"num_peaks": 2})
    output_path = tmp_path / "output.toml"

    save_config(config, output_path)

    content = output_path.read_text(encoding="utf-8")
    document = tomlkit.parse(content)
    assert list(document) == ["session", "reader", "roi", "analyzer", "task", "result"]
    assert document["task"]["num_peaks"] == 2
    assert document["result"]["pixel_per_ev"] == 16.0


def test_save_config_valid_content(tmp_path, config_file):
    """Test save_config output can be loaded again."""

    config = load_config(config_file)
    output_path = tmp_path / "output.toml"

    save_config(config, output_path)
    loaded = load_config(output_path)

    assert loaded.content == config.content
