import pytest
from datetime import datetime
import struct
import numpy as np


@pytest.fixture
def header_bytes():
    header = (
        b"UKSOFT2001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\x00\t\x00\x10"
        b"\x01\x10\x00\x00\x00\xb4\x04\x11\x00\x00\x00\x00\x00\x00\x00\x80"
        b"\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
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
        "width": 128,
        "height": 256,
        "no_images": 1,
        "attachedrecipesize": 0,
        "recipe": None,
        "img_header_size": 288,
        "img_version": 7,
        "colorscale_low": 1,
        "colorscale_high": 443,
        "timestamp": "5678/04/04 15:03:12",
        "mask_xshift": 256,
        "mask_yshift": 0,
        "usemask": 0,
        "attachedmarkedsize": 22,
        "marked_header_size": 128,
        "spin": 0,
        "img_meta_size": 2000,
    }


@pytest.fixture
def metadata_bytes(header_bytes):
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
def raw_file(tmp_path, metadata_bytes, img_array):
    """Create a raw file.

    The raw data has lenght of 2332 bytes.
    """
    raw_file = tmp_path / "test.raw"
    # append filler
    # append image bytes
    img_bytes = img_array.tobytes()
    raw_file.write_bytes(metadata_bytes + b"\xff" * 2000 + img_bytes)

    return raw_file
