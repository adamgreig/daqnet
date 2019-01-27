"""
Ethernet RMII Interface

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Module, Signal, Cat
from .crc import CRC32
from .mac_address_match import MACAddressMatch


class RMIIRx:
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

    Outputs:
        * `rx_valid`: pulsed when a valid packet is in memory
        * `rx_offset`: n-bit start address of received packet
        * `rx_len`: 11-bit length of received packet
    """
    def __init__(self, mac_addr, write_port, crs_dv, rxd0, rxd1):
        # Outputs
        self.rx_valid = Signal()
        self.rx_offset = Signal(write_port.addr.nbits)
        self.rx_len = Signal(11)

        # Store arguments
        self.mac_addr = mac_addr
        self.write_port = write_port
        self.crs_dv = crs_dv
        self.rxd0 = rxd0
        self.rxd1 = rxd1

    def elaborate(self, platform):

        m = Module()

        m.submodules.crc = crc = CRC32()
        m.submodules.mac_match = mac_match = MACAddressMatch(self.mac_addr)
        m.submodules.rxbyte = rxbyte = RMIIRxByte(
            self.crs_dv, self.rxd0, self.rxd1)

        adr = Signal(self.write_port.addr.nbits)

        with m.FSM() as fsm:
            m.d.comb += [
                self.write_port.addr.eq(adr),
                self.write_port.data.eq(rxbyte.data),
                self.write_port.en.eq(rxbyte.data_valid),
                crc.data.eq(rxbyte.data),
                crc.data_valid.eq(rxbyte.data_valid),
                crc.reset.eq(fsm.ongoing("IDLE")),
                mac_match.data.eq(rxbyte.data),
                mac_match.data_valid.eq(rxbyte.data_valid),
                mac_match.reset.eq(fsm.ongoing("IDLE")),
            ]

            # Idle until we see data valid
            with m.State("IDLE"):
                m.d.sync += self.rx_len.eq(0)
                m.d.sync += self.rx_valid.eq(0)
                with m.If(rxbyte.dv):
                    m.d.sync += self.rx_offset.eq(adr)
                    m.next = "DATA"

            # Save incoming data to memory
            with m.State("DATA"):
                with m.If(rxbyte.data_valid):
                    m.d.sync += adr.eq(adr + 1)
                    m.d.sync += self.rx_len.eq(self.rx_len + 1)
                with m.Elif(~rxbyte.dv):
                    m.next = "EOF"

            with m.State("EOF"):
                with m.If(crc.crc_match & mac_match.mac_match):
                    m.d.sync += self.rx_valid.eq(1)
                m.next = "IDLE"

        return m


class RMIIRxByte:
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

        self.crs_dv = crs_dv
        self.rxd0 = rxd0
        self.rxd1 = rxd1

    def elaborate(self, platform):
        m = Module()

        # Sample RMII signals on rising edge of ref_clk
        crs_dv_reg = Signal()
        rxd_reg = Signal(2)
        m.d.sync += [
            crs_dv_reg.eq(self.crs_dv),
            rxd_reg.eq(Cat(self.rxd0, self.rxd1)),
        ]

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += [
                    self.crs.eq(0),
                    self.dv.eq(0),
                    self.data_valid.eq(0),
                ]
                with m.If(crs_dv_reg & (rxd_reg == 0b01)):
                    m.next = "PREAMBLE_SFD"

            with m.State("PREAMBLE_SFD"):
                m.d.sync += [
                    self.crs.eq(1),
                    self.dv.eq(1),
                    self.data_valid.eq(0),
                ]
                with m.If(rxd_reg == 0b11):
                    m.next = "NIBBLE1"
                with m.Elif(rxd_reg != 0b01):
                    m.next = "IDLE"

            with m.State("NIBBLE1"):
                m.d.sync += [
                    self.data[0:2].eq(rxd_reg),
                    self.data_valid.eq(0),
                ]
                with m.If(self.dv):
                    m.d.sync += self.crs.eq(crs_dv_reg)
                    m.next = "NIBBLE2"
                with m.Else():
                    m.next = "IDLE"

            with m.State("NIBBLE2"):
                m.d.sync += [
                    self.data[2:4].eq(rxd_reg),
                    self.data_valid.eq(0),
                ]
                with m.If(self.dv):
                    m.d.sync += self.dv.eq(crs_dv_reg)
                    m.next = "NIBBLE3"
                with m.Else():
                    m.next = "IDLE"

            with m.State("NIBBLE3"):
                m.d.sync += [
                    self.data[4:6].eq(rxd_reg),
                    self.data_valid.eq(0),
                ]
                with m.If(self.dv):
                    m.d.sync += self.crs.eq(crs_dv_reg)
                    m.next = "NIBBLE4"
                with m.Else():
                    m.next = "IDLE"

            with m.State("NIBBLE4"):
                m.d.sync += [
                    self.data[6:8].eq(rxd_reg),
                    self.data_valid.eq(0),
                ]
                with m.If(self.dv):
                    m.d.sync += [
                        self.dv.eq(crs_dv_reg),
                        self.data_valid.eq(1),
                    ]
                    m.next = "NIBBLE1"
                with m.Else():
                    m.d.sync += self.data_valid.eq(1),
                    m.next = "IDLE"

        return m


