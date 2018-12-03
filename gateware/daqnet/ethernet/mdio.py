"""
MDIO Controller

Copyright 2018 Adam Greig
"""

from migen import (Module, Signal, TSTriple, If, FSM, Array,
                   NextValue, NextState)


class MDIO(Module):
    """
    MDIO interface controller.

    Reads/writes MDIO registers on an attached PHY.

    Parameters:
        * `clk_div`: divider from controller clock to MDC (aim for ~2.5MHz)

    Pins:
        * `mdio`: MDIO pin (data in/out)
        * `mdc`: MDC pin (clock out)

    Inputs:
        * `phy_addr`: 5-bit PHY address
        * `reg_addr`: 5-bit register address to read/write to
        * `rw`: select read (0) or write (1) operation
        * `write_data`: 16-bit data to write
        * `start`: operation begins on rising edge of `start`

    Outputs:
        * `read_data`: 16-bit data read from register, valid once busy is 0
        * `busy`: 1 if controller is busy, 0 if ready to take requests
    """
    def __init__(self, clk_div, mdio, mdc):
        # Inputs
        self.phy_addr = Signal(5)
        self.reg_addr = Signal(5)
        self.rw = Signal()
        self.write_data = Signal(16)
        self.start = Signal()

        # Outputs
        self.read_data = Signal(16)
        self.busy = Signal()

        ###

        # Create tristate for MDIO
        self.mdio_t = TSTriple()
        if mdio is not None:
            # Skip special creation when mdio=None (for use with simulator)
            self.specials += self.mdio_t.get_tristate(mdio)

        # Create divided clock for MDC
        mdc_int = Signal()
        mdc_rise = Signal()
        mdc_fall = Signal()
        mdc_divider = Signal(max=clk_div)
        self.sync += (
            If(
                mdc_divider == 0,
                mdc_divider.eq(clk_div - 1),
                mdc_int.eq(0),
                mdc_fall.eq(1),
                mdc_rise.eq(0),
            ).Elif(
                mdc_divider == clk_div//2,
                mdc_divider.eq(mdc_divider - 1),
                mdc_int.eq(1),
                mdc_fall.eq(0),
                mdc_rise.eq(1),
            ).Else(
                mdc_divider.eq(mdc_divider - 1),
                mdc_fall.eq(0),
                mdc_rise.eq(0),
            )
        )

        # MDIO FSM
        self.submodules.fsm = FSM(reset_state="IDLE")
        self.comb += self.busy.eq(~self.fsm.ongoing("IDLE"))
        bit_counter = Signal(6)

        # Latches for inputs
        _phy_addr = Signal.like(self.phy_addr)
        _reg_addr = Signal.like(self.reg_addr)
        _rw = Signal.like(self.rw)
        _write_data = Signal.like(self.write_data)

        # Idle state
        # Constantly register input data and wait for START signal
        self.fsm.act(
            "IDLE",
            mdc.eq(0),
            self.mdio_t.oe.eq(0),

            # Latch input signals while in idle
            NextValue(_phy_addr, self.phy_addr),
            NextValue(_reg_addr, self.reg_addr),
            NextValue(_rw, self.rw),
            NextValue(_write_data, self.write_data),

            If(self.start == 1, NextState("SYNC"))
        )

        # Synchronise to MDC. Enter this state at any time.
        # Will transition to PRE_32 immediately after the next falling edge
        # on MDC.
        self.fsm.act(
            "SYNC",
            mdc.eq(0),
            self.mdio_t.oe.eq(0),

            If(mdc_fall == 1,
                NextValue(bit_counter, 32),
                NextState("PRE_32"))
        )

        # PRE_32
        # Preamble field: 32 bits of 1
        self.fsm.act(
            "PRE_32",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),

            # Output all 1s
            self.mdio_t.o.eq(1),

            # Count falling edges of MDC
            If(mdc_fall == 1,
                NextValue(bit_counter, bit_counter - 1)),
            # Transition to ST on the falling edge after 32 rising edges
            If(bit_counter == 0,
               NextValue(bit_counter, 2),
               NextState("ST"))
        )

        # ST
        # Start field: always 01
        self.fsm.act(
            "ST",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            self.mdio_t.o.eq(bit_counter[0]),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 2),
                NextState("OP"))
        )

        # OP
        # Opcode field: read=10, write=01
        self.fsm.act(
            "OP",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            (If(_rw == 1, self.mdio_t.o.eq(bit_counter[0]))
             .Else(self.mdio_t.o.eq(~bit_counter[0]))),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 5),
                NextState("PA5"))
        )

        # PA5
        # PHY address field, 5 bits
        self.fsm.act(
            "PA5",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            self.mdio_t.o.eq(Array(_phy_addr)[bit_counter - 1]),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 5),
                NextState("RA5"))
        )

        # RA5
        # Register address field, 5 bits
        self.fsm.act(
            "RA5",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            self.mdio_t.o.eq(Array(_reg_addr)[bit_counter - 1]),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 2),
                If(
                    _rw == 1,
                    NextState("TA_W")
                ).Else(
                    NextState("TA_R")
                ))
        )

        # TA
        # Turnaround, 2 bits, OE released for read operations
        self.fsm.act(
            "TA_R",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(0),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 16),
                NextState("D16_R"))
        )

        # TA
        # Turnaround, 2 bits, driven to 10 for write operations
        self.fsm.act(
            "TA_W",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            self.mdio_t.o.eq(~bit_counter[0]),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0,
                NextValue(bit_counter, 16),
                NextState("D16_W"))
        )

        # D16
        # Data field, read operation
        self.fsm.act(
            "D16_R",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(0),
            If(mdc_rise == 1,
                NextValue(Array(self.read_data)[bit_counter - 1],
                          self.mdio_t.i)),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0, NextState("IDLE"))
        )

        # D16
        # Data field, write operation
        self.fsm.act(
            "D16_W",
            mdc.eq(mdc_int),
            self.mdio_t.oe.eq(1),
            self.mdio_t.o.eq(Array(_write_data)[bit_counter - 1]),
            If(mdc_fall == 1, NextValue(bit_counter, bit_counter - 1)),
            If(bit_counter == 0, NextState("IDLE"))
        )


