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
from typing import Type, Dict
from dash import html, dcc

from faas_profiler_core.models import MemoryUsage

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

        rss_times, rss = zip(*results.rss)
        vms_times, vms = zip(*results.vms)

        rss_interval = np.array(rss_times) - rss_times[0]
        vms_interval = np.array(vms_times) - vms_times[0]

        rss_df = pd.DataFrame({
            "Time (ms)": seconds_to_ms(rss_interval),
            "Usage": np.array(rss),
        })
        vms_df = pd.DataFrame({
            "Time (ms)": seconds_to_ms(vms_interval),
            "Usage": np.array(vms),
        })

        rss_multiplier, rss_bytes_unit = convert_bytes_to_best_unit(
            rss_df["Usage"].max())
        vms_multiplier, vms_bytes_unit = convert_bytes_to_best_unit(
            vms_df["Usage"].max())
        rss_df['Usage'] = rss_df['Usage'].apply(lambda x: x * rss_multiplier)
        vms_df['Usage'] = vms_df['Usage'].apply(lambda x: x * vms_multiplier)

        rss_fig = px.line(
            rss_df,
            x="Time (ms)",
            y="Usage",
            title=f"Memory-Usage ({rss_bytes_unit})")

        rss_fig.add_trace(go.Scatter(
            x=seconds_to_ms(np.array(rss_interval)),
            y=np.repeat(rss_df['Usage'].mean(), len(rss)),
            name="Mean",
            line=dict(color="Red", width=2)))

        vms_fig = px.line(
            vms_df,
            x="Time (ms)",
            y="Usage",
            title=f"Memory-Usage ({vms_bytes_unit})")

        vms_fig.add_trace(go.Scatter(
            x=seconds_to_ms(np.array(vms_interval)),
            y=np.repeat(vms_df['Usage'].mean(), len(vms)),
            name="Mean",
            line=dict(color="Red", width=2)))

        return html.Div([
            dcc.Graph(figure=rss_fig),
            dcc.Graph(figure=vms_fig),
            dbc.Row(
                [
                    dbc.Col([html.B("Number of Measuring Points:"), html.P(len(np.array(rss)))]),
                    dbc.Col([html.B("Interval:"), html.P(f"{seconds_to_ms(results.interval)} ms")])
                ]
            )
        ])

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        rss_df = pd.DataFrame()
        vms_df = pd.DataFrame()

        for record_id, data in record_data.items():
            results = MemoryUsage.load(data.results)
            rss_times, rss = zip(*results.rss)
            vms_times, vms = zip(*results.vms)

            rss_df = rss_df.append(pd.DataFrame({
                "Time (ms)": seconds_to_ms(np.array(rss_times) - rss_times[0]),
                "Usage": np.array(rss),
                "Record ID": str(record_id)
            }))
            vms_df = vms_df.append(pd.DataFrame({
                "Time (ms)": seconds_to_ms(np.array(vms_times) - vms_times[0]),
                "Usage": np.array(vms),
                "Record ID": str(record_id)
            }))

        rss_multiplier, rss_bytes_unit = convert_bytes_to_best_unit(
            rss_df["Usage"].max())
        vms_multiplier, vms_bytes_unit = convert_bytes_to_best_unit(
            vms_df["Usage"].max())
        rss_df['Usage'] = rss_df['Usage'].apply(lambda x: x * rss_multiplier)
        vms_df['Usage'] = vms_df['Usage'].apply(lambda x: x * vms_multiplier)

        rss_fig = px.line(
            rss_df,
            title=f"Memory Usage (RSS) by Record ({rss_bytes_unit})",
            x="Time (ms)",
            y="Usage",
            color="Record ID")

        vms_fig = px.line(
            vms_df,
            title=f"Virtual Memory Size by Record ({vms_bytes_unit})",
            x="Time (ms)",
            y="Usage",
            color="Record ID")

        return html.Div([
            dcc.Graph(figure=rss_fig),
            dcc.Graph(figure=vms_fig)
        ])

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()
        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):

            trace_usage = []
            for record_data in trace_data.values():
                record_result = MemoryUsage.load(record_data.results)
                _, usage = zip(*record_result.rss)
                trace_usage += usage

            df = pd.concat([df, pd.DataFrame({
                "Trace ID": str(trace_id)[:8],
                "Average Usage": np.array(trace_usage).mean()
            }, index=[idx])])

        multiplier, bytes_unit = convert_bytes_to_best_unit(
            df["Average Usage"].max())
        df['Average Usage'] = df['Average Usage'].apply(
            lambda x: x * multiplier)

        fig = px.line(
            df,
            x="Trace ID",
            y="Average Usage",
            title=f"Memory-Usage ({bytes_unit})")

        return html.Div([
            dcc.Graph(figure=fig)
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
