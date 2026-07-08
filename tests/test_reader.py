import numpy as np
import matplotlib.pyplot as plt
import pytest

from pyleem.reader import UViewReader, read_files, get_time_intervals, find_onset


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


def test_reader_update_metadata(reader):
    """Test reader update_metadata method."""
    reader.update_metadata({"Beam Energy": (400.0, "eV")})
    assert reader.metadata["Beam Energy"] == (400.0, "eV")


def test_read_files_time_intervals(xps_multiple_raw_files):
    """Test read_files adds TimeInterval metadata."""

    readers = read_files(xps_multiple_raw_files, UViewReader)

    assert len(readers) == 3
    assert readers[0].metadata["TimeInterval"] == (0.0, "s")
    assert readers[1].metadata["TimeInterval"] == (60.0, "s")
    assert readers[2].metadata["TimeInterval"] == (120.0, "s")


def test_read_files_metadata_list(xps_multiple_raw_files):
    """Test read_files adds metadata."""

    readers = read_files(
        xps_multiple_raw_files,
        UViewReader,
        metadata_list=[
            {"Start Voltage": (2.0, "eV")},
            {"Start Voltage": (4.0, "eV")},
            {"Start Voltage": (6.0, "eV")},
        ],
    )

    assert len(readers) == 3
    assert readers[0].metadata["Start Voltage"] == (2.0, "eV")
    assert readers[1].metadata["Start Voltage"] == (4.0, "eV")
    assert readers[2].metadata["Start Voltage"] == (6.0, "eV")


def test_find_onset():
    """Test find_onset with 2D images.

    Low noise frames followed by signal frames."""

    shape = (20, 20)
    images = np.zeros((10, *shape))
    images[:5] = np.random.normal(0.1, 0.1, (5, *shape))
    images[5:] = np.random.normal(0.1, 0.1, (5, *shape)) + 10  # added signal

    onset_idx = find_onset(images)
    assert onset_idx == 5


def test_read_files_onset(xps_multiple_raw_files):
    """Test read_files onset slices readers."""
    readers = read_files(xps_multiple_raw_files, UViewReader, onset=1)

    assert len(readers) == 2
    assert [reader.path for reader in readers] == xps_multiple_raw_files[1:]


def test_read_files_onset_auto(create_reader):
    """Test read_files can derive onset from image intensity."""
    images = [
        np.ones((256, 128), dtype=np.uint16),
        np.ones((256, 128), dtype=np.uint16) * 2,
        np.ones((256, 128), dtype=np.uint16) * 20,
    ]
    expected_readers = [
        create_reader(f"onset_{index}.dat", image) for index, image in enumerate(images)
    ]

    readers = read_files(
        [reader.path for reader in expected_readers], UViewReader, onset=None
    )

    assert [reader.path for reader in readers] == [
        reader.path for reader in expected_readers[2:]
    ]


def test_reader_plot_image(reader):
    """Test reader plot_image method."""
    fig, ax = plt.subplots()
    reader.plot_image(ax=ax)
    assert len(ax.images) == 1
    plt.close(fig)

    ax = reader.plot_image(ax=None)

    assert len(ax.images) == 1
    assert ax.get_xlabel() == "X [pixels]"
    assert ax.get_ylabel() == "Y [pixels]"
    assert ax.get_title() == "Raw Image Data"


def test_get_time_intervals(xps_readers):
    """Test get_time_intervals returns seconds from the first reader."""
    assert get_time_intervals(xps_readers) == [0.0, 60.0, 120.0]
