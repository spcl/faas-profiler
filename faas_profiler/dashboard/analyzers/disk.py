#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_core_components as dcc

from typing import Type
from dash import html

from faas_profiler_core.models import DiskIOCounters
from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler_core.models import RecordData


class DiskIOAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = DiskIOCounters.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for Disk IO
        """
        return "Disk IO Counters"

    def render(self):
        """
        Returns a bar chart for all Disk IO Counters
        """
        bytes_fig = go.Figure([go.Bar(
            x=["Bytes read (MB)", "Bytes write (MB)"],
            y=[self.results.read_bytes * 1e-6, self.results.write_bytes * 1e-6]
        )])

        counts_fig = go.Figure([go.Bar(
            x=["Read count", "Write count"],
            y=[self.results.read_bytes, self.results.write_bytes]
        )])

        return html.Div(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=bytes_fig)),
                    dbc.Col(dcc.Graph(figure=counts_fig))
                ]
            ))