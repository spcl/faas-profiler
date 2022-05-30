#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for all memory related measurements
"""

import psutil

from faas_profiler.measurements import Measurement, MeasuringPoint, Schema


class MemoryUsage(Measurement):

    schema = Schema({
        "measuring_points": list
    })
    name = "Memory Usage"

    def __init__(self, include_children=False) -> None:
        self.process = None
        self.memory_usage = []

        self.include_children = include_children

    def on_start(self, pid: int, timestamp: float) -> None:
        self.process = psutil.Process(pid)
        self.memory_usage = [MeasuringPoint(timestamp, self._get_memory())]

    def on_stop(self, pid: int, timestamp: float) -> None:
        self.process = None

    def sample_measure(self, timestamp: float) -> None:
        self.memory_usage.append(MeasuringPoint(
            timestamp=timestamp,
            value=self._get_memory()))

    @property
    def results(self) -> dict:
        return self.schema.validate({
            "measuring_points": self.memory_usage
        })

    def _get_memory(self):
        try:
            memory_info = self.process.memory_info()
            memory = memory_info.rss

            if self.include_children:
                try:
                    for child_process in self.process.children(recursive=True):
                        child_memory_info = child_process.memory_info()
                        memory += child_memory_info.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return memory
        except psutil.AccessDenied:
            return -1
