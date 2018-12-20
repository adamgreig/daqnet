"""
Ethernet IP stack

Copyright 2018 Adam Greig
"""

from migen import (Module, Signal, If, FSM, NextValue, NextState, Memory,
                   Constant)


class IPStack(Module):
    """
    Ethernet IP stack.

    Handles responding to ARP and ICMP Ping requests, and transmitting and
    receiving UDP data packets into BRAMs.

    Parameters:
        * `ip4_addr`: IPv4 address in standard xxx.xxx.xxx.xxx format
        * `mac_addr`: MAC address in standard XX:XX:XX:XX:XX:XX format

    Ports:
        * `rx_port`: Read port into RX packet memory (supply from MAC)
        * `tx_port`: Write port into TX packet memory (supply from MAC)

    Inputs:
        * `rx_valid`: Assert to signal a valid packet in RX memory
        * `rx_len`: Received packet length. Valid while `rx_valid` asserted.
        * `tx_ready`: Assert while ready to load a new packet into TX memory

    Outputs:
        * `rx_ack`: Asserted to acknowledge reception of packet
        * `tx_start`: Asserted when a packet is in TX memory ready to send
        * `tx_len`: 11-bit length of packet to transmit
    """
    def __init__(self, ip4_addr, mac_addr, rx_port, tx_port):
        # Inputs
        self.rx_valid = Signal()
        self.rx_len = Signal(11)
        self.tx_ready = Signal()

        # Outputs
        self.rx_ack = Signal()
        self.tx_start = Signal()
        self.tx_len = Signal(11)

        ###

        self.ip4_addr = [int(x, 10) for x in ip4_addr.split(".")]
        self.mac_addr = [int(x, 16) for x in mac_addr.split(":")]
        self.ip4_addr_int = sum(self.ip4_addr[3-x] << (8*x) for x in range(4))
        self.mac_addr_int = sum(self.mac_addr[5-x] << (8*x) for x in range(6))

        self.rx_dst_mac_addr = Signal(48)
        self.rx_src_mac_addr = Signal(48)
        self.rx_ethertype = Signal(16)

        # Protocol handling submodules
        self.submodules.arp = ProtocolARP(self)
        self.submodules.ipv4 = ProtocolIPv4(self)

        self.comb += [
            self.arp.rx_port_dat_r.eq(rx_port.dat_r),
        ]

        self.submodules.fsm = FSM(reset_state="IDLE")

        # Wait for rx_valid
        self.fsm.act(
            "IDLE",
            NextValue(self.rx_ack, 0),
            rx_port.adr.eq(0),
            If(self.rx_valid, NextState("RX_DST_ADDR_0")),
        )

        # Read destination MAC address into rx_dst_mac_addr
        fsm_read(self.fsm, "RX_DST_ADDR", 6, "RX_SRC_ADDR_0",
                 self.rx_dst_mac_addr, rx_port.dat_r, rx_port.adr, 0)

        # Read source MAC address into rx_dst_mac_addr
        fsm_read(self.fsm, "RX_SRC_ADDR", 6, "RX_ETYPE_0",
                 self.rx_src_mac_addr, rx_port.dat_r, rx_port.adr, 6)

        # Read ethertype into rx_ethertype
        fsm_read(self.fsm, "RX_ETYPE", 2, "RX_SWITCH",
                 self.rx_ethertype, rx_port.dat_r, rx_port.adr, 12)

        # Jump based on received ethertype
        self.fsm.act(
            "RX_SWITCH",
            rx_port.adr.eq(14),
            If(
                self.rx_ethertype == 0x0806,
                NextState("RX_ARP")
            ).Elif(
                self.rx_ethertype == 0x0800,
                NextState("RX_IPV4"),
            ).Else(
                NextValue(self.rx_ack, 1),
                NextState("IDLE"),
            )
        )

        # Handle received ARP packets
        self.fsm.act(
            "RX_ARP",
            rx_port.adr.eq(self.arp.rx_port_adr),
            tx_port.adr.eq(self.arp.tx_port_adr),
            tx_port.dat_w.eq(self.arp.tx_port_dat_w),
            tx_port.we.eq(self.arp.tx_port_we),
            self.tx_start.eq(self.arp.tx_start),
            self.tx_len.eq(self.arp.tx_len),
            self.arp.run.eq(1),
            If(
                self.arp.done,
                NextState("RX_DONE"),
            )
        )

        # Handle received IPv4 packets
        self.fsm.act(
            "RX_IPV4",
            NextState("RX_DONE"),
        )

        self.fsm.act(
            "RX_DONE",
            NextValue(self.rx_ack, 1),
            NextState("IDLE"),
        )


