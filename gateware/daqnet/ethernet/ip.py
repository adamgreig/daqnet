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
            self.tx_len.eq(42),
            self.tx_offset.eq(0),
            self.rx_port.addr.eq(self.rx_addr),
            self.tx_port.addr.eq(eth.tx_addr + self.tx_offset),
            self.tx_port.data.eq(eth.tx_data),
            self.tx_port.en.eq(eth.tx_en),
        ]

        m.d.sync += [
            eth.rx_data.eq(self.rx_port.data),
        ]

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += self.rx_addr.eq(self.rx_offset),
                m.d.sync += self.tx_start.eq(0)
                with m.If(self.rx_valid):
                    m.d.sync += [
                        self.rx_ack.eq(1),
                    ]
                    m.next = "REPLY"

            with m.State("REPLY"):
                m.d.sync += self.rx_addr.eq(self.rx_addr + 1),
                m.d.sync += eth.run.eq(~eth.done)
                m.d.sync += self.rx_ack.eq(0)
                with m.If(eth.done):
                    with m.If(eth.send):
                        m.d.sync += self.tx_start.eq(1)
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
    """
    def __init__(self, ip_stack):
        self.run = Signal()
        self.done = Signal()
        self.send = Signal()
        self.rx_data = Signal(8)
        self.tx_en = Signal()
        self.tx_addr = Signal(11)
        self.tx_data = Signal(8)

        self.send_at_end = Signal()
        self.ip_stack = ip_stack

    def start_fsm(self):
        """
        Call to generate first FSM state.
        """
        self._fsm_ctr = 0
        with self.m.State("IDLE"):
            self.m.d.sync += self.send_at_end.eq(0)
            self.m.d.sync += self.tx_en.eq(0)
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
                                self.m.d.sync += self.send_at_end.eq(1)
                            with self.m.Else():
                                self.m.next = "DONE_NO_TX"
                with self.m.Case():
                    self.m.next = "DONE_NO_TX"

        self._fsm_ctr += 1

    def end_fsm(self, send=False):
        """
        Call to generate final FSM state. Set `send` True if a response
        packet should be sent.
        """
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
            if send:
                self.m.next = "DONE_TX"
            else:
                with self.m.If(self.send_at_end):
                    self.m.next = "DONE_TX"
                with self.m.Else():
                    self.m.next = "DONE_NO_TX"


class _EthernetLayer(_StackLayer):
    """
    Implements top-level Ethernet handling.

    Muxes to lower levels depending on packet EtherType.
    """
    def get_fragment(self, platform):
        self.m = Module()
        self.m.submodules.arp = arp = _ARPLayer(self.ip_stack)
        # self.m.submodules.ipv4 = ipv4 = _IPv4Layer(self.ip_stack)

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
                # 0x0800: ipv4,
            })

            # If we need to transmit, fill in the Ethernet source and ethertype
            self.write("SRC", val=self.ip_stack.mac_addr_int, dst=6, n=6)
            self.write("ETYPE", val=ethertype, dst=12, n=2)

            self.end_fsm()

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

            # Read incoming packet, checking copying relevant fields as we go.
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
            self.end_fsm(send=True)

        return self.m.lower(platform)


class _IPv4Layer(_StackLayer):
    """
    Implements a simple IPv4 layer.
    """
    def get_fragment(self, platform):
        self.m = Module()
        return self.m.lower(platform)


class _ICMPv4Layer(_StackLayer):
    """
    Implements a simple ICMPv4 layer.

    Replies to echo requests only.
    """


class _UDPLayer(_StackLayer):
    """
    Implements a simple UDP layer.
    """


def run_rx_test(name, rx_bytes, expected_bytes, mac_addr, ip4_addr):
    from nmigen.back import pysim

    rx_mem = Memory(8, 64, [0]*4 + rx_bytes)
    rx_mem_port = rx_mem.read_port()
    tx_mem = Memory(8, 64)
    tx_mem_port = tx_mem.write_port()

    ipstack = IPStack(mac_addr, ip4_addr, rx_mem_port, tx_mem_port)

    def testbench():
        for _ in range(2):
            yield

        yield ipstack.rx_offset.eq(4)
        yield ipstack.rx_valid.eq(1)
        yield
        yield ipstack.rx_valid.eq(0)

        for _ in range(128):
            yield

        tx_bytes = []
        for idx in range(64):
            tx_bytes.append((yield tx_mem[idx]))

        if expected_bytes is not None:
            # Check transmit got asserted with valid tx_len, tx_offset
            print("Received:", " ".join(
                f"{x:02X}" for x in tx_bytes[:len(expected_bytes)]))
            print("Expected:", " ".join(
                f"{x:02X}" for x in expected_bytes))
            assert tx_bytes[:len(expected_bytes)] == expected_bytes
        else:
            # Check transmit did not get asserted
            pass

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
        # DSCP class selector 2, no ECN
        0x40,
        # Total length 44
        0, 44,
        # Identification 0x3456
        0x34, 0x56,
        # Flags, fragment 0x0000
        0x00, 0x00,
        # TTL 64
        0x40,
        # Protocol ICMP (1)
        0x01,
        # Checksum 0x0000 (not checked at present)
        0x00, 0x00,
        # Source IP 10.0.0.1
        10, 0, 0, 1,
        # Destination IP 10.0.0.5
        10, 0, 0, 5,
        # ICMP type 8 (ping request)
        0x08,
        # ICMP code 0
        0x00,
        # ICMP checksum 0x0000 (not checked)
        0x00, 0x00,
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
        # DSCP class selector 2, no ECN
        0x40,
        # Total length 44
        0, 44,
        # Identification 0x3456
        0x34, 0x56,
        # Flags, fragment 0x0000
        0x00, 0x00,
        # TTL 64
        0x40,
        # Protocol ICMP (1)
        0x01,
        # Checksum 0x0000 (not checked at present)
        0x00, 0x00,
        # Source IP 10.0.0.5
        10, 0, 0, 5,
        # Destination IP 10.0.0.1
        10, 0, 0, 1,
        # ICMP type 0 (ping response)
        0x00,
        # ICMP code 0
        0x00,
        # ICMP checksum 0x0000 (not checked)
        0x00, 0x00,
        # ICMP identifier 0x1234
        0x12, 0x34,
        # ICMP sequence 0xABCD
        0xAB, 0xCD,
        # Some payload bytes
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
    ]

    run_rx_test("icmp", rx_bytes, expected_bytes, mac_addr, ip4_addr)
