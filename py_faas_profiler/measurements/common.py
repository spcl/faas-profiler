#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for common measurements:
- WallTime
"""

from time import time
from typing import Type

from py_faas_profiler.measurements.base import ParallelMeasurement, register_with_name
from py_faas_profiler.config import ProfileContext


@register_with_name("Common::WallTime")
class WallTime(ParallelMeasurement):
    """
    Measures the execution time of the function using the Python standard time library.

    The measurement runs in the same process as the function.
    """

    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
        self.start_time: float = None
        self.end_time: float = None

        self._results = {}

    def start(self) -> None:
        self.start_time = time()

    def stop(self) -> None:
        self.end_time = time()

    def tearDown(self):
        self._results = {"wallTime": self.end_time - self.start_time}

        del self.start_time
        del self.end_time

    def results(self) -> dict:
        return self._results
