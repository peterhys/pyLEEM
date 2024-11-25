from pyleem.metadata import get_header, get_imgmeta_index, get_imgmeta
import numpy as np
import pandas as pd
import os


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

    def subset_values(self, key_list):
        """Return a subset of the metadata values.

        The units are included. To get the units, access the imgmeta attribute.
        """
        return [self.imgmeta[key][0] for key in key_list]

    def subset_units(self, key_list):
        """Return a subset of the metadata units."""

        return [self.imgmeta[key][1] for key in key_list]

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

    def __lt__(self, other):
        """For sorting purposes."""

        return self.path < other.path

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def to_h5(self, f, gname=None, write_img=True):
        """Write entry to a HDF5 file.

        If write image if True, than the image is compressed using gzip.
        """

        # name removes the extension
        gname = gname or os.path.splitext(os.path.basename(self.path))[0]
        group = f.create_group(gname)
        group.attrs.update({k: v for k, v in self.header.items() if v is not None})

        if write_img:
            img_group = group.create_dataset(
                "image", data=self.read_image(), compression="gzip"
            )
        else:
            img_group = group.create_group("image")

        for key, value in self.imgmeta.items():
            if value:
                img_group.attrs[key] = value[0]
                img_group.attrs[key + "_unit"] = value[1]

        self.custom_h5(group)

    def custom_h5(self, group):
        """Custom HDF5 writing.

        Function to be implemented by the subclass.
        To access the image group, use group["image"].
        """
        pass
