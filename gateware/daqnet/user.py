from nmigen import Elaboratable, Module, Signal, Memory


class User(Elaboratable):
    def __init__(self):
        self.user_rx_mem = Memory(8, 32)
        self.user_tx_mem = Memory(8, 32,
                                  [ord(x) for x in "Hello, World!!\r\n"])
        self.mem_r_port = self.user_tx_mem.read_port()
        self.mem_w_port = self.user_rx_mem.write_port()
        self.packet_received = Signal()
        self.transmit_ready = Signal()
        self.transmit_packet = Signal()

    def elaborate(self, platform):
        m = Module()
        rx_port = self.user_rx_mem.read_port()
        tx_port = self.user_tx_mem.write_port()

        m.submodules += [self.mem_r_port, self.mem_w_port, rx_port, tx_port]

        led1 = platform.request("user_led_1")
        led2 = platform.request("user_led_2")

        m.d.comb += [
            tx_port.addr.eq(0),
            tx_port.en.eq(0),
            tx_port.data.eq(0),
            rx_port.addr.eq(0),
        ]

        m.d.sync += [
            led1.eq(rx_port.data & 1),
            led2.eq((rx_port.data & 2) >> 1),
        ]

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += self.transmit_packet.eq(0)
                with m.If(self.packet_received):
                    m.next = "RX"
            with m.State("RX"):
                with m.If(self.transmit_ready):
                    m.d.sync += self.transmit_packet.eq(1)
                    m.next = "IDLE"

        return m
