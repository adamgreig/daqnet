from nmigen import Signal, Instance, Const


class SB_IO:
    """
    I/O Primitive SB_IO.

    Parameters:
        * in_pin_type: one of SB_IO.PIN_INPUT (default), PIN_INPUT_LATCH,
          PIN_INPUT_REGISTERED, PIN_INPUT_REGISTERED_LATCH, or PIN_INPUT_DDR.
        * out_pin_type: one of SB_IO.PIN_NO_OUTPUT (default), PIN_OUTPUT,
          PIN_OUTPUT_TRISTATE, PIN_OUTPUT_ENABLE_REGISTERED,
          PIN_OUTPUT_REGISTERED, PIN_OUTPUT_REGISTERED_ENABLE,
          PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED, PIN_OUTPUT_DDR,
          PIN_OUTPUT_DDR_ENABLE, PIN_OUTPUT_DDR_ENABLE_REGISTERED,
          PIN_OUTPUT_REGISTERED_INVERTED,
          PIN_OUTPUT_REGISTERED_ENABLE_INVERTED,
          PIN_OUTPUT_REGISTERED_ENABLE_REGISTERED_INVERTED.
        * pullup: True or False, whether to enable internal pullup.
        * neg_trigger: True or False, whether to invert polarity of IO FFs
        * io_standard: One of SB_LVCMOS or SB_LVDS_INPUT

    Pins:
        * package_pin: connect to top-level pin

    Inputs:
        * latch_input_value: when high, maintain current input value
        * input_clock: clock for input FFs
        * output_clock: clock for output FFs
        * output_enable: when high, enable output, otherwise high impedance
        * d_out_0: Output data, or in DDR mode, data for rising output_clock
        * d_out_1: In DDR mode, data for falling output_clock edge

    Outputs:
        * d_in_0: Input data, or in DDR mode, data at rising input_clock edge
        * d_in_1: In DDR mode, data at falling input_clock edge

    Note clock_enable is omitted to prevent inefficient instantiation of
    constant drivers; if you need clock_enable instantiate SB_IO directly.
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
                 pullup=False, neg_trigger=False, io_standard="SB_LVCMOS"):
        self.in_pin_type = in_pin_type
        self.out_pin_type = out_pin_type
        self.pullup = int(pullup)
        self.neg_trigger = int(neg_trigger)
        self.io_standard = io_standard

    def get_fragment(self, platform):
        pin_type = self.in_pin_type | (self.out_pin_type << 2)
        inst = Instance(
            "SB_IO",
            p_PIN_TYPE=pin_type,
            p_PULLUP=self.pullup,
            p_NEG_TRIGGER=self.neg_trigger,
            p_IO_STANDARD=self.io_standard,
        )

        if hasattr(self, "package_pin"):
            inst.named_ports["PACKAGE_PIN"] = self.package_pin
            inst.add_ports(self.package_pin, dir="io")

        for name in ("LATCH_INPUT_VALUE", "INPUT_CLK", "OUTPUT_CLK",
                     "OUTPUT_ENABLE", "D_OUT_0", "D_OUT_1"):
            if hasattr(self, name.lower()):
                inst.named_ports[name] = getattr(self, name.lower())
                inst.add_ports(getattr(self, name.lower()), dir="i")

        for name in ("D_IN_0", "D_IN_1"):
            if hasattr(self, name.lower()):
                inst.named_ports[name] = getattr(self, name.lower())
                inst.add_ports(getattr(self, name.lower()), dir="o")

        return inst


class SB_PLL40_PAD:
    """
    Phase-locked loop primitive SB_PLL40_PAD.

    This class only supports simple use of generating a frequency and
    outputting it, without any static or dynamic delay, and without any
    external feedback.

    Used when the PLL source is an input pad in banks 0 or 2, and the source
    clock is not required inside the FPGA.

    Parameters:
        * divr, divf, divq, filter_range: PLL parameters. Refer to
          documentation or icepll executable.

    Inputs:
        * package_pin: Connect directly to input pad

    Outputs:
        * plloutcore: Clock output to core logic
        * plloutglobal: Clock output to global buffer
        * lock: PLL lock indicator
    """
    def __init__(self, divr, divf, divq, filter_range):
        self.divr = divr
        self.divf = divf
        self.divq = divq
        self.filter_range = filter_range

    def get_fragment(self, platform):
        inst = Instance(
            "SB_PLL40_PAD",
            p_FEEDBACK_PATH="SIMPLE",
            p_PLLOUT_SELECT="GENCLK",
            p_DIVR=self.divr,
            p_DIVF=self.divf,
            p_DIVQ=self.divq,
            p_FILTER_RANGE=self.filter_range,
            i_PACKAGEPIN=self.packagepin,
            i_RESETB=Const(1),
        )

        for name in ("LOCK", "PLLOUTCORE", "PLLOUTGLOBAL"):
            if hasattr(self, name.lower()):
                inst.named_ports[name] = getattr(self, name.lower())
                inst.add_ports(getattr(self, name.lower()), dir="o")

        return inst


class Pin:
    def __init__(self, name, dirn, pads, make_sb_io=False):
        self.name = name
        self.pads = pads
        self.dirn = dirn

        if make_sb_io:
            self.sb_io = SB_IO()
            self.sb_io.package_pin = Signal(name=name)
        else:
            self.sb_io = None
            self.signal = Signal(name=name)

    def make_pcf(self):
        """
        Returns a list of string entries for PCF file for this pin.
        """
        pcf_lines = []
        if isinstance(self.pads, tuple):
            for idx, p in enumerate(self.pads):
                pcf_lines.append(f"set_io {self.name}[{idx}] {p}")
        else:
            pcf_lines.append(f"set_io {self.name} {self.pads}")
        return pcf_lines


class Platform:
    def __init__(self, pins):
        self.pins = pins
        self.modules = []
        pcf = []

        for pin in self.pins:
            if pin.sb_io:
                setattr(self, f"{pin.name}_sb_io", pin.sb_io)
            else:
                setattr(self, f"{pin.name}_pad", pin.signal)
            pcf += pin.make_pcf()

        self.pcf = "\n".join(pcf)

    def get_instances(self):
        instances = []
        for pin in self.pins:
            if pin.sb_io:
                subfrag = pin.sb_io
                subfrag_name = f"{pin.name}_sb_io"
                instances.append((subfrag_name, subfrag))
        for name, module in self.modules:
            instances.append((name, module))
        return instances

    def get_ports(self):
        ports = []
        for pin in self.pins:
            if pin.sb_io:
                ports.append((pin.sb_io.package_pin, pin.dirn))
            else:
                ports.append((pin.signal, pin.dirn))
        return ports


class SensorPlatform(Platform):
    def __init__(self, args):
        pins = (
            Pin("clk25", "i", "B6"),
            Pin("user_led_3", "o", "A10"),
            Pin("user_led_4", "o", "A11"),
            Pin("user_sw_1", "i", "L1"),
            Pin("user_sw_2", "i", "L7"),
            Pin("adc_cs", "o", "L2"),
            Pin("adc_dout", "o", "L3"),
            Pin("adc_sclk", "o", "L4"),
            Pin("flash_sdi", "o", "K9"),
            Pin("flash_sdo", "i", "J9"),
            Pin("flash_sck", "o", "L10"),
            Pin("flash_cs", "o", "K10"),
            Pin("flash_io2", "i", "H11"),
            Pin("flash_io3", "i", "J11"),
            Pin("daqnet_led1", "o", "A3"),
            Pin("daqnet_led2", "o", "A4"),
            Pin("daqnet_txp", "o", "C2"),
            Pin("daqnet_txn", "o", "C1"),
            Pin("daqnet_rx", "i", "B2", make_sb_io=True),
        )

        super().__init__(pins)

        self.daqnet_rx_sb_io.io_standard = "SB_LVDS_INPUT"

        self.pll = SB_PLL40_PAD(divr=0, divf=31, divq=3, filter_range=2)
        self.pll.packagepin = self.clk25_pad
        self.clk = self.pll.plloutglobal
        self.modules.append(("PLL", self.pll))


class SwitchPlatform(Platform):
    def __init__(self, args):
        pins = (
            Pin("clk25", "i", "B6"),
            Pin("user_led_1", "o", "A11"),
            Pin("user_led_2", "o", "A10"),
            Pin("uart_rx", "i", "A4"),
            Pin("uart_tx", "o", "A3"),
            Pin("flash_sdi", "o", "K9"),
            Pin("flash_sdo", "i", "J9"),
            Pin("flash_sck", "o", "L10"),
            Pin("flash_cs", "o", "K10"),
            Pin("flash_io2", "i", "K11"),
            Pin("flash_io3", "i", "J11"),
            Pin("rmii_txd0", "o", "J3"),
            Pin("rmii_txd1", "o", "L1"),
            Pin("rmii_txen", "o", "L2"),
            Pin("rmii_rxd0", "i", "K5"),
            Pin("rmii_rxd1", "i", "J5"),
            Pin("rmii_crs_dv", "i", "L4"),
            Pin("rmii_ref_clk", "i", "K4"),
            Pin("rmii_mdc", "o", "K3"),
            Pin("rmii_mdio", "io", "L3"),
            Pin("phy_rst", "o", "K2"),
            Pin("eth_led", "o", "J2"),
            Pin("daqnet_0_led1", "o", "C4"),
            Pin("daqnet_0_led2", "o", "D3"),
            Pin("daqnet_0_txp", "o", "B1"),
            Pin("daqnet_0_txn", "o", "B2"),
            Pin("daqnet_0_rx", "i", "C1", make_sb_io=True),
            Pin("daqnet_1_led1", "o", "D2"),
            Pin("daqnet_1_led2", "o", "C3"),
            Pin("daqnet_1_txp", "o", "E1"),
            Pin("daqnet_1_txn", "o", "D1"),
            Pin("daqnet_1_rx", "i", "E3", make_sb_io=True),
            Pin("daqnet_2_led1", "o", "G3"),
            Pin("daqnet_2_led2", "o", "F3"),
            Pin("daqnet_2_txp", "o", "F1"),
            Pin("daqnet_2_txn", "o", "F2"),
            Pin("daqnet_2_rx", "i", "G2", make_sb_io=True),
            Pin("daqnet_3_led1", "o", "F4"),
            Pin("daqnet_3_led2", "o", "H3"),
            Pin("daqnet_3_txp", "o", "H1"),
            Pin("daqnet_3_txn", "o", "H2"),
            Pin("daqnet_3_rx", "i", "K1", make_sb_io=True),
        )

        super().__init__(pins)

        self.daqnet_0_rx_sb_io.io_standard = "SB_LVDS_INPUT"
        self.daqnet_1_rx_sb_io.io_standard = "SB_LVDS_INPUT"
        self.daqnet_2_rx_sb_io.io_standard = "SB_LVDS_INPUT"
        self.daqnet_3_rx_sb_io.io_standard = "SB_LVDS_INPUT"

        self.pll = SB_PLL40_PAD(divr=0, divf=31, divq=3, filter_range=2)
        self.pll.packagepin = self.clk25_pad
        self.clk = self.pll.plloutglobal = Signal()
        self.modules.append(("PLL", self.pll))
