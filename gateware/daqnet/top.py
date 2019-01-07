from nmigen import Signal, Module, ClockDomain

# from .ethernet.mac import MAC
# from .ethernet.ip import IPStack
# from .uart import UARTTxFromMemory, UARTTx


class LEDBlinker:
    def __init__(self, nbits):
        self.led = Signal()
        self.nbits = nbits

    def get_fragment(self, platform):
        m = Module()
        divider = Signal(self.nbits)
        m.d.sync += divider.eq(divider + 1)
        m.d.comb += self.led.eq(divider[-1])
        return m.lower(platform)


class Top:
    def __init__(self, platform, args):
        pass


class SwitchTop(Top):
    def __init__(self, platform, args):
        self.led_blinker = LEDBlinker(24)

    def get_fragment(self, platform):
        m = Module()

        for name, module in platform.get_instances():
            setattr(m.submodules, name, module)

        cd = ClockDomain("sync", reset_less=True)
        m.d.comb += cd.clk.eq(platform.clk)

        blinker = self.led_blinker.get_fragment(platform)
        blinker.add_domains(cd)
        m.submodules.led_blinker = blinker
        m.d.comb += platform.user_led_1_pad.eq(self.led_blinker.led)

        frag = m.lower(platform)

        for port, dirn in platform.get_ports():
            frag.add_ports(port, dir=dirn)

        return frag


class SensorTop(Top):
    def __init__(self, platform, args):
        self.led_blinker = LEDBlinker(23)

    def get_fragment(self, platform):
        m = Module()

        for name, module in platform.get_instances():
            setattr(m.submodules, name, module)

        cd = ClockDomain("sync", reset_less=True)
        m.d.comb += cd.clk.eq(platform.clk)

        blinker = self.led_blinker.get_fragment(platform)
        blinker.add_domains(cd)
        m.submodules.led_blinker = blinker
        m.d.comb += platform.user_led_3_pad.eq(self.led_blinker.led)

        frag = m.lower(platform)

        for port, dirn in platform.get_ports():
            frag.add_ports(port, dir=dirn)

        return frag


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
        rmii = platform.request("rmii")
        phy_rst = platform.request("phy_rst")
        eth_led = platform.request("eth_led")
        mac_addr = "02:44:4E:30:76:9E"
        self.submodules.mac = MAC(100e6, 0, mac_addr, rmii, phy_rst, eth_led)

        # Instantiate IP stack
        ip4_addr = "10.1.1.5"
        self.submodules.ipstack = IPStack(
            ip4_addr, mac_addr, self.mac.rx_port, self.mac.tx_port)
        self.comb += [
            self.ipstack.rx_valid.eq(self.mac.rx_valid),
            self.ipstack.rx_len.eq(self.mac.rx_len),
            self.ipstack.tx_ready.eq(self.mac.tx_ready),
            self.mac.rx_ack.eq(self.ipstack.rx_ack),
            self.mac.tx_start.eq(self.ipstack.tx_start),
            self.mac.tx_len.eq(self.ipstack.tx_len),
        ]

        # Debug outputs
        led1 = platform.request("user_led")
        led2 = platform.request("user_led")

        self.comb += [
            led1.eq(eth_led),
            led2.eq(self.mac.link_up),
        ]
