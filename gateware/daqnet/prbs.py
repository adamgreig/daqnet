"""
Generate PRBS bit sequences.

Copyright 2017 Adam Greig
"""

import pytest
import numpy as np
from migen import Module, Signal, Cat, Mux, If
from migen.sim import run_simulation

# These are the taps for each PRBS sequence which are not the MSb,
# i.e., for PRBS9, we have x^9 + x^5 + 1, where 5 comes from this dict.
TAPS = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}


class PRBS(Module):
    """
    Generates PRBSk binary test sequences, output as the 1-bit signal `self.x`.

    k must be one of (7, 9, 11, 15, 20, 23, 31).
    """
    def __init__(self, k):
        # `x` is a single bit which outputs the PRBS sequence.
        self.x = Signal()

        ###

        if k not in TAPS.keys():
            raise ValueError("k={} invalid for PRBS".format(k))

        tap = TAPS[k]
        self.state = Signal(k, reset=1)
        self.comb += self.x.eq(self.state[k-1] ^ self.state[tap-1])
        self.sync += Cat(self.state).eq(Cat(self.x, self.state))


class PRBSErrorDetector(Module):
    """
    Compares incoming bit sequences to the PRBS they should have been generated
    by, and outputs a pulse every time an error is detected.
    """
    def __init__(self, k, bit):
        """
        `k` is the PRBS length, one of (7, 9, 11, 15, 20, 23, 31).
        `bit` is the input bit to be tested against the PRBS.

        Outputs:
        `err`: pulses high for one clock when the incoming bit does not match.
        Note that two immediately adjacent errors will cause a longer pulse,
        rather than two separate pulses.
        """
        self.err = Signal()

        if k not in TAPS.keys():
            raise ValueError("k={} invalid for PRBS".format(k))

        # Run the same PRBS as the transmitter, but we can choose whether to
        # shift in the new feedback bit, or to shift in the received bit
        # instead, to synchronise state.
        tap = TAPS[k]
        self.prbs = Signal(k, reset=1)
        self.feedback_bit = Signal()
        self.prbs_in = Signal()
        self.bit_in = Signal()
        self.sync += self.bit_in.eq(bit)
        self.comb += self.feedback_bit.eq(self.prbs[k-1] ^ self.prbs[tap-1])
        self.sync += Cat(self.prbs).eq(Cat(self.prbs_in, self.prbs))

        # Track whether we need to reload the PRBS state from the incoming
        # bits to resynchronise.
        self.reload = Signal(reset=1)

        # Select the PRBS input as either the feedback or the input bit
        self.comb += self.prbs_in.eq(Mux(
            self.reload, self.bit_in, self.feedback_bit))

        # Compute current error value and store previous k values of err.
        self.comb += self.err.eq(self.bit_in != self.feedback_bit)
        self.err_sr = Signal(k, reset=2**k - 1)
        self.sync += Cat(self.err_sr).eq(Cat(self.err, self.err_sr))

        # Count how many errors occurred in the last k bits
        logk = int(np.ceil(np.log2(k)))
        self.err_count = Signal(logk)
        self.comb += self.err_count.eq(sum(self.err_sr))

        # If the number of errors exceeds k/2, assume we've lost sync and
        # reload the PRBS.
        self.reload_ctr = Signal(logk + 1)
        self.sync += If(
                self.err_count > k//2,
                self.reload_ctr.eq(k + k//2),
                self.err_sr.eq(0)
            ).Elif(
                self.reload != 0,
                self.reload_ctr.eq(self.reload_ctr - 1)
            )
        self.comb += self.reload.eq(self.reload_ctr != 0)


@pytest.mark.parametrize("k", TAPS.keys())
def test_prbs(k):
    prbs = PRBS(k)

    def tb():
        lfsr = 1
        # Test up to the first 512 bits. We'd be here forever testing PRBS31.
        for _ in range(min((1 << k) - 1, 512)):

            # These two lines simulate the PRBS generator in Python
            bit = ((lfsr >> (k-1)) ^ (lfsr >> TAPS[k]-1)) & 1
            lfsr = ((lfsr << 1) | bit) & ((1 << k)-1)

            # We compare it to the hardware simulation result
            assert (yield prbs.x) == bit

            # Run the hardware for one clock cycle
            yield

    run_simulation(prbs, tb())


@pytest.mark.parametrize("k", TAPS.keys())
def test_prbs_error_detector(k):
    source = Signal()
    prbsdetector = PRBSErrorDetector(k, source)
    nbits = min((1 << k) - 1, 512)
    tx_errors = np.random.binomial(1, 0.02, nbits)
    tx_err = Signal()

    # Ensure no errors at startup to make verification easier
    tx_errors[:2*k] = 0

    # Give a large burst of errors in the middle to check recovery
    tx_errors[nbits//2:nbits//2 + 3*k] = 1
    tx_errors[nbits//2 + 3*k:nbits//2 + 5*k] = 0

    tx_errors = tx_errors.tolist()

    def tb():
        rx_errors = []
        valid = []
        lfsr = 1
        for i in range(nbits):
            bit = ((lfsr >> (k-1)) ^ (lfsr >> TAPS[k]-1)) & 1
            lfsr = ((lfsr << 1) | bit) & ((1 << k)-1)

            (yield source.eq(bit ^ tx_errors[i]))
            (yield tx_err.eq(tx_errors[i]))
            yield
            rx_errors.append((yield prbsdetector.err))
            valid.append(1-(yield prbsdetector.reload))

        # Check that, outside the initial synchronisation and the
        # large error burst in the middle (plus some resync time),
        # all errors are detected correctly.
        valid = np.array(valid, dtype=np.bool)[:-1]
        valid_tx_errors = np.array(tx_errors)[:-1][valid]
        valid_rx_errors = np.array(rx_errors)[1:][valid]
        print(valid_tx_errors)
        print(valid_rx_errors)
        assert valid_tx_errors.tolist() == valid_rx_errors.tolist()

    run_simulation(prbsdetector, tb(), vcd_name="dump.vcd")
