import pytest
from pyleem.reader import RawReader
import numpy as np
import h5py


@pytest.fixture
def reader(raw_file):
    """Create a reader from a raw file.

    The raw data has lenght of 2332 bytes.
    """

    user_tags = {
        104: [("expo", "<f", "s"), ("avg", "<Bc", "")],
        228: [("X", "<f", "m"), ("Y", "<f", "m")],
    }
    return RawReader(raw_file, metasize=2500, user_tags=user_tags, read_img=True)


@pytest.fixture
def img_metadata_parsed():
    """Return the parsed image metadata."""

    return {
        "AL": ("Invalid", "mA", 203),
        "ALE": (128.0, "V", 210),
        "avg": (16, "", 104),
        "expo": (128.0, "s", 104),
        "ECH": (128.0, "MTorr", 236),
        "ME": ("Local", "K", 190),
        "X": (128.0, "m", 228),
        "Y": (128.0, "m", 228),
        "Preset (FOV):": ("XPS", "", 110),
    }


def test_reader_size(reader):
    """Test the length of the bytes."""

    assert len(reader.metabytes) == 2500


def test_header(reader, header_parsed):
    """Test the header."""

    assert reader.header == header_parsed


def test_imgmeta(reader, img_metadata_parsed):
    """Test the image metadata."""

    assert reader.imgmeta == img_metadata_parsed


def test_imgmeta_df(reader):
    """Test the image metadata dataframe."""

    assert reader.imgmeta_df.loc["AL", "value"] == "Invalid"
    assert reader.imgmeta_df.loc["avg", "unit"] == ""
    assert reader.imgmeta_df.loc["ME", "tag"] == 190


def test_subset_values(reader):

    values = reader.subset_values(["ALE", "AL", "ME"])
    assert values == [128.0, "Invalid", "Local"]


def test_subset_units(reader):
    """Test extract the units."""

    keys = ["ALE", "AL", "ME"]
    units = reader.subset_units(keys)
    assert units == ["V", "mA", "K"]


def test_list_headers(reader, header_parsed):
    """Test header keys."""

    assert sorted(reader.list_headers()) == sorted(list(header_parsed.keys()))


def test_list_metadata(reader, img_metadata_parsed):
    """Test metadata keys."""

    assert sorted(reader.list_metadata()) == sorted(list(img_metadata_parsed.keys()))


def test_image_array(reader, img_array):
    """Test the image array."""

    assert np.array_equal(reader.img, img_array)


def test_image_false(tmp_path, metadata_bytes):
    """Test the image array if img_read is False."""

    raw_file = tmp_path / "test.raw"
    # append filler
    raw_file.write_bytes(metadata_bytes + b"\xff" * 2000)

    reader = RawReader(raw_file, metasize=2000, read_img=False)

    assert reader.img is None


def test_comparison_less_than(tmp_path, metadata_bytes):
    """Test the equality comparison of RawReader instances."""
    raw_file1 = tmp_path / "test_equal_01.raw"
    raw_file1.write_bytes(metadata_bytes + b"\xff" * 2000)

    reader1 = RawReader(raw_file1, metasize=2500, read_img=False)

    raw_file2 = tmp_path / "test_equal_02.raw"
    raw_file2.write_bytes(metadata_bytes + b"\xff" * 2000)

    reader2 = RawReader(raw_file2, metasize=2500, read_img=False)

    assert reader1 < reader2


def test_repr(reader, raw_file):
    """Test the representation of the reader."""

    assert repr(reader) == f"RawReader({raw_file})"


def test_to_h5(reader, tmp_path):
    """Test the writing of the reader to a HDF5 file."""

    h5_file = tmp_path / "test.h5"
    with h5py.File(h5_file.as_posix(), "w") as f:
        reader.to_h5(f, write_img=True)

    with h5py.File(h5_file, "r") as f:
        group = f["test"]
        assert group.attrs["timestamp"] == reader.header["timestamp"]
        assert "image" in group
        assert np.array_equal(group["image"], reader.img)

        for key, value in reader.imgmeta.items():
            assert group["image"].attrs[key] == value[0]
            assert group["image"].attrs[key + "_unit"] == value[1]

    with h5py.File(h5_file.as_posix(), "w") as f:
        reader.to_h5(f, write_img=False)

    with h5py.File(h5_file, "r") as f:
        group = f["test"]
        assert "image" in group
        assert not np.array_equal(group["image"], reader.img)

        for key, value in reader.imgmeta.items():
            assert group["image"].attrs[key] == value[0]
            assert group["image"].attrs[key + "_unit"] == value[1]


def test_custom_h5(tmp_path, raw_file):
    """Test the custom HDF5 method."""

    h5_file = tmp_path / "test.h5"

    class CustomReader(RawReader):
        def custom_h5(self, group):
            group.attrs.update({"custom": "custom"})

    reader = CustomReader(raw_file, metasize=2500, read_img=False)
    with h5py.File(h5_file, "w") as f:
        reader.to_h5(f)

    with h5py.File(h5_file, "r") as f:
        group = f["test"]
        assert group.attrs["custom"] == "custom"
