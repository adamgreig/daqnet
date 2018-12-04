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
        self.comb += self.link_up.eq(self.phy_manager.link_up)


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

        # Latches for BCR, BSR, LPA, which we'll poll to determine link status
        bcr = Signal(16)
        bsr = Signal(16)
        lpa = Signal(16)

        # Compute output signal from registers
        self.comb += self.link_up.eq(
            ~bcr[15] &     # Software reset must be off (also ensures MDIO
                           # stuck high doesn't falsely indicate link)
            bcr[12] &      # Autonegotiation must be on
            bsr[2] &       # Link must be up
            bsr[4] &       # No remote fault
            bsr[5] &       # No autonegotiation incomplete
            lpa[8]         # No link without 100Mbps full duplex
        )

        registers_to_read = [
            ("BCR", 0x00, bcr),
            ("BSR", 0x01, bsr),
            ("LPA", 0x05, lpa),
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
            If(counter == 0,
                NextValue(counter, one_ms),
                NextState("POLL_WAIT")),
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
                self.mdio.reg_addr.eq(Constant(addr)),
                self.mdio.rw.eq(0),
                self.mdio.start.eq(0),

                If(self.phy_reset == 1, NextState("RESET")),
                If(~self.mdio.busy,
                    NextValue(latch, self.mdio.read_data),
                    NextState(next_state)),
            )


def test_phy_manager():
    from migen.sim import run_simulation

    mdc = Signal()
    mdio = None
    phy_rst = Signal()

    # Specify a fake 5MHz clock frequency to reduce number of simulation steps
    # (must be >2.5MHz to generate MDC divider).
    phy_manager = PHYManager(5e6, 0, phy_rst, mdio, mdc)

    def testbench():
        # 1ms is 5000 ticks, so check we're still asserting phy_rst
        for _ in range(5000):
            assert (yield phy_rst) == 0
            yield

        assert (yield phy_manager.link_up) == 0

        # Allow enough clocks to step the state machine through
        for _ in range(100):
            yield

        # Now we wait another 1ms for bring-up, without asserting reset
        for _ in range(4900):
            assert (yield phy_rst) == 1
            yield

        assert (yield phy_manager.link_up) == 0

        # Wait for the first register read to synchronise to MDIO
        while True:
            if (yield phy_manager.mdio.mdio_t.o) == 1:
                break
            yield

        # Clock through BCR register read, setting bit 12
        for clk in range(129):
            if clk == 101:
                yield (phy_manager.mdio.mdio_t.i.eq(1))
            else:
                yield (phy_manager.mdio.mdio_t.i.eq(0))
            yield

        # Wait for the second register read to synchronise to MDIO
        while True:
            if (yield phy_manager.mdio.mdio_t.o) == 1:
                break
            yield

        # Clock through BSR read, setting bits 2, 4, 5
        for clk in range(129):
            if clk in (121, 117, 115):
                yield (phy_manager.mdio.mdio_t.i.eq(1))
            else:
                yield (phy_manager.mdio.mdio_t.i.eq(0))
            yield

        # Wait for the third register read to synchronise to MDIO
        while True:
            if (yield phy_manager.mdio.mdio_t.o) == 1:
                break
            yield

        # Clock through LPA register read, setting bit 8
        for clk in range(129):
            if clk == 109:
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