class ProtocolARP(Module):
    def __init__(self, ipstack):
        # Inputs
        self.run = Signal()
        self.rx_port_dat_r = Signal(8)

        # Outputs
        self.rx_port_adr = Signal(11)
        self.tx_port_adr = Signal(11)
        self.tx_port_dat_w = Signal(8)
        self.tx_port_we = Signal()
        self.tx_start = Signal()
        self.tx_len = Signal(11)
        self.done = Signal()

        ###

        arp_etype = Constant(0x0806, 16)
        arp_htype = Constant(1, 16)
        arp_ptype = Constant(0x0800, 16)
        arp_hlen = Constant(6, 8)
        arp_plen = Constant(4, 8)
        arp_oper_reply = Constant(2, 16)

        # Decoded fields
        self.rx_arp_htype = Signal(16)
        self.rx_arp_ptype = Signal(16)
        self.rx_arp_hlen = Signal(8)
        self.rx_arp_plen = Signal(8)
        self.rx_arp_oper = Signal(16)
        self.rx_arp_sha = Signal(48)
        self.rx_arp_spa = Signal(32)
        self.rx_arp_tpa = Signal(32)

        self.submodules.fsm = FSM(reset_state="IDLE")

        self.fsm.act(
            "IDLE",
            self.done.eq(0),
            self.tx_start.eq(0),
            self.rx_port_adr.eq(14),
            If(self.run, NextState("RX_HTYPE_0")),
        )

        fsm_read(self.fsm, "RX_HTYPE", 2, "RX_PTYPE_0", self.rx_arp_htype,
                 self.rx_port_dat_r, self.rx_port_adr, 14)
        fsm_read(self.fsm, "RX_PTYPE", 2, "RX_HLEN_0", self.rx_arp_ptype,
                 self.rx_port_dat_r, self.rx_port_adr, 16)
        fsm_read(self.fsm, "RX_HLEN", 1, "RX_PLEN_0", self.rx_arp_hlen,
                 self.rx_port_dat_r, self.rx_port_adr, 18)
        fsm_read(self.fsm, "RX_PLEN", 1, "RX_OPER_0", self.rx_arp_plen,
                 self.rx_port_dat_r, self.rx_port_adr, 19)
        fsm_read(self.fsm, "RX_OPER", 2, "RX_SHA_0", self.rx_arp_oper,
                 self.rx_port_dat_r, self.rx_port_adr, 20)
        fsm_read(self.fsm, "RX_SHA", 6, "RX_SPA_0", self.rx_arp_sha,
                 self.rx_port_dat_r, self.rx_port_adr, 22)
        fsm_read(self.fsm, "RX_SPA", 4, "RX_SKIP_THA", self.rx_arp_spa,
                 self.rx_port_dat_r, self.rx_port_adr, 28)
        fsm_read(self.fsm, "RX_TPA", 4, "MATCH", self.rx_arp_tpa,
                 self.rx_port_dat_r, self.rx_port_adr, 38)

        self.fsm.act(
            "RX_SKIP_THA",
            self.rx_port_adr.eq(38),
            NextState("RX_TPA_0"),
        )

        self.fsm.act(
            "MATCH",
            If(
                (self.rx_arp_ptype == 0x0800) &
                (self.rx_arp_oper == 1) &
                (self.rx_arp_tpa == ipstack.ip4_addr_int),
                NextState("TX_DST_ADDR_0"),
            ).Else(
                NextState("DONE"),
            )
        )

        fsm_write(self.fsm, "TX_DST_ADDR", 6, "TX_SRC_ADDR_0",
                  self.rx_arp_sha, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 0)
        fsm_write(self.fsm, "TX_SRC_ADDR", 6, "TX_ETYPE_0",
                  Constant(ipstack.mac_addr_int, 48), self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 6)
        fsm_write(self.fsm, "TX_ETYPE", 2, "TX_HTYPE_0",
                  arp_etype, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 12)
        fsm_write(self.fsm, "TX_HTYPE", 2, "TX_PTYPE_0",
                  arp_htype, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 14)
        fsm_write(self.fsm, "TX_PTYPE", 2, "TX_HLEN_0",
                  arp_ptype, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 16)
        fsm_write(self.fsm, "TX_HLEN", 1, "TX_PLEN_0",
                  arp_hlen, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 18)
        fsm_write(self.fsm, "TX_PLEN", 1, "TX_OPER_0",
                  arp_plen, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 19)
        fsm_write(self.fsm, "TX_OPER", 2, "TX_SHA_0",
                  arp_oper_reply, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 20)
        fsm_write(self.fsm, "TX_SHA", 6, "TX_SPA_0",
                  Constant(ipstack.mac_addr_int, 48), self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 22)
        fsm_write(self.fsm, "TX_SPA", 4, "TX_THA_0",
                  Constant(ipstack.ip4_addr_int, 32), self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 28)
        fsm_write(self.fsm, "TX_THA", 6, "TX_TPA_0",
                  self.rx_arp_sha, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 32)
        fsm_write(self.fsm, "TX_TPA", 4, "TX_DONE",
                  self.rx_arp_spa, self.tx_port_dat_w,
                  self.tx_port_we, self.tx_port_adr, 38)

        self.fsm.act(
            "TX_DONE",
            self.tx_start.eq(1),
            self.tx_len.eq(42),
            self.done.eq(1),
            NextState("IDLE"),
        )

        self.fsm.act(
            "DONE",
            self.done.eq(1),
            NextState("IDLE"),
        )


