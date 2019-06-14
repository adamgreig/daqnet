import argparse
import subprocess

from .platform import SensorPlatform, SwitchPlatform
from .top import SensorTop, SwitchTop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device", choices=["switch", "sensor"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--verilog", action="store_true")
    parser.add_argument("--program", action="store_true")
    parser.add_argument("--flash", action="store_true")
    args = parser.parse_args()
    if args.device == "switch":
        plat = SwitchPlatform()
        top = SwitchTop(plat, args)
    elif args.device == "sensor":
        plat = SensorPlatform()
        top = SensorTop(plat, args)
    plat.build(top, args.device, "build/", synth_opts=["-relut"],
               nextpnr_opts=["--seed", args.seed, "--freq", 100,
                             "--placer", "heap"])
    if args.program:
        subprocess.run(
            ["ffp", "fpga", "program", "build/{}.bin".format(args.device)])
    if args.flash:
        subprocess.run(
            ["ffp", "flash", "program", "build/{}.bin".format(args.device)])
