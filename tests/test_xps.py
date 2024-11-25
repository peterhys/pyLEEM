import pytest
import numpy as np
import pandas as pd
import scipy
from roifile import ImagejRoi, ROI_TYPE
from pyleem.roi import LineROI
import h5py
from pyleem.xps import (
    shirley_background,
    pseudo_voigt_fits,
    plot_xps_fits,
    df_fit_result,
    read_profile,
    parse_filename,
    profile_roi,
    XPSReader,
)
from lmfit import Parameters
from lmfit.minimizer import MinimizerResult
from lmfit.models import PseudoVoigtModel
import matplotlib.pyplot as plt


def test_shirley_background():
    """Test shirley_substract function.

    There are three tests here:
    1. If the background difference from the two edges are zero then the background is
    expected to be zero.
    2. If the center of the background dip should be the center of the signal.
    3. The shirley should recover the signal with the given tolerance for Gaussian distribution.

    There is possibly a way to approximate the shirley background directly into a distribution;
    here we simply approximate the background using a sideways tangent function. The background
    is fed back into the shirley background calculation. The function should be able to recover
    the second/third shirley background.
    """

    sig1 = np.array([0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0])
    bg1 = np.linspace(3, 0, 11)
    total_sig = sig1 + bg1
    dx = 1.0

    # Test 1
    base_diff = 0
    extracted_bg = shirley_background(total_sig, dx, base_diff)
    assert np.all(extracted_bg == 0)

    # Test 2
    base_diff = 3
    extracted_bg = shirley_background(total_sig, dx, base_diff)

    # the most negative value
    assert np.diff(extracted_bg).argmin() == len(extracted_bg) // 2

    # Test 3

    mean = 0
    variance = 1
    sigma = np.sqrt(variance)
    x = np.linspace(mean - 3 * sigma, mean + 3 * sigma, 101)
    tan_bg = -np.atan(1 * x)
    tan_bg = tan_bg - tan_bg.min()
    sig = scipy.stats.norm.pdf(x, mean, sigma) * 20
    dx = x[1] - x[0]
    base_diff = np.pi
    total_sig_1 = tan_bg + sig
    s_bg1 = shirley_background(total_sig_1, dx, base_diff)
    total_sig_2 = s_bg1 + sig
    s_bg2 = shirley_background(total_sig_2, dx, base_diff)
    total_sig_3 = s_bg2 + sig
    s_bg3 = shirley_background(total_sig_3, dx, base_diff)

    assert np.allclose(s_bg3, s_bg2, rtol=0.005)


def test_pseudo_voigt_fits():
    """Test pseudo_voigt_fits function."""
    peaks = ["peak1", "peak2"]
    constraints = {
        "peak1_center": {"value": 1.0, "min": 0.5, "max": 1.5, "vary": False},
        "peak2_center": {"value": 2.0, "min": 1.5, "max": 2.5},
    }
    model, params = pseudo_voigt_fits(peaks, constraints)

    assert model is not None
    assert params is not None

    # test the constraints are added
    for peak in peaks:
        for suffix in ["amplitude", "sigma", "fraction"]:
            param_name = f"{peak}_{suffix}"
            assert param_name in params
            assert params[param_name].min == 0

    for key, value in constraints.items():
        assert params[key].value == value["value"]
        assert params[key].min == value["min"]
        assert params[key].max == value["max"]
        assert params[key].vary == value.get("vary", True)


def test_df_fit_result():
    """Test xps_fit_result function."""

    param1 = Parameters()
    param1.add("param1", value=1.0)
    param1.add("param2", value=2.0)
    param1.add("param1_amplitude", value=1.0)
    param1.add("param2_amplitude", value=2.0)
    result1 = MinimizerResult(params=param1, redchi=1.5)

    param2 = Parameters()
    param2.add("param1", value=1.5)
    param2.add("param2", value=2.5)
    param2.add("param1_amplitude", value=2.0)
    param2.add("param2_amplitude", value=1.0)

    uvars = {"param1": 1.0, "param2": 2.0}

    result2 = MinimizerResult(params=param2, redchi=1.2, uvars=uvars)

    results = [("sample1", result1), ("sample2", result2)]
    df = df_fit_result(results, area=False, uncertainty=False)
    assert df.shape == (2, 5)
    assert df.columns.tolist() == [
        "param1",
        "param2",
        "param1_amplitude",
        "param2_amplitude",
        "Reduced_chi",
    ]

    df = df_fit_result(results, area=True, uncertainty=True)
    assert df.columns.tolist() == [
        "param1",
        "param2",
        "param1_amplitude",
        "param2_amplitude",
        "param1_area",
        "param2_area",
        "Reduced_chi",
    ]
    # the area still calculated because under params the amplitude param exists
    assert np.array_equal(df["param1_area"], [1 / 3, 2 / 3])
    assert np.array_equal(df["param2_area"], [2 / 3, 1 / 3])


