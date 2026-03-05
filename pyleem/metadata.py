from pyleem.metainfo import (
    FILE_CONTENTS,
    IMG_CONTENTS,
    UNIT_CODES,
    DATA_TAGS,
)
import struct
from datetime import datetime, timedelta, timezone


def convert_win_filetime(timestamp):
    """Convert Windows filetime to datetime string.

    Windows filetime is a 64-bit value representing 100-nanosecond
    intervals since January 1, 1601 (UTC). To further
    convert to local time, need to add the timezone offset.

    :param int timestamp: Windows filetime value.
    :return: Formatted datetime string (YYYY/MM/DD HH:MM:SS.ffffff).
    :rtype: str
    """
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    dt = epoch + timedelta(microseconds=timestamp / 10)
    return dt.strftime("%Y/%m/%d %H:%M:%S.%f")


def get_metadata(metabytes):
    """Extract and parse metadata from UView .dat file header.

    :param bytes metabytes: Raw metadata bytes from file header.
    :return: Dictionary of metadata entries as (value, unit) tuples.
    :rtype: dict
    """

    metadata = {}

    # filetype
    filetypebytes = metabytes[:20]
    filetype = filetypebytes.split(b"\x00")[0]
    metadata["filetype"] = (filetype.decode("utf-8"), None)

    pos = 20
    for entry, format in FILE_CONTENTS:
        size = struct.calcsize(format)
        value = struct.unpack(format, metabytes[pos : pos + size])[0]
        if entry is not None:
            metadata[entry] = (value, None)
        pos += size

    if metadata["attachedRecipeSize"][0] > 0:
        recipe = metabytes[pos : pos + metadata["attachedRecipeSize"][0]]
        metadata["recipe"] = (recipe.decode("utf-8"), None)
        pos += metadata["attachedRecipeSize"]
    else:
        metadata["recipe"] = (None, None)

    assert metadata["FileSize"][0] >= pos

    # Reset to system metadata end
    pos = metadata["FileSize"][0]

    for entry, fmt in IMG_CONTENTS:
        size = struct.calcsize(fmt)
        value = struct.unpack(fmt, metabytes[pos : pos + size])[0]
        if entry is not None:
            metadata[entry] = (value, None)
        pos += size

    pos = metadata["ImageSize"][0] + metadata["FileSize"][0]

    # Markup data
    markup_size = metadata["attachedMarkupSize"][0]
    actual_block_size = 128 * ((markup_size // 128) + 1)
    metadata["markup_block_size"] = (actual_block_size, None)
    metadata["markup_data"] = (metabytes[pos : pos + actual_block_size].hex(), None)

    pos = (
        metadata["FileSize"][0]
        + metadata["ImageSize"][0]
        + metadata["markup_block_size"][0]
    )

    # Read optional extra LEEM data
    if metadata["LEEMdataVersion"][0] > 2:
        extra_size = metadata["LEEMdataVersion"][0]
        leemdataextra = metabytes[pos : pos + extra_size]
        metadata["extra_leem_data"] = (leemdataextra, None)
        leemdata = parse_leem_data(leemdataextra)
    else:
        metadata["extra_leem_data"] = b""
        leemdata = {}

    # Post-processing
    # image time is a string
    # time stamp is a datetime object
    metadata["ImageTime"] = (convert_win_filetime(metadata["ImageTime"][0]), None)
    metadata["TimeStamp"] = (
        datetime.strptime(metadata["ImageTime"][0], "%Y/%m/%d %H:%M:%S.%f"),
        None,
    )

    metadata.update(leemdata)

    return metadata


def is_tag_in_range(tag, range):
    """Check whether tag's base value is within range.

    UView uses the highest bit to mark image overlay. This function
    masks that bit before checking range. Range min and max can be
    the same value for a single tag.

    :param int tag: Integer tag value (0-255).
    :param tuple range: Tuple (min_base, max_base) defining range.
    :return: True if base tag is within range, False otherwise.
    :rtype: bool
    """
    base_tag = tag & 0x7F
    return range[1] >= base_tag >= range[0]


def parse_leem_data(data):
    """Parse LEEM-specific metadata from extra data block.

    LEEM data contains tagged metadata with various formats including
    standard values, gauge readings, and camera settings.

    :param bytes data: LEEM metadata bytes.
    :return: Dictionary of metadata as (value, unit) tuples.
    :rtype: dict
    :raises ValueError: If an unrecognized tag value is encountered.
    """

    leemdata = {}

    while data:
        tag = data[0]
        data = data[1:]

        if tag == 255:
            # end tag
            break

        elif is_tag_in_range(tag, (0, 99)):
            # standard tags 0..99

            source, data = data.split(b"\x00", maxsplit=1)
            source = source.decode("utf-8")
            if data[:4] == b"sO\xc3G":
                value = "invalid"
            elif data[:4] == b"\xf3O\xc3G":
                value = "local"
            else:
                value = struct.unpack(f"<f", data[:4])[0]

            last_char = source[-1]
            unit = None
            if last_char.isdigit() and int(last_char) in UNIT_CODES:
                unit = UNIT_CODES[int(last_char)]
                source = source[:-1]

            leemdata[source] = (value, unit)
            data = data[4:]

        elif is_tag_in_range(tag, (106, 109)) or is_tag_in_range(tag, (120, 126)):
            # gauge tags
            # 106 - 109 are standard gauge tags
            # additional gauge tags are 120 - 126 (the menu suggests 127 - 130
            # are also gauge tags but they are outside of the correct range)
            source, unit, data = data.split(b"\x00", maxsplit=2)
            source = source.decode("utf-8")
            unit = unit.decode("utf-8")
            value = struct.unpack(f"<f", data[:4])[0]

            leemdata[source] = (value, unit)
            data = data[4:]

        elif is_tag_in_range(tag, (100, 100)) or is_tag_in_range(tag, (111, 116)):

            base_tag = tag & 0x7F

            for source, unit, arg_struct in DATA_TAGS[base_tag]:
                size = struct.calcsize(arg_struct)
                value = struct.unpack(arg_struct, data[:size])[0]

                leemdata[source] = (value, unit)
                data = data[size:]

        elif is_tag_in_range(tag, (104, 104)):
            # camera exposure and average
            # at least in our instrument, the average value is reversed compared to
            # the menu settings, where the average count is before the settting
            exposure, average_count, average_mode = struct.unpack(f"<fbb", data[:6])

            leemdata["Camera Exposure"] = (exposure, "s")
            leemdata["Camera Average"] = (average_count, None)

            if average_mode == 0:
                leemdata["Camera Average Mode"] = ("no average", None)
            elif average_mode > 0:
                leemdata["Camera Average Mode"] = ("average", None)
            elif average_mode < 0:
                leemdata["Camera Average Mode"] = ("sliding average", None)

            data = data[6:]

        elif is_tag_in_range(tag, (105, 105)):
            # image title
            title, data = data.split(b"\x00", maxsplit=1)
            leemdata["Image Title"] = (title.decode("utf-8"), None)

        elif is_tag_in_range(tag, (110, 110)):
            # FOV
            fov, data = data.split(b"\x00", maxsplit=1)
            leemdata["FOV"] = (fov.decode("utf-8"), None)

            cal_fov = struct.unpack(f"<f", data[:4])[0]
            leemdata["Cal. FOV"] = (cal_fov, None)
            data = data[4:]

        else:
            raise ValueError(f"Incorrect tag value: {tag}")

    return leemdata
