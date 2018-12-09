"""
Ethernet RMII Interface

Copyright 2018 Adam Greig
"""

from functools import reduce
from operator import and_

from migen import Module, Signal, If, Cat, FSM, NextValue, NextState
from .crc import CRC32


class RMIIRx(Module):
    """
    RMII receive module

    Receives incoming packets and saves them to a memory. Validates incoming
    frame check sequence and only asserts `rx_valid` when an entire valid
    packet has been saved to the port.

    This module must be run in the RMII ref_clk domain, and the memory port
    and inputs and outputs must be in the same clock domain.

    Parameters:
        * `mac_addr`: 6-byte MAC address (list of ints)

    Ports:
        * `write_port`: a write-capable memory port, 8 bits wide by 2048,
                        running in the RMII ref_clk domain

    Pins:
        * `crs_dv`: Data valid, input
        * `rxd0`: RX data 0, input
        * `rxd1`: RX data 1, input

    Inputs:
        * `rx_ack`: assert when packet has been read from memory and reception
                    can restart

    Outputs:
        * `rx_valid`: asserted when a valid packet is in memory, until `rx_ack`
                      is asserted
        * `rx_len`: 11-bit wide length of received packet, valid while
                    packet_rx is high
    """
    def __init__(self, mac_addr, write_port, crs_dv, rxd0, rxd1):
        # Inputs
        self.rx_ack = Signal()

        # Outputs
        self.rx_valid = Signal()
        self.rx_len = Signal(11)

        ###

        self.submodules.rxbyte = RMIIRxByte(crs_dv, rxd0, rxd1)
        self.submodules.crc = CRC32()
        self.submodules.mac_match = MACAddressMatch(mac_addr)
        self.submodules.fsm = FSM(reset_state="IDLE")

        self.comb += [
            write_port.adr.eq(self.rx_len),
            write_port.dat_w.eq(self.rxbyte.data),
            write_port.we.eq(self.rxbyte.data_valid),
            self.crc.data.eq(self.rxbyte.data),
            self.crc.data_valid.eq(self.rxbyte.data_valid),
            self.crc.reset.eq(self.fsm.ongoing("IDLE")),
            self.mac_match.data.eq(self.rxbyte.data),
            self.mac_match.data_valid.eq(self.rxbyte.data_valid),
            self.mac_match.reset.eq(self.fsm.ongoing("IDLE")),
            self.rx_valid.eq(self.fsm.ongoing("ACK")),
        ]

        # Idle until we see data valid
        self.fsm.act(
            "IDLE",
            NextValue(self.rx_len, 0),
            If(
                self.rxbyte.dv,
                NextState("DATA")
            ),
        )

        # Save incoming data to memory
        self.fsm.act(
            "DATA",
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
            If(
                self.crc.crc_match & self.mac_match.mac_match,
                NextState("ACK"),
            ).Else(
                NextState("IDLE"),
            ),
        )

        self.fsm.act(
            "ACK",
            If(
                self.rx_ack,
                NextState("IDLE"),
            ),
        )


class MACAddressMatch(Module):
    """
    MAC Address Matcher

    Parameters:
        * `mac_addr`: 6-byte MAC address (list of ints)

    Inputs:
        * `reset`: Restart address matching
        * `data`: 8-bit input data
        * `data_valid`: Pulsed high when new data is ready at `data`.

    Outputs:
        * `mac_match`: High if destination MAC address matches or is broadcast.
                       Remains high until `reset` is asserted.
    """
    def __init__(self, mac_addr):
        # Inputs
        self.reset = Signal()
        self.data = Signal(8)
        self.data_valid = Signal()

        # Outputs
        self.mac_match = Signal()

        ###

        mac = [Signal(8) for _ in range(6)]

        self.sync += [
            self.mac_match.eq(
                reduce(and_, [mac[idx] == mac_addr[idx] for idx in range(6)])
                |
                reduce(and_, [mac[idx] == 0xFF for idx in range(6)])
            ),
        ]

        self.submodules.fsm = FSM(reset_state="RESET")

        self.fsm.act(
            "RESET",
            NextValue(mac[0], 0),
            NextValue(mac[1], 0),
            NextValue(mac[2], 0),
            NextValue(mac[3], 0),
            NextValue(mac[4], 0),
            NextValue(mac[5], 0),
            If(~self.reset, NextState("BYTE0")),
        )

        for idx in range(6):
            next_state = f"BYTE{idx+1}" if idx < 5 else "DONE"
            self.fsm.act(
                f"BYTE{idx}",
                NextValue(mac[idx], self.data),
                If(
                    self.reset == 1,
                    NextState("RESET")
                ).Elif(
                    self.data_valid,
                    NextState(next_state),
                )
            )

        self.fsm.act(
            "DONE",
            If(
                self.reset == 1,
                NextState("RESET"),
            )
        )


