import argparse
from .platform import BlackIcePlatform, ProtoSensorPlatform
from .top import BlackIceTop, ProtoSensorTop


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action='store_true')
    parser.add_argument("--program", action='store_true')
    return parser.parse_args()


def main():
    args = get_args()
    # plat = ProtoSensorPlatform()
    # top = ProtoSensorTop(plat)
    plat = BlackIcePlatform()
    top = BlackIceTop(plat)
    if args.build:
        plat.build(top)
    if args.program:
        prog = plat.create_programmer()
        prog.load_bitstream("build/top.bin")
