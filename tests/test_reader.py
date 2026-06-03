import pytest
from pyleem.reader import UViewReader
import numpy as np


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


def test_reader_read_image(reader, xps_array):
    """Test reader read_image method."""
    image = reader.read_image()
    assert np.array_equal(image, xps_array)
