#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaaS-Profiler for python package
"""

from .measurements import *
from .profiler import *
from .config import *
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


del logging
del sys
