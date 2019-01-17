import argparse

from .platform import SensorPlatform, SwitchPlatform
from .top import SensorTop, SwitchTop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device", choices=["switch", "sensor"])
    args = parser.parse_args()
    if args.device == "switch":
        plat = SwitchPlatform(args)
        top = SwitchTop(plat, args)
    elif args.device == "sensor":
        plat = SensorPlatform(args)
        top = SensorTop(plat, args)
    frag = top.get_fragment(plat)
    plat.build(frag, args.device, "build/", freq=50)
