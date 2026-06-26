import pytest

from pyleem.analysis.spectra import SpectraAnalyzer, kinetic_energy


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
    analyzer = SpectraAnalyzer(
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