def test_read_profile(tmp_path):
    """Test read_profile function."""

    file1 = tmp_path / "test.csv"
    data1 = "pixel,intensity\n0,10\n1,20\n2,30"
    file1.write_text(data1)

    file2 = tmp_path / "test2.csv"
    data2 = ",pixel,intensity\n0, 0,10\n1, 1,20\n2, 2,30"
    file2.write_text(data2)

    df1 = read_profile(file1, 20.0, 10.0, 5, 5.0)
    df2 = read_profile(file2, 20.0, 10.0, 5, 5.0)

    assert df1.equals(df2)
    assert df1["pixel"].tolist() == [0, 1, 2]
    assert df1["intensity"].tolist() == [10, 20, 30]
    assert np.allclose(df1["kinetic energy"], [15, 15.2, 15.4])
    assert np.allclose(df1["binding energy"], [5, 4.8, 4.6])


def test_parse_filename():
    """Test parse_filename function."""

    # Test with a valid filename
    filename = "20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C.dat"
    expected_output = [
        ("filename", "20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C.dat"),
        ("date", "20240101"),
        ("sample", "1"),
        ("condition", "E"),
        ("aperture", "1FA"),
        ("incident_voltage", 700),
        ("start_voltage", 412),
        ("element", "C1s"),
        ("position", "C"),
    ]
    parsed_output = parse_filename(filename)
    assert parsed_output == dict(expected_output)

    # Test with a filename missing the optional position
    filename = "20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s.dat"
    expected_output = [
        ("filename", "20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s.dat"),
        ("date", "20240101"),
        ("sample", "1"),
        ("condition", "E"),
        ("aperture", "1FA"),
        ("incident_voltage", 700),
        ("start_voltage", 412),
        ("element", "C1s"),
        ("position", "None"),
    ]
    parsed_output = parse_filename(filename)
    assert parsed_output == dict(expected_output)

    # Test with an invalid filename
    filename = "invalid_filename"
    try:
        parse_filename(filename)
    except ValueError as e:
        assert str(e) == f"File name {filename} does not match the expected format"
    else:
        assert False, "Expected ValueError not raised"


def test_plot_xps_fits():
    """Test plot_xps_fits function."""

    fig, (ax, res_ax) = plt.subplots(2, 1, figsize=(8, 6))

    x = np.linspace(0, 10, 20)
    y = np.sin(x)
    bg_total = np.zeros_like(x)

    # Create a dummy ModelResult object
    params = Parameters()
    params.add("amplitude", value=1.0)
    params.add("center", value=5.0)
    params.add("sigma", value=1.0)
    params.add("fraction", value=0.5)

    model = PseudoVoigtModel(prefix="peak1_") + PseudoVoigtModel(prefix="peak2_")

    class MockModelResult:
        def __init__(self, model, best_fit, residual, params):
            self.model = model
            self.best_fit = best_fit
            self.residual = residual
            self.params = params

        def eval_components(self, **kwargs):
            return {"peak1_": np.sin(x), "peak2_": np.cos(x)}

    result = MockModelResult(model=model, best_fit=y, residual=y, params=params)

    plot_xps_fits(
        ax, res_ax, x, y, bg_total, result, title="Test Plot", xlabel="x axis"
    )

    assert ax.get_title() == "Test Plot"
    assert ax.get_xlabel() == ""  # x axis label is set at the residual plot
    assert ax.get_ylabel() == "Intensity"
    assert res_ax.get_xlabel() == "x axis"
    assert res_ax.get_ylabel() == "Residuals"

    # Check if the plot has the correct number of lines
    assert len(ax.get_lines()) == 5  # XPS data, total fit, background and two peaks
    assert len(res_ax.get_lines()) == 1  # residuals

    plt.close(fig)


