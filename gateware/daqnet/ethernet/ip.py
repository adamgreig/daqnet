"""
Ethernet IP stack

Copyright 2018-2019 Adam Greig
"""

from nmigen import Module, Signal, Memory


class IPStack:
    """
    IP stack.

    This simple IP stack handles Ethernet frames, ARP packets, and IPv4 ICMP
    and UDP packets.

    Parameters:
        * `mac_addr`: MAC address in standard XX:XX:XX:XX:XX:XX format
        * `ip4_addr`: IPv4 address in standard xxx.xxx.xxx.xxx format

    RX port:
        * `rx_port`: Read port into RX packet memory
        * `rx_len`: Length of received packet
        * `rx_offset`: Start address of received packet
        * `rx_valid`: High when new packet data is ready in `rx_len`
        * `rx_ack`: Pulsed high when current packet has been processed

    TX port:
        * `tx_port`: Write port into TX packet memory
        * `tx_len`: Set to length of packet to transmit
        * `tx_offset`: Set to start address of packet to transmit
        * `tx_start`: Pulsed high when valid TX data is on `tx_len`
    """
    def __init__(self, mac_addr, ip4_addr, rx_port, tx_port):
        # RX port
        self.rx_port = rx_port
        self.rx_len = Signal(11)
        self.rx_offset = Signal(11)
        self.rx_valid = Signal()
        self.rx_ack = Signal()

        # TX port
        self.tx_port = tx_port
        self.tx_len = Signal(11)
        self.tx_offset = Signal(11)
        self.tx_start = Signal()

        self.mac_addr = [int(x, 16) for x in mac_addr.split(":")]
        self.ip4_addr = [int(x, 10) for x in ip4_addr.split(".")]
        self.mac_addr_int = sum(self.mac_addr[5-x] << (8*x) for x in range(6))
        self.ip4_addr_int = sum(self.ip4_addr[3-x] << (8*x) for x in range(4))

    def get_fragment(self, platform):
        m = Module()

        m.submodules.eth = eth = _EthernetLayer(self)

        self.rx_addr = Signal(11)

        m.d.comb += [
            self.rx_port.addr.eq(self.rx_addr),
            self.tx_port.addr.eq(eth.tx_addr + self.tx_offset),
            self.tx_port.data.eq(eth.tx_data),
            self.tx_port.en.eq(eth.tx_en),
        ]

        m.d.sync += [
            eth.rx_data.eq(self.rx_port.data),
        ]

        load_ctr = Signal(3)

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += self.rx_addr.eq(self.rx_offset),
                m.d.sync += self.tx_start.eq(0)
                m.d.sync += eth.run.eq(0)
                m.d.sync += load_ctr.eq(0)
                with m.If(self.rx_valid):
                    m.d.sync += self.rx_ack.eq(1)
                    m.next = "REPLY"

            with m.State("REPLY"):
                m.d.sync += self.rx_addr.eq(self.rx_addr + 1),
                m.d.sync += eth.run.eq(~eth.done)
                m.d.sync += self.rx_ack.eq(0)
                with m.If(eth.done):
                    with m.If(eth.send):
                        m.next = "TX_LOAD"
                        m.d.sync += self.tx_start.eq(1)
                        m.d.sync += self.tx_len.eq(eth.tx_len)
                    with m.Else():
                        m.next = "IDLE"

            with m.State("TX_LOAD"):
                m.d.sync += eth.run.eq(0)
                m.d.sync += self.tx_start.eq(1)
                with m.If(load_ctr == 4):
                    m.next = "TX_INCR_OFFSET"
                with m.Else():
                    m.d.sync += load_ctr.eq(load_ctr + 1)

            with m.State("TX_INCR_OFFSET"):
                m.d.sync += self.tx_start.eq(0)
                m.d.sync += self.tx_offset.eq(self.tx_offset + self.tx_len)
                m.next = "IDLE"

        return m.lower(platform)


