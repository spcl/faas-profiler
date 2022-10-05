#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Analyzers
"""

import pandas as pd
import plotly.express as px

from dash import html, dcc

from faas_profiler_core.models import EFSAccesses, S3Accesses

from faas_profiler.dashboard.analyzers.base import Analyzer
from faas_profiler.utilis import convert_bytes_to_best_unit


class EFSCaptureAnalyzer(Analyzer):
    requested_data = "aws::EFSAccess"
    name = "EFS Access Capture"

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()

        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):
            for record_data in trace_data.values():
                record_result = EFSAccesses.load(record_data.results)
                for access in record_result.accesses:
                    if not access.file_size or not access.execution_time:
                        continue

                    bandwidth = access.file_size / \
                        (.001 * access.execution_time)
                    df = pd.concat([df, pd.DataFrame({
                        "Mode": access.mode,
                        "Bandwidth": bandwidth,
                        "Trace ID": str(trace_id)[:8],
                        "EFS Mount": record_result.mount_point
                    }, index=[idx])])

        multiplier, bytes_unit = convert_bytes_to_best_unit(
            df["Bandwidth"].max())
        df['Bandwidth'] = df['Bandwidth'].apply(lambda x: x * multiplier) * 8

        fig = px.line(
            df,
            x="Trace ID",
            y="Bandwidth",
            color="Mode",
            title=f"EFS Bandwidth ({bytes_unit}it/sec)")

        fig.add_hline(
            y=df['Bandwidth'].mean(),
            name="Mean",
            line=dict(color="Red", width=2))

        return html.Div([
            dcc.Graph(figure=fig),
        ])


class S3CaptureAnalyzer(Analyzer):
    requested_data = "aws::S3Access"
    name = "S3 Access Capture"

    def analyze_profile(self, traces_data):
        df = pd.DataFrame()

        for idx, (trace_id, trace_data) in enumerate(traces_data.items()):
            for record_data in trace_data.values():
                record_result = S3Accesses.load(record_data.results)

                for access in record_result.accesses:
                    if not access.object_size or not access.execution_time:
                        continue

                    bandwidth = access.object_size / \
                        (.001 * access.execution_time)
                    df = pd.concat([df, pd.DataFrame({
                        "Mode": access.mode,
                        "Bandwidth": bandwidth,
                        "Trace ID": str(trace_id)[:8],
                        "Bucket": access.bucket_name
                    }, index=[idx])])

        multiplier, bytes_unit = convert_bytes_to_best_unit(
            df["Bandwidth"].max())
        df['Bandwidth'] = df['Bandwidth'].apply(lambda x: x * multiplier) * 8

        fig = px.line(
            df,
            line_group="Bucket",
            x="Trace ID",
            y="Bandwidth",
            color="Mode",
            title=f"S3 API Access Bandwidth ({bytes_unit}it/sec)")

        return html.Div([
            dcc.Graph(figure=fig),
        ])
