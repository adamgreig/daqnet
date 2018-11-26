from migen.build.generic_platform import Pins, IOStandard, Subsignal
from migen.build.lattice import LatticePlatform
from migen.build.platforms import mystorm_blackice_ii


# Prototyping platform on BlackICE II

_adc = [
    (
        "adc", 0,
        Subsignal("dout1", Pins("pmod8:1"), IOStandard("SB_LVCMOS")),
        Subsignal("dout2", Pins("pmod8:0"), IOStandard("SB_LVCMOS")),
        Subsignal("ain", Pins("pmod8:2"), IOStandard("SB_LVDS_INPUT")),
    ),
]

_io = mystorm_blackice_ii._io + _adc
_connectors = mystorm_blackice_ii._connectors


class BlackIcePlatform(mystorm_blackice_ii.Platform):
    def __init__(self):
        LatticePlatform.__init__(self, "ice40-hx8k-tq144:4k", _io, _connectors,
                                 toolchain="icestorm")


# Prototype sensor node platform
_protosensor_io = [
    ("user_led", 0, Pins("A3"), IOStandard("SB_LVCMOS")),
    ("user_led", 1, Pins("A4"), IOStandard("SB_LVCMOS")),
    ("user_led", 2, Pins("A10"), IOStandard("SB_LVCMOS")),
    ("user_led", 3, Pins("A11"), IOStandard("SB_LVCMOS")),

    ("user_sw", 0, Pins("L1"), IOStandard("SB_LVCMOS")),
    ("user_sw", 1, Pins("L5"), IOStandard("SB_LVCMOS")),

    ("clk25", 0, Pins("B6"), IOStandard("SB_LVCMOS")),

    ("adc", 0,
        Subsignal("cs", Pins("L2")),
        Subsignal("dout", Pins("L3")),
        Subsignal("sclk", Pins("L4")),
        IOStandard("SB_LVCMOS")),

    ("flash", 0,
        Subsignal("io3", Pins("J11")),
        Subsignal("io2", Pins("H11")),
        Subsignal("sdi", Pins("K9")),
        Subsignal("sdo", Pins("J9")),
        Subsignal("sck", Pins("L10")),
        Subsignal("cs", Pins("K10")),
        IOStandard("SB_LVCMOS")),

    ("TDP", 0, Pins("C2"), IOStandard("SB_LVCMOS")),
    ("TDN", 0, Pins("C1"), IOStandard("SB_LVCMOS")),
    ("RD", 0, Pins("B2"), IOStandard("SB_LVDS_INPUT")),
]


class ProtoSensorPlatform(LatticePlatform):
    default_clk_name = "clk25"
    default_clk_period = 40

    def __init__(self):
        super().__init__(
            "ice40-hx8k-bg121", _protosensor_io, toolchain="icestorm")
