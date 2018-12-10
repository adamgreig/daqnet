"""
Ethernet RMII Interface

Copyright 2018 Adam Greig
"""

from migen import Module, Signal, If, Cat, FSM, NextValue, NextState
from .crc import CRC32
from .mac_address_match import MACAddressMatch


class RMIIRx(Module):
    """
    RMII receive module

    Receives incoming packets and saves them to a memory. Validates incoming
    frame check sequence and only asserts `rx_valid` when an entire valid
    packet has been saved to the port.

    This module must be run in the RMII ref_clk domain, and the memory port
    and inputs and outputs must also be in that clock domain.

    Parameters:
        * `mac_addr`: 6-byte MAC address (list of ints)

    Ports:
        * `write_port`: a write-capable memory port, 8 bits wide by 2048,
                        running in the RMII ref_clk domain

    Pins:
        * `crs_dv`: RMII carrier sense/data valid
        * `rxd0`: RMII receive data 0
        * `rxd1`: RMII receive data 1

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


class RMIIRxByte(Module):
    """
    RMII Receive Byte De-muxer

    Handles receiving a byte dibit-by-dibit.

    This submodule must be in the RMII ref_clk clock domain,
    and its outputs are likewise in that domain.

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


class RMIITx(Module):
    """
    RMII transmit module

    Transmits outgoing packets from a memory. Adds preamble, start of frame
    delimiter, and frame check sequence (CRC32) automatically.

    This module must be run in the RMII ref_clk domain, and the memory port
    and inputs and outputs must also be in that clock domain.

    Ports:
        * `read_port`: a read memory port, 8 bits wide by 2048,
          running in the RMII ref_clk domain

    Pins:
        * `txen`: RMII transmit enable
        * `txd0`: RMII transmit data 0
        * `txd1`: RMII transmit data 1

    Inputs:
        * `tx_start`: Assert to begin transmission of a packet
        * `tx_len`: 11-bit wide length of packet to transmit, read
          when `tx_start` is asserted.

    Outputs:
        * `tx_ready`: Asserted while ready to transmit a new packet
    """
    def __init__(self, read_port, txen, txd0, txd1):
        # Inputs
        self.tx_start = Signal()
        self.tx_len = Signal(11)

        # Outputs
        self.tx_ready = Signal()

        ###

        # Transmit byte counter
        tx_idx = Signal(11)
        # Transmit length latch
        tx_len = Signal(11)

        self.submodules.txbyte = RMIITxByte(txen, txd0, txd1)
        self.submodules.crc = CRC32()
        self.submodules.fsm = FSM(reset_state="IDLE")

        self.comb += [
            read_port.adr.eq(tx_idx),
            self.crc.data.eq(read_port.dat_r),
            self.crc.reset.eq(self.fsm.ongoing("IDLE")),
            self.crc.data_valid.eq(
                self.fsm.ongoing("DATA") & self.txbyte.ready),
            self.tx_ready.eq(self.fsm.ongoing("IDLE")),
            self.txbyte.data_valid.eq(
                ~(self.fsm.ongoing("IDLE") | self.fsm.ongoing("IPG"))),
        ]

        self.fsm.act(
            "IDLE",
            self.txbyte.data.eq(0),
            NextValue(tx_idx, 0),
            NextValue(tx_len, self.tx_len),
            If(self.tx_start, NextState("PREAMBLE"))
        )

        self.fsm.act(
            "PREAMBLE",
            self.txbyte.data.eq(0x55),
            If(
                tx_idx == 7,
                NextState("SFD"),
            ).Elif(
                self.txbyte.ready,
                NextValue(tx_idx, tx_idx + 1),
            )
        )

        self.fsm.act(
            "SFD",
            self.txbyte.data.eq(0x5D),
            If(
                self.txbyte.ready,
                NextValue(tx_idx, 0),
                NextState("DATA"),
            )
        )

        self.fsm.act(
            "DATA",
            self.txbyte.data.eq(read_port.dat_r),
            If(
                tx_idx == tx_len,
                NextState("FCS1"),
            ).Elif(
                self.txbyte.ready,
                NextValue(tx_idx, tx_idx + 1),
            )
        )

        self.fsm.act(
            "FCS1",
            self.txbyte.data.eq(self.crc.crc_out[0:8]),
            If(
                self.txbyte.ready,
                NextState("FCS2"),
            )
        )

        self.fsm.act(
            "FCS2",
            self.txbyte.data.eq(self.crc.crc_out[8:16]),
            If(
                self.txbyte.ready,
                NextState("FCS3"),
            )
        )

        self.fsm.act(
            "FCS3",
            self.txbyte.data.eq(self.crc.crc_out[16:24]),
            If(
                self.txbyte.ready,
                NextState("FCS4"),
            )
        )

        self.fsm.act(
            "FCS4",
            self.txbyte.data.eq(self.crc.crc_out[24:32]),
            If(
                self.txbyte.ready,
                NextValue(tx_idx, 0),
                NextState("IPG"),
            )
        )

        self.fsm.act(
            "IPG",
            If(
                tx_idx == 48,
                NextState("IDLE"),
            ).Else(
                NextValue(tx_idx, tx_idx + 1)
            )
        )