class _StackLayer:
    """
    Layer in IP stack.

    Interfaces to a layer above and zero or more layers below.

    Incoming packet data is streamed in-order into each layer, which performs
    any processing for its part of the packet and then streams further data
    to a delegated child layer if required.

    Outgoing packet data is sent up to the parent layer as an address and data
    to put in that address. Addresses are relative to the start of this layer's
    data.

    Parameters:
        * `ip_stack`: reference to top-level IPStack instance which contains
          relevant constants such as configured IP and MAC address

    Interface:
        * `run`: Input pulsed high to start this layer processing a received
          packet which will begin streaming in
        * `done`: Output pulsed high when processing is finished
        * `send`: Output pulsed high along with `done` if a packet should be
          transmitted from the tx memory
        * `rx_data`: Input 8-bit received packet data, one byte per clock
        * `tx_en`: Output pulsed high if `tx_addr` and `tx_data` are valid
        * `tx_addr`: Output 11-bit address to store `tx_data` in, relative to
          start address of this layer
        * `tx_data`: Output 8-bit data to store at `tx_addr`
        * `tx_len`: Output 11-bit number of bytes to transmit from this layer,
          valid when `send` is high.
    """
    def __init__(self, ip_stack):
        self.run = Signal()
        self.done = Signal()
        self.send = Signal()
        self.rx_data = Signal(8)
        self.tx_en = Signal()
        self.tx_addr = Signal(11)
        self.tx_data = Signal(8)
        self.tx_len = Signal(11)

        self.send_at_end = Signal()
        self.child_tx_len = Signal(11)
        self.ip_stack = ip_stack

    def start_fsm(self):
        """
        Call to generate first FSM state.
        """
        self._fsm_ctr = 0
        with self.m.State("IDLE"):
            self.m.d.sync += self.send_at_end.eq(0)
            self.m.d.sync += self.tx_en.eq(0)
            self.m.d.sync += self.child_tx_len.eq(0)
            with self.m.If(self.run):
                self.m.next = self._fsm_ctr

    def skip(self, name, n=1):
        """
        Skip `n` bytes from the input.
        """
        for i in range(n):
            with self.m.State(self._fsm_ctr):
                self._fsm_ctr += 1
                self.m.d.sync += self.tx_en.eq(0)
                self.m.next = self._fsm_ctr

    def copy(self, name, dst, n=1):
        """
        Copy `n` bytes from input stream to offset `dst` in output.
        """
        for i in range(n):
            with self.m.State(self._fsm_ctr):
                self._fsm_ctr += 1
                self.m.d.sync += [
                    self.tx_en.eq(1),
                    self.tx_addr.eq(dst + i),
                    self.tx_data.eq(self.rx_data),
                ]
                self.m.next = self._fsm_ctr

    def copy_sig_n(self, name, dst, n):
        """
        Copy `n` bytes from input stream to offset `dst` in output,
        where `n` is a register or other signal.
        """
        ctr = Signal(shape=n.nbits)
        with self.m.State(self._fsm_ctr):
            self._fsm_ctr += 1
            self.m.d.sync += [
                self.tx_en.eq(1),
                self.tx_addr.eq(dst + ctr),
                self.tx_data.eq(self.rx_data),
            ]
            with self.m.If(ctr == n - 1):
                self.m.next = self._fsm_ctr
                self.m.d.sync += ctr.eq(0)
            with self.m.Else():
                self.m.d.sync += ctr.eq(ctr + 1)

    def extract(self, name, reg, n=1, bigendian=True):
        """
        Extract `n` bytes from input stream to register `reg`.
        """
        for i in range(n):
            with self.m.State(self._fsm_ctr):
                self._fsm_ctr += 1
                if bigendian:
                    left, right = 8*(n-i-1), 8*(n-i)
                else:
                    left, right = 8*i, 8*(i+1)
                self.m.d.sync += reg[left:right].eq(self.rx_data)
                self.m.d.sync += self.tx_en.eq(0)
                self.m.next = self._fsm_ctr

    def check(self, name, val, n=1, bigendian=True):
        """
        Compare `n` bytes from input stream to `val` and only proceed on match.
        """
        for i in range(n):
            with self.m.State(self._fsm_ctr):
                self._fsm_ctr += 1
                self.m.d.sync += self.tx_en.eq(0)
                if bigendian:
                    val_byte = (val >> 8*(n-i-1)) & 0xFF
                else:
                    val_byte = (val >> 8*i) & 0xFF
                with self.m.If(self.rx_data == val_byte):
                    self.m.next = self._fsm_ctr
                with self.m.Else():
                    self.m.next = "DONE_NO_TX"

    def write(self, name, val, dst, n=1, bigendian=True):
        """
        Writes `n` bytes of `val` (register or constant) to offset `dst`.
        """
        for i in range(n):
            with self.m.State(self._fsm_ctr):
                self._fsm_ctr += 1
                if bigendian:
                    val_byte = (val >> 8*(n-i-1)) & 0xFF
                else:
                    val_byte = (val >> 8*i) & 0xFF
                self.m.d.sync += [
                    self.tx_addr.eq(dst + i),
                    self.tx_data.eq(val_byte),
                    self.tx_en.eq(1),
                ]
                self.m.next = self._fsm_ctr

    def switch(self, key, cases):
        """
        Depending on the value in register `key`, delegate further
        processing to the relevant case from `cases` (a dictionary
        of integers mapping submodules).
        """
        # Wire up submodules' rx_data
        for case in cases:
            submod = cases[case]
            self.m.d.sync += [
                submod.rx_data.eq(self.rx_data),
            ]

        # Generate switch state
        with self.m.State(self._fsm_ctr):
            with self.m.Switch(key):
                for case in cases:
                    submod = cases[case]
                    with self.m.Case(case):
                        self.m.d.sync += [
                            self.tx_en.eq(submod.tx_en),
                            self.tx_addr.eq(submod.tx_addr + self._fsm_ctr),
                            self.tx_data.eq(submod.tx_data),
                        ]
                        self.m.d.comb += submod.run.eq(~submod.done)
                        with self.m.If(submod.done):
                            with self.m.If(submod.send):
                                self.m.next = self._fsm_ctr + 1
                                self.m.d.sync += [
                                    self.send_at_end.eq(1),
                                    self.child_tx_len.eq(submod.tx_len),
                                ]
                            with self.m.Else():
                                self.m.next = "DONE_NO_TX"
                with self.m.Case():
                    self.m.next = "DONE_NO_TX"

        self._fsm_ctr += 1

    def end_fsm(self, tx_len=0, send=False):
        """
        Call to generate final FSM state.

        * `tx_len`: number of bytes sent by this layer
        * `send`: whether to send a reply packet. Automatically set from child
                  if a `switch` statement was used.
        """
        self.m.d.sync += self.tx_len.eq(tx_len + self.child_tx_len)
        with self.m.State("DONE_NO_TX"):
            self.m.d.comb += [
                self.done.eq(1),
                self.send.eq(0),
            ]
            self.m.next = "IDLE"
        with self.m.State("DONE_TX"):
            self.m.d.comb += [
                self.done.eq(1),
                self.send.eq(1),
            ]
            self.m.next = "IDLE"
        with self.m.State(self._fsm_ctr):
            self.m.d.sync += self.tx_en.eq(0)
            if send:
                self.m.next = "DONE_TX"
            else:
                with self.m.If(self.send_at_end):
                    self.m.next = "DONE_TX"
                with self.m.Else():
                    self.m.next = "DONE_NO_TX"

    def get_fragment(self, platform):
        """
        Default dummy implementation to allow using not-yet-implemented
        modules.
        """
        self.m = Module()

        with self.m.FSM():
            self.start_fsm()
            self.end_fsm()

        self.m.d.comb += [
            self.tx_addr.eq(0),
            self.tx_data.eq(0),
        ]

        return self.m.lower(platform)


