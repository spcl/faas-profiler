#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Analyzers
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_core_components as dcc

from typing import Type
from dash import html

from faas_profiler_core.models import CPUUsage

from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler_core.models import RecordData


class CPUUsageAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = CPUUsage.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for the line analyzer
        """
        return "CPU Usage"

    def render(self):
        """
        Returns a line chart for all recorded memory usages.
        """
        interval = self.results.interval
        measuring_points = self.results.measuring_points

        if len(measuring_points) == 0:
            return html.P("No cpu usages recorded.")

        n = len(measuring_points)
        measuring_points = np.array(measuring_points)
        time_interval = np.arange(0, n * interval, interval) * 1e-3

        data = pd.DataFrame({
            "Time (ms)": time_interval, "Usage (%)": measuring_points
        })
        mean = sum(measuring_points) / n

        fig = px.line(
            data,
            x="Time (ms)",
            y="Usage (%)",
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