class RMIITx:
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
        * `tx_start`: Pulse high to begin transmission of a packet
        * `tx_offset`: n-bit address offset of packet to transmit
        * `tx_len`: 11-bit length of packet to transmit

    Outputs:
        * `tx_ready`: Asserted while ready to transmit a new packet
    """
    def __init__(self, read_port, txen, txd0, txd1):
        # Inputs
        self.tx_start = Signal()
        self.tx_offset = Signal(read_port.addr.nbits)
        self.tx_len = Signal(11)

        # Outputs
        self.tx_ready = Signal()

        self.read_port = read_port
        self.txen = txen
        self.txd0 = txd0
        self.txd1 = txd1

    def elaborate(self, platform):
        m = Module()

        # Transmit byte counter
        tx_idx = Signal(self.read_port.addr.nbits)
        # Transmit length latch
        tx_len = Signal(11)
        # Transmit offset latch
        tx_offset = Signal(self.read_port.addr.nbits)

        m.submodules.crc = crc = CRC32()
        m.submodules.txbyte = txbyte = RMIITxByte(
            self.txen, self.txd0, self.txd1)

        with m.FSM() as fsm:
            m.d.comb += [
                self.read_port.addr.eq(tx_idx + tx_offset),
                crc.data.eq(txbyte.data),
                crc.reset.eq(fsm.ongoing("IDLE")),
                crc.data_valid.eq(
                    (fsm.ongoing("DATA") | fsm.ongoing("PAD"))
                    & txbyte.ready),
                self.tx_ready.eq(fsm.ongoing("IDLE")),
                txbyte.data_valid.eq(
                    ~(fsm.ongoing("IDLE") | fsm.ongoing("IPG"))),
            ]

            with m.State("IDLE"):
                m.d.comb += txbyte.data.eq(0)
                m.d.sync += [
                    tx_idx.eq(0),
                    tx_offset.eq(self.tx_offset),
                    tx_len.eq(self.tx_len),
                ]
                with m.If(self.tx_start):
                    m.next = "PREAMBLE"

            with m.State("PREAMBLE"):
                m.d.comb += txbyte.data.eq(0x55)
                with m.If(txbyte.ready):
                    with m.If(tx_idx == 6):
                        m.d.sync += tx_idx.eq(0)
                        m.next = "SFD"
                    with m.Else():
                        m.d.sync += tx_idx.eq(tx_idx + 1)

            with m.State("SFD"):
                m.d.comb += txbyte.data.eq(0xD5)
                with m.If(txbyte.ready):
                    m.next = "DATA"

            with m.State("DATA"):
                m.d.comb += txbyte.data.eq(self.read_port.data)
                with m.If(txbyte.ready):
                    m.d.sync += tx_idx.eq(tx_idx + 1)
                    with m.If(tx_idx == tx_len - 1):
                        with m.If(tx_len < 60):
                            m.next = "PAD"
                        with m.Else():
                            m.next = "FCS1"

            with m.State("PAD"):
                m.d.comb += txbyte.data.eq(0x00)
                with m.If(txbyte.ready):
                    m.d.sync += tx_idx.eq(tx_idx + 1)
                    with m.If(tx_idx == 59):
                        m.next = "FCS1"

            with m.State("FCS1"):
                m.d.comb += txbyte.data.eq(crc.crc_out[0:8])
                with m.If(txbyte.ready):
                    m.next = "FCS2"

            with m.State("FCS2"):
                m.d.comb += txbyte.data.eq(crc.crc_out[8:16])
                with m.If(txbyte.ready):
                    m.next = "FCS3"

            with m.State("FCS3"):
                m.d.comb += txbyte.data.eq(crc.crc_out[16:24])
                with m.If(txbyte.ready):
                    m.next = "FCS4"

            with m.State("FCS4"):
                m.d.comb += txbyte.data.eq(crc.crc_out[24:32])
                with m.If(txbyte.ready):
                    m.d.sync += tx_idx.eq(0)
                    m.next = "IPG"

            with m.State("IPG"):
                m.d.sync += tx_idx.eq(tx_idx + 1)
                with m.If(tx_idx == 48):
                    m.next = "IDLE"

        return m


class RMIITxByte:
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

        self.txen = txen
        self.txd0 = txd0
        self.txd1 = txd1

    def elaborate(self, platform):
        m = Module()

        # Register input data on the data_valid signal
        data_reg = Signal(8)

        with m.FSM() as fsm:
            m.d.comb += [
                self.ready.eq(fsm.ongoing("IDLE") | fsm.ongoing("NIBBLE4")),
                self.txen.eq(~fsm.ongoing("IDLE")),
            ]

            with m.State("IDLE"):
                m.d.comb += [
                    self.txd0.eq(0),
                    self.txd1.eq(0),
                ]
                m.d.sync += data_reg.eq(self.data)
                with m.If(self.data_valid):
                    m.next = "NIBBLE1"

            with m.State("NIBBLE1"):
                m.d.comb += [
                    self.txd0.eq(data_reg[0]),
                    self.txd1.eq(data_reg[1]),
                ]
                m.next = "NIBBLE2"

            with m.State("NIBBLE2"):
                m.d.comb += [
                    self.txd0.eq(data_reg[2]),
                    self.txd1.eq(data_reg[3]),
                ]
                m.next = "NIBBLE3"

            with m.State("NIBBLE3"):
                m.d.comb += [
                    self.txd0.eq(data_reg[4]),
                    self.txd1.eq(data_reg[5]),
                ]
                m.next = "NIBBLE4"

            with m.State("NIBBLE4"):
                m.d.comb += [
                    self.txd0.eq(data_reg[6]),
                    self.txd1.eq(data_reg[7]),
                ]
                m.d.sync += data_reg.eq(self.data)
                with m.If(self.data_valid):
                    m.next = "NIBBLE1"
                with m.Else():
                    m.next = "IDLE"

        return m


def test_rmii_rx():
    import random
    from nmigen.back import pysim
    from nmigen import Memory

    crs_dv = Signal()
    rxd0 = Signal()
    rxd1 = Signal()

    mem = Memory(8, 128)
    mem_port = mem.write_port()
    mac_addr = [random.randint(0, 255) for _ in range(6)]

    rmii_rx = RMIIRx(mac_addr, mem_port, crs_dv, rxd0, rxd1)

    def testbench():
        def tx_packet():
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

            # Finish clocking
            for _ in range(6):
                yield

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

        # Transmit first packet
        yield from tx_packet()

        # Check packet was received
        assert (yield rmii_rx.rx_valid)
        assert (yield rmii_rx.rx_len) == 102
        assert (yield rmii_rx.rx_offset) == 0
        mem_contents = []
        for idx in range(102):
            mem_contents.append((yield mem[idx]))
        assert mem_contents == txbytes

        # Pause (inter-frame gap)
        for _ in range(20):
            yield

        assert (yield rmii_rx.rx_valid) == 0

        # Transmit a second packet
        yield from tx_packet()

        # Check packet was received
        assert (yield rmii_rx.rx_valid)
        assert (yield rmii_rx.rx_len) == 102
        assert (yield rmii_rx.rx_offset) == 102
        mem_contents = []
        for idx in range(102):
            mem_contents.append((yield mem[(102+idx) % 128]))
        assert mem_contents == txbytes

        yield

    mod = rmii_rx.elaborate(None)
    mod.submodules += mem_port
    vcdf = open("rmii_rx.vcd", "w")
    with pysim.Simulator(mod, vcd_file=vcdf) as sim:
        sim.add_clock(1/50e6)
        sim.add_sync_process(testbench())
        sim.run()


def test_rmii_rx_byte():
    import random
    from nmigen.back import pysim

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

    frag = rmii_rx_byte.elaborate(None)
    vcdf = open("rmii_rx_byte.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1/50e6)
        sim.add_sync_process(testbench())
        sim.run()


def test_rmii_tx():
    from nmigen.back import pysim
    from nmigen import Memory

    txen = Signal()
    txd0 = Signal()
    txd1 = Signal()

    txbytes = [
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x02, 0x44, 0x4e, 0x30, 0x76,
        0x9e, 0x08, 0x06, 0x00, 0x01, 0x08, 0x00, 0x06, 0x04, 0x00, 0x01,
        0x02, 0x44, 0x4e, 0x30, 0x76, 0x9e, 0xc0, 0xa8, 0x02, 0xc8, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0xa8, 0x02, 0xc8
    ]

    preamblebytes = [0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0xD5]
    padbytes = [0x00] * (60 - len(txbytes))
    crcbytes = [0x44, 0x5E, 0xB4, 0xD2]

    txnibbles = []
    rxnibbles = []

    for txbyte in preamblebytes + txbytes + padbytes + crcbytes:
        txnibbles += [
            (txbyte & 0b11),
            ((txbyte >> 2) & 0b11),
            ((txbyte >> 4) & 0b11),
            ((txbyte >> 6) & 0b11),
        ]

    # Put the transmit bytes into memory at some offset, and fill the rest of
    # memory with all-1s (to ensure we're not relying on memory being zeroed).
    txbytes_zp = txbytes + [0xFF]*(128 - len(txbytes))
    txoffset = 120
    txbytes_mem = txbytes_zp[-txoffset:] + txbytes_zp[:-txoffset]
    mem = Memory(8, 128, txbytes_mem)
    mem_port = mem.read_port()

    rmii_tx = RMIITx(mem_port, txen, txd0, txd1)

    def testbench():
        for _ in range(10):
            yield

        yield (rmii_tx.tx_start.eq(1))
        yield (rmii_tx.tx_offset.eq(txoffset))
        yield (rmii_tx.tx_len.eq(len(txbytes)))

        yield

        yield (rmii_tx.tx_start.eq(0))
        yield (rmii_tx.tx_offset.eq(0))
        yield (rmii_tx.tx_len.eq(0))

        for _ in range((len(txbytes) + 12) * 4 + 120):
            if (yield txen):
                rxnibbles.append((yield txd0) | ((yield txd1) << 1))
            yield

        print(len(txnibbles), len(rxnibbles))
        print(txnibbles)
        print(rxnibbles)
        assert txnibbles == rxnibbles

    mod = rmii_tx.elaborate(None)
    mod.submodules += mem_port

    vcdf = open("rmii_tx.vcd", "w")
    with pysim.Simulator(mod, vcd_file=vcdf) as sim:
        sim.add_clock(1/50e6)
        sim.add_sync_process(testbench())
        sim.run()


def test_rmii_tx_byte():
    import random
    from nmigen.back import pysim

    txen = Signal()
    txd0 = Signal()
    txd1 = Signal()

    rmii_tx_byte = RMIITxByte(txen, txd0, txd1)
    data = rmii_tx_byte.data
    data_valid = rmii_tx_byte.data_valid

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

    frag = rmii_tx_byte.elaborate(None)
    vcdf = open("rmii_tx_byte.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1/50e6)
        sim.add_sync_process(testbench())
        sim.run()
