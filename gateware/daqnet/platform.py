from migen.build.generic_platform import Pins, IOStandard, Subsignal
from migen.build.lattice import LatticePlatform

# Prototype sensor node platform
_protosensor_io = [
    ("user_led", 0, Pins("A10"), IOStandard("SB_LVCMOS")),
    ("user_led", 1, Pins("A11"), IOStandard("SB_LVCMOS")),

    ("user_sw", 0, Pins("L1"), IOStandard("SB_LVCMOS")),
    ("user_sw", 1, Pins("L7"), IOStandard("SB_LVCMOS")),

    ("clk25", 0, Pins("B6"), IOStandard("SB_LVCMOS")),

    ("adc", 0,
        Subsignal("cs", Pins("L2")),
        Subsignal("dout", Pins("L3")),
        Subsignal("sclk", Pins("L4")),
        IOStandard("SB_LVCMOS")),

    ("flash", 0,
        Subsignal("sdi", Pins("K9")),
        Subsignal("sdo", Pins("J9")),
        Subsignal("sck", Pins("L10")),
        Subsignal("cs", Pins("K10")),
        Subsignal("io2", Pins("H11")),
        Subsignal("io3", Pins("J11")),
        IOStandard("SB_LVCMOS")),

    ("daqnet", 0,
        Subsignal("led1", Pins("A3"), IOStandard("SB_LVCMOS")),
        Subsignal("led2", Pins("A4"), IOStandard("SB_LVCMOS")),
        Subsignal("txp", Pins("C2"), IOStandard("SB_LVCMOS")),
        Subsignal("txn", Pins("C1"), IOStandard("SB_LVCMOS")),
        Subsignal("rx", Pins("B2"), IOStandard("SB_LVDS_INPUT"))),
]


class ProtoSensorPlatform(LatticePlatform):
    default_clk_name = "clk25"
    default_clk_period = 40

    def __init__(self):
        super().__init__(
            "ice40-hx8k-bg121", _protosensor_io, toolchain="icestorm")


# Prototype switch platform
_protoswitch_io = [
    ("user_led", 0, Pins("A11"), IOStandard("SB_LVCMOS")),
    ("user_led", 1, Pins("A10"), IOStandard("SB_LVCMOS")),

    ("clk25", 0, Pins("B6"), IOStandard("SB_LVCMOS")),

    ("uart", 0,
        Subsignal("rx", Pins("A4")),
        Subsignal("tx", Pins("A3")),
        IOStandard("SB_LVCMOS")),

    ("flash", 0,
        Subsignal("sdi", Pins("K9")),
        Subsignal("sdo", Pins("J9")),
        Subsignal("sck", Pins("L10")),
        Subsignal("cs", Pins("K10")),
        Subsignal("io2", Pins("K11")),
        Subsignal("io3", Pins("J11")),
        IOStandard("SB_LVCMOS")),

    ("rmii", 0,
        Subsignal("txd0", Pins("J3")),
        Subsignal("txd1", Pins("L1")),
        Subsignal("txen", Pins("L2")),
        Subsignal("rxd0", Pins("K5")),
        Subsignal("rxd1", Pins("J5")),
        Subsignal("crs_dv", Pins("L4")),
        Subsignal("ref_clk", Pins("K4")),
        Subsignal("mdc", Pins("K3")),
        Subsignal("mdio", Pins("L3")),
        IOStandard("SB_LVCMOS")),

    ("phy_rst", 0, Pins("K2"), IOStandard("SB_LVCMOS")),
    ("eth_led", 0, Pins("J2"), IOStandard("SB_LVCMOS")),

    ("daqnet", 0,
        Subsignal("led1", Pins("C4"), IOStandard("SB_LVCMOS")),
        Subsignal("led2", Pins("D3"), IOStandard("SB_LVCMOS")),
        Subsignal("txp", Pins("B1"), IOStandard("SB_LVCMOS")),
        Subsignal("txn", Pins("B2"), IOStandard("SB_LVCMOS")),
        Subsignal("rx", Pins("C1"), IOStandard("SB_LVDS_INPUT"))),

    ("daqnet", 1,
        Subsignal("led1", Pins("D2"), IOStandard("SB_LVCMOS")),
        Subsignal("led2", Pins("C3"), IOStandard("SB_LVCMOS")),
        Subsignal("txp", Pins("E1"), IOStandard("SB_LVCMOS")),
        Subsignal("txn", Pins("D1"), IOStandard("SB_LVCMOS")),
        Subsignal("rx", Pins("E3"), IOStandard("SB_LVDS_INPUT"))),

    ("daqnet", 2,
        Subsignal("led1", Pins("G3"), IOStandard("SB_LVCMOS")),
        Subsignal("led2", Pins("F3"), IOStandard("SB_LVCMOS")),
        Subsignal("txp", Pins("F1"), IOStandard("SB_LVCMOS")),
        Subsignal("txn", Pins("F2"), IOStandard("SB_LVCMOS")),
        Subsignal("rx", Pins("G2"), IOStandard("SB_LVDS_INPUT"))),

    ("daqnet", 3,
        Subsignal("led1", Pins("F4"), IOStandard("SB_LVCMOS")),
        Subsignal("led2", Pins("H3"), IOStandard("SB_LVCMOS")),
        Subsignal("txp", Pins("H1"), IOStandard("SB_LVCMOS")),
        Subsignal("txn", Pins("H2"), IOStandard("SB_LVCMOS")),
        Subsignal("rx", Pins("K1"), IOStandard("SB_LVDS_INPUT"))),
]


class ProtoSwitchPlatform(LatticePlatform):
    default_clk_name = "clk25"
    default_clk_period = 40

    def __init__(self):
        super().__init__(
            "ice40-hx8k-bg121", _protoswitch_io, toolchain="icestorm")
