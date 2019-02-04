import socket
import struct
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("port")
    parser.add_argument("data")
    return parser.parse_args()


def main():
    args = get_args()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.connect((args.address, int(args.port)))
    s.send(struct.pack("B", int(args.data, 0)) + b"\x00"*15)
    s.close()


if __name__ == "__main__":
    main()
