import pytest
import struct
import numpy as np
import cv2
from pyleem.roi import LineROI


def set_start_voltage(metadata_bytes, voltage):
    """Return a copy of metadata_bytes with the Start Voltage tag replaced."""
    return (
        metadata_bytes[:-22]
        + b"\x26Start Voltage1\x00"
        + struct.pack("<f", voltage)
        + b"\xff\xff"
    )


def create_xps_array(center=60, sigma=10):
    """Create an example XPS image array (256x128 pixels)."""
    img_array = np.zeros((256, 128), dtype=np.uint16)
    x = np.arange(128)
    peak = 500 * np.exp(-((x - center) ** 2) / (2 * sigma**2))
    background = 100 + 100 / (1 + np.exp(0.06 * (x - center)))
    img_array[0, :] = (peak + background).astype(np.uint16)
    return img_array


def create_sees_array(center=60, sigma=10):
    """Create an example SEES image array (256x128 pixels)."""
    sees_array = np.zeros((256, 128), dtype=np.uint16)
    x = np.arange(128)
    profile = 500 / (1 + np.exp(-(x - center) / sigma))
    sees_array[0, :] = profile.astype(np.uint16)
    return sees_array


def create_noisy_array(seed=0):
    """Create a low-signal noise image array (256x128 pixels)."""
    noisy_array = np.zeros((256, 128), dtype=np.uint16)
    noisy_array[0, :] = np.random.default_rng(seed).integers(0, 4, 128, dtype=np.uint16)
    return noisy_array


@pytest.fixture
def header_bytes():
    header = (
        b"UKSOFT2001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\x00\t\x00\x10"
        b"\x01\x10\x00\x00\x00\x04\x04\x11\x00\x00\x00\x00\x00\x00\x00\x80"
        b"\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x01"
        b"\x07\x00\x01\x00\xbb\x01"
        b"\x00\x00\x81\x92\xb1z\xdc\x01"
        b"\x00\x01\x00\x00\x00\x00\x16\x00\x00\x00\xd0\x07"
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
        "FileSize": 104,
        "FileVersion": 9,
        "BitsPerPixel": 272,
        "CameraBitsPerPixel": 16,
        "MCPDiameterInPixels": 0,
        "HorizontalBinning": 4,
        "VerticalBinning": 4,
        "ImageWidth": 128,
        "ImageHeight": 256,
        "NrImages": 1,
        "attachedRecipeSize": 0,
        "recipe": None,
        "ImageSize": 288,
        "ImageVersion": 7,
        "ColorScaleLow": 1,
        "ColorScaleHigh": 443,
        "ImageTime": "2026/01/01 00:00:00.000000",
        "MaskXShift": 256,
        "MaskYShift": 0,
        "RotateMask": 0,
        "attachedMarkupSize": 22,
        "spin": 0,
        "LEEMdataVersion": 2000,
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
        b"nXPS\x00\x00\x00\x80Eq\x00\x00\x00\x00"
        b"\x26Start Voltage1\x00\x00\x00HC"
        b"\xff\xff"
    )

    return header_bytes + empty_1 + marker + empty_2 + img_header


@pytest.fixture
def xps_array():
    """Create an example XPS image array."""
    return create_xps_array()


@pytest.fixture
def noisy_array():
    """Create a low-signal noise image array."""
    return create_noisy_array()


@pytest.fixture
def sees_array():
    """Create an example SEES image array."""
    return create_sees_array()


@pytest.fixture
def xps_raw_file(tmp_path, metadata_bytes, xps_array):
    """Create a single XPS raw file."""
    raw_file = tmp_path / "test.dat"
    raw_file.write_bytes(metadata_bytes + b"\xff" * 2000 + xps_array.tobytes())
    return raw_file


@pytest.fixture
def noisy_raw_file(tmp_path, metadata_bytes, noisy_array):
    """Create a single low-signal noise raw file."""
    raw_file = tmp_path / "test_noisy.dat"
    raw_file.write_bytes(metadata_bytes + b"\xff" * 2000 + noisy_array.tobytes())
    return raw_file


