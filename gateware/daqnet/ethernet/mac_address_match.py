"""
MAC Address Matcher

Copyright 2018 Adam Greig
"""

import operator
from functools import reduce

from migen import Module, Signal, If, FSM, NextValue, NextState


class MACAddressMatch(Module):
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

        ###

        mac = [Signal(8) for _ in range(6)]

        self.sync += self.mac_match.eq(
            reduce(operator.and_,
                   [(mac[idx] == mac_addr[idx]) | (mac[idx] == 0xFF)
                    for idx in range(6)]))

        self.submodules.fsm = FSM(reset_state="RESET")

        self.fsm.act(
            "RESET",
            [NextValue(mac[idx], 0) for idx in range(6)],
            If(~self.reset, NextState("BYTE0")),
        )

        for idx in range(6):
            next_state = f"BYTE{idx+1}" if idx < 5 else "DONE"
            self.fsm.act(
                f"BYTE{idx}",
                NextValue(mac[idx], self.data),
                If(
                    self.reset == 1,
                    NextState("RESET")
                ).Elif(
                    self.data_valid,
                    NextState(next_state),
                )
            )

        self.fsm.act(
            "DONE",
            If(self.reset == 1, NextState("RESET"))
        )


def test_mac_address_match():
    import random
    from migen.sim import run_simulation

    data = Signal(8)
    data_valid = Signal()
    reset = Signal()

    mac_address = [random.randint(0, 255) for _ in range(6)]
    mac_address = [0x01, 0x23, 0x45, 0x67, 0x89, 0xAB]
    mac_matcher = MACAddressMatch(mac_address)

    mac_matcher.comb += [
        mac_matcher.data.eq(data),
        mac_matcher.data_valid.eq(data_valid),
        mac_matcher.reset.eq(reset),
    ]

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

    run_simulation(mac_matcher, testbench(), vcd_name="mac_matcher.vcd")
