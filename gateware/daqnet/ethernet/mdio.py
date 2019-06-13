"""
MDIO Controller

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Elaboratable, Module, Signal, Array


class MDIO(Elaboratable):
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

        # Parameters
        self.clk_div = clk_div

        # Pins
        self.mdio = mdio
        self.mdc = mdc

    def elaborate(self, platform):

        m = Module()

        # Create divided clock for MDC
        mdc_int = Signal()
        mdc_rise = Signal()
        mdc_fall = Signal()
        mdc_divider = Signal(max=self.clk_div)
        with m.If(mdc_divider == 0):
            m.d.sync += [
                mdc_divider.eq(self.clk_div - 1),
                mdc_int.eq(0),
                mdc_fall.eq(1),
                mdc_rise.eq(0),
            ]

        with m.Elif(mdc_divider == self.clk_div//2):
            m.d.sync += [
                mdc_divider.eq(mdc_divider - 1),
                mdc_int.eq(1),
                mdc_fall.eq(0),
                mdc_rise.eq(1),
            ]

        with m.Else():
            m.d.sync += [
                mdc_divider.eq(mdc_divider - 1),
                mdc_fall.eq(0),
                mdc_rise.eq(0),
            ]

        # Latches for inputs
        _phy_addr = Signal.like(self.phy_addr)
        _reg_addr = Signal.like(self.reg_addr)
        _rw = Signal.like(self.rw)
        _write_data = Signal.like(self.write_data)

        # MDIO FSM
        bit_counter = Signal(6)
        with m.FSM() as fsm:
            m.d.comb += self.busy.eq(~fsm.ongoing("IDLE"))

            # Idle state
            # Constantly register input data and wait for START signal
            with m.State("IDLE"):
                m.d.comb += [
                    self.mdc.eq(0),
                    self.mdio.oe.eq(0),
                ]

                # Latch input signals while in idle
                m.d.sync += [
                    _phy_addr.eq(self.phy_addr),
                    _reg_addr.eq(self.reg_addr),
                    _rw.eq(self.rw),
                    _write_data.eq(self.write_data),
                ]

                with m.If(self.start):
                    m.next = "SYNC"

            # Synchronise to MDC. Enter this state at any time.
            # Will transition to PRE_32 immediately after the next
            # falling edge on MDC.
            with m.State("SYNC"):
                m.d.comb += [
                    self.mdc.eq(0),
                    self.mdio.oe.eq(0),
                ]

                with m.If(mdc_fall):
                    m.d.sync += bit_counter.eq(32)
                    m.next = "PRE_32"

            # PRE_32
            # Preamble field: 32 bits of 1
            with m.State("PRE_32"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),

                    # Output all 1s
                    self.mdio.o.eq(1),
                ]

                # Count falling edges of MDC,
                # transition to ST after 32 MDC clocks
                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(2)
                        m.next = "ST"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # ST
            # Start field: always 01
            with m.State("ST"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                    self.mdio.o.eq(bit_counter[0]),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(2)
                        m.next = "OP"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # OP
            # Opcode field: read=10, write=01
            with m.State("OP"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                ]
                with m.If(_rw):
                    m.d.comb += self.mdio.o.eq(bit_counter[0])
                with m.Else():
                    m.d.comb += self.mdio.o.eq(~bit_counter[0])

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(5)
                        m.next = "PA5"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # PA5
            # PHY address field, 5 bits
            with m.State("PA5"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                    self.mdio.o.eq(Array(_phy_addr)[bit_counter - 1]),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(5)
                        m.next = "RA5"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # RA5
            # Register address field, 5 bits
            with m.State("RA5"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                    self.mdio.o.eq(Array(_reg_addr)[bit_counter - 1]),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        with m.If(_rw):
                            m.d.sync += bit_counter.eq(2)
                            m.next = "TA_W"
                        with m.Else():
                            m.d.sync += bit_counter.eq(1)
                            m.next = "TA_R"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # TA
            # Turnaround, 1 bits, OE released for read operations
            with m.State("TA_R"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(0),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(16)
                        m.next = "D16_R"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # TA
            # Turnaround, 2 bits, driven to 10 for write operations
            with m.State("TA_W"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                    self.mdio.o.eq(~bit_counter[0]),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 1):
                        m.d.sync += bit_counter.eq(16)
                        m.next = "D16_W"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # D16
            # Data field, read operation
            with m.State("D16_R"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(0),
                ]

                with m.If(mdc_fall):
                    bit = Array(self.read_data)[bit_counter - 1]
                    m.d.sync += bit.eq(self.mdio.i)
                    with m.If(bit_counter == 1):
                        m.next = "READ_LAST_CLOCK"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

            # Because we sample MDIO on the falling edge, the final clock
            # pulse is not used for data, but should probably be emitted to
            # stop things getting confused.
            with m.State("READ_LAST_CLOCK"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(0),
                ]

                with m.If(mdc_fall):
                    m.next = "IDLE"

            # D16
            # Data field, write operation
            with m.State("D16_W"):
                m.d.comb += [
                    self.mdc.eq(mdc_int),
                    self.mdio.oe.eq(1),
                    self.mdio.o.eq(Array(_write_data)[bit_counter - 1]),
                ]

                with m.If(mdc_fall):
                    with m.If(bit_counter == 0):
                        m.next = "IDLE"
                    with m.Else():
                        m.d.sync += bit_counter.eq(bit_counter - 1)

        return m


def test_mdio_read():
    import random
    from nmigen.lib.io import Pin
    from nmigen.back import pysim

    mdc = Signal()
    mdio_pin = Pin(1, 'io')
    mdio = MDIO(20, mdio_pin, mdc)

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
                    obits.append((yield mdio.mdio.o))
                    oebits.append((yield mdio.mdio.oe))
                    if mdio_clk >= 48:
                        yield (mdio.mdio.i.eq(ibits[mdio_clk - 48]))
                    if mdio_clk == 63:
                        break
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
            expected = [1]*46 + [0]*17
            assert oebits == expected

            # Check we read the correct value in the end
            expected = int("".join(str(x) for x in ibits), 2)
            assert read_data == expected
            assert not was_busy

    vcdf = open("mdio_read.vcd", "w")
    with pysim.Simulator(mdio, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()


def test_mdio_write():
    import random
    from nmigen.lib.io import Pin
    from nmigen.back import pysim

    mdc = Signal()
    mdio_pin = Pin(1, 'io')
    mdio = MDIO(20, mdio_pin, mdc)

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
                    obits.append((yield mdio.mdio.o))
                    oebits.append((yield mdio.mdio.oe))
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

    vcdf = open("mdio_write.vcd", "w")
    with pysim.Simulator(mdio, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()
