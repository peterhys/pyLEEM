import numpy as np
import pytest

from pyleem.analysis.spectra import SpectraBase, kinetic_energy


def test_kinetic_energy():
    """Test kinetic_energy converts one pixel value."""
    result = kinetic_energy(
        pixel=32,
        start_voltage=114.0,
        pixel_per_ev=16,
        peak_shift=3.75,
    )

    assert result == pytest.approx(119.75)


def test_spectra_analyzer_get_kinetic_energy(xps_readers, roi):
    """Test SpectraAnalyzer builds kinetic energy from metadata."""
    analyzer = SpectraBase(
        readers=xps_readers,
        roi=roi,
        pixel_per_ev=16,
        peak_shift=3.75,
    )

    energy = analyzer.get_kinetic_energy(0)

    assert len(energy) == 128
    assert energy[0] == pytest.approx(117.75)
    assert energy[16] == pytest.approx(118.75)
    assert energy[-1] == pytest.approx(125.6875)


def test_spectra_analyzer_stitch_profiles(raw_reader_factory, roi):
    """Test SpectraAnalyzer stitches profiles by kinetic energy."""
    images = []
    for offset in [10, 60, 110]:
        image = np.zeros((256, 128), dtype=np.uint16)
        image[0, :] = np.arange(128) + offset
        images.append(image)

    readers = [
        raw_reader_factory(f"spectra_{index}.dat", image)
        for index, image in enumerate(images)
    ]
    for reader, start_voltage in zip(readers, [0.0, 4.0, 8.0]):
        reader.metadata["Start Voltage"] = (start_voltage, "V")

    analyzer = SpectraBase(
        readers=readers,
        roi=roi,
        pixel_per_ev=16,
        peak_shift=0,
    )

    stitched_energy, stitched_profile = analyzer.stitch_profiles([0, 1, 2])

    assert stitched_energy == pytest.approx(
        np.concatenate(
            [
                np.arange(0, 96) / 16,
                4 + np.arange(32, 96) / 16,
                8 + np.arange(32, 128) / 16,
            ]
        )
    )
    assert stitched_profile == pytest.approx(
        np.concatenate(
            [
                10 + np.arange(0, 96),
                60 + np.arange(32, 96),
                110 + np.arange(32, 128),
            ]
        )
    )
