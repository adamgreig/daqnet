"""
Ethernet CRC32 Module

Copyright 2018 Adam Greig
"""

from migen import Module, Signal, If, Memory, FSM, NextState, NextValue


class CRC32(Module):
    """
    Ethernet CRC32

    Processes one byte of data every *two* clock cycles.

    Inputs:
        * `reset`: Re-initialises CRC to start state while high
        * `data`: 8-bit input data
        * `data_valid`: Pulses high when new data is ready at `data`.
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

        ###

        crc = Signal(32)

        table = Memory(32, 256, make_crc32_table())
        table_port = table.get_port()
        self.specials += [table, table_port]

        self.comb += [
            self.crc_out.eq(crc ^ 0xFFFFFFFF),
            self.crc_match.eq(crc == 0xDEBB20E3),
            table_port.adr.eq(crc ^ self.data),
        ]

        self.submodules.fsm = FSM(reset_state="RESET")

        self.fsm.act(
            "RESET",
            NextValue(crc, 0xFFFFFFFF),
            NextState("IDLE"),
        )

        self.fsm.act(
            "IDLE",
            If(self.reset == 1, NextState("RESET")),
            If(self.data_valid, NextState("BUSY"))
        )

        self.fsm.act(
            "BUSY",
            If(self.reset == 1, NextState("RESET")),
            NextValue(crc, table_port.dat_r ^ (crc >> 8)),
            NextState("IDLE"),
        )


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
    from migen.sim import run_simulation
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

    run_simulation(crc, testbench(), vcd_name="crc32.vcd")


def test_crc32_match():
    from migen.sim import run_simulation
    crc = CRC32()

    frame = [
        0x08, 0x00, 0x20, 0x0A, 0x70, 0x66, 0x08, 0x00, 0x20, 0x0A, 0xAC, 0x96,
        0x08, 0x00, 0x45, 0x00, 0x00, 0x28, 0xA6, 0xF5, 0x00, 0x00, 0x1A, 0x06,
        0x75, 0x94, 0xC0, 0x5D, 0x02, 0x01, 0x84, 0xE3, 0x3D, 0x05, 0x00, 0x15,
        0x0F, 0x87, 0x9C, 0xCB, 0x7E, 0x01, 0x27, 0xE3, 0xEA, 0x01, 0x50, 0x12,
        0x10, 0x00, 0xDF, 0x3D, 0x00, 0x00, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x5A, 0x05, 0xDE, 0xFA
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
        # out = yield (crc.crc_out)
        # assert out == 0xFADE055A
        match = yield (crc.crc_match)
        assert match == 1

    run_simulation(crc, testbench(), vcd_name="crc32_match.vcd")


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