class _EthernetLayer(_StackLayer):
    """
    Implements top-level Ethernet handling.

    Muxes to lower levels depending on packet EtherType.
    """
    def get_fragment(self, platform):
        self.m = Module()
        self.m.submodules.arp = arp = _ARPLayer(self.ip_stack)
        self.m.submodules.ipv4 = ipv4 = _IPv4Layer(self.ip_stack)

        ethertype = Signal(16)

        with self.m.FSM():
            self.start_fsm()

            # Copy source into outgoing destination in case we transmit later.
            self.skip("DST", n=6)
            self.copy("SRC", dst=0, n=6)

            # Extract and switch on the ethertype field.
            # If there's no handler or the handler doesn't need to transmit,
            # we'll return to idle after this.
            self.extract("ETYPE", reg=ethertype, n=2)
            self.switch(ethertype, {
                0x0806: arp,
                0x0800: ipv4,
            })

            # If we need to transmit, fill in the Ethernet source and ethertype
            self.write("SRC", val=self.ip_stack.mac_addr_int, dst=6, n=6)
            self.write("ETYPE", val=ethertype, dst=12, n=2)
            self.end_fsm(tx_len=14)

        return self.m.lower(platform)


class _ARPLayer(_StackLayer):
    """
    Implements an Ethernet ARP handling.

    Replies to requests for its own MAC address only.
    """
    def get_fragment(self, platform):
        self.m = Module()

        with self.m.FSM():
            self.start_fsm()

            # Read incoming packet, checking/copying relevant fields as we go.
            # If any checks do not pass, we abort immediately.
            self.copy("HTYPE", dst=0, n=2)
            self.check("PTYPE", val=0x0800, n=2)
            self.copy("LEN", dst=4, n=2)
            self.check("OPER", val=1, n=2)
            self.copy("SHA", dst=18, n=6)
            self.copy("SPA", dst=24, n=4)
            self.skip("THA", n=6)
            self.check("TPA", val=self.ip_stack.ip4_addr_int, n=4)

            # If the TPA check matches, prepare to send a response.
            self.write("PTYPE", val=0x0800, dst=2, n=2)
            self.write("OPER", val=2, dst=6, n=2)
            self.write("SHA", val=self.ip_stack.mac_addr_int, dst=8, n=6)
            self.write("SPA", val=self.ip_stack.ip4_addr_int, dst=14, n=4)

            # Send response
            self.end_fsm(tx_len=28, send=True)

        return self.m.lower(platform)


