import pytest
from pyleem.reader import UViewReader, UViewReaderGroup
import numpy as np
import matplotlib.pyplot as plt


@pytest.fixture
def reader(xps_raw_file):
    """Create a reader from a raw file."""
    return UViewReader(xps_raw_file)


def test_reader_metadata(reader):
    """Test reader metadata."""
    assert len(reader.metabytes) == UViewReader.METASIZE
    assert reader.metadata["AL"][0] == "invalid"
    assert reader.metadata["Camera Average"][0] == 16
    assert reader.metadata["ALE"][0] == 128.0
    assert reader.metadata["AL"][1] == "mA"
    assert reader.metadata["ALE"][1] == "V"
    assert reader.metadata["Camera Average"][1] is None


def test_reader_image(reader, xps_array):
    """Test reader image property."""
    image = reader.image
    assert np.array_equal(image, xps_array)


def test_reader_sort(tmp_path, metadata_bytes):
    """Test sorting readers by path."""
    file1 = tmp_path / "a_test.dat"
    file2 = tmp_path / "b_test.dat"

    file1.write_bytes(metadata_bytes + b"\xff" * 2000)
    file2.write_bytes(metadata_bytes + b"\xff" * 2000)

    reader1 = UViewReader(file1)
    reader2 = UViewReader(file2)
    assert reader1 < reader2


def test_reader_group_time_intervals(xps_multiple_raw_files):
    """Test reader group time intervals start at zero."""

    reader_group = UViewReaderGroup(xps_multiple_raw_files)

    assert len(reader_group.time_intervals) == 3
    assert reader_group.time_intervals[0] == 0
    assert reader_group.time_intervals[1] == 60
    assert reader_group.time_intervals[2] == 120

    assert reader_group.readers[0].metadata["TimeInterval"] == (0, "s")
    assert reader_group.readers[1].metadata["TimeInterval"] == (60, "s")
    assert reader_group.readers[2].metadata["TimeInterval"] == (120, "s")


def test_reader_plot_image(reader):
    """Test reader plot_image method."""
    fig, ax = plt.subplots()
    reader.plot_image(ax=ax)
    assert len(ax.images) == 1
    plt.close(fig)

    reader.plot_image(ax=None)
    assert len(plt.get_fignums()) == 1
    plt.close("all")
