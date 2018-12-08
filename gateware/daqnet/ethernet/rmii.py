"""
Ethernet RMII Interface

Copyright 2018 Adam Greig
"""

from migen import (Module, Signal, If, Cat, FSM, NextValue, NextState,
                   ClockDomain)
from .crc import CRC32


class RMIIRx(Module):
    """
    RMII receive module

    Receives incoming packets and saves them to a memory. Validates incoming
    frame check sequence and only asserts `rx_valid` when an entire valid
    packet has been saved to the port.

    Ports:
        * `write_port`: a write-capable memory port, 8 bits wide by 2048

    Pins:
        * `ref_clk`: RMII reference clock, input
        * `crs_dv`: Data valid, input
        * `rxd0`: RX data 0, input
        * `rxd1`: RX data 1, input

    Inputs:
        * `rx_ack`: acknowledge packet recepton and restart listening

    Outputs:
        * `rx_valid`: pulses high when a valid packet has been saved to memory
        * `rx_len`: 11-bit wide length of received packet, valid when
          packet_rx is high
    """
    def __init__(self, write_port, ref_clk, crs_dv, rxd0, rxd1, sim=False):
        # Inputs
        self.rx_ack = Signal()

        # Outputs
        self.rx_valid = Signal()
        self.rx_len = Signal(11)

        ###

        self.submodules.rxbyte = RMIIRxByte(ref_clk, crs_dv, rxd0, rxd1, sim)
        self.submodules.crc = CRC32()

        self.comb += [
            write_port.adr.eq(self.rx_len),
            write_port.dat_w.eq(self.rxbyte.data),
            self.crc.data.eq(self.rxbyte.data),
        ]

        self.submodules.fsm = FSM(reset_state="IDLE")

        # Idle until we see carrier sense
        self.fsm.act(
            "IDLE",
            write_port.we.eq(0),
            self.crc.data_valid.eq(0),
            self.rx_valid.eq(0),
            NextValue(self.rx_len, 0),
            If(
                self.rxbyte.dv,
                NextState("DATA")
            ),
        )

        # Save incoming data to memory
        self.fsm.act(
            "DATA",
            self.crc.data_valid.eq(self.rxbyte.data_valid),
            write_port.we.eq(self.rxbyte.data_valid),
            self.rx_valid.eq(0),
            If(
                self.rxbyte.data_valid,
                NextValue(self.rx_len, self.rx_len + 1)
            ).Elif(
                ~self.rxbyte.dv,
                NextState("EOF")
            ),
        )

        self.fsm.act(
            "EOF",
            write_port.we.eq(0),
            self.rx_valid.eq(0),
            self.crc.data_valid.eq(0),
            If(
                self.crc.crc_match,
                NextState("ACK"),
            ).Else(
                NextState("ACK"),
            ),
        )

        self.fsm.act(
            "ACK",
            self.rx_valid.eq(1),
            If(
                self.rx_ack,
                NextState("IDLE"),
            ),
        )


