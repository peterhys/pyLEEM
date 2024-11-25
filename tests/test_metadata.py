from pyleem.metadata import (
    get_header,
    convert_win_filetime,
    get_imgmeta,
    get_imgmeta_index,
)
import pytest


def test_get_header(header_bytes, header_parsed):
    """Test extract_headermeta function."""

    headermeta = get_header(header_bytes)

    assert headermeta == header_parsed


def test_convert_win_filetime():
    """Test convert_win_filetime function."""
    # Windows filetime for 2023-01-01 00:00:00
    win_time = 133170720000000000
    dt = convert_win_filetime(win_time)
    assert dt == "2023/01/01 13:40:00"


def test_get_imgmeta_index():
    """Test get_imgmeta_index function."""
    headermeta = {
        "file_header_size": 100,
        "img_header_size": 50,
        "marked_header_size": 128,
        "img_meta_size": 200,
    }

    slice = get_imgmeta_index(headermeta)
    assert slice.start == 278
    assert slice.stop == 478


def test_get_imgmeta(img_metabytes):
    """Test get_imgmeta function."""

    standard_tags = [1, 2]
    gauge_tags = [3]
    special_tags = {
        4: [("FOV Value", None, ""), (None, "<f", "")],
        5: [("Avg", "<H", ""), ("content", "<5s", "")],
        6: [(None, "<f", ""), ("Secs", "<f", "s")],
    }

    result = get_imgmeta(
        img_metabytes,
        std_tags=standard_tags,
        gauge_tags=gauge_tags,
        special_tags=special_tags,
    )
    assert result["Standard X"][0] == 1.0
    assert result["Standard X"][1] == "V"

    assert result["Standard. Y"][0] == 2.0
    assert result["Standard. Y"][1] == "mA"

    assert result["Gauge"][0] == 3.0
    assert result["Gauge"][1] == "mBar"

    assert result["FOV Value"][0] == "FOV"
    assert result["FOV Value"][1] == ""

    assert result["Avg"][0] == 1
    assert result["content"][0] == "Value"

    assert result["Secs"][0] == 1.0
    assert result["Secs"][1] == "s"


def test_get_imgmeta_user_tags(img_metabytes):
    """Test get_imgmeta function with user tags.

    Here we replace the parsing for a standard tag, gauge tag, and special tag.
    """

    standard_tags = [1, 2]
    gauge_tags = [3]
    special_tags = {
        4: [("FOV Value", None, ""), (None, "<f", "")],
        5: [("Avg", "<H", ""), ("content", "<5s", "")],
        6: [(None, "<f", ""), ("Secs", "<f", "s")],
    }

    user_tags = {
        1: [(None, None, ""), ("Sample Temperature", "<f", "°C")],
        3: [(None, "<11s", ""), ("PCH", "<f", "mTorr")],
        4: [
            ("Preset (FOV)", None, ""),
            ("Undetermined", "<f", ""),
        ],  # predefined tag
    }

    result = get_imgmeta(
        img_metabytes, user_tags, standard_tags, gauge_tags, special_tags
    )

    assert result["Sample Temperature"][0] == 1.0
    assert result["Sample Temperature"][1] == "°C"

    assert result["PCH"][0] == 3.0
    assert result["PCH"][1] == "mTorr"

    assert result["Preset (FOV)"][0] == "FOV"
    assert result["Undetermined"][0] == 7.0


def test_get_imgmeta_invalid_tag():
    """Test get_imgmeta function with invalid tag."""

    mock_data = b"\xFF"  # termination tag
    result = get_imgmeta(mock_data)
    assert result == {}

    with pytest.raises(ValueError, match="Unknown tag 32"):
        get_imgmeta(b"\x20")  # unknown tag
