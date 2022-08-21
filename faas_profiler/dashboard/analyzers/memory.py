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
import dash_core_components as dcc

from typing import Type
from dash import html

from faas_profiler_core.models import MemoryLineUsage, MemoryUsage

from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler_core.models import RecordData


class LineMemoryAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = MemoryLineUsage.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for the line analyzer
        """
        return "Line Memory Analyzer"

    def render(self):
        """
        Returns a table for all recorded lines.
        """
        line_memories = self.results.line_memories
        if len(line_memories) == 0:
            return html.P("No memory lines recorded.")

        table_header = [html.Thead(html.Tr([
            html.Th("Line Number"),
            html.Th("Total Memory (MB)"),
            html.Th("Memory Increment (MB)"),
            html.Th("Occurrence"),
            html.Th("Line Content")]))]

        table_rows = []
        for memory_line in line_memories:
            table_rows.append(html.Tr([
                html.Td(memory_line.line_number),
                html.Td("{:.2f}".format(memory_line.memory_total)),
                html.Td("{:.2f}".format(memory_line.memory_increment)),
                html.Td(memory_line.occurrences),
                html.Td(html.Code(html.Pre(memory_line.content)))]))

        table_body = [html.Tbody(table_rows)]

        return dbc.Table(
            table_header +
            table_body,
            bordered=False,
            color="light")


class MemoryUsageAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = MemoryUsage.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for the line analyzer
        """
        return "Memory Usage"

    def render(self):
        """
        Returns a line chart for all recorded memory usages.
        """
        interval = self.results.interval
        measuring_points = self.results.measuring_points

        if len(measuring_points) == 0:
            return html.P("No memory usages recorded.")

        n = len(measuring_points)
        measuring_points = np.array(measuring_points) * 1e-6
        time_interval = np.arange(0, n * interval, interval) * 1e-3

        data = pd.DataFrame({
            "Time (ms)": time_interval, "Usage (MB)": measuring_points
        })
        mean = sum(measuring_points) / n

        fig = px.line(
            data,
            x="Time (ms)",
            y="Usage (MB)",
            title="Memory-Usage")

        fig.add_shape(go.layout.Shape(
            type="line",
            x0=time_interval[0],
            y0=mean,
            x1=time_interval[-1],
            y1=mean,
            line=dict(color="Red", width=2)))


        return html.Div([
            dcc.Graph(figure=fig)
        ])
