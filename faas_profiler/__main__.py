#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Entrypoints
"""

import sys
import logging
import argparse

from fire import Fire

from faas_profiler import CLI

from faas_profiler.server import fp_server

def cli():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.info("Starting FaaS-Profiler CLI.")
    Fire(CLI)

def server():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.info("Starting FaaS-Profiler Server.")
    fp_server.run(host="0.0.0.0", port=80)

if __name__ == "__main__":
    cli()