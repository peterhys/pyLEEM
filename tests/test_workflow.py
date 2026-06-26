import pytest

from pyleem.analyzer import Analyzer
from pyleem.config import Config, load_config
from pyleem.reader import UViewReader
from pyleem.roi import LineROI
from pyleem.workflow import Workflow, get_reader_paths, resolve_path


@pytest.fixture
def mock_analyzer():
    class MockAnalyzer(Analyzer):
        """Test analyzer used by Workflow tests."""

        def __init__(self, readers, roi=None, onset=0, scale=1):
            super().__init__(readers=readers, roi=roi, onset=onset)
            self.scale = scale
            self.parameters = None

        def analyze(self, **parameters):
            """Test analyze stores task parameters and returns a result."""
            self.parameters = parameters
            return {
                "reader_count": len(self.readers),
                "scale": self.scale,
                "sigma": parameters["sigma"],
            }

    return MockAnalyzer


def workflow_config(paths=None, roi_file="test.roi", **changes):
    """Create a minimal workflow Config."""
    reader = {}
    if paths is not None:
        reader["paths"] = paths

    content = {
        "session": {
            "reader": "UViewReader",
            "roi": "LineROI",
            "analyzer": "MockAnalyzer",
        },
        "reader": reader,
        "roi": {"roi_file": roi_file},
        "analyzer": {"scale": 2},
        "task": {"sigma": 8, "background": "linear"},
    }
    return Config(content).with_changes(**changes)


CONFIG_CONTENT = """
[session]
reader = "UViewReader"
roi = "LineROI"
analyzer = "MockAnalyzer"

[reader]
paths = ["test_raw_0.dat", "test_raw_1.dat", "test_raw_2.dat"]

[roi]
roi_file = "test.roi"

[analyzer]
scale = 2

[task]
sigma = 8
background = "linear"
"""


@pytest.fixture
def config_content():
    """Write a minimal TOML workflow config content."""

    return CONFIG_CONTENT.strip()


def test_resolve_path(tmp_path):
    """Test resolve_path resolves paths against root."""

    absolute_path = tmp_path / "absolute.dat"

    assert resolve_path("relative.dat", tmp_path) == tmp_path / "relative.dat"
    assert resolve_path(absolute_path, tmp_path) == absolute_path


def test_get_reader_paths_paths(tmp_path):
    """Test get_reader_paths reads explicit paths."""

    config = workflow_config(paths=["test_raw_0.dat", "test_raw_1.dat"])

    assert get_reader_paths(config.reader, tmp_path) == [
        tmp_path / "test_raw_0.dat",
        tmp_path / "test_raw_1.dat",
    ]


def test_get_reader_paths_pattern(tmp_path):
    """Test get_reader_paths reads paths from a pattern."""

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test_raw_1.dat").touch()
    (data_dir / "test_raw_0.dat").touch()

    config = workflow_config(reader={"path_pattern": "data/*.dat"})

    assert get_reader_paths(config.reader, tmp_path) == [
        data_dir / "test_raw_0.dat",
        data_dir / "test_raw_1.dat",
    ]


def test_get_reader_paths_raises(tmp_path):
    """Test get_reader_paths raises for invalid config."""

    config = workflow_config(reader={"paths": ["a.dat"], "path_pattern": "*.dat"})

    with pytest.raises(
        ValueError, match="Reader requires either paths or path_pattern."
    ):
        get_reader_paths(config.reader, tmp_path)

    config = workflow_config(reader={})

    with pytest.raises(
        ValueError, match="Reader requires either paths or path_pattern."
    ):
        get_reader_paths(config.reader, tmp_path)


def test_workflow_builds(tmp_path, xps_multiple_raw_files, roi_file, mock_analyzer):
    """Test Workflow builds readers, ROI, and analyzer from Config content."""

    paths = [path.name for path in xps_multiple_raw_files]
    config = workflow_config(paths=paths, roi_file=roi_file.name)

    workflow = Workflow(config, root=tmp_path)

    assert [reader.path for reader in workflow.readers] == xps_multiple_raw_files
    assert all(isinstance(reader, UViewReader) for reader in workflow.readers)
    assert isinstance(workflow.roi, LineROI)
    assert workflow.roi.src == (0, 0)
    assert workflow.roi.dst == (0, 127)
    assert isinstance(workflow.analyzer, mock_analyzer)
    assert workflow.analyzer.scale == 2