class _IPv4Layer(_StackLayer):
    """
    Implements a simple IPv4 layer.
    """
    def __init__(self, ip_stack):
        super().__init__(ip_stack)
        self.total_length = Signal(16)
        self.source_ip = Signal(32)

    def get_fragment(self, platform):
        self.m = Module()
        self.m.submodules.icmpv4 = icmpv4 = _ICMPv4Layer(self.ip_stack, self)
        self.m.submodules.udp = udp = _UDPLayer(self.ip_stack, self)
        self.m.submodules.ipchecksum = ipchecksum = _InternetChecksum()

        self.m.d.comb += [
            ipchecksum.data.eq(self.tx_data),
            ipchecksum.en.eq(self.tx_en),
            ipchecksum.reset.eq(self.done),
        ]

        protocol = Signal(8)

        with self.m.FSM():
            self.start_fsm()

            # Process incoming packet header and delegate if required
            self.check("VER_IHL", val=0x45, n=1)
            self.skip("DSCP_ECN", n=1)
            self.extract("TOTAL_LENGTH", reg=self.total_length, n=2)
            self.skip("ID_FRAG_TTL", n=5)
            self.extract("PROTO", reg=protocol, n=1)
            self.skip("CHECKSUM", n=2)
            self.extract("SOURCE", reg=self.source_ip, n=4)
            self.check("DEST", val=self.ip_stack.ip4_addr_int, n=4)
            self.switch(protocol, {
                0x01: icmpv4,
                0x11: udp,
            })

            # If the child layer requested transmission, fill in the
            # outbound IPv4 header
            self.write("VER_IHL", val=0x45, dst=0, n=1)
            self.write("DSCP_ECN", val=0x00, dst=1, n=1)
            self.write("TOTAL_LENGTH", val=self.child_tx_len+20, dst=2, n=2)
            self.write("ID_FLAGS_FRAG", val=0x00000000, dst=4, n=4)
            self.write("TTL", val=64, dst=8, n=1)
            self.write("PROTO", val=protocol, dst=9, n=1)
            self.write("SOURCE", val=self.ip_stack.ip4_addr_int, dst=12, n=4)
            self.write("DEST", val=self.source_ip, dst=16, n=4)
            self.write("CHECKSUM", val=ipchecksum.checksum, dst=10, n=2)
            self.end_fsm(tx_len=20, send=True)

        return self.m.lower(platform)


