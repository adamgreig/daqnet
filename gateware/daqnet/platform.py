from nmigen import Signal, Instance, Const


class SB_IO:
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

        * package_pin: connect to top-level pin
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
        self.params = {
            "pin_type": in_pin_type | (out_pin_type << 2),
            "pullup": int(pullup),
            "neg_trigger": int(neg_trigger),
            "io_standard": io_standard,
        }

        self.ports = (
            ("PACKAGE_PIN", "io"),
            ("LATCH_INPUT_VALUE", "i"),
            ("CLOCK_ENABLE", "i"),
            ("INPUT_CLK", "i"),
            ("OUTPUT_CLK", "i"),
            ("OUTPUT_ENABLE", "i"),
            ("D_OUT_0", "i"),
            ("D_OUT_1", "i"),
            ("D_IN_0", "o"),
            ("D_IN_1", "o"),
        )

        self.ports_available = [p[0] for p in self.ports]
        self.ports_used = {}

    def change_pin_type(self, in_pin_type, out_pin_type):
        self.params["pin_type"] = in_pin_type | (out_pin_type << 2)

    def __getattr__(self, name):
        if name in self.ports_used:
            return self.ports_used[name]
        elif name.upper() in self.ports_available:
            self.ports_used[name] = Signal(name=name)
            return self.ports_used[name]
        else:
            raise AttributeError

    def get_fragment(self, platform):
        args = {f"p_{key.upper()}": val for (key, val) in self.params.items()}

        required_ports = ("PACKAGE_PIN",)

        for port, dirn, required in self.ports:
            if port.lower() in self.__dict__:
                args[f"{dirn}_{port}"] = getattr(self, port.lower())
            elif port in required_ports:
                raise ValueError(f"Required port {port} missing")

        return Instance("SB_IO", **args)


class SB_PLL40_PAD:
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
    def __init__(self, divr, divf, divq, filter_range, **kwargs):
        kwargs["divr"] = divr
        kwargs["divf"] = divf
        kwargs["divq"] = divq
        kwargs["filter_range"] = filter_range

        if "feedback_path" not in kwargs:
            kwargs["feedback_path"] = "SIMPLE"
        if "pllout_select" not in kwargs:
            kwargs["pllout_select"] = "GENCLK"

        self.params = kwargs

        self.ports = (
            ("PACKAGEPIN", "i"),
            ("EXTFEEDBACK", "i"),
            ("DYNAMICDELAY", "i"),
            ("LATCHINPUTVALUE", "i"),
            ("SCLK", "i"),
            ("SDI", "i"),
            ("SDO", "o"),
            ("RESETB", "i"),
            ("LOCK", "o"),
            ("PLLOUTCORE", "o"),
            ("PLLOUTGLOBAL", "o"),
        )

    def __getattr__(self, name):
        if name in self.ports_used:
            return self.ports_used[name]
        elif name.upper() in self.ports_available:
            self.ports_used[name] = Signal(name=name)
            return self.ports_used[name]
        else:
            raise AttributeError

    def get_fragment(self, platform):
        args = {f"p_{key.upper()}": val for (key, val) in self.params.items()}

        required_ports = ("PACKAGEPIN",)

        for port, dirn in self.ports:
            if port.lower() in self.__dict__:
                args[f"{dirn}_{port}"] = getattr(self, port.lower())
            elif port in required_ports:
                raise ValueError(f"Required port {port} missing")

        # Ensure i_RESETB is set high if not provided
        if "i_RESETB" not in args:
            args["i_RESETB"] = Const(1)

        return Instance("SB_PLL40_PAD", **args)


class Port:
    """
    Represents a port (one or more pins with the same name) available to the
    platform.
    """
    def __init__(self, name, dirn, pads):
        """
        name: name of port
        pads: either a single string of one pin location or a tuple of strings
        """
        self.name = name
        self.dirn = dirn
        self.pads = pads
        n = len(self.pads) if isinstance(self.pads, tuple) else 1
        self.signal = Signal(n, name=name)

    def make_pcf(self):
        """
        Returns a string of lines for the PCF file containing this port.
        """
        pcf_lines = []
        if isinstance(self.pads, tuple):
            for idx, p in enumerate(self.pads):
                pcf_lines.append(f"set_io {self.name}[{idx}] {p}")
        else:
            pcf_lines.append(f"set_io {self.name} {self.pads}")
        return "\n".join(pcf_lines)


