#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for all network related measurements
"""

from typing import List
import psutil

from faas_profiler.measurements import Measurement, Schema


class NetworkIOCounters(Measurement):
    schema = Schema({
        "io_counters": dict
    })
    name = "Network IO Counters"

    def __init__(self) -> None:
        self.start_snapshot = None
        self.io_counters_delta = {}

    def on_start(self, pid: int, timestamp: float) -> None:
        self.io_counters_delta = {}
        self.start_snapshot = psutil.net_io_counters(pernic=True)

    def on_stop(self, pid: int, timestamp: float) -> None:
        end_snapshot = psutil.net_io_counters(pernic=True)

        def io_counters_delta(start_counters, end_counters): return {
            "bytes_sent": end_counters.bytes_sent - start_counters.bytes_sent,
            "bytes_recv": end_counters.bytes_recv - start_counters.bytes_recv,
            "packets_sent": end_counters.packets_sent - start_counters.packets_sent,
            "packets_recv": end_counters.packets_recv - start_counters.packets_recv}

        self.io_counters_delta = {
            interface: io_counters_delta(
                self.start_snapshot[interface],
                end_counters) for interface,
            end_counters in end_snapshot.items()}

    def sample_measure(self, timestamp: float) -> None:
        pass

    @property
    def results(self) -> dict:
        return self.schema.validate({
            "io_counters": self.io_counters_delta
        })


class NetworkConnections(Measurement):
    schema = Schema([{
        "socket_descriptor": int,
        "family": str,
        "type": str,
        "local_address": str,
        "remote_address": str,
        "status": str
    }])
    name = "Network Connections"

    def __init__(self) -> None:
        self.process = None
        self.connections = []

    def on_start(self, pid: int, timestamp: float) -> None:
        self.process = psutil.Process(pid)
        self.connections = self._get_connections()

    def on_stop(self, pid: int, timestamp: float) -> None:
        self.process = None

    def sample_measure(self, timestamp: float) -> None:
        self.connections += self._get_connections()

    def _get_connections(self) -> list:
        connections = []
        for conn in self.process.connections():
            connections.append({
                "socket_descriptor": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
                "status": conn.status
            })

        return connections

    @property
    def results(self) -> dict:
        return self.schema.validate(self.connections)
