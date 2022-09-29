#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utitils module
"""

import logging
import math
from typing import Tuple, Any

TRACE_ID_KEY = "trace_id"
RECORD_ID_KEY = "record_id"

BYTES_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")


def convert_bytes_to_best_unit(
    size_bytes: float
) -> Tuple[float, str]:
    """
    Converts number of bytes to best unit.
    """
    if size_bytes == 0:
        return (size_bytes, "B")

    i = int(math.floor(math.log(size_bytes, 1024)))
    multiplier = 1.0 / math.pow(1024, i)

    return (multiplier, BYTES_UNITS[i])


def seconds_to_ms(sec: float) -> float:
    """
    Seconds to ms
    """
    return sec * 1000


def print_ms(msec: float) -> str:
    return "{:.2f} ms".format(msec)


def time_delta_in_sec(date1, date2) -> float:
    return (date1 - date2).total_seconds()


def bytes_to_kb(bytes: float) -> float:
    """
    Bytes to KB
    """
    return bytes * 1e-3


def detail_link(trace_id="ALL", record_id="ALL") -> str:
    return f"?{TRACE_ID_KEY}={trace_id}&{RECORD_ID_KEY}={record_id}"


def get_idx_safely(arr: list, idx: int, default: Any = None) -> Any:
    try:
        return arr[idx]
    except IndexError:
        return default


def short_uuid(uid) -> str:
    return str(uid)[:8]


class Loggable:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
