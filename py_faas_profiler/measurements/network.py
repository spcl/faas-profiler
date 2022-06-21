#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for network measurements:
- NetworkConnections
- NetworkIOCounters
"""

import logging
import psutil

from typing import List, Set, Type
from functools import reduce

from py_faas_profiler.measurements.base import PeriodicMeasurement, register_with_name
from py_faas_profiler.config import ProfileContext


@register_with_name("Network::Connections")
class Connections(PeriodicMeasurement):

    _logger = logging.getLogger("Network::Connections")
    _logger.setLevel(logging.INFO)

    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
        self.process = None
        self.connections: List[psutil._common.pconn] = []
        self.socket_descriptors: Set[int] = set()

        self._results = {}

        try:
            self.process = psutil.Process(profiler_context.pid)
        except psutil.Error as err:
            self._logger.warn(f"Could not set process: {err}")

    def start(self):
        self._update_connection()

    def measure(self):
        self._update_connection()

    def tearDown(self) -> None:

        self._results = {"connections": [{
            "socket_descriptor": conn.fd,
            "family": str(conn.family),
            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
        } for conn in self.connections]}

        del self.process
        del self.connections
        del self.socket_descriptors

    def _update_connection(self):
        if self.process is None:
            return

        for conn in self.process.connections():
            if conn.fd in self.socket_descriptors:
                return

            self.connections.append(conn)
            self.socket_descriptors.add(conn.fd)

    def results(self) -> dict:
        return self._results


@register_with_name("Network::IOCounters")
class IOCounters(PeriodicMeasurement):
    def setUp(
        self,
        profiler_context: Type[ProfileContext],
        config: dict = {}
    ) -> None:
        self.per_interface = config.get("per_interface", False)

        self.start_snapshot: Type[psutil.snetio] = None
        self.end_snapshot: Type[psutil.snetio] = None

        self._interfaces_counters = []
        self._total_counters = {}

    def start(self) -> None:
        self.start_snapshot = psutil.net_io_counters(pernic=self.per_interface)

    def stop(self) -> None:
        self.end_snapshot = psutil.net_io_counters(pernic=self.per_interface)

    def tearDown(self) -> None:

        self._interfaces_counters = []
        self._total_counters = {}

        if self.per_interface:
            for ifc, end_counters in self.end_snapshot.items():
                start_counters = self.start_snapshot.get(ifc)
                if start_counters:
                    self._interfaces_counters.append({
                        "interface": ifc,
                        **_get_snapshot_net_io_delta(start_counters, end_counters)._asdict()
                    })

            self._total_counters = reduce(lambda a, b: {
                k: v + a.get(k, 0) for k, v in b.items() if k != "interface"
            }, self._interfaces_counters)
        else:
            self._total_counters = _get_snapshot_net_io_delta(
                self.start_snapshot, self.end_snapshot)._asdict()

        del self.start_snapshot
        del self.end_snapshot

    def results(self) -> dict:
        return {
            "interfaces": self._interfaces_counters,
            "total": self._total_counters
        }


def _get_snapshot_net_io_delta(
    start_snapshot: Type[psutil._common.snetio],
    end_snapshot: Type[psutil._common.snetio]
) -> Type[psutil._common.snetio]:
    return psutil._common.snetio(
        bytes_sent=end_snapshot.bytes_sent - start_snapshot.bytes_sent,
        bytes_recv=end_snapshot.bytes_recv - start_snapshot.bytes_recv,
        packets_sent=end_snapshot.packets_sent - start_snapshot.packets_sent,
        packets_recv=end_snapshot.packets_recv - start_snapshot.packets_recv,
        errin=end_snapshot.errin - start_snapshot.errin,
        errout=end_snapshot.errout - start_snapshot.errout,
        dropin=end_snapshot.dropin - start_snapshot.dropin,
        dropout=end_snapshot.dropout - start_snapshot.dropout)
