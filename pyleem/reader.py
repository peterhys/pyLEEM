from pyleem.metadata import get_header, get_imgmeta_index, get_imgmeta
import numpy as np
import pandas as pd


class RawReader:
    """Read LEEM raw .dat file."""

    def __init__(self, path, user_tags=None, metasize=16384, read_img=True):
        self.path = path
        self.metasize = metasize
        self.metabytes = self.read_metabytes(metasize)

        self.header = get_header(self.metabytes)
        # file metadata added to attributes
        self.__dict__.update(self.header)
        self.imgmeta_slice = get_imgmeta_index(self.header)
        self.imgmeta = get_imgmeta(self.metabytes[self.imgmeta_slice], user_tags)
        self.imgmeta_df = pd.DataFrame.from_dict(
            self.imgmeta, orient="index", columns=["value", "unit", "tag"]
        )

        if read_img:
            self.img = self.read_image()
        else:
            self.img = None

    def read_metabytes(self, metasize):
        with open(self.path, "rb") as f:
            metabytes = f.read(metasize)

        return metabytes

    def subset_value(self, key_list):
        """Return a subset of the metadata values.

        The units are included. To get the units, access the imgmeta attribute.
        """
        return {key: self.imgmeta[key][0] for key in key_list}

    def subset_unit(self, key_list):
        """Return a subset of the metadata units."""

        return {key: self.imgmeta[key][1] for key in key_list}

    def list_headers(self):
        """List the header keys."""
        return list(self.header.keys())

    def list_metadata(self):
        """List the metadata keys."""
        return list(self.imgmeta.keys())

    def read_image(self):
        """Read the image data.

        The images are stored in the last part of the file. The byte format is
        16-bit unsigned integer (little-endian). The image are shaped as
        (height, width).
        """
        dt = dt = np.dtype(np.uint16)
        dt = dt.newbyteorder("<")

        with open(self.path, "rb") as f:
            f.seek(-self.height * self.width * 2, 2)
            img = np.frombuffer(f.read(), dtype=dt).reshape(self.height, self.width)
        return img
