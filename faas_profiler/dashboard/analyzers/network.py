#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import pandas as pd

from uuid import UUID
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import plotly.express as px

from typing import Type, Dict, Any, List
from dash import html, dcc

from faas_profiler_core.models import NetworkIOCounters, NetworkConnections
from faas_profiler_core.models import RecordData

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.utilis import bytes_to_kb

class NetworkIOAnalyzer(Analyzer):
    requested_data = "network::IOCounters"
    name = "Network IO Counters"

    def analyze_profile(
        self,
        traces_data: Dict[UUID, Type[RecordData]]
    ) -> Any:
        df = pd.DataFrame()
        for trace_id, records in traces_data.items():
            for record in records:
                df = df.append(
                    {"Trace": str(trace_id), **record.results},
                ignore_index=True)


        df2 = df.groupby("Trace").mean()
        fig = make_subplots(rows=1, cols=2)

        fig.add_trace(
            go.Scatter(x=df["Trace"], y=df2["packets_received"], name="Packets received"),
            row=1, col=1)

        fig.add_trace(
            go.Scatter(x=df["Trace"], y=df2["packets_sent"], name="Packets sent"),
            row=1, col=1)

        fig.add_trace(
            go.Scatter(x=df["Trace"], y=df2["bytes_received"].apply(bytes_to_kb), name="Bytes received (KB)"),
            row=1, col=2)

        fig.add_trace(
            go.Scatter(x=df["Trace"], y=df2["bytes_sent"].apply(bytes_to_kb), name="Bytes sent (KB)"),
            row=1, col=2)

        return html.Div(
            dcc.Graph(figure=fig)
        )

 
    def analyze_trace(self, record_data: List[Type[RecordData]]):
        return super().analyze_trace(record_data)


    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        _results = NetworkIOCounters.load(record_data.results)

        bytes_fig = go.Figure([go.Bar(
            x=["Bytes sent (KB)", "Bytes received (KB)"],
            y=[bytes_to_kb(_results.bytes_sent), bytes_to_kb(_results.bytes_received)]
        )])

        packet_fig = go.Figure([go.Bar(
            x=["Packets sent", "Packets received"],
            y=[_results.packets_sent, _results.packets_received]
        )])

        error_fig = go.Figure([go.Bar(
            x=["Error In", "Error Out"],
            y=[_results.error_in, _results.error_out]
        )])

        drop_fig = go.Figure([go.Bar(
            x=["Drop In", "Drop out"],
            y=[_results.drop_in, _results.drop_out]
        )])

        return html.Div(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=bytes_fig)),
                    dbc.Col(dcc.Graph(figure=packet_fig)),
                    dbc.Col(dcc.Graph(figure=error_fig)),
                    dbc.Col(dcc.Graph(figure=drop_fig))
                ]
            ))



class NetworkConnectionAnalyzer(Analyzer):
    requested_data = "network::Connections"
    name = "Network Connections"

    def analyze_record(self, record_data: Type[RecordData]):
        if not record_data or not record_data.results:
            return

        df = pd.DataFrame()
        _results = NetworkConnections.load(record_data.results)

        for connection in _results.connections:
            df = df.append({
                "Connection": f"{connection.remote_address} ({connection.socket_family.name})",
                "Number of Connections": connection.number_of_connections
            }, ignore_index=True)

        fig = px.bar(df, x='Connection', y='Number of Connections')
        return html.Div(
            dcc.Graph(figure=fig)
        )