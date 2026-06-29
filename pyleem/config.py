"""Configuration snapshots for workflow analysis runs.

The file is structured as follows:

```toml
[session]
version = "0.1.0"
reader = "UViewReader"
roi = "LineROI"
analyzer = "XPSAnalyzer"

[reader]
paths = ["data_0eV.dat", "data_1eV.dat", "data_2eV.dat"]

[roi]
roi_file = "line.roi"

[analyzer]
onset = 0

[task]
num_peaks = 1
baselines = [[197, 100], [197, 100], [197, 100]]
ref_index = 0
ref_value = 285.0
incident_voltage = 400

[result]
pixel_per_ev = 166.0
peak_shift = 3.75
```
"""

from copy import deepcopy
from pathlib import Path

import tomlkit


class Config:
    """Immutable configuration snapshot."""

    sections = ("session", "reader", "roi", "analyzer", "task")
    replace_sections = ("result",)

    def __init__(self, content=None):
        content = content or {}
        full_content = {}

        for section in self.sections + self.replace_sections:
            full_content[section] = deepcopy(content.get(section, {}))

        object.__setattr__(self, "_content", full_content)

    def __setattr__(self, name, value):
        raise AttributeError("Config is immutable. Use with_changes method.")

    def __getattr__(self, name):
        if name in self.sections + self.replace_sections:
            return self.content[name]

        raise AttributeError(name)

    @property
    def content(self):
        """Get a copy of the config content."""
        return deepcopy(self._content)

    def with_changes(self, **changes):
        """Create a new config with changes."""
        content = self.content

        for section, values in changes.items():
            if section not in self.sections + self.replace_sections:
                raise KeyError(f"Unknown config section: {section}")

            if values is not None:
                if section in self.replace_sections:
                    content[section] = deepcopy(values)
                else:
                    content[section].update(deepcopy(values))

        return Config(content)


def load_config(path):
    """Load a configuration file."""
    path = Path(path)
    content = tomlkit.parse(path.read_text(encoding="utf-8"))

    return Config(content)


def save_config(config, path):
    """Save a configuration file."""
    path = Path(path)
    path.write_text(tomlkit.dumps(config.content), encoding="utf-8")
