#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

from unicodedata import name
from xml import dom
import pandas as pd

import dns.resolver
import dns.reversename
from socket import getservbyport

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
from faas_profiler.utilis import bytes_to_kb, get_idx_safely, convert_bytes_to_best_unit, short_uuid


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
            go.Scatter(
                x=df["Trace"],
                y=df2["packets_received"],
                name="Packets received"),
            row=1,
            col=1)

        fig.add_trace(
            go.Scatter(
                x=df["Trace"],
                y=df2["packets_sent"],
                name="Packets sent"),
            row=1,
            col=1)

        fig.add_trace(
            go.Scatter(
                x=df["Trace"],
                y=df2["bytes_received"].apply(bytes_to_kb),
                name="Bytes received (KB)"),
            row=1,
            col=2)

        fig.add_trace(
            go.Scatter(
                x=df["Trace"],
                y=df2["bytes_sent"].apply(bytes_to_kb),
                name="Bytes sent (KB)"),
            row=1,
            col=2)

        return html.Div(
            dcc.Graph(figure=fig)
        )

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        df = pd.DataFrame()

        for record_id, data in record_data.items():
            results = NetworkIOCounters.load(data.results)
            df = df.append({
                "Record ID": short_uuid(record_id),
                "Bytes Sent": results.bytes_sent,
                "Bytes Received": results.bytes_received,
                "Packets Sent": results.packets_sent,
                "Packets Received": results.packets_received,
                "Error In": results.error_in,
                "Error Out": results.error_out,
                "Drop In": results.drop_in,
                "Drop Out": results.drop_out
            }, ignore_index=True)

        bytes_peak = max(df["Bytes Sent"].max(), df["Bytes Received"].max())
        multiplier, bytes_unit = convert_bytes_to_best_unit(bytes_peak)
        df['Bytes Sent'] = df['Bytes Sent'].apply(lambda x: x * multiplier)
        df['Bytes Received'] = df['Bytes Received'].apply(
            lambda x: x * multiplier)

        bytes_fig = px.line(
            df,
            title=f"Bytes Sent/Received by Record ({bytes_unit})",
            x="Record ID",
            y=["Bytes Sent", "Bytes Received"])

        packet_fig = px.line(
            df,
            title=f"Packets Sent/Received by Record",
            x="Record ID",
            y=["Packets Sent", "Packets Received"])

        error_fig = px.line(
            df,
            title=f"Error In/Out by Record",
            x="Record ID",
            y=["Error In", "Error Out"])

        drop_fig = px.line(
            df,
            title=f"Drop In/Out Record",
            x="Record ID",
            y=["Drop In", "Drop Out"])

        return html.Div([
            dbc.Row([
                dbc.Col(dcc.Graph(figure=bytes_fig)),
                dbc.Col(dcc.Graph(figure=packet_fig))
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=error_fig)),
                dbc.Col(dcc.Graph(figure=drop_fig))
            ])
        ])

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

    UNKNOWN_IP = "Unknown IP"
    UNKNOWN_PORT = "Unknown Port"
    UNKNOWN_DOMAIN = "Unknown Domain"
    UNKNOWN_APPLICATION = "Unknown Application"

    def analyze_record(self, record_data: Type[RecordData]):
        results = NetworkConnections.load(record_data.results)
        df = pd.DataFrame()

        for connection in results.connections:
            ip_split = str(connection.remote_address).split(":")
            ip_addr = get_idx_safely(ip_split, 0, self.UNKNOWN_IP)
            port = get_idx_safely(ip_split, 1, self.UNKNOWN_PORT)

            domain = self.UNKNOWN_DOMAIN
            application = self.UNKNOWN_APPLICATION

            if ip_addr != self.UNKNOWN_IP:
                try:
                    reverse_dns = dns.reversename.from_address(ip_addr)
                    domain = str(dns.resolver.resolve(reverse_dns, "PTR")[0])
                except BaseException:
                    pass

            if port != self.UNKNOWN_PORT:
                try:
                    application = getservbyport(int(port))
                except BaseException:
                    pass

            df = df.append({
                "IP Address": ip_addr,
                "Port": port,
                "Domain": domain,
                "Application": application
            }, ignore_index=True)

        fig = px.bar(
            df,
            title="Connections by Domain",
            x="Domain",
            color="Application",
            text="IP Address")

        return html.Div(
            dcc.Graph(figure=fig)
        )
