import matplotlib.pyplot as plt
import numpy as np
import pytest
from pyleem.analyzer import Analyzer, find_onset


def test_find_onset():
    """Test find_onset with 2D images.

    Low noise frames followed by signal frames."""

    shape = (20, 20)
    images = np.zeros((10, *shape))
    images[:5] = np.random.normal(0.1, 0.1, (5, *shape))
    images[5:] = np.random.normal(0.1, 0.1, (5, *shape)) + 10  # added signal

    onset_idx = find_onset(images)
    assert onset_idx == 4


@pytest.fixture
def mock_analyzer():

    class AnnotatedAnalyzer(Analyzer):
        """Analyzer subclass for testing processed images and overlays."""

        def __init__(self, *args, **kwargs):
            self.annotation_indexes = []
            super().__init__(*args, **kwargs)

        def get_processed_image(self, index):
            """Return a visibly processed image."""
            return self.get_raw_image(index) + 1

        def get_annotated_image(self, index):
            """Return a visibly annotated image."""
            return self.get_raw_image(index) + 2

        def annotate_image(self, index, ax):
            """Draw a simple overlay."""
            self.annotation_indexes.append(index)
            ax.axhline(0, color="red")
            return ax

    return AnnotatedAnalyzer


def test_analyzer_readers(xps_readers):
    """Test Analyzer stores the reader list."""
    analyzer = Analyzer(xps_readers)

    assert analyzer.readers == xps_readers


def test_analyzer_raises():
    """Test Analyzer requires at least one reader."""
    with pytest.raises(ValueError, match="readers cannot be empty"):
        Analyzer([])


def test_analyzer_onset(xps_readers):
    """Test Analyzer onset slices readers."""
    analyzer = Analyzer(xps_readers, onset=1)

    assert analyzer.onset == 1
    assert analyzer.readers == xps_readers[1:]


def test_analyzer_indices(xps_readers):
    """Test Analyzer indices match the active reader list."""
    analyzer = Analyzer(xps_readers)
    onset_analyzer = Analyzer(xps_readers, onset=1)

    assert list(analyzer.indices) == [0, 1, 2]
    assert list(onset_analyzer.indices) == [0, 1]


def test_analyzer_onset_raises(xps_reader):
    """Test Analyzer onset raises if no readers after slicing."""
    with pytest.raises(ValueError, match="readers empty after onset"):
        Analyzer([xps_reader], onset=1)


def test_analyzer_onset_auto(create_reader):
    """Test Analyzer can derive onset from image intensity."""
    images = [
        np.ones((256, 128), dtype=np.uint16),
        np.ones((256, 128), dtype=np.uint16) * 2,
        np.ones((256, 128), dtype=np.uint16) * 20,
    ]
    readers = [
        create_reader(f"onset_{index}.dat", image)
        for index, image in enumerate(images)
    ]

    analyzer = Analyzer(readers, onset=None)

    assert analyzer.onset == 1
    assert analyzer.readers == readers[1:]


def test_analyzer_get_image(xps_reader, mock_analyzer):
    """Test get_image dispatches raw and processed images."""
    analyzer = mock_analyzer([xps_reader])

    assert np.array_equal(analyzer.get_raw_image(0), xps_reader.image)
    assert np.array_equal(analyzer.get_processed_image(0), xps_reader.image + 1)


def test_analyzer_plot_image(xps_reader, mock_analyzer):
    """Test plot_image draws the processed image."""
    analyzer = mock_analyzer([xps_reader])
    fig, ax = plt.subplots()

    # default, processed image
    analyzer.plot_image(0, ax=ax)

    plotted = np.asarray(ax.images[0].get_array())
    assert np.array_equal(plotted, xps_reader.image + 1)
    plt.close(fig)


def test_analyzer_plot_image_annotated(xps_reader, mock_analyzer):
    """Test plot_image calls annotate_image for annotated images."""
    analyzer = mock_analyzer([xps_reader])
    fig, ax = plt.subplots()

    returned = analyzer.plot_image(0, ax=ax, annotate=True)

    assert returned is ax
    assert analyzer.annotation_indexes == [0]
    assert len(ax.lines) == 1
    plt.close(fig)


def test_analyzer_get_autolevel(xps_reader):
    """Test autolevel returns percentile display limits."""
    analyzer = Analyzer([xps_reader])
    image = np.arange(101, dtype=float).reshape(1, 101)

    vmin, vmax = analyzer.get_autolevel(image)

    assert vmin == pytest.approx(1)
    assert vmax == pytest.approx(99)


def test_analyzer_plot_image_autolevel(create_reader, mock_analyzer):
    """Test plot_image autolevel changes display limits only."""
    image = np.arange(256 * 128, dtype=np.uint16).reshape(256, 128)
    reader = create_reader("autolevel.dat", image)
    analyzer = mock_analyzer([reader])
    fig, ax = plt.subplots()

    analyzer.plot_image(0, ax=ax, autolevel=True)

    plotted = np.asarray(ax.images[0].get_array())
    expected_image = image + 1
    expected_limits = np.percentile(expected_image, [1, 99])

    assert np.array_equal(plotted, expected_image)
    assert ax.images[0].get_clim() == pytest.approx(tuple(expected_limits))
    plt.close(fig)


def test_analyzer_get_measurement(xps_reader, roi, mock_analyzer):
    """Test get_measurement measures the processed image by default."""
    analyzer = mock_analyzer([xps_reader], roi=roi)

    measurement = analyzer.get_measurement(0)
    assert np.array_equal(measurement.profile, xps_reader.image[0, :] + 1)


def test_analyzer_get_profile(xps_reader, roi, mock_analyzer):
    """Test get_profile returns the ROI measurement profile."""
    analyzer = mock_analyzer([xps_reader], roi=roi)

    profile = analyzer.get_profile(0)

    assert np.array_equal(profile, xps_reader.image[0, :] + 1)


def test_analyzer_get_pixel(xps_reader, roi, mock_analyzer):
    """Test get_pixel returns profile pixel positions."""
    analyzer = mock_analyzer([xps_reader], roi=roi)

    pixel = analyzer.get_pixel(0)

    assert np.array_equal(pixel, np.arange(128))


def test_analyzer_get_pixel_raises(xps_reader, mock_analyzer):
    """Test get_pixel raises when profile is not available."""
    analyzer = mock_analyzer([xps_reader])
    analyzer.get_profile = lambda index: None

    with pytest.raises(ValueError, match="Profile is not available"):
        analyzer.get_pixel(0)


def test_analyzer_get_metadata(xps_readers):
    """Test get_metadata returns metadata values without units."""
    analyzer = Analyzer(xps_readers)

    assert analyzer.get_metadata("Start Voltage", 0) == (114.0, "V")
    assert analyzer.get_metadata("Start Voltage", 1) == (115.0, "V")
    assert analyzer.get_metadata("Start Voltage", 2) == (116.0, "V")


def test_analyzer_unimplemented(xps_reader):
    """Test base Analyzer raises if method is not implemented."""
    analyzer = Analyzer([xps_reader])

    with pytest.raises(
        NotImplementedError, match="'analyze' method is not implemented"
    ):
        analyzer.analyze()


def test_analyzer_subclasses_registry(mock_analyzer):
    """Test Analyzer subclasses are registered in the registry."""
    assert Analyzer.REGISTRY["AnnotatedAnalyzer"] is mock_analyzer
    assert Analyzer.REGISTRY["Analyzer"] is Analyzer
