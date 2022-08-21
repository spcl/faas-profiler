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

from faas_profiler_core.models import NetworkIOCounters, NetworkConnections
from faas_profiler.dashboard.analyzers import Analyzer
from faas_profiler_core.models import RecordData


class NetworkIOAnalyzer(Analyzer):

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = NetworkIOCounters.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for the line analyzer
        """
        return "Network IO Counters"

    def render(self):
        """
        Returns a bar chart for all IO Counters
        """
        bytes_fig = go.Figure([go.Bar(
            x=["Bytes sent (MB)", "Bytes received (MB)"],
            y=[self.results.bytes_sent * 1e-6, self.results.bytes_received * 1e-6]
        )])

        packet_fig = go.Figure([go.Bar(
            x=["Packets sent", "Packets received"],
            y=[self.results.packets_sent, self.results.packets_received]
        )])

        error_fig = go.Figure([go.Bar(
            x=["Error In", "Error Out"],
            y=[self.results.error_in, self.results.error_out]
        )])

        drop_fig = go.Figure([go.Bar(
            x=["Drop In", "Drop out"],
            y=[self.results.drop_in, self.results.drop_out]
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

    def __init__(self, record_data: Type[RecordData]):
        self.record_data = record_data
        self.record_name = record_data.name
        self.results = NetworkConnections.load(self.record_data.results)

        super().__init__(record_data)

    def name(self) -> str:
        """
        Returns the name for the line analyzer
        """
        return "Network Connections"

    def render(self):
        """
        Returns a bar chart for all IO Counters
        """
        connections = self.results.connections
        if len(connections) == 0:
            return html.P("No connections recorded.")

        _connection_rows = []

        n = len(connections)
        num_per_group = 4

        conn_groups = [connections[i:i + n]
                       for i in range(0, n, num_per_group)]
        for conn_group in conn_groups:
            _connection_cards = []
            for conn in conn_group:
                _connection_cards.append(dbc.Col(
                    dbc.Card([dbc.CardBody([
                        html.P([html.B("Socket Descriptor: "), conn.socket_descriptor], className="card-text"),
                        html.P([html.B("Socket Family: "), conn.socket_family.name], className="card-text"),
                        html.P([html.B("Local Address: "), conn.local_address], className="card-text"),
                        html.P([html.B("Remote Address: "), conn.remote_address], className="card-text")
                    ])
                    ])))

            _connection_rows.append(dbc.Row(_connection_cards))

        return html.Div(_connection_rows)
