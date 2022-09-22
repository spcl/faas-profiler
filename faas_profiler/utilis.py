#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utitils module
"""

import logging


def seconds_to_ms(sec: float) -> float:
    """
    Seconds to ms
    """
    return sec * 1e4

def bytes_to_kb(bytes: float) -> float:
    """
    Bytes to KB
    """
    return bytes * 1e-3

class Loggable:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
