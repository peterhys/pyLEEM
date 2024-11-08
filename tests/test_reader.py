import pytest
from pyleem.reader import RawReader
from datetime import datetime
import numpy as np


@pytest.fixture
def metadat_bytes(header_bytes):
    """Create an example metadata bytes."""

    empty_1 = b"\xff" * 240

    marker = (
        b"\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04"
        b"\x00\x00\x80\x00\x00\x00\x03\x00\xce\x02\xc7\x03'\x01e\x00$\x01\n\x00"
    )
    empty_2 = b"\x00" * 110

    img_header = (
        b"\xd2ALE1\x00\x00\x00\x00C\xcbAL2\x00sO\xc3G"
        b"h\x00\x00\x00C\x10\x01"
        b"\xecECH\x00MTorr\x00\x00\x00\x00C"
        b"\xe4\x00\x00\x00C\x00\x00\x00C\xbeME5\x00\xf3O\xc3G"
        b"nXPS\x00\x00\x00\x80Eq\x00\x00\x00\x00\xff\xff"
    )

    return header_bytes + empty_1 + marker + empty_2 + img_header


@pytest.fixture
def img_array():
    """Create an example image array."""

    return np.random.rand(256, 128).astype(np.uint16)


@pytest.fixture
def reader(tmp_path, metadat_bytes, img_array):
    """Create a raw file.

    The raw data has lenght of 2332 bytes.
    """
    raw_file = tmp_path / "test.raw"
    # append filler
    # append image bytes
    img_bytes = img_array.tobytes()
    raw_file.write_bytes(metadat_bytes + b"\xff" * 2000 + img_bytes)

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


def test_subset_value(reader):

    values = reader.subset_value(["ALE", "AL", "ME"])
    assert values == {
        "ALE": 128.0,
        "AL": "Invalid",
        "ME": "Local",
    }


def test_subset_unit(reader):
    """Test extract the units."""

    keys = ["ALE", "AL", "ME"]
    units = reader.subset_unit(keys)
    assert units == {"ALE": "V", "AL": "mA", "ME": "K"}


def test_list_headers(reader, header_parsed):
    """Test header keys."""

    assert sorted(reader.list_headers()) == sorted(list(header_parsed.keys()))


def test_list_metadata(reader, img_metadata_parsed):
    """Test metadata keys."""

    assert sorted(reader.list_metadata()) == sorted(list(img_metadata_parsed.keys()))


def test_image_array(reader, img_array):
    """Test the image array."""

    assert np.array_equal(reader.img, img_array)


def test_image_false(tmp_path, metadat_bytes):
    """Test the image array if img_read is False."""

    raw_file = tmp_path / "test.raw"
    # append filler
    raw_file.write_bytes(metadat_bytes + b"\xff" * 2000)

    reader = RawReader(raw_file, metasize=2000, read_img=False)

    assert reader.img is None
