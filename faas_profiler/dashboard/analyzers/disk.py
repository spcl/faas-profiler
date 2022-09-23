#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from plotly.subplots import make_subplots
from typing import Type, Dict
from uuid import UUID
from dash import html, dcc

from faas_profiler_core.models import DiskIOCounters
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData

from faas_profiler.utilis import convert_bytes_to_best_unit


class DiskIOAnalyzer(Analyzer):
    requested_data = "disk::IOCounters"
    name = "Disk IO Counters"

    BYTES_AXIS_READ = "Read in {unit}"
    BYTES_AXIS_WRITE = "Write {unit}"

    COUNT_AXIS_READ = "Count Read"
    COUNT_AXIS_WRITE = "Count Write"

    def analyze_record(self, record_data: Type[RecordData]):
        """

        """
        results = DiskIOCounters.load(record_data.results)

        multiplier, bytes_unit = convert_bytes_to_best_unit(max(
            results.read_bytes, results.write_bytes))

        fig = make_subplots(rows=1, cols=2)

        fig.add_trace(
            go.Bar(
                name="Bytes Read and Written",
                x=[
                    self.BYTES_AXIS_READ.format(unit=bytes_unit),
                    self.BYTES_AXIS_WRITE.format(unit=bytes_unit)],
                y=[
                    results.read_bytes * multiplier,
                    results.write_bytes * multiplier]
            ), row=1, col=1)

        fig.add_trace(
            go.Bar(
                name="Count Read and Write Operations",
                x=[self.COUNT_AXIS_READ, self.COUNT_AXIS_WRITE],
                y=[results.read_count, results.write_count]
            ), row=1, col=2)

        return html.Div(
            dcc.Graph(figure=fig)
        )

    def analyze_profile(self, traces_data: Dict[UUID, Type[RecordData]]):
        return super().analyze_profile(traces_data)
