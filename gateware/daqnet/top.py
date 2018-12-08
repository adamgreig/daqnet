from migen import Signal, Module, ClockDomain, Instance, If, Memory

from .ethernet.mac import MAC
from .uart import UARTTxFromMemory, UARTTx


class PLL(Module):
    def __init__(self, divr, divf, divq, filter_range, name="PLL"):
        self.clk_in = Signal()
        self.clk_out = Signal()
        self.specials += Instance(
            'SB_PLL40_PAD',
            name=name,
            p_FEEDBACK_PATH="SIMPLE",
            p_PLLOUT_SELECT="GENCLK",
            p_DIVR=divr,
            p_DIVF=divf,
            p_DIVQ=divq,
            p_FILTER_RANGE=filter_range,
            i_PACKAGEPIN=self.clk_in,
            i_RESETB=1,
            i_BYPASS=0,
            o_PLLOUTGLOBAL=self.clk_out,
        )


class ProtoSensorTop(Module):
    def __init__(self, platform):
        # Set up clock in
        self.clock_domains.sys = ClockDomain("sys")
        clk25 = platform.request("clk25")

        self.submodules.pll = PLL(divr=0, divf=31, divq=2, filter_range=2)
        self.comb += self.pll.clk_in.eq(clk25)
        self.comb += self.sys.clk.eq(self.pll.clk_out)

        leds = [platform.request("user_led") for _ in range(4)]
        counter = Signal(32)
        self.sync += counter.eq(counter + 1)
        self.comb += [leds[0].eq(counter[31]),
                      leds[1].eq(counter[30]),
                      leds[2].eq(counter[29])]

        rd = platform.request("RD")
        d = Signal()
        self.specials += Instance(
            "SB_IO",
            name="LVDS_RD",
            p_PIN_TYPE=6,
            p_IO_STANDARD="SB_LVDS_INPUT",
            i_PACKAGE_PIN=rd,
            o_D_IN_0=d,
            i_INPUT_CLK=self.sys.clk,
        )
        self.comb += leds[3].eq(d)


class ProtoSwitchTop(Module):
    def __init__(self, platform):
        self.clock_domains.sys = ClockDomain("sys")
        clk25 = platform.request("clk25")

        # Set up 100MHz PLL
        self.submodules.pll = PLL(divr=0, divf=31, divq=3, filter_range=2)
        self.comb += self.pll.clk_in.eq(clk25)
        self.comb += self.sys.clk.eq(self.pll.clk_out)

        # Instantiate Ethernet MAC
        rx_mem = Memory(8, 2048, [0x55 for _ in range(2048)])
        rx_port = rx_mem.get_port(write_capable=True)
        rx_port_r = rx_mem.get_port()
        self.specials += [rx_mem, rx_port, rx_port_r]
        rmii = platform.request("rmii")
        phy_rst = platform.request("phy_rst")
        eth_led = platform.request("eth_led")
        self.submodules.mac = MAC(100e6, 0, rx_port, rmii, phy_rst, eth_led)

        # Debug outputs
        uart = platform.request("uart")
        led1 = platform.request("user_led")
        led2 = platform.request("user_led")

        self.submodules.uarttx = UARTTxFromMemory(100, 11, rx_port_r)
        stopadr = Signal(11)
        self.sync += If(self.mac.rx_valid, stopadr.eq(self.mac.rx_len))
        self.comb += [
            uart.tx.eq(self.uarttx.tx_out),
            self.uarttx.startadr.eq(0),
            self.uarttx.stopadr.eq(stopadr),
            self.mac.rx_ack.eq(self.uarttx.ready),
            self.uarttx.trigger.eq(self.mac.rx_valid),
            led1.eq(self.mac.rx_valid),
            led2.eq(self.mac.rmii_rx.crc.crc_match),
        ]
