"""
Gateway utilities and common modules.

Copyright 2018-2019 Adam Greig
Released under the MIT license; see LICENSE for details.
"""

from nmigen import Module, Signal, Cat, Elaboratable


class LFSR(Elaboratable):
    TAPS = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}

    def __init__(self, k):
        self.reset = Signal()
        self.state = Signal(k, reset=1)

        if k not in LFSR.TAPS.keys():
            raise ValueError(f"k={k} invalid for LFSR")

        self.k = k

    def elaborate(self, platform):
        m = Module()
        x = Signal()
        tap = LFSR.TAPS[self.k]
        m.d.comb += x.eq(self.state[self.k-1] ^ self.state[tap-1])
        with m.If(self.reset):
            m.d.sync += self.state.eq(1)
        with m.Else():
            m.d.sync += Cat(self.state).eq(Cat(x, self.state))

        return m


class PulseStretch(Elaboratable):
    def __init__(self, nclks):
        # Inputs
        self.trigger = Signal()

        # Outputs
        self.pulse = Signal()

        self.nclks = nclks

    def elaborate(self, platform):
        m = Module()

        counter = Signal(max=self.nclks)

        with m.FSM() as fsm:
            m.d.comb += self.pulse.eq(fsm.ongoing("STRETCH"))
            with m.State("WAIT"):
                m.d.sync += counter.eq(0)
                with m.If(self.trigger):
                    m.next = "STRETCH"

            with m.State("STRETCH"):
                with m.If(counter == self.nclks - 1):
                    m.next = "WAIT"
                with m.Else():
                    m.d.sync += counter.eq(counter + 1)

        return m


class PipelinedAdder(Elaboratable):
    """
    Implements an n-wide adder using m pipelined sub-adders.
    """
    def __init__(self, n, m):
        self.a = Signal(n)
        self.b = Signal(n)
        self.c = Signal(n)

        self.n = n
        self.m = m

    def elaborate(self, platform):
        m = Module()

        bits_per_sub = self.n//self.m
        ci = 0
        for idx in range(self.m):
            sub_adder = Signal(bits_per_sub+1, name=f"sub{idx}")
            i0 = idx*bits_per_sub
            i1 = (idx+1)*bits_per_sub
            m.d.sync += sub_adder.eq(self.a[i0:i1] + self.b[i0:i1] + ci)
            m.d.comb += self.c[i0:i1].eq(sub_adder[:bits_per_sub])
            ci = sub_adder[-1]

        return m


def test_pipelined_adder():
    from nmigen.back import pysim
    import random

    n = 64
    m = 4
    adder = PipelinedAdder(n, m)

    def testbench():
        for _ in range(100):
            a = random.randrange(2**n)
            b = random.randrange(2**n)
            yield
            yield adder.a.eq(a)
            yield adder.b.eq(b)
            for _ in range(m+1):
                yield
            assert (yield adder.c) == (a+b) % (2**n)

        yield adder.a.eq(2**n-1)
        yield adder.b.eq(1)
        for _ in range(m+1):
            yield
        assert (yield adder.c) == 0

    vcdf = open("adder.vcd", "w")
    with pysim.Simulator(adder, vcd_file=vcdf) as sim:
        sim.add_clock(1e-6)
        sim.add_sync_process(testbench())
        sim.run()
