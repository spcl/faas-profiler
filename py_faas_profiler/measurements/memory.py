#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for memory measurements:
- Usage
"""

from functools import reduce
import logging
import psutil

from typing import List, Type
from time import time
from dataclasses import asdict

from py_faas_profiler.measurements.base import ParallelMeasurement, register_with_name
from py_faas_profiler.config import ProfileContext, MeasuringPoint, average_measuring_points


@register_with_name("Memory::Usage")
class Usage(ParallelMeasurement):

    _logger = logging.getLogger("Memory::Usage")
    _logger.setLevel(logging.INFO)

    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
        self.include_children = config.get("include_children", True)

        self._own_process_id = profiler_context.measurement_process_pid
        self._measuring_points: List[MeasuringPoint] = []
        self._average_usage = 0

        try:
            self.process = psutil.Process(profiler_context.pid)
        except psutil.Error as err:
            self._logger.warn(f"Could not set process: {err}")

    def start(self) -> None:
        self._append_new_memory_measurement()

    def measure(self):
        self._append_new_memory_measurement()

    def tearDown(self) -> None:
        self._average_usage = average_measuring_points(self._measuring_points)
        del self.process

    def results(self) -> dict:
        return {
            "measuringPoints": list(map(asdict, self._measuring_points)),
            "averageUsage": self._average_usage
        }

    def _append_new_memory_measurement(self):
        current_memory = self._get_memory()
        if current_memory:
            self._measuring_points.append(MeasuringPoint(
                timestamp=time(),
                data=current_memory))

    def _get_memory(self):
        try:
            memory_info = self.process.memory_info()
            memory = memory_info.rss

            if self.include_children:
                try:
                    for child_process in self.process.children(recursive=True):
                        if self._own_process_id is None or child_process.pid != self._own_process_id:
                            child_memory_info = child_process.memory_info()
                            memory += child_memory_info.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return memory
        except psutil.AccessDenied as e:
            self._logger.error(
                f"Could not get process memory info from {self.process}: {e}")

        return None
