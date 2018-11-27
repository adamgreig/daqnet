from migen import Signal, Module, ClockDomain, Instance, Cat
from .adc import ADC
from .uart import UART_TX


class PLL(Module):
    def __init__(self, divr, divf, divq, filter_range, name="PLL"):
        self.clk_in = Signal()
        self.clk_out = Signal()
        self.specials += Instance(
            '(* BEL="X16/Y33/pll_3" *) SB_PLL40_PAD',
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


class BlackIceTop(Module):
    def __init__(self, platform):
        # Set up explicit clock
        self.clock_domains.sys = ClockDomain("sys")
        clk100 = platform.request("clk100")
        self.submodules.pll = PLL(divr=0, divf=7, divq=4, filter_range=5)
        self.comb += self.pll.clk_in.eq(clk100)
        self.comb += self.sys.clk.eq(self.pll.clk_out)

        leds = [platform.request("user_led") for _ in range(4)]

        # counter = Signal(24)
        # self.sync += counter.eq(counter + 1)
        # self.comb += [leds[i].eq(counter[-1]) for i in range(2)]

        TAPS = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}
        k = 7
        tap = TAPS[k]
        prbs = Signal(k, reset=1)
        x = Signal()
        self.comb += x.eq(prbs[k-1] ^ prbs[tap-1])
        self.sync += Cat(prbs).eq(Cat(x, prbs))

        self.comb += [leds[i].eq(prbs[i]) for i in range(3)]
        self.sync += [leds[3].eq(prbs == 1)]

        if False:
            # Run ADC
            adc_pins = platform.request("adc")
            self.submodules.adc = ADC(self.clk100, adc_pins.ain, adc_pins.dout1)
            self.comb += adc_pins.dout2.eq(self.adc.diff_in)

            # Send ADC output via UART
            uart_pins = platform.request("serial")
            self.submodules.uart_tx = UART_TX(self.adc.samp_dat)
            self.comb += uart_pins.tx.eq(self.uart_tx.tx_out)

            # Drive LEDs off
            leds = [platform.request("user_led") for _ in range(4)]
            for led in leds:
                self.comb += led.eq(0)


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
