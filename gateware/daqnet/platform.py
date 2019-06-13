"""
iCE40HX Platform

Platform support and instance wrappers for iCE40 FPGAs.

Copyright 2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Fragment, Elaboratable, Signal, Instance, Const, Module
from nmigen.vendor.lattice_ice40 import LatticeICE40Platform
from nmigen.build import Resource, Pins, Clock, Subsignal


class _InstanceWrapper(Elaboratable):
    """
    Wraps an Instance, taking parameters in the constructor and then
    exposing all ports as attributes. Unused ports are not specified
    in the eventual Instance.

    itype: the type of the instance to create
    params: a dictionary of parameter names to values
    ports: a dictionary of port names to (dirn, shape) tuples
    required_ports: a list of required port names
    defaults: a dictionary of port names to default values if unused
    """
    def __init__(self, itype, params, ports, required_ports, defaults=None):
        super().__setattr__('ports_used', {})
        super().__setattr__('ports', ports)
        self.itype = itype
        self.params = params
        self.required_ports = required_ports
        self.defaults = defaults

    def __getattr__(self, name):
        if name in self.ports_used:
            return self.ports_used[name]
        elif name.upper() in self.ports:
            _, shape = self.ports[name.upper()]
            self.ports_used[name] = Signal(shape=shape, name=name)
            return self.ports_used[name]
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        if name.startswith("_Elaboratable"):
            super().__setattr__(name, value)
        elif name.upper() in self.ports:
            self.ports_used[name] = value
        else:
            super().__setattr__(name, value)

    def elaborate(self, platform):
        args = {f"p_{key.upper()}": val for (key, val) in self.params.items()}
        for port, (dirn, shape) in self.ports.items():
            if port.lower() in self.ports_used:
                args[f"{dirn}_{port}"] = self.ports_used[port.lower()]
            elif self.defaults and port in self.defaults:
                args[f"{dirn}_{port}"] = self.defaults[port]
            elif port in self.required_ports:
                raise ValueError(f"{self.itype}: Required port {port} missing")

        return Instance(self.itype, **args)


class SB_IO(_InstanceWrapper):
    """
    I/O Primitive SB_IO.

    Parameters:
        * in_pin_type: one of:
            SB_IO.PIN_INPUT (default),
            SB_IO.PIN_INPUT_LATCH
            SB_IO.PIN_INPUT_REGISTERED
            SB_IO.PIN_INPUT_REGISTERED_LATCH
            SB_IO.PIN_INPUT_DDR
        * out_pin_type: one of:
            SB_IO.PIN_NO_OUTPUT (default)
            SB_IO.PIN_OUTPUT
            SB_IO.PIN_OUTPUT_TRISTATE
            SB_IO.PIN_OUTPUT_ENABLE_REGISTERED
            SB_IO.PIN_OUTPUT_REGISTERED
            SB_IO.PIN_OUTPUT_REGISTERED_ENABLE
            SB_IO.PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED
            SB_IO.PIN_OUTPUT_DDR
            SB_IO.PIN_OUTPUT_DDR_ENABLE
            SB_IO.PIN_OUTPUT_DDR_ENABLE_REGISTERED
            SB_IO.PIN_OUTPUT_REGISTERED_INVERTED
            SB_IO.PIN_OUTPUT_REGISTERED_ENABLE_INVERTED
            SB_IO.PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED_INVERTED
        * pullup: boolean whether to enable internal pullup.
        * neg_trigger: boolean whether to invert polarity of IO FFs
        * io_standard: one of "SB_LVCMOS" or "SB_LVDS_INPUT"

    Ports:
        Ports must be used or accessed as attributes, e.g.:
            io1 = SB_IO(out_pin_type=SB_IO.PIN_OUTPUT)
            io1.package_pin = user_led1
            io2 = SB_IO()
            io2.package_pin = user_sw1
            m.d.comb += io1.d_out_0.eq(io2.d_in_0)
        Unused ports will not be added to the instantiated Instance.

        * package_pin: required, connect to top-level pin
        * latch_input_value: when high, maintain current input value
        * clock_enable: clock enable common to input and output clock
        * input_clock: clock for input FFs
        * output_clock: clock for output FFs
        * output_enable: when high, enable output, otherwise high impedance
        * d_out_0: Output data, or in DDR mode, data for rising output_clock
        * d_out_1: In DDR mode, data for falling output_clock edge
        * d_in_0: Input data, or in DDR mode, data at rising input_clock edge
        * d_in_1: In DDR mode, data at falling input_clock edge
    """

    PIN_INPUT = 0b01
    PIN_INPUT_LATCH = 0b11
    PIN_INPUT_REGISTERED = 0b00
    PIN_INPUT_REGISTERED_LATCH = 0b10
    PIN_INPUT_DDR = 0b00

    PIN_NO_OUTPUT = 0b0000
    PIN_OUTPUT = 0b0110
    PIN_OUTPUT_TRISTATE = 0b1010
    PIN_OUTPUT_ENABLE_REGISTERED = 0b1110
    PIN_OUTPUT_REGISTERED = 0b0101
    PIN_OUTPUT_REGISTERED_ENABLE = 0b1001
    PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED = 0b1101
    PIN_OUTPUT_DDR = 0b0100
    PIN_OUTPUT_DDR_ENABLE = 0b1000
    PIN_OUTPUT_DDR_ENABLE_REGISTERED = 0b1100
    PIN_OUTPUT_REGISTERED_INVERTED = 0b0111
    PIN_OUTPUT_REGISTERED_ENABLE_INVERTED = 0b1011
    PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED_INVERTED = 0b1111

    def __init__(self,
                 in_pin_type=PIN_INPUT,
                 out_pin_type=PIN_NO_OUTPUT,
                 pullup=False, neg_trigger=False,
                 io_standard="SB_LVCMOS"):
        params = {
            "pin_type": in_pin_type | (out_pin_type << 2),
            "pullup": int(pullup),
            "neg_trigger": int(neg_trigger),
            "io_standard": io_standard,
        }

        ports = {
            "PACKAGE_PIN": ("io", 1),
            "LATCH_INPUT_VALUE": ("i", 1),
            "CLOCK_ENABLE": ("i", 1),
            "INPUT_CLK": ("i", 1),
            "OUTPUT_CLK": ("i", 1),
            "OUTPUT_ENABLE": ("i", 1),
            "D_OUT_0": ("i", 1),
            "D_OUT_1": ("i", 1),
            "D_IN_0": ("o", 1),
            "D_IN_1": ("o", 1),
        }

        required = ("PACKAGE_PIN",)
        super().__init__("SB_IO", params, ports, required)

    def change_pin_type(self, in_pin_type, out_pin_type):
        self.params["pin_type"] = in_pin_type | (out_pin_type << 2)


class SB_PLL40_PAD(_InstanceWrapper):
    """
    Phase-locked loop primitive SB_PLL40_PAD.

    Used when the PLL source is an input pad in banks 0 or 2, and the source
    clock is not required inside the FPGA.

    Required Parameters:
        * divr: Reference clock divider, 0 to 15
        * divf: Feedback divider, 0 to 63
        * divq: VCO divider, 1 to 6
        * filter_range: PLL filter setting, 0 to 7

    Optional Parameters:
        See SB_PLL40_PAD documentation. Parameters may be given as additional
        kwargs when initialising SB_PLL40_PAD, e.g.:
        pll = SB_PLL40_PAD(0, 31, 3, 2, feedback_path="DELAY", fda_feedback=10)

        If unspecified, FEEDBACK_PATH is set to SIMPLE and PLLOUT_SELECT
        to GENCLK.

    Ports:
        Ports must be set or accessed as attributes to be used, e.g.:
            pll = SB_PLL40_PAD(0, 31, 3, 2)
            pll.packagepin = clk25
            m.d.comb += cd.clk.eq(pll.plloutglobal)
        Unused ports will not be added to the instantiated Instance.

        See SB_PLL40_PAD documentation for the full list of ports.

        Required ports:
        * packagepin: Connect directly to input pad

        Commonly used ports:
        * plloutglobal: Global buffer clock out
        * plloutcore: Core logic clock out

        If unspecified, RESETB is set to 1.
    """
    def __init__(self, divr, divf, divq, filter_range, **params):
        params["divr"] = divr
        params["divf"] = divf
        params["divq"] = divq
        params["filter_range"] = filter_range

        if "feedback_path" not in params:
            params["feedback_path"] = "SIMPLE"
        if "pllout_select" not in params:
            params["pllout_select"] = "GENCLK"

        ports = {
            "PACKAGEPIN": ("i", 1),
            "EXTFEEDBACK": ("i", 1),
            "DYNAMICDELAY": ("i", 1),
            "LATCHINPUTVALUE": ("i", 1),
            "SCLK": ("i", 1),
            "SDI": ("i", 1),
            "SDO": ("o", 1),
            "RESETB": ("i", 1),
            "LOCK": ("o", 1),
            "PLLOUTCORE": ("o", 1),
            "PLLOUTGLOBAL": ("o", 1),
        }

        required = ("PACKAGEPIN",)
        default = {"RESETB": Const(1)}
        super().__init__("SB_PLL40_PAD", params, ports, required, default)


class SensorPlatform(LatticeICE40Platform):
    device = "iCE40HX8K"
    package = "BG121"
    resources = [
        Resource("clk25", 0, Pins("B6", dir="i"), Clock(25e6)),
        Resource("user_led", 0, Pins("A10", dir="o")),
        Resource("user_led", 1, Pins("A11", dir="o")),
        Resource("user_sw", 0, Pins("L1", dir="i")),
        Resource("user_sw", 1, Pins("L7", dir="i")),
        Resource(
            "adc", 0,
            Subsignal("cs", Pins("L2", dir="o")),
            Subsignal("dout", Pins("L3", dir="o")),
            Subsignal("sclk", Pins("L4", dir="o")),
        ),
        Resource(
            "daqnet", 0,
            Subsignal("led1", Pins("A3", dir="o")),
            Subsignal("led2", Pins("A4", dir="o")),
            Subsignal("txp", Pins("C2", dir="o")),
            Subsignal("txn", Pins("C1", dir="o")),
            Subsignal("rx", Pins("B2", dir="i")),
        ),
    ]
    connectors = []


class SwitchPlatform(LatticeICE40Platform):
    device = "iCE40HX8K"
    package = "BG121"
    resources = [
        Resource("clk25", 0, Pins("B6", dir="i")),
        Resource("user_led", 0, Pins("A11", dir="o")),
        Resource("user_led", 1, Pins("A10", dir="o")),
        Resource(
            "uart", 0,
            Subsignal("rx", Pins("A4", dir="i")),
            Subsignal("tx", Pins("A3", dir="o")),
        ),
        Resource(
            "flash", 0,
            Subsignal("sdi", Pins("K9", dir="o")),
            Subsignal("sdo", Pins("J9", dir="i")),
            Subsignal("sck", Pins("L10", dir="o")),
            Subsignal("cs", Pins("K10", dir="o")),
            Subsignal("io2", Pins("K11", dir="i")),
            Subsignal("io3", Pins("J11", dir="i")),
        ),
        Resource(
            "rmii", 0,
            Subsignal("txd0", Pins("J3", dir="o")),
            Subsignal("txd1", Pins("L1", dir="o")),
            Subsignal("txen", Pins("L2", dir="o")),
            Subsignal("rxd0", Pins("K5", dir="i")),
            Subsignal("rxd1", Pins("J5", dir="i")),
            Subsignal("crs_dv", Pins("L4", dir="i")),
            Subsignal("ref_clk", Pins("K4", dir="i")),
        ),
        Resource(
            "mdio", 0,
            Subsignal("mdc", Pins("K3", dir="o")),
            Subsignal("mdio", Pins("L3", dir="io")),
        ),
        Resource(
            "phy", 0,
            Subsignal("rst", Pins("K2", dir="o")),
            Subsignal("led", Pins("J2", dir="o")),
        ),
        Resource(
            "daqnet", 0,
            Subsignal("led1", Pins("C4", dir="o")),
            Subsignal("led2", Pins("D3", dir="o")),
            Subsignal("txp", Pins("B1", dir="o")),
            Subsignal("txn", Pins("B2", dir="o")),
            Subsignal("rx", Pins("C1", dir="i")),
        ),
        Resource(
            "daqnet", 1,
            Subsignal("led1", Pins("D2", dir="o")),
            Subsignal("led2", Pins("C3", dir="o")),
            Subsignal("txp", Pins("E1", dir="o")),
            Subsignal("txn", Pins("D1", dir="o")),
            Subsignal("rx", Pins("E3", dir="i")),
        ),
        Resource(
            "daqnet", 2,
            Subsignal("led1", Pins("G3", dir="o")),
            Subsignal("led2", Pins("F3", dir="o")),
            Subsignal("txp", Pins("F1", dir="o")),
            Subsignal("txn", Pins("F2", dir="o")),
            Subsignal("rx", Pins("G2", dir="i")),
        ),
        Resource(
            "daqnet", 3,
            Subsignal("led1", Pins("F4", dir="o")),
            Subsignal("led2", Pins("H3", dir="o")),
            Subsignal("txp", Pins("H1", dir="o")),
            Subsignal("txn", Pins("H2", dir="o")),
            Subsignal("rx", Pins("K1", dir="i")),
        ),
    ]
    connectors = []
