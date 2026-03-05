FILE_CONTENTS = (  # starts at position 20
    ("FileSize", "<H"),
    ("FileVersion", "<H"),
    ("BitsPerPixel", "<H"),
    ("CameraBitsPerPixel", "<H"),
    ("MCPDiameterInPixels", "<H"),
    ("HorizontalBinning", "<B"),
    ("VerticalBinning", "<B"),
    (None, "<8c"),  # spare (LONGLONG)
    ("ImageWidth", "<H"),
    ("ImageHeight", "<H"),
    ("NrImages", "<H"),
    ("attachedRecipeSize", "<H"),
    (None, "<56c"),  # spare bytes
)


IMG_CONTENTS = (
    ("ImageSize", "<H"),
    ("ImageVersion", "<H"),
    ("ColorScaleLow", "<H"),
    ("ColorScaleHigh", "<H"),
    ("ImageTime", "<Q"),
    ("MaskXShift", "<H"),
    ("MaskYShift", "<H"),
    ("RotateMask", "<H"),
    ("attachedMarkupSize", "<H"),
    ("spin", "<H"),
    ("LEEMdataVersion", "<H"),
    ("LEEMdata", "<128s"),
    ("applied_processing", "<B"),
    ("gray_adjust_zone", "<b"),
    ("backgroundvalue", "<H"),
    ("desired_rendering", "<B"),
    (None, "<1c"),
    ("rendering_argShort", "<h"),
    ("rendering_argFloat", "<f"),
    ("desired_rotation", "<h"),
    ("rotation_offset", "<h"),
    (None, "<4c"),
)


DATA_TAGS = {
    # These are preset tags that contains data values
    # Some tags contains multiples parameters
    # Only the base tags are shown here
    100: [("Micrometers X", "mm", "<f"), ("Micrometers Y", "mm", "<f")],
    111: [("Phi", "deg", "<f"), ("Theta", "deg", "<f")],
    112: [("Spin", None, "<h")],  # unclear the struct
    113: [("FOV rotation", "deg", "<f")],  # unclear the struct
    114: [("Mirror state", None, "<f")],  # unclear the struct
    115: [("MCP screen voltage", "kV", "<f")],
    116: [("MCP channel plate voltage", "kV", "<f")],
}


UNIT_CODES = {
    0: None,
    1: "V",
    2: "mA",
    3: "A",
    4: "C",
    5: "K",
    6: "mV",
    7: "pA",
    8: "nA",
    9: "uA",
}


RENDERING_MODES = {
    0: "LINEAR_RENDERING",
    1: "HISTogramEQUALisation_RENDERING",
    2: "GAMMA_RENDERING",
    3: "LOG_RENDERING",
    4: "SQRT_RENDERING",
    5: "ASinH_RENDERING",
    6: "GAUSS_RENDERING",
    7: "CLAHE_RENDERING",
}
