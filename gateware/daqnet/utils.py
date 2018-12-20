"""
Gateway utilities and common modules.

Copyright 2018 Adam Greig
"""

from migen import Module, Signal, FSM, NextValue, NextState, If


class PulseStretch(Module):
    def __init__(self, nclks):
        # Inputs
        self.input = Signal()

        # Outputs
        self.output = Signal()

        ###

        counter = Signal(max=nclks)
        self.submodules.fsm = FSM(reset_state="WAIT")

        self.comb += self.output.eq(self.fsm.ongoing("STRETCH"))

        self.fsm.act(
            "WAIT",
            NextValue(counter, 0),
            If(self.input == 1, NextState("STRETCH")),
        )

        self.fsm.act(
            "STRETCH",
            If(
                counter == nclks-1,
                NextState("WAIT"),
            ).Else(
                NextValue(counter, counter + 1)
            )
        )
