"""
Simple UART
"""

from migen import Module, Signal, FSM, If, Cat, NextValue, NextState


class UART_TX(Module):
    """
    Implements a simple UART transmitter.

    In this extremely simple example we just transmit the input byte as often
    as we can.

    Parameters:
        * `clk_freq`: input clock frequency in Hz
        * `baud`: output bit rate in Hz

    Inputs:
        * `tx_data`: input byte (8 bits)

    Outputs:
        * `tx_out`: output TX bitstream
    """
    def __init__(self, tx_data, clk_freq=100e6, baud=1e6):
        assert clk_freq > baud
        assert baud > 0

        self.tx_out = Signal()

        ratio = int(clk_freq // baud)
        divider = Signal(max=ratio)
        self.sync += If(
            divider == 0, divider.eq(ratio - 1)
        ).Else(divider.eq(divider - 1))
        strobe = Signal()
        self.comb += strobe.eq(divider == 0)

        bitno = Signal(3)
        latch = Signal(8)

        self.submodules.fsm = FSM(reset_state="IDLE")

        self.fsm.act(
            "IDLE",
            If(
                strobe,
                NextValue(latch, tx_data),
                NextState("START"),
            ).Else(
                NextValue(self.tx_out, 1),
            )
        )

        self.fsm.act(
            "START",
            If(
                strobe,
                NextValue(self.tx_out, 0),
                NextState("DATA")
            )
        )

        self.fsm.act(
            "DATA",
            If(
                strobe,
                NextValue(self.tx_out, latch[0]),
                NextValue(latch, Cat(latch[1:], 0)),
                NextValue(bitno, bitno + 1),
                If(
                    bitno == 7,
                    NextState("STOP")
                )
            )
        )

        self.fsm.act(
            "STOP",
            If(
                strobe,
                NextValue(self.tx_out, 1),
                NextState("IDLE"),
            )
        )


def test_uart_tx():
    from migen.sim import run_simulation

    data = Signal(8)
    tx = UART_TX(data)

    def tb():
        teststr = "Hello"
        for val in [ord(x) for x in teststr]:
            yield (data.eq(val))
            for _ in range(1000):
                yield

    run_simulation(tx, tb(), vcd_name="uart.vcd")
