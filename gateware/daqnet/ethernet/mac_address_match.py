"""
MAC Address Matcher

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

import operator
from functools import reduce

from nmigen import Module, Signal


class MACAddressMatch:
    """
    MAC Address Matcher

    Parameters:
        * `mac_addr`: 6-byte MAC address (list of ints)

    Inputs:
        * `reset`: Restart address matching
        * `data`: 8-bit input data
        * `data_valid`: Pulsed high when new data is ready at `data`.

    Outputs:
        * `mac_match`: High if destination MAC address matches or is broadcast.
                       Remains high until `reset` is asserted.
    """
    def __init__(self, mac_addr):
        # Inputs
        self.reset = Signal()
        self.data = Signal(8)
        self.data_valid = Signal()

        # Outputs
        self.mac_match = Signal()

        # Parameters
        self.mac_addr = mac_addr

    def get_fragment(self, platform):
        m = Module()
        mac = [Signal(8) for _ in range(6)]

        m.d.sync += self.mac_match.eq(
            reduce(operator.and_,
                   [(mac[idx] == self.mac_addr[idx]) | (mac[idx] == 0xFF)
                    for idx in range(6)]))

        with m.FSM():
            with m.State("RESET"):
                m.d.sync += [mac[idx].eq(0) for idx in range(6)]
                with m.If(~self.reset):
                    m.next = "BYTE0"

            for idx in range(6):
                next_state = f"BYTE{idx+1}" if idx < 5 else "DONE"

                with m.State(f"BYTE{idx}"):
                    m.d.sync += mac[idx].eq(self.data)
                    with m.If(self.reset):
                        m.next = "RESET"
                    with m.Elif(self.data_valid):
                        m.next = next_state

            with m.State("DONE"):
                with m.If(self.reset):
                    m.next = "RESET"

        return m.lower(platform)


def test_mac_address_match():
    import random
    from nmigen.back import pysim

    mac_address = [random.randint(0, 255) for _ in range(6)]
    mac_address = [0x01, 0x23, 0x45, 0x67, 0x89, 0xAB]
    mac_matcher = MACAddressMatch(mac_address)

    data = mac_matcher.data
    data_valid = mac_matcher.data_valid
    reset = mac_matcher.reset

    def testbench():
        yield (reset.eq(1))
        for _ in range(10):
            yield
        yield (reset.eq(0))
        yield

        # Check it matches its own MAC address
        for byte in mac_address:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 1

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

        # Check it matches broadcast
        for byte in [0xFF]*6:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 1

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

        # Check it doesn't match some other MAC address
        for byte in mac_address[::-1]:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 0

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

    frag = mac_matcher.get_fragment(None)
    vcdf = open("mac_matcher.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()
