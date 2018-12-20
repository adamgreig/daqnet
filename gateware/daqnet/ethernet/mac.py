"""
Ethernet RMII MAC

Copyright 2018 Adam Greig
"""

from migen import (Module, Signal, Constant, If, FSM, NextValue, NextState,
                   Memory, ClockDomain, ClockDomainsRenamer)
from .mdio import MDIO
from .rmii import RMIIRx, RMIITx
from ..utils import PulseStretch


class MAC(Module):
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

        ###

        # Turn MAC address into list-of-ints
        self.mac_addr = [int(x, 16) for x in mac_addr.split(":")]

        # Create RMII clock domain from RMII clock input
        self.clock_domains.rmii = ClockDomain("rmii")
        self.comb += self.rmii.clk.eq(rmii.ref_clk)

        # Create RX packet memory and read/write ports
        rx_mem = Memory(8, 2048)
        self.rx_port = rx_mem.get_port()
        rx_port_w = rx_mem.get_port(write_capable=True, clock_domain="rmii")
        self.specials += [rx_mem, self.rx_port, rx_port_w]

        # Create TX packet memory and read/write ports
        tx_mem = Memory(8, 2048)
        self.tx_port = tx_mem.get_port(write_capable=True)
        tx_port_r = tx_mem.get_port(clock_domain="rmii")
        self.specials += [tx_mem, self.tx_port, tx_port_r]

        # Create submodules for PHY and RMII
        self.submodules.phy_manager = PHYManager(
            clk_freq, phy_addr, phy_rst, rmii.mdio, rmii.mdc)
        self.submodules.rmii_rx = ClockDomainsRenamer("rmii")(
            RMIIRx(self.mac_addr, rx_port_w, rmii.crs_dv,
                   rmii.rxd0, rmii.rxd1))
        self.submodules.rmii_tx = ClockDomainsRenamer("rmii")(
            RMIITx(tx_port_r, rmii.txen, rmii.txd0, rmii.txd1))
        self.submodules.stretch = PulseStretch(int(clk_freq/1000))

        # Double register RMIIRx inputs/outputs for CDC
        rx_valid_latch = Signal()
        rx_len_latch = Signal(11)
        rx_ack_latch = Signal()
        tx_start_latch = Signal()
        tx_len_latch = Signal(11)
        tx_ready_latch = Signal()
        self.sync += [
            rx_valid_latch.eq(self.rmii_rx.rx_valid),
            self.rx_valid.eq(rx_valid_latch),
            rx_len_latch.eq(self.rmii_rx.rx_len),
            self.rx_len.eq(rx_len_latch),
            rx_ack_latch.eq(self.rx_ack),
            self.rmii_rx.rx_ack.eq(rx_ack_latch),
            tx_start_latch.eq(self.tx_start),
            self.rmii_tx.tx_start.eq(tx_start_latch),
            tx_len_latch.eq(self.tx_len),
            self.rmii_tx.tx_len.eq(tx_len_latch),
            tx_ready_latch.eq(self.rmii_tx.tx_ready),
            self.tx_ready.eq(tx_ready_latch),
        ]

        self.comb += [
            self.link_up.eq(self.phy_manager.link_up),
            self.stretch.input.eq(self.rx_valid | ~self.tx_ready),
            eth_led.eq(self.stretch.output),
        ]


class PHYManager(Module):
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

        ###

        # Create MDIO submodule
        clk_div = int(clk_freq // 2.5e6)
        self.submodules.mdio = MDIO(clk_div, mdio, mdc)
        self.mdio.phy_addr = Constant(phy_addr)

        # Latches for registers we read
        bsr = Signal(16)

        # Compute output signal from registers
        self.comb += self.link_up.eq(
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
        self.submodules.fsm = FSM(reset_state="RESET")
        one_ms = int(clk_freq//1000)
        counter = Signal(max=one_ms)

        # Assert PHY_RST and begin 1ms counter
        self.fsm.act(
            "RESET",
            phy_rst.eq(0),
            NextValue(counter, one_ms),
            NextState("RESET_WAIT"),
        )

        # Wait for reset timeout
        self.fsm.act(
            "RESET_WAIT",
            phy_rst.eq(0),
            NextValue(counter, counter - 1),
            If(self.phy_reset == 1, NextState("RESET")),
            If(
                counter == 0,
                NextValue(counter, one_ms),
                NextState("WRITE_WAIT" if registers_to_write else "POLL_WAIT")
            ),
        )

        # Wait 1ms before writing
        if registers_to_write:
            self.fsm.act(
                "WRITE_WAIT",
                phy_rst.eq(1),
                NextValue(counter, counter - 1),
                If(self.phy_reset == 1, NextState("RESET")),
                If(
                    counter == 0,
                    NextState(f"WRITE_{registers_to_write[0][0]}")
                ),
            )

        for idx, (name, addr, val) in enumerate(registers_to_write):
            if idx == len(registers_to_write) - 1:
                next_state = "POLL_WAIT"
            else:
                next_state = f"WRITE_{registers_to_write[idx+1][0]}"

            self.fsm.act(
                f"WRITE_{name}",
                phy_rst.eq(0),
                self.mdio.reg_addr.eq(Constant(addr)),
                self.mdio.rw.eq(1),
                self.mdio.write_data.eq(Constant(val)),
                self.mdio.start.eq(1),

                If(self.phy_reset == 1, NextState("RESET")),
                If(self.mdio.busy, NextState(f"WRITE_{name}_WAIT")),
            )

            self.fsm.act(
                f"WRITE_{name}_WAIT",
                phy_rst.eq(1),
                self.mdio.reg_addr.eq(0),
                self.mdio.rw.eq(0),
                self.mdio.write_data.eq(0),
                self.mdio.start.eq(0),
                If(self.phy_reset == 1, NextState("RESET")),
                If(~self.mdio.busy,
                    NextValue(counter, one_ms),
                    NextState(next_state)),
            )

        # Wait 1ms between polls
        self.fsm.act(
            "POLL_WAIT",
            phy_rst.eq(1),
            NextValue(counter, counter - 1),
            If(self.phy_reset == 1, NextState("RESET")),
            If(counter == 0,
                NextState(f"POLL_{registers_to_read[0][0]}")),
        )

        for idx, (name, addr, latch) in enumerate(registers_to_read):
            if idx == len(registers_to_read) - 1:
                next_state = "POLL_WAIT"
            else:
                next_state = f"POLL_{registers_to_read[idx+1][0]}"

            # Trigger a read of the register
            self.fsm.act(
                f"POLL_{name}",
                phy_rst.eq(1),
                self.mdio.reg_addr.eq(Constant(addr)),
                self.mdio.rw.eq(0),
                self.mdio.start.eq(1),

                If(self.phy_reset == 1, NextState("RESET")),
                If(self.mdio.busy, NextState(f"POLL_{name}_WAIT")),
            )

            # Wait for MDIO to stop being busy
            self.fsm.act(
                f"POLL_{name}_WAIT",
                phy_rst.eq(1),
                self.mdio.reg_addr.eq(0),
                self.mdio.rw.eq(0),
                self.mdio.start.eq(0),

                If(self.phy_reset == 1, NextState("RESET")),
                If(~self.mdio.busy,
                    NextValue(latch, self.mdio.read_data),
                    NextValue(counter, one_ms),
                    NextState(next_state)),
            )


def test_phy_manager():
    from migen.sim import run_simulation

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

    run_simulation(phy_manager, testbench(), vcd_name="phy_manager.vcd")