class ProtocolIPv4(Module):
    def __init__(self, ipstack):
        self.rx_ihl = Signal(4)
        self.rx_total_len = Signal(16)
        self.rx_proto = Signal(8)
        self.rx_hdr_chk = Signal(16)
        self.rx_src_addr = Signal(32)
        self.rx_dst_addr = Signal(32)
        self.submodules.icmp = ProtocolICMP(ipstack, self)
        self.submodules.udp = ProtocolUDP(ipstack, self)


class ProtocolICMP(Module):
    def __init__(self, ipstack, ipv4):
        self.rx_type = Signal(8)
        self.rx_code = Signal(8)
        self.rx_check = Signal(16)
        self.rx_ident = Signal(16)
        self.rx_seq = Signal(16)


class ProtocolUDP(Module):
    def __init__(self, ipstack, ipv4):
        self.rx_src_port = Signal(16)
        self.rx_dst_port = Signal(16)
        self.rx_len = Signal(16)
        self.rx_chk = Signal(16)


def fsm_read(fsm, name, nbytes, next_state, dst, src, adr, offset):
    """
    Creates a sequence of states to read from a byte-memory into a Signal.

        * `fsm`: The FSM to add states to
        * `name`: The name prefix for the states
        * `nbytes`: The number of bytes to read
        * `next_state`: The state to enter once complete
        * `dst`: The Signal to read into
        * `src`: The byte-wide Signal to read from (e.g. `port.dat_r`)
        * `adr`: The address signal to write (e.g. `port.adr`)
        * `offset`: The offset to add to `adr` (the start offset of the field)
    """
    for idx in range(0, nbytes):
        ns = f"{name}_{idx+1}" if idx < (nbytes - 1) else next_state
        ridx = nbytes - 1 - idx
        fsm.act(
            f"{name}_{idx}",
            NextValue(dst[ridx*8:(ridx+1)*8], src),
            adr.eq(idx + offset + 1),
            NextState(ns),
        )


def fsm_write(fsm, name, nbytes, next_state, src, dst, we, adr, offset):
    """
    Creates a sequence of states to write from a Signal to a byte-memory.

        * `fsm`: The FSM to add states to
        * `name`: The name prefix for the states
        * `nbytes`: The number of bytes to write
        * `next_state`: The state to enter once complete
        * `src`: The Signal to read from
        * `dst`: The byte-wide Signal to write to (e.g. `port.dat_w`)
        * `we`: Write-enable line for the memory (asserted to 1 in all states)
        * `adr`: The address signal to write (e.g. `port.adr`)
        * `offset`: The offset to add to `adr` (the start offset of the field)
    """
    for idx in range(0, nbytes):
        ns = f"{name}_{idx+1}" if idx < (nbytes - 1) else next_state
        ridx = nbytes - 1 - idx
        fsm.act(
            f"{name}_{idx}",
            we.eq(1),
            dst.eq(src[ridx*8:(ridx+1)*8]),
            adr.eq(idx + offset),
            NextState(ns),
        )


def test_rx_arp():
    from migen.sim import run_simulation

    mac_addr = "01:23:45:67:89:AB"
    ip4_addr = "10.0.0.5"

    # Sample ARP request packet
    rx_bytes = [
        # Sent to 01:23:45:67:89:AB from 00:01:02:03:04:05
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
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
        # Sent to 00:01:02:03:04:05 from 01:23:45:67:89:AB
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB,
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

    rx_mem = Memory(8, 64, rx_bytes)
    rx_mem_port = rx_mem.get_port()
    tx_mem = Memory(8, 64)
    tx_mem_port = tx_mem.get_port(write_capable=True)

    ipstack = IPStack(ip4_addr, mac_addr, rx_mem_port, tx_mem_port)
    ipstack.specials += [rx_mem, rx_mem_port, tx_mem, tx_mem_port]

    def testbench():
        for _ in range(10):
            yield

        yield ipstack.rx_valid.eq(1)
        yield
        yield ipstack.rx_valid.eq(0)

        for _ in range(128):
            yield

        tx_bytes = []
        for idx in range(64):
            tx_bytes.append((yield tx_mem[idx]))
        assert tx_bytes[:42] == expected_bytes

    run_simulation(ipstack, testbench(), vcd_name="ipstack_rx_arp.vcd")
