from pyleem.metadata import (
    convert_win_filetime,
    get_metadata_fixed_header,
    parse_leem_data,
    is_tag_in_range,
)
import pytest
import struct
import numpy as np
from datetime import datetime


def test_convert_win_filetime():
    """Test Windows filetime conversion (UTC)."""
    win_time = 133801824000000000
    assert convert_win_filetime(win_time) == "2025/01/01 05:20:00.000000"


def test_get_metadata_fixed_header(metadata_bytes, header_parsed):
    """Test metadata extraction from bytes."""
    metadata = get_metadata_fixed_header(metadata_bytes)

    for key in header_parsed.keys():
        assert metadata[key][0] == header_parsed[key]

    # Verify timestamp conversion
    assert metadata["ImageTime"][0] == "2026/01/01 00:00:00.000000"
    assert isinstance(metadata["ImageTime"][0], str)
    assert isinstance(metadata["TimeStamp"][0], datetime)
    assert metadata["FOV"] == ("XPS", "um")

    # Verify all entries are tuples
    for value in metadata.values():
        assert isinstance(value, tuple) and len(value) == 2


def test_is_tag_in_range():
    """Test tag range checking with bit masking."""
    assert is_tag_in_range(50, (0, 99))
    assert is_tag_in_range(178, (0, 99))  # 178 & 0x7F = 50
    assert not is_tag_in_range(232, (0, 99))  # 232 & 0x7F = 104
    assert not is_tag_in_range(100, (0, 99))


def test_parse_standard_tags():
    """Test parsing standard tags."""
    # Tag with unit code
    data = b"\x02Start Voltage1\x00" + struct.pack("<f", 10.5)
    leemdata = parse_leem_data(data)
    assert leemdata["Start Voltage"][0] == 10.5
    assert leemdata["Start Voltage"][1] == "V"

    # Tag without unit code
    data = b"\x03Start Voltage\x00" + struct.pack("<f", 25.3)
    leemdata = parse_leem_data(data)
    assert leemdata["Start Voltage"][0] == pytest.approx(25.3, rel=1e-5, abs=1e-8)
    assert leemdata["Start Voltage"][1] is None

    # Standard tag with special markers
    data = b"\x02Start Voltage\x00" + b"sO\xc3G"
    leemdata = parse_leem_data(data)
    assert leemdata["Start Voltage"][0] == "invalid"

    data = b"\x03Control\x00" + b"\xf3O\xc3G"
    leemdata = parse_leem_data(data)
    assert leemdata["Control"][0] == "local"


def test_parse_gauge_tags():
    """Test parsing gauge tags."""
    data = b"\x6aPressure\x00Torr\x00" + struct.pack("<f", 1.5e-6)
    leemdata = parse_leem_data(data)
    assert leemdata["Pressure"][0] == pytest.approx(1.5e-6)
    assert leemdata["Pressure"][1] == "Torr"


def test_parse_camera_tags():
    """Test parsing camera exposure and average tags."""
    data = b"\x68" + struct.pack("<f", 0.5) + struct.pack("<BB", 4, 0)
    leemdata = parse_leem_data(data)
    assert leemdata["Camera Exposure"][0] == 0.5
    assert leemdata["Camera Average"][0] == 4
    assert leemdata["Camera Average Mode"][0] == "no average"

    # Different average modes
    data = b"\x68" + struct.pack("<f", 0.5) + struct.pack("<bb", 4, 1)
    assert parse_leem_data(data)["Camera Average Mode"][0] == "average"

    data = b"\x68" + struct.pack("<f", 0.5) + struct.pack("<bb", 4, -1)
    assert parse_leem_data(data)["Camera Average Mode"][0] == "sliding average"


def test_parse_special_tags():
    """Test parsing special tags."""
    # Image title
    data = b"\x69Test Image\x00"
    leemdata = parse_leem_data(data)
    assert leemdata["Image Title"][0] == "Test Image"

    # FOV tag
    data = b"\x6e10um\x00" + struct.pack("<f", 7.5)
    leemdata = parse_leem_data(data)
    assert leemdata["FOV"][0] == 10.0
    assert leemdata["FOV"][1] == "um"
    assert leemdata["Cal. FOV"][0] == pytest.approx(7.5)

    # Data tag (Micrometers)
    data = b"\x64" + struct.pack("<f", 100.5) + struct.pack("<f", 200.3)
    leemdata = parse_leem_data(data)
    assert leemdata["Micrometers X"][0] == pytest.approx(100.5)
    assert leemdata["Micrometers Y"][0] == pytest.approx(200.3)


def test_parse_cp1252_metadata():
    """Test metadata Windows cp1252/Latin-1 strings decoding."""
    # FOV tag (0x6e) carrying a cp1252 micro sign.
    data = b"\x6e10\xb5m\x00" + struct.pack("<f", 7.5)
    leemdata = parse_leem_data(data)
    assert leemdata["FOV"][0] == 10.0
    assert leemdata["FOV"][1] == "um"

    # Gauge tag (0x6a) with a micro sign in the unit (e.g. "uA").
    data = b"\x6aEmission\x00\xb5A\x00" + struct.pack("<f", 1.5)
    leemdata = parse_leem_data(data)
    assert leemdata["Emission"][1] == b"\xb5A".decode("cp1252")


def test_parse_end_marker():
    """Test end marker and complex tag combinations."""
    # Test end marker
    data = (
        b"\x02FOV\x00"
        + struct.pack("<f", 10.5)
        + b"\xff"
        + b"\x03Start Voltage\x00"
        + struct.pack("<f", 25.3)
    )
    leemdata = parse_leem_data(data)
    assert "FOV" in leemdata
    assert "Start Voltage" not in leemdata

    # Test multiple tag types
    data = (
        b"\x02FOV1\x00"
        + struct.pack("<f", 10.5)
        + b"\x6aPressure\x00mBar\x00"
        + struct.pack("<f", 2.5e-5)
        + b"\x68"
        + struct.pack("<f", 0.5)
        + struct.pack("<bb", 4, -1)
        + b"\xff"
    )
    leemdata = parse_leem_data(data)
    assert leemdata["FOV"][0] == 10.5
    assert leemdata["Pressure"][0] == pytest.approx(2.5e-5)
    assert leemdata["Camera Exposure"][0] == 0.5

    # Test empty data
    assert parse_leem_data(b"") == {}


def test_metadata_with_nan_values(header_bytes):
    """Test metadata handling of NaN values."""
    empty_1 = b"\xff" * 240
    marker = (
        b"\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04"
        b"\x00\x00\x80\x00\x00\x00\x03\x00\xce\x02\xc7\x03'\x01e\x00$\x01\n\x00"
    )
    empty_2 = b"\x00" * 110
    # Create tag with NaN value
    img_header = b"\x02Test\x00" + struct.pack("<f", float("nan")) + b"\xff\xff"

    metadata_bytes = header_bytes + empty_1 + marker + empty_2 + img_header
    metadata = get_metadata_fixed_header(metadata_bytes)

    assert "Test" in metadata
    assert np.isnan(metadata["Test"][0])
