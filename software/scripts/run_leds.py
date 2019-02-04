import time
import socket
import struct
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("port")
    return parser.parse_args()


def set_leds(s, led1, led2):
    data = int(led1) | (int(led2) << 1)
    s.send(struct.pack("B", data) + b"\x00"*15)


def main():
    args = get_args()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.connect((args.address, int(args.port)))
    while True:
        for x in range(4):
            set_leds(s, x & 1 == 1, x & 2 == 2)
            time.sleep(0.2)


if __name__ == "__main__":
    main()