class _ICMPv4Layer(_StackLayer):
    """
    Implements a simple ICMPv4 layer.

    Replies to echo requests only.
    """
    def __init__(self, ip_stack, ipv4):
        super().__init__(ip_stack)
        self.ipv4 = ipv4

    def get_fragment(self, platform):
        self.m = Module()
        self.m.submodules.ipchecksum = ipchecksum = _InternetChecksum()

        payload_n = Signal(11)

        self.m.d.comb += [
            ipchecksum.data.eq(self.tx_data),
            ipchecksum.en.eq(self.tx_en),
            ipchecksum.reset.eq(self.done),
        ]
        self.m.d.sync += payload_n.eq(self.ipv4.total_length - 28)

        with self.m.FSM():
            self.start_fsm()
            self.check("TYPE", val=8, n=1)
            self.check("CODE", val=0, n=1)
            self.skip("CHECKSUM", n=2)
            self.copy("IDENTIFIER", dst=4, n=2)
            self.copy("SEQUENCE", dst=6, n=2)
            self.copy_sig_n("PAYLOAD", dst=8, n=payload_n)
            self.write("TYPE", val=0, dst=0, n=1)
            self.write("CODE", val=0, dst=1, n=1)
            self.write("CHECKSUM", val=ipchecksum.checksum, dst=2, n=2)
            self.end_fsm(tx_len=self.ipv4.total_length - 20, send=True)

        return self.m.lower(platform)


class _UDPLayer(_StackLayer):
    """
    Implements a simple UDP layer.
    """
    def __init__(self, ip_stack, ipv4):
        super().__init__(ip_stack)
        self.ipv4 = ipv4


class _InternetChecksum:
    """
    Implements the Internet Checksum algorithm from RFC 1071.

    Inputs:
        * `data`: 8-bit data to add to checksum. Alternating bytes are treated
          as high/low bytes and must be input in that order.
        * `en`: Checksum updated with `data` when `en` is high
        * `reset`: Pulse high to reset checksum to zero

    Outputs:
        * `checksum`: 16-bit current value of checksum
    """
    def __init__(self):
        self.data = Signal(8)
        self.en = Signal()
        self.reset = Signal()
        self.checksum = Signal(16)

    def get_fragment(self, platform):
        m = Module()
        state = Signal(17)
        lowbyte = Signal()
        data_shift = Signal(16)

        m.d.comb += self.checksum.eq(~state[:-1])

        with m.If(lowbyte):
            m.d.comb += data_shift.eq(self.data)
        with m.Else():
            m.d.comb += data_shift.eq(self.data << 8)

        with m.If(self.reset):
            m.d.sync += [state.eq(0), lowbyte.eq(0)]
        with m.Else():
            with m.If(self.en):
                m.d.sync += state.eq(state[:-1] + data_shift + state[-1])
                m.d.sync += lowbyte.eq(~lowbyte),
        return m.lower(platform)