@pytest.fixture
def sees_raw_file(tmp_path, metadata_bytes, sees_array):
    """Create a single SEES raw file."""
    modified_metadata = set_start_voltage(metadata_bytes, 0.0)
    sees_file = tmp_path / "test_sees.dat"
    sees_file.write_bytes(modified_metadata + b"\xff" * 2000 + sees_array.tobytes())
    return sees_file


@pytest.fixture
def desp_raw_file(tmp_path, metadata_bytes):
    """Create a single DESP raw file with a circular pattern."""
    image = np.zeros((256, 128), dtype=np.uint16)
    cv2.circle(image, (64, 128), 40, 1000, -1)
    desp_file = tmp_path / "test_desp.dat"
    desp_file.write_bytes(metadata_bytes + b"\xff" * 2000 + image.tobytes())
    return desp_file


@pytest.fixture
def xps_multiple_raw_files(tmp_path, metadata_bytes):
    """Create multiple XPS raw files with different start voltages and timestamps."""
    files = []

    # timestamps 1 minute apart
    image_times = [
        b"\x00FD\xb6\xb1z\xdc\x01",
        b"\x00\x8c\x07\xda\xb1z\xdc\x01",
        b"\x00\xd2\xca\xfd\xb1z\xdc\x01",
    ]
    header_original = b"\x00\x00\x81\x92\xb1z\xdc\x01"

    for i in range(3):
        modified_metadata = set_start_voltage(metadata_bytes, 114.0 + i * 1.0)
        modified_metadata = modified_metadata.replace(header_original, image_times[i])

        raw_file = tmp_path / f"test_raw_{i}.dat"
        raw_file.write_bytes(
            modified_metadata[: len(metadata_bytes)]
            + b"\xff" * 2000
            + create_xps_array(center=80 - i * 16).tobytes()
        )
        files.append(raw_file)
    return files


@pytest.fixture
def sees_multiple_raw_files(tmp_path, metadata_bytes):
    """Create multiple SEES raw files with different start voltages."""
    files = []

    for i in range(3):
        modified_metadata = set_start_voltage(metadata_bytes, 0.0 + i * 1.0)

        sees_file = tmp_path / f"test_sees_{i}.dat"
        sees_file.write_bytes(
            modified_metadata
            + b"\xff" * 2000
            + create_sees_array(center=80 - i * 16).tobytes()
        )
        files.append(sees_file)
    return files


@pytest.fixture
def desp_radius_to_energy_func():
    """Create a potential function."""
    return lambda x: 0.01 * x**2 + 5


@pytest.fixture
def desp_files(tmp_path, metadata_bytes, desp_radius_to_energy_func):
    """Create multiple DESP raw files with different circle radii."""
    files = []

    for i in range(3):
        modified_metadata = set_start_voltage(
            metadata_bytes, desp_radius_to_energy_func(20 + i * 20)
        )
        image = np.zeros((256, 128), dtype=np.uint16)
        cv2.circle(image, (64, 128), 20 + i * 20, 1000, -1)

        desp_file = tmp_path / f"test_desp_{i}.dat"
        desp_file.write_bytes(modified_metadata + b"\xff" * 2000 + image.tobytes())
        files.append(desp_file)
    return files


@pytest.fixture
def roi():
    """Create an uncalibrated LineROI (vertical line, 128 pixels)."""
    return LineROI(src=(0, 0), dst=(0, 127), linewidth=1)


@pytest.fixture
def roi_file(tmp_path, roi):
    """Save the conftest roi fixture to a temporary ImageJ ROI file."""

    roi_path = tmp_path / "test.roi"
    roi.to_roi_object().tofile(roi_path)
    return roi_path


@pytest.fixture
def pixel_per_ev():
    """Create a pixel per eV function."""
    return 16


@pytest.fixture
def peak_shift():
    """Create a peak shift function."""
    return 0
