#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler Main
"""

from fire import Fire
from faas_profiler import Commands

def main():
    Fire(Commands())

if __name__ == "__main__":
    main()