def test_mdio_read():
    import random
    from migen.sim import run_simulation

    mdc = Signal()
    mdio = MDIO(20, None, mdc)

    def testbench():
        rng = random.Random(0)

        # Run ten random reads in sequence
        for testrun in range(10):
            phy_addr = rng.randint(0, 31)
            reg_addr = rng.randint(0, 31)
            reg_value = rng.randint(0, 65535)

            # Idle clocks at start
            for _ in range(10):
                yield
            # Set up a register read
            yield (mdio.phy_addr.eq(phy_addr))
            yield (mdio.reg_addr.eq(reg_addr))
            yield (mdio.rw.eq(0))
            yield (mdio.start.eq(1))
            yield
            yield (mdio.phy_addr.eq(0))
            yield (mdio.reg_addr.eq(0))
            yield (mdio.start.eq(0))

            # Clock through the read
            ibits = [int(x) for x in f"{reg_value:016b}"]
            obits = []
            oebits = []
            mdio_clk = 0
            last_mdc = (yield mdc)
            while True:
                yield
                new_mdc = (yield mdc)
                # Detect rising edge
                if new_mdc and last_mdc == 0:
                    mdio_clk += 1
                    obits.append((yield mdio.mdio_t.o))
                    oebits.append((yield mdio.mdio_t.oe))
                    if mdio_clk == 64:
                        break
                    if mdio_clk >= 48:
                        yield (mdio.mdio_t.i.eq(ibits[mdio_clk - 48]))
                last_mdc = new_mdc

            for _ in range(100):
                yield

            read_data = (yield mdio.read_data)
            was_busy = (yield mdio.busy)

            # Check transmitted bits were correct
            pre_32 = [1]*32
            st = [0, 1]
            op = [1, 0]
            pa5 = [int(x) for x in f"{phy_addr:05b}"]
            ra5 = [int(x) for x in f"{reg_addr:05b}"]
            expected = pre_32 + st + op + pa5 + ra5
            assert obits[:46] == expected

            # Check OE transitioned correctly
            expected = [1]*46 + [0]*18
            assert oebits == expected

            # Check we read the correct value in the end
            expected = int("".join(str(x) for x in ibits), 2)
            assert read_data == expected
            assert not was_busy

    run_simulation(mdio, testbench(), vcd_name="mdio.vcd")


def test_mdio_write():
    import random
    from migen.sim import run_simulation

    mdc = Signal()
    mdio = MDIO(20, None, mdc)

    def testbench():
        rng = random.Random(0)

        # Run ten random writes in sequence
        for testrun in range(10):
            phy_addr = rng.randint(0, 31)
            reg_addr = rng.randint(0, 31)
            reg_value = rng.randint(0, 65535)

            # Idle clocks at start
            for _ in range(10):
                yield

            # Set up a register write
            yield (mdio.phy_addr.eq(phy_addr))
            yield (mdio.reg_addr.eq(reg_addr))
            yield (mdio.write_data.eq(reg_value))
            yield (mdio.rw.eq(1))
            yield (mdio.start.eq(1))
            yield
            yield (mdio.phy_addr.eq(0))
            yield (mdio.write_data.eq(0))
            yield (mdio.rw.eq(0))
            yield (mdio.reg_addr.eq(0))
            yield (mdio.start.eq(0))

            # Clock through the write
            obits = []
            oebits = []
            mdio_clk = 0
            last_mdc = (yield mdc)
            while True:
                yield
                new_mdc = (yield mdc)
                # Detect rising edge
                if new_mdc and last_mdc == 0:
                    mdio_clk += 1
                    obits.append((yield mdio.mdio_t.o))
                    oebits.append((yield mdio.mdio_t.oe))
                    if mdio_clk == 64:
                        break
                last_mdc = new_mdc

            # Idle at end
            for _ in range(100):
                yield

            was_busy = (yield mdio.busy)

            # Check transmitted bits were correct
            pre_32 = [1]*32
            st = [0, 1]
            op = [0, 1]
            pa5 = [int(x) for x in f"{phy_addr:05b}"]
            ra5 = [int(x) for x in f"{reg_addr:05b}"]
            ta = [1, 0]
            d16 = [int(x) for x in f"{reg_value:016b}"]
            expected = pre_32 + st + op + pa5 + ra5 + ta + d16
            assert obits == expected

            # Check OE transitioned correctly
            expected = [1]*64
            assert oebits == expected
            assert not was_busy

    run_simulation(mdio, testbench(), vcd_name="mdio.vcd")
