#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for common measurements:
- ExecutionTime
"""

from time import time
from typing import TYPE_CHECKING, Type
from py_faas_profiler.measurements.base import Measurement, ParallelMeasurement
from py_faas_profiler.config import ProfileContext


@Measurement.register("Common::ExecutionTime")
class ExecutionTime(ParallelMeasurement):
    """
    Measures the execution time of the function using the Python standard time library.

    The measurement runs in the same process as the function.
    """

    def setUp(
            self,
            profiler_context: Type[ProfileContext],
            config: dict = {}) -> None:
        self.start_time: float = None
        self.end_time: float = None

    def start(self) -> None:
        self.start_time = time()

    def stop(self) -> None:
        self.end_time = time()

    def tearDown(self):
        self.start_time: float = None
        self.end_time: float = None


@Measurement.register("Common::S3Capture")
class S3Capture(Measurement):
    pass
