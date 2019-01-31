"""
Gateway utilities and common modules.

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Module, Signal, Cat


class LFSR:
    TAPS = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}

    def __init__(self, k):
        self.reset = Signal()
        self.state = Signal(k, reset=1)

        if k not in LFSR.TAPS.keys():
            raise ValueError(f"k={k} invalid for LFSR")

        self.k = k

    def elaborate(self, platform):
        m = Module()
        x = Signal()
        tap = LFSR.TAPS[self.k]
        m.d.comb += x.eq(self.state[self.k-1] ^ self.state[tap-1])
        with m.If(self.reset):
            m.d.sync += self.state.eq(1)
        with m.Else():
            m.d.sync += Cat(self.state).eq(Cat(x, self.state))

        return m


class PulseStretch:
    def __init__(self, nclks):
        # Inputs
        self.trigger = Signal()

        # Outputs
        self.pulse = Signal()

        self.nclks = nclks

    def elaborate(self, platform):
        m = Module()

        counter = Signal(max=self.nclks)

        with m.FSM() as fsm:
            m.d.comb += self.pulse.eq(fsm.ongoing("STRETCH"))
            with m.State("WAIT"):
                m.d.sync += counter.eq(0)
                with m.If(self.trigger):
                    m.next = "STRETCH"

            with m.State("STRETCH"):
                with m.If(counter == self.nclks - 1):
                    m.next = "WAIT"
                with m.Else():
                    m.d.sync += counter.eq(counter + 1)

        return m
