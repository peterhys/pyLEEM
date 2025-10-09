import numpy as np
import skimage.measure
from scipy.ndimage import gaussian_filter
from pyleem.reader import RawReader
import matplotlib.pyplot as plt

def se_fit(profile):
    """Fit the secondary electron profile."""
    profile_derivative = np.gradient(profile)
    slope = np.max(profile_derivative)
    index = np.argmax(profile_derivative)
    offset = index - profile[index] / slope
    return index, slope, offset


def fit_se_profile(files, roi, sigma=10, plot=False, **params):
    """Fit the secondary electron profile."""

    offset_list = []
    indices = []
    profiles = []
    start_voltages = []
    for file in files:

        reader = RawReader(file)
        start_voltages.append(reader.imgmeta["Start Voltage"][0])
        image = reader.read_image()
        profile = skimage.measure.profile_line(image, **roi)
        profile = gaussian_filter(profile, sigma)
        index, slope, offset = se_fit(profile)
        offset_list.append(offset)
        indices.append(index)
        profiles.append(profile)

    # the ppev calculation is actually reversed
    ppev = np.abs(
        (offset_list[0] - offset_list[1]) / (start_voltages[0] - start_voltages[1])
    )
    ps = indices[0] / ppev + start_voltages[0]

    if plot:
        plot_fitline(profiles, indices, offset_list)
    return ppev, ps


def plot_fitline(profiles, indices, offset_list):
    """Plot the fitline for each profile."""
    for profile, index, offset in zip(profiles, indices, offset_list):
        x = np.arange(len(profile))
        plt.plot(x, profile, label="Profile")
        plt.plot([offset, index], [0, profile[index]], "--", label="Offset")
        plt.legend()
        plt.xlabel("Pixels")
        plt.ylabel("Intensity")
        plt.title("Profile with Offset Line")
