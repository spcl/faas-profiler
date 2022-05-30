#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for all disk related measurements
"""

from typing import List
import psutil

from faas_profiler.measurements import Measurement, MeasuringPoint, Schema


class DiskIOCounters(Measurement):
    schema = Schema({
        "io_counters": dict
    })
    name = "Disk IO Counters"

    def __init__(self) -> None:
        self.start_snapshot = None
        self.io_counters_delta = {}

    def on_start(self, pid: int, timestamp: float) -> None:
        self.io_counters_delta = {}
        self.start_snapshot = psutil.disk_io_counters(perdisk=True)

    def on_stop(self, pid: int, timestamp: float) -> None:
        end_snapshot = psutil.disk_io_counters(perdisk=True)

        def io_counters_delta(start_counters, end_counters): return {
            "read_count": end_counters.read_count - start_counters.read_count,
            "write_count": end_counters.write_count - start_counters.write_count,
            "read_bytes": end_counters.read_bytes - start_counters.read_bytes,
            "write_bytes": end_counters.write_bytes - start_counters.write_bytes,
            "read_time": end_counters.read_time - start_counters.read_time,
            "write_time": end_counters.write_time - start_counters.write_time}

        self.io_counters_delta = {
            disk: io_counters_delta(
                self.start_snapshot[disk],
                end_counters) for disk,
            end_counters in end_snapshot.items()}

    def sample_measure(self, timestamp: float) -> None:
        pass

    @property
    def results(self) -> dict:
        return self.schema.validate({
            "io_counters": self.io_counters_delta
        })


class DiskUsage(Measurement):
    schema = Schema([{
        "path": str,
        "total": float,
        "used": float,
        "free": float,
        "percent": float
    }])
    name = "Disk Usage"

    def __init__(self, paths: List[str] = [
                 "/Users/maltewae/src/github.com/spcl/faas-profiler/examples/custom/"]) -> None:
        self.paths = paths

        self.start_snapshots = {}
        self.end_snapshots = {}

    def on_start(self, pid: int, timestamp: float) -> None:
        self.end_snapshots = {}
        try:
            self.start_snapshot = {
                p: psutil.disk_usage(p) for p in self.paths
            }
        except OSError:
            self.start_snapshot = {}

    def on_stop(self, pid: int, timestamp: float) -> None:
        try:
            self.end_snapshots = {
                p: psutil.disk_usage(p) for p in self.paths
            }
        except OSError:
            self.end_snapshots = {}

    def sample_measure(self, timestamp: float) -> None:
        pass

    @property
    def results(self) -> dict:
        return self.schema.validate([
            {
                "path": path,
                "total": float(end_snapshot.total - self.start_snapshot[path].total),
                "used": float(end_snapshot.used - self.start_snapshot[path].used),
                "free": float(end_snapshot.free - self.start_snapshot[path].free),
                "percent": float(end_snapshot.percent - self.start_snapshot[path].percent)
            } for path, end_snapshot in self.end_snapshots.items()
        ])
