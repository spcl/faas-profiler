#!/usr/bin/env python3
"""
Install routine for FaaS-Profiler
"""

import argparse
import os
import subprocess


def run_command(cmd, cwd=None):
    ret = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        cwd=cwd)
    if ret.returncode:
        raise RuntimeError(
            "Running {} failed!\n Output: {}".format(
                cmd, ret.stdout.decode("utf-8")))
    return ret.stdout.decode("utf-8")


DEFAULT_VENV = ".faas-profiler-venv"

parser = argparse.ArgumentParser(description="Install FaaS-Profiler")

parser.add_argument(
    '--venv',
    metavar='DIR',
    type=str,
    default=DEFAULT_VENV,
    help='destination of Python virtual environment')

args = parser.parse_args()

if not os.path.exists(args.venv):
    print(f"Creating Python environment at {args.venv}...")
    run_command(f"python -mvenv {args.venv}")
else:
    print(f"Using Python environment at {args.venv}.")

print("Upgrade pip")
run_command(f"source {args.venv}/bin/activate && pip3 install --upgrade pip")

print("Install production requirements")
run_command(
    f"source {args.venv}/bin/activate && pip3 install -r requirements.txt --upgrade")

print("Install FaaS-Profiler")
run_command(f"source {args.venv}/bin/activate && pip3 install -e .")