def test_workflow_builds_from_file(
    tmp_path, config_file, xps_multiple_raw_files, roi_file
):
    """Test Workflow builds from a loaded TOML Config file."""

    config = load_config(config_file)

    workflow = Workflow(config, root=tmp_path)

    assert [reader.path for reader in workflow.readers] == xps_multiple_raw_files
    assert workflow.roi.src == (0, 0)
    assert workflow.roi.dst == (0, 127)
    assert workflow.analyzer.scale == 2


def test_workflow_init_updates_config(tmp_path, xps_multiple_raw_files, roi_file):
    """Test Workflow init updates Config before building objects."""

    paths = [path.name for path in xps_multiple_raw_files]
    config = workflow_config(paths=paths, roi_file=roi_file.name)

    workflow = Workflow(
        config,
        root=tmp_path,
        analyzer={"scale": 3},
        task={"window": 5},
    )

    assert workflow.analyzer.scale == 3
    assert workflow.config.task == {
        "sigma": 8,
        "background": "linear",
        "window": 5,
    }


def test_workflow_run_updates_config(tmp_path, xps_multiple_raw_files, roi_file):
    """Test Workflow run merges task parameters and stores result."""

    paths = [path.name for path in xps_multiple_raw_files]
    config = workflow_config(paths=paths, roi_file=roi_file.name)
    workflow = Workflow(config, root=tmp_path)
    original_config = workflow.config

    result = workflow.run(sigma=10)

    assert result == {"reader_count": 3, "scale": 2, "sigma": 10}
    assert workflow.analyzer.parameters == {"sigma": 10, "background": "linear"}
    assert workflow.config is not original_config
    assert original_config.task == {"sigma": 8, "background": "linear"}
    assert workflow.config.task == {"sigma": 10, "background": "linear"}
    assert workflow.config.result == result


def test_workflow_save(tmp_path, xps_multiple_raw_files, roi_file):
    """Test Workflow saves the updated Config."""

    paths = [path.name for path in xps_multiple_raw_files]
    config = workflow_config(paths=paths, roi_file=roi_file.name)
    workflow = Workflow(config, root=tmp_path)
    workflow.run(sigma=10)

    output_path = tmp_path / "workflow_output.toml"
    workflow.save(output_path)
    saved = load_config(output_path)

    assert saved.task == {"sigma": 10, "background": "linear"}
    assert saved.result == {"reader_count": 3, "scale": 2, "sigma": 10}


def test_workflow_builds_without_config(
    tmp_path, xps_multiple_raw_files, roi_file, mock_analyzer
):
    """Test Workflow builds without a config.

    Here we combine the test for build, run, and save.
    """

    paths = [path.name for path in xps_multiple_raw_files]

    workflow = Workflow(
        config=None,
        root=tmp_path,
        session={
            "reader": "UViewReader",
            "roi": "LineROI",
            "analyzer": "MockAnalyzer",
        },
        reader={"paths": paths},
        roi={"roi_file": roi_file.name},
        analyzer={"scale": 2},
        task={"sigma": 8, "background": "linear"},
    )

    assert [reader.path for reader in workflow.readers] == xps_multiple_raw_files
    assert isinstance(workflow.roi, LineROI)
    assert isinstance(workflow.analyzer, mock_analyzer)
    assert workflow.config.task == {"sigma": 8, "background": "linear"}

    workflow.run(sigma=10)
    assert workflow.config.task == {"sigma": 10, "background": "linear"}
    assert workflow.config.result == {"reader_count": 3, "scale": 2, "sigma": 10}

    workflow.save(tmp_path / "workflow_output.toml")
    saved = load_config(tmp_path / "workflow_output.toml")
    assert saved.task == {"sigma": 10, "background": "linear"}
    assert saved.result == {"reader_count": 3, "scale": 2, "sigma": 10}
