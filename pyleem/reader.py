from pyleem.metadata import get_header, get_imgmeta_index, get_imgmeta


class RawReader:
    """Read LEEM raw .dat file."""

    def __init__(self, path, user_tags=None, metasize=16384):
        self.path = path
        self.metasize = metasize
        self.metabytes = self.read_metabytes(metasize)

        self.header = get_header(self.metabytes)
        # file metadata added to attributes
        self.__dict__.update(self.header)
        self.imgmeta_slice = get_imgmeta_index(self.header)
        self.imgmeta = get_imgmeta(
            self.metabytes[self.imgmeta_slice], user_tags=user_tags
        )

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
