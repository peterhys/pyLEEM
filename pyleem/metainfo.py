FILE_INFO = (  # starts at position 20
    ("file_header_size", "<H"),
    ("file_version", "<H"),
    ("bits_per_pixel", "<H"),
    ("camera_bits_per_pixel", "<H"),
    ("MCP_diam", "<H"),
    ("hbinning", "<H"),
    ("vbinning", "<H"),
    (None, "<cccccc"),
    ("width", "<H"),
    ("height", "<H"),
    ("no_images", "<H"),
    ("attachedrecipesize", "<H"),
    (None, "<" + "c" * 56),  # should be exactly at the position of POS
)
IMG_INFO = (
    ("img_header_size", "<H"),
    ("img_version", "<H"),
    ("colorscale_low", "<H"),
    ("colorscale_high", "<H"),
    ("timestamp", "<Q"),
    ("mask_xshift", "<H"),
    ("mask_yshift", "<H"),
    ("usemask", "<B"),
    (None, "<c"),  # discard
    ("attachedmarkedsize", "<H"),
    ("spin", "<H"),
    ("img_meta_size", "<H"),
)

# it appears that sometime more tag shows up
STD_TAGS = (  # type <f (float)
    2,  # Illum. Defl. X
    3,  # Illum. Defl. Y
    6,  # MCPchannelplate
    11,  # Objective
    14,  # Transfer Lens
    21,  # Interm. Lens
    24,  # Projective 1
    38,  # Start Voltage
    39,  # Sample Temp.
    128,  # Illum.Stigm.A
    129,  # Illum.Stigm.B
    130,  # Illum. Defl. X
    131,  # Illum.Defl. Y
    132,  # Cond. Lens 3
    133,  # CL3 Align. X
    134,  # CL3 Align. Y
    135,  # Cond. Lens 2
    136,  # CL1 Align. X
    137,  # CL1 Align. Y
    138,  # Cond. Lens 1
    140,  # Obj.Stigm. A
    141,  # Obj.Stigm. B
    142,  # Transfer Lens
    143,  # Diffr.Stigm.A
    144,  # Diffr.Stigm.B
    145,  # FL Align. X
    146,  # FL Align.Y
    147,  # Field Lens
    148,  # IL Align. X
    149,  # Interm. Lens
    150,  # P1 Align. X
    151,  # P1 Align. Y
    152,  # Projective 1
    153,  # P2 Align. X
    154,  # P2 Align. Y
    155,  # Projective 2
    156,  # P3 Align.X
    157,  # P3 Align.Y
    158,  # Illum. Defl. Y
    159,  # Illum.Equal.Y
    160,  # Outer Select.
    161,  # Image Equal.X
    162,  # Image Equal.Y
    163,  # Inner Select.
    164,  # Obj.Align. X
    165,  # Obj.Align. Y
    168,  # IL Align. Y
    169,  # Bomb. Voltage
    170,  # Temp. Control
    171,  # Filament
    172,  # Emission Set
    173,  # Projective 3
    174,  # Ret. Lens
    175,  # SEL+/-
    176,  # Mirror TL 1
    177,  # MFL1 Align X
    178,  # MFL1 Align Y
    179,  # Mirror FL1
    180,  # MFL2 Align  X
    181,  # MFL2 Align Y
    182,  # Mirror FL 2
    183,  # MTL2 Align X
    184,  # Bias
    185,  # AL Align. B
    186,  # MTL2 Align Y
    187,  # Mirror TL 2
    188,  # Sec2 Align X
    189,  # Sec2 Align Y
    190,  # MIllu. Equal X
    191,  # MIllu. Equal Y
    192,  # MOuter Select.
    193,  # C1/Fil+
    194,  # MImage Eq X
    195,  # MImage Eq Y
    196,  # MInner Select.
    197,  # MExtractor
    198,  # Mirror Align X
    199,  # Mirror Align Y
    200,  # Mirror Stig. A
    201,  # Mirror Stig. B
    202,  # MFocus
    203,  # AL Align. A
    204,  # RL Align. Y
    205,  # RL Align. X
    206,  # Emission Curr.
    207,  # Wehnelt
    208,  # Ana.Stigm.A
    209,  # MTL Align. Y
    210,  # Acc. Lens
    211,  # Inner Lens
    212,  # MTrans. Lens
    213,  # MTL Align. X
    214,  # Mirror
    215,  # Ana.Stigm.B
    217,  # V CCS1
    218,  # C2/Fil-
    219,  # MTL Align. Y
    220,  # Workfunction
    222,  # U4/TC-
    223,  # I CCV4
    224,  # V CCS2
    225,  # U3/TC+
    226,  # I CCV3
)

GAUGE_TAGS = (
    106,  # MCH
    235,  # COL
    236,  # ECH
    237,  # PCH
)
SPEC_TAGS = {
    # Bc format only B is stored in the final value
    232: [("Camera Exposure", "<f", "s"), ("Camera Average", "<Bc", "")],
    104: [("Camera Exposure", "<f", "s"), ("Camera Average", "<Bc", "")],
    244: [("MCPchannelplate", "<f", "kV")],
    243: [("MCPscreen", "<f", "kV")],
    228: [("Micrometers X", "<f", "mm"), ("Micrometers Y", "<f", "mm")],
    242: [(None, "<c", ""), ("Mirror state", "<B", "")],
    110: [
        ("Preset (FOV):", None, ""),
        (None, "<9s", ""),
    ],  # not sure what is actually stored here
    233: [("Imagetitle:", None, "")],
}


UNIT_DICT = {
    "1": "V",
    "2": "mA",
    "3": "A",
    "4": "°C",
    "5": "K",
    "6": "mV",
    "7": "pA",
    "8": "nA",
    "9": "µA",
}
