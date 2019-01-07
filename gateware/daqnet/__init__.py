import argparse

from nmigen.back import rtlil, verilog

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
    with open(f"build/{args.device}.pcf", "w") as f:
        f.write(plat.pcf)
    frag = top.get_fragment(plat)
    with open(f"build/{args.device}.il", "w") as f:
        f.write(rtlil.convert(frag, name=args.device))
    with open(f"build/{args.device}.v", "w") as f:
        f.write(verilog.convert(frag, name=args.device))
