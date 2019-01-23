import argparse

from .platform import SensorPlatform, SwitchPlatform
from .top import SensorTop, SwitchTop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device", choices=["switch", "sensor"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--verilog", action="store_true")
    args = parser.parse_args()
    if args.device == "switch":
        plat = SwitchPlatform(args)
        top = SwitchTop(plat, args)
    elif args.device == "sensor":
        plat = SensorPlatform(args)
        top = SensorTop(plat, args)
    frag = top.get_fragment(plat)
    plat.build(frag, args.device, "build/", freq=100, emit_v=args.verilog,
               seed=args.seed)
