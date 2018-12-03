from migen import Signal, Module, ClockDomain, Instance, If

from .ethernet.mdio import MDIO


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

        self.submodules.pll = PLL(divr=0, divf=31, divq=3, filter_range=2)
        self.comb += self.pll.clk_in.eq(clk25)
        self.comb += self.sys.clk.eq(self.pll.clk_out)

        rmii = platform.request("rmii")

        self.submodules.mdio = MDIO(40, rmii.mdio, rmii.mdc)

        self.comb += self.mdio.phy_addr.eq(0)
        self.comb += self.mdio.reg_addr.eq(0)
        self.comb += self.mdio.rw.eq(0)

        divider = Signal(24)
        self.sync += divider.eq(divider + 1)
        self.sync += If(
            divider == 0,
            self.mdio.start.eq(1)
        ).Else(
            self.mdio.start.eq(0)
        )
