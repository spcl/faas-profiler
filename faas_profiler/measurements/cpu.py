#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for all CPU related measurements
"""

import psutil

from faas_profiler.measurements import Measurement, MeasuringPoint, Schema


class CPUUsage(Measurement):

    schema = Schema({
        "measuring_points": list
    })
    name = "CPU Usage"

    def __init__(self, include_children=False) -> None:
        self.process = None
        self.cpu_usage = []

        self.include_children = include_children

    def on_start(self, pid: int, timestamp: float) -> None:
        self.process = psutil.Process(pid)
        self.cpu_usage = [
            MeasuringPoint(
                timestamp,
                self._get_cpu_percentage())]

    def on_stop(self, pid: int, timestamp: float) -> None:
        self.process = None

    def sample_measure(self, timestamp: float) -> None:
        self.cpu_usage.append(MeasuringPoint(
            timestamp=timestamp,
            value=self._get_cpu_percentage()))

    @property
    def results(self) -> dict:
        return self.schema.validate({
            "measuring_points": self.cpu_usage
        })

    def _get_cpu_percentage(self):
        try:
            percent = self.process.cpu_percent()

            if self.include_children:
                try:
                    for child_process in self.process.children(recursive=True):
                        percent += child_process.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return percent
        except psutil.AccessDenied:
            return -1