def test_ipv4_checksum():
    from nmigen.back import pysim

    checksum = _InternetChecksum()

    data = [0x45, 0x00, 0x00, 0x73, 0x00, 0x00, 0x40, 0x00, 0x40, 0x11, 0x00,
            0x00, 0xc0, 0xa8, 0x00, 0x01, 0xc0, 0xa8, 0x00, 0xc7]
    expected_checksum = 0xb861

    def testbench():
        yield
        yield

        for i in range(2):

            for byte in data:
                yield checksum.data.eq(byte)
                yield checksum.en.eq(1)
                yield

            yield checksum.en.eq(0)
            yield

            assert (yield checksum.checksum) == expected_checksum

            yield checksum.reset.eq(1)
            yield
            yield checksum.reset.eq(0)
            yield

    frag = checksum.get_fragment(None)
    vcdf = open(f"ipstack_ipv4_checksum.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1/100e6)
        sim.add_sync_process(testbench())
        sim.run()


def run_rx_test(name, rx_bytes, expected_bytes, mac_addr, ip4_addr):
    from nmigen.back import pysim

    mem_n = 64
    rx_mem = Memory(8, mem_n, [0]*4 + rx_bytes)
    rx_mem_port = rx_mem.read_port()
    tx_mem = Memory(8, mem_n)
    tx_mem_port = tx_mem.write_port()

    ipstack = IPStack(mac_addr, ip4_addr, rx_mem_port, tx_mem_port)

    def testbench():
        for repeat in range(3):
            yield
            yield

            yield ipstack.rx_offset.eq(4)
            yield ipstack.rx_valid.eq(1)
            yield
            yield ipstack.rx_valid.eq(0)
            yield ipstack.rx_offset.eq(0)

            tx_start = False
            tx_offset = 0
            tx_len = 0
            for _ in range(128):
                if (yield ipstack.tx_start):
                    tx_start = True
                    tx_offset = (yield ipstack.tx_offset)
                    tx_len = (yield ipstack.tx_len)
                yield

            tx_bytes = []
            for idx in range(len(expected_bytes)):
                tx_bytes.append((yield tx_mem[(tx_offset + idx) % mem_n]))

            if expected_bytes is not None:
                # Check transmit got asserted with valid tx_len, tx_offset
                assert tx_start
                assert tx_len == len(expected_bytes)
                print("Received:", " ".join(
                    f"{x:02X}" for x in tx_bytes),
                    f"({len(tx_bytes)} bytes)")
                print("Expected:", " ".join(
                    f"{x:02X}" for x in expected_bytes),
                    f"({len(expected_bytes)} bytes)")
                print("Diff:    ", " ".join(
                    "XX" if x != y else "  "
                    for (x, y) in zip(tx_bytes, expected_bytes)))
                assert tx_bytes == expected_bytes
            else:
                # Check transmit did not get asserted
                assert not tx_start

    frag = ipstack.get_fragment(None)
    frag.add_subfragment(rx_mem_port.get_fragment(None))
    frag.add_subfragment(tx_mem_port.get_fragment(None))

    vcdf = open(f"ipstack_rx_{name}.vcd", "w")
    with pysim.Simulator(frag, vcd_file=vcdf) as sim:
        sim.add_clock(1/100e6)
        sim.add_sync_process(testbench())
        sim.run()


def test_rx_arp():
    mac_addr = "01:23:45:67:89:AB"
    ip4_addr = "10.0.0.5"

    # Sample ARP request packet
    rx_bytes = [
        # Sent to FF:FF:FF:FF:FF:FF
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        # Sent from 00:01:02:03:04:05
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
        # Ethertype is ARP
        0x08, 0x06,
        # HTYPE is 1=Ethernet
        0x00, 0x01,
        # PTYPE is 0800=IPv4
        0x08, 0x00,
        # HLEN is 6
        0x06,
        # PLEN is 4
        0x04,
        # OPER is 1=request
        0x00, 0x01,
        # SHA is 00:01:02:03:04:05
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
        # SPA is 10.0.0.1
        0x0A, 0x00, 0x00, 0x01,
        # THA is ignored in requests
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # TPA is 10.0.0.5
        0x0A, 0x00, 0x00, 0x05
    ]

    expected_bytes = [
        # Sent to 00:01:02:03:04:05
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
        # Sent from 01:23:45:67:89:AB
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB,
        # Ethertype is ARP
        0x08, 0x06,
        # HTYPE is 1=Ethernet
        0x00, 0x01,
        # PTYPE is 0800=IPv4
        0x08, 0x00,
        # HLEN is 6
        0x06,
        # PLEN is 4
        0x04,
        # OPER is 2=request
        0x00, 0x02,
        # SHA is 01:23:45:67:89:AB
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB,
        # SPA is 10.0.0.5
        0x0A, 0x00, 0x00, 0x05,
        # THA is 00:01:02:03:04:05
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
        # TPA is 10.0.0.1
        0x0A, 0x00, 0x00, 0x01
    ]

    run_rx_test("arp", rx_bytes, expected_bytes, mac_addr, ip4_addr)


def test_rx_icmp():
    mac_addr = "01:23:45:67:89:AB"
    ip4_addr = "10.0.0.5"

    # Sample ARP request packet
    rx_bytes = [
        # Sent to 01:23:45:67:89:AB from 00:01:02:03:04:05
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
        # Ethertype is IPv4
        0x08, 0x00,
        # IP version 4, IHL 5
        0x45,
        # DSCP class selector 0, no ECN
        0x00,
        # Total length 44
        0, 44,
        # Identification 0x0000
        0x00, 0x00,
        # Flags, fragment 0x0000
        0x00, 0x00,
        # TTL 64
        0x40,
        # Protocol ICMP (1)
        0x01,
        # Checksum 0x100C (not checked at present)
        0x01, 0x0c,
        # Source IP 10.0.0.1
        10, 0, 0, 1,
        # Destination IP 10.0.0.5
        10, 0, 0, 5,
        # ICMP type 8 (ping request)
        0x08,
        # ICMP code 0
        0x00,
        # ICMP checksum 0x023E (not checked)
        0x02, 0x3e,
        # ICMP identifier 0x1234
        0x12, 0x34,
        # ICMP sequence 0xABCD
        0xAB, 0xCD,
        # Some payload bytes
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
    ]

    expected_bytes = [
        # Sent to 00:01:02:03:04:05 from 01:23:45:67:89:AB
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB,
        # Ethertype is IPv4
        0x08, 0x00,
        # IP version 4, IHL 5
        0x45,
        # DSCP class selector 0, no ECN
        0x00,
        # Total length 44
        0, 44,
        # Identification 0x0000
        0x00, 0x00,
        # Flags, fragment 0x0000
        0x00, 0x00,
        # TTL 64
        0x40,
        # Protocol ICMP (1)
        0x01,
        # Checksum 0x66CC
        0x66, 0xCC,
        # Source IP 10.0.0.5
        10, 0, 0, 5,
        # Destination IP 10.0.0.1
        10, 0, 0, 1,
        # ICMP type 0 (ping response)
        0x00,
        # ICMP code 0
        0x00,
        # ICMP checksum 0x09BE
        0x09, 0xBE,
        # ICMP identifier 0x1234
        0x12, 0x34,
        # ICMP sequence 0xABCD
        0xAB, 0xCD,
        # Some payload bytes
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
    ]

    run_rx_test("icmp", rx_bytes, expected_bytes, mac_addr, ip4_addr)
