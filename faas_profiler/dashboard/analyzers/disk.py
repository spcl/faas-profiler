#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import pandas as pd

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import plotly.express as px

from plotly.subplots import make_subplots
from typing import Type, Dict
from uuid import UUID
from dash import html, dcc

from faas_profiler_core.models import DiskIOCounters
from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler_core.models import RecordData

from faas_profiler.utilis import convert_bytes_to_best_unit, short_uuid


class DiskIOAnalyzer(Analyzer):
    requested_data = "disk::IOCounters"
    name = "Disk IO Counters"

    BYTES_AXIS_READ = "Read in {unit}"
    BYTES_AXIS_WRITE = "Write {unit}"

    COUNT_AXIS_READ = "Count Read"
    COUNT_AXIS_WRITE = "Count Write"

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        df = pd.DataFrame()

        for record_id, data in record_data.items():
            results = DiskIOCounters.load(data.results)
            df = df.append({
                "Record ID": short_uuid(record_id),
                "Bytes Read": results.read_bytes,
                "Bytes Write": results.write_bytes,
                "Count Read": results.read_count,
                "Count Write": results.write_count,
            }, ignore_index=True)

        bytes_peak = max(df["Bytes Read"].max(), df["Bytes Write"].max())
        multiplier, bytes_unit = convert_bytes_to_best_unit(bytes_peak)
        df['Bytes Write'] = df['Bytes Write'].apply(lambda x: x * multiplier)
        df['Bytes Read'] = df['Bytes Read'].apply(lambda x: x * multiplier)

        bytes_fig = px.line(
            df,
            title=f"Bytes Read/Write by Record ({bytes_unit})",
            x="Record ID",
            y=["Bytes Read", "Bytes Write"])

        count_fig = px.line(
            df,
            title="Count Read/Write by Record",
            x="Record ID",
            y=["Count Read", "Count Write"])

        return html.Div([
            dbc.Row([
                dbc.Col(dcc.Graph(figure=bytes_fig)),
                dbc.Col(dcc.Graph(figure=count_fig))
            ])
        ])

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
