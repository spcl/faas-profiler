#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Entrypoints
"""

import sys
import logging

from fire import Fire

from faas_profiler import CLI

def cli():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.info("Starting FaaS-Profiler CLI.")
    Fire(CLI)


if __name__ == "__main__":
    cli()