class RMIITxByte(Module):
    """
    RMII Transmit Byte Muxer

    Handles transmitting a byte dibit-by-dibit.

    This submodule must be in the RMII ref_clk clock domain,
    and its inputs and outputs are likewise in that domain.

    Pins:
        * `txen`: RMII Transmit enable
        * `txd0`: TMII Transmit data 0
        * `txd1`: TMII Transmit data 1

    Inputs:
        * `data`: 8-bit wide data to transmit. Latched internally so you may
          update it to the next word after asserting `data_valid`.
        * `data_valid`: Assert while valid data is present at `data`.

    Outputs:
        * `ready`: Asserted when ready to receive new data. This is asserted
                   while the final dibit is being transmitted so that new data
                   can be produced on the next clock cycle.
    """
    def __init__(self, txen, txd0, txd1):
        # Inputs
        self.data = Signal(8)
        self.data_valid = Signal()

        # Outputs
        self.ready = Signal()

        ###

        # Register input data on the data_valid signal
        data_reg = Signal(8)

        self.submodules.fsm = FSM(reset_state="IDLE")

        self.comb += [
            self.ready.eq(
                self.fsm.ongoing("IDLE") | self.fsm.ongoing("NIBBLE4")),
            txen.eq(~self.fsm.ongoing("IDLE")),
        ]

        self.fsm.act(
            "IDLE",
            txd0.eq(0),
            txd1.eq(0),
            NextValue(data_reg, self.data),
            If(self.data_valid, NextState("NIBBLE1"))
        )

        self.fsm.act(
            "NIBBLE1",
            txd0.eq(data_reg[0]),
            txd1.eq(data_reg[1]),
            NextState("NIBBLE2"),
        )

        self.fsm.act(
            "NIBBLE2",
            txd0.eq(data_reg[2]),
            txd1.eq(data_reg[3]),
            NextState("NIBBLE3"),
        )

        self.fsm.act(
            "NIBBLE3",
            txd0.eq(data_reg[4]),
            txd1.eq(data_reg[5]),
            NextState("NIBBLE4"),
        )

        self.fsm.act(
            "NIBBLE4",
            txd0.eq(data_reg[6]),
            txd1.eq(data_reg[7]),
            NextValue(data_reg, self.data),
            If(
                self.data_valid,
                NextState("NIBBLE1")
            ).Else(
                NextState("IDLE")
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

    rmii_rx_byte = RMIIRxByte(crs_dv, rxd0, rxd1)

    def testbench():
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

    run_simulation(rmii_rx_byte, testbench(),
                   clocks={"sys": (20, 0)}, vcd_name="rmii_rx_byte.vcd")


def test_rmii_tx():
    from migen.sim import run_simulation
    from migen import Memory

    txen = Signal()
    txd0 = Signal()
    txd1 = Signal()

    txbytes = [
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xF0, 0xDE, 0xF1, 0x38, 0x89, 0x40,
        0x08, 0x00, 0x45, 0x00, 0x00, 0x54, 0x00, 0x00, 0x40, 0x00, 0x40, 0x01,
        0xB6, 0xD0, 0xC0, 0xA8, 0x01, 0x88, 0xC0, 0xA8, 0x01, 0x00, 0x08, 0x00,
        0x0D, 0xD9, 0x12, 0x1E, 0x00, 0x07, 0x3B, 0x3E, 0x0C, 0x5C, 0x00, 0x00,
        0x00, 0x00, 0x13, 0x03, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x57,
        0x6F, 0x72, 0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F,
        0x72, 0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72,
        0x6C, 0x64, 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C,
        0x64, 0x48,
    ]

    txbytes = [
        0x18, 0x31, 0xBF, 0xCB, 0x8E, 0xA4, 0x02, 0x44, 0x4E, 0x30, 0x76, 0x9E,
        0x08, 0x00, 0x45, 0x00, 0x00, 0x2F, 0x12, 0x34, 0x40, 0x00, 0xFF, 0x11,
        0xE3, 0x6E, 0xC0, 0xA8, 0x02, 0xC8, 0xC0, 0xA8, 0x02, 0x02, 0x00, 0x00,
        0x00, 0x00, 0x03, 0xE8, 0x07, 0xD0, 0x00, 0x17, 0xFB, 0xD2, 0x48, 0x65,
        0x6C, 0x6C, 0x6F, 0x2C, 0x20, 0x44, 0x41, 0x51, 0x6E, 0x65, 0x74, 0x21,
        0x0A
    ]

    preamblebytes = [0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x5D]
    crcbytes = [0x52, 0x32, 0x1F, 0x9E]
    crcbytes = [0x2F, 0x15, 0x10, 0x22]

    txnibbles = []
    rxnibbles = []

    for txbyte in preamblebytes + txbytes + crcbytes:
        txnibbles += [
            (txbyte & 0b11),
            ((txbyte >> 2) & 0b11),
            ((txbyte >> 4) & 0b11),
            ((txbyte >> 6) & 0b11),
        ]

    mem = Memory(8, 128, txbytes)
    mem_port = mem.get_port()

    rmii_tx = RMIITx(mem_port, txen, txd0, txd1)
    rmii_tx.specials += [mem, mem_port]

    def testbench():
        for _ in range(10):
            yield

        yield (rmii_tx.tx_start.eq(1))
        yield (rmii_tx.tx_len.eq(len(txbytes)))

        yield

        yield (rmii_tx.tx_start.eq(0))
        yield (rmii_tx.tx_len.eq(0))

        for _ in range((len(txbytes) + 12) * 4 + 10):
            if (yield txen):
                rxnibbles.append((yield txd0) | ((yield txd1) << 1))
            yield

        assert txnibbles == rxnibbles

    run_simulation(rmii_tx, testbench(), clocks={"sys": (20, 0)},
                   vcd_name="rmii_tx.vcd")


def test_rmii_tx_byte():
    import random
    from migen.sim import run_simulation

    data = Signal(8)
    data_valid = Signal()

    txen = Signal()
    txd0 = Signal()
    txd1 = Signal()

    rmii_tx_byte = RMIITxByte(txen, txd0, txd1)
    rmii_tx_byte.comb += [
        rmii_tx_byte.data.eq(data),
        rmii_tx_byte.data_valid.eq(data_valid),
    ]

    def testbench():
        for _ in range(10):
            yield

        txbytes = [random.randint(0, 255) for _ in range(8)]
        txnibbles = []
        rxnibbles = []

        yield (data_valid.eq(1))
        for txbyte in txbytes:
            txnibbles += [
                (txbyte & 0b11),
                ((txbyte >> 2) & 0b11),
                ((txbyte >> 4) & 0b11),
                ((txbyte >> 6) & 0b11),
            ]
            yield (data.eq(txbyte))
            yield
            rxnibbles.append((yield txd0) | ((yield txd1) << 1))
            yield
            rxnibbles.append((yield txd0) | ((yield txd1) << 1))
            yield
            rxnibbles.append((yield txd0) | ((yield txd1) << 1))
            yield
            rxnibbles.append((yield txd0) | ((yield txd1) << 1))

        yield (data_valid.eq(0))

        yield
        rxnibbles.append((yield txd0) | ((yield txd1) << 1))
        rxnibbles = rxnibbles[1:]
        assert txnibbles == rxnibbles

        for _ in range(10):
            yield

    run_simulation(rmii_tx_byte, testbench(), clocks={"sys": (20, 0)},
                   vcd_name="rmii_tx_byte.vcd")
