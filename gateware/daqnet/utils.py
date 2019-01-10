"""
Gateway utilities and common modules.

Copyright 2018-2019 Adam Greig
"""

from nmigen import Module, Signal


class PulseStretch:
    def __init__(self, nclks):
        # Inputs
        self.trigger = Signal()

        # Outputs
        self.pulse = Signal()

        self.nclks = nclks

    def get_fragment(self, platform):
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

        return m.lower(platform)
