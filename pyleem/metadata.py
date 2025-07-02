from pyleem.metainfo import (
    FILE_INFO,
    IMG_INFO,
    STD_TAGS,
    GAUGE_TAGS,
    SPEC_TAGS,
    UNIT_DICT,
)
import logging
import struct
from datetime import datetime


logger = logging.getLogger(__name__)


def convert_win_filetime(timestamp):
    """Convert windows filetime to unix epoch.

    Returns a time string with the format of YYYY/MM/DD HH:MM:SS.
    The string format is for saving to a HDF5 file.
    """

    # 11644473600 is the difference between windows epoch and unix epoch
    return datetime.fromtimestamp(timestamp / 1e7 - 11644473600).strftime(
        "%Y/%m/%d %H:%M:%S.%f"
    )


def get_header(metabytes, file_info=FILE_INFO, img_info=IMG_INFO):
    """Extract metadata file header.

    The first 20 bytes are dedicated to the file name.
    """
    header_metadata = {}

    # filetype
    filetypebytes = metabytes[:20]
    filetype = filetypebytes.split(b"\x00")[0]
    header_metadata["filetype"] = filetype.decode("utf-8")

    pos = 20
    for entry, format in file_info:
        size = struct.calcsize(format)  # allows arbitrary format
        value = struct.unpack(format, metabytes[pos : pos + size])[0]
        if entry is not None:
            header_metadata[entry] = value
        pos += size

    if header_metadata["attachedrecipesize"] > 0:
        recipe = metabytes[pos : pos + header_metadata["attachedrecipesize"]]
        header_metadata["recipe"] = recipe.decode("utf-8")
        pos += header_metadata["attachedrecipesize"]
    else:
        header_metadata["recipe"] = None

    assert header_metadata["file_header_size"] >= pos  # check the position is correct

    # reset pos to the correct system metadata end size

    pos = header_metadata["file_header_size"]

    for entry, fmt in img_info:
        size = struct.calcsize(fmt)
        value = struct.unpack(fmt, metabytes[pos : pos + size])[0]
        if entry is not None:
            header_metadata[entry] = value
        pos += size

    # post processing

    header_metadata["timestamp"] = convert_win_filetime(header_metadata["timestamp"])
    header_metadata["marked_header_size"] = 128 * (
        header_metadata["attachedmarkedsize"] // 128 + 1
    )

    return header_metadata


def get_imgmeta_index(headermeta_dict):
    """Return the index of the imagemeta."""

    sysheader_size = headermeta_dict["file_header_size"]
    imageheader_size = headermeta_dict["img_header_size"]
    markedheader_size = headermeta_dict["marked_header_size"]
    header_size = sysheader_size + imageheader_size + markedheader_size
    return slice(header_size, header_size + headermeta_dict["img_meta_size"])


def get_imgmeta(
    data,
    user_tags=None,
    std_tags=STD_TAGS,
    gauge_tags=GAUGE_TAGS,
    special_tags=SPEC_TAGS,
    unit_dict=UNIT_DICT,
):
    """Extract image metadata from the data

    :param bytes data: image metadata bytes
    :param dict user_tags: custom tags or parsing options
        user_tags only supports defined pre-defined length
    """

    # allow custom format
    # the same as special tags
    # override existing tags
    user_tags = user_tags or {}
    special_tags_combined = {**special_tags, **user_tags}
    imagemeta_dict = {}
    while data:
        tag = data[0]  # first byte is the tag
        data = data[1:]

        logger.debug(f"Tag: {tag}, Data: {data[:40]}")

        if tag in special_tags_combined:

            # maybe more info than just the value
            for name, fmt, unit in special_tags_combined[tag]:

                if fmt is None:  # variable length string that ends with \x00
                    value = data.split(b"\x00", maxsplit=1)[0]
                    size = len(value) + 1  # include the null byte
                else:
                    size = struct.calcsize(fmt)
                    value = struct.unpack(fmt, data[:size])[0]

                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8")
                    except:
                        value = value

                data = data[size:]

                if name is not None:
                    imagemeta_dict[name] = (value, unit, tag)

        elif tag in std_tags:
            # the standard size is float 4 bytes

            name, data = data.split(b"\x00", maxsplit=1)

            if data[:4] == b"sO\xc3G":
                value = "Invalid"
            elif data[:4] == b"\xf3O\xc3G":
                value = "Local"
            else:
                value = struct.unpack(f"<f", data[:4])[0]

            data = data[4:]
            if chr(name[-1]) in unit_dict:
                unit = unit_dict[chr(name[-1])]
                name = name[:-1]
            else:
                unit = ""

            imagemeta_dict[name.decode("utf-8")] = (value, unit, tag)

        elif tag in gauge_tags:
            # data is float 4 bytes
            name, unit, data = data.split(b"\x00", maxsplit=2)
            value = struct.unpack(f"<f", data[:4])[0]

            data = data[4:]
            imagemeta_dict[name.decode("utf-8")] = (value, unit.decode("utf-8"), tag)

        elif tag == 255:
            break

        else:
            raise ValueError(f"Unknown tag {tag}")
    return imagemeta_dict
