from pathlib import Path
from pyleem.reader import Reader, read_files
from pyleem.roi import ROI
from pyleem.analyzer import Analyzer
from pyleem.config import Config, save_config


def resolve_path(path, root):
    """Resolve a path against the root directory."""
    path = Path(path)
    return path if path.is_absolute() else root / path


def get_reader_paths(reader_content, root):
    """Return reader paths resolved against the workflow root."""

    if "paths" in reader_content and "path_pattern" in reader_content:
        raise ValueError("Reader requires either paths or path_pattern.")
    if "paths" in reader_content:
        return [resolve_path(path, root) for path in reader_content["paths"]]
    if "path_pattern" in reader_content:
        return sorted(root.glob(reader_content["path_pattern"]))

    raise ValueError("Reader requires either paths or path_pattern.")


class Workflow:
    """Build and run analyzers from Config content.

    The workflow requires the analyzer to always take
    readers, roi, and allows additional kwargs.

    The workflow only runs the analyze method of the analyzer.
    If the result contains content that are not pickleable, the analyzer should
    specify the result keys to save.
    """

    def __init__(self, config=None, root=None, **kwargs):
        self.root = Path(root or ".")
        config = config or Config()
        self.config = config.with_changes(**kwargs)
        self.roi = self.build_roi()
        self.readers = self.build_readers()
        self.analyzer = self.build_analyzer()

    def build_readers(self):
        """Resolve path and build readers."""
        reader_class = Reader.REGISTRY[self.config.session["reader"]]
        paths = get_reader_paths(self.config.reader, self.root)

        return read_files(paths, reader_class)

    def build_roi(self):
        """Build the ROI from the configuration."""
        roi_name = self.config.session.get("roi", "NoROI")
        roi_class = ROI.REGISTRY[roi_name]
        roi_config = dict(self.config.roi)

        if "roi_file" in roi_config and roi_config["roi_file"] is not None:
            roi_config["roi_file"] = resolve_path(roi_config["roi_file"], self.root)

        return roi_class(**roi_config)

    def build_analyzer(self):
        """Build the analyzer from the configuration."""
        analyzer_class = Analyzer.REGISTRY[self.config.session["analyzer"]]

        return analyzer_class(
            readers=self.readers,
            roi=self.roi,
            **self.config.analyzer,
        )

    def run(self, **parameters):
        """Run the workflow."""
        task = self.config.task
        task.update(parameters)

        result = self.analyzer.analyze(**task)
        saved_result = self.get_saved_result(result)

        self.config = self.config.with_changes(task=task, result=saved_result)

        return result

    def get_saved_result(self, result):
        """Return the result content that should be stored in Config."""
        save_keys = getattr(self.analyzer, "save_keys", None)

        if save_keys is None:
            return result

        return {key: result[key] for key in save_keys}

    def save(self, path):
        """Export the workflow to a configuration file."""
        save_config(self.config, path)
