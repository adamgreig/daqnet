"""
Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Signal, Module, ClockDomain
from .platform import SB_PLL40_PAD

from .ethernet.mac import MAC
from .ethernet.ip import IPStack
from .user import User


class LEDBlinker:
    def __init__(self, nbits):
        self.led = Signal()
        self.nbits = nbits

    def elaborate(self, platform):
        m = Module()
        divider = Signal(self.nbits)
        m.d.sync += divider.eq(divider + 1)
        m.d.comb += self.led.eq(divider[-1])
        return m


class Top:
    def __init__(self, platform, args):
        pass


class SensorTop(Top):
    def __init__(self, platform, args):
        self.led_blinker = LEDBlinker(23)

    def elaborate(self, platform):
        m = Module()

        # Set up PLL
        m.submodules.pll = pll = SB_PLL40_PAD(0, 31, 3, 2)
        pll.packagepin = platform.request("clk25")
        pll.plloutglobal = Signal()

        # Set up clock domain on PLL output
        cd = ClockDomain("sync", reset_less=True)
        m.d.comb += cd.clk.eq(pll.plloutglobal)
        m.domains += cd

        # Create LED blinker in PLL clock domain
        blinker = self.led_blinker.elaborate(platform)
        m.submodules.led_blinker = blinker
        m.d.comb += platform.request("user_led_3").eq(self.led_blinker.led)

        return m


class SwitchTop(Top):
    def __init__(self, platform, args):
        self.led_blinker = LEDBlinker(24)

    def elaborate(self, platform):
        m = Module()

        # Set up PLL to multiply 25MHz clock to 100MHz clock
        m.submodules.pll = pll = SB_PLL40_PAD(0, 31, 3, 2)
        pll.packagepin = platform.request("clk25")
        pll.plloutglobal = Signal()

        # Set up clock domain on output of PLL
        cd = ClockDomain("sync", reset_less=True)
        m.d.comb += cd.clk.eq(pll.plloutglobal)
        m.domains += cd

        # Ethernet MAC
        rmii = platform.request_group("rmii")
        phy_rst = platform.request("phy_rst")
        eth_led = platform.request("eth_led")
        mac_addr = "02:44:4E:30:76:9E"
        mac = MAC(100e6, 0, mac_addr, rmii, phy_rst, eth_led)
        m.submodules.mac = mac

        # Explicitly zero unused inputs in MAC
        m.d.comb += [
            mac.phy_reset.eq(0),
        ]

        # User data stuff
        user = User()
        m.submodules.user = user

        # IP stack
        ip4_addr = "10.1.1.5"
        m.submodules.ipstack = ipstack = IPStack(
            mac_addr, ip4_addr, 16, 1735, mac.rx_port, mac.tx_port,
            user.mem_r_port, user.mem_w_port)
        m.d.comb += [
            mac.tx_start.eq(ipstack.tx_start),
            mac.tx_len.eq(ipstack.tx_len),
            mac.tx_offset.eq(ipstack.tx_offset),
            ipstack.rx_valid.eq(mac.rx_valid),
            ipstack.rx_len.eq(mac.rx_len),
            ipstack.rx_offset.eq(mac.rx_offset),
            mac.rx_ack.eq(ipstack.rx_ack),
            ipstack.user_tx.eq(user.transmit_packet),
            user.transmit_ready.eq(ipstack.user_ready),
            user.packet_received.eq(ipstack.user_rx),
        ]

        return m
