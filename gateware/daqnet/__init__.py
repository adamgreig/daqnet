import argparse
import subprocess
from .platform import ProtoSensorPlatform, ProtoSwitchPlatform
from .top import ProtoSensorTop, ProtoSwitchTop


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action='store_true')
    parser.add_argument("--program", action='store_true')
    return parser.parse_args()


def main():
    args = get_args()
    plat = ProtoSwitchPlatform()
    # plat.add_period_constraint('sys', 10)
    top = ProtoSwitchTop(plat)
    if args.build:
        plat.build(top)
    if args.program:
        subprocess.run(["/home/adam/Projects/amp_flashprog/prog.py",
                        "--fpga", "build/top.bin"])
        # prog = plat.create_programmer()
        # prog.load_bitstream("build/top.bin")