class RMIIRxByte(Module):
    """
    RMII Receive Byte module

    Handles receiving a byte dibit-by-dibit.

    Pins:
        * `ref_clk`: RMII reference clock, input
        * `crs_dv`: Data valid, input
        * `rxd0`: RX data 0, input
        * `rxd1`: RX data 1, input

    Outputs:
        * `data`: 8-bit wide output data
        * `data_valid`: pulsed high when `data` is a valid byte
        * `crs`: RMII Carrier Sense recovered signal
        * `dv`: RMII Data valid recovered signal
    """
    def __init__(self, ref_clk, crs_dv, rxd0, rxd1, sim=False):
        # Outputs
        self.data = Signal(8)
        self.data_valid = Signal()
        self.crs = Signal()
        self.dv = Signal()

        ###

        self.clock_domains.rmii = ClockDomain("rmii")

        if sim:
            self.comb += ref_clk.eq(self.rmii.clk)
        else:
            self.comb += self.rmii.clk.eq(ref_clk)

        # Sample RMII signals on rising edge of ref_clk
        crs_dv_ext = Signal()
        rxd_ext = Signal(2)
        self.sync.rmii += [
            crs_dv_ext.eq(crs_dv),
            rxd_ext.eq(Cat(rxd0, rxd1)),
        ]

        # Synchronise RMII signals to system clock domain
        ref_clk_latch = Signal()
        ref_clk_int = Signal()
        crs_dv_latch = Signal()
        crs_dv_int = Signal()
        rxd_latch = Signal(2)
        rxd_int = Signal(2)
        self.sync += [
            ref_clk_latch.eq(ref_clk),
            ref_clk_int.eq(ref_clk_latch),
            crs_dv_latch.eq(crs_dv_ext),
            crs_dv_int.eq(crs_dv_latch),
            rxd_latch.eq(rxd_ext),
            rxd_int.eq(rxd_latch),
        ]

        self.crs_dv_int = Signal()
        self.comb += self.crs_dv_int.eq(crs_dv_int)

        # Detect rising edge of synchronised ref_clk
        clk_last = Signal()
        clk_rise = Signal()
        self.sync += clk_last.eq(ref_clk_int)
        self.comb += clk_rise.eq(~clk_last & ref_clk_int)

        self.submodules.fsm = FSM(reset_state="IDLE")

        self.fsm.act(
            "IDLE",
            self.data_valid.eq(0),
            NextValue(self.crs, 0),
            NextValue(self.dv, 0),
            If(
                clk_rise & crs_dv_int & (rxd_int == 0b01),
                NextState("PREAMBLE_SFD"),
            )
        )

        self.fsm.act(
            "PREAMBLE_SFD",
            self.data_valid.eq(0),
            NextValue(self.crs, 1),
            NextValue(self.dv, 1),
            If(
                rxd_int == 0b11,
                NextState("NIBBLE1"),
            ).Elif(
                rxd_int != 0b01,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE1",
            self.data_valid.eq(0),
            NextValue(self.data[0:2], rxd_int),
            If(
                clk_rise & self.dv,
                NextValue(self.crs, crs_dv_int),
                NextState("NIBBLE2"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE2",
            self.data_valid.eq(0),
            NextValue(self.data[2:4], rxd_int),
            If(
                clk_rise & self.dv,
                NextValue(self.dv, crs_dv_int),
                NextState("NIBBLE3"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE3",
            self.data_valid.eq(0),
            NextValue(self.data[4:6], rxd_int),
            If(
                clk_rise & self.dv,
                NextValue(self.crs, crs_dv_int),
                NextState("NIBBLE4"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE4",
            self.data_valid.eq(0),
            NextValue(self.data[6:8], rxd_int),
            If(
                clk_rise & self.dv,
                NextValue(self.dv, crs_dv_int),
                NextState("EOB"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "EOB",
            self.data_valid.eq(1),
            NextState("NIBBLE1"),
        )


def test_rmii_rx():
    import random
    from migen.sim import run_simulation
    from migen import Memory

    ref_clk = Signal()
    crs_dv = Signal()
    rxd0 = Signal()
    rxd1 = Signal()

    mem = Memory(8, 128)
    mem_port = mem.get_port(write_capable=True)

    rmii_rx = RMIIRx(mem_port, ref_clk, crs_dv, rxd0, rxd1, sim=True)

    rmii_rx.specials += [mem, mem_port]

    def testbench():
        for _ in range(10):
            yield

        txbytes = [
            0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xF0, 0xDE, 0xF1, 0x38, 0x89,
            0x40, 0x08, 0x00, 0x45, 0x00, 0x00, 0x54, 0x00, 0x00, 0x40, 0x00,
            0x40, 0x01, 0xB6, 0xD0, 0xC0, 0xA8, 0x01, 0x88, 0xC0, 0xA8, 0x01,
            0x00, 0x08, 0x00, 0x0D, 0xD9, 0x12, 0x1E, 0x00, 0x07, 0x3B, 0x3E,
            0x0C, 0x5C, 0x00, 0x00, 0x00, 0x00, 0x13, 0x03, 0x0F, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x48, 0x65,
            0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x48, 0x65,
            0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x48, 0x65,
            0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64, 0x48, 0x52,
            0x32, 0x1F, 0x9E
        ]

        yield (crs_dv.eq(1))
        # Preamble
        for _ in range(random.randint(10, 40)):
            yield (rxd0.eq(1))
            yield (rxd1.eq(0))
            yield
            yield
        # SFD
        yield (rxd0.eq(1))
        yield (rxd1.eq(1))
        yield
        yield
        # Data
        for txbyte in txbytes:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
                yield
                yield
        yield (crs_dv.eq(0))

        for _ in range(10):
            yield

        assert (yield rmii_rx.rx_valid)
        assert (yield rmii_rx.rx_len) == 102

        mem_contents = []
        for idx in range(102):
            mem_contents.append((yield mem[idx]))
        assert mem_contents == txbytes

        yield (rmii_rx.rx_ack.eq(1))

        for _ in range(10):
            yield

    run_simulation(rmii_rx, testbench(),
                   clocks={"sys": (10, 0), "rmii": (20, 3)},
                   vcd_name="rmii_rx.vcd")


def test_rmii_rx_byte():
    import random
    from migen.sim import run_simulation

    ref_clk = Signal()
    crs_dv = Signal()
    rxd0 = Signal()
    rxd1 = Signal()

    def testbench(rmii_rx_byte):
        for _ in range(10):
            yield

        txbytes = [random.randint(0, 255) for _ in range(8)]
        rxbytes = []
        yield (crs_dv.eq(1))
        # Preamble
        for _ in range(random.randint(10, 40)):
            yield (rxd0.eq(1))
            yield (rxd1.eq(0))
            yield
            yield
        # SFD
        yield (rxd0.eq(1))
        yield (rxd1.eq(1))
        yield
        yield
        # Data (except last two bytes)
        for txbyte in txbytes[:-2]:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))
        # Data (last two bytes)
        for txbyte in txbytes[-2:]:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
                if dibit in (0, 4):
                    yield (crs_dv.eq(0))
                else:
                    yield (crs_dv.eq(1))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))
        yield (crs_dv.eq(0))
        for _ in range(10):
            yield
            if (yield rmii_rx_byte.data_valid):
                rxbytes.append((yield rmii_rx_byte.data))

        assert rxbytes == txbytes

    for phase in range(0, 20):
        rmii_rx_byte = RMIIRxByte(ref_clk, crs_dv, rxd0, rxd1, sim=True)
        run_simulation(rmii_rx_byte, testbench(rmii_rx_byte),
                       clocks={"sys": (10, 0), "rmii": (20, phase)},
                       vcd_name="rmii_rx_byte.vcd")