def test_profile_roi():
    """Test profile_roi function."""

    # Create a 10x10 grid with values on the diagonal
    image = np.zeros((10, 10))
    np.fill_diagonal(np.fliplr(image), np.arange(10))
    image[-1, 4:] = 9

    # Define ROI parameters
    # horizontal line, should return 0, 0, 9, 0, 0, 9, 9, 9, 9, 9, 9, 9, 0
    roi_horiz = {
        "src": (9, -2),
        "dst": (9, 10),
        "linewidth": 1,
        "order": 1,
        "mode": "constant",
        "cval": 1,
        "reduce_func": np.mean,
    }

    df = profile_roi(image, roi_horiz, 0, 0, 1, 0)

    assert df.shape == (13, 4)
    assert np.array_equal(df["pixel"], np.arange(13))

    assert np.array_equal(df["intensity"], [1, 1, 9, 0, 0, 0, 9, 9, 9, 9, 9, 9, 1])

    # diagonal line, the exact value is difficult to calculate because its the average
    # of the pixel that's rotated by 45 degrees
    # however, the total signal value should be the same
    roi_diag = {
        "src": (0, 9),
        "dst": (8, 1),
        "linewidth": 2,
        "order": 1,
        "reduce_func": np.sum,
    }

    pixel_per_ev = 1.0
    incident_voltage = 20.0
    start_voltage = 10.0
    peak_shift = 0.0

    df = profile_roi(
        image, roi_diag, incident_voltage, start_voltage, pixel_per_ev, peak_shift
    )

    assert df.shape == (
        13,
        4,
    )  # int(10^sqrt(2)) + 1 not sure why it is +1 here actually
    assert np.array_equal(df["pixel"], np.arange(13))
    assert df["intensity"].sum() - np.arange(9).sum() < 1

    assert np.allclose(
        df["kinetic energy"],
        start_voltage + peak_shift + df["pixel"] / pixel_per_ev,
    )
    assert np.allclose(df["binding energy"], incident_voltage - df["kinetic energy"])


@pytest.fixture
def roi(tmp_path):
    roi_file = tmp_path / "test.roi"
    roif = ImagejRoi(
        x1=0,
        y1=0,
        x2=9,
        y2=9,
        stroke_width=1,
        stroke_color=b"M\xff\xff\x00",
        roitype=ROI_TYPE.LINE,
    )
    roif.tofile(roi_file)

    # Initialize the XPSReader
    roi = LineROI(file=roi_file, linewidth=1)
    return roi


@pytest.fixture
def xps_reader(tmp_path, img_array, metadata_bytes, roi):
    """Fixture for the XPSReader isntance."""
    # Create a temporary ROI file

    pixel_per_ev = 1.0
    peak_shift = 0.0

    raw_file = tmp_path / "20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C.dat"
    # append filler
    # append image bytes

    img_bytes = img_array.tobytes()
    raw_file.write_bytes(metadata_bytes + b"\xff" * 2000 + img_bytes)

    reader = XPSReader(raw_file.as_posix(), roi, pixel_per_ev, peak_shift)
    return reader


def test_XPSReader(roi, img_array, xps_reader):
    """Test the XPSReader class."""

    pixel_per_ev = 1.0
    peak_shift = 0.0
    # Check the file_info attribute
    expected_file_info = {
        "filename": xps_reader.path,
        "date": "20240101",
        "sample": "1",
        "condition": "E",
        "aperture": "1FA",
        "incident_voltage": 700.0,
        "start_voltage": 412.0,
        "element": "C1s",
        "position": "C",
    }
    assert xps_reader.info == expected_file_info

    # Check the roi attribute
    assert xps_reader.roi == roi

    # Check the profile attribute
    expected_profile = profile_roi(img_array, roi, 700, 412, pixel_per_ev, peak_shift)
    pd.testing.assert_frame_equal(xps_reader.profile, expected_profile)


def test_custom_h5(tmp_path, xps_reader):
    """Test the writing of the reader to a HDF5 file."""

    h5_file = tmp_path / "test.h5"
    with h5py.File(h5_file, "w") as f:
        xps_reader.to_h5(f, write_img=True)

    with h5py.File(h5_file, "r") as f:
        assert np.array_equal(
            f["20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C"]["profile"]["intensity"],
            xps_reader.profile["intensity"],
        )
        assert np.array_equal(
            f["20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C"]["profile"][
                "binding energy"
            ],
            xps_reader.profile["binding energy"],
        )
        assert "roi" in f["20240101_XPS_Sample1_E_1FA_700eV_412eV_C1s_C"]["profile"]