class Platform:
    def __init__(self, ports):
        self.ports_available = {port.name: port for port in ports}
        self.ports_used = {}

    def request(self, port):
        if port in self.ports_available:
            self.ports_used[port] = self.ports_available[port]
            del self.ports_available[port]
            return self.ports_used[port].signal
        elif port in self.ports_used:
            raise ValueError(f"Port {port} already used")
        else:
            raise ValueError(f"Unknown port {port}")

    def get_pcf(self):
        return "\n".join(port.make_pcf() for port in self.ports_used.values())

    def get_ports(self):
        return [(port.signal, port.dirn) for port in self.ports_used.values()]


class SensorPlatform(Platform):
    def __init__(self, args):
        ports = (
            Port("clk25", "i", "B6"),
            Port("user_led_3", "o", "A10"),
            Port("user_led_4", "o", "A11"),
            Port("user_sw_1", "i", "L1"),
            Port("user_sw_2", "i", "L7"),
            Port("adc_cs", "o", "L2"),
            Port("adc_dout", "o", "L3"),
            Port("adc_sclk", "o", "L4"),
            Port("flash_sdi", "o", "K9"),
            Port("flash_sdo", "i", "J9"),
            Port("flash_sck", "o", "L10"),
            Port("flash_cs", "o", "K10"),
            Port("flash_io2", "i", "H11"),
            Port("flash_io3", "i", "J11"),
            Port("daqnet_led1", "o", "A3"),
            Port("daqnet_led2", "o", "A4"),
            Port("daqnet_txp", "o", "C2"),
            Port("daqnet_txn", "o", "C1"),
            Port("daqnet_rx", "i", "B2"),
        )

        super().__init__(ports)


class SwitchPlatform(Platform):
    def __init__(self, args):
        ports = (
            Port("clk25", "i", "B6"),
            Port("user_led_1", "o", "A11"),
            Port("user_led_2", "o", "A10"),
            Port("uart_rx", "i", "A4"),
            Port("uart_tx", "o", "A3"),
            Port("flash_sdi", "o", "K9"),
            Port("flash_sdo", "i", "J9"),
            Port("flash_sck", "o", "L10"),
            Port("flash_cs", "o", "K10"),
            Port("flash_io2", "i", "K11"),
            Port("flash_io3", "i", "J11"),
            Port("rmii_txd0", "o", "J3"),
            Port("rmii_txd1", "o", "L1"),
            Port("rmii_txen", "o", "L2"),
            Port("rmii_rxd0", "i", "K5"),
            Port("rmii_rxd1", "i", "J5"),
            Port("rmii_crs_dv", "i", "L4"),
            Port("rmii_ref_clk", "i", "K4"),
            Port("rmii_mdc", "o", "K3"),
            Port("rmii_mdio", "io", "L3"),
            Port("phy_rst", "o", "K2"),
            Port("eth_led", "o", "J2"),
            Port("daqnet_0_led1", "o", "C4"),
            Port("daqnet_0_led2", "o", "D3"),
            Port("daqnet_0_txp", "o", "B1"),
            Port("daqnet_0_txn", "o", "B2"),
            Port("daqnet_0_rx", "i", "C1"),
            Port("daqnet_1_led1", "o", "D2"),
            Port("daqnet_1_led2", "o", "C3"),
            Port("daqnet_1_txp", "o", "E1"),
            Port("daqnet_1_txn", "o", "D1"),
            Port("daqnet_1_rx", "i", "E3"),
            Port("daqnet_2_led1", "o", "G3"),
            Port("daqnet_2_led2", "o", "F3"),
            Port("daqnet_2_txp", "o", "F1"),
            Port("daqnet_2_txn", "o", "F2"),
            Port("daqnet_2_rx", "i", "G2"),
            Port("daqnet_3_led1", "o", "F4"),
            Port("daqnet_3_led2", "o", "H3"),
            Port("daqnet_3_txp", "o", "H1"),
            Port("daqnet_3_txn", "o", "H2"),
            Port("daqnet_3_rx", "i", "K1"),
        )

        super().__init__(ports)