class RMIIRxByte(Module):
    """
    RMII Receive Byte De-muxer

    Handles receiving a byte dibit-by-dibit.

    Clock this submodule off the RMII ref_clk signal.
    No clock domain crossing is implemented in this module;
    only interface to it on the RMII ref_clk domain.

    Pins:
        * `crs_dv`: Data valid, input
        * `rxd0`: RX data 0, input
        * `rxd1`: RX data 1, input

    Outputs:
        * `data`: 8-bit wide output data
        * `data_valid`: Asserted for one cycle when `data` is valid
        * `dv`: RMII Data valid recovered signal
        * `crs`: RMII Carrier sense recovered signal
    """
    def __init__(self, crs_dv, rxd0, rxd1):
        # Outputs
        self.data = Signal(8)
        self.data_valid = Signal()
        self.dv = Signal()
        self.crs = Signal()

        ###

        # Sample RMII signals on rising edge of ref_clk
        crs_dv_reg = Signal()
        rxd_reg = Signal(2)
        self.sync += [
            crs_dv_reg.eq(crs_dv),
            rxd_reg.eq(Cat(rxd0, rxd1)),
        ]

        # Run byte-recovery FSM on RMII clock domain
        self.submodules.fsm = FSM(reset_state="IDLE")

        self.fsm.act(
            "IDLE",
            NextValue(self.crs, 0),
            NextValue(self.dv, 0),
            NextValue(self.data_valid, 0),
            If(
                crs_dv_reg & (rxd_reg == 0b01),
                NextState("PREAMBLE_SFD"),
            )
        )

        self.fsm.act(
            "PREAMBLE_SFD",
            NextValue(self.crs, 1),
            NextValue(self.dv, 1),
            NextValue(self.data_valid, 0),
            If(
                rxd_reg == 0b11,
                NextState("NIBBLE1"),
            ).Elif(
                rxd_reg != 0b01,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE1",
            NextValue(self.data[0:2], rxd_reg),
            NextValue(self.data_valid, 0),
            If(
                self.dv,
                NextValue(self.crs, crs_dv_reg),
                NextState("NIBBLE2"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE2",
            NextValue(self.data[2:4], rxd_reg),
            NextValue(self.data_valid, 0),
            If(
                self.dv,
                NextValue(self.dv, crs_dv_reg),
                NextState("NIBBLE3"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE3",
            NextValue(self.data[4:6], rxd_reg),
            NextValue(self.data_valid, 0),
            If(
                self.dv,
                NextValue(self.crs, crs_dv_reg),
                NextState("NIBBLE4"),
            ).Elif(
                ~self.dv,
                NextState("IDLE"),
            )
        )

        self.fsm.act(
            "NIBBLE4",
            NextValue(self.data[6:8], rxd_reg),
            If(
                self.dv,
                NextValue(self.dv, crs_dv_reg),
                NextValue(self.data_valid, 1),
                NextState("NIBBLE1"),
            ).Elif(
                ~self.dv,
                NextValue(self.data_valid, 0),
                NextState("IDLE"),
            )
        )


def test_rmii_rx():
    import random
    from migen.sim import run_simulation
    from migen import Memory

    crs_dv = Signal()
    rxd0 = Signal()
    rxd1 = Signal()

    mem = Memory(8, 128)
    mem_port = mem.get_port(write_capable=True)
    mac_addr = [random.randint(0, 255) for _ in range(6)]

    rmii_rx = RMIIRx(mac_addr, mem_port, crs_dv, rxd0, rxd1)
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
        # SFD
        yield (rxd0.eq(1))
        yield (rxd1.eq(1))
        yield
        # Data
        for txbyte in txbytes:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
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

        assert (yield rmii_rx.rx_valid) == 0

    run_simulation(rmii_rx, testbench(),
                   clocks={"sys": (20, 0)}, vcd_name="rmii_rx.vcd")


def test_rmii_rx_byte():
    import random
    from migen.sim import run_simulation

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

        # SFD
        yield (rxd0.eq(1))
        yield (rxd1.eq(1))
        yield

        # Data (except last two bytes), with CRS=1 DV=1
        for txbyte in txbytes[:-2]:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))

        # Data (last two bytes), with CRS=0 DV=1
        for txbyte in txbytes[-2:]:
            for dibit in range(0, 8, 2):
                yield (rxd0.eq((txbyte >> (dibit + 0)) & 1))
                yield (rxd1.eq((txbyte >> (dibit + 1)) & 1))
                if dibit in (0, 4):
                    # CRS=0
                    yield (crs_dv.eq(0))
                else:
                    # DV=1
                    yield (crs_dv.eq(1))
                yield
                if (yield rmii_rx_byte.data_valid):
                    rxbytes.append((yield rmii_rx_byte.data))

        yield (crs_dv.eq(0))

        for _ in range(10):
            yield
            if (yield rmii_rx_byte.data_valid):
                rxbytes.append((yield rmii_rx_byte.data))

        assert rxbytes == txbytes

    for phase in range(20):
        rmii_rx_byte = RMIIRxByte(crs_dv, rxd0, rxd1)
        run_simulation(rmii_rx_byte, testbench(rmii_rx_byte),
                       clocks={"sys": (20, 0)}, vcd_name="rmii_rx_byte.vcd")


def test_mac_address_match():
    import random
    from migen.sim import run_simulation

    data = Signal(8)
    data_valid = Signal()
    reset = Signal()

    mac_address = [random.randint(0, 255) for _ in range(6)]
    mac_address = [0x01, 0x23, 0x45, 0x67, 0x89, 0xAB]
    mac_matcher = MACAddressMatch(mac_address)

    mac_matcher.comb += [
        mac_matcher.data.eq(data),
        mac_matcher.data_valid.eq(data_valid),
        mac_matcher.reset.eq(reset),
    ]

    def testbench():
        yield (reset.eq(1))
        for _ in range(10):
            yield
        yield (reset.eq(0))
        yield

        # Check it matches its own MAC address
        for byte in mac_address:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 1

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

        # Check it matches broadcast
        for byte in [0xFF]*6:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 1

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

        # Check it doesn't match some other MAC address
        for byte in mac_address[::-1]:
            yield (data.eq(byte))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        for idx in range(100):
            yield (data.eq(idx))
            yield (data_valid.eq(1))
            yield
            yield (data_valid.eq(0))
            yield

        assert (yield mac_matcher.mac_match) == 0

        yield (reset.eq(1))
        yield
        yield (reset.eq(0))
        yield

    run_simulation(mac_matcher, testbench(), vcd_name="mac_matcher.vcd")
