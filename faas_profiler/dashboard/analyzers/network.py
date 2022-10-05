#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""
import numpy as np
import pandas as pd

import dns.resolver
import dns.reversename
from socket import getservbyport

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import plotly.express as px

from typing import Tuple, Type, Dict
from dash import html, dcc

from faas_profiler_core.models import NetworkIOCounters, NetworkConnections
from faas_profiler_core.models import RecordData

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.utilis import bytes_to_kb, get_idx_safely, convert_bytes_to_best_unit, short_uuid


class NetworkIOAnalyzer(Analyzer):
    requested_data = "network::IOCounters"
    name = "Network IO Counters"

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()
        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):

            bytes_sent, bytes_received = [], []
            packets_sent, packets_received = [], []
            for record_data in trace_data.values():
                record_result = NetworkIOCounters.load(record_data.results)
                bytes_sent.append(record_result.bytes_sent)
                bytes_received.append(record_result.bytes_received)
                packets_sent.append(record_result.packets_sent)
                packets_received.append(record_result.packets_received)

            df = pd.concat([df, pd.DataFrame({
                "Trace ID": str(trace_id)[:8],
                "Average Bytes Sent": np.array(bytes_sent).mean(),
                "Average Bytes Received": np.array(bytes_received).mean(),
                "Average Packets Sent": np.array(packets_sent).mean(),
                "Average Packets Received": np.array(packets_received).mean()
            }, index=[idx])])

        multiplier, bytes_unit = convert_bytes_to_best_unit(
            max(df["Average Bytes Sent"].max(), df["Average Bytes Received"].max()))
        df['Average Bytes Sent'] = df['Average Bytes Sent'].apply(
            lambda x: x * multiplier)
        df['Average Bytes Received'] = df['Average Bytes Received'].apply(
            lambda x: x * multiplier)

        fig = px.line(
            df,
            x="Trace ID",
            y=["Average Bytes Sent", "Average Bytes Received"],
            title=f"Bytes Sent/Received in {bytes_unit}")

        fig.update_layout(
            xaxis_title="Traces",
            yaxis_title=f"Bytes Sent/Received in {bytes_unit}",
            legend_title="Bytes Sent/Received",
        )

        return html.Div([
            dcc.Graph(figure=fig)
        ])

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
            title="Packets Sent/Received by Record",
            x="Record ID",
            y=["Packets Sent", "Packets Received"])

        error_fig = px.line(
            df,
            title="Error In/Out by Record",
            x="Record ID",
            y=["Error In", "Error Out"])

        drop_fig = px.line(
            df,
            title="Drop In/Out Record",
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

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()
        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):

            for record_data in trace_data.values():
                record_result = NetworkConnections.load(record_data.results)
                for conn in record_result.connections:
                    if str(conn.remote_address).startswith("169.254"):
                        continue

                    df = pd.concat([df, pd.DataFrame({
                        "Trace ID": str(trace_id)[:8],
                        "Remote Address": conn.remote_address,
                        "Connections": conn.number_of_connections
                    }, index=[idx])])

        fig = px.bar(
            df,
            title="Connections by IP",
            y="Connections",
            x="Remote Address",
            color="Trace ID")

        return html.Div(
            dcc.Graph(figure=fig)
        )

    def analyze_trace(
        self,
        record_data: Dict[str, Type[RecordData]]
    ):
        df = pd.DataFrame()

        for record_id, data in record_data.items():
            result = NetworkConnections.load(data.results)
            for connection in result.connections:
                ip_addr, domain, port, application = self.enhance_connection(
                    connection.remote_address)

                df = df.append({
                    "Record ID": str(record_id),
                    "IP Address": ip_addr,
                    "Port": port,
                    "Domain": domain,
                    "Application": application,
                    "Count": connection.number_of_connections
                }, ignore_index=True)

        fig = px.bar(
            df,
            title="Connections by Domain",
            y="Domain",
            x="Count",
            color="Record ID",
            text="IP Address")

        return html.Div(
            dcc.Graph(figure=fig)
        )

    def analyze_record(self, record_data: Type[RecordData]):
        results = NetworkConnections.load(record_data.results)
        df = pd.DataFrame()

        for connection in results.connections:
            ip_addr, domain, port, application = self.enhance_connection(
                connection.remote_address)

            df = df.append({
                "IP Address": ip_addr,
                "Port": port,
                "Domain": domain,
                "Application": application,
                "Count": connection.number_of_connections
            }, ignore_index=True)

        fig = px.bar(
            df,
            title="Connections by Domain",
            x="Domain",
            y="Count",
            color="Application",
            text="IP Address")

        return html.Div(
            dcc.Graph(figure=fig)
        )

    def enhance_connection(
        self,
        full_remote_addr: str
    ) -> Tuple[str, str, str, str]:
        ip_split = str(full_remote_addr).split(":")
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

        return ip_addr, domain, port, application
