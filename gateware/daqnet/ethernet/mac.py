"""
Ethernet RMII MAC

Copyright 2018 Adam Greig
"""

from migen import (Module, Signal, Constant, If, FSM, NextValue, NextState)
from .mdio import MDIO


class MAC(Module):
    """
    Ethernet RMII MAC.

    Parameters:
        * `clk_freq`: MAC's clock frequency
        * `phy_addr`: 5-bit address of the PHY

    Pins:
        * `rmii`: signal group containing txd0, txd1, txen, rxd0, rxd1, crs_dv,
                  clk, mdc, mdio
        * `phy_rst`: PHY RST pin (output, active low)
        * `eth_led`: Ethernet LED, active high, pulsed on packet traffic

    Outputs:
        * `link_up`: High while link is established
    """
    def __init__(self, clk_freq, phy_addr, rmii, phy_rst, eth_led):
        # Inputs

        # Outputs
        self.link_up = Signal()

        ###

        self.submodules.phy_manager = PHYManager(
            clk_freq, phy_addr, phy_rst, rmii.mdio, rmii.mdc)

        self.comb += [
            self.link_up.eq(self.phy_manager.link_up),
            eth_led.eq(self.link_up),
            rmii.txen.eq(0),
            rmii.txd0.eq(0),
            rmii.txd1.eq(0),
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
            ("BCR", 0x00, (1 << 13) | (1 << 12) | (1 << 8)),
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
