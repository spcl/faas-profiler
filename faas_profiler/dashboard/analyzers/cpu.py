#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Analyzers
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from typing import Type
from dash import html, dcc

from faas_profiler_core.models import CPUUsage

from faas_profiler.utilis import seconds_to_ms
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData


class CPUUsageAnalyzer(Analyzer):
    requested_data = "cpu::Usage"
    name = "CPU Usage"

    X_AXIS = "Time ({unit})"
    Y_AXIS = "Usage ({unit})"

    def analyze_record(self, record_data: Type[RecordData]):
        """
        Returns a line chart for all recorded memory usages.
        """
        results = CPUUsage.load(record_data.results)

        interval = results.interval
        measuring_points = results.measuring_points

        if len(measuring_points) == 0:
            return html.P("No cpu usages recorded.")

        n = len(measuring_points)
        measuring_points = np.array(measuring_points)
        time_interval = seconds_to_ms(np.arange(0, n * interval, interval))

        data = pd.DataFrame({
            self.X_AXIS.format(unit="ms"): time_interval,
            self.Y_AXIS.format(unit="%"): measuring_points
        })

        fig = px.line(
            data,
            x=self.X_AXIS.format(unit="ms"),
            y=self.Y_AXIS.format(unit="%"),
            title="CPU-Usage")

        fig.add_trace(go.Scatter(
            x=time_interval,
            y=np.repeat(np.mean(measuring_points), n),
            name="Mean",
            line=dict(color="Red", width=2)))

        return html.Div([
            dcc.Graph(figure=fig),
            dbc.Row(
                [
                    dbc.Col([html.B("Number of Measuring Points:"), html.P(n)]),
                    dbc.Col([html.B("Interval:"), html.P(f"{seconds_to_ms(interval)} ms")])
                ]
            )
        ])


# class ProfileCPUUsageAnalyzer(Analyzer):

#     def __init__(self, profile_access: Type[ProfileAccess]):
#         self.profile_access = profile_access
#         self.all_cpu_data = self.profile_access.get_all_record_data(
#             "cpu::Usage")
#         super().__init__()

#     def name(self) -> str:
#         return "Profile CPU Usage"

#     def render(self):
#         fig = go.Figure()
#         for trace, trace_data in self.all_cpu_data.items():
#             fig.add_trace(go.Bar(
#                 x=list(trace_data.keys()),
#                 y=[np.average(f["measuring_points"]) for f in trace_data.values()],
#                 name=str(trace),
#                 xaxis=None
#             ))

#         fig.update_layout(
#             barmode='group',
#             xaxis_visible=False,
#             xaxis_showticklabels=False)

#         return html.Div([
#             dcc.Graph(figure=fig)
#         ])
