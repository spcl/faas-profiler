#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Analyzers
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from typing import Type
from dash import html, dcc

from faas_profiler_core.models import MemoryLineUsage, MemoryUsage

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData

from faas_profiler.utilis import convert_bytes_to_best_unit, seconds_to_ms


class MemoryUsageAnalyzer(Analyzer):
    requested_data = "memory::Usage"
    name = "Memory Usage"

    X_AXIS = "Time ({unit})"
    Y_AXIS = "Usage ({unit})"

    def analyze_record(self, record_data: Type[RecordData]):
        """
        Analzyes CPU usage of one record.
        """
        results = MemoryUsage.load(record_data.results)

        interval = results.interval
        measuring_points = results.measuring_points

        if len(measuring_points) == 0:
            return html.P("No memory usages recorded.")

        n = len(measuring_points)
        measuring_points = np.array(measuring_points)
        peak = np.max(measuring_points)
        multiplier, bytes_unit = convert_bytes_to_best_unit(peak)

        measuring_points = measuring_points * multiplier
        time_interval = seconds_to_ms(np.arange(0, n * interval, interval))

        data = pd.DataFrame({
            self.X_AXIS.format(unit="ms"): time_interval,
            self.Y_AXIS.format(unit=bytes_unit): measuring_points
        })

        fig = px.line(
            data,
            x=self.X_AXIS.format(unit="ms"),
            y=self.Y_AXIS.format(unit=bytes_unit),
            title="Memory-Usage")

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


# class LineMemoryAnalyzer(Analyzer):

#     def __init__(self, record_data: Type[RecordData]):
#         self.record_data = record_data
#         self.record_name = record_data.name
#         self.results = MemoryLineUsage.load(self.record_data.results)

#         super().__init__()

#     def name(self) -> str:
#         """
#         Returns the name for the line analyzer
#         """
#         return "Line Memory Analyzer"

#     def render(self):
#         """
#         Returns a table for all recorded lines.
#         """
#         line_memories = self.results.line_memories
#         if len(line_memories) == 0:
#             return html.P("No memory lines recorded.")

#         table_header = [html.Thead(html.Tr([
#             html.Th("Line Number"),
#             html.Th("Total Memory (MB)"),
#             html.Th("Memory Increment (MB)"),
#             html.Th("Occurrence"),
#             html.Th("Line Content")]))]

#         table_rows = []
#         for memory_line in line_memories:
#             table_rows.append(html.Tr([
#                 html.Td(memory_line.line_number),
#                 html.Td("{:.2f}".format(memory_line.memory_total)),
#                 html.Td("{:.2f}".format(memory_line.memory_increment)),
#                 html.Td(memory_line.occurrences),
#                 html.Td(html.Code(html.Pre(memory_line.content)))]))

#         table_body = [html.Tbody(table_rows)]

#         return dbc.Table(
#             table_header +
#             table_body,
#             borderless=True,
#             bordered=False,
#             color="light")


# class MemoryUsageAnalyzer(Analyzer):

#     def __init__(self, record_data: Type[RecordData]):
#         self.record_data = record_data
#         self.record_name = record_data.name
#         self.results = MemoryUsage.load(self.record_data.results)

#         super().__init__()

#     def name(self) -> str:
#         """
#         Returns the name for the line analyzer
#         """
#         return "Memory Usage"

#     def render(self):
#         """
#         Returns a line chart for all recorded memory usages.
#         """
#         interval = self.results.interval
#         measuring_points = self.results.measuring_points

#         if len(measuring_points) == 0:
#             return html.P("No memory usages recorded.")

#         n = len(measuring_points)
#         measuring_points = np.array(measuring_points) * 1e-6
#         time_interval = np.arange(0, n * interval, interval) * 1e-3

#         data = pd.DataFrame({
#             "Time (ms)": time_interval, "Usage (MB)": measuring_points
#         })
#         mean = sum(measuring_points) / n

#         fig = px.line(
#             data,
#             x="Time (ms)",
#             y="Usage (MB)",
#             title="Memory-Usage")

#         fig.add_shape(go.layout.Shape(
#             type="line",
#             x0=time_interval[0],
#             y0=mean,
#             x1=time_interval[-1],
#             y1=mean,
#             line=dict(color="Red", width=2)))

#         return html.Div([
#             dcc.Graph(figure=fig)
#         ])


# class ProfileMemoryUsageAnalyzer(Analyzer):

#     def __init__(self, profile_access: Type[ProfileAccess]):
#         self.profile_access = profile_access
#         self.all_memory_data = self.profile_access.get_all_record_data(
#             "memory::Usage")
#         super().__init__()

#     def name(self) -> str:
#         return "Profile Memory Usage"

#     def render(self):
#         fig = go.Figure()
#         for trace, trace_data in self.all_memory_data.items():
#             fig.add_trace(go.Bar(
#                 x=list(trace_data.keys()),
#                 y=[np.average(f["measuring_points"]) * 1e-6 for f in trace_data.values()],
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
