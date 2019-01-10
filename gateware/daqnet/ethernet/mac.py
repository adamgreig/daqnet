"""
Ethernet RMII MAC

Copyright 2018-2019 Adam Greig
"""

from nmigen import Module, Signal, Const, Memory, ClockDomain
from nmigen.hdl.xfrm import DomainRenamer
from .mdio import MDIO
from .rmii import RMIIRx, RMIITx
from ..utils import PulseStretch


class MAC:
    """
    Ethernet RMII MAC.

    Clock domain:
        This module is clocked at the system clock frequency and generates an
        RMII clock domain internally. All its inputs and outputs are in the
        system clock domain.

    Parameters:
        * `clk_freq`: MAC's clock frequency
        * `phy_addr`: 5-bit address of the PHY
        * `mac_addr`: MAC address in standard XX:XX:XX:XX:XX:XX format

    Ports:
        * `rx_port`: Read port into RX packet memory, 8 bytes by 2048 cells.
        * `tx_port`: Write port into TX packet memory, 8 bytes by 2048 cells.

    Pins:
        * `rmii`: signal group containing txd0, txd1, txen, rxd0, rxd1, crs_dv,
                  ref_clk, mdc, mdio
        * `phy_rst`: PHY RST pin (output, active low)
        * `eth_led`: Ethernet LED, active high, pulsed on packet traffic

    Inputs:
        * `rx_ack`: Assert to acknowledge packet reception and restart
                    listening for new packets, ideally within 48 RMII
                    ref_clk cycles.
        * `tx_start`: Assert to begin transmission of a packet from memory
        * `tx_len`: 11-bit wide length of packet to transmit

    Outputs:
        * `link_up`: High while link is established
        * `rx_valid`: Asserted when a valid packet is in RX memory.
                      Acknowledge by asserting `rx_ack`.
        * `rx_len`: Received packet length. Valid while `rx_valid` is asserted
        * `tx_ready`: Asserted while ready to transmit a new packet
    """
    def __init__(self, clk_freq, phy_addr, mac_addr, rmii, phy_rst, eth_led):
        # Ports
        self.rx_port = None  # Assigned below
        self.tx_port = None  # Assigned below

        # Inputs
        self.rx_ack = Signal()
        self.tx_start = Signal()
        self.tx_len = Signal(11)

        # Outputs
        self.link_up = Signal()
        self.rx_valid = Signal()
        self.rx_len = Signal(11)
        self.tx_ready = Signal()

        self.clk_freq = clk_freq
        self.phy_addr = phy_addr
        self.mac_addr = [int(x, 16) for x in mac_addr.split(":")]
        self.rmii = rmii
        self.phy_rst = phy_rst
        self.eth_led = eth_led

        # Create packet memories and interface ports
        self.rx_mem = Memory(8, 2048)
        self.rx_port = self.rx_mem.read_port()
        self.tx_mem = Memory(8, 2048)
        self.tx_port = self.tx_mem.write_port()

    def get_fragment(self, platform):
        m = Module()

        # Create RMII clock domain from RMII clock input
        cd = ClockDomain("rmii", reset_less=True)
        m.d.comb += cd.clk.eq(self.rmii.ref_clk)
        m.domains.rmii = cd

        # Create RX write and TX read ports for RMII use
        rx_port_w = self.rx_mem.write_port(domain="rmii")
        tx_port_r = self.tx_mem.read_port(domain="rmii")
        m.submodules += [self.rx_port, rx_port_w, self.tx_port, tx_port_r]

        # Create submodules for PHY and RMII
        m.submodules.phy_manager = phy_manager = PHYManager(
            self.clk_freq, self.phy_addr, self.phy_rst,
            self.rmii.mdio, self.rmii.mdc)
        m.submodules.stretch = stretch = PulseStretch(int(self.clk_freq/1000))
        m.d.comb += phy_manager.phy_reset.eq(0)

        rmii_rx = RMIIRx(
            self.mac_addr, rx_port_w, self.rmii.crs_dv,
            self.rmii.rxd0, self.rmii.rxd1)
        rmii_tx = RMIITx(
            tx_port_r, self.rmii.txen, self.rmii.txd0, self.rmii.txd1)

        # Double register RMIIRx inputs/outputs for CDC
        rx_valid_latch = Signal()
        rx_len_latch = Signal(11)
        rx_ack_latch = Signal()
        tx_start_latch = Signal()
        tx_len_latch = Signal(11)
        tx_ready_latch = Signal()
        m.d.sync += [
            rx_valid_latch.eq(rmii_rx.rx_valid),
            self.rx_valid.eq(rx_valid_latch),
            rx_len_latch.eq(rmii_rx.rx_len),
            self.rx_len.eq(rx_len_latch),
            rx_ack_latch.eq(self.rx_ack),
            rmii_rx.rx_ack.eq(rx_ack_latch),
            tx_start_latch.eq(self.tx_start),
            rmii_tx.tx_start.eq(tx_start_latch),
            tx_len_latch.eq(self.tx_len),
            rmii_tx.tx_len.eq(tx_len_latch),
            tx_ready_latch.eq(rmii_tx.tx_ready),
            self.tx_ready.eq(tx_ready_latch),
        ]

        m.d.comb += [
            self.link_up.eq(phy_manager.link_up),
            stretch.trigger.eq(self.rx_valid | ~self.tx_ready),
            self.eth_led.eq(stretch.pulse),
        ]

        m.submodules.rmii_rx = DomainRenamer("rmii")(
            rmii_rx.get_fragment(platform))
        m.submodules.rmii_tx = DomainRenamer("rmii")(
            rmii_tx.get_fragment(platform))

        frag = m.lower(platform)
        frag.add_ports(self.rmii.txen, self.rmii.txd0, self.rmii.txd1, dir='o')
        frag.add_ports(self.rmii.mdc, dir='o')
        return frag


