#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-profiler main module.

Entrypoint for console.
"""

import sys
import logging
from fire import Fire

from faas_profiler import CLI

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.info("Starting FaaS-Profiler CLI.")
    Fire(CLI)
    logging.info("Stopped FaaS-Profiler CLI.")

if __name__ == "__main__":
    main()