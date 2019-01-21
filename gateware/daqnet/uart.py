"""
A UART transmitter.

Copyright 2017 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from migen import Module, Signal, If, FSM, NextValue, NextState, Array


class UARTTx(Module):
    """
    UART Transmitter.
    """
    def __init__(self, divider):
        """
        Parameters:
            * `divider`: amount to divide clock by for baud rate, constant.

        Inputs:
            * `data`: 8bit Signal containing data to transmit.
            * `start`: pulse high to begin transmission, for at least one
                       bit period. Assert `start` until `self.ready`
                       is deasserted.

        Outputs:
            * `ready`: asserted high when idle
            * `tx_out`: the output serial data
        """
        # Inputs
        self.data = Signal(8)
        self.start = Signal()

        # Outputs
        self.ready = Signal()
        self.tx_out = Signal()

        ###

        # Baud rate clock generator
        self.div = Signal(max=divider - 1)
        self.baud = Signal()
        self.sync += If(
            self.div == divider - 1,
            self.div.eq(0),
            self.baud.eq(1),
        ).Else(
            self.div.eq(self.div + 1),
            self.baud.eq(0)
        )

        # Transmitter state machine
        self.bitno = Signal(3)
        self.submodules.fsm = FSM(reset_state="IDLE")
        self.comb += self.ready.eq(self.fsm.ongoing("IDLE"))
        self.fsm.act(
            "IDLE",
            self.tx_out.eq(1),
            If(self.baud & self.start, NextState("START"))
        )
        self.fsm.act(
            "START",
            self.tx_out.eq(0),
            NextValue(self.bitno, 0),
            If(self.baud, NextState("DATA"))
        )
        self.fsm.act(
            "DATA",
            self.tx_out.eq(Array(self.data)[self.bitno]),
            If(
                self.baud,
                NextValue(self.bitno, self.bitno + 1),
                If(self.bitno == 7, NextState("STOP"))
            )
        )
        self.fsm.act(
            "STOP",
            self.tx_out.eq(1),
            If(self.baud, NextState("IDLE"))
        )


class UARTTxFromMemory(Module):
    """
    Given a port into a memory, provide for dumping the memory over a UART.
    """
    def __init__(self, divider, awidth, port):
        """
        Parameters:
            * `divider`: the UART baud rate divider (=clk/baud)
            * `awidth`: the width of the address bus

        Ports:
            * `port`: a read port to a Memory instance

        Inputs:
            * `startadr`: the first address to transmit
            * `stopadr`: the last address to transmit
            * `trigger`: transmission begins when pulsed high

        Outputs:
            * `self.ready`: low while transmitting
            * `self.tx_out`: the TX output
        """
        # Inputs
        self.startadr = Signal(awidth)
        self.stopadr = Signal(awidth)
        self.trigger = Signal()

        # Outputs
        self.ready = Signal()
        self.tx_out = Signal()

        ###

        self.uart_data = Signal(8)
        self.uart_start = Signal()
        self.submodules.uart = UARTTx(divider)
        self.comb += [
            self.uart.data.eq(self.uart_data),
            self.uart.start.eq(self.uart_start),
            self.tx_out.eq(self.uart.tx_out),
        ]

        self.adr = Signal(awidth)
        self.submodules.fsm = FSM(reset_state="IDLE")
        self.comb += self.ready.eq(self.fsm.ongoing("IDLE"))
        self.fsm.act(
            "IDLE",
            NextValue(self.adr, self.startadr),
            If(self.trigger, NextState("SETUP_READ"))
        )
        self.fsm.act(
            "SETUP_READ",
            NextValue(port.adr, self.adr),
            NextState("WAIT_READ")
        )
        self.fsm.act(
            "WAIT_READ",
            NextState("STORE_READ")
        )
        self.fsm.act(
            "STORE_READ",
            NextValue(self.uart_data, port.dat_r),
            NextValue(self.adr, self.adr + 1),
            NextState("SETUP_WRITE"),
        )
        self.fsm.act(
            "SETUP_WRITE",
            NextValue(self.uart_start, 1),
            If(self.uart.ready == 0, NextState("WAIT_WRITE"))
        )
        self.fsm.act(
            "WAIT_WRITE",
            NextValue(self.uart_start, 0),
            If(self.uart.ready, NextState("FINISH_WRITE"))
        )
        self.fsm.act(
            "FINISH_WRITE",
            If(
                self.adr == self.stopadr,
                NextState("IDLE")
            ).Else(
                NextState("SETUP_READ")
            )
        )


def test_uart_tx():
    from migen.sim import run_simulation
    divider = 10
    data = Signal(8)
    start = Signal()
    tx = UARTTx(divider)
    tx.comb += tx.data.eq(data)
    tx.comb += tx.start.eq(start)
    txout = []

    def tb():
        teststring = "Hello World"
        for val in [ord(x) for x in teststring]:
            yield (data.eq(val))
            yield (start.eq(1))
            while (yield tx.ready):
                yield
            yield (start.eq(0))
            while not (yield tx.ready):
                txout.append((yield tx.tx_out))
                yield

        expected_bits = []
        for c in [ord(x) for x in teststring]:
            # Start bit
            expected_bits.append(0)
            # Data, LSbit first
            for bit in "{:08b}".format(c)[::-1]:
                expected_bits.append(int(bit))
            # Stop bit
            expected_bits.append(1)

        assert txout[::divider] == expected_bits

    run_simulation(tx, tb())


def test_uart_tx_from_memory():
    from migen.sim import run_simulation
    from migen import Memory

    # Store some string in the memory, shifted left by 4 so each
    # character takes up 12 bits.
    teststring = "0123456789ABCDEF"
    mem = Memory(8, 16, [ord(x) for x in teststring])
    port = mem.get_port()

    divider = 10
    trigger = Signal()
    uartfrommem = UARTTxFromMemory(divider, 5, port)
    uartfrommem.comb += [
        uartfrommem.startadr.eq(0),
        uartfrommem.stopadr.eq(16),
        uartfrommem.trigger.eq(trigger),
    ]

    uartfrommem.specials += [mem, port]
    txout = []

    def tb():
        yield
        yield (trigger.eq(1))
        yield
        while (yield uartfrommem.ready):
            yield
        while not (yield uartfrommem.ready):
            if (yield uartfrommem.uart.baud):
                txout.append((yield uartfrommem.tx_out))
            yield

        # Generate the bits we expect to see
        expected_bits = [1]
        for c in [ord(x) for x in teststring]:
            # Start bit
            expected_bits.append(0)
            # Data, LSbit first, bottom byte
            for bit in "{:08b}".format(c)[::-1]:
                expected_bits.append(int(bit))
            # Stop bit, inter-byte idle bit as we prepare the next byte
            expected_bits.append(1)
            expected_bits.append(1)

        assert txout == expected_bits[:-1]

    run_simulation(uartfrommem, tb())