class PHYManager:
    """
    Manage a PHY over MDIO.

    Can trigger a PHY reset. Resets PHY at power-up.

    Continually polls PHY for acceptable link status and outputs link status.

    Parameters:
        * `clk_freq`: Frequency of this module's clock, used to time the 1ms
                      reset period and calculate the MDIO clock divider
        * `phy_addr`: 5-bit address of the PHY

    Pins:
        * `phy_rst`: PHY RST pin (output, active low)
        * `mdio`: MDIO pin (data in/out)
        * `mdc`: MDC pin (clock out)

    Inputs:
        * `phy_reset`: Pulse high to trigger a PHY reset

    Outputs:
        * `link_up`: High while link is established
    """
    def __init__(self, clk_freq, phy_addr, phy_rst, mdio, mdc):
        # Inputs
        self.phy_reset = Signal()

        # Outputs
        self.link_up = Signal()

        self.clk_freq = clk_freq
        self.phy_addr = phy_addr
        self.phy_rst = phy_rst
        self.mdio = mdio
        self.mdc = mdc

    def get_fragment(self, platform):
        m = Module()

        # Create MDIO submodule
        clk_div = int(self.clk_freq // 2.5e6)
        m.submodules.mdio = mdio = MDIO(clk_div, self.mdio, self.mdc)
        self.mdio = mdio
        mdio.phy_addr = Const(self.phy_addr)

        # Latches for registers we read
        bsr = Signal(16)

        # Compute output signal from registers
        m.d.comb += self.link_up.eq(
            bsr[2] &        # Link must be up
            ~bsr[4] &       # No remote fault
            bsr[5] &        # Autonegotiation complete
            bsr[14]         # 100Mbps full duplex
        )

        registers_to_write = [
            # Enable 100Mbps, autonegotiation, and full-duplex
            # ("BCR", 0x00, (1 << 13) | (1 << 12) | (1 << 8)),
        ]

        registers_to_read = [
            # Basic status register contains everything we need to know
            ("BSR", 0x01, bsr),
        ]

        # Controller FSM
        one_ms = int(self.clk_freq//1000)
        counter = Signal(max=one_ms)
        with m.FSM():

            # Assert PHY_RST and begin 1ms counter
            with m.State("RESET"):
                m.d.comb += self.phy_rst.eq(0)
                m.d.sync += counter.eq(one_ms)
                m.next = "RESET_WAIT"

            # Wait for reset timeout
            with m.State("RESET_WAIT"):
                m.d.comb += self.phy_rst.eq(0)
                m.d.sync += counter.eq(counter - 1)
                with m.If(self.phy_reset):
                    m.next = "RESET"
                with m.Elif(counter == 0):
                    m.d.sync += counter.eq(one_ms)
                    write = bool(registers_to_write)
                    m.next = "WRITE_WAIT" if write else "POLL_WAIT"

            # Wait 1ms before writing
            if registers_to_write:
                with m.State("WRITE_WAIT"):
                    m.d.comb += self.phy_rst.eq(1),
                    m.d.sync += counter.eq(counter - 1)
                    with m.If(self.phy_reset):
                        m.next = "RESET"
                    with m.Elif(counter == 0):
                        m.next = f"WRITE_{registers_to_write[0][0]}"
            else:
                m.d.comb += mdio.write_data.eq(0)

            for idx, (name, addr, val) in enumerate(registers_to_write):
                if idx == len(registers_to_write) - 1:
                    next_state = "POLL_WAIT"
                else:
                    next_state = f"WRITE_{registers_to_write[idx+1][0]}"

                with m.State(f"WRITE_{name}"):
                    m.d.comb += [
                        self.phy_rst.eq(0),
                        mdio.reg_addr.eq(Const(addr)),
                        mdio.rw.eq(1),
                        mdio.write_data.eq(Const(val)),
                        mdio.start.eq(1),
                    ]

                    with m.If(self.phy_reset):
                        m.next = "RESET"
                    with m.Elif(mdio.busy):
                        m.next = f"WRITE_{name}_WAIT"

                with m.State(f"WRITE_{name}_WAIT"):
                    m.d.comb += [
                        self.phy_rst.eq(1),
                        mdio.reg_addr.eq(0),
                        mdio.rw.eq(0),
                        mdio.write_data.eq(0),
                        mdio.start.eq(0),
                    ]
                    with m.If(self.phy_reset):
                        m.next = "RESET"
                    with m.Elif(~mdio.busy):
                        m.d.sync += counter.eq(one_ms)
                        m.next = next_state

            # Wait 1ms between polls
            with m.State("POLL_WAIT"):
                m.d.comb += self.phy_rst.eq(1)
                m.d.sync += counter.eq(counter - 1)
                with m.If(self.phy_reset):
                    m.next = "RESET"
                with m.Elif(counter == 0):
                    m.next = f"POLL_{registers_to_read[0][0]}"

            for idx, (name, addr, latch) in enumerate(registers_to_read):
                if idx == len(registers_to_read) - 1:
                    next_state = "POLL_WAIT"
                else:
                    next_state = f"POLL_{registers_to_read[idx+1][0]}"

                # Trigger a read of the register
                with m.State(f"POLL_{name}"):
                    m.d.comb += [
                        self.phy_rst.eq(1),
                        mdio.reg_addr.eq(Const(addr)),
                        mdio.rw.eq(0),
                        mdio.start.eq(1),
                    ]

                    with m.If(self.phy_reset):
                        m.next = "RESET"
                    with m.Elif(mdio.busy):
                        m.next = f"POLL_{name}_WAIT"

                # Wait for MDIO to stop being busy
                with m.State(f"POLL_{name}_WAIT"):
                    m.d.comb += [
                        self.phy_rst.eq(1),
                        mdio.reg_addr.eq(0),
                        mdio.rw.eq(0),
                        mdio.start.eq(0),
                    ]

                    with m.If(self.phy_reset):
                        m.next = "RESET"
                    with m.Elif(~mdio.busy):
                        m.d.sync += [
                            latch.eq(mdio.read_data),
                            counter.eq(one_ms),
                        ]
                        m.next = next_state

        frag = m.lower(platform)
        frag.add_ports(self.mdc, dir='o')
        return frag


def test_phy_manager():
    from nmigen.back import pysim

    mdc = Signal()
    mdio = None
    phy_rst = Signal()

    # Specify a fake 10MHz clock frequency to reduce number of simulation steps
    phy_manager = PHYManager(10e6, 0, phy_rst, mdio, mdc)

    def testbench():
        # 1ms is 10000 ticks, so check we're still asserting phy_rst
        for _ in range(10000):
            assert (yield phy_rst) == 0
            yield

        assert (yield phy_manager.link_up) == 0

        # Allow enough clocks to step the state machine through
        for _ in range(100):
            yield

        # Now we wait another 1ms for bring-up, without asserting reset
        for _ in range(9900):
            assert (yield phy_rst) == 1
            yield

        assert (yield phy_manager.link_up) == 0

        # Wait for the register read to synchronise to MDIO
        while True:
            if (yield phy_manager.mdio.mdio_t.o) == 1:
                break
            yield

        # Clock through BSR register read, setting bits 14, 5, 2
        for clk in range(260):
            if clk in (194, 230, 242):
                yield (phy_manager.mdio.mdio_t.i.eq(1))
            else:
                yield (phy_manager.mdio.mdio_t.i.eq(0))
            yield

        # Finish register reads
        for _ in range(100):
            yield

        # Check link_up becomes 1
        assert (yield phy_manager.link_up) == 1

    frag = phy_manager.get_fragment(None)
    vcdf = open("phy_manager.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()
