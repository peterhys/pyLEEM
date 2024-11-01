import pytest
from datetime import datetime
import struct


@pytest.fixture
def header_bytes():
    header = (
        b"UKSOFT2001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\x00\t\x00\x10"
        b"\x01\x10\x00\x00\x00\xb4\x04\x11\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x05\x00\x05\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x01"
        b"\x07\x00\x01\x00\xbb\x01\x80\xb6rl\xdd \xdb\x11\x00\x01\x00\x00\x00"
        b"\x00\x16\x00\x00\x00\xd0\x07"
    )

    return header


@pytest.fixture
def img_metabytes():

    content = {
        1: b"\x01Standard X1\x00" + struct.pack("<f", 1.0),
        2: b"\x02Standard. Y2\x00" + struct.pack("<f", 2.0),
        3: b"\x03Gauge\x00mBar\x00" + struct.pack("<f", 3.0),
        4: b"\x04FOV\x00" + struct.pack("<f", 7.0),
        5: b"\x05" + struct.pack("<H", 1) + struct.pack("<5s", b"Value"),
        6: b"\x06\x00\x00\x00\x00" + struct.pack("<f", 1.0),
    }

    content_bytes = b"".join(content.values())
    return content_bytes


@pytest.fixture
def header_parsed():
    """Return the parsed header."""

    return {
        "filetype": "UKSOFT2001",
        "file_header_size": 104,
        "file_version": 9,
        "bits_per_pixel": 272,
        "camera_bits_per_pixel": 16,
        "MCP_diam": 0,
        "hbinning": 1204,
        "vbinning": 17,
        "width": 1280,
        "height": 1280,
        "no_images": 1,
        "attachedrecipesize": 0,
        "recipe": None,
        "img_header_size": 288,
        "img_version": 7,
        "colorscale_low": 1,
        "colorscale_high": 443,
        "timestamp": datetime(5678, 4, 4, 15, 3, 12, 372681),
        "mask_xshift": 256,
        "mask_yshift": 0,
        "usemask": 0,
        "attachedmarkedsize": 22,
        "marked_header_size": 128,
        "spin": 0,
        "img_meta_size": 2000,
    }
