"""
Ethernet CRC32 Module

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Module, Signal, Memory


class CRC32:
    """
    Ethernet CRC32

    Processes one byte of data every two clock cycles.

    Inputs:
        * `reset`: Re-initialises CRC to start state while high
        * `data`: 8-bit input data
        * `data_valid`: Pulsed high when new data is ready at `data`.
                        Requires one clock to process between new data.

    Outputs:
        * `crc_out`: complement of current 32-bit CRC value
        * `crc_match`: high if crc residual is currently 0xC704DD7B

    When using for transmission, note that `crc_out` must be sent in little
    endian (i.e. if `crc_out` is 0xAABBCCDD then transmit 0xDD 0xCC 0xBB 0xAA).
    """
    def __init__(self):
        # Inputs
        self.reset = Signal()
        self.data = Signal(8)
        self.data_valid = Signal()

        # Outputs
        self.crc_out = Signal(32)
        self.crc_match = Signal()

    def elaborate(self, platform):

        m = Module()
        crc = Signal(32)

        self.crctable = Memory(32, 256, make_crc32_table())
        table_port = self.crctable.read_port()
        m.submodules += table_port

        m.d.comb += [
            self.crc_out.eq(crc ^ 0xFFFFFFFF),
            self.crc_match.eq(crc == 0xDEBB20E3),
            table_port.addr.eq(crc ^ self.data),
        ]

        with m.FSM():
            with m.State("RESET"):
                m.d.sync += crc.eq(0xFFFFFFFF)
                m.next = "IDLE"

            with m.State("IDLE"):
                with m.If(self.reset):
                    m.next = "RESET"
                with m.Elif(self.data_valid):
                    m.next = "BUSY"

            with m.State("BUSY"):
                with m.If(self.reset):
                    m.next = "RESET"
                m.d.sync += crc.eq(table_port.data ^ (crc >> 8))
                m.next = "IDLE"

        return m


def make_crc32_table():
    poly = 0x04C11DB7
    table = []
    for i in range(256):
        ir = int(f"{i:08b}"[::-1], 2)
        r = ir << 24
        for _ in range(8):
            if r & (1 << 31):
                r = ((r << 1) & 0xFFFFFFFF) ^ poly
            else:
                r = (r << 1) & 0xFFFFFFFF
        r = int(f"{r:032b}"[::-1], 2)
        table.append(r)
    return table


def test_crc32():
    from nmigen.back import pysim
    crc = CRC32()

    def testbench():
        yield
        yield
        for byte in [ord(x) for x in "123456789"]:
            yield (crc.data.eq(byte))
            yield (crc.data_valid.eq(1))
            yield
            yield (crc.data_valid.eq(0))
            yield (crc.data.eq(0))
            yield
        yield
        out = yield (crc.crc_out)
        assert out == 0xCBF43926

    frag = crc.elaborate(None)
    vcdf = open("crc32.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()


def test_crc32_match():
    from nmigen.back import pysim
    crc = CRC32()

    frame = [
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xF0, 0xDE, 0xF1, 0x38, 0x89, 0x40,
        0x08, 0x00, 0x45, 0x00, 0x00, 0x54, 0x00, 0x00, 0x40, 0x00, 0x40, 0x01,
        0xB6, 0xD0, 0xC0, 0xA8, 0x01, 0x88, 0xC0, 0xA8, 0x01, 0x00, 0x08, 0x00,
        0x0D, 0xD9, 0x12, 0x1E, 0x00, 0x07, 0x3B, 0x3E, 0x0C, 0x5C, 0x00, 0x00,
        0x00, 0x00, 0x13, 0x03, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x57,
        0x6F, 0x72, 0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F,
        0x72, 0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72,
        0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C,
        0x64, 0x48, 0x52, 0x32, 0x1F, 0x9E
    ]

    def testbench():
        yield
        yield
        for byte in frame:
            yield (crc.data.eq(byte))
            yield (crc.data_valid.eq(1))
            yield
            yield (crc.data_valid.eq(0))
            yield (crc.data.eq(0))
            yield
        yield
        match = yield (crc.crc_match)
        assert match == 1

    frag = crc.elaborate(None)
    vcdf = open("crc32_match.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()


def test_crc32_py():
    check = 0xCBF43926

    data = [ord(x) for x in "123456789"]

    table = make_crc32_table()

    # init
    crc = 0xFFFFFFFF

    # process
    for byte in data:
        crc = table[(crc & 0xFF) ^ byte] ^ (crc >> 8)

    # xorout
    crc ^= 0xFFFFFFFF

    assert hex(crc) == hex(check)
