"""
Sigma-delta ADC using one differential input and one single-ended output.

Copyright 2018 Adam Greig
"""

import numpy as np
from migen import Module, Signal, Instance, Constant, ClockDomain


class SDADC(Module):
    """
    Implements a sigma-delta ADC.

    Required circuit:
        * ADC Input to positive LVDS input
        * 1k resistor between output pin and negative LVDS input
        * 1n capacitor between negative LVDS input and ground

    Inputs:
        * `inpin`: LVDS input signal
        * `outpin`: LVCMOS output signal

    Outputs:
        * `samp_clk`: Clock signal pulses high each valid output word
        * `samp_dat`: 8-bit signed output sample data
    """

    def __init__(self, sys_clk, inpin, outpin):
        self.samp_clk = Signal()
        self.samp_dat = Signal(8)

        self.diff_in = Signal()
        self.comb += outpin.eq(~self.diff_in)

        self.specials += Instance(
            "SB_IO",
            p_PIN_TYPE=Constant(0b00000, 6),
            p_IO_STANDARD="SB_LVDS_INPUT",
            io_PACKAGE_PIN=inpin,
            o_D_IN_0=self.diff_in,
            i_INPUT_CLK=sys_clk,
        )

        self.submodules.cic = CIC(self.diff_in, W=8, D=1024, Q=2)
        self.comb += [
            self.samp_clk.eq(self.cic.samp_clk),
            self.samp_dat.eq(self.cic.samp_dat),
        ]


class CIC(Module):
    """
    A cascaded integrator-comb filter for 1-bit inputs.

    Parameters:
        * W is the output word width
        * D is the downsampling ratio, and must be a positive power of 2
        * Q is the filter order and is typically between 1 to 5

    Inputs:
        * `bitin`: input bit to filter

    Outputs:
        * `samp_dat`: output word of width W
        * `samp_clk`: output clock
    """
    def __init__(self, bitin, W=8, D=512, Q=2):
        assert D >= 1, "D must be positive"
        assert D & (D - 1) == 0, "D must be a power of two"
        assert Q >= 1, "Q must be positive"
        B = 1 + int(np.ceil(Q * np.log2(D)))
        assert W <= B, "W must be at least the register size B"

        self.samp_dat = Signal(W)
        self.samp_clk = Signal()

        self.clk_div = Signal(int(np.log2(D)))
        self.sync += self.clk_div.eq(self.clk_div + 1)

        self.clock_domains.cd_samp = ClockDomain()
        self.comb += self.cd_samp.clk.eq(self.clk_div[-1])
        self.comb += self.samp_clk.eq(self.cd_samp.clk)

        sampin = Signal(B)
        self.comb += sampin.eq(bitin)

        integrators = [sampin]
        for q in range(Q):
            integrator = Signal(B)
            self.sync += integrator.eq(integrator + integrators[-1])
            integrators.append(integrator)

        downsampled = Signal(B)
        self.sync.samp += downsampled.eq(integrators[-1])

        combs = []
        csums = [downsampled]
        for q in range(Q):
            comb = Signal(B)
            csum = Signal(B)
            if len(combs) == 0:
                self.comb += csum.eq(csums[-1])
                csums.append(csum)
            else:
                self.comb += csum.eq(csums[-1] - combs[-1])
                csums.append(csum)
            self.sync.samp += comb.eq(csums[-1])
            combs.append(comb)

        out_sum = Signal(B)
        self.comb += out_sum.eq((csums[-1] - combs[-1]) << 1)

        self.comb += self.samp_dat.eq(out_sum[-W:])


def test_cic():
    from migen.sim import run_simulation

    # Generate 300us worth of samples of a sine wave, 150 samples
    sine = np.cos(2*np.pi*10e3*np.linspace(0, 200e-6, 150))
    # Expand into 2000 1-bit samples
    expand = 20
    data = np.empty(expand*sine.size, dtype=np.uint8)
    for idx, samp in enumerate(sine):
        samp = int((samp * 127 + 128) / (256 / expand))
        assert 0 <= samp <= expand, f"samp={samp}"
        data[idx*expand:(idx+1)*expand] = [1]*samp + [0]*(expand-samp)

    bit = Signal()
    D = 64
    cic = CIC(bit, W=8, D=D, Q=3)

    def tb():
        for databit in data:
            yield (bit.eq(int(databit)))
            yield

    run_simulation(cic, tb(),
                   clocks={"sys": 10, "samp": 10*D},
                   vcd_name="cic.vcd")
